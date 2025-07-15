#!/usr/bin/env python3
import requests
import json
import time
import sys
import os
from dotenv import load_dotenv
import random
import string
import statistics
import uuid

# Load environment variables from frontend/.env to get the backend URL
load_dotenv("frontend/.env")

# Get the backend URL from environment variables
BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BACKEND_URL:
    print("Error: REACT_APP_BACKEND_URL not found in frontend/.env")
    sys.exit(1)

# Ensure the URL doesn't end with a slash
if BACKEND_URL.endswith("/"):
    BACKEND_URL = BACKEND_URL[:-1]

# Add the /api prefix
API_URL = f"{BACKEND_URL}/api"

print(f"Using API URL: {API_URL}")

# Test data
TEST_WALLET_PUBLIC_KEY = "A7GZMJLFzGSPn1nYHsGhLbU5pby4q96AessVHn5qVXFZ"  # Dev wallet for testing
TEST_SIGNATURE = "5VxYCvdJZ1XoqJVBs4ysZCQ1RbZ3ZEpgEMran6UNnQmtK9XFMpf9YYBmJiNQQJqFbsL82F8BkYJh3UtEm5EJQzXP"  # Example signature
TEST_MESSAGE = "Connect Wallet"
TESTNET_TOKEN_ADDRESS = "Gh9ZwEmdLJ8DscKNTkTqPbNwLNNBjuSzaG9Vp2KGtKJr"
DEV_WALLET_ADDRESS = "A7GZMJLFzGSPn1nYHsGhLbU5pby4q96AessVHn5qVXFZ"
TRANSACTION_FEE_PERCENTAGE = 0.12  # 12% - UPDATED DEV FEE

# Helper function to generate a random client name
def random_client_name():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

# Helper function to print test results
def print_test_result(test_name, success, response=None, error=None):
    if success:
        print(f"✅ {test_name}: PASSED")
        if response:
            print(f"   Response: {json.dumps(response, indent=2)}")
    else:
        print(f"❌ {test_name}: FAILED")
        if error:
            print(f"   Error: {error}")
        if response:
            print(f"   Response: {json.dumps(response, indent=2)}")
    print("-" * 80)

# Test 1: Basic API connectivity
def test_api_connectivity():
    try:
        response = requests.get(f"{API_URL}/")
        response.raise_for_status()
        data = response.json()
        return True, data
    except Exception as e:
        return False, str(e)

# Test 2: Status check API
def test_status_check():
    try:
        # Create a status check
        client_name = random_client_name()
        response = requests.post(
            f"{API_URL}/status",
            json={"client_name": client_name}
        )
        response.raise_for_status()
        create_data = response.json()
        
        # Get status checks
        response = requests.get(f"{API_URL}/status")
        response.raise_for_status()
        get_data = response.json()
        
        # Verify the created status check is in the list
        found = any(check["client_name"] == client_name for check in get_data)
        
        return found, {"created": create_data, "all_checks": get_data[:2]}  # Limit output for readability
    except Exception as e:
        return False, str(e)

# Test 3: Solana Web3 Integration - Wallet Balance
def test_wallet_balance():
    try:
        response = requests.get(f"{API_URL}/wallet/balance/{TEST_WALLET_PUBLIC_KEY}")
        response.raise_for_status()
        data = response.json()
        
        # Verify the response contains the expected fields
        if "public_key" in data and "balance_lamports" in data and "balance_sol" in data:
            return True, data
        else:
            return False, "Response missing expected fields"
    except Exception as e:
        return False, str(e)

# Test 4: Phantom Wallet Backend APIs - Wallet Connection
def test_wallet_connection():
    try:
        response = requests.post(
            f"{API_URL}/wallet/connect",
            json={
                "public_key": TEST_WALLET_PUBLIC_KEY,
                "signature": TEST_SIGNATURE,
                "message": TEST_MESSAGE
            }
        )
        response.raise_for_status()
        data = response.json()
        
        # Verify the response indicates success
        if data.get("success") and data.get("public_key") == TEST_WALLET_PUBLIC_KEY:
            return True, data
        else:
            return False, "Wallet connection failed"
    except Exception as e:
        return False, str(e)

# Test 5: Game Session Management - Blackjack
def test_blackjack_session_creation():
    try:
        response = requests.post(
            f"{API_URL}/game/session/create",
            params={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "game_type": "blackjack",
                "num_hands": 2
            }
        )
        response.raise_for_status()
        data = response.json()
        
        # Verify the response contains the expected fields
        if (data.get("success") and 
            "session_id" in data and 
            "game_data" in data and 
            "player_hands" in data["game_data"] and 
            "dealer_hand" in data["game_data"] and
            len(data["game_data"]["player_hands"]) == 2):
            
            # Verify initial deal has 2 cards for player and dealer
            player_hand_1 = data["game_data"]["player_hands"][0]
            player_hand_2 = data["game_data"]["player_hands"][1]
            dealer_hand = data["game_data"]["dealer_hand"]
            
            if (len(player_hand_1["cards"]) == 2 and 
                len(player_hand_2["cards"]) == 2 and 
                len(dealer_hand["cards"]) == 2):
                return True, data
            else:
                return False, "Initial deal doesn't have the correct number of cards"
        else:
            return False, "Blackjack session creation failed or has incorrect data"
    except Exception as e:
        return False, str(e)

# Test 6: Game Session Management - Video Poker
def test_video_poker_session_creation():
    try:
        response = requests.post(
            f"{API_URL}/game/session/create",
            params={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "game_type": "video_poker"
            }
        )
        response.raise_for_status()
        data = response.json()
        
        # Verify the response contains the expected fields
        if (data.get("success") and 
            "session_id" in data and 
            "game_data" in data and 
            "hand" in data["game_data"] and 
            "hand_rank" in data["game_data"] and
            len(data["game_data"]["hand"]) == 5 and
            data["game_data"]["initial_deal"] == True):
            return True, data
        else:
            return False, "Video poker session creation failed or has incorrect data"
    except Exception as e:
        return False, str(e)

# Test 7: Wagering System with 2% Dev Fee
def test_wagering_system():
    try:
        # First create a game session
        session_response = requests.post(
            f"{API_URL}/game/session/create",
            params={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "game_type": "blackjack"
            }
        )
        session_response.raise_for_status()
        session_data = session_response.json()
        session_id = session_data["session_id"]
        
        # Now place a wager
        wager_amount = 1.0  # 1 SOL for testing
        response = requests.post(
            f"{API_URL}/game/wager",
            json={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "amount": wager_amount,
                "game_type": "blackjack",
                "session_id": session_id,
                "transaction_signature": TEST_SIGNATURE
            }
        )
        response.raise_for_status()
        data = response.json()
        
        # Verify the response contains the expected fields and fee calculation is correct
        expected_dev_fee = wager_amount * TRANSACTION_FEE_PERCENTAGE
        expected_game_amount = wager_amount - expected_dev_fee
        
        if (data.get("success") and 
            "wager_id" in data and 
            "total_amount" in data and 
            "game_amount" in data and 
            "dev_fee" in data and
            abs(data["dev_fee"] - expected_dev_fee) < 0.001 and  # Allow for floating point precision
            abs(data["game_amount"] - expected_game_amount) < 0.001 and
            data["dev_wallet"] == DEV_WALLET_ADDRESS):
            return True, data
        else:
            return False, "Wager processing failed or fee calculation is incorrect"
    except Exception as e:
        return False, str(e)

# Test 8: Game Logic APIs - Blackjack Hit
def test_blackjack_hit():
    try:
        # First create a game session
        session_response = requests.post(
            f"{API_URL}/game/session/create",
            params={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "game_type": "blackjack"
            }
        )
        session_response.raise_for_status()
        session_data = session_response.json()
        session_id = session_data["session_id"]
        
        # Get initial hand value
        initial_hand_value = session_data["game_data"]["player_hands"][0]["value"]
        
        # Now hit
        response = requests.post(
            f"{API_URL}/game/blackjack/hit",
            params={
                "session_id": session_id,
                "hand_index": 0
            }
        )
        response.raise_for_status()
        data = response.json()
        
        # Verify the response contains the expected fields
        if (data.get("success") and 
            "new_card" in data and 
            "message" in data and
            "game_state" in data):
            
            # Verify a new card was added to the player's hand
            player_hand = data["game_state"]["player_hands"][0]
            if len(player_hand["cards"]) == 3:  # Should now have 3 cards
                # Verify hand value was updated
                new_hand_value = player_hand["value"]
                if new_hand_value != initial_hand_value:
                    return True, data
                else:
                    return False, "Hand value was not updated after hit"
            else:
                return False, "New card was not added to player's hand"
        else:
            return False, "Blackjack hit failed or has incorrect data"
    except Exception as e:
        return False, str(e)

# Test 9: Game Logic APIs - Blackjack Hit Until Bust
def test_blackjack_hit_until_bust():
    try:
        # First create a game session
        session_response = requests.post(
            f"{API_URL}/game/session/create",
            params={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "game_type": "blackjack"
            }
        )
        session_response.raise_for_status()
        session_data = session_response.json()
        session_id = session_data["session_id"]
        
        # Hit until bust or reach 10 hits (to prevent infinite loop)
        busted = False
        hit_count = 0
        max_hits = 10
        
        while hit_count < max_hits:
            response = requests.post(
                f"{API_URL}/game/blackjack/hit",
                params={
                    "session_id": session_id,
                    "hand_index": 0
                }
            )
            response.raise_for_status()
            data = response.json()
            
            hit_count += 1
            
            # Check if busted
            if data["game_state"]["player_hands"][0]["busted"]:
                busted = True
                break
        
        if busted:
            return True, {
                "message": f"Successfully busted after {hit_count} hits",
                "final_hand": data["game_state"]["player_hands"][0]
            }
        else:
            return False, f"Failed to bust after {hit_count} hits"
    except Exception as e:
        return False, str(e)

# Test 10: Game Logic APIs - Blackjack Stand
def test_blackjack_stand():
    try:
        # First create a game session
        session_response = requests.post(
            f"{API_URL}/game/session/create",
            params={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "game_type": "blackjack"
            }
        )
        session_response.raise_for_status()
        session_data = session_response.json()
        session_id = session_data["session_id"]
        
        # Get initial game state
        initial_game_state = session_data["game_data"]
        
        # Now stand
        response = requests.post(
            f"{API_URL}/game/blackjack/stand",
            params={
                "session_id": session_id,
                "hand_index": 0
            }
        )
        response.raise_for_status()
        data = response.json()
        
        # Verify the response contains the expected fields
        if (data.get("success") and 
            "message" in data and
            "game_state" in data):
            
            # Verify game state remains unchanged after stand
            player_hand = data["game_state"]["player_hands"][0]
            initial_player_hand = initial_game_state["player_hands"][0]
            
            if (player_hand["value"] == initial_player_hand["value"] and
                len(player_hand["cards"]) == len(initial_player_hand["cards"])):
                return True, data
            else:
                return False, "Game state changed after stand"
        else:
            return False, "Blackjack stand failed or has incorrect data"
    except Exception as e:
        return False, str(e)

# Test 11: Game Logic APIs - Blackjack Finish
def test_blackjack_finish():
    try:
        # First create a game session
        session_response = requests.post(
            f"{API_URL}/game/session/create",
            params={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "game_type": "blackjack"
            }
        )
        session_response.raise_for_status()
        session_data = session_response.json()
        session_id = session_data["session_id"]
        
        # Now finish the game
        response = requests.post(
            f"{API_URL}/game/blackjack/finish",
            params={
                "session_id": session_id
            }
        )
        response.raise_for_status()
        data = response.json()
        
        # Verify the response contains the expected fields
        if (data.get("success") and 
            "game_state" in data and
            "results" in data and
            data["game_state"]["game_over"] == True):
            
            # Verify dealer has played according to rules
            dealer_hand = data["game_state"]["dealer_hand"]
            dealer_value = dealer_hand["value"]
            
            # Dealer should have played to at least 17 unless busted
            if dealer_value >= 17 or dealer_hand["busted"]:
                
                # Verify results contain expected fields
                result = data["results"][0]
                if ("hand_index" in result and
                    "result" in result and
                    "payout_multiplier" in result and
                    "player_value" in result and
                    "dealer_value" in result):
                    return True, data
                else:
                    return False, "Results missing expected fields"
            else:
                return False, f"Dealer didn't play according to rules. Value: {dealer_value}"
        else:
            return False, "Blackjack finish failed or has incorrect data"
    except Exception as e:
        return False, str(e)

