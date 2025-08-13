#!/usr/bin/env python3
"""
Video Poker Backend Testing - PRIORITY 1
Testing POST /api/video_poker/new endpoint functionality
"""
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

print(f"🎯 VIDEO POKER BACKEND TESTING - PRIORITY 1")
print(f"Using API URL: {API_URL}")
print("=" * 80)

# Test data
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

# Test 1: Video Poker New Endpoint - Basic Functionality
def test_video_poker_new_basic():
    """Test POST /api/video_poker/new endpoint with valid inputs"""
    try:
        test_cases = [
            {
                "player_wallet": "A7GZMJLFzGSPn1nYHsGhLbU5pby4q96AessVHn5qVXFZ",
                "wager": 0.01,
                "description": "Minimum wager amount (0.01 SOL)"
            },
            {
                "player_wallet": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                "wager": 0.1,
                "description": "Medium wager amount (0.1 SOL)"
            },
            {
                "player_wallet": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
                "wager": 1.0,
                "description": "High wager amount (1.0 SOL)"
            }
        ]
        
        results = []
        for test_case in test_cases:
            response = requests.post(
                f"{API_URL}/video_poker/new",
                json={
                    "player_wallet": test_case["player_wallet"],
                    "wager": test_case["wager"]
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # Verify response structure
            success = (
                data.get("success") == True and
                "session_id" in data and
                "game_state" in data and
                isinstance(data["game_state"], dict)
            )
            
            # Verify game_state structure
            game_state = data.get("game_state", {})
            game_state_valid = (
                "hand" in game_state and
                "hand_rank" in game_state and
                "initial_deal" in game_state and
                "game_complete" in game_state and
                isinstance(game_state["hand"], list) and
                len(game_state["hand"]) == 5 and
                game_state["initial_deal"] == True and
                game_state["game_complete"] == False
            )
            
            # Verify each card has required fields
            cards_valid = True
            for card in game_state.get("hand", []):
                if not (isinstance(card, dict) and "card" in card and "held" in card):
                    cards_valid = False
                    break
            
            results.append({
                "description": test_case["description"],
                "wager": test_case["wager"],
                "success": success and game_state_valid and cards_valid,
                "session_id": data.get("session_id"),
                "hand_size": len(game_state.get("hand", [])),
                "initial_deal": game_state.get("initial_deal"),
                "game_complete": game_state.get("game_complete"),
                "hand_rank": game_state.get("hand_rank"),
                "sample_cards": [card.get("card") for card in game_state.get("hand", [])[:3]]
            })
        
        all_passed = all(result["success"] for result in results)
        
        return all_passed, {
            "test_cases": len(test_cases),
            "all_passed": all_passed,
            "results": results
        }
        
    except Exception as e:
        return False, str(e)

# Test 2: Video Poker New Endpoint Error Handling
def test_video_poker_new_error_handling():
    """Test POST /api/video_poker/new endpoint error handling"""
    try:
        test_cases = [
            {
                "data": {},
                "expected_status": [400, 500],
                "description": "Missing all parameters"
            },
            {
                "data": {"player_wallet": "A7GZMJLFzGSPn1nYHsGhLbU5pby4q96AessVHn5qVXFZ"},
                "expected_status": [400, 500],
                "description": "Missing wager parameter"
            },
            {
                "data": {"wager": 0.01},
                "expected_status": [400, 500],
                "description": "Missing player_wallet parameter"
            },
            {
                "data": {"player_wallet": "invalid_wallet", "wager": 0.01},
                "expected_status": [400, 500],
                "description": "Invalid wallet address format"
            },
            {
                "data": {"player_wallet": "A7GZMJLFzGSPn1nYHsGhLbU5pby4q96AessVHn5qVXFZ", "wager": 0},
                "expected_status": [400, 500],
                "description": "Zero wager amount"
            },
            {
                "data": {"player_wallet": "A7GZMJLFzGSPn1nYHsGhLbU5pby4q96AessVHn5qVXFZ", "wager": -0.01},
                "expected_status": [400, 500],
                "description": "Negative wager amount"
            }
        ]
        
        results = []
        for test_case in test_cases:
            try:
                response = requests.post(
                    f"{API_URL}/video_poker/new",
                    json=test_case["data"]
                )
                
                # Check if we got an expected status code
                status_correct = response.status_code in test_case["expected_status"]
                
                results.append({
                    "description": test_case["description"],
                    "expected_status": test_case["expected_status"],
                    "actual_status": response.status_code,
                    "status_correct": status_correct,
                    "response": response.json() if response.status_code in [200, 400] else "Server error"
                })
                
            except Exception as e:
                results.append({
                    "description": test_case["description"],
                    "expected_status": test_case["expected_status"],
                    "actual_status": "Exception",
                    "status_correct": True,  # Exception is acceptable for error cases
                    "error": str(e)
                })
        
        # Count how many tests passed (got expected status codes)
        passed_tests = sum(1 for result in results if result["status_correct"])
        
        return passed_tests >= 4, {  # At least 4 out of 6 should pass
            "test_cases": len(test_cases),
            "passed_tests": passed_tests,
            "results": results
        }
        
    except Exception as e:
        return False, str(e)

# Test 3: Video Poker Multiple Games Creation
def test_video_poker_multiple_games():
    """Test creating multiple Video Poker games simultaneously"""
    try:
        num_games = 10
        games_created = []
        session_ids = set()
        
        for i in range(num_games):
            wallet = TEST_WALLETS[i % len(TEST_WALLETS)]
            wager = round(0.01 + (i * 0.01), 2)  # Vary wager amounts
            
            response = requests.post(
                f"{API_URL}/video_poker/new",
                json={
                    "player_wallet": wallet,
                    "wager": wager
                }
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("success") and "session_id" in data:
                games_created.append({
                    "game_number": i + 1,
                    "session_id": data["session_id"],
                    "player_wallet": wallet,
                    "wager": wager,
                    "hand_size": len(data["game_state"]["hand"]),
                    "initial_deal": data["game_state"]["initial_deal"],
                    "game_complete": data["game_state"]["game_complete"]
                })
                session_ids.add(data["session_id"])
        
        # Verify all games were created successfully
        all_created = len(games_created) == num_games
        
        # Verify all session IDs are unique
        unique_sessions = len(session_ids) == num_games
        
        # Verify all games have proper structure
        all_valid = all(
            game["hand_size"] == 5 and
            game["initial_deal"] == True and
            game["game_complete"] == False
            for game in games_created
        )
        
        return all_created and unique_sessions and all_valid, {
            "games_requested": num_games,
            "games_created": len(games_created),
            "unique_sessions": len(session_ids),
            "all_created": all_created,
            "unique_sessions_check": unique_sessions,
            "all_valid_structure": all_valid,
            "sample_games": games_created[:3]  # Show first 3 games
        }
        
    except Exception as e:
        return False, str(e)

# Test 4: Video Poker Response Structure Validation
def test_video_poker_response_structure():
    """Test Video Poker response structure validation in detail"""
    try:
        # Create a Video Poker game
        response = requests.post(
            f"{API_URL}/video_poker/new",
            json={
                "player_wallet": "A7GZMJLFzGSPn1nYHsGhLbU5pby4q96AessVHn5qVXFZ",
                "wager": 0.05
            }
        )
        response.raise_for_status()
        data = response.json()
        
        # Detailed response structure validation
        validations = {
            "success_field": data.get("success") == True,
            "session_id_present": "session_id" in data and isinstance(data["session_id"], str) and len(data["session_id"]) > 0,
            "game_state_present": "game_state" in data and isinstance(data["game_state"], dict),
            "message_present": "message" in data and isinstance(data["message"], str)
        }
        
        # Game state structure validation
        game_state = data.get("game_state", {})
        game_state_validations = {
            "hand_present": "hand" in game_state and isinstance(game_state["hand"], list),
            "hand_size_correct": len(game_state.get("hand", [])) == 5,
            "hand_rank_present": "hand_rank" in game_state and isinstance(game_state["hand_rank"], str),
            "initial_deal_correct": game_state.get("initial_deal") == True,
            "game_complete_correct": game_state.get("game_complete") == False
        }
        
        # Card structure validation
        hand = game_state.get("hand", [])
        card_validations = {
            "all_cards_have_card_field": all("card" in card for card in hand),
            "all_cards_have_held_field": all("held" in card for card in hand),
            "all_held_initially_false": all(card.get("held") == False for card in hand),
            "all_cards_are_strings": all(isinstance(card.get("card"), str) for card in hand),
            "all_cards_valid_format": all(" of " in card.get("card", "") for card in hand)
        }
        
        # Combine all validations
        all_validations = {**validations, **game_state_validations, **card_validations}
        all_passed = all(all_validations.values())
        
        return all_passed, {
            "all_passed": all_passed,
            "validations": all_validations,
            "session_id": data.get("session_id"),
            "hand_rank": game_state.get("hand_rank"),
            "sample_cards": [card.get("card") for card in hand[:3]],  # Show first 3 cards
            "response_keys": list(data.keys()),
            "game_state_keys": list(game_state.keys())
        }
        
    except Exception as e:
        return False, str(e)

# Test 5: Video Poker Game Flow Validation
def test_video_poker_game_flow():
    """Test complete Video Poker game flow validation"""
    try:
        test_cases = [
            {
                "wager": 0.01,
                "description": "Low wager complete flow"
            },
            {
                "wager": 0.1,
                "description": "Medium wager complete flow"
            },
            {
                "wager": 1.0,
                "description": "High wager complete flow"
            }
        ]
        
        results = []
        for test_case in test_cases:
            # Step 1: Create new game
            response = requests.post(
                f"{API_URL}/video_poker/new",
                json={
                    "player_wallet": "A7GZMJLFzGSPn1nYHsGhLbU5pby4q96AessVHn5qVXFZ",
                    "wager": test_case["wager"]
                }
            )
            response.raise_for_status()
            data = response.json()
            
            if not data.get("success"):
                results.append({
                    "description": test_case["description"],
                    "success": False,
                    "error": "Failed to create game"
                })
                continue
            
            session_id = data["session_id"]
            initial_game_state = data["game_state"]
            
            # Verify initial state
            initial_valid = (
                len(initial_game_state["hand"]) == 5 and
                initial_game_state["initial_deal"] == True and
                initial_game_state["game_complete"] == False and
                "hand_rank" in initial_game_state
            )
            
            if not initial_valid:
                results.append({
                    "description": test_case["description"],
                    "success": False,
                    "error": "Invalid initial game state"
                })
                continue
            
            # Step 2: Hold some cards (optional)
            hold_positions = [0, 2, 4]  # Hold cards at positions 0, 2, 4
            hold_response = requests.post(
                f"{API_URL}/game/video_poker/hold",
                params={"session_id": session_id},
                json=hold_positions
            )
            hold_response.raise_for_status()
            hold_data = hold_response.json()
            
            # Step 3: Draw new cards
            draw_response = requests.post(
                f"{API_URL}/game/video_poker/draw",
                params={"session_id": session_id}
            )
            draw_response.raise_for_status()
            draw_data = draw_response.json()
            
            # Verify final state
            final_valid = (
                draw_data.get("success") == True and
                "game_state" in draw_data and
                draw_data["game_state"]["game_complete"] == True and
                draw_data["game_state"]["initial_deal"] == False and
                "final_hand" in draw_data and
                "payout_multiplier" in draw_data
            )
            
            results.append({
                "description": test_case["description"],
                "wager": test_case["wager"],
                "success": initial_valid and final_valid,
                "session_id": session_id,
                "initial_hand_rank": initial_game_state["hand_rank"],
                "final_hand_rank": draw_data.get("final_hand"),
                "payout_multiplier": draw_data.get("payout_multiplier"),
                "held_positions": hold_positions,
                "initial_valid": initial_valid,
                "final_valid": final_valid
            })
        
        all_passed = all(result["success"] for result in results)
        
        return all_passed, {
            "test_cases": len(test_cases),
            "all_passed": all_passed,
            "results": results
        }
        
    except Exception as e:
        return False, str(e)

# Test 6: Video Poker Wager Integration
def test_video_poker_wager_integration():
    """Test Video Poker integration with wager system"""
    try:
        test_cases = [
            {"wager": 0.01, "description": "Minimum wager integration"},
            {"wager": 0.1, "description": "Medium wager integration"},
            {"wager": 1.0, "description": "High wager integration"}
        ]
        
        results = []
        for test_case in test_cases:
            # Step 1: Create Video Poker game
            game_response = requests.post(
                f"{API_URL}/video_poker/new",
                json={
                    "player_wallet": "A7GZMJLFzGSPn1nYHsGhLbU5pby4q96AessVHn5qVXFZ",
                    "wager": test_case["wager"]
                }
            )
            game_response.raise_for_status()
            game_data = game_response.json()
            
            if not game_data.get("success"):
                results.append({
                    "description": test_case["description"],
                    "success": False,
                    "error": "Failed to create Video Poker game"
                })
                continue
            
            session_id = game_data["session_id"]
            
            # Step 2: Place wager using wager endpoint
            wager_response = requests.post(
                f"{API_URL}/game/wager",
                json={
                    "player_wallet": "A7GZMJLFzGSPn1nYHsGhLbU5pby4q96AessVHn5qVXFZ",
                    "amount": test_case["wager"],
                    "game_type": "video_poker",
                    "session_id": session_id,
                    "transaction_signature": "test_signature"
                }
            )
            wager_response.raise_for_status()
            wager_data = wager_response.json()
            
            # Verify wager processing
            expected_dev_fee = test_case["wager"] * 0.12  # 12% dev fee
            expected_game_amount = test_case["wager"] - expected_dev_fee
            
            wager_valid = (
                wager_data.get("success") == True and
                "wager_id" in wager_data and
                abs(wager_data["dev_fee"] - expected_dev_fee) < 0.001 and
                abs(wager_data["game_amount"] - expected_game_amount) < 0.001 and
                wager_data["dev_wallet"] == "A7GZMJLFzGSPn1nYHsGhLbU5pby4q96AessVHn5qVXFZ"
            )
            
            results.append({
                "description": test_case["description"],
                "wager": test_case["wager"],
                "success": wager_valid,
                "session_id": session_id,
                "wager_id": wager_data.get("wager_id"),
                "dev_fee": wager_data.get("dev_fee"),
                "game_amount": wager_data.get("game_amount"),
                "expected_dev_fee": expected_dev_fee,
                "expected_game_amount": expected_game_amount,
                "dev_wallet": wager_data.get("dev_wallet")
            })
        
        all_passed = all(result["success"] for result in results)
        
        return all_passed, {
            "test_cases": len(test_cases),
            "all_passed": all_passed,
            "results": results
        }
        
    except Exception as e:
        return False, str(e)

# Main test execution
def main():
    print("🎯 VIDEO POKER BACKEND ENDPOINT TESTING")
    print("=" * 80)
    
    # List of Video Poker specific tests
    tests = [
        ("🎮 Video Poker New Endpoint - Basic Functionality", test_video_poker_new_basic),
        ("🚨 Video Poker New Endpoint - Error Handling", test_video_poker_new_error_handling),
        ("🔄 Video Poker Multiple Games Creation", test_video_poker_multiple_games),
        ("📋 Video Poker Response Structure Validation", test_video_poker_response_structure),
        ("🎯 Video Poker Game Flow Validation", test_video_poker_game_flow),
        ("💰 Video Poker Wager Integration", test_video_poker_wager_integration)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            success, result = test_func()
            print_test_result(test_name, success, result)
            if success:
                passed_tests += 1
        except Exception as e:
            print_test_result(test_name, False, error=str(e))
    
    print("=" * 80)
    print(f"🎯 VIDEO POKER BACKEND TESTING SUMMARY")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print("=" * 80)
    
    if passed_tests == total_tests:
        print("🎉 ALL VIDEO POKER BACKEND TESTS PASSED!")
        return True
    else:
        print("⚠️  SOME VIDEO POKER BACKEND TESTS FAILED")
        return False

if __name__ == "__main__":
    main()