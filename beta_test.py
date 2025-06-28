#!/usr/bin/env python3
import requests
import json
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
TRANSACTION_FEE_PERCENTAGE = 0.02  # 2%

def test_complete_blackjack_flow():
    print("\n=== Testing Complete Blackjack Game Flow ===")
    
    # 1. Check wallet balance
    print("\n1. Checking wallet balance...")
    try:
        balance_response = requests.get(f"{API_URL}/wallet/balance/{TEST_WALLET_PUBLIC_KEY}")
        balance_response.raise_for_status()
        balance_data = balance_response.json()
        initial_balance = balance_data["balance_sol"]
        print(f"Initial wallet balance: {initial_balance} SOL")
    except Exception as e:
        print(f"Error checking wallet balance: {str(e)}")
        return False
    
    # 2. Connect wallet
    print("\n2. Connecting wallet...")
    try:
        wallet_response = requests.post(
            f"{API_URL}/wallet/connect",
            json={
                "public_key": TEST_WALLET_PUBLIC_KEY,
                "signature": TEST_SIGNATURE,
                "message": "Connect Wallet"
            }
        )
        wallet_response.raise_for_status()
        wallet_data = wallet_response.json()
        print(f"Wallet connection response: {wallet_data['message']}")
    except Exception as e:
        print(f"Error connecting wallet: {str(e)}")
        return False
    
    # 3. Create game session
    print("\n3. Creating blackjack game session...")
    try:
        session_response = requests.post(
            f"{API_URL}/game/session/create",
            params={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "game_type": "blackjack",
                "num_hands": 1
            }
        )
        session_response.raise_for_status()
        session_data = session_response.json()
        session_id = session_data["session_id"]
        initial_game_state = session_data["game_data"]
        print(f"Session created with ID: {session_id}")
        print(f"Initial player hand: {initial_game_state['player_hands'][0]['cards']}")
        print(f"Initial player value: {initial_game_state['player_hands'][0]['value']}")
        print(f"Initial dealer hand: {initial_game_state['dealer_hand']['cards']}")
    except Exception as e:
        print(f"Error creating game session: {str(e)}")
        return False
    
    # 4. Place wager
    print("\n4. Placing wager...")
    wager_amount = 0.1  # 0.1 SOL
    try:
        wager_response = requests.post(
            f"{API_URL}/game/wager",
            json={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "amount": wager_amount,
                "game_type": "blackjack",
                "session_id": session_id,
                "transaction_signature": TEST_SIGNATURE
            }
        )
        wager_response.raise_for_status()
        wager_data = wager_response.json()
        dev_fee = wager_data["dev_fee"]
        game_amount = wager_data["game_amount"]
        print(f"Wager placed: {wager_amount} SOL")
        print(f"Dev fee: {dev_fee} SOL")
        print(f"Game amount: {game_amount} SOL")
    except Exception as e:
        print(f"Error placing wager: {str(e)}")
        return False
    
    # 5. Hit or stand based on initial hand value
    player_hand = initial_game_state['player_hands'][0]
    player_value = player_hand['value']
    
    if player_value < 17:
        print("\n5. Player hand value is less than 17, hitting...")
        try:
            hit_response = requests.post(
                f"{API_URL}/game/blackjack/hit",
                params={
                    "session_id": session_id,
                    "hand_index": 0
                }
            )
            hit_response.raise_for_status()
            hit_data = hit_response.json()
            new_card = hit_data["new_card"]
            new_game_state = hit_data["game_state"]
            new_player_value = new_game_state["player_hands"][0]["value"]
            print(f"Hit received card: {new_card}")
            print(f"New player value: {new_player_value}")
            
            # If still under 17, hit again
            if new_player_value < 17:
                print("Player hand value is still less than 17, hitting again...")
                hit_response = requests.post(
                    f"{API_URL}/game/blackjack/hit",
                    params={
                        "session_id": session_id,
                        "hand_index": 0
                    }
                )
                hit_response.raise_for_status()
                hit_data = hit_response.json()
                new_card = hit_data["new_card"]
                new_game_state = hit_data["game_state"]
                new_player_value = new_game_state["player_hands"][0]["value"]
                print(f"Hit received card: {new_card}")
                print(f"New player value: {new_player_value}")
        except Exception as e:
            print(f"Error hitting: {str(e)}")
            return False
    else:
        print("\n5. Player hand value is 17 or higher, standing...")
    
    # 6. Stand
    print("\n6. Standing...")
    try:
        stand_response = requests.post(
            f"{API_URL}/game/blackjack/stand",
            params={
                "session_id": session_id,
                "hand_index": 0
            }
        )
        stand_response.raise_for_status()
        stand_data = stand_response.json()
        print(f"Stand response: {stand_data['message']}")
    except Exception as e:
        print(f"Error standing: {str(e)}")
        return False
    
    # 7. Finish game
    print("\n7. Finishing game...")
    try:
        finish_response = requests.post(
            f"{API_URL}/game/blackjack/finish",
            params={
                "session_id": session_id
            }
        )
        finish_response.raise_for_status()
        finish_data = finish_response.json()
        final_game_state = finish_data["game_state"]
        results = finish_data["results"]
        
        print(f"Final player hand: {final_game_state['player_hands'][0]['cards']}")
        print(f"Final player value: {final_game_state['player_hands'][0]['value']}")
        print(f"Final dealer hand: {final_game_state['dealer_hand']['cards']}")
        print(f"Final dealer value: {final_game_state['dealer_hand']['value']}")
        print(f"Game result: {results[0]['result']}")
        print(f"Payout multiplier: {results[0]['payout_multiplier']}")
    except Exception as e:
        print(f"Error finishing game: {str(e)}")
        return False
    
    # 8. Record result
    print("\n8. Recording result...")
    try:
        result = results[0]
        payout_multiplier = result["payout_multiplier"]
        payout_amount = wager_amount * payout_multiplier
        
        result_response = requests.post(
            f"{API_URL}/game/result",
            json={
                "session_id": session_id,
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "game_type": "blackjack",
                "wager_amount": wager_amount,
                "payout_amount": payout_amount,
                "game_data": final_game_state,
                "transaction_signature": TEST_SIGNATURE
            }
        )
        result_response.raise_for_status()
        result_data = result_response.json()
        print(f"Result recorded: {result_data['message']}")
        print(f"Payout amount: {payout_amount} SOL")
    except Exception as e:
        print(f"Error recording result: {str(e)}")
        return False
    
    # 9. Check player statistics
    print("\n9. Checking player statistics...")
    try:
        stats_response = requests.get(f"{API_URL}/player/stats/{TEST_WALLET_PUBLIC_KEY}")
        stats_response.raise_for_status()
        stats_data = stats_response.json()
        print(f"Total games played: {stats_data['total_games']}")
        print(f"Blackjack games: {stats_data['blackjack_games']}")
        print(f"Video poker games: {stats_data['poker_games']}")
        print(f"Total wagered: {stats_data['total_wagered']} SOL")
        print(f"Total payout: {stats_data['total_payout']} SOL")
        print(f"Net profit: {stats_data['net_profit']} SOL")
    except Exception as e:
        print(f"Error checking player statistics: {str(e)}")
        return False
    
    # 10. Check leaderboard
    print("\n10. Checking leaderboard...")
    try:
        leaderboard_response = requests.get(f"{API_URL}/leaderboard")
        leaderboard_response.raise_for_status()
        leaderboard_data = leaderboard_response.json()
        print(f"Leaderboard entries: {len(leaderboard_data['leaderboard'])}")
    except Exception as e:
        print(f"Error checking leaderboard: {str(e)}")
        return False
    
    print("\n=== Blackjack Game Flow Test Completed Successfully ===")
    return True

