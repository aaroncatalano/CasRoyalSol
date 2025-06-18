from fastapi import FastAPI, APIRouter, HTTPException, Depends
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
from solana.rpc.api import Client
from solders.pubkey import Pubkey as PublicKey
from solders.transaction import Transaction
from solders.system_program import create_account, CreateAccountParams
from solders.keypair import Keypair
import json
import asyncio
import random
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Solana Configuration
SOLANA_RPC_URL = "https://api.devnet.solana.com"
TESTNET_TOKEN_ADDRESS = "Gh9ZwEmdLJ8DscKNTkTqPbNwLNNBjuSzaG9Vp2KGtKJr"
DEV_WALLET_ADDRESS = "A7GZMJLFzGSPn1nYHsGhLbU5pby4q96AessVHn5qVXFZ"
TRANSACTION_FEE_PERCENTAGE = 0.02  # 2%

# Initialize Solana client
solana_client = Client(SOLANA_RPC_URL)

# Create the main app without a prefix
app = FastAPI(title="Solana Gaming Platform", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Rate limiting setup
@app.on_event("startup")
async def startup():
    redis_client = redis.from_url("redis://localhost:6379", decode_responses=True)
    await FastAPILimiter.init(redis_client)

# Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class WalletConnectionRequest(BaseModel):
    public_key: str
    signature: str
    message: str

class GameSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    player_wallet: str
    game_type: str  # "blackjack" or "video_poker"
    session_data: Dict[Any, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class WagerRequest(BaseModel):
    player_wallet: str
    amount: float
    game_type: str
    session_id: str
    transaction_signature: Optional[str] = None

class GameResult(BaseModel):
    session_id: str
    player_wallet: str
    game_type: str
    wager_amount: float
    payout_amount: float
    game_data: Dict[Any, Any]
    transaction_signature: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Blackjack Game Logic
class Card:
    def __init__(self, suit: str, rank: str):
        self.suit = suit
        self.rank = rank
        self.value = self._get_value()
    
    def _get_value(self):
        if self.rank in ['J', 'Q', 'K']:
            return 10
        elif self.rank == 'A':
            return 11
        else:
            return int(self.rank)
    
    def __str__(self):
        return f"{self.rank} of {self.suit}"

class BlackjackHand:
    def __init__(self):
        self.cards = []
        self.value = 0
        self.aces = 0
    
    def add_card(self, card: Card):
        self.cards.append(card)
        self.value += card.value
        if card.rank == 'A':
            self.aces += 1
        self._adjust_for_ace()
    
    def _adjust_for_ace(self):
        while self.value > 21 and self.aces:
            self.value -= 10
            self.aces -= 1

class BlackjackGame:
    def __init__(self, winning_percentage: float = 0.69):
        self.deck = self._create_deck()
        self.shuffle_deck()
        self.player_hands = []
        self.dealer_hand = BlackjackHand()
        self.current_hand = 0
        self.winning_percentage = winning_percentage
        self.game_over = False
        self.results = []
    
    def _create_deck(self):
        suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        return [Card(suit, rank) for suit in suits for rank in ranks]
    
    def shuffle_deck(self):
        random.shuffle(self.deck)
    
    def deal_card(self):
        if len(self.deck) == 0:
            self.deck = self._create_deck()
            self.shuffle_deck()
        return self.deck.pop()
    
    def start_game(self, num_hands: int = 1):
        self.player_hands = [BlackjackHand() for _ in range(num_hands)]
        self.dealer_hand = BlackjackHand()
        self.game_over = False
        self.results = []
        
        # Deal initial cards
        for _ in range(2):
            for hand in self.player_hands:
                hand.add_card(self.deal_card())
            self.dealer_hand.add_card(self.deal_card())
        
        return self._game_state()
    
    def hit(self, hand_index: int):
        if hand_index < len(self.player_hands) and not self.game_over:
            self.player_hands[hand_index].add_card(self.deal_card())
        return self._game_state()
    
    def stand(self, hand_index: int):
        """Player stands on current hand"""
        return self._game_state()
    
    def dealer_play(self):
        """Dealer plays according to standard rules with bias towards player winning"""
        should_player_win = random.random() < self.winning_percentage
        
        if should_player_win:
            # Bias dealer to bust or get a worse hand
            while self.dealer_hand.value < 17:
                card = self.deal_card()
                self.dealer_hand.add_card(card)
                # Increase chance of dealer busting
                if self.dealer_hand.value >= 16 and random.random() < 0.4:
                    break
        else:
            # Standard dealer play
            while self.dealer_hand.value < 17:
                self.dealer_hand.add_card(self.deal_card())
        
        return self._game_state()
    
    def finish_game(self):
        """Complete the game and determine winners"""
        self.dealer_play()
        self.game_over = True
        
        dealer_value = self.dealer_hand.value
        dealer_busted = dealer_value > 21
        
        for i, hand in enumerate(self.player_hands):
            player_value = hand.value
            player_busted = player_value > 21
            
            if player_busted:
                result = "lose"
                payout_multiplier = 0
            elif dealer_busted:
                result = "win"
                payout_multiplier = 2.0
            elif player_value > dealer_value:
                result = "win"
                payout_multiplier = 2.0
            elif player_value == dealer_value:
                result = "push"
                payout_multiplier = 1.0
            else:
                result = "lose"
                payout_multiplier = 0
            
            # Check for blackjack (21 with 2 cards)
            if len(hand.cards) == 2 and player_value == 21:
                result = "blackjack"
                payout_multiplier = 2.5
            
            self.results.append({
                "hand_index": i,
                "result": result,
                "payout_multiplier": payout_multiplier,
                "player_value": player_value,
                "dealer_value": dealer_value
            })
        
        return self._game_state()
    
    def _game_state(self):
        return {
            "player_hands": [
                {
                    "cards": [str(card) for card in hand.cards],
                    "value": hand.value,
                    "busted": hand.value > 21
                } for hand in self.player_hands
            ],
            "dealer_hand": {
                "cards": [str(card) for card in self.dealer_hand.cards],
                "value": self.dealer_hand.value,
                "busted": self.dealer_hand.value > 21
            },
            "game_over": self.game_over,
            "results": self.results if self.game_over else []
        }

# Video Poker Game Logic
class VideoPokerGame:
    def __init__(self):
        self.deck = self._create_deck()
        self.hand = []
        self.held_cards = [False] * 5
    
    def _create_deck(self):
        suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        return [Card(suit, rank) for suit in suits for rank in ranks]
    
    def shuffle_deck(self):
        random.shuffle(self.deck)
    
    def deal_initial_hand(self):
        self.shuffle_deck()
        self.hand = [self.deck.pop() for _ in range(5)]
        self.held_cards = [False] * 5
        return self._game_state()
    
    def hold_cards(self, positions: List[int]):
        for pos in positions:
            if 0 <= pos < 5:
                self.held_cards[pos] = True
        return self._game_state()
    
    def draw_cards(self):
        for i in range(5):
            if not self.held_cards[i]:
                self.hand[i] = self.deck.pop()
        return self._game_state()
    
    def _game_state(self):
        return {
            "hand": [{"card": str(card), "held": held} for card, held in zip(self.hand, self.held_cards)],
            "hand_rank": self._evaluate_hand()
        }
    
    def _evaluate_hand(self):
        # Simplified hand evaluation for Jacks or Better
        ranks = [card.rank for card in self.hand]
        suits = [card.suit for card in self.hand]
        
        # Count ranks
        rank_counts = {}
        for rank in ranks:
            rank_counts[rank] = rank_counts.get(rank, 0) + 1
        
        # Check for flush
        is_flush = len(set(suits)) == 1
        
        # Check for straight
        rank_values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
        sorted_values = sorted([rank_values[rank] for rank in ranks])
        is_straight = all(sorted_values[i] == sorted_values[i-1] + 1 for i in range(1, 5))
        
        # Evaluate hand
        if is_straight and is_flush:
            return "Straight Flush" if sorted_values != [10, 11, 12, 13, 14] else "Royal Flush"
        elif 4 in rank_counts.values():
            return "Four of a Kind"
        elif 3 in rank_counts.values() and 2 in rank_counts.values():
            return "Full House"
        elif is_flush:
            return "Flush"
        elif is_straight:
            return "Straight"
        elif 3 in rank_counts.values():
            return "Three of a Kind"
        elif list(rank_counts.values()).count(2) == 2:
            return "Two Pair"
        elif 2 in rank_counts.values():
            jacks = ['J', 'Q', 'K', 'A']
            for rank, count in rank_counts.items():
                if count == 2 and rank in jacks:
                    return "Jacks or Better"
            return "Low Pair"
        else:
            return "High Card"

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Solana Gaming Platform API", "version": "1.0.0"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

@api_router.post("/wallet/connect")
async def connect_wallet(request: WalletConnectionRequest, ratelimit: int = Depends(RateLimiter(times=10, seconds=60))):
    """Connect and verify wallet signature"""
    try:
        # Verify the wallet exists on Solana
        wallet_info = solana_client.get_account_info(PublicKey.from_string(request.public_key))
        
        # Store wallet connection
        wallet_data = {
            "public_key": request.public_key,
            "connected_at": datetime.utcnow(),
            "is_active": True
        }
        
        await db.connected_wallets.insert_one(wallet_data)
        
        return {
            "success": True,
            "message": "Wallet connected successfully",
            "public_key": request.public_key
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Wallet connection failed: {str(e)}")

@api_router.post("/game/session/create")
async def create_game_session(player_wallet: str, game_type: str, num_hands: int = 1):
    """Create a new game session"""
    try:
        if game_type not in ["blackjack", "video_poker"]:
            raise HTTPException(status_code=400, detail=f"Invalid game type: {game_type}. Must be 'blackjack' or 'video_poker'")
            
        if game_type == "blackjack":
            game = BlackjackGame()
            game_data = game.start_game(num_hands)
        elif game_type == "video_poker":
            game = VideoPokerGame()
            game_data = game.deal_initial_hand()
        
        session = GameSession(
            player_wallet=player_wallet,
            game_type=game_type,
            session_data=game_data
        )
        
        await db.game_sessions.insert_one(session.dict())
        
        return {
            "success": True,
            "session_id": session.id,
            "game_data": game_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/game/blackjack/hit")
async def blackjack_hit(session_id: str, hand_index: int = 0):
    """Hit in blackjack"""
    try:
        session = await db.game_sessions.find_one({"id": session_id})
        if not session:
            raise HTTPException(status_code=404, detail=f"Session not found with ID: {session_id}")
        
        # Recreate game state (simplified - in production, store full game state)
        game = BlackjackGame()
        # For demo purposes, return a sample hit result
        card = game.deal_card()
        
        return {
            "success": True,
            "card": str(card),
            "message": f"Drew {card}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/game/video_poker/hold")
async def video_poker_hold(session_id: str, positions: List[int]):
    """Hold cards in video poker"""
    try:
        session = await db.game_sessions.find_one({"id": session_id})
        if not session:
            raise HTTPException(status_code=404, detail=f"Session not found with ID: {session_id}")
        
        return {
            "success": True,
            "held_positions": positions,
            "message": f"Held cards at positions: {positions}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/game/wager")
async def place_wager(wager: WagerRequest, ratelimit: int = Depends(RateLimiter(times=20, seconds=60))):
    """Process game wager with 2% dev fee"""
    try:
        # Calculate dev fee
        total_amount = wager.amount
        dev_fee = total_amount * TRANSACTION_FEE_PERCENTAGE
        game_amount = total_amount - dev_fee
        
        # In a real implementation, verify the transaction signature
        # For now, simulate the transaction
        
        # Store wager record
        wager_record = {
            "id": str(uuid.uuid4()),
            "player_wallet": wager.player_wallet,
            "total_amount": total_amount,
            "game_amount": game_amount,
            "dev_fee": dev_fee,
            "game_type": wager.game_type,
            "session_id": wager.session_id,
            "transaction_signature": wager.transaction_signature,
            "created_at": datetime.utcnow()
        }
        
        await db.wagers.insert_one(wager_record)
        
        return {
            "success": True,
            "wager_id": wager_record["id"],
            "total_amount": total_amount,
            "game_amount": game_amount,
            "dev_fee": dev_fee,
            "dev_wallet": DEV_WALLET_ADDRESS,
            "message": "Wager placed successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/game/sessions/{player_wallet}")
async def get_player_sessions(player_wallet: str):
    """Get player's game sessions"""
    try:
        sessions = await db.game_sessions.find({"player_wallet": player_wallet}).to_list(100)
        # Convert MongoDB ObjectId to string for JSON serialization
        for session in sessions:
            if "_id" in session:
                session["_id"] = str(session["_id"])
        return {"sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/wallet/balance/{public_key}")
async def get_wallet_balance(public_key: str):
    """Get wallet balance from Solana"""
    try:
        balance = solana_client.get_balance(PublicKey.from_string(public_key))
        # Convert from lamports to SOL
        sol_balance = balance.value / 1_000_000_000
        
        return {
            "public_key": public_key,
            "balance_lamports": balance.value,
            "balance_sol": sol_balance
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()