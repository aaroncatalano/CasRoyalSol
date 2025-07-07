#!/usr/bin/env python3
import requests
import json
import time
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

# Test 1: SolanaBust Wager Validation - Below Minimum
def test_solanabust_wager_below_minimum():
    try:
        # Place a wager below the minimum (0.005 SOL)
        wager_amount = 0.004
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
        
        # We expect a 400 Bad Request
        if response.status_code == 400 and "Minimum wager for SolanaBust is 0.005 SOL" in response.text:
            return True, {"status_code": response.status_code, "error": response.json()}
        else:
            return False, f"Expected 400 status code with minimum wager error, got {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)

# Test 2: SolanaBust Wager Validation - Above Maximum
def test_solanabust_wager_above_maximum():
    try:
        # Place a wager above the maximum (0.05 SOL)
        wager_amount = 0.06
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
        
        # We expect a 400 Bad Request
        if response.status_code == 400 and "Maximum wager for SolanaBust is 0.05 SOL" in response.text:
            return True, {"status_code": response.status_code, "error": response.json()}
        else:
            return False, f"Expected 400 status code with maximum wager error, got {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)

# Test 3: SolanaBust Wager Validation - Valid Minimum
def test_solanabust_wager_valid_minimum():
    try:
        # Place a wager at the minimum (0.005 SOL)
        wager_amount = 0.005
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
        
        # We expect a 200 OK
        if response.status_code == 200 and response.json().get("success"):
            return True, response.json()
        else:
            return False, f"Expected 200 status code with success, got {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)

# Test 4: SolanaBust Wager Validation - Valid Middle
def test_solanabust_wager_valid_middle():
    try:
        # Place a wager in the middle of the range (0.007 SOL)
        wager_amount = 0.007
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
        
        # We expect a 200 OK
        if response.status_code == 200 and response.json().get("success"):
            return True, response.json()
        else:
            return False, f"Expected 200 status code with success, got {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)

# Test 5: SolanaBust Wager Validation - Valid Maximum
def test_solanabust_wager_valid_maximum():
    try:
        # Place a wager at the maximum (0.05 SOL)
        wager_amount = 0.05
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
        
        # We expect a 200 OK
        if response.status_code == 200 and response.json().get("success"):
            return True, response.json()
        else:
            return False, f"Expected 200 status code with success, got {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)

# Test 6: Blackjack Wager Validation - Below Minimum
def test_blackjack_wager_below_minimum():
    try:
        # Place a wager below the minimum (0.01 SOL)
        wager_amount = 0.005
        response = requests.post(
            f"{API_URL}/game/wager",
            json={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "amount": wager_amount,
                "game_type": "blackjack",
                "session_id": str(uuid.uuid4()),
                "transaction_signature": TEST_SIGNATURE
            }
        )
        
        # We expect a 400 Bad Request
        if response.status_code == 400 and "Minimum wager is 0.01 SOL" in response.text:
            return True, {"status_code": response.status_code, "error": response.json()}
        else:
            return False, f"Expected 400 status code with minimum wager error, got {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)

# Test 7: Blackjack Wager Validation - Above Maximum
def test_blackjack_wager_above_maximum():
    try:
        # Place a wager above the maximum (10 SOL)
        wager_amount = 11.0
        response = requests.post(
            f"{API_URL}/game/wager",
            json={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "amount": wager_amount,
                "game_type": "blackjack",
                "session_id": str(uuid.uuid4()),
                "transaction_signature": TEST_SIGNATURE
            }
        )
        
        # We expect a 400 Bad Request
        if response.status_code == 400 and "Maximum wager is 10 SOL" in response.text:
            return True, {"status_code": response.status_code, "error": response.json()}
        else:
            return False, f"Expected 400 status code with maximum wager error, got {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)

# Test 8: Blackjack Wager Validation - Valid
def test_blackjack_wager_valid():
    try:
        # Place a valid wager (1 SOL)
        wager_amount = 1.0
        response = requests.post(
            f"{API_URL}/game/wager",
            json={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "amount": wager_amount,
                "game_type": "blackjack",
                "session_id": str(uuid.uuid4()),
                "transaction_signature": TEST_SIGNATURE
            }
        )
        
        # We expect a 200 OK
        if response.status_code == 200 and response.json().get("success"):
            return True, response.json()
        else:
            return False, f"Expected 200 status code with success, got {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)

# Test 9: Video Poker Wager Validation - Valid
def test_video_poker_wager_valid():
    try:
        # Place a valid wager (1 SOL)
        wager_amount = 1.0
        response = requests.post(
            f"{API_URL}/game/wager",
            json={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "amount": wager_amount,
                "game_type": "video_poker",
                "session_id": str(uuid.uuid4()),
                "transaction_signature": TEST_SIGNATURE
            }
        )
        
        # We expect a 200 OK
        if response.status_code == 200 and response.json().get("success"):
            return True, response.json()
        else:
            return False, f"Expected 200 status code with success, got {response.status_code}: {response.text}"
    except Exception as e:
        return False, str(e)

