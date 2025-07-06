#!/usr/bin/env python3
import requests
import json
import time
import sys
import os
from dotenv import load_dotenv
import random
import string
import uuid
import concurrent.futures

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
TRANSACTION_FEE_PERCENTAGE = 0.04  # 4%

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

# Test 1: Verify Crash Game Type is Valid
def test_crash_game_type_valid():
    try:
        # Place a wager for crash game
        wager_amount = 1.0
        response = requests.post(
            f"{API_URL}/game/wager",
            json={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "amount": wager_amount,
                "game_type": "crash",
                "session_id": str(uuid.uuid4()),
                "transaction_signature": TEST_SIGNATURE
            }
        )
        response.raise_for_status()
        data = response.json()
        
        # Verify the response contains the expected fields
        if (data.get("success") and 
            "wager_id" in data and 
            "total_amount" in data and 
            "game_amount" in data and 
            "dev_fee" in data):
            return True, data
        else:
            return False, "Crash game type not accepted"
    except Exception as e:
        return False, str(e)

# Test 2: Verify 4% Dev Fee for Crash Game
def test_crash_game_dev_fee():
    try:
        # Test with different wager amounts
        wager_amounts = [0.1, 0.5, 1.0, 5.0, 10.0]
        results = []
        
        for wager_amount in wager_amounts:
            # Place wager for crash game
            wager_response = requests.post(
                f"{API_URL}/game/wager",
                json={
                    "player_wallet": TEST_WALLET_PUBLIC_KEY,
                    "amount": wager_amount,
                    "game_type": "crash",
                    "session_id": str(uuid.uuid4()),
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

# Test 3: Complete Crash Game Flow with Different Multipliers
def test_crash_game_flow_with_multipliers():
    try:
        # Test with different multipliers
        multipliers = [1.2, 2.0, 3.5, 5.0, 10.0]
        results = []
        
        for multiplier in multipliers:
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
            
            # 3. Record a result (simulating a crash game outcome)
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
            
            results.append({
                "multiplier": multiplier,
                "wager_amount": wager_amount,
                "payout_amount": payout_amount,
                "result_recorded": result_data.get("success", False)
            })
        
        # Check if all results were recorded successfully
        all_passed = all(result["result_recorded"] for result in results)
        
        return all_passed, {
            "multipliers_tested": len(multipliers),
            "results": results
        }
    except Exception as e:
        return False, str(e)

# Test 4: Crash Game with Player Loss (Crash Before Cash Out)
def test_crash_game_player_loss():
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
        
        # 3. Record a result (simulating a crash game where player loses)
        # Payout is 0 when player doesn't cash out before crash
        payout_amount = 0.0
        
        result_response = requests.post(
            f"{API_URL}/game/result",
            json={
                "session_id": session_id,
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "game_type": "crash",
                "wager_amount": wager_amount,
                "payout_amount": payout_amount,
                "game_data": {
                    "multiplier": 1.5,  # The game crashed at 1.5x
                    "crashed_at": 1.5,
                    "cashed_out": False  # Player didn't cash out in time
                },
                "transaction_signature": TEST_SIGNATURE
            }
        )
        result_response.raise_for_status()
        result_data = result_response.json()
        
        return result_data.get("success", False), {
            "wager_amount": wager_amount,
            "payout_amount": payout_amount,
            "game_crashed_at": 1.5,
            "player_cashed_out": False,
            "result_recorded": result_data.get("success", False)
        }
    except Exception as e:
        return False, str(e)

# Test 5: Verify Existing Games Still Work (Blackjack and Video Poker)
def test_existing_games_still_work():
    try:
        results = {}
        
        # Test Blackjack
        # 1. Create session
        blackjack_session_response = requests.post(
            f"{API_URL}/game/session/create",
            params={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "game_type": "blackjack"
            }
        )
        blackjack_session_response.raise_for_status()
        blackjack_session_data = blackjack_session_response.json()
        blackjack_session_id = blackjack_session_data["session_id"]
        
        # 2. Place wager
        wager_amount = 1.0
        blackjack_wager_response = requests.post(
            f"{API_URL}/game/wager",
            json={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "amount": wager_amount,
                "game_type": "blackjack",
                "session_id": blackjack_session_id,
                "transaction_signature": TEST_SIGNATURE
            }
        )
        blackjack_wager_response.raise_for_status()
        
        # 3. Finish game
        blackjack_finish_response = requests.post(
            f"{API_URL}/game/blackjack/finish",
            params={"session_id": blackjack_session_id}
        )
        blackjack_finish_response.raise_for_status()
        blackjack_finish_data = blackjack_finish_response.json()
        
        # Record blackjack result
        blackjack_result = blackjack_finish_data["results"][0]
        blackjack_payout_multiplier = blackjack_result["payout_multiplier"]
        blackjack_payout_amount = wager_amount * blackjack_payout_multiplier
        
        blackjack_result_response = requests.post(
            f"{API_URL}/game/result",
            json={
                "session_id": blackjack_session_id,
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "game_type": "blackjack",
                "wager_amount": wager_amount,
                "payout_amount": blackjack_payout_amount,
                "game_data": blackjack_finish_data["game_state"],
                "transaction_signature": TEST_SIGNATURE
            }
        )
        blackjack_result_response.raise_for_status()
        
        results["blackjack"] = {
            "session_created": blackjack_session_data.get("success", False),
            "wager_placed": blackjack_wager_response.json().get("success", False),
            "game_finished": blackjack_finish_data.get("success", False),
            "result_recorded": blackjack_result_response.json().get("success", False)
        }
        
        # Test Video Poker
        # 1. Create session
        poker_session_response = requests.post(
            f"{API_URL}/game/session/create",
            params={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "game_type": "video_poker"
            }
        )
        poker_session_response.raise_for_status()
        poker_session_data = poker_session_response.json()
        poker_session_id = poker_session_data["session_id"]
        
        # 2. Place wager
        poker_wager_response = requests.post(
            f"{API_URL}/game/wager",
            json={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "amount": wager_amount,
                "game_type": "video_poker",
                "session_id": poker_session_id,
                "transaction_signature": TEST_SIGNATURE
            }
        )
        poker_wager_response.raise_for_status()
        
        # 3. Draw cards
        poker_draw_response = requests.post(
            f"{API_URL}/game/video_poker/draw",
            params={"session_id": poker_session_id}
        )
        poker_draw_response.raise_for_status()
        poker_draw_data = poker_draw_response.json()
        
        # Record poker result
        poker_payout_multiplier = poker_draw_data["payout_multiplier"]
        poker_payout_amount = wager_amount * poker_payout_multiplier
        
        poker_result_response = requests.post(
            f"{API_URL}/game/result",
            json={
                "session_id": poker_session_id,
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "game_type": "video_poker",
                "wager_amount": wager_amount,
                "payout_amount": poker_payout_amount,
                "game_data": poker_draw_data["game_state"],
                "transaction_signature": TEST_SIGNATURE
            }
        )
        poker_result_response.raise_for_status()
        
        results["video_poker"] = {
            "session_created": poker_session_data.get("success", False),
            "wager_placed": poker_wager_response.json().get("success", False),
            "cards_drawn": poker_draw_data.get("success", False),
            "result_recorded": poker_result_response.json().get("success", False)
        }
        
        # Check if all operations were successful
        blackjack_success = all(results["blackjack"].values())
        poker_success = all(results["video_poker"].values())
        
        return blackjack_success and poker_success, results
    except Exception as e:
        return False, str(e)

# Test 6: Concurrent Game Sessions
def test_concurrent_game_sessions():
    try:
        # Number of concurrent sessions to test
        num_sessions = 5
        
        # Function to run a complete crash game flow
        def run_crash_game():
            session_id = str(uuid.uuid4())
            wager_amount = 1.0
            multiplier = random.uniform(1.1, 5.0)
            
            # Place wager
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
            
            # Record result
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
            
            return {
                "session_id": session_id,
                "multiplier": multiplier,
                "wager_success": wager_response.json().get("success", False),
                "result_success": result_response.json().get("success", False)
            }
        
        # Run concurrent game sessions
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_sessions) as executor:
            futures = [executor.submit(run_crash_game) for _ in range(num_sessions)]
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())
        
        # Check if all sessions were successful
        all_successful = all(
            result["wager_success"] and result["result_success"] 
            for result in results
        )
        
        return all_successful, {
            "num_concurrent_sessions": num_sessions,
            "all_successful": all_successful,
            "results": results
        }
    except Exception as e:
        return False, str(e)

