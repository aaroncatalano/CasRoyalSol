#!/usr/bin/env python3
import requests
import json
import sys
import os
from dotenv import load_dotenv

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
TRANSACTION_FEE_PERCENTAGE = 0.12  # 12% - UPDATED DEV FEE

# Additional test wallets for variety
TEST_WALLETS = [
    "A7GZMJLFzGSPn1nYHsGhLbU5pby4q96AessVHn5qVXFZ",
    "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
    "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"
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

# Test: POST /api/game/wager endpoint with blackjack game type
def test_wager_endpoint_blackjack():
    """Test POST /api/game/wager endpoint with blackjack game type and 12% dev fee"""
    try:
        test_amounts = [0.01, 0.1, 1.0]  # Various wager amounts
        results = []
        
        for amount in test_amounts:
            # Create a session first
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
            expected_dev_fee = amount * TRANSACTION_FEE_PERCENTAGE
            expected_game_amount = amount - expected_dev_fee
            
            # Verify response
            success = (
                data.get("success") and
                "wager_id" in data and
                abs(data.get("dev_fee", 0) - expected_dev_fee) < 0.001 and
                abs(data.get("game_amount", 0) - expected_game_amount) < 0.001 and
                data.get("dev_wallet") == DEV_WALLET_ADDRESS and
                data.get("total_amount") == amount
            )
            
            results.append({
                "amount": amount,
                "success": success,
                "dev_fee": data.get("dev_fee"),
                "expected_dev_fee": expected_dev_fee,
                "game_amount": data.get("game_amount"),
                "expected_game_amount": expected_game_amount,
                "dev_wallet": data.get("dev_wallet")
            })
        
        all_passed = all(result["success"] for result in results)
        return all_passed, {"test_results": results}
        
    except Exception as e:
        return False, str(e)

# Test: POST /api/game/wager endpoint with video_poker game type
def test_wager_endpoint_video_poker():
    """Test POST /api/game/wager endpoint with video_poker game type and 12% dev fee"""
    try:
        test_amounts = [0.01, 0.1, 1.0]  # Various wager amounts
        results = []
        
        for amount in test_amounts:
            # Create a session first
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
            
            # Place wager
            response = requests.post(
                f"{API_URL}/game/wager",
                json={
                    "player_wallet": TEST_WALLET_PUBLIC_KEY,
                    "amount": amount,
                    "game_type": "video_poker",
                    "session_id": session_id,
                    "transaction_signature": TEST_SIGNATURE
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # Calculate expected values
            expected_dev_fee = amount * TRANSACTION_FEE_PERCENTAGE
            expected_game_amount = amount - expected_dev_fee
            
            # Verify response
            success = (
                data.get("success") and
                "wager_id" in data and
                abs(data.get("dev_fee", 0) - expected_dev_fee) < 0.001 and
                abs(data.get("game_amount", 0) - expected_game_amount) < 0.001 and
                data.get("dev_wallet") == DEV_WALLET_ADDRESS and
                data.get("total_amount") == amount
            )
            
            results.append({
                "amount": amount,
                "success": success,
                "dev_fee": data.get("dev_fee"),
                "expected_dev_fee": expected_dev_fee,
                "game_amount": data.get("game_amount"),
                "expected_game_amount": expected_game_amount,
                "dev_wallet": data.get("dev_wallet")
            })
        
        all_passed = all(result["success"] for result in results)
        return all_passed, {"test_results": results}
        
    except Exception as e:
        return False, str(e)

# Test: POST /api/blackjack/new endpoint
def test_blackjack_new_endpoint():
    """Test POST /api/blackjack/new endpoint with different player wallets"""
    try:
        results = []
        
        for i, wallet in enumerate(TEST_WALLETS[:3]):  # Test with 3 different wallets
            wager_amount = 0.05 + (i * 0.05)  # Different wager amounts
            
            response = requests.post(
                f"{API_URL}/blackjack/new",
                json={
                    "player_wallet": wallet,
                    "wager": wager_amount
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # Verify response structure
            success = (
                data.get("success") and
                "session_id" in data and
                "game_state" in data and
                "message" in data and
                "player_hands" in data["game_state"] and
                "dealer_hand" in data["game_state"] and
                len(data["game_state"]["player_hands"]) > 0 and
                len(data["game_state"]["player_hands"][0]["cards"]) == 2 and  # Initial deal
                len(data["game_state"]["dealer_hand"]["cards"]) == 2  # Initial deal
            )
            
            results.append({
                "wallet": wallet,
                "wager": wager_amount,
                "success": success,
                "session_id": data.get("session_id"),
                "player_hand_value": data["game_state"]["player_hands"][0]["value"] if success else None,
                "dealer_hand_value": data["game_state"]["dealer_hand"]["value"] if success else None,
                "game_over": data["game_state"].get("game_over", False) if success else None
            })
        
        all_passed = all(result["success"] for result in results)
        return all_passed, {"test_results": results}
        
    except Exception as e:
        return False, str(e)

# Test: POST /api/video_poker/new endpoint
def test_video_poker_new_endpoint():
    """Test POST /api/video_poker/new endpoint with different player wallets"""
    try:
        results = []
        
        for i, wallet in enumerate(TEST_WALLETS[:3]):  # Test with 3 different wallets
            wager_amount = 0.05 + (i * 0.05)  # Different wager amounts
            
            response = requests.post(
                f"{API_URL}/video_poker/new",
                json={
                    "player_wallet": wallet,
                    "wager": wager_amount
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # Verify response structure
            success = (
                data.get("success") and
                "session_id" in data and
                "game_state" in data and
                "message" in data and
                "hand" in data["game_state"] and
                len(data["game_state"]["hand"]) == 5 and  # 5 cards in video poker
                "hand_rank" in data["game_state"] and
                "initial_deal" in data["game_state"] and
                data["game_state"]["initial_deal"] == True
            )
            
            results.append({
                "wallet": wallet,
                "wager": wager_amount,
                "success": success,
                "session_id": data.get("session_id"),
                "hand_rank": data["game_state"]["hand_rank"] if success else None,
                "initial_deal": data["game_state"]["initial_deal"] if success else None,
                "game_complete": data["game_state"].get("game_complete", False) if success else None
            })
        
        all_passed = all(result["success"] for result in results)
        return all_passed, {"test_results": results}
        
    except Exception as e:
        return False, str(e)

# Test: Error handling for missing parameters
def test_error_handling_missing_parameters():
    """Test error handling with missing parameters"""
    try:
        test_cases = [
            {
                "name": "Blackjack new - missing player_wallet",
                "endpoint": f"{API_URL}/blackjack/new",
                "data": {"wager": 1.0}
            },
            {
                "name": "Blackjack new - missing wager",
                "endpoint": f"{API_URL}/blackjack/new",
                "data": {"player_wallet": TEST_WALLET_PUBLIC_KEY}
            },
            {
                "name": "Video poker new - missing player_wallet",
                "endpoint": f"{API_URL}/video_poker/new",
                "data": {"wager": 1.0}
            },
            {
                "name": "Video poker new - missing wager",
                "endpoint": f"{API_URL}/video_poker/new",
                "data": {"player_wallet": TEST_WALLET_PUBLIC_KEY}
            }
        ]
        
        results = []
        for test_case in test_cases:
            try:
                response = requests.post(test_case["endpoint"], json=test_case["data"])
                
                # Check if we got the expected error status
                success = response.status_code in [400, 422, 500]  # Any error status is acceptable
                
                results.append({
                    "name": test_case["name"],
                    "success": success,
                    "status_code": response.status_code,
                    "expected_error": True,
                    "got_error": response.status_code >= 400
                })
                
            except Exception as e:
                # Exception is also acceptable for missing parameters
                results.append({
                    "name": test_case["name"],
                    "success": True,  # Exception means error handling worked
                    "error": str(e),
                    "expected_error": True,
                    "got_error": True
                })
        
        all_passed = all(result["success"] for result in results)
        return all_passed, {"test_results": results}
        
    except Exception as e:
        return False, str(e)

# Test: Error handling for invalid wallet addresses
def test_error_handling_invalid_wallets():
    """Test error handling with invalid wallet addresses"""
    try:
        invalid_wallets = [
            "invalid_wallet",
            "123",
            "",
            "not_a_solana_address"
        ]
        
        results = []
        for wallet in invalid_wallets:
            try:
                # Test with blackjack new endpoint
                response = requests.post(
                    f"{API_URL}/blackjack/new",
                    json={
                        "player_wallet": wallet,
                        "wager": 1.0
                    }
                )
                
                # Should get an error status
                success = response.status_code >= 400
                
                results.append({
                    "wallet": wallet,
                    "endpoint": "blackjack/new",
                    "success": success,
                    "status_code": response.status_code,
                    "got_error": response.status_code >= 400
                })
                
            except Exception as e:
                # Exception is also acceptable for invalid wallets
                results.append({
                    "wallet": wallet,
                    "endpoint": "blackjack/new",
                    "success": True,  # Exception means validation worked
                    "error": str(e),
                    "got_error": True
                })
        
        all_passed = all(result["success"] for result in results)
        return all_passed, {"test_results": results}
        
    except Exception as e:
        return False, str(e)

# Test: 12% Dev fee calculation verification
def test_dev_fee_calculation_verification():
    """Test 12% dev fee calculation with various amounts"""
    try:
        test_amounts = [0.01, 0.05, 0.1, 0.5, 1.0]  # Various amounts
        results = []
        
        for amount in test_amounts:
            # Test with blackjack
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
            expected_dev_fee = amount * TRANSACTION_FEE_PERCENTAGE
            expected_game_amount = amount - expected_dev_fee
            
            # Verify calculation accuracy
            dev_fee_accurate = abs(data.get("dev_fee", 0) - expected_dev_fee) < 0.000001
            game_amount_accurate = abs(data.get("game_amount", 0) - expected_game_amount) < 0.000001
            
            results.append({
                "amount": amount,
                "dev_fee": data.get("dev_fee"),
                "expected_dev_fee": expected_dev_fee,
                "game_amount": data.get("game_amount"),
                "expected_game_amount": expected_game_amount,
                "dev_fee_accurate": dev_fee_accurate,
                "game_amount_accurate": game_amount_accurate,
                "percentage_accurate": abs((data.get("dev_fee", 0) / amount) - TRANSACTION_FEE_PERCENTAGE) < 0.000001
            })
        
        all_accurate = all(
            result["dev_fee_accurate"] and 
            result["game_amount_accurate"] and 
            result["percentage_accurate"] 
            for result in results
        )
        
        return all_accurate, {
            "test_results": results,
            "fee_percentage": TRANSACTION_FEE_PERCENTAGE,
            "all_calculations_accurate": all_accurate
        }
        
    except Exception as e:
        return False, str(e)

def run_requested_tests():
    """Run the specific tests requested by the user"""
    print("=" * 80)
    print("BLACKJACK AND VIDEO POKER BACKEND ENDPOINT TESTING")
    print("Testing 12% Dev Fee Calculation and API Endpoints")
    print("=" * 80)
    
    # List of tests to run based on user request
    tests_to_run = [
        ("POST /api/game/wager - Blackjack", test_wager_endpoint_blackjack),
        ("POST /api/game/wager - Video Poker", test_wager_endpoint_video_poker),
        ("POST /api/blackjack/new", test_blackjack_new_endpoint),
        ("POST /api/video_poker/new", test_video_poker_new_endpoint),
        ("Error Handling - Missing Parameters", test_error_handling_missing_parameters),
        ("Error Handling - Invalid Wallets", test_error_handling_invalid_wallets),
        ("12% Dev Fee Calculation Verification", test_dev_fee_calculation_verification),
    ]
    
    passed_tests = 0
    total_tests = len(tests_to_run)
    test_results = []
    
    for test_name, test_func in tests_to_run:
        print(f"\n🧪 Running: {test_name}")
        try:
            success, response = test_func()
            print_test_result(test_name, success, response if success else None, response if not success else None)
            
            if success:
                passed_tests += 1
            
            test_results.append({
                "name": test_name,
                "success": success,
                "response": response
            })
            
        except Exception as e:
            print_test_result(test_name, False, None, str(e))
            test_results.append({
                "name": test_name,
                "success": False,
                "error": str(e)
            })
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests / total_tests) * 100:.1f}%")
    
    # Print detailed results
    print("\n📊 DETAILED RESULTS:")
    for result in test_results:
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        print(f"  {status}: {result['name']}")
    
    print("\n" + "=" * 80)
    
    return {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": total_tests - passed_tests,
        "success_rate": (passed_tests / total_tests) * 100,
        "test_results": test_results
    }

if __name__ == "__main__":
    print("🚀 Starting Backend API Testing...")
    print(f"Backend URL: {API_URL}")
    print(f"Dev Fee Percentage: {TRANSACTION_FEE_PERCENTAGE * 100}%")
    print(f"Dev Wallet: {DEV_WALLET_ADDRESS}")
    
    # Run the requested tests
    results = run_requested_tests()
    
    # Exit with appropriate code
    if results["success_rate"] == 100:
        print("\n🎉 All tests passed! Backend is ready for frontend integration.")
        sys.exit(0)
    else:
        print(f"\n⚠️  {results['failed_tests']} test(s) failed. Please review the issues above.")
        sys.exit(1)