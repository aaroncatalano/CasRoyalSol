"""
Input Validation and Sanitization System
Comprehensive validation for all API endpoints
"""
import re
from typing import Any, Dict, Optional
from fastapi import HTTPException
from pydantic import BaseModel, validator
from solders.pubkey import Pubkey as PublicKey
import logging

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom validation error"""
    pass

class InputValidator:
    """
    Comprehensive input validation and sanitization
    """
    
    # Solana wallet address regex
    SOLANA_ADDRESS_REGEX = r'^[1-9A-HJ-NP-Za-km-z]{32,44}$'
    
    # Transaction signature regex
    SOLANA_SIGNATURE_REGEX = r'^[1-9A-HJ-NP-Za-km-z]{87,88}$'
    
    # Game types
    VALID_GAME_TYPES = {"blackjack", "video_poker", "crash"}
    
    # Wager limits by game type
    WAGER_LIMITS = {
        "blackjack": {"min": 0.01, "max": 10.0},
        "video_poker": {"min": 0.01, "max": 10.0},
        "crash": {"min": 0.005, "max": 0.2}
    }
    
    @staticmethod
    def validate_solana_address(address: str) -> str:
        """
        Validate Solana wallet address format and structure
        """
        if not address:
            raise ValidationError("Wallet address cannot be empty")
        
        # Remove any whitespace
        address = address.strip()
        
        # Check format
        if not re.match(InputValidator.SOLANA_ADDRESS_REGEX, address):
            raise ValidationError("Invalid Solana wallet address format")
        
        # Try to create PublicKey to validate
        try:
            PublicKey.from_string(address)
        except Exception as e:
            raise ValidationError(f"Invalid Solana wallet address: {str(e)}")
        
        return address
    
    @staticmethod
    def validate_transaction_signature(signature: str) -> str:
        """
        Validate Solana transaction signature format
        """
        if not signature:
            raise ValidationError("Transaction signature cannot be empty")
        
        # Remove any whitespace
        signature = signature.strip()
        
        # Check format
        if not re.match(InputValidator.SOLANA_SIGNATURE_REGEX, signature):
            raise ValidationError("Invalid transaction signature format")
        
        return signature
    
    @staticmethod
    def validate_game_type(game_type: str) -> str:
        """
        Validate game type
        """
        if not game_type:
            raise ValidationError("Game type cannot be empty")
        
        game_type = game_type.strip().lower()
        
        if game_type not in InputValidator.VALID_GAME_TYPES:
            raise ValidationError(f"Invalid game type. Must be one of: {', '.join(InputValidator.VALID_GAME_TYPES)}")
        
        return game_type
    
    @staticmethod
    def validate_wager_amount(amount: float, game_type: str) -> float:
        """
        Validate wager amount based on game type
        """
        if amount is None:
            raise ValidationError("Wager amount cannot be empty")
        
        if not isinstance(amount, (int, float)):
            raise ValidationError("Wager amount must be a number")
        
        if amount <= 0:
            raise ValidationError("Wager amount must be positive")
        
        # Get limits for game type
        limits = InputValidator.WAGER_LIMITS.get(game_type)
        if not limits:
            raise ValidationError(f"Unknown game type: {game_type}")
        
        if amount < limits["min"]:
            raise ValidationError(f"Minimum wager for {game_type} is {limits['min']} SOL")
        
        if amount > limits["max"]:
            raise ValidationError(f"Maximum wager for {game_type} is {limits['max']} SOL")
        
        return round(amount, 9)  # Round to 9 decimal places for SOL precision
    
    @staticmethod
    def validate_session_id(session_id: str) -> str:
        """
        Validate session ID format
        """
        if not session_id:
            raise ValidationError("Session ID cannot be empty")
        
        session_id = session_id.strip()
        
        # Check length (UUIDs are typically 36 characters with hyphens)
        if len(session_id) < 10 or len(session_id) > 50:
            raise ValidationError("Invalid session ID format")
        
        # Check for dangerous characters
        if not re.match(r'^[a-zA-Z0-9\-_]+$', session_id):
            raise ValidationError("Session ID contains invalid characters")
        
        return session_id
    
    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 100) -> str:
        """
        Sanitize string input to prevent injection attacks
        """
        if not input_str:
            return ""
        
        # Remove HTML tags
        input_str = re.sub(r'<[^>]+>', '', input_str)
        
        # Remove SQL injection attempts
        sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'EXEC']
        for keyword in sql_keywords:
            input_str = re.sub(keyword, '', input_str, flags=re.IGNORECASE)
        
        # Remove script tags and dangerous content
        input_str = re.sub(r'<script.*?</script>', '', input_str, flags=re.IGNORECASE | re.DOTALL)
        input_str = re.sub(r'javascript:', '', input_str, flags=re.IGNORECASE)
        
        # Trim to max length
        if len(input_str) > max_length:
            input_str = input_str[:max_length]
        
        return input_str.strip()
    
    @staticmethod
    def validate_hand_index(hand_index: int, max_hands: int = 5) -> int:
        """
        Validate hand index for blackjack
        """
        if hand_index is None:
            raise ValidationError("Hand index cannot be empty")
        
        if not isinstance(hand_index, int):
            raise ValidationError("Hand index must be an integer")
        
        if hand_index < 0:
            raise ValidationError("Hand index cannot be negative")
        
        if hand_index >= max_hands:
            raise ValidationError(f"Hand index cannot be greater than {max_hands - 1}")
        
        return hand_index
    
    @staticmethod
    def validate_card_positions(positions: list, max_cards: int = 5) -> list:
        """
        Validate card positions for video poker
        """
        if not isinstance(positions, list):
            raise ValidationError("Card positions must be a list")
        
        if len(positions) > max_cards:
            raise ValidationError(f"Cannot hold more than {max_cards} cards")
        
        valid_positions = []
        for pos in positions:
            if not isinstance(pos, int):
                raise ValidationError("Card positions must be integers")
            
            if pos < 0 or pos >= max_cards:
                raise ValidationError(f"Card position must be between 0 and {max_cards - 1}")
            
            valid_positions.append(pos)
        
        # Remove duplicates
        return list(set(valid_positions))

# Enhanced request models with validation
class ValidatedWagerRequest(BaseModel):
    player_wallet: str
    amount: float
    game_type: str
    session_id: str
    transaction_signature: Optional[str] = None
    
    @validator('player_wallet')
    def validate_wallet(cls, v):
        return InputValidator.validate_solana_address(v)
    
    @validator('game_type')
    def validate_game(cls, v):
        return InputValidator.validate_game_type(v)
    
    @validator('amount')
    def validate_amount(cls, v, values):
        game_type = values.get('game_type', 'blackjack')
        return InputValidator.validate_wager_amount(v, game_type)
    
    @validator('session_id')
    def validate_session(cls, v):
        return InputValidator.validate_session_id(v)
    
    @validator('transaction_signature')
    def validate_signature(cls, v):
        if v:
            return InputValidator.validate_transaction_signature(v)
        return v

class ValidatedGameResultRequest(BaseModel):
    session_id: str
    player_wallet: str
    game_type: str
    wager_amount: float
    payout_amount: float
    game_data: dict
    transaction_signature: Optional[str] = None
    
    @validator('session_id')
    def validate_session(cls, v):
        return InputValidator.validate_session_id(v)
    
    @validator('player_wallet')
    def validate_wallet(cls, v):
        return InputValidator.validate_solana_address(v)
    
    @validator('game_type')
    def validate_game(cls, v):
        return InputValidator.validate_game_type(v)
    
    @validator('wager_amount', 'payout_amount')
    def validate_amounts(cls, v):
        if v < 0:
            raise ValueError("Amounts cannot be negative")
        return round(v, 9)
    
    @validator('transaction_signature')
    def validate_signature(cls, v):
        if v:
            return InputValidator.validate_transaction_signature(v)
        return v

# Global validator instance
validator = InputValidator()