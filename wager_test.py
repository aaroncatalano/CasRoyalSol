#!/usr/bin/env python3
import requests
import json
import os
from dotenv import load_dotenv

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
TEST_SIGNATURE = "5VxYCvdJZ1XoqJVBs4ysZCQ1RbZ3ZEpgEMran6UNnQmtK9XFMpf9YYBmJiNQQJqFbsL82F8BkYJh3UtEm5EJQzXP"  # Example signature

# First create a game session
print("\nCreating a blackjack session...")
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
print(f"Session created with ID: {session_id}")

# Now try to place a wager with different amounts
wager_amounts = [0.01, 0.1, 1.0, 10.0, 100.0]

for amount in wager_amounts:
    print(f"\nTesting wager amount: {amount} SOL")
    try:
        wager_response = requests.post(
            f"{API_URL}/game/wager",
            json={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "amount": amount,
                "game_type": "blackjack",
                "session_id": session_id,
                "transaction_signature": TEST_SIGNATURE
            }
        )
        
        # Print status code and response
        print(f"Status code: {wager_response.status_code}")
        
        if wager_response.status_code == 200:
            data = wager_response.json()
            print(f"Success: {data.get('success', False)}")
            print(f"Wager ID: {data.get('wager_id', 'N/A')}")
            print(f"Total amount: {data.get('total_amount', 'N/A')}")
            print(f"Game amount: {data.get('game_amount', 'N/A')}")
            print(f"Dev fee: {data.get('dev_fee', 'N/A')}")
        else:
            print(f"Error response: {wager_response.text}")
    except Exception as e:
        print(f"Exception: {str(e)}")