def test_complete_video_poker_flow():
    print("\n=== Testing Complete Video Poker Game Flow ===")
    
    # 1. Check wallet balance
    print("\n1. Checking wallet balance...")
    try:
        balance_response = requests.get(f"{API_URL}/wallet/balance/{TEST_WALLET_PUBLIC_KEY}")
        balance_response.raise_for_status()
        balance_data = balance_response.json()
        initial_balance = balance_data["balance_sol"]
        print(f"Initial wallet balance: {initial_balance} SOL")
    except Exception as e:
        print(f"Error checking wallet balance: {str(e)}")
        return False
    
    # 2. Connect wallet
    print("\n2. Connecting wallet...")
    try:
        wallet_response = requests.post(
            f"{API_URL}/wallet/connect",
            json={
                "public_key": TEST_WALLET_PUBLIC_KEY,
                "signature": TEST_SIGNATURE,
                "message": "Connect Wallet"
            }
        )
        wallet_response.raise_for_status()
        wallet_data = wallet_response.json()
        print(f"Wallet connection response: {wallet_data['message']}")
    except Exception as e:
        print(f"Error connecting wallet: {str(e)}")
        return False
    
    # 3. Create game session
    print("\n3. Creating video poker game session...")
    try:
        session_response = requests.post(
            f"{API_URL}/game/session/create",
            params={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "game_type": "video_poker"
            }
        )
        session_response.raise_for_status()
        session_data = session_response.json()
        session_id = session_data["session_id"]
        initial_game_state = session_data["game_data"]
        initial_hand = [card["card"] for card in initial_game_state["hand"]]
        initial_hand_rank = initial_game_state["hand_rank"]
        print(f"Session created with ID: {session_id}")
        print(f"Initial hand: {initial_hand}")
        print(f"Initial hand rank: {initial_hand_rank}")
    except Exception as e:
        print(f"Error creating game session: {str(e)}")
        return False
    
    # 4. Place wager
    print("\n4. Placing wager...")
    wager_amount = 0.1  # 0.1 SOL
    try:
        wager_response = requests.post(
            f"{API_URL}/game/wager",
            json={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "amount": wager_amount,
                "game_type": "video_poker",
                "session_id": session_id,
                "transaction_signature": TEST_SIGNATURE
            }
        )
        wager_response.raise_for_status()
        wager_data = wager_response.json()
        dev_fee = wager_data["dev_fee"]
        game_amount = wager_data["game_amount"]
        print(f"Wager placed: {wager_amount} SOL")
        print(f"Dev fee: {dev_fee} SOL")
        print(f"Game amount: {game_amount} SOL")
    except Exception as e:
        print(f"Error placing wager: {str(e)}")
        return False
    
    # 5. Hold cards based on initial hand
    print("\n5. Holding cards...")
    
    # Simple strategy: hold pairs, three of a kind, etc.
    ranks = {}
    for i, card_data in enumerate(initial_game_state["hand"]):
        card = card_data["card"]
        rank = card.split(" of ")[0]
        if rank not in ranks:
            ranks[rank] = []
        ranks[rank].append(i)
    
    # Hold positions for pairs or better
    hold_positions = []
    for rank, positions in ranks.items():
        if len(positions) >= 2:  # Pair or better
            hold_positions.extend(positions)
    
    # If no pairs, hold high cards (J, Q, K, A)
    if not hold_positions:
        high_cards = ["J", "Q", "K", "A"]
        for i, card_data in enumerate(initial_game_state["hand"]):
            card = card_data["card"]
            rank = card.split(" of ")[0]
            if rank in high_cards:
                hold_positions.append(i)
    
    try:
        hold_response = requests.post(
            f"{API_URL}/game/video_poker/hold",
            params={
                "session_id": session_id
            },
            json=hold_positions
        )
        hold_response.raise_for_status()
        hold_data = hold_response.json()
        print(f"Holding positions: {hold_positions}")
        print(f"Hold response: {hold_data['message']}")
    except Exception as e:
        print(f"Error holding cards: {str(e)}")
        return False
    
    # 6. Draw cards
    print("\n6. Drawing cards...")
    try:
        draw_response = requests.post(
            f"{API_URL}/game/video_poker/draw",
            params={
                "session_id": session_id
            }
        )
        draw_response.raise_for_status()
        draw_data = draw_response.json()
        final_game_state = draw_data["game_state"]
        final_hand = [card["card"] for card in final_game_state["hand"]]
        final_hand_rank = draw_data["final_hand"]
        payout_multiplier = draw_data["payout_multiplier"]
        
        print(f"Final hand: {final_hand}")
        print(f"Final hand rank: {final_hand_rank}")
        print(f"Payout multiplier: {payout_multiplier}")
        
        # Verify held cards remained the same
        held_cards_unchanged = True
        for pos in hold_positions:
            if final_game_state["hand"][pos]["card"] != initial_game_state["hand"][pos]["card"]:
                held_cards_unchanged = False
                break
        
        print(f"Held cards unchanged: {held_cards_unchanged}")
    except Exception as e:
        print(f"Error drawing cards: {str(e)}")
        return False
    
    # 7. Record result
    print("\n7. Recording result...")
    try:
        payout_amount = wager_amount * payout_multiplier
        
        result_response = requests.post(
            f"{API_URL}/game/result",
            json={
                "session_id": session_id,
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "game_type": "video_poker",
                "wager_amount": wager_amount,
                "payout_amount": payout_amount,
                "game_data": final_game_state,
                "transaction_signature": TEST_SIGNATURE
            }
        )
        result_response.raise_for_status()
        result_data = result_response.json()
        print(f"Result recorded: {result_data['message']}")
        print(f"Payout amount: {payout_amount} SOL")
    except Exception as e:
        print(f"Error recording result: {str(e)}")
        return False
    
    # 8. Check player statistics
    print("\n8. Checking player statistics...")
    try:
        stats_response = requests.get(f"{API_URL}/player/stats/{TEST_WALLET_PUBLIC_KEY}")
        stats_response.raise_for_status()
        stats_data = stats_response.json()
        print(f"Total games played: {stats_data['total_games']}")
        print(f"Blackjack games: {stats_data['blackjack_games']}")
        print(f"Video poker games: {stats_data['poker_games']}")
        print(f"Total wagered: {stats_data['total_wagered']} SOL")
        print(f"Total payout: {stats_data['total_payout']} SOL")
        print(f"Net profit: {stats_data['net_profit']} SOL")
    except Exception as e:
        print(f"Error checking player statistics: {str(e)}")
        return False
    
    print("\n=== Video Poker Game Flow Test Completed Successfully ===")
    return True