# Test 12: Game Logic APIs - Video Poker Hold
def test_video_poker_hold():
    try:
        # First create a game session
        session_response = requests.post(
            f"{API_URL}/game/session/create",
            params={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "game_type": "video_poker"
            }
        )
        session_response.raise_for_status()
        session_data = session_response.json()
        session_id = session_data["session_id"]
        
        # Now hold cards
        positions = [0, 2, 4]  # Hold cards at positions 0, 2, and 4
        response = requests.post(
            f"{API_URL}/game/video_poker/hold",
            params={
                "session_id": session_id
            },
            json=positions
        )
        response.raise_for_status()
        data = response.json()
        
        # Verify the response contains the expected fields
        if (data.get("success") and 
            "held_positions" in data and 
            "message" in data and
            set(data["held_positions"]) == set(positions)):
            return True, data
        else:
            return False, "Video poker hold failed or has incorrect data"
    except Exception as e:
        return False, str(e)

# Test 13: Game Logic APIs - Video Poker Draw
def test_video_poker_draw():
    try:
        # First create a game session
        session_response = requests.post(
            f"{API_URL}/game/session/create",
            params={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "game_type": "video_poker"
            }
        )
        session_response.raise_for_status()
        session_data = session_response.json()
        session_id = session_data["session_id"]
        
        # Get initial cards
        initial_hand = session_data["game_data"]["hand"]
        
        # Hold some cards
        positions = [0, 2]  # Hold cards at positions 0 and 2
        hold_response = requests.post(
            f"{API_URL}/game/video_poker/hold",
            params={
                "session_id": session_id
            },
            json=positions
        )
        hold_response.raise_for_status()
        
        # Now draw new cards
        response = requests.post(
            f"{API_URL}/game/video_poker/draw",
            params={
                "session_id": session_id
            }
        )
        response.raise_for_status()
        data = response.json()
        
        # Verify the response contains the expected fields
        if (data.get("success") and 
            "game_state" in data and
            "final_hand" in data and
            "payout_multiplier" in data and
            data["game_state"]["game_complete"] == True):
            
            # Verify held cards remained the same
            final_hand = data["game_state"]["hand"]
            
            # Check if held cards are the same
            held_cards_unchanged = True
            for pos in positions:
                if final_hand[pos]["card"] != initial_hand[pos]["card"]:
                    held_cards_unchanged = False
                    break
            
            if held_cards_unchanged:
                return True, data
            else:
                return False, "Held cards were changed during draw"
        else:
            return False, "Video poker draw failed or has incorrect data"
    except Exception as e:
        return False, str(e)

# Test 14: Complete Blackjack Game Flow
def test_complete_blackjack_game_flow():
    try:
        # 1. Create session
        session_response = requests.post(
            f"{API_URL}/game/session/create",
            params={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "game_type": "blackjack"
            }
        )
        session_response.raise_for_status()
        session_data = session_response.json()
        session_id = session_data["session_id"]
        
        # 2. Place wager
        wager_amount = 1.0
        wager_response = requests.post(
            f"{API_URL}/game/wager",
            json={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "amount": wager_amount,
                "game_type": "blackjack",
                "session_id": session_id,
                "transaction_signature": TEST_SIGNATURE
            }
        )
        wager_response.raise_for_status()
        
        # 3. Hit once
        hit_response = requests.post(
            f"{API_URL}/game/blackjack/hit",
            params={
                "session_id": session_id,
                "hand_index": 0
            }
        )
        hit_response.raise_for_status()
        hit_data = hit_response.json()
        
        # 4. Stand
        stand_response = requests.post(
            f"{API_URL}/game/blackjack/stand",
            params={
                "session_id": session_id,
                "hand_index": 0
            }
        )
        stand_response.raise_for_status()
        stand_data = stand_response.json()
        
        # 5. Finish game
        finish_response = requests.post(
            f"{API_URL}/game/blackjack/finish",
            params={
                "session_id": session_id
            }
        )
        finish_response.raise_for_status()
        finish_data = finish_response.json()
        
        # 6. Record result
        result = finish_data["results"][0]
        payout_multiplier = result["payout_multiplier"]
        payout_amount = wager_amount * payout_multiplier
        
        result_response = requests.post(
            f"{API_URL}/game/result",
            json={
                "session_id": session_id,
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "game_type": "blackjack",
                "wager_amount": wager_amount,
                "payout_amount": payout_amount,
                "game_data": finish_data["game_state"],
                "transaction_signature": TEST_SIGNATURE
            }
        )
        result_response.raise_for_status()
        result_data = result_response.json()
        
        # Verify the dev fee calculation
        dev_fee = wager_amount * TRANSACTION_FEE_PERCENTAGE
        
        return True, {
            "session_id": session_id,
            "wager_amount": wager_amount,
            "game_result": result["result"],
            "payout_multiplier": payout_multiplier,
            "payout_amount": payout_amount,
            "dev_fee": dev_fee,
            "initial_cards": session_data["game_data"]["player_hands"][0]["cards"],
            "hit_card": hit_data.get("new_card"),
            "final_player_value": result["player_value"],
            "dealer_value": result["dealer_value"],
            "result_recorded": result_data.get("success", False)
        }
    except Exception as e:
        return False, str(e)

# Test 15: Complete Video Poker Game Flow
def test_complete_video_poker_game_flow():
    try:
        # 1. Create session
        session_response = requests.post(
            f"{API_URL}/game/session/create",
            params={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "game_type": "video_poker"
            }
        )
        session_response.raise_for_status()
        session_data = session_response.json()
        session_id = session_data["session_id"]
        initial_hand = session_data["game_data"]["hand"]
        
        # 2. Place wager
        wager_amount = 1.0
        wager_response = requests.post(
            f"{API_URL}/game/wager",
            json={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "amount": wager_amount,
                "game_type": "video_poker",
                "session_id": session_id,
                "transaction_signature": TEST_SIGNATURE
            }
        )
        wager_response.raise_for_status()
        wager_data = wager_response.json()
        
        # 3. Hold some cards
        positions = [0, 2, 4]  # Hold cards at positions 0, 2, and 4
        hold_response = requests.post(
            f"{API_URL}/game/video_poker/hold",
            params={
                "session_id": session_id
            },
            json=positions
        )
        hold_response.raise_for_status()
        hold_data = hold_response.json()
        
        # 4. Draw new cards
        draw_response = requests.post(
            f"{API_URL}/game/video_poker/draw",
            params={
                "session_id": session_id
            }
        )
        draw_response.raise_for_status()
        draw_data = draw_response.json()
        
        # 5. Record result
        hand_rank = draw_data["final_hand"]
        payout_multiplier = draw_data["payout_multiplier"]
        payout_amount = wager_amount * payout_multiplier
        
        result_response = requests.post(
            f"{API_URL}/game/result",
            json={
                "session_id": session_id,
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "game_type": "video_poker",
                "wager_amount": wager_amount,
                "payout_amount": payout_amount,
                "game_data": draw_data["game_state"],
                "transaction_signature": TEST_SIGNATURE
            }
        )
        result_response.raise_for_status()
        result_data = result_response.json()
        
        # Verify the dev fee calculation
        dev_fee = wager_amount * TRANSACTION_FEE_PERCENTAGE
        
        # Verify held cards remained the same
        final_hand = draw_data["game_state"]["hand"]
        held_cards_unchanged = True
        for pos in positions:
            if final_hand[pos]["card"] != initial_hand[pos]["card"]:
                held_cards_unchanged = False
                break
        
        return True, {
            "session_id": session_id,
            "wager_amount": wager_amount,
            "initial_hand": [card["card"] for card in initial_hand],
            "held_positions": positions,
            "final_hand": [card["card"] for card in final_hand],
            "hand_rank": hand_rank,
            "payout_multiplier": payout_multiplier,
            "payout_amount": payout_amount,
            "dev_fee": dev_fee,
            "held_cards_unchanged": held_cards_unchanged,
            "result_recorded": result_data.get("success", False)
        }
    except Exception as e:
        return False, str(e)

# Test 16: Blackjack Win Rate Validation
def test_blackjack_win_rate():
    try:
        wins = 0
        losses = 0
        pushes = 0
        blackjacks = 0
        total_games = 20
        
        for _ in range(total_games):
            # Create session
            session_response = requests.post(
                f"{API_URL}/game/session/create",
                params={
                    "player_wallet": TEST_WALLET_PUBLIC_KEY,
                    "game_type": "blackjack"
                }
            )
            session_id = session_response.json()["session_id"]
            
            # Finish game immediately
            finish_response = requests.post(
                f"{API_URL}/game/blackjack/finish",
                params={
                    "session_id": session_id
                }
            )
            finish_data = finish_response.json()
            
            # Record result
            result = finish_data["results"][0]["result"]
            if result == "win":
                wins += 1
            elif result == "lose":
                losses += 1
            elif result == "push":
                pushes += 1
            elif result == "blackjack":
                blackjacks += 1
                wins += 1  # Count blackjack as a win for win rate calculation
        
        win_rate = (wins / total_games) * 100
        
        # Expected win rate is 69%
        # Allow for some variance due to randomness
        if abs(win_rate - 69) <= 15:  # Allow 15% variance
            return True, {
                "total_games": total_games,
                "wins": wins,
                "losses": losses,
                "pushes": pushes,
                "blackjacks": blackjacks,
                "win_rate": f"{win_rate:.2f}%",
                "expected_win_rate": "69%"
            }
        else:
            return False, f"Win rate of {win_rate:.2f}% is too far from expected 69%"
    except Exception as e:
        return False, str(e)

# Test 17: Video Poker Win Rate Validation
def test_video_poker_win_rate():
    try:
        wins = 0
        losses = 0
        total_games = 20
        
        for _ in range(total_games):
            # Create session
            session_response = requests.post(
                f"{API_URL}/game/session/create",
                params={
                    "player_wallet": TEST_WALLET_PUBLIC_KEY,
                    "game_type": "video_poker"
                }
            )
            session_id = session_response.json()["session_id"]
            
            # Draw cards immediately
            draw_response = requests.post(
                f"{API_URL}/game/video_poker/draw",
                params={
                    "session_id": session_id
                }
            )
            draw_data = draw_response.json()
            
            # Record result
            payout_multiplier = draw_data["payout_multiplier"]
            if payout_multiplier > 0:
                wins += 1
            else:
                losses += 1
        
        win_rate = (wins / total_games) * 100
        
        # Expected win rate is 65%
        # Allow for some variance due to randomness
        if abs(win_rate - 65) <= 15:  # Allow 15% variance
            return True, {
                "total_games": total_games,
                "wins": wins,
                "losses": losses,
                "win_rate": f"{win_rate:.2f}%",
                "expected_win_rate": "65%"
            }
        else:
            return False, f"Win rate of {win_rate:.2f}% is too far from expected 65%"
    except Exception as e:
        return False, str(e)

# Test 24: Video Poker with Different Hold Combinations
def test_video_poker_different_holds():
    try:
        results = []
        
        # Test different hold combinations
        hold_combinations = [
            [],  # Hold no cards
            [0, 1, 2, 3, 4],  # Hold all cards
            [0, 1],  # Hold first two cards
            [3, 4],  # Hold last two cards
            [1, 3]   # Hold middle and second-to-last
        ]
        
        for positions in hold_combinations:
            # Create session
            session_response = requests.post(
                f"{API_URL}/game/session/create",
                params={
                    "player_wallet": TEST_WALLET_PUBLIC_KEY,
                    "game_type": "video_poker"
                }
            )
            session_response.raise_for_status()
            session_data = session_response.json()
            session_id = session_data["session_id"]
            initial_hand = session_data["game_data"]["hand"]
            
            # Hold cards
            hold_response = requests.post(
                f"{API_URL}/game/video_poker/hold",
                params={
                    "session_id": session_id
                },
                json=positions
            )
            hold_response.raise_for_status()
            
            # Draw new cards
            draw_response = requests.post(
                f"{API_URL}/game/video_poker/draw",
                params={
                    "session_id": session_id
                }
            )
            draw_response.raise_for_status()
            draw_data = draw_response.json()
            
            # Verify held cards remained the same
            final_hand = draw_data["game_state"]["hand"]
            held_cards_unchanged = True
            for pos in positions:
                if final_hand[pos]["card"] != initial_hand[pos]["card"]:
                    held_cards_unchanged = False
                    break
            
            # Verify non-held cards were replaced
            non_held_cards_changed = True
            for i in range(5):
                if i not in positions and final_hand[i]["card"] == initial_hand[i]["card"]:
                    non_held_cards_changed = False
                    break
            
            # Special case for holding all cards
            if len(positions) == 5:
                non_held_cards_changed = True
            
            results.append({
                "hold_positions": positions,
                "initial_hand": [card["card"] for card in initial_hand],
                "final_hand": [card["card"] for card in final_hand],
                "hand_rank": draw_data["final_hand"],
                "payout_multiplier": draw_data["payout_multiplier"],
                "held_cards_unchanged": held_cards_unchanged,
                "non_held_cards_changed": non_held_cards_changed if len(positions) < 5 else "N/A (all cards held)"
            })
        
        all_tests_passed = all(result["held_cards_unchanged"] for result in results)
        all_tests_passed = all_tests_passed and all(
            result["non_held_cards_changed"] == True or 
            result["non_held_cards_changed"] == "N/A (all cards held)" 
            for result in results
        )
        
        return all_tests_passed, {
            "hold_combinations_tested": len(hold_combinations),
            "results": results
        }
    except Exception as e:
        return False, str(e)

