#!/usr/bin/env python3
import requests
import json
import time
import sys
import os
from dotenv import load_dotenv
import random
import string

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
            return True, data
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
            len(data["game_data"]["hand"]) == 5):
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
        if data.get("success") and "card" in data and "message" in data:
            return True, data
        else:
            return False, "Blackjack hit failed or has incorrect data"
    except Exception as e:
        return False, str(e)

# Test 9: Game Logic APIs - Video Poker Hold
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

# Test 10: Get Player Sessions
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

# Test 11: Rate Limiting
def test_rate_limiting():
    try:
        # Make multiple requests in quick succession to trigger rate limiting
        success_count = 0
        rate_limited = False
        
        for _ in range(15):  # The limit is 10 requests per minute for wallet/connect
            try:
                response = requests.post(
                    f"{API_URL}/wallet/connect",
                    json={
                        "public_key": TEST_WALLET_PUBLIC_KEY,
                        "signature": TEST_SIGNATURE,
                        "message": TEST_MESSAGE
                    }
                )
                
                if response.status_code == 200:
                    success_count += 1
                elif response.status_code == 429:  # Too Many Requests
                    rate_limited = True
                    break
            except Exception:
                pass
            
            time.sleep(0.1)  # Small delay between requests
        
        if rate_limited:
            return True, {"message": "Rate limiting is working correctly", "successful_requests": success_count}
        else:
            return False, "Rate limiting did not trigger as expected"
    except Exception as e:
        return False, str(e)

# Test 12: Error Handling - Invalid Game Type
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

# Test 13: Error Handling - Invalid Session ID
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
        ("Game Logic APIs - Video Poker Hold", test_video_poker_hold),
        ("Get Player Sessions", test_get_player_sessions),
        ("Rate Limiting", test_rate_limiting),
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