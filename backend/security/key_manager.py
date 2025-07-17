"""
Secure Key Management System
Handles private key storage and access with multiple security layers
"""
import os
import base58
import logging
from typing import Optional
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class SecureKeyManager:
    """
    Secure key management with encryption and access controls
    """
    
    def __init__(self):
        self.encryption_key = self._get_or_create_encryption_key()
        self.fernet = Fernet(self.encryption_key)
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for additional security layer"""
        key_file = "/app/backend/security/master.key"
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            os.makedirs("/app/backend/security", exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            # Set restrictive permissions
            os.chmod(key_file, 0o600)
            return key
    
    def get_house_private_key(self) -> Optional[str]:
        """
        Securely retrieve house wallet private key
        """
        try:
            # Try to get from environment variable first
            encrypted_key = os.getenv("HOUSE_WALLET_PRIVATE_KEY_ENCRYPTED")
            if encrypted_key:
                # Decrypt the key
                decrypted_key = self.fernet.decrypt(encrypted_key.encode()).decode()
                return decrypted_key
            
            # Fallback to plain key (for migration period)
            plain_key = os.getenv("HOUSE_WALLET_PRIVATE_KEY")
            if plain_key:
                logger.warning("Using unencrypted private key - MIGRATE TO ENCRYPTED VERSION!")
                return plain_key
            
            raise ValueError("No house wallet private key found in environment")
            
        except Exception as e:
            logger.error(f"Failed to retrieve house private key: {e}")
            raise ValueError("House wallet private key access failed")
    
    def encrypt_private_key(self, private_key: str) -> str:
        """
        Encrypt a private key for storage
        """
        try:
            encrypted_key = self.fernet.encrypt(private_key.encode())
            return encrypted_key.decode()
        except Exception as e:
            logger.error(f"Failed to encrypt private key: {e}")
            raise ValueError("Private key encryption failed")
    
    def validate_private_key(self, private_key: str) -> bool:
        """
        Validate private key format and accessibility
        """
        try:
            # Try to decode the private key
            private_key_bytes = base58.b58decode(private_key)
            
            # Check length (Solana private keys are 64 bytes)
            if len(private_key_bytes) != 64:
                return False
            
            # Try to create keypair
            from solders.keypair import Keypair
            keypair = Keypair.from_bytes(private_key_bytes)
            
            return True
        except Exception as e:
            logger.error(f"Private key validation failed: {e}")
            return False

# Global instance
key_manager = SecureKeyManager()