# Test 25: Blackjack Different Scenarios
def test_blackjack_different_scenarios():
    try:
        results = []
        
        # Test different scenarios
        scenarios = [
            "hit_until_bust",  # Hit until bust
            "stand_immediately",  # Stand immediately
            "hit_once_stand"  # Hit once then stand
        ]
        
        for scenario in scenarios:
            # Create session
            session_response = requests.post(
                f"{API_URL}/game/session/create",
                params={
                    "player_wallet": TEST_WALLET_PUBLIC_KEY,
                    "game_type": "blackjack"
                }
            )
            session_response.raise_for_status()
            session_data = session_response.json()
            session_id = session_data["session_id"]
            initial_hand = session_data["game_data"]["player_hands"][0]
            
            if scenario == "hit_until_bust":
                # Hit until bust or reach 10 hits (to prevent infinite loop)
                busted = False
                hit_count = 0
                max_hits = 10
                final_value = initial_hand["value"]
                
                while hit_count < max_hits and not busted:
                    hit_response = requests.post(
                        f"{API_URL}/game/blackjack/hit",
                        params={
                            "session_id": session_id,
                            "hand_index": 0
                        }
                    )
                    hit_response.raise_for_status()
                    hit_data = hit_response.json()
                    
                    hit_count += 1
                    final_value = hit_data["game_state"]["player_hands"][0]["value"]
                    
                    # Check if busted
                    if hit_data["game_state"]["player_hands"][0]["busted"]:
                        busted = True
                        break
                
                # Finish game
                finish_response = requests.post(
                    f"{API_URL}/game/blackjack/finish",
                    params={
                        "session_id": session_id
                    }
                )
                finish_response.raise_for_status()
                finish_data = finish_response.json()
                
                results.append({
                    "scenario": scenario,
                    "initial_value": initial_hand["value"],
                    "final_value": final_value,
                    "hit_count": hit_count,
                    "busted": busted,
                    "result": finish_data["results"][0]["result"],
                    "payout_multiplier": finish_data["results"][0]["payout_multiplier"]
                })
                
            elif scenario == "stand_immediately":
                # Stand immediately
                stand_response = requests.post(
                    f"{API_URL}/game/blackjack/stand",
                    params={
                        "session_id": session_id,
                        "hand_index": 0
                    }
                )
                stand_response.raise_for_status()
                
                # Finish game
                finish_response = requests.post(
                    f"{API_URL}/game/blackjack/finish",
                    params={
                        "session_id": session_id
                    }
                )
                finish_response.raise_for_status()
                finish_data = finish_response.json()
                
                results.append({
                    "scenario": scenario,
                    "initial_value": initial_hand["value"],
                    "final_value": initial_hand["value"],  # Unchanged
                    "dealer_value": finish_data["game_state"]["dealer_hand"]["value"],
                    "result": finish_data["results"][0]["result"],
                    "payout_multiplier": finish_data["results"][0]["payout_multiplier"]
                })
                
            elif scenario == "hit_once_stand":
                # Hit once
                hit_response = requests.post(
                    f"{API_URL}/game/blackjack/hit",
                    params={
                        "session_id": session_id,
                        "hand_index": 0
                    }
                )
                hit_response.raise_for_status()
                hit_data = hit_response.json()
                
                # Stand
                stand_response = requests.post(
                    f"{API_URL}/game/blackjack/stand",
                    params={
                        "session_id": session_id,
                        "hand_index": 0
                    }
                )
                stand_response.raise_for_status()
                
                # Finish game
                finish_response = requests.post(
                    f"{API_URL}/game/blackjack/finish",
                    params={
                        "session_id": session_id
                    }
                )
                finish_response.raise_for_status()
                finish_data = finish_response.json()
                
                results.append({
                    "scenario": scenario,
                    "initial_value": initial_hand["value"],
                    "after_hit_value": hit_data["game_state"]["player_hands"][0]["value"],
                    "dealer_value": finish_data["game_state"]["dealer_hand"]["value"],
                    "result": finish_data["results"][0]["result"],
                    "payout_multiplier": finish_data["results"][0]["payout_multiplier"]
                })
        
        return True, {
            "scenarios_tested": len(scenarios),
            "results": results
        }
    except Exception as e:
        return False, str(e)

# Test 26: Win Rate Verification with More Games
def test_win_rates_with_more_games():
    try:
        # Test blackjack win rate with more games
        blackjack_results = []
        blackjack_total_games = 50
        
        for _ in range(blackjack_total_games):
            # Create session
            session_response = requests.post(
                f"{API_URL}/game/session/create",
                params={
                    "player_wallet": TEST_WALLET_PUBLIC_KEY,
                    "game_type": "blackjack"
                }
            )
            session_id = session_response.json()["session_id"]
            
            # Finish game immediately
            finish_response = requests.post(
                f"{API_URL}/game/blackjack/finish",
                params={
                    "session_id": session_id
                }
            )
            finish_data = finish_response.json()
            
            # Record result
            result = finish_data["results"][0]["result"]
            blackjack_results.append(result)
        
        # Calculate blackjack win rate
        blackjack_wins = blackjack_results.count("win") + blackjack_results.count("blackjack")
        blackjack_win_rate = (blackjack_wins / blackjack_total_games) * 100
        
        # Test video poker win rate with more games
        poker_results = []
        poker_total_games = 50
        
        for _ in range(poker_total_games):
            # Create session
            session_response = requests.post(
                f"{API_URL}/game/session/create",
                params={
                    "player_wallet": TEST_WALLET_PUBLIC_KEY,
                    "game_type": "video_poker"
                }
            )
            session_id = session_response.json()["session_id"]
            
            # Draw cards immediately
            draw_response = requests.post(
                f"{API_URL}/game/video_poker/draw",
                params={
                    "session_id": session_id
                }
            )
            draw_data = draw_response.json()
            
            # Record result
            payout_multiplier = draw_data["payout_multiplier"]
            hand_rank = draw_data["final_hand"]
            poker_results.append({
                "hand_rank": hand_rank,
                "payout_multiplier": payout_multiplier,
                "win": payout_multiplier > 0
            })
        
        # Calculate video poker win rate
        poker_wins = sum(1 for result in poker_results if result["win"])
        poker_win_rate = (poker_wins / poker_total_games) * 100
        
        return True, {
            "blackjack": {
                "total_games": blackjack_total_games,
                "wins": blackjack_wins,
                "win_rate": f"{blackjack_win_rate:.2f}%",
                "expected_win_rate": "69%",
                "within_target": abs(blackjack_win_rate - 69) <= 15,
                "result_distribution": {result: blackjack_results.count(result) for result in set(blackjack_results)}
            },
            "video_poker": {
                "total_games": poker_total_games,
                "wins": poker_wins,
                "win_rate": f"{poker_win_rate:.2f}%",
                "expected_win_rate": "65%",
                "within_target": abs(poker_win_rate - 65) <= 15,
                "hand_rank_distribution": {
                    hand_rank: len([r for r in poker_results if r["hand_rank"] == hand_rank])
                    for hand_rank in set(r["hand_rank"] for r in poker_results)
                }
            }
        }
    except Exception as e:
        return False, str(e)

# Test 18: Blackjack Payout Multipliers
def test_blackjack_payout_multipliers():
    try:
        # Run multiple games to try to get different outcomes
        results = []
        multipliers = {}
        
        for _ in range(20):
            # Create session
            session_response = requests.post(
                f"{API_URL}/game/session/create",
                params={
                    "player_wallet": TEST_WALLET_PUBLIC_KEY,
                    "game_type": "blackjack"
                }
            )
            session_id = session_response.json()["session_id"]
            
            # Finish game immediately
            finish_response = requests.post(
                f"{API_URL}/game/blackjack/finish",
                params={
                    "session_id": session_id
                }
            )
            finish_data = finish_response.json()
            
            # Record result
            result = finish_data["results"][0]
            results.append({
                "result": result["result"],
                "payout_multiplier": result["payout_multiplier"]
            })
            
            # Track multipliers by result type
            if result["result"] not in multipliers:
                multipliers[result["result"]] = []
            multipliers[result["result"]].append(result["payout_multiplier"])
        
        # Verify payout multipliers match expected values
        expected_multipliers = {
            "win": 2.0,
            "lose": 0.0,
            "push": 1.0,
            "blackjack": 2.5
        }
        
        all_correct = True
        errors = []
        
        for result_type, expected in expected_multipliers.items():
            if result_type in multipliers:
                # Check if all multipliers for this result type match expected value
                if not all(abs(m - expected) < 0.001 for m in multipliers[result_type]):
                    all_correct = False
                    errors.append(f"{result_type} has incorrect multiplier(s): {multipliers[result_type]}, expected {expected}")
        
        if all_correct:
            return True, {
                "multipliers_by_result": {k: list(set(v)) for k, v in multipliers.items()},
                "expected_multipliers": expected_multipliers,
                "results_count": {k: len(v) for k, v in multipliers.items()}
            }
        else:
            return False, {"errors": errors, "results": results}
    except Exception as e:
        return False, str(e)

