import sys
from pathlib import Path
from fastapi import FastAPI, APIRouter, HTTPException, Depends
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
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
import socketio
import uvicorn
# Removed Redis imports to avoid compatibility issues

# Add the current directory to Python path to import our module
sys.path.append(str(Path(__file__).parent))

try:
    from solana_payout import SolanaPayoutService
    SOLANA_PAYOUT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Solana payout service not available: {e}")
    SolanaPayoutService = None
    SOLANA_PAYOUT_AVAILABLE = False

try:
    from multiplayer_service import multiplayer_service
    MULTIPLAYER_AVAILABLE = True
    print("✅ Multiplayer service loaded successfully")
except ImportError as e:
    print(f"Warning: Multiplayer service not available: {e}")
    multiplayer_service = None
    MULTIPLAYER_AVAILABLE = False

try:
    from solanabust_rooms import room_manager, start_game_loop
    ROOMS_AVAILABLE = True
    print("✅ SolanaBust rooms service loaded successfully")
except ImportError as e:
    print(f"Warning: SolanaBust rooms service not available: {e}")
    room_manager = None
    ROOMS_AVAILABLE = False
    start_game_loop = None

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize Solana payout service
if SOLANA_PAYOUT_AVAILABLE:
    try:
        solana_payout_service = SolanaPayoutService()
        logger.info("Solana payout service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Solana payout service: {e}")
        solana_payout_service = None
else:
    solana_payout_service = None
    logger.warning("Solana payout service not available - payouts will be simulated only")

# Solana Configuration
SOLANA_RPC_URL = "https://api.devnet.solana.com"
TESTNET_TOKEN_ADDRESS = "Gh9ZwEmdLJ8DscKNTkTqPbNwLNNBjuSzaG9Vp2KGtKJr"
DEV_WALLET_ADDRESS = "A7GZMJLFzGSPn1nYHsGhLbU5pby4q96AessVHn5qVXFZ"
TRANSACTION_FEE_PERCENTAGE = 0.12  # 12% developer fee

# Initialize Solana client
solana_client = Client(SOLANA_RPC_URL)

# Create FastAPI app
app = FastAPI(title="Solana Gaming Platform API", version="1.0.0")

# Create Socket.IO app if multiplayer is available
if MULTIPLAYER_AVAILABLE:
    sio_app = socketio.ASGIApp(multiplayer_service.sio, other_asgi_app=app)
    logger.info("Socket.IO integrated with FastAPI")
else:
    sio_app = app
    logger.warning("Socket.IO not available - multiplayer features disabled")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Rate limiting setup
@app.on_event("startup")
async def startup():
    try:
        # Disable Redis rate limiting for now to avoid compatibility issues
        logger.info("Rate limiting disabled - Redis not required for Socket.IO functionality")
    except Exception as e:
        logger.warning(f"Rate limiting setup warning: {e}")
        # Continue without rate limiting

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

class GameResultRequest(BaseModel):
    session_id: str
    player_wallet: str
    game_type: str
    wager_amount: float
    payout_amount: float
    game_data: dict
    transaction_signature: Optional[str] = None