# Test 7: Verify 4% Dev Fee Across All Game Types
def test_dev_fee_across_game_types():
    try:
        game_types = ["blackjack", "video_poker", "crash"]
        results = []
        
        for game_type in game_types:
            # For blackjack and video poker, we need to create a session first
            session_id = None
            if game_type in ["blackjack", "video_poker"]:
                session_response = requests.post(
                    f"{API_URL}/game/session/create",
                    params={
                        "player_wallet": TEST_WALLET_PUBLIC_KEY,
                        "game_type": game_type
                    }
                )
                session_response.raise_for_status()
                session_id = session_response.json()["session_id"]
            else:
                # For crash, just generate a UUID
                session_id = str(uuid.uuid4())
            
            # Place wager
            wager_amount = 1.0
            wager_response = requests.post(
                f"{API_URL}/game/wager",
                json={
                    "player_wallet": TEST_WALLET_PUBLIC_KEY,
                    "amount": wager_amount,
                    "game_type": game_type,
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
                "game_type": game_type,
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
            "game_types_tested": game_types,
            "results": results,
            "fee_percentage": f"{TRANSACTION_FEE_PERCENTAGE * 100}%"
        }
    except Exception as e:
        return False, str(e)

# Test 8: Error Handling - Invalid Inputs
def test_error_handling():
    try:
        error_tests = []
        
        # Test 1: Invalid wager amount (too small)
        try:
            response = requests.post(
                f"{API_URL}/game/wager",
                json={
                    "player_wallet": TEST_WALLET_PUBLIC_KEY,
                    "amount": 0.001,  # Too small
                    "game_type": "crash",
                    "session_id": str(uuid.uuid4()),
                    "transaction_signature": TEST_SIGNATURE
                }
            )
            error_tests.append({
                "test": "Invalid wager amount (too small)",
                "status_code": response.status_code,
                "expected_status_code": 400,
                "passed": response.status_code == 400
            })
        except Exception as e:
            error_tests.append({
                "test": "Invalid wager amount (too small)",
                "error": str(e),
                "passed": False
            })
        
        # Test 2: Invalid wager amount (too large)
        try:
            response = requests.post(
                f"{API_URL}/game/wager",
                json={
                    "player_wallet": TEST_WALLET_PUBLIC_KEY,
                    "amount": 20.0,  # Too large
                    "game_type": "crash",
                    "session_id": str(uuid.uuid4()),
                    "transaction_signature": TEST_SIGNATURE
                }
            )
            error_tests.append({
                "test": "Invalid wager amount (too large)",
                "status_code": response.status_code,
                "expected_status_code": 400,
                "passed": response.status_code == 400
            })
        except Exception as e:
            error_tests.append({
                "test": "Invalid wager amount (too large)",
                "error": str(e),
                "passed": False
            })
        
        # Test 3: Invalid game type
        try:
            response = requests.post(
                f"{API_URL}/game/wager",
                json={
                    "player_wallet": TEST_WALLET_PUBLIC_KEY,
                    "amount": 1.0,
                    "game_type": "invalid_game",
                    "session_id": str(uuid.uuid4()),
                    "transaction_signature": TEST_SIGNATURE
                }
            )
            error_tests.append({
                "test": "Invalid game type",
                "status_code": response.status_code,
                "expected_status_code": 400,
                "passed": response.status_code == 400
            })
        except Exception as e:
            error_tests.append({
                "test": "Invalid game type",
                "error": str(e),
                "passed": False
            })
        
        # Check if all error tests passed
        all_passed = all(test["passed"] for test in error_tests)
        
        return all_passed, {
            "error_tests": error_tests,
            "all_passed": all_passed
        }
    except Exception as e:
        return False, str(e)

def run_all_tests():
    tests = [
        ("Verify Crash Game Type is Valid", test_crash_game_type_valid),
        ("Verify 4% Dev Fee for Crash Game", test_crash_game_dev_fee),
        ("Complete Crash Game Flow with Different Multipliers", test_crash_game_flow_with_multipliers),
        ("Crash Game with Player Loss", test_crash_game_player_loss),
        ("Verify Existing Games Still Work", test_existing_games_still_work),
        ("Concurrent Game Sessions", test_concurrent_game_sessions),
        ("Verify 4% Dev Fee Across All Game Types", test_dev_fee_across_game_types),
        ("Error Handling - Invalid Inputs", test_error_handling)
    ]
    
    results = {}
    
    print("\n" + "=" * 80)
    print("SOLANA BUST CRASH GAME BACKEND API TESTS")
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