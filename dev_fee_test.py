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

# Test 1: 2% Dev Fee with 0.1 SOL Wager
def test_dev_fee_small_wager():
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
        
        # Place a wager of 0.1 SOL
        wager_amount = 0.1  # 0.1 SOL
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
        expected_dev_fee = wager_amount * TRANSACTION_FEE_PERCENTAGE  # Should be 0.002 SOL
        expected_game_amount = wager_amount - expected_dev_fee  # Should be 0.098 SOL
        
        if (data.get("success") and 
            "wager_id" in data and 
            "total_amount" in data and 
            "game_amount" in data and 
            "dev_fee" in data and
            abs(data["dev_fee"] - expected_dev_fee) < 0.0001 and  # Allow for floating point precision
            abs(data["game_amount"] - expected_game_amount) < 0.0001 and
            data["dev_wallet"] == DEV_WALLET_ADDRESS):
            return True, {
                "wager_amount": wager_amount,
                "dev_fee": data["dev_fee"],
                "expected_dev_fee": expected_dev_fee,
                "game_amount": data["game_amount"],
                "expected_game_amount": expected_game_amount,
                "dev_wallet": data["dev_wallet"]
            }
        else:
            return False, "Wager processing failed or fee calculation is incorrect"
    except Exception as e:
        return False, str(e)

# Test 2: 2% Dev Fee with 0.5 SOL Wager
def test_dev_fee_medium_wager():
    try:
        # Create a game session
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
        
        # Place a wager of 0.5 SOL
        wager_amount = 0.5  # 0.5 SOL
        response = requests.post(
            f"{API_URL}/game/wager",
            json={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "amount": wager_amount,
                "game_type": "video_poker",
                "session_id": session_id,
                "transaction_signature": TEST_SIGNATURE
            }
        )
        response.raise_for_status()
        data = response.json()
        
        # Verify the response contains the expected fields and fee calculation is correct
        expected_dev_fee = wager_amount * TRANSACTION_FEE_PERCENTAGE  # Should be 0.01 SOL
        expected_game_amount = wager_amount - expected_dev_fee  # Should be 0.49 SOL
        
        if (data.get("success") and 
            "wager_id" in data and 
            "total_amount" in data and 
            "game_amount" in data and 
            "dev_fee" in data and
            abs(data["dev_fee"] - expected_dev_fee) < 0.0001 and  # Allow for floating point precision
            abs(data["game_amount"] - expected_game_amount) < 0.0001 and
            data["dev_wallet"] == DEV_WALLET_ADDRESS):
            return True, {
                "wager_amount": wager_amount,
                "dev_fee": data["dev_fee"],
                "expected_dev_fee": expected_dev_fee,
                "game_amount": data["game_amount"],
                "expected_game_amount": expected_game_amount,
                "dev_wallet": data["dev_wallet"]
            }
        else:
            return False, "Wager processing failed or fee calculation is incorrect"
    except Exception as e:
        return False, str(e)

# Test 3: 2% Dev Fee with 1.0 SOL Wager
def test_dev_fee_large_wager():
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
        
        # Place a wager of 1.0 SOL
        wager_amount = 1.0  # 1.0 SOL
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
        expected_dev_fee = wager_amount * TRANSACTION_FEE_PERCENTAGE  # Should be 0.02 SOL
        expected_game_amount = wager_amount - expected_dev_fee  # Should be 0.98 SOL
        
        if (data.get("success") and 
            "wager_id" in data and 
            "total_amount" in data and 
            "game_amount" in data and 
            "dev_fee" in data and
            abs(data["dev_fee"] - expected_dev_fee) < 0.0001 and  # Allow for floating point precision
            abs(data["game_amount"] - expected_game_amount) < 0.0001 and
            data["dev_wallet"] == DEV_WALLET_ADDRESS):
            return True, {
                "wager_amount": wager_amount,
                "dev_fee": data["dev_fee"],
                "expected_dev_fee": expected_dev_fee,
                "game_amount": data["game_amount"],
                "expected_game_amount": expected_game_amount,
                "dev_wallet": data["dev_wallet"]
            }
        else:
            return False, "Wager processing failed or fee calculation is incorrect"
    except Exception as e:
        return False, str(e)

# Test 4: Complete Blackjack Game Flow with Dev Fee
def test_blackjack_complete_flow_with_dev_fee():
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
        wager_amount = 0.25  # 0.25 SOL
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
        
        # Calculate dev fee
        dev_fee = wager_data["dev_fee"]
        game_amount = wager_data["game_amount"]
        
        # 3. Finish game
        finish_response = requests.post(
            f"{API_URL}/game/blackjack/finish",
            params={
                "session_id": session_id
            }
        )
        finish_response.raise_for_status()
        finish_data = finish_response.json()
        
        # 4. Record result
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
        expected_dev_fee = wager_amount * TRANSACTION_FEE_PERCENTAGE
        
        if abs(dev_fee - expected_dev_fee) < 0.0001:
            return True, {
                "session_id": session_id,
                "wager_amount": wager_amount,
                "dev_fee": dev_fee,
                "expected_dev_fee": expected_dev_fee,
                "game_amount": game_amount,
                "game_result": result["result"],
                "payout_multiplier": payout_multiplier,
                "payout_amount": payout_amount,
                "result_recorded": result_data.get("success", False)
            }
        else:
            return False, "Dev fee calculation is incorrect"
    except Exception as e:
        return False, str(e)