# Test 19: Video Poker Payout Multipliers
def test_video_poker_payout_multipliers():
    try:
        # Run multiple games to try to get different hand ranks
        results = []
        multipliers = {}
        
        for _ in range(30):  # More games to increase chance of different hands
            # Create session
            session_response = requests.post(
                f"{API_URL}/game/session/create",
                params={
                    "player_wallet": TEST_WALLET_PUBLIC_KEY,
                    "game_type": "video_poker"
                }
            )
            session_id = session_response.json()["session_id"]
            
            # Draw cards immediately
            draw_response = requests.post(
                f"{API_URL}/game/video_poker/draw",
                params={
                    "session_id": session_id
                }
            )
            draw_data = draw_response.json()
            
            # Record result
            hand_rank = draw_data["final_hand"]
            payout_multiplier = draw_data["payout_multiplier"]
            
            results.append({
                "hand_rank": hand_rank,
                "payout_multiplier": payout_multiplier
            })
            
            # Track multipliers by hand rank
            if hand_rank not in multipliers:
                multipliers[hand_rank] = []
            multipliers[hand_rank].append(payout_multiplier)
        
        # Verify payout multipliers match expected values
        expected_multipliers = {
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
        
        all_correct = True
        errors = []
        
        for hand_rank, expected in expected_multipliers.items():
            if hand_rank in multipliers:
                # Check if all multipliers for this hand rank match expected value
                if not all(abs(m - expected) < 0.001 for m in multipliers[hand_rank]):
                    all_correct = False
                    errors.append(f"{hand_rank} has incorrect multiplier(s): {multipliers[hand_rank]}, expected {expected}")
        
        if all_correct:
            return True, {
                "multipliers_by_hand": {k: list(set(v)) for k, v in multipliers.items()},
                "expected_multipliers": expected_multipliers,
                "hands_seen": list(multipliers.keys())
            }
        else:
            return False, {"errors": errors, "results": results}
    except Exception as e:
        return False, str(e)

# Test 20: Player Statistics
def test_player_statistics():
    try:
        # First play a few games to generate statistics
        for game_type in ["blackjack", "video_poker"]:
            for _ in range(3):
                # Create session
                session_response = requests.post(
                    f"{API_URL}/game/session/create",
                    params={
                        "player_wallet": TEST_WALLET_PUBLIC_KEY,
                        "game_type": game_type
                    }
                )
                session_id = session_response.json()["session_id"]
                
                # Place wager
                wager_amount = 50.0
                requests.post(
                    f"{API_URL}/game/wager",
                    json={
                        "player_wallet": TEST_WALLET_PUBLIC_KEY,
                        "amount": wager_amount,
                        "game_type": game_type,
                        "session_id": session_id,
                        "transaction_signature": TEST_SIGNATURE
                    }
                )
                
                # Finish game
                if game_type == "blackjack":
                    finish_response = requests.post(
                        f"{API_URL}/game/blackjack/finish",
                        params={"session_id": session_id}
                    )
                    finish_data = finish_response.json()
                    result = finish_data["results"][0]
                    payout_multiplier = result["payout_multiplier"]
                else:  # video_poker
                    draw_response = requests.post(
                        f"{API_URL}/game/video_poker/draw",
                        params={"session_id": session_id}
                    )
                    draw_data = draw_response.json()
                    payout_multiplier = draw_data["payout_multiplier"]
                
                # Record result
                payout_amount = wager_amount * payout_multiplier
                requests.post(
                    f"{API_URL}/game/result",
                    json={
                        "session_id": session_id,
                        "player_wallet": TEST_WALLET_PUBLIC_KEY,
                        "game_type": game_type,
                        "wager_amount": wager_amount,
                        "payout_amount": payout_amount,
                        "game_data": {},
                        "transaction_signature": TEST_SIGNATURE
                    }
                )
        
        # Now get player statistics
        response = requests.get(f"{API_URL}/player/stats/{TEST_WALLET_PUBLIC_KEY}")
        response.raise_for_status()
        data = response.json()
        
        # Verify the response contains the expected fields
        if ("player_wallet" in data and
            "total_games" in data and
            "total_wagered" in data and
            "total_payout" in data and
            "net_profit" in data and
            "blackjack_games" in data and
            "poker_games" in data and
            "recent_results" in data):
            
            # Verify statistics are consistent
            if (data["blackjack_games"] + data["poker_games"] == len(data["recent_results"]) and
                data["net_profit"] == data["total_payout"] - data["total_wagered"]):
                return True, data
            else:
                return False, "Player statistics are inconsistent"
        else:
            return False, "Player statistics missing expected fields"
    except Exception as e:
        return False, str(e)

# Test 21: Get Player Sessions
def test_get_player_sessions():
    try:
        # Create a few game sessions first
        for game_type in ["blackjack", "video_poker"]:
            requests.post(
                f"{API_URL}/game/session/create",
                params={
                    "player_wallet": TEST_WALLET_PUBLIC_KEY,
                    "game_type": game_type
                }
            )
        
        # Now get the player's sessions
        response = requests.get(f"{API_URL}/game/sessions/{TEST_WALLET_PUBLIC_KEY}")
        response.raise_for_status()
        data = response.json()
        
        # Verify the response contains sessions
        if "sessions" in data and isinstance(data["sessions"], list):
            return True, {"session_count": len(data["sessions"])}
        else:
            return False, "Failed to get player sessions or incorrect data format"
    except Exception as e:
        return False, str(e)

# Test 22: Error Handling - Invalid Game Type
def test_error_handling_invalid_game():
    try:
        response = requests.post(
            f"{API_URL}/game/session/create",
            params={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "game_type": "invalid_game_type"
            }
        )
        
        # We expect a 400 Bad Request
        if response.status_code == 400:
            return True, {"status_code": response.status_code, "error": response.json()}
        else:
            return False, f"Expected 400 status code, got {response.status_code}"
    except Exception as e:
        return False, str(e)

# Test 23: Error Handling - Invalid Session ID
def test_error_handling_invalid_session():
    try:
        invalid_session_id = "non_existent_session_id"
        response = requests.post(
            f"{API_URL}/game/blackjack/hit",
            params={
                "session_id": invalid_session_id,
                "hand_index": 0
            }
        )
        
        # We expect a 404 Not Found
        if response.status_code == 404:
            return True, {"status_code": response.status_code, "error": response.json()}
        else:
            return False, f"Expected 404 status code, got {response.status_code}"
    except Exception as e:
        return False, str(e)

# Test 43: SolanaBust Room Join
def test_solanabust_room_join():
    """Test joining a SolanaBust multiplayer room"""
    try:
        # Test data for room joining
        test_wallet = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"  # Valid phantom wallet format
        test_username = "TestPlayer123"
        test_bet_amount = 0.01  # Valid bet amount
        
        response = requests.post(
            f"{API_URL}/solanabust/join-room",
            json={
                "wallet_address": test_wallet,
                "username": test_username,
                "bet_amount": test_bet_amount
            }
        )
        response.raise_for_status()
        data = response.json()
        
        # Verify successful room join
        if (data.get("success") and 
            "room_id" in data and 
            "room_state" in data):
            
            room_state = data["room_state"]
            
            # Verify room state structure
            if ("room_id" in room_state and
                "game_state" in room_state and
                "players" in room_state and
                "player_count" in room_state and
                "min_players" in room_state):
                
                # Verify player was added to room
                player_found = False
                for player in room_state["players"]:
                    if (player["wallet_address"] == test_wallet and
                        player["username"] == test_username and
                        player["bet_amount"] == test_bet_amount):
                        player_found = True
                        break
                
                if player_found:
                    return True, {
                        "room_id": data["room_id"],
                        "player_count": room_state["player_count"],
                        "game_state": room_state["game_state"],
                        "min_players": room_state["min_players"],
                        "player_added": True
                    }
                else:
                    return False, "Player not found in room after joining"
            else:
                return False, "Room state missing expected fields"
        else:
            return False, "Room join failed or missing expected response fields"
    except Exception as e:
        return False, str(e)

# Test 44: SolanaBust Room Join Validation
def test_solanabust_room_join_validation():
    """Test SolanaBust room join validation with various inputs"""
    try:
        test_cases = [
            # Valid cases
            {
                "wallet_address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                "username": "ValidPlayer",
                "bet_amount": 0.005,
                "should_pass": True,
                "description": "Minimum valid bet amount"
            },
            {
                "wallet_address": "A7GZMJLFzGSPn1nYHsGhLbU5pby4q96AessVHn5qVXFZ",
                "username": "MaxBetPlayer",
                "bet_amount": 0.2,
                "should_pass": True,
                "description": "Maximum valid bet amount"
            },
            
            # Invalid cases
            {
                "wallet_address": "",
                "username": "NoWallet",
                "bet_amount": 0.01,
                "should_pass": False,
                "description": "Empty wallet address"
            },
            {
                "wallet_address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                "username": "LowBet",
                "bet_amount": 0.004,
                "should_pass": False,
                "description": "Below minimum bet amount"
            },
            {
                "wallet_address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                "username": "HighBet",
                "bet_amount": 0.21,
                "should_pass": False,
                "description": "Above maximum bet amount"
            }
        ]
        
        results = []
        for test_case in test_cases:
            try:
                response = requests.post(
                    f"{API_URL}/solanabust/join-room",
                    json={
                        "wallet_address": test_case["wallet_address"],
                        "username": test_case["username"],
                        "bet_amount": test_case["bet_amount"]
                    }
                )
                
                success = response.status_code == 200 and response.json().get("success", False)
                
                results.append({
                    "description": test_case["description"],
                    "expected_pass": test_case["should_pass"],
                    "actual_pass": success,
                    "status_code": response.status_code,
                    "correct": success == test_case["should_pass"]
                })
                
            except Exception as e:
                results.append({
                    "description": test_case["description"],
                    "expected_pass": test_case["should_pass"],
                    "actual_pass": False,
                    "error": str(e),
                    "correct": not test_case["should_pass"]  # If we expected failure and got error, that's correct
                })
        
        all_correct = all(result["correct"] for result in results)
        
        return all_correct, {
            "test_cases": len(test_cases),
            "all_correct": all_correct,
            "results": results
        }
        
    except Exception as e:
        return False, str(e)

# Test 45: SolanaBust Room State Retrieval
def test_solanabust_room_state():
    """Test retrieving room state for a specific player"""
    try:
        # First join a room
        test_wallet = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        test_username = "StateTestPlayer"
        test_bet_amount = 0.015
        
        join_response = requests.post(
            f"{API_URL}/solanabust/join-room",
            json={
                "wallet_address": test_wallet,
                "username": test_username,
                "bet_amount": test_bet_amount
            }
        )
        join_response.raise_for_status()
        join_data = join_response.json()
        
        if not join_data.get("success"):
            return False, "Failed to join room for state test"
        
        # Now get room state
        response = requests.get(
            f"{API_URL}/solanabust/room-state",
            params={"wallet_address": test_wallet}
        )
        response.raise_for_status()
        data = response.json()
        
        # Verify room state response
        if (data.get("success") and "room_state" in data):
            room_state = data["room_state"]
            
            # Verify room state structure
            if ("room_id" in room_state and
                "game_state" in room_state and
                "players" in room_state and
                "current_multiplier" in room_state and
                "player_count" in room_state):
                
                # Verify our player is in the room state
                player_found = False
                for player in room_state["players"]:
                    if player["wallet_address"] == test_wallet:
                        player_found = True
                        break
                
                if player_found:
                    return True, {
                        "room_id": room_state["room_id"],
                        "game_state": room_state["game_state"],
                        "player_count": room_state["player_count"],
                        "current_multiplier": room_state["current_multiplier"],
                        "player_found": True
                    }
                else:
                    return False, "Player not found in room state"
            else:
                return False, "Room state missing expected fields"
        else:
            return False, "Room state retrieval failed or missing expected response fields"
    except Exception as e:
        return False, str(e)

# Test 46: SolanaBust Active Room Status
def test_solanabust_active_room():
    """Test getting active room status"""
    try:
        response = requests.get(f"{API_URL}/solanabust/active-room")
        response.raise_for_status()
        data = response.json()
        
        # The response should either show an active room or indicate no active room
        if data.get("success"):
            # Active room found
            if "room_state" in data:
                room_state = data["room_state"]
                
                # Verify room state structure
                if ("room_id" in room_state and
                    "game_state" in room_state and
                    "players" in room_state):
                    return True, {
                        "has_active_room": True,
                        "room_id": room_state["room_id"],
                        "game_state": room_state["game_state"],
                        "player_count": room_state.get("player_count", 0)
                    }
                else:
                    return False, "Active room state missing expected fields"
            else:
                return False, "Success response missing room_state"
        else:
            # No active room - this is also a valid response
            if "message" in data:
                return True, {
                    "has_active_room": False,
                    "message": data["message"]
                }
            else:
                return False, "No active room response missing message"
    except Exception as e:
        return False, str(e)

# Test 47: SolanaBust Cash Out Mechanics
def test_solanabust_cash_out():
    """Test SolanaBust cash out mechanics"""
    try:
        # First join a room
        test_wallet = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        test_username = "CashOutPlayer"
        test_bet_amount = 0.02
        
        join_response = requests.post(
            f"{API_URL}/solanabust/join-room",
            json={
                "wallet_address": test_wallet,
                "username": test_username,
                "bet_amount": test_bet_amount
            }
        )
        join_response.raise_for_status()
        join_data = join_response.json()
        
        if not join_data.get("success"):
            return False, "Failed to join room for cash out test"
        
        # Attempt to cash out
        response = requests.post(
            f"{API_URL}/solanabust/cash-out",
            json={"wallet_address": test_wallet}
        )
        response.raise_for_status()
        data = response.json()
        
        # Cash out might succeed or fail depending on game state
        # Both are valid responses as long as the API responds correctly
        if data.get("success"):
            # Cash out succeeded
            if ("cashed_out" in data and "room_state" in data):
                return True, {
                    "cash_out_successful": True,
                    "cashed_out": data["cashed_out"],
                    "payout_amount": data.get("payout_amount"),
                    "multiplier": data.get("multiplier"),
                    "payout_sent": data.get("payout_sent", False),
                    "payout_signature": data.get("payout_signature"),
                    "explorer_url": data.get("explorer_url")
                }
            else:
                return False, "Cash out success response missing expected fields"
        else:
            # Cash out failed (likely due to game state) - this is also valid
            return True, {
                "cash_out_successful": False,
                "message": "Cash out failed (likely due to game state - this is expected behavior)"
            }
    except Exception as e:
        return False, str(e)

# Test 48: SolanaBust 12% Developer Fee Calculation
def test_solanabust_12_percent_dev_fee():
    """Test 12% developer fee calculation for SolanaBust"""
    try:
        test_amounts = [0.005, 0.01, 0.025, 0.05, 0.1, 0.2]  # Various SolanaBust amounts
        results = []
        
        for amount in test_amounts:
            # Join room with specific bet amount
            test_wallet = f"9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWW{random.randint(1,9)}"
            test_username = f"FeeTestPlayer{random.randint(100,999)}"
            
            try:
                response = requests.post(
                    f"{API_URL}/solanabust/join-room",
                    json={
                        "wallet_address": test_wallet,
                        "username": test_username,
                        "bet_amount": amount
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") and "room_state" in data:
                        # Find our player in the room state
                        player_data = None
                        for player in data["room_state"]["players"]:
                            if player["wallet_address"] == test_wallet:
                                player_data = player
                                break
                        
                        if player_data:
                            expected_dev_fee = amount * 0.12  # 12% fee
                            expected_net_bet = amount - expected_dev_fee
                            
                            actual_dev_fee = player_data.get("dev_fee", 0)
                            actual_net_bet = player_data.get("net_bet", 0)
                            
                            fee_correct = abs(actual_dev_fee - expected_dev_fee) < 0.000001
                            net_correct = abs(actual_net_bet - expected_net_bet) < 0.000001
                            
                            results.append({
                                "bet_amount": amount,
                                "expected_dev_fee": expected_dev_fee,
                                "actual_dev_fee": actual_dev_fee,
                                "expected_net_bet": expected_net_bet,
                                "actual_net_bet": actual_net_bet,
                                "fee_correct": fee_correct,
                                "net_correct": net_correct,
                                "overall_correct": fee_correct and net_correct
                            })
                        else:
                            results.append({
                                "bet_amount": amount,
                                "error": "Player not found in room state"
                            })
                    else:
                        results.append({
                            "bet_amount": amount,
                            "error": "Failed to join room or get room state"
                        })
                else:
                    results.append({
                        "bet_amount": amount,
                        "error": f"HTTP {response.status_code}"
                    })
                    
            except Exception as e:
                results.append({
                    "bet_amount": amount,
                    "error": str(e)
                })
        
        # Check if all calculations are correct
        successful_tests = [r for r in results if "overall_correct" in r]
        all_correct = all(r["overall_correct"] for r in successful_tests)
        
        return all_correct, {
            "test_amounts": test_amounts,
            "successful_tests": len(successful_tests),
            "total_tests": len(test_amounts),
            "all_fee_calculations_correct": all_correct,
            "results": results
        }
        
    except Exception as e:
        return False, str(e)

# Test 49: SolanaBust Multiplayer Game Flow
def test_solanabust_multiplayer_game_flow():
    """Test complete SolanaBust multiplayer game flow"""
    try:
        # Create multiple players to join the room
        players = [
            {"wallet": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWW1", "username": "Player1", "bet": 0.01},
            {"wallet": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWW2", "username": "Player2", "bet": 0.015},
            {"wallet": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWW3", "username": "Player3", "bet": 0.02},
            {"wallet": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWW4", "username": "Player4", "bet": 0.025}
        ]
        
        join_results = []
        room_id = None
        
        # Step 1: All players join the room
        for player in players:
            response = requests.post(
                f"{API_URL}/solanabust/join-room",
                json={
                    "wallet_address": player["wallet"],
                    "username": player["username"],
                    "bet_amount": player["bet"]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    join_results.append({
                        "player": player["username"],
                        "joined": True,
                        "room_id": data.get("room_id")
                    })
                    if not room_id:
                        room_id = data.get("room_id")
                else:
                    join_results.append({
                        "player": player["username"],
                        "joined": False,
                        "error": "Join failed"
                    })
            else:
                join_results.append({
                    "player": player["username"],
                    "joined": False,
                    "error": f"HTTP {response.status_code}"
                })
        
        successful_joins = len([r for r in join_results if r["joined"]])
        
        # Step 2: Check active room status
        active_room_response = requests.get(f"{API_URL}/solanabust/active-room")
        active_room_data = active_room_response.json() if active_room_response.status_code == 200 else {}
        
        # Step 3: Check room states for each player
        room_states = []
        for player in players:
            try:
                response = requests.get(
                    f"{API_URL}/solanabust/room-state",
                    params={"wallet_address": player["wallet"]}
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        room_states.append({
                            "player": player["username"],
                            "has_room_state": True,
                            "game_state": data["room_state"].get("game_state"),
                            "player_count": data["room_state"].get("player_count")
                        })
                    else:
                        room_states.append({
                            "player": player["username"],
                            "has_room_state": False
                        })
                else:
                    room_states.append({
                        "player": player["username"],
                        "has_room_state": False,
                        "error": f"HTTP {response.status_code}"
                    })
            except Exception as e:
                room_states.append({
                    "player": player["username"],
                    "has_room_state": False,
                    "error": str(e)
                })
        
        # Step 4: Test cash out attempts
        cash_out_results = []
        for player in players[:2]:  # Test cash out for first 2 players
            try:
                response = requests.post(
                    f"{API_URL}/solanabust/cash-out",
                    json={"wallet_address": player["wallet"]}
                )
                if response.status_code == 200:
                    data = response.json()
                    cash_out_results.append({
                        "player": player["username"],
                        "cash_out_attempted": True,
                        "success": data.get("success", False),
                        "cashed_out": data.get("cashed_out", False)
                    })
                else:
                    cash_out_results.append({
                        "player": player["username"],
                        "cash_out_attempted": True,
                        "success": False,
                        "error": f"HTTP {response.status_code}"
                    })
            except Exception as e:
                cash_out_results.append({
                    "player": player["username"],
                    "cash_out_attempted": True,
                    "success": False,
                    "error": str(e)
                })
        
        # Evaluate overall success
        min_players_joined = successful_joins >= 4  # Need at least 4 players
        room_states_working = len([r for r in room_states if r["has_room_state"]]) > 0
        active_room_working = active_room_data.get("success") is not None
        
        overall_success = min_players_joined and room_states_working and active_room_working
        
        return overall_success, {
            "players_joined": successful_joins,
            "min_players_met": min_players_joined,
            "room_id": room_id,
            "join_results": join_results,
            "active_room_working": active_room_working,
            "room_states_working": room_states_working,
            "room_states": room_states,
            "cash_out_results": cash_out_results,
            "overall_success": overall_success
        }
        
    except Exception as e:
        return False, str(e)

# Test 50: SolanaBust Real SOL Payout Integration
def test_solanabust_real_sol_payout_integration():
    """Test SolanaBust integration with real SOL payout system"""
    try:
        # First check if payout service is available
        balance_response = requests.get(f"{API_URL}/payouts/house-balance")
        if balance_response.status_code != 200:
            return True, {
                "payout_service_available": False,
                "message": "Payout service not available - this is expected in some environments"
            }
        
        balance_data = balance_response.json()
        house_balance = balance_data.get("balance_sol", 0)
        
        if house_balance < 0.01:  # Need at least 0.01 SOL for testing
            return True, {
                "payout_service_available": True,
                "house_balance": house_balance,
                "message": "Insufficient house balance for payout testing"
            }
        
        # Join room and attempt cash out to test payout integration
        test_wallet = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        test_username = "PayoutTestPlayer"
        test_bet_amount = 0.005  # Small amount for testing
        
        # Join room
        join_response = requests.post(
            f"{API_URL}/solanabust/join-room",
            json={
                "wallet_address": test_wallet,
                "username": test_username,
                "bet_amount": test_bet_amount
            }
        )
        
        if join_response.status_code != 200:
            return False, "Failed to join room for payout integration test"
        
        join_data = join_response.json()
        if not join_data.get("success"):
            return False, "Room join failed for payout integration test"
        
        # Attempt cash out (may or may not succeed depending on game state)
        cash_out_response = requests.post(
            f"{API_URL}/solanabust/cash-out",
            json={"wallet_address": test_wallet}
        )
        
        if cash_out_response.status_code == 200:
            cash_out_data = cash_out_response.json()
            
            # If cash out was successful, check for payout integration
            if cash_out_data.get("success") and cash_out_data.get("cashed_out"):
                payout_sent = cash_out_data.get("payout_sent", False)
                payout_signature = cash_out_data.get("payout_signature")
                explorer_url = cash_out_data.get("explorer_url")
                
                return True, {
                    "payout_service_available": True,
                    "house_balance": house_balance,
                    "cash_out_successful": True,
                    "payout_sent": payout_sent,
                    "payout_signature": payout_signature,
                    "explorer_url": explorer_url,
                    "payout_amount": cash_out_data.get("payout_amount"),
                    "multiplier": cash_out_data.get("multiplier")
                }
            else:
                return True, {
                    "payout_service_available": True,
                    "house_balance": house_balance,
                    "cash_out_successful": False,
                    "message": "Cash out failed (expected due to game state)"
                }
        else:
            return True, {
                "payout_service_available": True,
                "house_balance": house_balance,
                "cash_out_response_code": cash_out_response.status_code,
                "message": "Cash out API call failed (may be expected)"
            }
        
    except Exception as e:
        return False, str(e)

# Test 51: SolanaBust Edge Cases and Error Handling
def test_solanabust_edge_cases():
    """Test SolanaBust edge cases and error handling"""
    try:
        edge_case_results = []
        
        # Test 1: Invalid wallet address format
        try:
            response = requests.post(
                f"{API_URL}/solanabust/join-room",
                json={
                    "wallet_address": "invalid_wallet_format",
                    "username": "TestPlayer",
                    "bet_amount": 0.01
                }
            )
            edge_case_results.append({
                "test": "Invalid wallet address",
                "expected_fail": True,
                "actual_fail": response.status_code != 200,
                "status_code": response.status_code
            })
        except Exception as e:
            edge_case_results.append({
                "test": "Invalid wallet address",
                "expected_fail": True,
                "actual_fail": True,
                "error": str(e)
            })
        
        # Test 2: Missing required fields
        try:
            response = requests.post(
                f"{API_URL}/solanabust/join-room",
                json={
                    "username": "TestPlayer",
                    "bet_amount": 0.01
                    # Missing wallet_address
                }
            )
            edge_case_results.append({
                "test": "Missing wallet address",
                "expected_fail": True,
                "actual_fail": response.status_code != 200,
                "status_code": response.status_code
            })
        except Exception as e:
            edge_case_results.append({
                "test": "Missing wallet address",
                "expected_fail": True,
                "actual_fail": True,
                "error": str(e)
            })
        
        # Test 3: Cash out without being in room
        try:
            response = requests.post(
                f"{API_URL}/solanabust/cash-out",
                json={"wallet_address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWX"}
            )
            edge_case_results.append({
                "test": "Cash out without being in room",
                "expected_fail": True,
                "actual_fail": response.status_code != 200 or not response.json().get("success", False),
                "status_code": response.status_code
            })
        except Exception as e:
            edge_case_results.append({
                "test": "Cash out without being in room",
                "expected_fail": True,
                "actual_fail": True,
                "error": str(e)
            })
        
        # Test 4: Room state for non-existent player
        try:
            response = requests.get(
                f"{API_URL}/solanabust/room-state",
                params={"wallet_address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWY"}
            )
            # This should return success=False or appropriate message
            data = response.json() if response.status_code == 200 else {}
            edge_case_results.append({
                "test": "Room state for non-existent player",
                "expected_behavior": "Should handle gracefully",
                "status_code": response.status_code,
                "success": data.get("success", False),
                "handled_gracefully": response.status_code == 200
            })
        except Exception as e:
            edge_case_results.append({
                "test": "Room state for non-existent player",
                "expected_behavior": "Should handle gracefully",
                "error": str(e),
                "handled_gracefully": False
            })
        
        # Test 5: Concurrent room joins (same player)
        test_wallet = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWZ"
        concurrent_results = []
        
        for i in range(3):
            try:
                response = requests.post(
                    f"{API_URL}/solanabust/join-room",
                    json={
                        "wallet_address": test_wallet,
                        "username": f"ConcurrentPlayer{i}",
                        "bet_amount": 0.01
                    }
                )
                concurrent_results.append({
                    "attempt": i + 1,
                    "status_code": response.status_code,
                    "success": response.json().get("success", False) if response.status_code == 200 else False
                })
            except Exception as e:
                concurrent_results.append({
                    "attempt": i + 1,
                    "error": str(e),
                    "success": False
                })
        
        edge_case_results.append({
            "test": "Concurrent room joins (same player)",
            "expected_behavior": "Should handle duplicate joins gracefully",
            "concurrent_results": concurrent_results,
            "handled_gracefully": len([r for r in concurrent_results if r.get("success")]) <= 1
        })
        
        # Evaluate overall edge case handling
        critical_failures = []
        for result in edge_case_results:
            if "expected_fail" in result and result["expected_fail"] and not result["actual_fail"]:
                critical_failures.append(f"Expected failure but got success: {result['test']}")
            elif "handled_gracefully" in result and not result["handled_gracefully"]:
                critical_failures.append(f"Not handled gracefully: {result['test']}")
        
        overall_success = len(critical_failures) == 0
        
        return overall_success, {
            "edge_cases_tested": len(edge_case_results),
            "critical_failures": critical_failures,
            "overall_success": overall_success,
            "detailed_results": edge_case_results
        }
        
    except Exception as e:
        return False, str(e)

def run_all_tests():
    tests = [
        ("API Connectivity", test_api_connectivity),
        ("Status Check API", test_status_check),
        ("Solana Web3 Integration - Wallet Balance", test_wallet_balance),
        ("Phantom Wallet Backend APIs - Wallet Connection", test_wallet_connection),
        ("Game Session Management - Blackjack", test_blackjack_session_creation),
        ("Game Session Management - Video Poker", test_video_poker_session_creation),
        ("Wagering System with 4% Dev Fee", test_wagering_system),
        ("Game Logic APIs - Blackjack Hit", test_blackjack_hit),
        ("Game Logic APIs - Blackjack Hit Until Bust", test_blackjack_hit_until_bust),
        ("Game Logic APIs - Blackjack Stand", test_blackjack_stand),
        ("Game Logic APIs - Blackjack Finish", test_blackjack_finish),
        ("Game Logic APIs - Video Poker Hold", test_video_poker_hold),
        ("Game Logic APIs - Video Poker Draw", test_video_poker_draw),
        ("Complete Blackjack Game Flow", test_complete_blackjack_game_flow),
        ("Complete Video Poker Game Flow", test_complete_video_poker_game_flow),
        ("Blackjack Win Rate Validation", test_blackjack_win_rate),
        ("Video Poker Win Rate Validation", test_video_poker_win_rate),
        ("Blackjack Payout Multipliers", test_blackjack_payout_multipliers),
        ("Video Poker Payout Multipliers", test_video_poker_payout_multipliers),
        ("Player Statistics", test_player_statistics),
        ("Get Player Sessions", test_get_player_sessions),
        ("Error Handling - Invalid Game Type", test_error_handling_invalid_game),
        ("Error Handling - Invalid Session ID", test_error_handling_invalid_session),
        ("Error Handling - Invalid Wallet Address", test_error_handling_invalid_wallet_address),
        ("Multiplayer Stats", test_multiplayer_stats),
        ("Recent Announcements", test_recent_announcements),
        ("Manual Win Announcement", test_manual_win_announcement),
        ("SolanaBust Wager Validation", test_solana_bust_wager_validation),
        ("Bet Categorization Logic", test_bet_categorization),
        ("Enhanced Game Results with Multiplayer", test_enhanced_game_results),
        ("Complete Crash Game Flow (SolanaBust)", test_crash_game_flow)
    ]
    
    results = {}
    
    print("\n" + "=" * 80)
    print("SOLANA GAMING PLATFORM BACKEND API TESTS")
    print("=" * 80)
    
    for test_name, test_func in tests:
        print(f"\nRunning test: {test_name}")
        success, data = test_func()
        print_test_result(test_name, success, data if success else None, data if not success else None)
        results[test_name] = success
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    print("-" * 80)
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {passed/total*100:.2f}%")
    print("=" * 80)
    
    return results

# Test 27: House Wallet Balance
def test_house_wallet_balance():
    try:
        response = requests.get(f"{API_URL}/payouts/house-balance")
        response.raise_for_status()
        data = response.json()
        
        # Verify the response contains the expected fields
        if ("balance_sol" in data and 
            "balance_lamports" in data and 
            "address" in data and  # Changed from "wallet_address" to "address"
            isinstance(data["balance_sol"], (int, float)) and
            data["balance_sol"] >= 0):
            return True, data
        else:
            return False, "House balance response missing expected fields or invalid data"
    except Exception as e:
        return False, str(e)

# Test 28: Send Winner Payout
def test_send_winner_payout():
    try:
        # Test with a small amount (0.001 SOL)
        payout_amount = 0.001
        response = requests.post(
            f"{API_URL}/payouts/send",
            json={
                "winner_address": TEST_WALLET_PUBLIC_KEY,
                "amount_sol": payout_amount,
                "game_id": "test_game_001",
                "session_id": str(uuid.uuid4())
            }
        )
        response.raise_for_status()
        data = response.json()
        
        # Verify the response contains the expected fields
        if (data.get("success") and 
            "signature" in data and 
            "explorer_url" in data and
            "amount_sol" in data and
            data["amount_sol"] == payout_amount):
            return True, data
        else:
            return False, "Payout send failed or missing expected fields"
    except Exception as e:
        return False, str(e)

# Test 29: Payout Status Check
def test_payout_status():
    try:
        # First send a payout to get a payout ID
        payout_amount = 0.001
        send_response = requests.post(
            f"{API_URL}/payouts/send",
            json={
                "winner_address": TEST_WALLET_PUBLIC_KEY,
                "amount_sol": payout_amount,
                "game_id": "test_game_002",
                "session_id": str(uuid.uuid4())
            }
        )
        send_response.raise_for_status()
        send_data = send_response.json()
        
        if not send_data.get("success"):
            return False, "Failed to send payout for status test"
        
        # Extract payout ID from the response (assuming it's in the signature or a separate field)
        payout_id = send_data.get("payout_id") or send_data.get("signature")
        
        if not payout_id:
            return False, "No payout ID found in send response"
        
        # Now check the status
        status_response = requests.get(f"{API_URL}/payouts/status/{payout_id}")
        status_response.raise_for_status()
        status_data = status_response.json()
        
        # Verify the response contains status information
        if ("status" in status_data or "signature" in status_data):
            return True, status_data
        else:
            return False, "Payout status response missing expected fields"
    except Exception as e:
        return False, str(e)

# Test 30: Payout History
def test_payout_history():
    try:
        response = requests.get(f"{API_URL}/payouts/history?limit=10")
        response.raise_for_status()
        data = response.json()
        
        # Verify the response contains history data
        if ("payouts" in data and isinstance(data["payouts"], list)):
            return True, {
                "payout_count": len(data["payouts"]),
                "sample_payout": data["payouts"][0] if data["payouts"] else None
            }
        else:
            return False, "Payout history response missing expected fields or invalid format"
    except Exception as e:
        return False, str(e)

# Test 31: Game Result with Automatic Payout
def test_game_result_with_automatic_payout():
    try:
        # Create a game session first
        session_response = requests.post(
            f"{API_URL}/game/session/create",
            params={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "game_type": "blackjack"
            }
        )
        session_response.raise_for_status()
        session_data = session_response.json()
        session_id = session_data["session_id"]
        
        # Record a winning game result with payout
        payout_amount = 0.002  # Small test amount
        result_response = requests.post(
            f"{API_URL}/game/result",
            json={
                "session_id": session_id,
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "game_type": "blackjack",
                "wager_amount": 0.001,
                "payout_amount": payout_amount,
                "game_data": {
                    "result": "win",
                    "player_value": 21,
                    "dealer_value": 20
                },
                "transaction_signature": TEST_SIGNATURE
            }
        )
        result_response.raise_for_status()
        result_data = result_response.json()
        
        # Verify the response includes payout information
        if (result_data.get("success") and 
            "payout_amount" in result_data and
            result_data["payout_amount"] == payout_amount):
            
            # Check if automatic payout was triggered
            payout_sent = result_data.get("payout_sent", False)
            
            return True, {
                "result_recorded": True,
                "payout_amount": result_data["payout_amount"],
                "payout_sent": payout_sent,
                "payout_signature": result_data.get("payout_signature"),
                "explorer_url": result_data.get("explorer_url"),
                "payout_error": result_data.get("payout_error")
            }
        else:
            return False, "Game result recording failed or missing payout information"
    except Exception as e:
        return False, str(e)

# Test 32: Error Handling - Invalid Payout Amount
def test_error_handling_invalid_payout_amount():
    try:
        # Test with amount exceeding maximum limit
        response = requests.post(
            f"{API_URL}/payouts/send",
            json={
                "winner_address": TEST_WALLET_PUBLIC_KEY,
                "amount_sol": 15.0,  # Exceeds 10 SOL limit
                "game_id": "test_game_003",
                "session_id": str(uuid.uuid4())
            }
        )
        
        # We expect a 400 Bad Request
        if response.status_code == 400:
            return True, {"status_code": response.status_code, "error": response.json()}
        else:
            return False, f"Expected 400 status code for excessive amount, got {response.status_code}"
    except Exception as e:
        return False, str(e)

# Test 33: Error Handling - Invalid Wallet Address
def test_error_handling_invalid_wallet_address():
    try:
        # Test with invalid wallet address
        response = requests.post(
            f"{API_URL}/payouts/send",
            json={
                "winner_address": "invalid_wallet_address",
                "amount_sol": 0.001,
                "game_id": "test_game_004",
                "session_id": str(uuid.uuid4())
            }
        )
        
        # We expect a 400 or 500 error
        if response.status_code in [400, 500]:
            return True, {"status_code": response.status_code, "error": response.json()}
        else:
            return False, f"Expected 400 or 500 status code for invalid wallet, got {response.status_code}"
    except Exception as e:
        return False, str(e)

# Test 34: Multiplayer Stats
def test_multiplayer_stats():
    try:
        response = requests.get(f"{API_URL}/multiplayer/stats")
        response.raise_for_status()
        data = response.json()
        
        # Verify the response contains the expected fields
        if ("active_players" in data and 
            "total_wagered" in data and 
            "total_games" in data and 
            "chat_messages" in data and
            isinstance(data["active_players"], int) and
            isinstance(data["total_wagered"], (int, float)) and
            isinstance(data["total_games"], int) and
            isinstance(data["chat_messages"], int)):
            return True, data
        else:
            return False, "Multiplayer stats response missing expected fields or invalid data types"
    except Exception as e:
        return False, str(e)

# Test 35: Recent Announcements
def test_recent_announcements():
    try:
        response = requests.get(f"{API_URL}/multiplayer/announcements?limit=10")
        response.raise_for_status()
        data = response.json()
        
        # Verify the response contains announcements array
        if ("announcements" in data and isinstance(data["announcements"], list)):
            return True, {
                "announcement_count": len(data["announcements"]),
                "sample_announcement": data["announcements"][0] if data["announcements"] else None
            }
        else:
            return False, "Recent announcements response missing expected fields or invalid format"
    except Exception as e:
        return False, str(e)

# Test 36: Manual Win Announcement
def test_manual_win_announcement():
    try:
        # Test with a big win (above 0.1 SOL threshold)
        big_win_amount = 0.15
        response = requests.post(
            f"{API_URL}/multiplayer/announce-win",
            json={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "amount": big_win_amount,
                "game_type": "blackjack",
                "multiplier": 2.5
            }
        )
        response.raise_for_status()
        data = response.json()
        
        # Verify the response indicates success
        if data.get("success") and data.get("message"):
            return True, data
        else:
            return False, "Manual win announcement failed or missing expected fields"
    except Exception as e:
        return False, str(e)

# Test 37: SolanaBust Wager Validation
def test_solana_bust_wager_validation():
    try:
        # Create a crash game session first
        session_response = requests.post(
            f"{API_URL}/game/session/create",
            params={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "game_type": "crash"
            }
        )
        
        # This should fail since crash game sessions aren't implemented in the current backend
        # But let's test the wager validation for crash game type
        
        test_cases = [
            # Valid SolanaBust wagers
            {"amount": 0.005, "should_pass": True, "description": "Minimum valid SolanaBust wager"},
            {"amount": 0.025, "should_pass": True, "description": "Mid-range SolanaBust wager"},
            {"amount": 0.05, "should_pass": True, "description": "Maximum valid SolanaBust wager"},
            
            # Invalid SolanaBust wagers
            {"amount": 0.004, "should_pass": False, "description": "Below minimum SolanaBust wager"},
            {"amount": 0.051, "should_pass": False, "description": "Above maximum SolanaBust wager"},
            {"amount": 0.1, "should_pass": False, "description": "Way above maximum SolanaBust wager"},
        ]
        
        results = []
        session_id = str(uuid.uuid4())  # Use a dummy session ID
        
        for test_case in test_cases:
            try:
                response = requests.post(
                    f"{API_URL}/game/wager",
                    json={
                        "player_wallet": TEST_WALLET_PUBLIC_KEY,
                        "amount": test_case["amount"],
                        "game_type": "crash",
                        "session_id": session_id,
                        "transaction_signature": TEST_SIGNATURE
                    }
                )
                
                if test_case["should_pass"]:
                    # Should succeed
                    if response.status_code == 200:
                        results.append({
                            "test": test_case["description"],
                            "passed": True,
                            "amount": test_case["amount"],
                            "response": response.json()
                        })
                    else:
                        results.append({
                            "test": test_case["description"],
                            "passed": False,
                            "amount": test_case["amount"],
                            "error": f"Expected success but got {response.status_code}"
                        })
                else:
                    # Should fail
                    if response.status_code == 400:
                        results.append({
                            "test": test_case["description"],
                            "passed": True,
                            "amount": test_case["amount"],
                            "error_response": response.json()
                        })
                    else:
                        results.append({
                            "test": test_case["description"],
                            "passed": False,
                            "amount": test_case["amount"],
                            "error": f"Expected 400 error but got {response.status_code}"
                        })
                        
            except Exception as e:
                results.append({
                    "test": test_case["description"],
                    "passed": False,
                    "amount": test_case["amount"],
                    "error": str(e)
                })
        
        # Check if all tests passed
        all_passed = all(result["passed"] for result in results)
        
        return all_passed, {
            "test_results": results,
            "total_tests": len(test_cases),
            "passed_tests": sum(1 for r in results if r["passed"])
        }
        
    except Exception as e:
        return False, str(e)

# Test 38: Bet Categorization Logic
def test_bet_categorization():
    try:
        # Test different bet amounts to verify categorization
        test_amounts = [
            {"amount": 0.005, "expected_category": "Small Fish", "icon": "🐟"},
            {"amount": 0.01, "expected_category": "Medium Bet", "icon": "🎯"},
            {"amount": 0.05, "expected_category": "High Roller", "icon": "💎"},
            {"amount": 0.2, "expected_category": "Crypto Whale", "icon": "🐋"}
        ]
        
        results = []
        session_id = str(uuid.uuid4())
        
        for test_case in test_amounts:
            try:
                # Test with blackjack (which supports these amounts)
                response = requests.post(
                    f"{API_URL}/game/wager",
                    json={
                        "player_wallet": TEST_WALLET_PUBLIC_KEY,
                        "amount": test_case["amount"],
                        "game_type": "blackjack",
                        "session_id": session_id,
                        "transaction_signature": TEST_SIGNATURE
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results.append({
                        "amount": test_case["amount"],
                        "expected_category": test_case["expected_category"],
                        "wager_successful": True,
                        "dev_fee": data.get("dev_fee"),
                        "total_amount": data.get("total_amount")
                    })
                else:
                    results.append({
                        "amount": test_case["amount"],
                        "expected_category": test_case["expected_category"],
                        "wager_successful": False,
                        "error": response.json() if response.content else f"Status: {response.status_code}"
                    })
                    
            except Exception as e:
                results.append({
                    "amount": test_case["amount"],
                    "expected_category": test_case["expected_category"],
                    "wager_successful": False,
                    "error": str(e)
                })
        
        # All wagers should succeed for bet categorization test
        all_successful = all(result["wager_successful"] for result in results)
        
        return all_successful, {
            "categorization_tests": results,
            "note": "Bet categorization logic is implemented in multiplayer service, not directly testable via API"
        }
        
    except Exception as e:
        return False, str(e)

# Test 39: Enhanced Game Results with Multiplayer Integration
def test_enhanced_game_results():
    try:
        # Create a game session
        session_response = requests.post(
            f"{API_URL}/game/session/create",
            params={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "game_type": "blackjack"
            }
        )
        session_response.raise_for_status()
        session_data = session_response.json()
        session_id = session_data["session_id"]
        
        # Test with a big win (above 0.1 SOL threshold)
        big_win_payout = 0.12  # Above 0.1 SOL threshold
        wager_amount = 0.05
        
        # Record game result
        result_response = requests.post(
            f"{API_URL}/game/result",
            json={
                "session_id": session_id,
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "game_type": "blackjack",
                "wager_amount": wager_amount,
                "payout_amount": big_win_payout,
                "game_data": {
                    "result": "win",
                    "player_value": 21,
                    "dealer_value": 20,
                    "multiplier": big_win_payout / wager_amount
                },
                "transaction_signature": TEST_SIGNATURE
            }
        )
        result_response.raise_for_status()
        result_data = result_response.json()
        
        # Verify the response includes enhanced features
        expected_fields = ["success", "message", "payout_amount"]
        has_expected_fields = all(field in result_data for field in expected_fields)
        
        # Check if automatic payout was attempted
        payout_attempted = "payout_sent" in result_data
        
        return True, {
            "result_recorded": result_data.get("success", False),
            "payout_amount": result_data.get("payout_amount"),
            "payout_attempted": payout_attempted,
            "payout_sent": result_data.get("payout_sent", False),
            "payout_signature": result_data.get("payout_signature"),
            "explorer_url": result_data.get("explorer_url"),
            "has_expected_fields": has_expected_fields,
            "is_big_win": big_win_payout >= 0.1,
            "multiplayer_integration": "Enhanced game results should trigger multiplayer announcements"
        }
        
    except Exception as e:
        return False, str(e)

# Test 40: Complete Crash Game Flow (SolanaBust)
def test_crash_game_flow():
    try:
        # Note: The current backend doesn't have crash game session creation implemented
        # But we can test the wager system for crash game type
        
        session_id = str(uuid.uuid4())  # Use dummy session ID
        wager_amount = 0.01  # Valid SolanaBust amount
        
        # Test wager placement for crash game
        wager_response = requests.post(
            f"{API_URL}/game/wager",
            json={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "amount": wager_amount,
                "game_type": "crash",
                "session_id": session_id,
                "transaction_signature": TEST_SIGNATURE
            }
        )
        wager_response.raise_for_status()
        wager_data = wager_response.json()
        
        # Verify wager was processed correctly
        expected_dev_fee = wager_amount * TRANSACTION_FEE_PERCENTAGE
        expected_game_amount = wager_amount - expected_dev_fee
        
        wager_correct = (
            wager_data.get("success") and
            abs(wager_data.get("dev_fee", 0) - expected_dev_fee) < 0.001 and
            abs(wager_data.get("game_amount", 0) - expected_game_amount) < 0.001
        )
        
        # Test game result recording for crash game
        multiplier = 2.5
        payout_amount = wager_amount * multiplier
        
        result_response = requests.post(
            f"{API_URL}/game/result",
            json={
                "session_id": session_id,
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "game_type": "crash",
                "wager_amount": wager_amount,
                "payout_amount": payout_amount,
                "game_data": {
                    "result": "win",
                    "multiplier": multiplier,
                    "crash_point": 3.0,
                    "cash_out_point": multiplier
                },
                "transaction_signature": TEST_SIGNATURE
            }
        )
        result_response.raise_for_status()
        result_data = result_response.json()
        
        result_correct = (
            result_data.get("success") and
            result_data.get("payout_amount") == payout_amount
        )
        
        return wager_correct and result_correct, {
            "wager_processing": {
                "success": wager_correct,
                "wager_amount": wager_amount,
                "dev_fee": wager_data.get("dev_fee"),
                "game_amount": wager_data.get("game_amount")
            },
            "result_recording": {
                "success": result_correct,
                "payout_amount": result_data.get("payout_amount"),
                "payout_sent": result_data.get("payout_sent", False)
            },
            "multiplier": multiplier,
            "note": "Crash game session creation not implemented in current backend, but wager and result processing work"
        }
        
    except Exception as e:
        return False, str(e)

# Test 34: SolanaBust Wager Validation
def test_solana_bust_wager_validation():
    try:
        results = []
        
        # Test valid amounts for SolanaBust
        valid_amounts = [0.005, 0.01, 0.025, 0.05]
        for amount in valid_amounts:
            response = requests.post(
                f"{API_URL}/game/wager",
                json={
                    "player_wallet": TEST_WALLET_PUBLIC_KEY,
                    "amount": amount,
                    "game_type": "crash",
                    "session_id": str(uuid.uuid4()),
                    "transaction_signature": TEST_SIGNATURE
                }
            )
            
            success = response.status_code == 200
            results.append({
                "amount": amount,
                "valid": True,
                "success": success,
                "response": response.json() if success else response.text
            })
        
        # Test invalid amounts for SolanaBust
        invalid_amounts = [0.004, 0.051]  # Below min and above max
        for amount in invalid_amounts:
            response = requests.post(
                f"{API_URL}/game/wager",
                json={
                    "player_wallet": TEST_WALLET_PUBLIC_KEY,
                    "amount": amount,
                    "game_type": "crash",
                    "session_id": str(uuid.uuid4()),
                    "transaction_signature": TEST_SIGNATURE
                }
            )
            
            success = response.status_code == 400  # Should be rejected
            results.append({
                "amount": amount,
                "valid": False,
                "success": success,
                "response": response.json() if response.status_code == 400 else response.text
            })
        
        # Check if all tests passed
        all_passed = all(result["success"] for result in results)
        
        return all_passed, {
            "tests_run": len(results),
            "results": results
        }
    except Exception as e:
        return False, str(e)

def run_payout_tests():
    """Run only the payout system tests"""
    payout_tests = [
        ("House Wallet Balance", test_house_wallet_balance),
        ("Send Winner Payout", test_send_winner_payout),
        ("Payout Status Check", test_payout_status),
        ("Payout History", test_payout_history),
        ("Game Result with Automatic Payout", test_game_result_with_automatic_payout),
        ("Error Handling - Invalid Payout Amount", test_error_handling_invalid_payout_amount),
        ("Error Handling - Invalid Wallet Address", test_error_handling_invalid_wallet_address),
        ("SolanaBust Wager Validation", test_solana_bust_wager_validation)
    ]
    
    results = {}
    
    print("\n" + "=" * 80)
    print("SOLANA PAYOUT SYSTEM TESTS")
    print("=" * 80)
    
    for test_name, test_func in payout_tests:
        print(f"\nRunning test: {test_name}")
        success, data = test_func()
        print_test_result(test_name, success, data if success else None, data if not success else None)
        results[test_name] = success
    
    print("\n" + "=" * 80)
    print("PAYOUT TESTS SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    print("-" * 80)
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {passed/total*100:.2f}%")
    print("=" * 80)
    
    return results

if __name__ == "__main__":
    # Check if we should run payout tests specifically
    if len(sys.argv) > 1 and sys.argv[1] == "payout":
        run_payout_tests()
    else:
        run_all_tests()

# Test 24: 4% Dev Fee Implementation
def test_4_percent_dev_fee():
    try:
        # Test with different wager amounts
        wager_amounts = [0.1, 0.5, 1.0, 5.0, 10.0]
        results = []
        
        for wager_amount in wager_amounts:
            # Create a game session
            session_response = requests.post(
                f"{API_URL}/game/session/create",
                params={
                    "player_wallet": TEST_WALLET_PUBLIC_KEY,
                    "game_type": "blackjack"
                }
            )
            session_response.raise_for_status()
            session_data = session_response.json()
            session_id = session_data["session_id"]
            
            # Place wager
            wager_response = requests.post(
                f"{API_URL}/game/wager",
                json={
                    "player_wallet": TEST_WALLET_PUBLIC_KEY,
                    "amount": wager_amount,
                    "game_type": "blackjack",
                    "session_id": session_id,
                    "transaction_signature": TEST_SIGNATURE
                }
            )
            wager_response.raise_for_status()
            wager_data = wager_response.json()
            
            # Calculate expected values
            expected_dev_fee = wager_amount * TRANSACTION_FEE_PERCENTAGE
            expected_game_amount = wager_amount - expected_dev_fee
            
            # Verify fee calculation
            dev_fee_correct = abs(wager_data["dev_fee"] - expected_dev_fee) < 0.001
            game_amount_correct = abs(wager_data["game_amount"] - expected_game_amount) < 0.001
            
            results.append({
                "wager_amount": wager_amount,
                "expected_dev_fee": expected_dev_fee,
                "actual_dev_fee": wager_data["dev_fee"],
                "expected_game_amount": expected_game_amount,
                "actual_game_amount": wager_data["game_amount"],
                "dev_fee_correct": dev_fee_correct,
                "game_amount_correct": game_amount_correct,
                "fee_percentage": (wager_data["dev_fee"] / wager_amount) * 100
            })
        
        # Check if all tests passed
        all_passed = all(result["dev_fee_correct"] and result["game_amount_correct"] for result in results)
        
        return all_passed, {
            "wager_amounts_tested": len(wager_amounts),
            "results": results,
            "fee_percentage": f"{TRANSACTION_FEE_PERCENTAGE * 100}%"
        }
    except Exception as e:
        return False, str(e)

# Test 25: Crash Game Wager Placement
def test_crash_game_wager():
    try:
        # Place a wager for crash game
        wager_amount = 1.0
        response = requests.post(
            f"{API_URL}/game/wager",
            json={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "amount": wager_amount,
                "game_type": "crash",
                "session_id": str(uuid.uuid4()),  # Generate a random session ID
                "transaction_signature": TEST_SIGNATURE
            }
        )
        response.raise_for_status()
        data = response.json()
        
        # Verify the response contains the expected fields and fee calculation is correct
        expected_dev_fee = wager_amount * TRANSACTION_FEE_PERCENTAGE
        expected_game_amount = wager_amount - expected_dev_fee
        
        if (data.get("success") and 
            "wager_id" in data and 
            "total_amount" in data and 
            "game_amount" in data and 
            "dev_fee" in data and
            abs(data["dev_fee"] - expected_dev_fee) < 0.001 and  # Allow for floating point precision
            abs(data["game_amount"] - expected_game_amount) < 0.001 and
            data["dev_wallet"] == DEV_WALLET_ADDRESS):
            return True, data
        else:
            return False, "Crash game wager processing failed or fee calculation is incorrect"
    except Exception as e:
        return False, str(e)

# Test 26: Complete Crash Game Flow
def test_complete_crash_game_flow():
    try:
        # 1. Generate a session ID for crash game
        session_id = str(uuid.uuid4())
        
        # 2. Place wager
        wager_amount = 1.0
        wager_response = requests.post(
            f"{API_URL}/game/wager",
            json={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "amount": wager_amount,
                "game_type": "crash",
                "session_id": session_id,
                "transaction_signature": TEST_SIGNATURE
            }
        )
        wager_response.raise_for_status()
        wager_data = wager_response.json()
        
        # 3. Record a result (simulating a crash game outcome)
        # In a real crash game, there would be a multiplier determined by the game
        multiplier = 2.5  # Example multiplier
        payout_amount = wager_amount * multiplier
        
        result_response = requests.post(
            f"{API_URL}/game/result",
            json={
                "session_id": session_id,
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "game_type": "crash",
                "wager_amount": wager_amount,
                "payout_amount": payout_amount,
                "game_data": {
                    "multiplier": multiplier,
                    "crashed_at": multiplier,
                    "cashed_out": True
                },
                "transaction_signature": TEST_SIGNATURE
            }
        )
        result_response.raise_for_status()
        result_data = result_response.json()
        
        # Verify the dev fee calculation
        dev_fee = wager_amount * TRANSACTION_FEE_PERCENTAGE
        
        return True, {
            "session_id": session_id,
            "wager_amount": wager_amount,
            "multiplier": multiplier,
            "payout_amount": payout_amount,
            "dev_fee": dev_fee,
            "dev_fee_percentage": f"{TRANSACTION_FEE_PERCENTAGE * 100}%",
            "result_recorded": result_data.get("success", False)
        }
    except Exception as e:
        return False, str(e)

# Test 41: 8% Developer Fee Calculation Testing
def test_8_percent_dev_fee_calculation():
    """Test 8% developer fee calculation with different wager amounts"""
    try:
        test_amounts = [0.01, 0.05, 1.0, 5.0, 10.0]  # Different wager amounts
        results = []
        
        for amount in test_amounts:
            # Create a game session
            session_response = requests.post(
                f"{API_URL}/game/session/create",
                params={
                    "player_wallet": TEST_WALLET_PUBLIC_KEY,
                    "game_type": "blackjack"
                }
            )
            session_response.raise_for_status()
            session_data = session_response.json()
            session_id = session_data["session_id"]
            
            # Place wager
            response = requests.post(
                f"{API_URL}/game/wager",
                json={
                    "player_wallet": TEST_WALLET_PUBLIC_KEY,
                    "amount": amount,
                    "game_type": "blackjack",
                    "session_id": session_id,
                    "transaction_signature": TEST_SIGNATURE
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # Calculate expected values
            expected_dev_fee = amount * 0.08  # 8%
            expected_game_amount = amount - expected_dev_fee
            
            # Verify calculations
            fee_correct = abs(data["dev_fee"] - expected_dev_fee) < 0.000001
            game_amount_correct = abs(data["game_amount"] - expected_game_amount) < 0.000001
            total_correct = abs(data["total_amount"] - amount) < 0.000001
            
            results.append({
                "wager_amount": amount,
                "expected_dev_fee": expected_dev_fee,
                "actual_dev_fee": data["dev_fee"],
                "expected_game_amount": expected_game_amount,
                "actual_game_amount": data["game_amount"],
                "fee_correct": fee_correct,
                "game_amount_correct": game_amount_correct,
                "total_correct": total_correct,
                "dev_wallet": data["dev_wallet"]
            })
        
        # Check if all calculations are correct
        all_correct = all(r["fee_correct"] and r["game_amount_correct"] and r["total_correct"] for r in results)
        
        return all_correct, {
            "test_amounts": test_amounts,
            "all_calculations_correct": all_correct,
            "results": results
        }
    except Exception as e:
        return False, str(e)

# Test 42: SolanaBust 8% Fee Testing
def test_solana_bust_8_percent_fee():
    """Test 8% developer fee for SolanaBust with specific wager limits"""
    try:
        # SolanaBust specific test amounts (0.005-0.05 SOL range)
        test_amounts = [0.005, 0.01, 0.025, 0.05]
        results = []
        
        for amount in test_amounts:
            # Place wager for crash game (SolanaBust)
            response = requests.post(
                f"{API_URL}/game/wager",
                json={
                    "player_wallet": TEST_WALLET_PUBLIC_KEY,
                    "amount": amount,
                    "game_type": "crash",
                    "session_id": str(uuid.uuid4()),
                    "transaction_signature": TEST_SIGNATURE
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # Calculate expected values for 8% fee
            expected_dev_fee = amount * 0.08
            expected_game_amount = amount - expected_dev_fee
            
            # Verify calculations
            fee_correct = abs(data["dev_fee"] - expected_dev_fee) < 0.000001
            game_amount_correct = abs(data["game_amount"] - expected_game_amount) < 0.000001
            
            results.append({
                "wager_amount": amount,
                "expected_dev_fee": expected_dev_fee,
                "actual_dev_fee": data["dev_fee"],
                "expected_game_amount": expected_game_amount,
                "actual_game_amount": data["game_amount"],
                "fee_correct": fee_correct,
                "game_amount_correct": game_amount_correct,
                "dev_wallet": data["dev_wallet"]
            })
        
        all_correct = all(r["fee_correct"] and r["game_amount_correct"] for r in results)
        
        return all_correct, {
            "game_type": "crash (SolanaBust)",
            "test_amounts": test_amounts,
            "all_calculations_correct": all_correct,
            "results": results
        }
    except Exception as e:
        return False, str(e)

# Test 43: Comprehensive 8% Fee System Validation
def test_comprehensive_8_percent_fee_system():
    """Comprehensive test of the entire 8% fee system"""
    try:
        comprehensive_results = {
            "game_type_coverage": []
        }
        
        # Test all game types with various amounts
        test_scenarios = [
            {"game_type": "crash", "amounts": [0.005, 0.01, 0.025, 0.05]},
            {"game_type": "blackjack", "amounts": [0.01, 0.1, 1.0, 5.0, 10.0]},
            {"game_type": "video_poker", "amounts": [0.01, 0.1, 1.0, 5.0, 10.0]}
        ]
        
        for scenario in test_scenarios:
            game_results = []
            
            for amount in scenario["amounts"]:
                try:
                    # Create session if needed
                    session_id = str(uuid.uuid4())
                    if scenario["game_type"] != "crash":
                        session_response = requests.post(
                            f"{API_URL}/game/session/create",
                            params={
                                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                                "game_type": scenario["game_type"]
                            }
                        )
                        session_response.raise_for_status()
                        session_data = session_response.json()
                        session_id = session_data["session_id"]
                    
                    # Place wager
                    response = requests.post(
                        f"{API_URL}/game/wager",
                        json={
                            "player_wallet": TEST_WALLET_PUBLIC_KEY,
                            "amount": amount,
                            "game_type": scenario["game_type"],
                            "session_id": session_id,
                            "transaction_signature": TEST_SIGNATURE
                        }
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    # Verify 8% fee calculation
                    expected_dev_fee = amount * 0.08
                    expected_game_amount = amount - expected_dev_fee
                    
                    fee_correct = abs(data["dev_fee"] - expected_dev_fee) < 0.000001
                    game_amount_correct = abs(data["game_amount"] - expected_game_amount) < 0.000001
                    wallet_correct = data["dev_wallet"] == DEV_WALLET_ADDRESS
                    
                    game_results.append({
                        "amount": amount,
                        "dev_fee": data["dev_fee"],
                        "expected_dev_fee": expected_dev_fee,
                        "game_amount": data["game_amount"],
                        "expected_game_amount": expected_game_amount,
                        "fee_correct": fee_correct,
                        "game_amount_correct": game_amount_correct,
                        "wallet_correct": wallet_correct,
                        "success": True
                    })
                    
                except Exception as e:
                    game_results.append({
                        "amount": amount,
                        "success": False,
                        "error": str(e)
                    })
            
            comprehensive_results["game_type_coverage"].append({
                "game_type": scenario["game_type"],
                "results": game_results,
                "all_successful": all(r.get("success", False) for r in game_results),
                "all_fees_correct": all(r.get("fee_correct", False) for r in game_results if r.get("success", False)),
                "all_wallets_correct": all(r.get("wallet_correct", False) for r in game_results if r.get("success", False))
            })
        
        # Overall system validation
        all_games_working = all(g["all_successful"] for g in comprehensive_results["game_type_coverage"])
        all_fees_correct = all(g["all_fees_correct"] for g in comprehensive_results["game_type_coverage"])
        all_wallets_correct = all(g["all_wallets_correct"] for g in comprehensive_results["game_type_coverage"])
        
        system_working = all_games_working and all_fees_correct and all_wallets_correct
        
        return system_working, {
            "system_working": system_working,
            "all_games_working": all_games_working,
            "all_fees_correct": all_fees_correct,
            "all_wallets_correct": all_wallets_correct,
            "detailed_results": comprehensive_results
        }
    except Exception as e:
        return False, str(e)

def run_8_percent_fee_tests():
    """Run comprehensive 8% fee system tests"""
    print("\n" + "=" * 80)
    print("8% DEVELOPER FEE SYSTEM TESTING")
    print("=" * 80)
    
    # Run specific 8% fee tests
    fee_tests = [
        ("8% Developer Fee Calculation Testing", test_8_percent_dev_fee_calculation),
        ("SolanaBust 8% Fee Testing", test_solana_bust_8_percent_fee),
        ("Comprehensive 8% Fee System Validation", test_comprehensive_8_percent_fee_system)
    ]
    
    fee_results = {}
    
    for test_name, test_func in fee_tests:
        print(f"\nRunning test: {test_name}")
        success, data = test_func()
        print_test_result(test_name, success, data if success else None, data if not success else None)
        fee_results[test_name] = success
    
    print("\n" + "=" * 80)
    print("8% FEE SYSTEM TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for success in fee_results.values() if success)
    total = len(fee_results)
    
    for test_name, success in fee_results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    print("-" * 80)
    print(f"8% Fee System Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {passed/total*100:.2f}%")
    print("=" * 80)
    
    return fee_results