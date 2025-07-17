import asyncio
import uuid
import random
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class SolanaBustPlayer:
    def __init__(self, wallet_address: str, username: str, bet_amount: float):
        self.wallet_address = wallet_address
        self.username = username
        self.bet_amount = bet_amount
        self.joined_at = datetime.utcnow()
        self.status = "betting"  # betting, flying, cashed_out, crashed
        self.cash_out_multiplier = None
        self.cash_out_time = None
        self.payout_amount = 0.0
        self.dev_fee = bet_amount * 0.12  # 12% dev fee
        self.net_bet = bet_amount - self.dev_fee

    def cash_out(self, multiplier: float):
        """Player cashes out at current multiplier"""
        if self.status == "flying":
            self.status = "cashed_out"
            self.cash_out_multiplier = multiplier
            self.cash_out_time = datetime.utcnow()
            self.payout_amount = self.bet_amount * multiplier
            return True
        return False

    def crash(self):
        """Player crashes (loses bet)"""
        if self.status == "flying":
            self.status = "crashed"
            self.payout_amount = 0.0
            return True
        return False

    def to_dict(self):
        return {
            "wallet_address": self.wallet_address,
            "username": self.username,
            "bet_amount": self.bet_amount,
            "status": self.status,
            "cash_out_multiplier": self.cash_out_multiplier,
            "payout_amount": self.payout_amount,
            "dev_fee": self.dev_fee,
            "net_bet": self.net_bet
        }

class SolanaBustRoom:
    def __init__(self, room_id: str, min_players: int = 1):  # Changed from 4 to 1 for testing
        self.room_id = room_id
        self.min_players = min_players
        self.players: Dict[str, SolanaBustPlayer] = {}
        self.game_state = "waiting"  # waiting, betting, flying, crashed, finished
        self.crash_point = None
        self.current_multiplier = 1.0
        self.created_at = datetime.utcnow()
        self.game_started_at = None
        self.betting_end_time = None
        self.betting_duration = 30  # 30 seconds
        self.crashed_at = None
        self.round_number = 1
        
        # Game statistics
        self.total_bets = 0.0
        self.total_payouts = 0.0
        self.total_dev_fees = 0.0
        self.house_profit = 0.0

    def generate_crash_point(self) -> float:
        """Generate crash point with 12% house edge"""
        random_value = random.random()
        # House edge built-in: 12% advantage
        crash_multiplier = 1 / (1 - random_value * 0.88) * 0.99
        return round(max(1.01, min(100.0, crash_multiplier)), 2)

    def add_player(self, wallet_address: str, username: str, bet_amount: float) -> bool:
        """Add player to room if betting phase"""
        if self.game_state not in ["waiting", "betting"]:
            return False
        
        if wallet_address in self.players:
            return False  # Player already in room
        
        player = SolanaBustPlayer(wallet_address, username, bet_amount)
        self.players[wallet_address] = player
        
        # Update room statistics
        self.total_bets += bet_amount
        self.total_dev_fees += player.dev_fee
        
        logger.info(f"Player {username} joined room {self.room_id} with bet {bet_amount} SOL")
        return True

    def remove_player(self, wallet_address: str) -> bool:
        """Remove player from room (only during betting phase)"""
        if self.game_state not in ["waiting", "betting"]:
            return False
        
        if wallet_address in self.players:
            player = self.players[wallet_address]
            self.total_bets -= player.bet_amount
            self.total_dev_fees -= player.dev_fee
            del self.players[wallet_address]
            logger.info(f"Player {wallet_address} removed from room {self.room_id}")
            return True
        return False

    def can_start_game(self) -> bool:
        """Check if game can start (minimum players met)"""
        return len(self.players) >= self.min_players

    def start_betting_phase(self):
        """Start betting phase"""
        self.game_state = "betting"
        self.betting_end_time = datetime.utcnow().timestamp() + self.betting_duration
        logger.info(f"Room {self.room_id} started betting phase")

    def start_flying_phase(self):
        """Start flying phase"""
        if not self.can_start_game():
            return False
        
        self.game_state = "flying"
        self.game_started_at = datetime.utcnow()
        self.current_multiplier = 1.0
        self.crash_point = self.generate_crash_point()
        
        # Set all players to flying status
        for player in self.players.values():
            player.status = "flying"
        
        logger.info(f"Room {self.room_id} started flying phase. Crash point: {self.crash_point}")
        return True

    def update_multiplier(self, new_multiplier: float):
        """Update current multiplier"""
        self.current_multiplier = new_multiplier

    def player_cash_out(self, wallet_address: str) -> bool:
        """Player attempts to cash out"""
        if self.game_state != "flying":
            return False
        
        if wallet_address not in self.players:
            return False
        
        player = self.players[wallet_address]
        if player.cash_out(self.current_multiplier):
            self.total_payouts += player.payout_amount
            logger.info(f"Player {player.username} cashed out at {self.current_multiplier}x for {player.payout_amount} SOL")
            return True
        return False

    def crash_game(self):
        """Crash the game"""
        self.game_state = "crashed"
        self.crashed_at = datetime.utcnow()
        
        # Crash all players who haven't cashed out
        for player in self.players.values():
            if player.status == "flying":
                player.crash()
        
        # Calculate final statistics
        self.house_profit = self.total_bets - self.total_payouts
        
        logger.info(f"Room {self.room_id} crashed at {self.crash_point}x. House profit: {self.house_profit} SOL")

    def finish_game(self):
        """Finish game and prepare for next round"""
        self.game_state = "finished"
        
        # Generate results for all players
        results = []
        for player in self.players.values():
            results.append({
                "wallet_address": player.wallet_address,
                "username": player.username,
                "bet_amount": player.bet_amount,
                "payout_amount": player.payout_amount,
                "status": player.status,
                "cash_out_multiplier": player.cash_out_multiplier,
                "dev_fee": player.dev_fee,
                "profit_loss": player.payout_amount - player.bet_amount
            })
        
        return results

    def reset_for_next_round(self):
        """Reset room for next round"""
        self.players.clear()
        self.game_state = "waiting"
        self.crash_point = None
        self.current_multiplier = 1.0
        self.game_started_at = None
        self.betting_end_time = None
        self.crashed_at = None
        self.round_number += 1
        
        # Reset statistics
        self.total_bets = 0.0
        self.total_payouts = 0.0
        self.total_dev_fees = 0.0
        self.house_profit = 0.0

    def get_room_state(self) -> Dict:
        """Get current room state"""
        return {
            "room_id": self.room_id,
            "game_state": self.game_state,
            "current_multiplier": self.current_multiplier,
            "crash_point": self.crash_point if self.game_state == "crashed" else None,
            "player_count": len(self.players),
            "min_players": self.min_players,
            "can_start": self.can_start_game(),
            "players": [player.to_dict() for player in self.players.values()],
            "round_number": self.round_number,
            "total_bets": self.total_bets,
            "total_payouts": self.total_payouts,
            "total_dev_fees": self.total_dev_fees,
            "house_profit": self.house_profit,
            "betting_time_left": max(0, self.betting_end_time - datetime.utcnow().timestamp()) if self.betting_end_time else 0
        }

