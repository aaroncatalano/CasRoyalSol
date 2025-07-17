# 🔐 Security Implementation Guide

## Phase 1: Security Fixes Integration

### STEP 1: Update Server.py with Security Middleware

Add these imports to the top of server.py:

```python
# Add these imports after existing imports
from security.key_manager import key_manager
from security.validators import InputValidator, ValidatedWagerRequest, ValidatedGameResultRequest
from security.auth import security_middleware, require_auth, optional_auth, rate_limit_only
from security.error_handler import error_handler, safe_endpoint, log_security_event, sanitize_for_logging
```

### STEP 2: Update SolanaPayoutService

Replace the existing SolanaPayoutService initialization:

```python
# OLD CODE - Remove this
if SOLANA_PAYOUT_AVAILABLE:
    try:
        solana_payout_service = SolanaPayoutService()
        logger.info("Solana payout service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Solana payout service: {e}")
        solana_payout_service = None

# NEW CODE - Add this
if SOLANA_PAYOUT_AVAILABLE:
    try:
        # Use secure key manager
        house_private_key = key_manager.get_house_private_key()
        solana_payout_service = SolanaPayoutService(house_private_key)
        logger.info("Solana payout service initialized with secure key management")
    except Exception as e:
        logger.error(f"Failed to initialize Solana payout service: {e}")
        solana_payout_service = None
```

### STEP 3: Update API Endpoints with Security

Example for wager endpoint:

```python
@api_router.post("/game/wager")
@safe_endpoint
async def place_wager(
    request: Request,
    wager: ValidatedWagerRequest,
    security_info: dict = Depends(optional_auth)
):
    """Process game wager with security validation"""
    try:
        # Log security event
        log_security_event("WAGER_ATTEMPT", f"Wallet: {wager.player_wallet[:8]}...", request)
        
        # Validate wager amount for game type
        InputValidator.validate_wager_amount(wager.amount, wager.game_type)
        
        # Calculate dev fee
        dev_fee = wager.amount * TRANSACTION_FEE_PERCENTAGE
        game_amount = wager.amount - dev_fee
        
        # Store wager in database
        wager_record = {
            "id": str(uuid.uuid4()),
            "player_wallet": wager.player_wallet,
            "amount": wager.amount,
            "game_type": wager.game_type,
            "session_id": wager.session_id,
            "dev_fee": dev_fee,
            "game_amount": game_amount,
            "dev_wallet": DEV_WALLET_ADDRESS,
            "transaction_signature": wager.transaction_signature,
            "timestamp": datetime.utcnow(),
            "client_ip": request.client.host
        }
        
        # Safe database operation
        await db_error_handler.safe_db_operation(
            db.wagers.insert_one, 
            wager_record
        )
        
        return {
            "success": True,
            "wager_id": wager_record["id"],
            "dev_fee": dev_fee,
            "game_amount": game_amount,
            "dev_wallet": DEV_WALLET_ADDRESS,
            "message": "Wager placed successfully"
        }
        
    except Exception as e:
        log_security_event("WAGER_ERROR", f"Error: {str(e)}", request)
        return error_handler.handle_error(e, request)
```

### STEP 4: Update Environment Variables

Update your .env file:

```bash
# Security Configuration
HOUSE_WALLET_PRIVATE_KEY_ENCRYPTED=your_encrypted_private_key_here
JWT_SECRET_KEY=your-super-secure-secret-key-change-this
ENVIRONMENT=production

# Logging Configuration
LOG_LEVEL=WARNING
LOG_FILE_PATH=/var/log/gaming_platform.log
```

### STEP 5: Add Security Middleware to FastAPI App

Add this after creating the FastAPI app:

```python
# Add security middleware
@app.middleware("http")
async def security_middleware_handler(request: Request, call_next):
    """Security middleware for all requests"""
    try:
        # Log request
        sanitized_path = sanitize_for_logging(request.url.path)
        logger.info(f"Request: {request.method} {sanitized_path} | IP: {request.client.host}")
        
        # Process request
        response = await call_next(request)
        
        # Log response
        logger.info(f"Response: {response.status_code} | Path: {sanitized_path}")
        
        return response
        
    except Exception as e:
        return error_handler.handle_error(e, request)
```

## Implementation Priority

### 🔴 IMMEDIATE (Critical Security)
1. **Implement secure key management** - Move private keys out of .env
2. **Add input validation** - Prevent injection attacks
3. **Enable error handling** - Prevent information leakage

### 🟡 HIGH PRIORITY (Within 24 hours)
1. **Add rate limiting** - Prevent abuse
2. **Implement authentication** - Control access
3. **Add security logging** - Monitor threats

### 🟢 MEDIUM PRIORITY (Within 48 hours)
1. **Database connection pooling** - Improve performance
2. **Add monitoring dashboard** - Track system health
3. **Implement backup systems** - Ensure reliability

## Testing the Implementation

### 1. Test Input Validation
```bash
# Test invalid wallet address
curl -X POST "http://localhost:8001/api/game/wager" \
  -H "Content-Type: application/json" \
  -d '{"player_wallet": "invalid", "amount": 0.1, "game_type": "blackjack", "session_id": "test"}'
```

### 2. Test Rate Limiting
```bash
# Rapid requests to trigger rate limiting
for i in {1..101}; do
  curl -X GET "http://localhost:8001/api/status" &
done
```

### 3. Test Error Handling
```bash
# Test with invalid game type
curl -X POST "http://localhost:8001/api/game/wager" \
  -H "Content-Type: application/json" \
  -d '{"player_wallet": "valid_wallet", "amount": 0.1, "game_type": "invalid", "session_id": "test"}'
```

## Security Checklist

### ✅ Before Deploying
- [ ] Private keys moved to secure storage
- [ ] Input validation implemented on all endpoints
- [ ] Rate limiting configured
- [ ] Error handling implemented
- [ ] Security logging enabled
- [ ] JWT authentication configured
- [ ] Database connection secured
- [ ] HTTPS enabled
- [ ] CORS configured properly
- [ ] All sensitive data sanitized in logs

### ✅ After Deploying
- [ ] Monitor error rates
- [ ] Check rate limiting effectiveness
- [ ] Verify authentication working
- [ ] Test all game endpoints
- [ ] Monitor security logs
- [ ] Test wallet connections
- [ ] Verify transaction processing
- [ ] Check payout functionality

## Common Issues and Solutions

### Issue: Private Key Not Found
**Solution**: Ensure HOUSE_WALLET_PRIVATE_KEY_ENCRYPTED is set in .env

### Issue: Rate Limiting Too Aggressive
**Solution**: Adjust limits in security/auth.py

### Issue: Authentication Failing
**Solution**: Check JWT_SECRET_KEY configuration

### Issue: Database Connection Errors
**Solution**: Implement db_error_handler retry logic

## Monitoring and Maintenance

### Log Files to Monitor
- `/var/log/gaming_platform.log` - Application logs
- `/var/log/solana_payouts.log` - Payout logs
- `/var/log/security_events.log` - Security events

### Key Metrics to Track
- Error rates by endpoint
- Rate limiting trigger frequency
- Authentication success/failure rates
- Database connection health
- Transaction processing times

This implementation provides enterprise-grade security for your gaming platform!