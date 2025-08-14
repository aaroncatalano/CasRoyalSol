#!/usr/bin/env python3
"""
Run the SolanaBust Crash Point Algorithm Test
"""
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the test function
from backend_test import test_solanabust_crash_point_algorithm_10_games, print_test_result

def main():
    print("🎯 RUNNING SOLANABUST CRASH POINT ALGORITHM TEST")
    print("=" * 80)
    
    # Run the test
    success, result = test_solanabust_crash_point_algorithm_10_games()
    
    # Print the result
    print_test_result("SolanaBust Crash Point Algorithm - 10 Games Test", success, result)
    
    if success:
        print("\n✅ TEST COMPLETED SUCCESSFULLY!")
        sys.exit(0)
    else:
        print("\n❌ TEST FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    main()