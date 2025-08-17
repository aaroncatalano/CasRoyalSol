#!/usr/bin/env python3
"""
SolanaBust Odds Analysis - Critical Analysis for Players Winning Too Frequently

This script performs comprehensive analysis of the SolanaBust crash game to identify
why players are winning too frequently despite the 70% house edge implementation.

Analysis includes:
1. Crash Point Distribution Analysis (50 games)
2. Player Behavior Simulation (different cash-out strategies)
3. Win/Loss Logic Verification
4. Mathematical Analysis (expected values and house edge)
5. Frontend Behavior Analysis
"""

import requests
import json
import time
import sys
import os
from dotenv import load_dotenv
import random
import statistics
import uuid
from collections import defaultdict
import math

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

print(f"🎯 SolanaBust Odds Analysis")
print(f"Using API URL: {API_URL}")
print("=" * 80)

# Test wallets for variety
TEST_WALLETS = [
    "A7GZMJLFzGSPn1nYHsGhLbU5pby4q96AessVHn5qVXFZ",
    "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
    "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
    "GDfnEsia2WLAW5t8yx2X5j2mkfA74i5kwGdDuZHt7XmG"
]

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*80}")
    print(f"🔍 {title}")
    print(f"{'='*80}")

def print_result(test_name, success, details=None):
    """Print formatted test results"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if details:
        if isinstance(details, dict):
            for key, value in details.items():
                print(f"   {key}: {value}")
        else:
            print(f"   {details}")
    print("-" * 40)

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

def cash_out_solanabust(session_id, cash_out_multiplier):
    """Cash out from a SolanaBust game"""
    try:
        response = requests.post(
            f"{API_URL}/solanabust/cash-out",
            json={
                "session_id": session_id,
                "cash_out_multiplier": cash_out_multiplier
            }
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error cashing out: {e}")
        return None

def analyze_crash_point_distribution():
    """
    1. Crash Point Distribution Analysis
    Generate 50 crash points and analyze distribution
    """
    print_section("1. CRASH POINT DISTRIBUTION ANALYSIS")
    
    crash_points = []
    games_data = []
    
    print("Generating 50 crash points...")
    
    for i in range(50):
        wallet = random.choice(TEST_WALLETS)
        wager_amount = 0.01  # Standard test amount
        
        game_data = start_solanabust_game(wallet, wager_amount)
        if game_data and game_data.get("success"):
            crash_point = game_data.get("crash_point")
            if crash_point:
                crash_points.append(crash_point)
                games_data.append({
                    "game_number": i + 1,
                    "crash_point": crash_point,
                    "session_id": game_data.get("session_id")
                })
        
        # Small delay to avoid overwhelming the server
        time.sleep(0.1)
    
    if len(crash_points) < 40:  # Need at least 40 successful games
        print_result("Crash Point Generation", False, f"Only generated {len(crash_points)} crash points")
        return None
    
    # Analyze distribution
    distribution = {
        "1.01x-1.5x": 0,
        "1.5x-2.0x": 0,
        "2.0x-3.0x": 0,
        "3.0x-5.0x": 0,
        "5.0x+": 0
    }
    
    for cp in crash_points:
        if 1.01 <= cp < 1.5:
            distribution["1.01x-1.5x"] += 1
        elif 1.5 <= cp < 2.0:
            distribution["1.5x-2.0x"] += 1
        elif 2.0 <= cp < 3.0:
            distribution["2.0x-3.0x"] += 1
        elif 3.0 <= cp < 5.0:
            distribution["3.0x-5.0x"] += 1
        else:
            distribution["5.0x+"] += 1
    
    # Calculate percentages
    total_games = len(crash_points)
    distribution_pct = {k: (v / total_games) * 100 for k, v in distribution.items()}
    
    # Expected distribution for 70% house edge
    expected_distribution = {
        "1.01x-1.5x": 50.0,
        "1.5x-2.0x": 20.0,
        "2.0x-3.0x": 15.0,
        "3.0x-5.0x": 10.0,
        "5.0x+": 5.0
    }
    
    # Calculate statistics
    avg_crash_point = statistics.mean(crash_points)
    median_crash_point = statistics.median(crash_points)
    min_crash_point = min(crash_points)
    max_crash_point = max(crash_points)
    
    print_result("Crash Point Distribution Analysis", True, {
        "Total Games": total_games,
        "Average Crash Point": f"{avg_crash_point:.2f}x",
        "Median Crash Point": f"{median_crash_point:.2f}x",
        "Min Crash Point": f"{min_crash_point:.2f}x",
        "Max Crash Point": f"{max_crash_point:.2f}x"
    })
    
    print("\n📊 DISTRIBUTION ANALYSIS:")
    print(f"{'Range':<12} {'Actual':<10} {'Expected':<10} {'Variance':<10}")
    print("-" * 45)
    
    total_variance = 0
    for range_key in distribution_pct:
        actual = distribution_pct[range_key]
        expected = expected_distribution[range_key]
        variance = abs(actual - expected)
        total_variance += variance
        
        print(f"{range_key:<12} {actual:>6.1f}%   {expected:>6.1f}%    {variance:>6.1f}%")
    
    print(f"\nTotal Variance from Expected: {total_variance:.1f}%")
    
    # Determine if distribution matches intended house edge
    distribution_acceptable = total_variance <= 30.0  # Allow 30% total variance
    
    print_result("Distribution Matches 70% House Edge", distribution_acceptable, 
                f"Total variance: {total_variance:.1f}% (threshold: 30%)")
    
    return {
        "crash_points": crash_points,
        "distribution": distribution_pct,
        "expected_distribution": expected_distribution,
        "total_variance": total_variance,
        "avg_crash_point": avg_crash_point,
        "games_data": games_data
    }

def simulate_player_strategies(crash_data):
    """
    2. Player Behavior Simulation
    Simulate common player strategies using the crash points from analysis 1
    """
    print_section("2. PLAYER BEHAVIOR SIMULATION")
    
    if not crash_data:
        print_result("Player Strategy Simulation", False, "No crash data available")
        return None
    
    crash_points = crash_data["crash_points"]
    strategies = {
        "Conservative (1.5x)": 1.5,
        "Moderate (2.0x)": 2.0,
        "Aggressive (3.0x)": 3.0,
        "Very Aggressive (5.0x)": 5.0
    }
    
    results = {}
    
    print("Simulating player strategies against actual crash points...")
    
    for strategy_name, cash_out_multiplier in strategies.items():
        wins = 0
        losses = 0
        total_wagered = 0
        total_payout = 0
        wager_amount = 0.01  # Standard wager
        
        for crash_point in crash_points:
            total_wagered += wager_amount
            
            # Player wins if they cash out before crash
            if cash_out_multiplier < crash_point:
                wins += 1
                payout = wager_amount * cash_out_multiplier
                total_payout += payout
            else:
                losses += 1
                # No payout when losing
        
        total_games = len(crash_points)
        win_rate = (wins / total_games) * 100
        net_profit = total_payout - total_wagered
        roi = (net_profit / total_wagered) * 100 if total_wagered > 0 else 0
        
        results[strategy_name] = {
            "cash_out_multiplier": cash_out_multiplier,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "total_wagered": total_wagered,
            "total_payout": total_payout,
            "net_profit": net_profit,
            "roi": roi
        }
        
        print_result(f"{strategy_name} Strategy", True, {
            "Win Rate": f"{win_rate:.1f}%",
            "Wins/Losses": f"{wins}/{losses}",
            "Net Profit": f"{net_profit:.4f} SOL",
            "ROI": f"{roi:.1f}%"
        })
    
    # Identify problematic strategies (too profitable for players)
    problematic_strategies = []
    for strategy_name, data in results.items():
        if data["roi"] > 0:  # Players making profit = bad for house
            problematic_strategies.append(strategy_name)
    
    print(f"\n🚨 PROBLEMATIC STRATEGIES (Player Profitable):")
    if problematic_strategies:
        for strategy in problematic_strategies:
            roi = results[strategy]["roi"]
            print(f"   - {strategy}: {roi:.1f}% ROI")
    else:
        print("   None - All strategies lose money for players")
    
    return results

def verify_win_loss_logic():
    """
    3. Win/Loss Logic Verification
    Test the comparison logic and edge cases
    """
    print_section("3. WIN/LOSS LOGIC VERIFICATION")
    
    test_cases = [
        # (cash_out_multiplier, expected_result_if_crash_point_is_higher)
        {"cash_out": 1.5, "crash_point": 2.0, "expected": "win"},
        {"cash_out": 2.0, "crash_point": 1.5, "expected": "lose"},
        {"cash_out": 1.89, "crash_point": 1.89, "expected": "lose"},  # Edge case: equal
        {"cash_out": 3.0, "crash_point": 5.0, "expected": "win"},
        {"cash_out": 5.0, "crash_point": 3.0, "expected": "lose"},
    ]
    
    print("Testing win/loss logic with controlled scenarios...")
    
    all_tests_passed = True
    
    for i, test_case in enumerate(test_cases):
        wallet = random.choice(TEST_WALLETS)
        wager_amount = 0.01
        
        # Start game
        game_data = start_solanabust_game(wallet, wager_amount)
        if not game_data or not game_data.get("success"):
            print_result(f"Test Case {i+1}", False, "Failed to start game")
            all_tests_passed = False
            continue
        
        session_id = game_data.get("session_id")
        actual_crash_point = game_data.get("crash_point")
        
        # We need to use the actual crash point from the game
        # So we'll test the logic by comparing cash_out vs actual crash point
        cash_out_multiplier = test_case["cash_out"]
        
        # Determine expected result based on actual crash point
        if cash_out_multiplier < actual_crash_point:
            expected_result = "win"
        else:
            expected_result = "lose"
        
        # Cash out
        cash_out_data = cash_out_solanabust(session_id, cash_out_multiplier)
        if not cash_out_data:
            print_result(f"Test Case {i+1}", False, "Failed to cash out")
            all_tests_passed = False
            continue
        
        actual_result = cash_out_data.get("result")
        payout_amount = cash_out_data.get("payout_amount", 0)
        
        # Verify logic
        logic_correct = actual_result == expected_result
        
        # Verify payout logic
        if expected_result == "win":
            expected_payout = wager_amount * cash_out_multiplier
            payout_correct = abs(payout_amount - expected_payout) < 0.0001
        else:
            payout_correct = payout_amount == 0.0
        
        test_passed = logic_correct and payout_correct
        all_tests_passed = all_tests_passed and test_passed
        
        print_result(f"Test Case {i+1}", test_passed, {
            "Cash Out": f"{cash_out_multiplier}x",
            "Crash Point": f"{actual_crash_point}x",
            "Expected": expected_result,
            "Actual": actual_result,
            "Payout": f"{payout_amount:.4f} SOL",
            "Logic Correct": logic_correct,
            "Payout Correct": payout_correct
        })
        
        time.sleep(0.1)  # Small delay
    
    return all_tests_passed

def calculate_mathematical_analysis(crash_data, strategy_results):
    """
    4. Mathematical Analysis
    Calculate expected values and verify house edge
    """
    print_section("4. MATHEMATICAL ANALYSIS")
    
    if not crash_data or not strategy_results:
        print_result("Mathematical Analysis", False, "Missing required data")
        return None
    
    crash_points = crash_data["crash_points"]
    
    # Calculate theoretical expected value for each strategy
    print("Calculating theoretical vs actual player advantage...")
    
    for strategy_name, results in strategy_results.items():
        cash_out_multiplier = results["cash_out_multiplier"]
        actual_win_rate = results["win_rate"]
        actual_roi = results["roi"]
        
        # Theoretical calculation based on crash point distribution
        theoretical_win_prob = sum(1 for cp in crash_points if cash_out_multiplier < cp) / len(crash_points)
        theoretical_win_rate = theoretical_win_prob * 100
        
        # Expected value calculation
        # EV = P(win) * payout - P(lose) * wager
        # Where payout = wager * multiplier, so net gain = wager * (multiplier - 1)
        expected_value = theoretical_win_prob * (cash_out_multiplier - 1) - (1 - theoretical_win_prob) * 1
        theoretical_roi = expected_value * 100
        
        print_result(f"{strategy_name} Analysis", True, {
            "Theoretical Win Rate": f"{theoretical_win_rate:.1f}%",
            "Actual Win Rate": f"{actual_win_rate:.1f}%",
            "Theoretical ROI": f"{theoretical_roi:.1f}%",
            "Actual ROI": f"{actual_roi:.1f}%",
            "Variance": f"{abs(actual_roi - theoretical_roi):.1f}%"
        })
    
    # Overall house edge calculation
    total_house_wins = sum(1 for cp in crash_points if cp < 2.0)  # Assuming average player cashes at 2x
    house_edge_actual = (total_house_wins / len(crash_points)) * 100
    
    print_result("House Edge Analysis", True, {
        "Expected House Edge": "70%",
        "Actual House Edge": f"{house_edge_actual:.1f}%",
        "Variance": f"{abs(70 - house_edge_actual):.1f}%"
    })
    
    return {
        "house_edge_actual": house_edge_actual,
        "house_edge_expected": 70,
        "variance": abs(70 - house_edge_actual)
    }

def analyze_frontend_behavior():
    """
    5. Frontend Behavior Analysis
    Check frontend integration and timing
    """
    print_section("5. FRONTEND BEHAVIOR ANALYSIS")
    
    print("Testing frontend integration scenarios...")
    
    # Test rapid cash-outs (timing vulnerability)
    wallet = random.choice(TEST_WALLETS)
    wager_amount = 0.01
    
    game_data = start_solanabust_game(wallet, wager_amount)
    if not game_data or not game_data.get("success"):
        print_result("Frontend Integration Test", False, "Failed to start game")
        return False
    
    session_id = game_data.get("session_id")
    crash_point = game_data.get("crash_point")
    
    # Test multiple rapid cash-out attempts
    cash_out_attempts = []
    for multiplier in [1.2, 1.5, 2.0]:
        start_time = time.time()
        cash_out_data = cash_out_solanabust(session_id, multiplier)
        end_time = time.time()
        
        cash_out_attempts.append({
            "multiplier": multiplier,
            "response_time": end_time - start_time,
            "success": cash_out_data is not None and cash_out_data.get("success", False),
            "result": cash_out_data.get("result") if cash_out_data else None
        })
        
        time.sleep(0.1)
    
    # Analyze results
    successful_attempts = [a for a in cash_out_attempts if a["success"]]
    
    print_result("Rapid Cash-out Test", True, {
        "Total Attempts": len(cash_out_attempts),
        "Successful": len(successful_attempts),
        "Crash Point": f"{crash_point}x",
        "Avg Response Time": f"{statistics.mean([a['response_time'] for a in cash_out_attempts]):.3f}s"
    })
    
    # Test invalid cash-out scenarios
    invalid_tests = [
        {"multiplier": 0.5, "description": "Below minimum"},
        {"multiplier": 100.0, "description": "Extremely high"},
        {"multiplier": -1.0, "description": "Negative multiplier"}
    ]
    
    for test in invalid_tests:
        game_data = start_solanabust_game(wallet, wager_amount)
        if game_data and game_data.get("success"):
            session_id = game_data.get("session_id")
            cash_out_data = cash_out_solanabust(session_id, test["multiplier"])
            
            # Invalid requests should fail
            should_fail = test["multiplier"] <= 1.0 or test["multiplier"] > 50.0
            actually_failed = not (cash_out_data and cash_out_data.get("success"))
            
            test_passed = should_fail == actually_failed
            
            print_result(f"Invalid Input: {test['description']}", test_passed, {
                "Multiplier": test["multiplier"],
                "Should Fail": should_fail,
                "Actually Failed": actually_failed
            })
    
    return True

def main():
    """Main analysis function"""
    print("🎯 SOLANABUST ODDS PROBLEM ANALYSIS")
    print("Analyzing why players are winning too frequently...")
    print("Expected: 70% house edge (30% player win rate)")
    
    # 1. Crash Point Distribution Analysis
    crash_data = analyze_crash_point_distribution()
    
    # 2. Player Behavior Simulation
    strategy_results = simulate_player_strategies(crash_data)
    
    # 3. Win/Loss Logic Verification
    logic_test_passed = verify_win_loss_logic()
    
    # 4. Mathematical Analysis
    math_analysis = calculate_mathematical_analysis(crash_data, strategy_results)
    
    # 5. Frontend Behavior Analysis
    frontend_test_passed = analyze_frontend_behavior()
    
    # Final Summary
    print_section("FINAL ANALYSIS SUMMARY")
    
    issues_found = []
    
    if crash_data:
        variance = crash_data["total_variance"]
        if variance > 30:
            issues_found.append(f"Crash point distribution variance too high: {variance:.1f}%")
        
        avg_crash = crash_data["avg_crash_point"]
        if avg_crash > 4.0:  # Expected average should be lower for 70% house edge
            issues_found.append(f"Average crash point too high: {avg_crash:.2f}x")
    
    if strategy_results:
        profitable_strategies = [name for name, data in strategy_results.items() if data["roi"] > 0]
        if profitable_strategies:
            issues_found.append(f"Player strategies are profitable: {', '.join(profitable_strategies)}")
    
    if not logic_test_passed:
        issues_found.append("Win/loss logic has errors")
    
    if math_analysis and math_analysis["variance"] > 15:
        issues_found.append(f"House edge variance too high: {math_analysis['variance']:.1f}%")
    
    print("🔍 ISSUES IDENTIFIED:")
    if issues_found:
        for i, issue in enumerate(issues_found, 1):
            print(f"   {i}. {issue}")
    else:
        print("   No critical issues found")
    
    print("\n💡 RECOMMENDATIONS:")
    if crash_data and crash_data["total_variance"] > 30:
        print("   - Adjust crash point generation algorithm to better match expected distribution")
    
    if strategy_results:
        profitable_count = len([name for name, data in strategy_results.items() if data["roi"] > 0])
        if profitable_count > 0:
            print("   - Review crash point algorithm - too many strategies are profitable for players")
    
    if math_analysis and math_analysis["house_edge_actual"] < 60:
        print("   - House edge is below target - increase frequency of low crash points")
    
    print("\n✅ ANALYSIS COMPLETE")
    print("Review the detailed results above to identify the root cause of excessive player wins.")

if __name__ == "__main__":
    main()