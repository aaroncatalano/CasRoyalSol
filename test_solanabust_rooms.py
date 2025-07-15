#!/usr/bin/env python3
import requests
import json
import sys
import os
from dotenv import load_dotenv
import random

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

# Test SolanaBust Room Join
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

# Test SolanaBust Active Room Status
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

# Test SolanaBust Room State Retrieval
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

# Test SolanaBust 12% Developer Fee Calculation
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

def run_solanabust_room_tests():
    tests = [
        ("SolanaBust Room Join", test_solanabust_room_join),
        ("SolanaBust Active Room Status", test_solanabust_active_room),
        ("SolanaBust Room State Retrieval", test_solanabust_room_state),
        ("SolanaBust 12% Developer Fee Calculation", test_solanabust_12_percent_dev_fee)
    ]
    
    results = {}
    
    print("\n" + "=" * 80)
    print("SOLANABUST MULTIPLAYER ROOM SYSTEM TESTS")
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
    run_solanabust_room_tests()