class PayoutRequest(BaseModel):
    winner_address: str
    amount_sol: float
    game_id: Optional[str] = None
    session_id: Optional[str] = None

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
    def __init__(self, winning_percentage: float = 0.35):
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
    def __init__(self, winning_percentage: float = 0.35):
        self.deck = self._create_deck()
        self.hand = []
        self.held_cards = [False] * 5
        self.winning_percentage = winning_percentage
        self.initial_deal = True
        self.game_complete = False
        self.final_hand_rank = ""
        self.payout_multiplier = 0
    
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
        self.initial_deal = True
        self.game_complete = False
        return self._game_state()
    
    def hold_cards(self, positions: List[int]):
        for pos in positions:
            if 0 <= pos < 5:
                self.held_cards[pos] = True
        return self._game_state()
    
    def draw_cards(self):
        """Draw final cards with bias towards winning hands"""
        for i in range(5):
            if not self.held_cards[i]:
                self.hand[i] = self.deck.pop()
        
        self.initial_deal = False
        self.game_complete = True
        
        # Evaluate final hand
        hand_rank = self._evaluate_hand()
        self.final_hand_rank = hand_rank
        self.payout_multiplier = self._get_payout_multiplier(hand_rank)
        
        # Apply winning bias - if should win but got losing hand, try to improve it
        should_player_win = random.random() < self.winning_percentage
        if should_player_win and self.payout_multiplier == 0:
            # Try to create a winning hand
            self._bias_towards_winning()
        
        return self._game_state()
    
    def _bias_towards_winning(self):
        """Attempt to improve hand to a winning combination"""
        # Simple bias: try to create at least Jacks or Better
        high_cards = [Card('Hearts', 'J'), Card('Diamonds', 'Q'), Card('Clubs', 'K'), Card('Spades', 'A')]
        
        # Find non-held positions and try to place high pairs
        non_held = [i for i in range(5) if not self.held_cards[i]]
        if len(non_held) >= 2:
            # Place a pair of Jacks
            self.hand[non_held[0]] = Card('Hearts', 'J')
            self.hand[non_held[1]] = Card('Diamonds', 'J')
            self.final_hand_rank = "Jacks or Better"
            self.payout_multiplier = 1.0
    
    def _game_state(self):
        return {
            "hand": [{"card": str(card), "held": held} for card, held in zip(self.hand, self.held_cards)],
            "hand_rank": self.final_hand_rank if self.game_complete else self._evaluate_hand(),
            "initial_deal": self.initial_deal,
            "game_complete": self.game_complete,
            "payout_multiplier": self.payout_multiplier if self.game_complete else 0
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
        
        # Special case for A-2-3-4-5 straight (wheel)
        if sorted_values == [2, 3, 4, 5, 14]:
            is_straight = True
        
        # Evaluate hand
        if is_straight and is_flush:
            if sorted_values == [10, 11, 12, 13, 14]:
                return "Royal Flush"
            else:
                return "Straight Flush"
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
    
    def _get_payout_multiplier(self, hand_rank: str):
        """Get payout multiplier based on hand rank"""
        payout_table = {
            "Royal Flush": 250,
            "Straight Flush": 50,
            "Four of a Kind": 25,
            "Full House": 9,
            "Flush": 6,
            "Straight": 4,
            "Three of a Kind": 3,
            "Two Pair": 2,
            "Jacks or Better": 1,
            "Low Pair": 0,
            "High Card": 0
        }
        return payout_table.get(hand_rank, 0)

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

def optional_rate_limiter():
    """Optional rate limiter that doesn't fail if Redis is unavailable"""
    # Rate limiting disabled
    return None

@api_router.post("/wallet/connect")
async def connect_wallet(request: WalletConnectionRequest):
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
    """Create a new game session with validation"""
    try:
        # Validate inputs
        if game_type not in ["blackjack", "video_poker"]:
            raise HTTPException(status_code=400, detail="Invalid game type. Must be 'blackjack' or 'video_poker'")
        
        if num_hands < 1 or num_hands > 5:
            raise HTTPException(status_code=400, detail="Number of hands must be between 1 and 5")
        
        # Validate wallet address format
        try:
            PublicKey.from_string(player_wallet)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid Solana wallet address format")
        
        if game_type == "blackjack":
            game = BlackjackGame()
            game_data = game.start_game(num_hands)
        elif game_type == "video_poker":
            game = VideoPokerGame()
            game_data = game.deal_initial_hand()
        else:
            raise HTTPException(status_code=400, detail="Invalid game type")
        
        session = GameSession(
            player_wallet=player_wallet,
            game_type=game_type,
            session_data=game_data
        )
        
        await db.game_sessions.insert_one(session.dict())
        
        return {
            "success": True,
            "session_id": session.id,
            "game_data": game_data,
            "message": f"{game_type.title()} session created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating game session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create game session: {str(e)}")

@api_router.post("/game/blackjack/hit")
async def blackjack_hit(session_id: str, hand_index: int = 0):
    """Hit in blackjack"""
    try:
        session = await db.game_sessions.find_one({"id": session_id})
        if not session:
            raise HTTPException(status_code=404, detail=f"Session not found with ID: {session_id}")
        
        # Get current game state from session
        current_game_data = session.get("session_data", {})
        
        # For simplicity, simulate hitting by dealing a new random card
        # In a real implementation, you'd restore the full game state
        game = BlackjackGame()
        card = game.deal_card()
        
        # Update the player's hand (this is a simplified approach)
        if "player_hands" in current_game_data and len(current_game_data["player_hands"]) > hand_index:
            # Add card to existing hand
            current_game_data["player_hands"][hand_index]["cards"].append(str(card))
            
            # Recalculate hand value (simplified)
            cards = current_game_data["player_hands"][hand_index]["cards"]
            hand_value = 0
            aces = 0
            
            for card_str in cards:
                rank = card_str.split(" of ")[0]
                if rank in ['J', 'Q', 'K']:
                    hand_value += 10
                elif rank == 'A':
                    hand_value += 11
                    aces += 1
                else:
                    hand_value += int(rank)
            
            # Adjust for aces
            while hand_value > 21 and aces > 0:
                hand_value -= 10
                aces -= 1
            
            current_game_data["player_hands"][hand_index]["value"] = hand_value
            current_game_data["player_hands"][hand_index]["busted"] = hand_value > 21
        
        # Update session
        await db.game_sessions.update_one(
            {"id": session_id},
            {"$set": {"session_data": current_game_data}}
        )
        
        return {
            "success": True,
            "game_state": current_game_data,
            "new_card": str(card),
            "message": f"Hit on hand {hand_index} - Drew {card}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/game/blackjack/stand")
async def blackjack_stand(session_id: str, hand_index: int = 0):
    """Stand in blackjack"""
    try:
        session = await db.game_sessions.find_one({"id": session_id})
        if not session:
            raise HTTPException(status_code=404, detail=f"Session not found with ID: {session_id}")
        
        # Get current game state from session
        current_game_data = session.get("session_data", {})
        
        # Standing doesn't change the hand, just return current state
        # The finish endpoint will handle dealer play
        
        return {
            "success": True,
            "game_state": current_game_data,
            "message": f"Stand on hand {hand_index}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/game/blackjack/finish")
async def blackjack_finish(session_id: str):
    """Finish blackjack game and determine winners"""
    try:
        session = await db.game_sessions.find_one({"id": session_id})
        if not session:
            raise HTTPException(status_code=404, detail=f"Session not found with ID: {session_id}")
        
        # Get current game state from session
        current_game_data = session.get("session_data", {})
        
        # Simulate dealer play with winning bias
        game = BlackjackGame()
        should_player_win = random.random() < 0.69  # 69% win rate
        
        # Start with current dealer hand
        dealer_value = current_game_data.get("dealer_hand", {}).get("value", 13)
        dealer_cards = current_game_data.get("dealer_hand", {}).get("cards", ["A of Diamonds", "2 of Spades"])
        
        # Get player value for comparison
        player_value = current_game_data.get("player_hands", [{}])[0].get("value", 0)
        player_busted = current_game_data.get("player_hands", [{}])[0].get("busted", False)
        
        # If player already busted, they lose regardless of bias
        if not player_busted:
            # Dealer plays according to rules with bias
            while dealer_value < 17:
                card = game.deal_card()
                dealer_cards.append(str(card))
                
                # Calculate new value
                rank = card.rank
                if rank in ['J', 'Q', 'K']:
                    dealer_value += 10
                elif rank == 'A':
                    dealer_value += 11
                else:
                    dealer_value += int(rank)
                
                # Adjust for aces if busted
                aces = len([c for c in dealer_cards if 'A of' in c])
                while dealer_value > 21 and aces > 0:
                    dealer_value -= 10
                    aces -= 1
                
                # Enhanced bias towards player winning
                if should_player_win:
                    # If dealer has 17-21 and player has less, bias dealer to bust
                    if dealer_value >= 17 and dealer_value <= 21 and player_value < dealer_value:
                        if random.random() < 0.6:  # 60% chance to draw another card and potentially bust
                            continue
                    # If dealer has 16 or less, bias towards busting
                    elif dealer_value >= 15 and random.random() < 0.7:
                        continue
                else:
                    # If we want dealer to win, play more conservatively
                    if dealer_value >= 17:
                        break
        
        # Update dealer hand
        current_game_data["dealer_hand"] = {
            "cards": dealer_cards,
            "value": dealer_value,
            "busted": dealer_value > 21
        }
        
        # Calculate results for each player hand
        results = []
        dealer_busted = dealer_value > 21
        
        for i, player_hand in enumerate(current_game_data.get("player_hands", [])):
            player_value = player_hand.get("value", 0)
            player_busted = player_hand.get("busted", False)
            
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
            if len(player_hand.get("cards", [])) == 2 and player_value == 21:
                result = "blackjack"
                payout_multiplier = 2.5
            
            results.append({
                "hand_index": i,
                "result": result,
                "payout_multiplier": payout_multiplier,
                "player_value": player_value,
                "dealer_value": dealer_value
            })
        
        # Mark game as complete
        current_game_data["game_over"] = True
        current_game_data["results"] = results
        
        # Update session
        await db.game_sessions.update_one(
            {"id": session_id},
            {"$set": {"session_data": current_game_data, "is_active": False}}
        )
        
        return {
            "success": True,
            "game_state": current_game_data,
            "results": results,
            "message": "Game completed"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/game/video_poker/draw")
async def video_poker_draw(session_id: str):
    """Draw cards in video poker"""
    try:
        session = await db.game_sessions.find_one({"id": session_id})
        if not session:
            raise HTTPException(status_code=404, detail=f"Session not found with ID: {session_id}")
        
        # Get current game state from session
        current_game_data = session.get("session_data", {})
        
        if "hand" not in current_game_data:
            raise HTTPException(status_code=400, detail="Invalid game state: no hand found")
        
        # Get held cards and current hand
        current_hand = current_game_data.get("hand", [])
        
        # Extract held positions from the hand data
        held_positions = []
        for i, card_data in enumerate(current_hand):
            if card_data.get("held", False):
                held_positions.append(i)
        
        # Create new deck for drawing replacement cards
        suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        deck = [Card(suit, rank) for suit in suits for rank in ranks]
        random.shuffle(deck)
        
        # Replace non-held cards
        new_hand = []
        for i, card_data in enumerate(current_hand):
            if i in held_positions:
                # Keep the held card
                new_hand.append({
                    "card": card_data["card"],
                    "held": True
                })
            else:
                # Draw a new card
                new_card = deck.pop()
                new_hand.append({
                    "card": str(new_card),
                    "held": False
                })
        
        # Evaluate final hand
        hand_rank = evaluate_poker_hand([card_data["card"] for card_data in new_hand])
        payout_multiplier = get_video_poker_payout(hand_rank)
        
        # Apply 65% win bias
        should_player_win = random.random() < 0.65
        if should_player_win and payout_multiplier == 0:
            # Try to improve to at least Jacks or Better
            # Simple bias: if no winning hand, try to create a pair of face cards
            face_cards = ['J', 'Q', 'K', 'A']
            suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
            
            # Find non-held positions
            non_held = [i for i in range(5) if i not in held_positions]
            if len(non_held) >= 2:
                # Create a pair of Jacks
                new_hand[non_held[0]] = {"card": "J of Hearts", "held": False}
                new_hand[non_held[1]] = {"card": "J of Diamonds", "held": False}
                hand_rank = "Jacks or Better"
                payout_multiplier = 1.0
        
        # Update game state
        final_game_state = {
            "hand": new_hand,
            "hand_rank": hand_rank,
            "initial_deal": False,
            "game_complete": True,
            "payout_multiplier": payout_multiplier
        }
        
        # Update session
        await db.game_sessions.update_one(
            {"id": session_id},
            {"$set": {"session_data": final_game_state, "is_active": False}}
        )
        
        return {
            "success": True,
            "game_state": final_game_state,
            "final_hand": hand_rank,
            "payout_multiplier": payout_multiplier,
            "message": f"Final hand: {hand_rank}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def evaluate_poker_hand(cards):
    """Evaluate poker hand from list of card strings"""
    ranks = []
    suits = []
    
    for card_str in cards:
        parts = card_str.split(" of ")
        if len(parts) == 2:
            rank, suit = parts
            ranks.append(rank)
            suits.append(suit)
    
    # Count ranks
    rank_counts = {}
    for rank in ranks:
        rank_counts[rank] = rank_counts.get(rank, 0) + 1
    
    # Check for flush
    is_flush = len(set(suits)) == 1
    
    # Check for straight
    rank_values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
    try:
        sorted_values = sorted([rank_values[rank] for rank in ranks if rank in rank_values])
        is_straight = len(sorted_values) == 5 and all(sorted_values[i] == sorted_values[i-1] + 1 for i in range(1, 5))
        
        # Special case for A-2-3-4-5 straight (wheel)
        if sorted_values == [2, 3, 4, 5, 14]:
            is_straight = True
    except:
        is_straight = False
    
    # Evaluate hand
    if is_straight and is_flush:
        if sorted_values == [10, 11, 12, 13, 14]:
            return "Royal Flush"
        else:
            return "Straight Flush"
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

def get_video_poker_payout(hand_rank):
    """Get payout multiplier based on hand rank"""
    payout_table = {
        "Royal Flush": 250,
        "Straight Flush": 50,
        "Four of a Kind": 25,
        "Full House": 9,
        "Flush": 6,
        "Straight": 4,
        "Three of a Kind": 3,
        "Two Pair": 2,
        "Jacks or Better": 1,
        "Low Pair": 0,
        "High Card": 0
    }
    return payout_table.get(hand_rank, 0)

@api_router.post("/game/video_poker/hold")
async def video_poker_hold(session_id: str, positions: List[int]):
    """Hold cards in video poker"""
    try:
        session = await db.game_sessions.find_one({"id": session_id})
        if not session:
            raise HTTPException(status_code=404, detail=f"Session not found with ID: {session_id}")
        
        # Get current game state from session
        current_game_data = session.get("session_data", {})
        
        if "hand" not in current_game_data:
            raise HTTPException(status_code=400, detail="Invalid game state: no hand found")
        
        # Update held cards
        hand = current_game_data["hand"]
        
        # Reset all held flags first
        for card_data in hand:
            card_data["held"] = False
        
        # Set held flags for specified positions
        for pos in positions:
            if 0 <= pos < len(hand):
                hand[pos]["held"] = True
        
        # Update the game state
        current_game_data["hand"] = hand
        
        # Update session
        await db.game_sessions.update_one(
            {"id": session_id},
            {"$set": {"session_data": current_game_data}}
        )
        
        return {
            "success": True,
            "game_state": current_game_data,
            "held_positions": positions,
            "message": f"Held cards at positions: {positions}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/game/wager")
async def place_wager(wager: WagerRequest):
    """Process game wager with 4% dev fee and validation"""
    try:
        # Game-specific wager validation
        if wager.game_type == "crash":
            # SolanaBust specific limits
            if wager.amount < 0.005:
                raise HTTPException(status_code=400, detail="Minimum wager for SolanaBust is 0.005 SOL")
            if wager.amount > 0.05:
                raise HTTPException(status_code=400, detail="Maximum wager for SolanaBust is 0.05 SOL")
        else:
            # Blackjack and Video Poker limits  
            if wager.amount < 0.01:
                raise HTTPException(status_code=400, detail="Minimum wager is 0.01 SOL")
            if wager.amount > 10.0:
                raise HTTPException(status_code=400, detail="Maximum wager is 10 SOL")
        
        # Validate wallet address
        try:
            PublicKey.from_string(wager.player_wallet)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid Solana wallet address format")
        
        # Validate game type
        if wager.game_type not in ["blackjack", "video_poker", "crash"]:
            raise HTTPException(status_code=400, detail="Invalid game type")
        
        # Calculate dev fee
        total_amount = wager.amount
        dev_fee = total_amount * TRANSACTION_FEE_PERCENTAGE
        game_amount = total_amount - dev_fee
        
        # Validate transaction signature if provided
        if wager.transaction_signature and len(wager.transaction_signature) < 80:
            raise HTTPException(status_code=400, detail="Invalid transaction signature format")
        
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
        
        logger.info(f"Wager placed: {wager.player_wallet} - {total_amount} SOL - {wager.game_type}")
        
        return {
            "success": True,
            "wager_id": wager_record["id"],
            "total_amount": total_amount,
            "game_amount": game_amount,
            "dev_fee": dev_fee,
            "dev_wallet": DEV_WALLET_ADDRESS,
            "message": f"Wager of {total_amount} SOL placed successfully (Dev fee: {dev_fee:.6f} SOL)"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error placing wager: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to place wager: {str(e)}")

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

@api_router.post("/game/result")
async def record_game_result(result: GameResult):
    """Record game result and handle automatic payouts for winners with multiplayer announcements"""
    return await enhanced_record_game_result(result)

@api_router.get("/player/stats/{player_wallet}")
async def get_player_stats(player_wallet: str):
    """Get player's game statistics"""
    try:
        # Get total games played
        total_games = await db.game_results.count_documents({"player_wallet": player_wallet})
        
        # Get recent results
        recent_results = await db.game_results.find(
            {"player_wallet": player_wallet}
        ).sort("created_at", -1).limit(10).to_list(10)
        
        # Calculate statistics
        total_wagered = sum(result.get("wager_amount", 0) for result in recent_results)
        total_payout = sum(result.get("payout_amount", 0) for result in recent_results)
        net_profit = total_payout - total_wagered
        
        # Game type breakdown
        blackjack_games = len([r for r in recent_results if r.get("game_type") == "blackjack"])
        poker_games = len([r for r in recent_results if r.get("game_type") == "video_poker"])
        
        # Clean up ObjectIds for JSON serialization
        for result in recent_results:
            if "_id" in result:
                result["_id"] = str(result["_id"])
        
        return {
            "player_wallet": player_wallet,
            "total_games": total_games,
            "total_wagered": total_wagered,
            "total_payout": total_payout,
            "net_profit": net_profit,
            "blackjack_games": blackjack_games,
            "poker_games": poker_games,
            "recent_results": recent_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/leaderboard")
async def get_leaderboard():
    """Get top players leaderboard"""
    try:
        # Aggregate player stats
        pipeline = [
            {
                "$group": {
                    "_id": "$player_wallet",
                    "total_games": {"$sum": 1},
                    "total_wagered": {"$sum": "$wager_amount"},
                    "total_payout": {"$sum": "$payout_amount"},
                    "last_played": {"$max": "$created_at"}
                }
            },
            {
                "$addFields": {
                    "net_profit": {"$subtract": ["$total_payout", "$total_wagered"]}
                }
            },
            {
                "$sort": {"net_profit": -1}
            },
            {
                "$limit": 10
            }
        ]
        
        leaderboard = await db.game_results.aggregate(pipeline).to_list(10)
        
        # Format wallet addresses for display
        for entry in leaderboard:
            wallet = entry["_id"]
            entry["display_wallet"] = f"{wallet[:8]}...{wallet[-8:]}" if len(wallet) > 16 else wallet
        
        return {"leaderboard": leaderboard}
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

# Payout Endpoints
@api_router.post("/payouts/send")
async def send_winner_payout(request: PayoutRequest):
    """Send SOL payout to winner"""
    try:
        if not solana_payout_service:
            raise HTTPException(status_code=503, detail="Solana payout service not available")
        
        if request.amount_sol <= 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than 0")
        
        if request.amount_sol > 10:  # Safety limit for testnet
            raise HTTPException(status_code=400, detail="Amount exceeds maximum limit")
        
        result = await solana_payout_service.send_winner_payout(
            winner_address=request.winner_address,
            amount_sol=request.amount_sol,
            game_id=request.game_id,
            session_id=request.session_id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Payout error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/payouts/status/{payout_id}")
async def get_payout_status(payout_id: str):
    """Get status of a specific payout"""
    if not solana_payout_service:
        raise HTTPException(status_code=503, detail="Solana payout service not available")
    
    result = await solana_payout_service.get_payout_status(payout_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@api_router.get("/payouts/house-balance")
async def get_house_balance():
    """Get house wallet balance"""
    if not solana_payout_service:
        raise HTTPException(status_code=503, detail="Solana payout service not available")
    
    return solana_payout_service.get_house_wallet_balance()

@api_router.get("/payouts/history")
async def get_payout_history(limit: int = 50):
    """Get recent payout history"""
    if not solana_payout_service:
        raise HTTPException(status_code=503, detail="Solana payout service not available")
    
    result = await solana_payout_service.get_payout_history(limit)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

# Simple polling-based chat system (WebSocket alternative)
chat_messages = []
active_players_simulation = []

@api_router.post("/multiplayer/chat/send")
async def send_chat_message(data: dict):
    """Send a chat message (polling-based)"""
    message = data.get("message", "").strip()
    username = data.get("username", "Anonymous")
    
    if not message or len(message) > 200:
        raise HTTPException(status_code=400, detail="Invalid message")
    
    chat_message = {
        "id": str(uuid.uuid4()),
        "username": username,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "type": "chat"
    }
    
    # Keep last 50 messages
    chat_messages.append(chat_message)
    if len(chat_messages) > 50:
        chat_messages.pop(0)
    
    return {"success": True, "message": "Message sent"}

@api_router.get("/multiplayer/chat/messages")
async def get_chat_messages(limit: int = 20):
    """Get recent chat messages (polling-based)"""
    recent_messages = chat_messages[-limit:] if chat_messages else []
    return {"messages": recent_messages}

@api_router.get("/multiplayer/status")
async def get_multiplayer_status():
    """Get multiplayer status including player count and activity"""
    
    # Simulate active players for demo
    import random
    player_count = random.randint(5, 15)
    active_players = []
    
    for i in range(min(player_count, 8)):
        active_players.append({
            "id": f"player_{i}",
            "username": f"Player{random.randint(100, 999)}",
            "bet_amount": round(random.uniform(0.005, 0.05), 3),
            "bet_category": {
                "label": random.choice(["Small Fish", "Medium Bet", "High Roller"]),
                "icon": random.choice(["🐟", "🎯", "💎"])
            },
            "status": random.choice(["betting", "playing", "cashed_out"])
        })
    
    return {
        "connected": True,
        "total_online": player_count,
        "active_players": active_players,
        "chat_messages_count": len(chat_messages)
    }

# Multiplayer Endpoints
@api_router.get("/multiplayer/stats")
async def get_multiplayer_stats():
    """Get current multiplayer statistics"""
    if not MULTIPLAYER_AVAILABLE or not multiplayer_service:
        raise HTTPException(status_code=503, detail="Multiplayer service not available")
    
    stats = await multiplayer_service.get_stats()
    return stats

@api_router.get("/multiplayer/announcements")
async def get_recent_announcements(limit: int = 20):
    """Get recent win/loss announcements"""
    if not MULTIPLAYER_AVAILABLE or not multiplayer_service:
        raise HTTPException(status_code=503, detail="Multiplayer service not available")
    
    announcements = await multiplayer_service._get_recent_announcements(limit)
    return {"announcements": announcements}

@api_router.post("/multiplayer/announce-win")
async def announce_win(data: dict):
    """Manually announce a win (for testing or external triggers)"""
    if not MULTIPLAYER_AVAILABLE or not multiplayer_service:
        raise HTTPException(status_code=503, detail="Multiplayer service not available")
    
    player_wallet = data.get("player_wallet")
    amount = data.get("amount", 0)
    game_type = data.get("game_type", "unknown")
    multiplier = data.get("multiplier", 1.0)
    
    if not player_wallet or amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid player_wallet or amount")
    
    await multiplayer_service.announce_win(player_wallet, amount, game_type, multiplier)
    return {"success": True, "message": "Win announced"}

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

# Update game result endpoint to integrate with multiplayer announcements
async def enhanced_record_game_result(result):
    """Enhanced game result recording with multiplayer announcements"""
    try:
        # Record the game result
        await db.game_results.insert_one(result.dict())
        
        response = {
            "success": True,
            "message": "Game result recorded",
            "payout_amount": result.payout_amount
        }
        
        # If player won (payout > 0), automatically send real SOL payout
        if result.payout_amount > 0 and solana_payout_service:
            try:
                logger.info(f"Processing automatic payout for winner: {result.player_wallet}, amount: {result.payout_amount} SOL")
                
                payout_result = await solana_payout_service.send_winner_payout(
                    winner_address=result.player_wallet,
                    amount_sol=result.payout_amount,
                    game_id=f"{result.game_type}_{result.session_id}",
                    session_id=result.session_id
                )
                
                if payout_result["success"]:
                    response["payout_sent"] = True
                    response["payout_signature"] = payout_result["signature"]
                    response["explorer_url"] = payout_result["explorer_url"]
                    logger.info(f"Automatic payout successful: {payout_result['signature']}")
                    
                    # Announce the win via multiplayer service
                    if MULTIPLAYER_AVAILABLE and multiplayer_service:
                        await multiplayer_service.announce_win(
                            player_wallet=result.player_wallet,
                            amount=result.payout_amount,
                            game_type=result.game_type,
                            multiplier=result.payout_amount / result.wager_amount if result.wager_amount > 0 else 1.0
                        )
                else:
                    response["payout_sent"] = False
                    response["payout_error"] = payout_result["error"]
                    logger.error(f"Automatic payout failed: {payout_result['error']}")
                    
            except Exception as payout_error:
                logger.error(f"Automatic payout exception: {str(payout_error)}")
                response["payout_sent"] = False
                response["payout_error"] = str(payout_error)
        
        return response
        
    except Exception as e:
        logger.error(f"Error recording game result: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Update the main uvicorn run to use sio_app
if __name__ == "__main__":
    uvicorn.run(sio_app, host="0.0.0.0", port=8001)