import asyncio
import logging
import random
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import socketio
from fastapi import FastAPI
import motor.motor_asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("multiplayer_service")

class MultiplayerService:
    def __init__(self):
        # Socket.IO server
        self.sio = socketio.AsyncServer(
            cors_allowed_origins="*",
            logger=True,
            engineio_logger=True
        )
        
        # MongoDB setup
        mongo_uri = os.getenv("MONGO_URL", "mongodb://localhost:27017")
        self.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)
        self.db = self.mongo_client.solana_gaming
        
        # In-memory storage for active players and game states
        self.active_players = {}  # socket_id -> player_info
        self.game_sessions = {}   # game_type -> {session_data}
        self.chat_messages = []   # Global chat history
        
        # Username generation
        self.adjectives = [
            "Lucky", "Crypto", "Solana", "Diamond", "Golden", "Silver", "Rocket", "Moon",
            "Legendary", "Epic", "Master", "Elite", "Pro", "Ace", "Champion", "Hero",
            "Nova", "Phoenix", "Thunder", "Blazing", "Swift", "Mighty", "Royal", "Supreme"
        ]
        
        self.nouns = [
            "Trader", "Whale", "Bull", "Bear", "Hodler", "Ape", "Wolf", "Lion",
            "Eagle", "Shark", "Tiger", "Falcon", "Warrior", "Hunter", "Player", "Gamer",
            "Knight", "Ninja", "Samurai", "Pioneer", "Explorer", "Voyager", "Captain", "Admiral"
        ]
        
        # Bet categories
        self.bet_categories = {
            "small": {"min": 0.001, "max": 0.009, "label": "Small Fish", "icon": "🐟"},
            "medium": {"min": 0.01, "max": 0.049, "label": "Medium Bet", "icon": "🎯"},
            "high": {"min": 0.05, "max": 0.199, "label": "High Roller", "icon": "💎"},
            "whale": {"min": 0.2, "max": float('inf'), "label": "Crypto Whale", "icon": "🐋"}
        }
        
        # Big win threshold (0.1 SOL as requested)
        self.big_win_threshold = 0.1
        
        # Setup Socket.IO event handlers
        self._setup_socket_handlers()
        
        logger.info("Multiplayer service initialized")

    def _setup_socket_handlers(self):
        """Setup Socket.IO event handlers"""
        
        @self.sio.event
        async def connect(sid, environ):
            logger.info(f"Client connected: {sid}")
            await self._handle_player_connect(sid)
        
        @self.sio.event
        async def disconnect(sid):
            logger.info(f"Client disconnected: {sid}")
            await self._handle_player_disconnect(sid)
        
        @self.sio.event
        async def join_game(sid, data):
            """Player joins a specific game"""
            await self._handle_join_game(sid, data)
        
        @self.sio.event
        async def place_bet(sid, data):
            """Player places a bet"""
            await self._handle_place_bet(sid, data)
        
        @self.sio.event
        async def cash_out(sid, data):
            """Player cashes out"""
            await self._handle_cash_out(sid, data)
        
        @self.sio.event
        async def send_chat(sid, data):
            """Player sends chat message"""
            await self._handle_chat_message(sid, data)

    def generate_username(self) -> str:
        """Generate a random username"""
        adjective = random.choice(self.adjectives)
        noun = random.choice(self.nouns)
        number = random.randint(100, 999)
        return f"{adjective}{noun}{number}"

    def get_bet_category(self, amount: float) -> Dict[str, Any]:
        """Categorize bet amount"""
        for category, info in self.bet_categories.items():
            if info["min"] <= amount <= info["max"]:
                return {
                    "category": category,
                    "label": info["label"],
                    "icon": info["icon"]
                }
        return {
            "category": "small",
            "label": "Small Fish",
            "icon": "🐟"
        }

    async def _handle_player_connect(self, sid: str):
        """Handle new player connection"""
        username = self.generate_username()
        
        player_info = {
            "sid": sid,
            "username": username,
            "connected_at": datetime.utcnow(),
            "current_game": None,
            "current_bet": None,
            "total_wagered": 0.0,
            "total_won": 0.0,
            "games_played": 0
        }
        
        self.active_players[sid] = player_info
        
        # Send welcome message to player
        await self.sio.emit('welcome', {
            "username": username,
            "message": f"Welcome {username}! You're now connected to Solana Gaming Platform."
        }, room=sid)
        
        # Broadcast player count update
        await self._broadcast_player_count()
        
        # Send current game states to new player
        await self._send_game_states(sid)

    async def _handle_player_disconnect(self, sid: str):
        """Handle player disconnection"""
        if sid in self.active_players:
            player = self.active_players[sid]
            logger.info(f"Player {player['username']} disconnected")
            
            # Remove from active players
            del self.active_players[sid]
            
            # Broadcast updated player count
            await self._broadcast_player_count()

    async def _handle_join_game(self, sid: str, data: Dict[str, Any]):
        """Handle player joining a game"""
        if sid not in self.active_players:
            return
        
        game_type = data.get("game_type")
        player = self.active_players[sid]
        player["current_game"] = game_type
        
        logger.info(f"Player {player['username']} joined {game_type}")
        
        # Broadcast to game room
        await self.sio.emit('player_joined_game', {
            "username": player["username"],
            "game_type": game_type,
            "timestamp": datetime.utcnow().isoformat()
        }, room=f"game_{game_type}")
        
        # Join the player to the game room
        await self.sio.enter_room(sid, f"game_{game_type}")

    async def _handle_place_bet(self, sid: str, data: Dict[str, Any]):
        """Handle player placing a bet"""
        if sid not in self.active_players:
            return
        
        player = self.active_players[sid]
        amount = data.get("amount", 0)
        game_type = data.get("game_type", "unknown")
        
        bet_category = self.get_bet_category(amount)
        
        bet_info = {
            "username": player["username"],
            "amount": amount,
            "category": bet_category,
            "game_type": game_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        player["current_bet"] = bet_info
        player["total_wagered"] += amount
        player["games_played"] += 1
        
        # Broadcast bet to all players in the game
        await self.sio.emit('player_bet_placed', {
            "username": player["username"],
            "bet_category": bet_category,
            "game_type": game_type,
            "message": f"{bet_category['icon']} {player['username']} placed a {bet_category['label']} bet!"
        }, room=f"game_{game_type}")
        
        # Update active player list
        await self._broadcast_active_players(game_type)
        
        logger.info(f"Player {player['username']} bet {amount} SOL on {game_type}")

    async def _handle_cash_out(self, sid: str, data: Dict[str, Any]):
        """Handle player cashing out"""
        if sid not in self.active_players:
            return
        
        player = self.active_players[sid]
        amount = data.get("winnings", 0)
        multiplier = data.get("multiplier", 1.0)
        game_type = data.get("game_type", "unknown")
        
        player["total_won"] += amount
        player["current_bet"] = None
        
        # Generate cash out announcement
        announcement = {
            "type": "cash_out",
            "username": player["username"],
            "amount": amount,
            "multiplier": multiplier,
            "game_type": game_type,
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"💰 {player['username']} cashed out at {multiplier:.1f}x for {amount:.6f} SOL!"
        }
        
        # Check if it's a big win
        if amount >= self.big_win_threshold:
            announcement["is_big_win"] = True
            announcement["message"] = f"🎉 BIG WIN! {player['username']} cashed out at {multiplier:.1f}x for {amount:.6f} SOL!"
            
            # Broadcast to all games for big wins
            await self.sio.emit('big_win_announcement', announcement)
        else:
            # Regular cash out - broadcast to game room only
            await self.sio.emit('cash_out_announcement', announcement, room=f"game_{game_type}")
        
        # Store announcement in database
        await self._store_announcement(announcement)
        
        # Update active player list
        await self._broadcast_active_players(game_type)
        
        logger.info(f"Player {player['username']} cashed out {amount} SOL at {multiplier}x")

    async def _handle_chat_message(self, sid: str, data: Dict[str, Any]):
        """Handle chat message from player"""
        if sid not in self.active_players:
            return
        
        player = self.active_players[sid]
        message = data.get("message", "").strip()
        
        if not message or len(message) > 200:  # Message validation
            return
        
        chat_message = {
            "username": player["username"],
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "type": "chat"
        }
        
        # Add to chat history (keep last 100 messages)
        self.chat_messages.append(chat_message)
        if len(self.chat_messages) > 100:
            self.chat_messages.pop(0)
        
        # Broadcast to all connected players
        await self.sio.emit('chat_message', chat_message)
        
        logger.info(f"Chat message from {player['username']}: {message}")

    async def _broadcast_player_count(self):
        """Broadcast current player count to all players"""
        count = len(self.active_players)
        await self.sio.emit('player_count_update', {
            "count": count,
            "message": f"{count} players online"
        })

    async def _broadcast_active_players(self, game_type: str):
        """Broadcast active players list for a specific game"""
        game_players = []
        
        for player in self.active_players.values():
            if player.get("current_game") == game_type and player.get("current_bet"):
                bet_info = player["current_bet"]
                game_players.append({
                    "username": player["username"],
                    "bet_category": bet_info["category"],
                    "status": "betting"
                })
        
        await self.sio.emit('active_players_update', {
            "game_type": game_type,
            "players": game_players,
            "count": len(game_players)
        }, room=f"game_{game_type}")

    async def _send_game_states(self, sid: str):
        """Send current game states to a newly connected player"""
        # Send recent chat messages
        recent_messages = self.chat_messages[-20:] if self.chat_messages else []
        await self.sio.emit('chat_history', {
            "messages": recent_messages
        }, room=sid)
        
        # Send recent announcements
        recent_announcements = await self._get_recent_announcements()
        await self.sio.emit('recent_announcements', {
            "announcements": recent_announcements
        }, room=sid)

    async def _store_announcement(self, announcement: Dict[str, Any]):
        """Store announcement in database"""
        try:
            await self.db.announcements.insert_one(announcement)
        except Exception as e:
            logger.error(f"Error storing announcement: {e}")

    async def _get_recent_announcements(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent announcements from database"""
        try:
            cursor = self.db.announcements.find().sort("timestamp", -1).limit(limit)
            announcements = await cursor.to_list(length=limit)
            
            # Convert ObjectId to string for JSON serialization
            for announcement in announcements:
                if "_id" in announcement:
                    announcement["_id"] = str(announcement["_id"])
            
            return announcements
        except Exception as e:
            logger.error(f"Error fetching announcements: {e}")
            return []

    # Public methods for external use
    async def announce_win(self, player_wallet: str, amount: float, game_type: str, multiplier: float = 1.0):
        """Announce a win from external game logic"""
        # Find player by wallet (you'd need to store wallet->sid mapping)
        username = f"Player{player_wallet[:6]}..."  # Fallback username
        
        announcement = {
            "type": "win",
            "username": username,
            "amount": amount,
            "multiplier": multiplier,
            "game_type": game_type,
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"🎉 {username} won {amount:.6f} SOL on {game_type}!"
        }
        
        if amount >= self.big_win_threshold:
            announcement["is_big_win"] = True
            announcement["message"] = f"🎉 BIG WIN! {username} won {amount:.6f} SOL on {game_type}!"
            await self.sio.emit('big_win_announcement', announcement)
        
        await self._store_announcement(announcement)

    async def get_stats(self) -> Dict[str, Any]:
        """Get current multiplayer stats"""
        return {
            "active_players": len(self.active_players),
            "total_wagered": sum(p.get("total_wagered", 0) for p in self.active_players.values()),
            "total_games": sum(p.get("games_played", 0) for p in self.active_players.values()),
            "chat_messages": len(self.chat_messages)
        }

# Global instance
multiplayer_service = MultiplayerService()