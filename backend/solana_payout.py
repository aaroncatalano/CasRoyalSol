import logging
from typing import Dict, Any, Optional
from solana.rpc.api import Client
from solana.rpc.commitment import Commitment
import base58
import os
from dotenv import load_dotenv
import asyncio
import motor.motor_asyncio
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/var/log/solana_payouts.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("solana_payout")

class SolanaPayoutService:
    def __init__(self):
        self.rpc_url = os.getenv("SOLANA_RPC_URL", "https://api.devnet.solana.com")
        self.client = Client(self.rpc_url)
        self.house_private_key = os.getenv("HOUSE_WALLET_PRIVATE_KEY")
        
        if not self.house_private_key:
            raise ValueError("HOUSE_WALLET_PRIVATE_KEY not found in environment variables")
        
        # Import the right classes based on available library
        try:
            # Try newer library imports first
            from solders.keypair import Keypair
            from solders.pubkey import Pubkey as PublicKey
            from solders.system_program import TransferParams, transfer
            
            private_key_bytes = base58.b58decode(self.house_private_key)
            self.house_keypair = Keypair.from_bytes(private_key_bytes)
            
            self.PublicKey = PublicKey
            self.TransferParams = TransferParams
            self.transfer = transfer
            
            # Use legacy transaction for compatibility with solana-py client
            from solana.transaction import Transaction
            self.Transaction = Transaction
            
        except ImportError:
            # Fallback to older library imports
            from solana.keypair import Keypair
            from solana.publickey import PublicKey
            from solana.system_program import TransferParams, transfer
            from solana.transaction import Transaction
            
            # Try to decode the private key (it's in base58 format)
            private_key_bytes = base58.b58decode(self.house_private_key)
            self.house_keypair = Keypair.from_secret_key(private_key_bytes)
            
            self.PublicKey = PublicKey
            self.TransferParams = TransferParams
            self.transfer = transfer
            self.Transaction = Transaction
        
        # MongoDB setup
        mongo_uri = os.getenv("MONGO_URL", "mongodb://localhost:27017")
        self.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
        self.db = self.mongo_client.solana_gaming
        self.payouts_collection = self.db.winner_payouts
        
        logger.info(f"Initialized Solana Payout Service with house wallet: {self.house_keypair.pubkey()}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def send_winner_payout(
        self, 
        winner_address: str, 
        amount_sol: float, 
        game_id: str = None,
        session_id: str = None
    ) -> Dict[str, Any]:
        """
        Send SOL payout to winner with retry logic and comprehensive logging
        """
        payout_record = {
            "winner_address": winner_address,
            "amount_sol": amount_sol,
            "amount_lamports": int(amount_sol * 1e9),
            "game_id": game_id,
            "session_id": session_id,
            "timestamp": datetime.utcnow(),
            "status": "initiated",
            "attempts": 0,
            "house_wallet": str(self.house_keypair.pubkey())
        }
        
        try:
            # Insert initial record
            result = await self.payouts_collection.insert_one(payout_record)
            payout_id = result.inserted_id
            
            logger.info(f"Initiating payout: {amount_sol} SOL to {winner_address} (Payout ID: {payout_id})")
            
            # Validate recipient address
            try:
                if hasattr(self.PublicKey, 'from_string'):
                    recipient_pubkey = self.PublicKey.from_string(winner_address)
                else:
                    recipient_pubkey = self.PublicKey(winner_address)
            except Exception as e:
                raise ValueError(f"Invalid recipient address: {winner_address}")
            
            # Check house wallet balance
            balance_response = self.client.get_balance(self.house_keypair.pubkey())
            
            # Handle different response formats
            if hasattr(balance_response, 'value'):
                house_balance_lamports = balance_response.value
            else:
                house_balance_lamports = balance_response["result"]["value"]
                
            house_balance_sol = house_balance_lamports / 1e9
            
            required_lamports = int(amount_sol * 1e9)
            
            # Add buffer for transaction fees
            fee_buffer = 5000
            if house_balance_lamports < (required_lamports + fee_buffer):
                raise ValueError(f"Insufficient house wallet balance. Required: {amount_sol} SOL, Available: {house_balance_sol} SOL")
            
            logger.info(f"House wallet balance: {house_balance_sol} SOL")
            
            # Create transfer instruction
            transfer_instruction = self.transfer(
                self.TransferParams(
                    from_pubkey=self.house_keypair.pubkey(),
                    to_pubkey=recipient_pubkey,
                    lamports=required_lamports
                )
            )
            
            # Get recent blockhash
            recent_blockhash_response = self.client.get_latest_blockhash()
            if hasattr(recent_blockhash_response, 'value'):
                recent_blockhash = recent_blockhash_response.value.blockhash
            else:
                recent_blockhash = recent_blockhash_response["result"]["value"]["blockhash"]
            
            # Create message with the transfer instruction
            from solders.message import Message
            
            message = Message.new_with_blockhash(
                [transfer_instruction],
                self.house_keypair.pubkey(),
                recent_blockhash
            )
            
            # Create transaction from message and sign it
            transaction = self.Transaction([self.house_keypair], message, recent_blockhash)
            
            # Update attempts
            await self.payouts_collection.update_one(
                {"_id": payout_id},
                {"$inc": {"attempts": 1}, "$set": {"status": "processing"}}
            )
            
            # Send transaction
            response = self.client.send_transaction(transaction)
            
            # Handle different response formats
            if hasattr(response, 'value'):
                signature = str(response.value)
            else:
                signature = response["result"]
            
            if signature:
                # Wait for confirmation
                await asyncio.sleep(2)
                
                # Transaction successful
                await self.payouts_collection.update_one(
                    {"_id": payout_id},
                    {
                        "$set": {
                            "status": "completed",
                            "signature": signature,
                            "completed_at": datetime.utcnow()
                        }
                    }
                )
                
                logger.info(f"Payout successful! Signature: {signature}")
                
                return {
                    "success": True,
                    "signature": signature,
                    "amount_sol": amount_sol,
                    "recipient": winner_address,
                    "payout_id": str(payout_id),
                    "explorer_url": f"https://explorer.solana.com/tx/{signature}?cluster=devnet"
                }
            else:
                raise Exception("Failed to get transaction signature from response")
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Payout failed: {error_msg}", exc_info=True)
            
            # Update record with error
            if 'payout_id' in locals():
                await self.payouts_collection.update_one(
                    {"_id": payout_id},
                    {
                        "$set": {
                            "status": "failed",
                            "error": error_msg,
                            "failed_at": datetime.utcnow()
                        }
                    }
                )
            
            return {
                "success": False,
                "error": error_msg,
                "payout_id": str(payout_id) if 'payout_id' in locals() else None
            }

    async def get_payout_status(self, payout_id: str) -> Dict[str, Any]:
        """Get status of a specific payout"""
        from bson import ObjectId
        
        try:
            payout = await self.payouts_collection.find_one({"_id": ObjectId(payout_id)})
            if payout:
                payout["_id"] = str(payout["_id"])
                return payout
            else:
                return {"error": "Payout not found"}
        except Exception as e:
            return {"error": str(e)}

    def get_house_wallet_balance(self) -> Dict[str, Any]:
        """Get current house wallet balance"""
        try:
            balance_response = self.client.get_balance(self.house_keypair.pubkey())
            
            # Handle different response formats
            if hasattr(balance_response, 'value'):
                balance_lamports = balance_response.value
            else:
                balance_lamports = balance_response["result"]["value"]
                
            balance_sol = balance_lamports / 1e9
            
            return {
                "address": str(self.house_keypair.pubkey()),
                "balance_sol": balance_sol,
                "balance_lamports": balance_lamports
            }
        except Exception as e:
            logger.error(f"Error getting house wallet balance: {str(e)}")
            return {"error": str(e)}

    async def get_payout_history(self, limit: int = 50) -> Dict[str, Any]:
        """Get recent payout history"""
        try:
            cursor = self.payouts_collection.find().sort("timestamp", -1).limit(limit)
            payouts = await cursor.to_list(length=limit)
            
            for payout in payouts:
                payout["_id"] = str(payout["_id"])
            
            return {"payouts": payouts}
        except Exception as e:
            return {"error": str(e)}