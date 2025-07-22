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
DEV_WALLET_ADDRESS = "A7GZMJLFzGSPn1nYHsGhLbU5pby4q96AessVHn5qVXFZ"
TRANSACTION_FEE_PERCENTAGE = 0.12  # 12% dev fee

# Additional test wallets for variety
TEST_WALLETS = [
    "A7GZMJLFzGSPn1nYHsGhLbU5pby4q96AessVHn5qVXFZ",
    "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
    "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
    "GDfnEsia2WLAW5t8yx2X5j2mkfA74i5kwGdDuZHt7XmG"
]

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

# Test: Video Poker Backend Endpoint Testing (Specific Request)
def test_video_poker_backend_endpoints():
    """Test Video Poker backend endpoints as specifically requested"""
    try:
        results = []
        
        # Test 1: POST /api/video_poker/new with valid player wallet and wager
        print("Testing POST /api/video_poker/new...")
        test_wallets = [
            "A7GZMJLFzGSPn1nYHsGhLbU5pby4q96AessVHn5qVXFZ",
            "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"
        ]
        
        wager_amounts = [0.01, 0.05, 0.1, 1.0]
        
        video_poker_new_tests = []
        for wallet in test_wallets:
            for wager in wager_amounts:
                try:
                    response = requests.post(
                        f"{API_URL}/video_poker/new",
                        json={
                            "player_wallet": wallet,
                            "wager": wager
                        }
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    # Verify proper game state creation with 5 cards dealt
                    success = (
                        data.get("success") == True and
                        "session_id" in data and
                        "game_state" in data and
                        "message" in data and
                        len(data["game_state"]["hand"]) == 5 and
                        data["game_state"]["initial_deal"] == True and
                        data["game_state"]["game_complete"] == False
                    )
                    
                    video_poker_new_tests.append({
                        "wallet": wallet,
                        "wager": wager,
                        "success": success,
                        "session_id": data.get("session_id"),
                        "cards_dealt": len(data["game_state"]["hand"]) if "game_state" in data else 0,
                        "initial_deal": data["game_state"].get("initial_deal") if "game_state" in data else False
                    })
                    
                except Exception as e:
                    video_poker_new_tests.append({
                        "wallet": wallet,
                        "wager": wager,
                        "success": False,
                        "error": str(e)
                    })
        
        results.append({
            "test": "POST /api/video_poker/new",
            "total_tests": len(video_poker_new_tests),
            "passed": sum(1 for t in video_poker_new_tests if t["success"]),
            "details": video_poker_new_tests
        })
        
        # Test 2: POST /api/game/wager for Video Poker with 12% dev fee
        print("Testing POST /api/game/wager for Video Poker...")
        wager_tests = []
        
        for wager_amount in [0.01, 0.1, 1.0]:
            try:
                # First create a video poker session
                session_response = requests.post(
                    f"{API_URL}/video_poker/new",
                    json={
                        "player_wallet": TEST_WALLET_PUBLIC_KEY,
                        "wager": wager_amount
                    }
                )
                session_response.raise_for_status()
                session_data = session_response.json()
                session_id = session_data["session_id"]
                
                # Now test wager recording
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
                
                # Verify 12% dev fee calculation
                expected_dev_fee = wager_amount * 0.12
                expected_game_amount = wager_amount - expected_dev_fee
                
                success = (
                    data.get("success") == True and
                    abs(data.get("dev_fee", 0) - expected_dev_fee) < 0.001 and
                    abs(data.get("game_amount", 0) - expected_game_amount) < 0.001 and
                    data.get("dev_wallet") == DEV_WALLET_ADDRESS
                )
                
                wager_tests.append({
                    "wager_amount": wager_amount,
                    "success": success,
                    "expected_dev_fee": expected_dev_fee,
                    "actual_dev_fee": data.get("dev_fee"),
                    "expected_game_amount": expected_game_amount,
                    "actual_game_amount": data.get("game_amount"),
                    "dev_wallet": data.get("dev_wallet")
                })
                
            except Exception as e:
                wager_tests.append({
                    "wager_amount": wager_amount,
                    "success": False,
                    "error": str(e)
                })
        
        results.append({
            "test": "POST /api/game/wager for Video Poker",
            "total_tests": len(wager_tests),
            "passed": sum(1 for t in wager_tests if t["success"]),
            "details": wager_tests
        })
        
        # Test 3: Video Poker Game Logic Verification
        print("Testing Video Poker Game Logic...")
        game_logic_tests = []
        
        for i in range(5):  # Test multiple games
            try:
                # Create new video poker game
                response = requests.post(
                    f"{API_URL}/video_poker/new",
                    json={
                        "player_wallet": TEST_WALLET_PUBLIC_KEY,
                        "wager": 0.1
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                # Verify game state structure
                game_state = data.get("game_state", {})
                success = (
                    len(game_state.get("hand", [])) == 5 and
                    game_state.get("initial_deal") == True and
                    game_state.get("game_complete") == False and
                    "hand_rank" in game_state and
                    all("card" in card_data and "held" in card_data for card_data in game_state.get("hand", []))
                )
                
                game_logic_tests.append({
                    "game_number": i + 1,
                    "success": success,
                    "session_id": data.get("session_id"),
                    "cards_count": len(game_state.get("hand", [])),
                    "initial_deal": game_state.get("initial_deal"),
                    "game_complete": game_state.get("game_complete"),
                    "hand_rank": game_state.get("hand_rank"),
                    "cards": [card.get("card") for card in game_state.get("hand", [])]
                })
                
            except Exception as e:
                game_logic_tests.append({
                    "game_number": i + 1,
                    "success": False,
                    "error": str(e)
                })
        
        results.append({
            "test": "Video Poker Game Logic",
            "total_tests": len(game_logic_tests),
            "passed": sum(1 for t in game_logic_tests if t["success"]),
            "details": game_logic_tests
        })
        
        # Test 4: Multiple Games Creation Test
        print("Testing multiple Video Poker games creation...")
        multiple_games_test = []
        session_ids = []
        
        for i in range(10):  # Create 10 games
            try:
                response = requests.post(
                    f"{API_URL}/video_poker/new",
                    json={
                        "player_wallet": TEST_WALLET_PUBLIC_KEY,
                        "wager": 0.05
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                session_id = data.get("session_id")
                success = (
                    data.get("success") == True and
                    session_id is not None and
                    session_id not in session_ids  # Ensure unique session IDs
                )
                
                if success:
                    session_ids.append(session_id)
                
                multiple_games_test.append({
                    "game_number": i + 1,
                    "success": success,
                    "session_id": session_id,
                    "unique_session": session_id not in session_ids[:-1] if session_id else False
                })
                
            except Exception as e:
                multiple_games_test.append({
                    "game_number": i + 1,
                    "success": False,
                    "error": str(e)
                })
        
        results.append({
            "test": "Multiple Games Creation",
            "total_tests": len(multiple_games_test),
            "passed": sum(1 for t in multiple_games_test if t["success"]),
            "unique_sessions": len(set(session_ids)),
            "details": multiple_games_test
        })
        
        # Calculate overall success rate
        total_tests = sum(r["total_tests"] for r in results)
        total_passed = sum(r["passed"] for r in results)
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        overall_success = success_rate >= 85  # Consider success if 85% or more tests pass
        
        return overall_success, {
            "overall_success_rate": f"{success_rate:.2f}%",
            "total_tests": total_tests,
            "total_passed": total_passed,
            "test_results": results
        }
        
    except Exception as e:
        return False, str(e)

# Main test execution
def main():
    print("🎮 VIDEO POKER BACKEND TESTING 🎮")
    print("=" * 80)
    print(f"Testing API at: {API_URL}")
    print("=" * 80)
    
    # Focus on Video Poker backend testing as requested
    tests = [
        ("Video Poker Backend Endpoints Testing", test_video_poker_backend_endpoints),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            success, result = test_func()
            print_test_result(test_name, success, result if success else None, result if not success else None)
            if success:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print_test_result(test_name, False, None, str(e))
            failed += 1
        
        # Add a small delay between tests to avoid overwhelming the server
        time.sleep(0.5)
    
    # Print summary
    print("=" * 80)
    print("🎯 VIDEO POKER BACKEND TEST SUMMARY")
    print("=" * 80)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")
    print(f"📈 Success Rate: {(passed / (passed + failed) * 100):.2f}%")
    print("=" * 80)

if __name__ == "__main__":
    main()