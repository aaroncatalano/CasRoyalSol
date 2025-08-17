#!/usr/bin/env python3
"""
SolanaBust Critical Odds Analysis - Focused Testing

This script performs targeted analysis of the SolanaBust crash game to identify
why players are winning too frequently despite the 70% house edge implementation.

Focus on:
1. Crash Point Distribution Analysis (50 games)
2. Mathematical Analysis of Expected vs Actual House Edge
3. Player Strategy Profitability Analysis
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

print(f"🎯 SolanaBust Critical Odds Analysis")
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

def analyze_crash_point_distribution():
    """
    Generate 50 crash points and analyze distribution
    """
    print_section("CRASH POINT DISTRIBUTION ANALYSIS")
    
    crash_points = []
    games_data = []
    
    print("Generating 50 crash points to analyze distribution...")
    
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
    
    print_result("Crash Point Generation", True, {
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

def simulate_player_strategies(crash_points):
    """
    Simulate common player strategies using the crash points
    """
    print_section("PLAYER STRATEGY PROFITABILITY ANALYSIS")
    
    if not crash_points:
        print_result("Player Strategy Simulation", False, "No crash data available")
        return None
    
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
        
        # Determine if strategy is problematic (profitable for players)
        is_problematic = roi > 0
        status_icon = "🚨" if is_problematic else "✅"
        
        print_result(f"{status_icon} {strategy_name} Strategy", not is_problematic, {
            "Win Rate": f"{win_rate:.1f}%",
            "Wins/Losses": f"{wins}/{losses}",
            "Net Profit": f"{net_profit:.4f} SOL",
            "ROI": f"{roi:.1f}%",
            "Status": "PROFITABLE FOR PLAYER" if is_problematic else "House Edge Working"
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
        print(f"\n⚠️  WARNING: {len(problematic_strategies)} out of {len(strategies)} strategies are profitable for players!")
    else:
        print("   None - All strategies lose money for players (House edge working correctly)")
    
    return results

def calculate_mathematical_analysis(crash_points, strategy_results):
    """
    Calculate expected values and verify house edge
    """
    print_section("MATHEMATICAL HOUSE EDGE ANALYSIS")
    
    if not crash_points or not strategy_results:
        print_result("Mathematical Analysis", False, "Missing required data")
        return None
    
    print("Calculating theoretical vs actual house edge...")
    
    # Calculate house edge for different cash-out points
    house_edge_analysis = {}
    
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
        
        # House edge = 1 - Player Expected Return
        house_edge = -theoretical_roi  # Negative ROI means house edge
        
        house_edge_analysis[strategy_name] = {
            "theoretical_win_rate": theoretical_win_rate,
            "actual_win_rate": actual_win_rate,
            "theoretical_roi": theoretical_roi,
            "actual_roi": actual_roi,
            "house_edge": house_edge
        }
        
        print_result(f"{strategy_name} Analysis", True, {
            "Theoretical Win Rate": f"{theoretical_win_rate:.1f}%",
            "Actual Win Rate": f"{actual_win_rate:.1f}%",
            "House Edge": f"{house_edge:.1f}%",
            "Player ROI": f"{actual_roi:.1f}%",
            "Variance": f"{abs(actual_roi - theoretical_roi):.1f}%"
        })
    
    # Overall house edge calculation based on average player behavior
    # Assume average player cashes out at 2.0x
    avg_cash_out = 2.0
    house_wins = sum(1 for cp in crash_points if cp < avg_cash_out)
    house_edge_actual = (house_wins / len(crash_points)) * 100
    
    print_result("Overall House Edge Analysis", True, {
        "Expected House Edge": "70%",
        "Actual House Edge": f"{house_edge_actual:.1f}%",
        "Variance": f"{abs(70 - house_edge_actual):.1f}%",
        "Assessment": "ACCEPTABLE" if abs(70 - house_edge_actual) <= 15 else "PROBLEMATIC"
    })
    
    return {
        "house_edge_actual": house_edge_actual,
        "house_edge_expected": 70,
        "variance": abs(70 - house_edge_actual),
        "strategy_analysis": house_edge_analysis
    }

def main():
    """Main analysis function"""
    print("🎯 SOLANABUST CRITICAL ODDS ANALYSIS")
    print("Analyzing why players are winning too frequently...")
    print("Expected: 70% house edge (30% player win rate)")
    
    # 1. Crash Point Distribution Analysis
    crash_data = analyze_crash_point_distribution()
    
    if not crash_data:
        print("❌ CRITICAL ERROR: Could not generate crash point data")
        return
    
    crash_points = crash_data["crash_points"]
    
    # 2. Player Strategy Profitability Analysis
    strategy_results = simulate_player_strategies(crash_points)
    
    # 3. Mathematical House Edge Analysis
    math_analysis = calculate_mathematical_analysis(crash_points, strategy_results)
    
    # Final Summary and Recommendations
    print_section("CRITICAL FINDINGS & RECOMMENDATIONS")
    
    issues_found = []
    recommendations = []
    
    # Check crash point distribution
    if crash_data["total_variance"] > 30:
        issues_found.append(f"Crash point distribution variance too high: {crash_data['total_variance']:.1f}%")
        recommendations.append("Adjust crash point generation algorithm to better match expected distribution")
    
    # Check average crash point
    avg_crash = crash_data["avg_crash_point"]
    if avg_crash > 3.0:  # Expected average should be lower for 70% house edge
        issues_found.append(f"Average crash point too high: {avg_crash:.2f}x (should be ~2.0x for 70% house edge)")
        recommendations.append("Lower the average crash point by increasing frequency of crashes in 1.01x-2.0x range")
    
    # Check player strategy profitability
    if strategy_results:
        profitable_strategies = [name for name, data in strategy_results.items() if data["roi"] > 0]
        if profitable_strategies:
            issues_found.append(f"Player strategies are profitable: {', '.join(profitable_strategies)}")
            recommendations.append("Increase crash frequency in low multiplier ranges to reduce player profitability")
    
    # Check house edge variance
    if math_analysis and math_analysis["variance"] > 15:
        issues_found.append(f"House edge variance too high: {math_analysis['variance']:.1f}%")
        recommendations.append("Fine-tune crash point algorithm to achieve target 70% house edge")
    
    print("🔍 CRITICAL ISSUES IDENTIFIED:")
    if issues_found:
        for i, issue in enumerate(issues_found, 1):
            print(f"   {i}. {issue}")
    else:
        print("   ✅ No critical issues found - house edge is working as intended")
    
    print("\n💡 RECOMMENDATIONS:")
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    else:
        print("   ✅ No changes needed - system is working correctly")
    
    # Final assessment
    critical_issues = len([issue for issue in issues_found if "profitable" in issue.lower() or "too high" in issue.lower()])
    
    if critical_issues > 0:
        print(f"\n🚨 CRITICAL ASSESSMENT: {critical_issues} critical issues found")
        print("   Players are likely winning too frequently due to the issues above")
    else:
        print("\n✅ ASSESSMENT: System appears to be working correctly")
        print("   If players are still winning too frequently, investigate frontend behavior or other factors")
    
    print("\n📊 SUMMARY STATISTICS:")
    print(f"   - Average Crash Point: {avg_crash:.2f}x")
    print(f"   - Distribution Variance: {crash_data['total_variance']:.1f}%")
    if math_analysis:
        print(f"   - Actual House Edge: {math_analysis['house_edge_actual']:.1f}%")
    if strategy_results:
        profitable_count = len([name for name, data in strategy_results.items() if data["roi"] > 0])
        print(f"   - Profitable Player Strategies: {profitable_count}/4")
    
    print("\n✅ ANALYSIS COMPLETE")

if __name__ == "__main__":
    main()