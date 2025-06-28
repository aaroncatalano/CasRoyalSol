#!/usr/bin/env python3
import requests
import json
import os
from dotenv import load_dotenv
import statistics

# Load environment variables from frontend/.env to get the backend URL
load_dotenv("frontend/.env")

# Get the backend URL from environment variables
BACKEND_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BACKEND_URL:
    print("Error: REACT_APP_BACKEND_URL not found in frontend/.env")
    exit(1)

# Ensure the URL doesn't end with a slash
if BACKEND_URL.endswith("/"):
    BACKEND_URL = BACKEND_URL[:-1]

# Add the /api prefix
API_URL = f"{BACKEND_URL}/api"

print(f"Using API URL: {API_URL}")

# Test data
TEST_WALLET_PUBLIC_KEY = "A7GZMJLFzGSPn1nYHsGhLbU5pby4q96AessVHn5qVXFZ"  # Dev wallet for testing

# Test blackjack win rate with more games
def test_blackjack_win_rate(num_games=100):
    print(f"\nTesting blackjack win rate with {num_games} games...")
    
    results = []
    
    for i in range(num_games):
        if i % 10 == 0:
            print(f"Progress: {i}/{num_games}")
            
        # Create session
        session_response = requests.post(
            f"{API_URL}/game/session/create",
            params={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "game_type": "blackjack"
            }
        )
        session_id = session_response.json()["session_id"]
        
        # Finish game immediately
        finish_response = requests.post(
            f"{API_URL}/game/blackjack/finish",
            params={
                "session_id": session_id
            }
        )
        finish_data = finish_response.json()
        
        # Record result
        result = finish_data["results"][0]["result"]
        results.append(result)
    
    # Calculate win rate
    wins = results.count("win") + results.count("blackjack")
    losses = results.count("lose")
    pushes = results.count("push")
    
    win_rate = (wins / num_games) * 100
    
    print("\nResults:")
    print(f"Total games: {num_games}")
    print(f"Wins: {wins} ({wins/num_games*100:.2f}%)")
    print(f"Losses: {losses} ({losses/num_games*100:.2f}%)")
    print(f"Pushes: {pushes} ({pushes/num_games*100:.2f}%)")
    print(f"Win rate: {win_rate:.2f}%")
    print(f"Expected win rate: 69%")
    print(f"Difference: {win_rate - 69:.2f}%")
    
    # Result distribution
    print("\nResult distribution:")
    for result_type in set(results):
        count = results.count(result_type)
        print(f"{result_type}: {count} ({count/num_games*100:.2f}%)")
    
    return results

# Run the test
results = test_blackjack_win_rate(100)