# Test 5: Complete Video Poker Game Flow with Dev Fee
def test_video_poker_complete_flow_with_dev_fee():
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
        
        # 2. Place wager
        wager_amount = 0.75  # 0.75 SOL
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
        
        # Calculate dev fee
        dev_fee = wager_data["dev_fee"]
        game_amount = wager_data["game_amount"]
        
        # 3. Draw cards
        draw_response = requests.post(
            f"{API_URL}/game/video_poker/draw",
            params={
                "session_id": session_id
            }
        )
        draw_response.raise_for_status()
        draw_data = draw_response.json()
        
        # 4. Record result
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
        expected_dev_fee = wager_amount * TRANSACTION_FEE_PERCENTAGE
        
        if abs(dev_fee - expected_dev_fee) < 0.0001:
            return True, {
                "session_id": session_id,
                "wager_amount": wager_amount,
                "dev_fee": dev_fee,
                "expected_dev_fee": expected_dev_fee,
                "game_amount": game_amount,
                "hand_rank": hand_rank,
                "payout_multiplier": payout_multiplier,
                "payout_amount": payout_amount,
                "result_recorded": result_data.get("success", False)
            }
        else:
            return False, "Dev fee calculation is incorrect"
    except Exception as e:
        return False, str(e)

# Test 6: Win Scenario with Dev Fee
def test_win_scenario_with_dev_fee():
    try:
        # Run multiple games until we get a win
        max_attempts = 10
        for attempt in range(max_attempts):
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
            wager_amount = 0.5  # 0.5 SOL
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
            
            # Calculate dev fee
            dev_fee = wager_data["dev_fee"]
            
            # 3. Finish game
            finish_response = requests.post(
                f"{API_URL}/game/blackjack/finish",
                params={
                    "session_id": session_id
                }
            )
            finish_response.raise_for_status()
            finish_data = finish_response.json()
            
            # Check if we won
            result = finish_data["results"][0]
            if result["result"] in ["win", "blackjack"]:
                payout_multiplier = result["payout_multiplier"]
                payout_amount = wager_amount * payout_multiplier
                
                # 4. Record result
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
                
                # Verify the dev fee calculation
                expected_dev_fee = wager_amount * TRANSACTION_FEE_PERCENTAGE
                
                if abs(dev_fee - expected_dev_fee) < 0.0001:
                    return True, {
                        "session_id": session_id,
                        "wager_amount": wager_amount,
                        "dev_fee": dev_fee,
                        "expected_dev_fee": expected_dev_fee,
                        "game_result": result["result"],
                        "payout_multiplier": payout_multiplier,
                        "payout_amount": payout_amount
                    }
                else:
                    return False, "Dev fee calculation is incorrect"
        
        return False, f"Failed to get a win after {max_attempts} attempts"
    except Exception as e:
        return False, str(e)

# Test 7: Loss Scenario with Dev Fee
def test_loss_scenario_with_dev_fee():
    try:
        # Run multiple games until we get a loss
        max_attempts = 10
        for attempt in range(max_attempts):
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
            wager_amount = 0.5  # 0.5 SOL
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
            
            # Calculate dev fee
            dev_fee = wager_data["dev_fee"]
            
            # 3. Finish game
            finish_response = requests.post(
                f"{API_URL}/game/blackjack/finish",
                params={
                    "session_id": session_id
                }
            )
            finish_response.raise_for_status()
            finish_data = finish_response.json()
            
            # Check if we lost
            result = finish_data["results"][0]
            if result["result"] == "lose":
                payout_multiplier = result["payout_multiplier"]
                payout_amount = wager_amount * payout_multiplier  # Should be 0
                
                # 4. Record result
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
                
                # Verify the dev fee calculation
                expected_dev_fee = wager_amount * TRANSACTION_FEE_PERCENTAGE
                
                if abs(dev_fee - expected_dev_fee) < 0.0001:
                    return True, {
                        "session_id": session_id,
                        "wager_amount": wager_amount,
                        "dev_fee": dev_fee,
                        "expected_dev_fee": expected_dev_fee,
                        "game_result": result["result"],
                        "payout_multiplier": payout_multiplier,
                        "payout_amount": payout_amount
                    }
                else:
                    return False, "Dev fee calculation is incorrect"
        
        return False, f"Failed to get a loss after {max_attempts} attempts"
    except Exception as e:
        return False, str(e)

def run_all_tests():
    tests = [
        ("2% Dev Fee with 0.1 SOL Wager", test_dev_fee_small_wager),
        ("2% Dev Fee with 0.5 SOL Wager", test_dev_fee_medium_wager),
        ("2% Dev Fee with 1.0 SOL Wager", test_dev_fee_large_wager),
        ("Complete Blackjack Game Flow with Dev Fee", test_blackjack_complete_flow_with_dev_fee),
        ("Complete Video Poker Game Flow with Dev Fee", test_video_poker_complete_flow_with_dev_fee),
        ("Win Scenario with Dev Fee", test_win_scenario_with_dev_fee),
        ("Loss Scenario with Dev Fee", test_loss_scenario_with_dev_fee)
    ]
    
    results = {}
    
    print("\n" + "=" * 80)
    print("SOLANA GAMING PLATFORM 2% DEV FEE TESTS")
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