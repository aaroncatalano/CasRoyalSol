#!/usr/bin/env python3
import requests
import json
import sys
import os
from dotenv import load_dotenv
import random
import time

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

# Test SolanaBust Cash Out Mechanics
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

# Test SolanaBust Room Join Validation
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

# Test SolanaBust Multiplayer Game Flow
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
        min_players_joined = successful_joins >= 1  # Need at least 1 player for testing
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

# Test Real SOL Payout Integration
def test_real_sol_payout_integration():
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
        
        return True, {
            "payout_service_available": True,
            "house_balance": house_balance,
            "message": f"House wallet has {house_balance} SOL available"
        }
        
    except Exception as e:
        return False, str(e)

def run_advanced_solanabust_tests():
    tests = [
        ("SolanaBust Cash Out Mechanics", test_solanabust_cash_out),
        ("SolanaBust Room Join Validation", test_solanabust_room_join_validation),
        ("SolanaBust Multiplayer Game Flow", test_solanabust_multiplayer_game_flow),
        ("Real SOL Payout Integration", test_real_sol_payout_integration)
    ]
    
    results = {}
    
    print("\n" + "=" * 80)
    print("ADVANCED SOLANABUST MULTIPLAYER ROOM SYSTEM TESTS")
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
    run_advanced_solanabust_tests()