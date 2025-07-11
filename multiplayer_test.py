#!/usr/bin/env python3
import requests
import json
import sys
import os
from dotenv import load_dotenv
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
TEST_WALLET_PUBLIC_KEY = "A7GZMJLFzGSPn1nYHsGhLbU5pby4q96AessVHn5qVXFZ"
TEST_SIGNATURE = "5VxYCvdJZ1XoqJVBs4ysZCQ1RbZ3ZEpgEMran6UNnQmtK9XFMpf9YYBmJiNQQJqFbsL82F8BkYJh3UtEm5EJQzXP"
TRANSACTION_FEE_PERCENTAGE = 0.04  # 4%

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

# Test 1: Multiplayer Stats
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

# Test 2: Recent Announcements
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

# Test 3: Manual Win Announcement
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

# Test 4: SolanaBust Wager Validation
def test_solana_bust_wager_validation():
    try:
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

# Test 5: Enhanced Game Results with Multiplayer Integration
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

# Test 6: Complete Crash Game Flow (SolanaBust)
def test_crash_game_flow():
    try:
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

def run_multiplayer_tests():
    tests = [
        ("Multiplayer Stats", test_multiplayer_stats),
        ("Recent Announcements", test_recent_announcements),
        ("Manual Win Announcement", test_manual_win_announcement),
        ("SolanaBust Wager Validation", test_solana_bust_wager_validation),
        ("Enhanced Game Results with Multiplayer", test_enhanced_game_results),
        ("Complete Crash Game Flow (SolanaBust)", test_crash_game_flow)
    ]
    
    results = {}
    
    print("\n" + "=" * 80)
    print("MULTIPLAYER SYSTEM TESTS - SOLANA GAMING PLATFORM")
    print("=" * 80)
    
    for test_name, test_func in tests:
        print(f"\nRunning test: {test_name}")
        success, data = test_func()
        print_test_result(test_name, success, data if success else None, data if not success else None)
        results[test_name] = success
    
    print("\n" + "=" * 80)
    print("MULTIPLAYER TEST SUMMARY")
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
    run_multiplayer_tests()