# Test 10: Dev Fee Calculation - Small Amounts
def test_dev_fee_calculation_small_amounts():
    try:
        # Test with small wager amounts
        wager_amounts = [0.005, 0.007, 0.01]
        results = []
        
        for wager_amount in wager_amounts:
            # Place a wager for crash game
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
            
            if response.status_code != 200:
                return False, f"Failed to place wager of {wager_amount} SOL: {response.text}"
            
            data = response.json()
            
            # Calculate expected values
            expected_dev_fee = wager_amount * TRANSACTION_FEE_PERCENTAGE
            expected_game_amount = wager_amount - expected_dev_fee
            
            # Verify fee calculation
            dev_fee_correct = abs(data["dev_fee"] - expected_dev_fee) < 0.0001
            game_amount_correct = abs(data["game_amount"] - expected_game_amount) < 0.0001
            
            results.append({
                "wager_amount": wager_amount,
                "expected_dev_fee": expected_dev_fee,
                "actual_dev_fee": data["dev_fee"],
                "expected_game_amount": expected_game_amount,
                "actual_game_amount": data["game_amount"],
                "dev_fee_correct": dev_fee_correct,
                "game_amount_correct": game_amount_correct,
                "fee_percentage": (data["dev_fee"] / wager_amount) * 100
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

# Test 11: Edge Case - Exactly at Boundary Values
def test_edge_case_boundary_values():
    try:
        # Test boundary values for SolanaBust
        test_cases = [
            {"game_type": "crash", "amount": 0.005, "expected_success": True, "description": "SolanaBust minimum"},
            {"game_type": "crash", "amount": 0.05, "expected_success": True, "description": "SolanaBust maximum"},
            {"game_type": "crash", "amount": 0.0049, "expected_success": False, "description": "Just below SolanaBust minimum"},
            {"game_type": "crash", "amount": 0.0501, "expected_success": False, "description": "Just above SolanaBust maximum"},
            {"game_type": "blackjack", "amount": 0.01, "expected_success": True, "description": "Blackjack minimum"},
            {"game_type": "blackjack", "amount": 10.0, "expected_success": True, "description": "Blackjack maximum"},
            {"game_type": "blackjack", "amount": 0.009, "expected_success": False, "description": "Just below Blackjack minimum"},
            {"game_type": "blackjack", "amount": 10.01, "expected_success": False, "description": "Just above Blackjack maximum"}
        ]
        
        results = []
        
        for test_case in test_cases:
            response = requests.post(
                f"{API_URL}/game/wager",
                json={
                    "player_wallet": TEST_WALLET_PUBLIC_KEY,
                    "amount": test_case["amount"],
                    "game_type": test_case["game_type"],
                    "session_id": str(uuid.uuid4()),
                    "transaction_signature": TEST_SIGNATURE
                }
            )
            
            success = (response.status_code == 200) == test_case["expected_success"]
            
            results.append({
                "description": test_case["description"],
                "game_type": test_case["game_type"],
                "amount": test_case["amount"],
                "expected_success": test_case["expected_success"],
                "actual_success": response.status_code == 200,
                "test_passed": success,
                "status_code": response.status_code,
                "response": response.json() if response.status_code == 200 else response.text[:100]
            })
        
        # Check if all tests passed
        all_passed = all(result["test_passed"] for result in results)
        
        return all_passed, {
            "test_cases": len(test_cases),
            "results": results
        }
    except Exception as e:
        return False, str(e)

def run_all_tests():
    tests = [
        ("SolanaBust Wager Validation - Below Minimum", test_solanabust_wager_below_minimum),
        ("SolanaBust Wager Validation - Above Maximum", test_solanabust_wager_above_maximum),
        ("SolanaBust Wager Validation - Valid Minimum", test_solanabust_wager_valid_minimum),
        ("SolanaBust Wager Validation - Valid Middle", test_solanabust_wager_valid_middle),
        ("SolanaBust Wager Validation - Valid Maximum", test_solanabust_wager_valid_maximum),
        ("Blackjack Wager Validation - Below Minimum", test_blackjack_wager_below_minimum),
        ("Blackjack Wager Validation - Above Maximum", test_blackjack_wager_above_maximum),
        ("Blackjack Wager Validation - Valid", test_blackjack_wager_valid),
        ("Video Poker Wager Validation - Valid", test_video_poker_wager_valid),
        ("Dev Fee Calculation - Small Amounts", test_dev_fee_calculation_small_amounts),
        ("Edge Case - Exactly at Boundary Values", test_edge_case_boundary_values)
    ]
    
    results = {}
    
    print("\n" + "=" * 80)
    print("SOLANABUST WAGER VALIDATION TESTS")
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