def test_error_handling():
    print("\n=== Testing Error Handling ===")
    
    # 1. Invalid game type
    print("\n1. Testing invalid game type...")
    try:
        response = requests.post(
            f"{API_URL}/game/session/create",
            params={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "game_type": "invalid_game"
            }
        )
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        if response.status_code == 400:
            print("✅ Correctly rejected invalid game type")
        else:
            print("❌ Failed to reject invalid game type")
    except Exception as e:
        print(f"Error testing invalid game type: {str(e)}")
    
    # 2. Invalid session ID
    print("\n2. Testing invalid session ID...")
    try:
        response = requests.post(
            f"{API_URL}/game/blackjack/hit",
            params={
                "session_id": "invalid_session_id",
                "hand_index": 0
            }
        )
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        if response.status_code == 404:
            print("✅ Correctly rejected invalid session ID")
        else:
            print("❌ Failed to reject invalid session ID")
    except Exception as e:
        print(f"Error testing invalid session ID: {str(e)}")
    
    # 3. Invalid wager amount (too high)
    print("\n3. Testing invalid wager amount (too high)...")
    try:
        # First create a valid session
        session_response = requests.post(
            f"{API_URL}/game/session/create",
            params={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "game_type": "blackjack"
            }
        )
        session_id = session_response.json()["session_id"]
        
        # Try to place a wager that's too high
        response = requests.post(
            f"{API_URL}/game/wager",
            json={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "amount": 100.0,  # Maximum is 10 SOL
                "game_type": "blackjack",
                "session_id": session_id,
                "transaction_signature": TEST_SIGNATURE
            }
        )
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        if response.status_code == 400:
            print("✅ Correctly rejected wager amount that's too high")
        else:
            print("❌ Failed to reject wager amount that's too high")
    except Exception as e:
        print(f"Error testing invalid wager amount: {str(e)}")
    
    # 4. Invalid wager amount (too low)
    print("\n4. Testing invalid wager amount (too low)...")
    try:
        # First create a valid session
        session_response = requests.post(
            f"{API_URL}/game/session/create",
            params={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "game_type": "blackjack"
            }
        )
        session_id = session_response.json()["session_id"]
        
        # Try to place a wager that's too low
        response = requests.post(
            f"{API_URL}/game/wager",
            json={
                "player_wallet": TEST_WALLET_PUBLIC_KEY,
                "amount": 0.001,  # Minimum is 0.01 SOL
                "game_type": "blackjack",
                "session_id": session_id,
                "transaction_signature": TEST_SIGNATURE
            }
        )
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        if response.status_code == 400:
            print("✅ Correctly rejected wager amount that's too low")
        else:
            print("❌ Failed to reject wager amount that's too low")
    except Exception as e:
        print(f"Error testing invalid wager amount: {str(e)}")
    
    print("\n=== Error Handling Tests Completed ===")
    return True

if __name__ == "__main__":
    print("\n=== COMPREHENSIVE BETA TESTING ===\n")
    
    # Run all tests
    blackjack_success = test_complete_blackjack_flow()
    video_poker_success = test_complete_video_poker_flow()
    error_handling_success = test_error_handling()
    
    # Print summary
    print("\n=== BETA TESTING SUMMARY ===")
    print(f"Blackjack Game Flow: {'✅ PASSED' if blackjack_success else '❌ FAILED'}")
    print(f"Video Poker Game Flow: {'✅ PASSED' if video_poker_success else '❌ FAILED'}")
    print(f"Error Handling: {'✅ PASSED' if error_handling_success else '❌ FAILED'}")
    
    if blackjack_success and video_poker_success and error_handling_success:
        print("\n✅ ALL TESTS PASSED - Application is ready for beta testing!")
    else:
        print("\n❌ SOME TESTS FAILED - Application needs fixes before beta testing.")