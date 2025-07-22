#!/usr/bin/env python3
import requests
import json
import time
import sys
import os
from dotenv import load_dotenv
import random
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
TRANSACTION_FEE_PERCENTAGE = 0.12  # 12% developer fee

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

def test_solanabust_start_endpoint():
    """Test POST /api/solanabust/start endpoint"""
    print("\n🎯 TESTING POST /api/solanabust/start ENDPOINT")
    print("=" * 60)
    
    test_cases = [
        {"wager_amount": 0.01, "auto_cash_out": 2.0, "description": "Standard wager (0.01 SOL)"},
        {"wager_amount": 0.05, "auto_cash_out": 1.5, "description": "Higher wager (0.05 SOL)"},
        {"wager_amount": 0.1, "auto_cash_out": 5.0, "description": "High wager (0.1 SOL)"},
    ]
    
    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['description']}")
        try:
            response = requests.post(
                f"{API_URL}/solanabust/start",
                json={
                    "player_wallet": TEST_WALLET_PUBLIC_KEY,
                    "wager_amount": test_case["wager_amount"],
                    "auto_cash_out": test_case["auto_cash_out"],
                    "transaction_signature": TEST_SIGNATURE
                }
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
                
                # Verify response structure
                if (data.get("success") and 
                    "session_id" in data and 
                    "crash_point" in data and
                    "game_state" in data):
                    
                    crash_point = data["crash_point"]
                    if 1.01 <= crash_point <= 50.0:
                        # Calculate dev fee
                        expected_dev_fee = test_case["wager_amount"] * TRANSACTION_FEE_PERCENTAGE
                        
                        results.append({
                            "test": test_case["description"],
                            "success": True,
                            "session_id": data["session_id"],
                            "crash_point": crash_point,
                            "wager_amount": test_case["wager_amount"],
                            "expected_dev_fee": expected_dev_fee,
                            "game_state": data["game_state"]
                        })
                        print("✅ Test PASSED")
                    else:
                        results.append({
                            "test": test_case["description"],
                            "success": False,
                            "error": f"Crash point {crash_point} outside expected range (1.01-50.0)"
                        })
                        print("❌ Test FAILED - Invalid crash point range")
                else:
                    results.append({
                        "test": test_case["description"],
                        "success": False,
                        "error": "Response missing required fields"
                    })
                    print("❌ Test FAILED - Missing required fields")
            else:
                results.append({
                    "test": test_case["description"],
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                })
                print(f"❌ Test FAILED - HTTP {response.status_code}")
                
        except Exception as e:
            results.append({
                "test": test_case["description"],
                "success": False,
                "error": str(e)
            })
            print(f"❌ Test FAILED - Exception: {str(e)}")
        
        print("-" * 40)
    
    return results

def test_solanabust_cash_out_endpoint():
    """Test POST /api/solanabust/cash-out endpoint"""
    print("\n🎯 TESTING POST /api/solanabust/cash-out ENDPOINT")
    print("=" * 60)
    
    # First start a game
    print("Step 1: Starting a SolanaBust game...")
    try:
        start_response = requests.post(
            f"{API_URL}/solanabust/start",
            json={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "wager_amount": 0.05,
                "auto_cash_out": 3.0,
                "transaction_signature": TEST_SIGNATURE
            }
        )
        start_response.raise_for_status()
        start_data = start_response.json()
        
        if not start_data.get("success"):
            print("❌ Failed to start SolanaBust game for cash-out test")
            return [{"test": "Cash-out test", "success": False, "error": "Failed to start game"}]
        
        session_id = start_data["session_id"]
        crash_point = start_data["crash_point"]
        wager_amount = 0.05
        
        print(f"✅ Game started successfully")
        print(f"   Session ID: {session_id}")
        print(f"   Crash Point: {crash_point}")
        print(f"   Wager Amount: {wager_amount} SOL")
        
        # Test cash-out at different multipliers
        test_multipliers = [1.5, 2.0, 2.5]
        results = []
        
        for multiplier in test_multipliers:
            # Only test if multiplier is below crash point
            if multiplier < crash_point:
                print(f"\nStep 2: Testing cash-out at {multiplier}x multiplier...")
                payout_amount = wager_amount * multiplier
                
                try:
                    response = requests.post(
                        f"{API_URL}/solanabust/cash-out",
                        json={
                            "session_id": session_id,
                            "player_wallet": TEST_WALLET_PUBLIC_KEY,
                            "cash_out_multiplier": multiplier,
                            "payout_amount": payout_amount
                        }
                    )
                    
                    print(f"Status Code: {response.status_code}")
                    
                    if response.status_code == 200:
                        data = response.json()
                        print(f"Response: {json.dumps(data, indent=2)}")
                        
                        # Verify cash-out response
                        if (data.get("success") and 
                            data.get("cashed_out") and
                            "multiplier" in data and
                            "payout_amount" in data):
                            
                            # Verify payout calculation
                            expected_payout = wager_amount * multiplier
                            if abs(data["payout_amount"] - expected_payout) < 0.001:
                                results.append({
                                    "test": f"Cash-out at {multiplier}x",
                                    "success": True,
                                    "session_id": session_id,
                                    "crash_point": crash_point,
                                    "cash_out_multiplier": multiplier,
                                    "wager_amount": wager_amount,
                                    "payout_amount": data["payout_amount"],
                                    "payout_sent": data.get("payout_sent", False),
                                    "transaction_signature": data.get("transaction_signature")
                                })
                                print("✅ Cash-out test PASSED")
                                break  # Only test one successful cash-out
                            else:
                                results.append({
                                    "test": f"Cash-out at {multiplier}x",
                                    "success": False,
                                    "error": f"Payout calculation incorrect: expected {expected_payout}, got {data['payout_amount']}"
                                })
                                print("❌ Cash-out test FAILED - Incorrect payout calculation")
                        else:
                            results.append({
                                "test": f"Cash-out at {multiplier}x",
                                "success": False,
                                "error": "Cash-out response missing required fields"
                            })
                            print("❌ Cash-out test FAILED - Missing required fields")
                    else:
                        results.append({
                            "test": f"Cash-out at {multiplier}x",
                            "success": False,
                            "error": f"HTTP {response.status_code}: {response.text}"
                        })
                        print(f"❌ Cash-out test FAILED - HTTP {response.status_code}")
                        
                except Exception as e:
                    results.append({
                        "test": f"Cash-out at {multiplier}x",
                        "success": False,
                        "error": str(e)
                    })
                    print(f"❌ Cash-out test FAILED - Exception: {str(e)}")
                
                print("-" * 40)
                break  # Only test one multiplier
        
        if not results:
            results.append({
                "test": "Cash-out test",
                "success": False,
                "error": f"No valid multiplier found for cash-out test (crash point: {crash_point})"
            })
        
        return results
        
    except Exception as e:
        return [{"test": "Cash-out test", "success": False, "error": str(e)}]

def test_database_integration():
    """Test database integration for SolanaBust games"""
    print("\n🎯 TESTING DATABASE INTEGRATION")
    print("=" * 60)
    
    try:
        wager_amount = 0.02
        auto_cash_out = 2.5
        
        print("Step 1: Starting a SolanaBust game...")
        # Start a game
        start_response = requests.post(
            f"{API_URL}/solanabust/start",
            json={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "wager_amount": wager_amount,
                "auto_cash_out": auto_cash_out,
                "transaction_signature": TEST_SIGNATURE
            }
        )
        start_response.raise_for_status()
        start_data = start_response.json()
        
        if not start_data.get("success"):
            return [{"test": "Database integration", "success": False, "error": "Failed to start SolanaBust game"}]
        
        session_id = start_data["session_id"]
        crash_point = start_data["crash_point"]
        
        print(f"✅ Game started successfully")
        print(f"   Session ID: {session_id}")
        print(f"   Crash Point: {crash_point}")
        
        # Verify dev fee calculation
        expected_dev_fee = wager_amount * TRANSACTION_FEE_PERCENTAGE
        print(f"   Expected Dev Fee: {expected_dev_fee} SOL")
        
        print("\nStep 2: Checking database storage...")
        # Get player sessions to verify database storage
        sessions_response = requests.get(f"{API_URL}/game/sessions/{TEST_WALLET_PUBLIC_KEY}")
        sessions_response.raise_for_status()
        sessions_data = sessions_response.json()
        
        print(f"Sessions response: {json.dumps(sessions_data, indent=2)}")
        
        # Find our session
        session_found = False
        for session in sessions_data.get("sessions", []):
            if session.get("id") == session_id and session.get("game_type") == "crash":
                session_found = True
                print("✅ Session found in database")
                break
        
        if not session_found:
            print("❌ Session not found in database")
        
        return [{
            "test": "Database integration",
            "success": session_found,
            "session_id": session_id,
            "wager_amount": wager_amount,
            "expected_dev_fee": expected_dev_fee,
            "crash_point": crash_point,
            "session_stored": session_found,
            "auto_cash_out": auto_cash_out
        }]
        
    except Exception as e:
        return [{"test": "Database integration", "success": False, "error": str(e)}]

def test_error_handling():
    """Test error handling for various invalid scenarios"""
    print("\n🎯 TESTING ERROR HANDLING")
    print("=" * 60)
    
    error_test_cases = [
        {
            "description": "Missing player wallet",
            "data": {
                "wager_amount": 0.01,
                "auto_cash_out": 2.0
            },
            "expected_status": 400
        },
        {
            "description": "Missing wager amount", 
            "data": {
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "auto_cash_out": 2.0
            },
            "expected_status": 400
        },
        {
            "description": "Invalid wager amount (too low)",
            "data": {
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "wager_amount": 0.004,
                "auto_cash_out": 2.0
            },
            "expected_status": 400
        },
        {
            "description": "Invalid wager amount (too high)",
            "data": {
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "wager_amount": 0.051,
                "auto_cash_out": 2.0
            },
            "expected_status": 400
        }
    ]
    
    results = []
    for i, test_case in enumerate(error_test_cases, 1):
        print(f"\nTest {i}: {test_case['description']}")
        try:
            response = requests.post(f"{API_URL}/solanabust/start", json=test_case["data"])
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            status_correct = response.status_code == test_case["expected_status"]
            
            results.append({
                "description": test_case["description"],
                "expected_status": test_case["expected_status"],
                "actual_status": response.status_code,
                "status_correct": status_correct,
                "response": response.json() if response.status_code != 500 else {"error": "Server error"}
            })
            
            if status_correct:
                print("✅ Error handling test PASSED")
            else:
                print(f"❌ Error handling test FAILED - Expected {test_case['expected_status']}, got {response.status_code}")
                
        except Exception as e:
            results.append({
                "description": test_case["description"],
                "error": str(e),
                "status_correct": False
            })
            print(f"❌ Error handling test FAILED - Exception: {str(e)}")
        
        print("-" * 40)
    
    return results

def main():
    print("🚀 SOLANABUST SINGLE PLAYER BACKEND ENDPOINT TESTING")
    print("=" * 80)
    
    all_results = []
    
    # Test 1: Start endpoint
    start_results = test_solanabust_start_endpoint()
    all_results.extend(start_results)
    
    # Test 2: Cash-out endpoint
    cash_out_results = test_solanabust_cash_out_endpoint()
    all_results.extend(cash_out_results)
    
    # Test 3: Database integration
    db_results = test_database_integration()
    all_results.extend(db_results)
    
    # Test 4: Error handling
    error_results = test_error_handling()
    all_results.extend(error_results)
    
    # Summary
    print("\n" + "=" * 80)
    print("🎯 SOLANABUST SINGLE PLAYER TESTING SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for result in all_results if result.get("success", False))
    total = len(all_results)
    
    for result in all_results:
        status = "✅ PASSED" if result.get("success", False) else "❌ FAILED"
        test_name = result.get("test", result.get("description", "Unknown test"))
        print(f"{status} - {test_name}")
        if not result.get("success", False) and "error" in result:
            print(f"    Error: {result['error']}")
    
    print("-" * 80)
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {passed/total*100:.2f}%")
    print("=" * 80)

if __name__ == "__main__":
    main()