class SolanaBustRoomManager:
    def __init__(self):
        self.rooms: Dict[str, SolanaBustRoom] = {}
        self.player_to_room: Dict[str, str] = {}  # wallet_address -> room_id
        self.active_room_id = None
        self.min_players = 1  # Minimum players for testing (was 4 for mainnet)

    def create_room(self) -> str:
        """Create a new room"""
        room_id = str(uuid.uuid4())
        room = SolanaBustRoom(room_id, self.min_players)
        self.rooms[room_id] = room
        
        # Set as active room if none exists
        if not self.active_room_id:
            self.active_room_id = room_id
            room.start_betting_phase()
        
        logger.info(f"Created new room: {room_id}")
        return room_id

    def get_active_room(self) -> Optional[SolanaBustRoom]:
        """Get the current active room"""
        if self.active_room_id and self.active_room_id in self.rooms:
            return self.rooms[self.active_room_id]
        return None

    def join_room(self, wallet_address: str, username: str, bet_amount: float) -> Optional[str]:
        """Join the active room"""
        # Remove player from current room if they're in one
        if wallet_address in self.player_to_room:
            old_room_id = self.player_to_room[wallet_address]
            if old_room_id in self.rooms:
                self.rooms[old_room_id].remove_player(wallet_address)
            del self.player_to_room[wallet_address]

        # Get or create active room
        room = self.get_active_room()
        if not room:
            room_id = self.create_room()
            room = self.rooms[room_id]
        
        # Add player to room
        if room.add_player(wallet_address, username, bet_amount):
            self.player_to_room[wallet_address] = room.room_id
            return room.room_id
        
        return None

    def leave_room(self, wallet_address: str) -> bool:
        """Leave current room"""
        if wallet_address in self.player_to_room:
            room_id = self.player_to_room[wallet_address]
            if room_id in self.rooms:
                success = self.rooms[room_id].remove_player(wallet_address)
                if success:
                    del self.player_to_room[wallet_address]
                    return True
        return False

    def cash_out_player(self, wallet_address: str) -> bool:
        """Player attempts to cash out"""
        if wallet_address in self.player_to_room:
            room_id = self.player_to_room[wallet_address]
            if room_id in self.rooms:
                return self.rooms[room_id].player_cash_out(wallet_address)
        return False

    def get_player_room_state(self, wallet_address: str) -> Optional[Dict]:
        """Get room state for a specific player"""
        if wallet_address in self.player_to_room:
            room_id = self.player_to_room[wallet_address]
            if room_id in self.rooms:
                return self.rooms[room_id].get_room_state()
        return None

    def get_room_state(self, room_id: str) -> Optional[Dict]:
        """Get room state by room ID"""
        if room_id in self.rooms:
            return self.rooms[room_id].get_room_state()
        return None

    async def game_loop(self):
        """Main game loop for managing rooms"""
        while True:
            try:
                room = self.get_active_room()
                if not room:
                    await asyncio.sleep(1)
                    continue

                if room.game_state == "waiting":
                    # Start betting phase
                    room.start_betting_phase()
                
                elif room.game_state == "betting":
                    # Check if betting time is up
                    if datetime.utcnow().timestamp() > room.betting_end_time:
                        if room.can_start_game():
                            room.start_flying_phase()
                        else:
                            # Extend betting time if not enough players
                            room.betting_end_time = datetime.utcnow().timestamp() + 10
                            logger.info(f"Room {room.room_id} extended betting time - waiting for more players")
                
                elif room.game_state == "flying":
                    # Update multiplier
                    room.update_multiplier(room.current_multiplier + 0.02)
                    
                    # Check if crash point reached
                    if room.current_multiplier >= room.crash_point:
                        room.crash_game()
                
                elif room.game_state == "crashed":
                    # Finish game and prepare for next round
                    room.finish_game()
                    await asyncio.sleep(5)  # 5 second pause
                    room.reset_for_next_round()
                    room.start_betting_phase()
                
                await asyncio.sleep(0.1)  # 100ms updates
                
            except Exception as e:
                logger.error(f"Error in game loop: {e}")
                await asyncio.sleep(1)

# Global room manager instance
room_manager = SolanaBustRoomManager()

# Start the game loop
def start_game_loop():
    """Start the game loop in background"""
    asyncio.create_task(room_manager.game_loop())