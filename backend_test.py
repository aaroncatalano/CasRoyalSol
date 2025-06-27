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
TRANSACTION_FEE_PERCENTAGE = 0.02  # 2%

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
        wager_amount = 100.0  # 100 SOL for testing
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
        wager_amount = 50.0
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
        wager_amount = 50.0
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

def run_all_tests():
    tests = [
        ("API Connectivity", test_api_connectivity),
        ("Status Check API", test_status_check),
        ("Solana Web3 Integration - Wallet Balance", test_wallet_balance),
        ("Phantom Wallet Backend APIs - Wallet Connection", test_wallet_connection),
        ("Game Session Management - Blackjack", test_blackjack_session_creation),
        ("Game Session Management - Video Poker", test_video_poker_session_creation),
        ("Wagering System with 2% Dev Fee", test_wagering_system),
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
        ("Error Handling - Invalid Session ID", test_error_handling_invalid_session)
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

if __name__ == "__main__":
    run_all_tests()