"""
API Authentication and Rate Limiting System
Implements JWT-based authentication and request rate limiting
"""
import jwt
import time
import hashlib
from typing import Dict, Optional
from datetime import datetime, timedelta
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    In-memory rate limiter for API endpoints
    """
    
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
        self.blocked_ips: Dict[str, float] = {}
        
        # Rate limit configurations
        self.LIMITS = {
            "per_ip_per_minute": 100,      # 100 requests per IP per minute
            "per_ip_per_hour": 1000,       # 1000 requests per IP per hour
            "per_wallet_per_minute": 10,   # 10 bets per wallet per minute
            "per_wallet_per_hour": 100,    # 100 bets per wallet per hour
            "block_duration": 300,         # 5 minutes block duration
        }
    
    def _get_client_id(self, request: Request, wallet_address: str = None) -> str:
        """Get unique client identifier"""
        client_ip = request.client.host
        if wallet_address:
            return f"wallet_{wallet_address}"
        return f"ip_{client_ip}"
    
    def _cleanup_old_requests(self, client_id: str, window_seconds: int):
        """Remove old requests outside the time window"""
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > cutoff_time
        ]
    
    def is_rate_limited(self, request: Request, wallet_address: str = None) -> bool:
        """
        Check if request should be rate limited
        """
        client_ip = request.client.host
        current_time = time.time()
        
        # Check if IP is temporarily blocked
        if client_ip in self.blocked_ips:
            if current_time < self.blocked_ips[client_ip]:
                return True
            else:
                del self.blocked_ips[client_ip]
        
        # Check IP-based rate limiting
        ip_client_id = f"ip_{client_ip}"
        self._cleanup_old_requests(ip_client_id, 60)  # 1 minute window
        
        if len(self.requests[ip_client_id]) >= self.LIMITS["per_ip_per_minute"]:
            # Block IP for 5 minutes
            self.blocked_ips[client_ip] = current_time + self.LIMITS["block_duration"]
            logger.warning(f"IP {client_ip} blocked for rate limiting")
            return True
        
        # Check wallet-based rate limiting if provided
        if wallet_address:
            wallet_client_id = f"wallet_{wallet_address}"
            self._cleanup_old_requests(wallet_client_id, 60)  # 1 minute window
            
            if len(self.requests[wallet_client_id]) >= self.LIMITS["per_wallet_per_minute"]:
                logger.warning(f"Wallet {wallet_address} rate limited")
                return True
        
        return False
    
    def record_request(self, request: Request, wallet_address: str = None):
        """
        Record a new request
        """
        current_time = time.time()
        client_ip = request.client.host
        
        # Record IP request
        ip_client_id = f"ip_{client_ip}"
        self.requests[ip_client_id].append(current_time)
        
        # Record wallet request if provided
        if wallet_address:
            wallet_client_id = f"wallet_{wallet_address}"
            self.requests[wallet_client_id].append(current_time)
    
    def get_rate_limit_status(self, request: Request, wallet_address: str = None) -> dict:
        """
        Get current rate limit status
        """
        client_ip = request.client.host
        ip_client_id = f"ip_{client_ip}"
        
        self._cleanup_old_requests(ip_client_id, 60)
        
        status = {
            "ip_requests_last_minute": len(self.requests[ip_client_id]),
            "ip_limit_per_minute": self.LIMITS["per_ip_per_minute"],
            "is_blocked": client_ip in self.blocked_ips
        }
        
        if wallet_address:
            wallet_client_id = f"wallet_{wallet_address}"
            self._cleanup_old_requests(wallet_client_id, 60)
            status.update({
                "wallet_requests_last_minute": len(self.requests[wallet_client_id]),
                "wallet_limit_per_minute": self.LIMITS["per_wallet_per_minute"]
            })
        
        return status

class APIAuthenticator:
    """
    JWT-based API authentication system
    """
    
    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or "your-secret-key-change-this-in-production"
        self.algorithm = "HS256"
        self.token_expiry = timedelta(hours=24)
    
    def create_access_token(self, wallet_address: str) -> str:
        """
        Create JWT access token for authenticated requests
        """
        payload = {
            "wallet_address": wallet_address,
            "exp": datetime.utcnow() + self.token_expiry,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> dict:
        """
        Verify and decode JWT token
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> dict:
        """
        Get current authenticated user from token
        """
        token = credentials.credentials
        return self.verify_token(token)

# Security middleware
class SecurityMiddleware:
    """
    Combined security middleware for authentication and rate limiting
    """
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.authenticator = APIAuthenticator()
        self.security = HTTPBearer()
    
    async def check_rate_limit(self, request: Request, wallet_address: str = None):
        """
        Check rate limiting for request
        """
        if self.rate_limiter.is_rate_limited(request, wallet_address):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": "60"}
            )
        
        self.rate_limiter.record_request(request, wallet_address)
    
    async def authenticate_request(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> dict:
        """
        Authenticate API request
        """
        return self.authenticator.verify_token(credentials.credentials)
    
    async def security_check(self, request: Request, require_auth: bool = False) -> dict:
        """
        Combined security check
        """
        user_info = None
        
        # Check authentication if required
        if require_auth:
            try:
                auth_header = request.headers.get("Authorization")
                if not auth_header or not auth_header.startswith("Bearer "):
                    raise HTTPException(status_code=401, detail="Authentication required")
                
                token = auth_header.split(" ")[1]
                user_info = self.authenticator.verify_token(token)
                
            except Exception as e:
                raise HTTPException(status_code=401, detail="Authentication failed")
        
        # Always check rate limiting
        wallet_address = user_info.get("wallet_address") if user_info else None
        await self.check_rate_limit(request, wallet_address)
        
        return user_info or {}

# Global security instance
security_middleware = SecurityMiddleware()

# Dependency functions for FastAPI
async def require_auth(request: Request):
    """Require authentication for endpoint"""
    return await security_middleware.security_check(request, require_auth=True)

async def optional_auth(request: Request):
    """Optional authentication with rate limiting"""
    return await security_middleware.security_check(request, require_auth=False)

async def rate_limit_only(request: Request):
    """Rate limiting only, no authentication"""
    await security_middleware.check_rate_limit(request)
    return {}

# Helper functions
def generate_api_key(wallet_address: str) -> str:
    """Generate API key for a wallet"""
    return security_middleware.authenticator.create_access_token(wallet_address)

def hash_sensitive_data(data: str) -> str:
    """Hash sensitive data for logging"""
    return hashlib.sha256(data.encode()).hexdigest()[:8]