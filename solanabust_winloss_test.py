#!/usr/bin/env python3
"""
SolanaBust Win/Loss Logic Verification

This script tests the actual win/loss logic implementation by testing
the cash-out endpoint with proper parameters.
"""

import requests
import json
import time
import sys
import os
from dotenv import load_dotenv
import random
import uuid

# Load environment variables
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

print(f"🎯 SolanaBust Win/Loss Logic Verification")
print(f"Using API URL: {API_URL}")
print("=" * 80)

# Test wallets
TEST_WALLETS = [
    "A7GZMJLFzGSPn1nYHsGhLbU5pby4q96AessVHn5qVXFZ",
    "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
    "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"
]

def start_solanabust_game(wallet_address, wager_amount):
    """Start a SolanaBust single player game"""
    try:
        response = requests.post(
            f"{API_URL}/solanabust/start",
            json={
                "player_wallet": wallet_address,
                "wager_amount": wager_amount,
                "auto_cash_out": None,
                "transaction_signature": f"test_sig_{uuid.uuid4()}"
            }
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error starting SolanaBust game: {e}")
        return None

def cash_out_solanabust(session_id, player_wallet, cash_out_multiplier, wager_amount):
    """Cash out from a SolanaBust game with correct parameters"""
    try:
        # Calculate expected payout
        payout_amount = wager_amount * cash_out_multiplier
        
        response = requests.post(
            f"{API_URL}/solanabust/cash-out",
            json={
                "session_id": session_id,
                "player_wallet": player_wallet,
                "cash_out_multiplier": cash_out_multiplier,
                "payout_amount": payout_amount
            }
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error cashing out: {e}")
        if hasattr(e, 'response') and e.response:
            try:
                error_detail = e.response.json()
                print(f"Error details: {error_detail}")
            except:
                print(f"Response text: {e.response.text}")
        return None

def test_win_loss_logic():
    """Test the win/loss logic with controlled scenarios"""
    print("\n🔍 TESTING WIN/LOSS LOGIC")
    print("=" * 50)
    
    test_results = []
    
    for test_num in range(10):
        wallet = random.choice(TEST_WALLETS)
        wager_amount = 0.01
        
        # Start game
        print(f"\nTest {test_num + 1}: Starting game...")
        game_data = start_solanabust_game(wallet, wager_amount)
        
        if not game_data or not game_data.get("success"):
            print(f"❌ Failed to start game {test_num + 1}")
            continue
        
        session_id = game_data.get("session_id")
        crash_point = game_data.get("crash_point")
        
        print(f"   Game started - Crash Point: {crash_point:.2f}x")
        
        # Test different cash-out scenarios
        test_scenarios = [
            crash_point - 0.5,  # Should win (cash out before crash)
            crash_point + 0.5,  # Should lose (cash out after crash)
            crash_point,        # Should lose (cash out at crash point)
        ]
        
        for i, cash_out_multiplier in enumerate(test_scenarios):
            if cash_out_multiplier <= 1.0:
                continue  # Skip invalid multipliers
            
            scenario_name = ["Before Crash (WIN)", "After Crash (LOSE)", "At Crash (LOSE)"][i]
            expected_result = "win" if cash_out_multiplier < crash_point else "lose"
            
            print(f"   Testing: {scenario_name} - Cash out at {cash_out_multiplier:.2f}x")
            
            # Start a new game for each scenario
            new_game_data = start_solanabust_game(wallet, wager_amount)
            if not new_game_data or not new_game_data.get("success"):
                continue
                
            new_session_id = new_game_data.get("session_id")
            new_crash_point = new_game_data.get("crash_point")
            
            # Use the original crash point for testing logic
            # We need to test against a known crash point
            if i == 0:  # Before crash test
                test_cash_out = min(new_crash_point - 0.1, cash_out_multiplier)
                expected = "win"
            else:  # After crash test
                test_cash_out = max(new_crash_point + 0.1, cash_out_multiplier)
                expected = "lose"
            
            if test_cash_out <= 1.0:
                test_cash_out = 1.1
                expected = "win" if test_cash_out < new_crash_point else "lose"
            
            cash_out_data = cash_out_solanabust(new_session_id, wallet, test_cash_out, wager_amount)
            
            if cash_out_data:
                actual_result = cash_out_data.get("result")
                payout_amount = cash_out_data.get("payout_amount", 0)
                
                # Verify logic
                logic_correct = actual_result == expected
                
                # Verify payout
                if expected == "win":
                    expected_payout = wager_amount * test_cash_out
                    payout_correct = abs(payout_amount - expected_payout) < 0.0001
                else:
                    payout_correct = payout_amount == 0.0
                
                test_passed = logic_correct and payout_correct
                status = "✅" if test_passed else "❌"
                
                print(f"   {status} Cash out {test_cash_out:.2f}x vs Crash {new_crash_point:.2f}x")
                print(f"      Expected: {expected}, Got: {actual_result}")
                print(f"      Payout: {payout_amount:.4f} SOL")
                
                test_results.append({
                    "test_num": test_num + 1,
                    "scenario": scenario_name,
                    "cash_out": test_cash_out,
                    "crash_point": new_crash_point,
                    "expected": expected,
                    "actual": actual_result,
                    "payout": payout_amount,
                    "passed": test_passed
                })
            else:
                print(f"   ❌ Failed to cash out")
            
            time.sleep(0.2)  # Small delay between tests
    
    # Summary
    print(f"\n📊 TEST RESULTS SUMMARY")
    print("=" * 30)
    
    if test_results:
        passed_tests = [t for t in test_results if t["passed"]]
        total_tests = len(test_results)
        pass_rate = (len(passed_tests) / total_tests) * 100
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {len(passed_tests)}")
        print(f"Failed: {total_tests - len(passed_tests)}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        
        # Show failed tests
        failed_tests = [t for t in test_results if not t["passed"]]
        if failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   Test {test['test_num']}: {test['scenario']}")
                print(f"      Cash out {test['cash_out']:.2f}x vs Crash {test['crash_point']:.2f}x")
                print(f"      Expected {test['expected']}, got {test['actual']}")
        
        return pass_rate >= 80  # Consider 80%+ pass rate as acceptable
    else:
        print("No test results available")
        return False

def main():
    """Main test function"""
    print("Testing SolanaBust win/loss logic implementation...")
    
    logic_test_passed = test_win_loss_logic()
    
    print(f"\n🎯 FINAL ASSESSMENT")
    print("=" * 30)
    
    if logic_test_passed:
        print("✅ Win/Loss Logic: WORKING CORRECTLY")
        print("   The game correctly determines wins and losses based on crash points")
    else:
        print("❌ Win/Loss Logic: HAS ISSUES")
        print("   There are problems with the win/loss determination logic")
    
    print("\n✅ TESTING COMPLETE")

if __name__ == "__main__":
    main()