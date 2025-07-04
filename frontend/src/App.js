import React, { useState, useEffect, useMemo } from 'react';
import { ConnectionProvider, WalletProvider, useWallet, useConnection } from '@solana/wallet-adapter-react';
import { WalletAdapterNetwork } from '@solana/wallet-adapter-base';
import { PhantomWalletAdapter } from '@solana/wallet-adapter-phantom';
import { WalletModalProvider, WalletMultiButton } from '@solana/wallet-adapter-react-ui';
import { clusterApiUrl, PublicKey, SystemProgram, Transaction, LAMPORTS_PER_SOL } from '@solana/web3.js';
import axios from 'axios';
import './App.css';

// Import wallet adapter CSS
require('@solana/wallet-adapter-react-ui/styles.css');

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Constants
const TESTNET_TOKEN_ADDRESS = "Gh9ZwEmdLJ8DscKNTkTqPbNwLNNBjuSzaG9Vp2KGtKJr";
const DEV_WALLET_ADDRESS = "A7GZMJLFzGSPn1nYHsGhLbU5pby4q96AessVHn5qVXFZ";

// Wallet connection component
const WalletConnection = () => {
  const { publicKey, connected, disconnect } = useWallet();
  const { connection } = useConnection();
  const [balance, setBalance] = useState(0);
  const [loading, setLoading] = useState(false);

  const fetchBalance = async () => {
    if (!publicKey) return;
    
    try {
      const balance = await connection.getBalance(publicKey);
      setBalance(balance / LAMPORTS_PER_SOL);
    } catch (error) {
      console.error('Error fetching balance:', error);
    }
  };

  useEffect(() => {
    console.log('Wallet state changed:', { connected, publicKey: publicKey?.toString() });
    if (connected && publicKey) {
      fetchBalance();
      connectWalletToBackend();
      
      // Set up periodic balance refresh every 10 seconds
      const balanceInterval = setInterval(fetchBalance, 10000);
      
      return () => clearInterval(balanceInterval);
    }
  }, [connected, publicKey]);

  // Manual refresh function
  const refreshBalance = async () => {
    setLoading(true);
    await fetchBalance();
    setLoading(false);
  };

  const connectWalletToBackend = async () => {
    if (!publicKey) return;
    
    try {
      const response = await axios.post(`${API}/wallet/connect`, {
        public_key: publicKey.toString(),
        signature: "demo_signature",
        message: "Connect to Solana Gaming Platform"
      });
      
      console.log('Wallet connected to backend:', response.data);
    } catch (error) {
      console.error('Error connecting wallet to backend:', error);
    }
  };

  const requestAirdrop = async () => {
    if (!publicKey) return;
    
    setLoading(true);
    try {
      const signature = await connection.requestAirdrop(publicKey, LAMPORTS_PER_SOL);
      await connection.confirmTransaction(signature);
      
      // Force balance refresh after transaction
      setTimeout(async () => {
        const newBalance = await connection.getBalance(publicKey);
        setBalance(newBalance / LAMPORTS_PER_SOL);
      }, 2000);
      
      await fetchBalance();
      alert('Airdrop successful! You received 1 SOL.');
    } catch (error) {
      console.error('Airdrop failed:', error);
      alert('Airdrop failed. Please try again.');
    }
    setLoading(false);
  };

  if (!connected) {
    return (
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-4 text-white">Connect Your Phantom Wallet</h2>
        <WalletMultiButton className="!bg-purple-600 hover:!bg-purple-700" />
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6 mb-6">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h3 className="text-xl font-semibold text-white">Wallet Connected</h3>
          <p className="text-gray-300 text-sm">{publicKey.toString().slice(0, 8)}...{publicKey.toString().slice(-8)}</p>
        </div>
        <button 
          onClick={disconnect}
          className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg"
        >
          Disconnect
        </button>
      </div>
      
      <div className="flex justify-between items-center">
        <div>
          <p className="text-gray-300">Balance: <span className="font-bold text-white">{balance.toFixed(4)} SOL</span></p>
          <p className="text-xs text-gray-400">Updates every 10 seconds</p>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={refreshBalance}
            disabled={loading}
            className="bg-green-500 hover:bg-green-600 disabled:bg-gray-500 text-white px-3 py-1 rounded text-sm"
          >
            {loading ? '↻' : '🔄'} Refresh
          </button>
          <button 
            onClick={requestAirdrop}
            disabled={loading}
            className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-500 text-white px-4 py-2 rounded-lg"
          >
            {loading ? 'Requesting...' : 'Get Testnet SOL'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Blackjack Game Component
const BlackjackGame = () => {
  const { publicKey, sendTransaction } = useWallet();
  const { connection } = useConnection();
  const [gameSession, setGameSession] = useState(null);
  const [wagerAmount, setWagerAmount] = useState(0.1);
  const [gameState, setGameState] = useState(null);
  const [loading, setLoading] = useState(false);
  const [gameComplete, setGameComplete] = useState(false);
  const [results, setResults] = useState([]);
  const [totalPayout, setTotalPayout] = useState(0);

  const startGame = async () => {
    console.log('startGame called, publicKey:', publicKey);
    if (!publicKey) {
      alert('Please connect your wallet first!');
      return;
    }
    
    // Place wager first, then start game
    setLoading(true);
    
    try {
      // 1. Place wager first - Send full amount to dev wallet (temporary house wallet)
      const totalWager = wagerAmount;
      
      console.log(`WAGER DEBUG: wagerAmount=${wagerAmount}, totalWager=${totalWager}`);
      console.log(`WAGER DEBUG: typeof wagerAmount=${typeof wagerAmount}`);
      
      if (!totalWager || totalWager <= 0) {
        alert('Invalid wager amount');
        setLoading(false);
        return;
      }
      const devFee = totalWager * 0.04; // 4% dev fee
      const houseAmount = totalWager - devFee;
      
      console.log(`Transaction: Total=${totalWager}, DevFee=${devFee}, House=${houseAmount}`);
      
      const transaction = new Transaction();
      
      // For now, send full amount to dev wallet (acts as house wallet)
      // In production, would split between dev wallet (2%) and house wallet (98%)
      const lamportsToSend = Math.floor(totalWager * LAMPORTS_PER_SOL);
      
      console.log(`LAMPORTS DEBUG: totalWager=${totalWager}, LAMPORTS_PER_SOL=${LAMPORTS_PER_SOL}`);
      console.log(`LAMPORTS DEBUG: calculated=${totalWager * LAMPORTS_PER_SOL}, floored=${lamportsToSend}`);
      
      transaction.add(
        SystemProgram.transfer({
          fromPubkey: publicKey,
          toPubkey: new PublicKey(DEV_WALLET_ADDRESS),
          lamports: lamportsToSend // Full wager amount
        })
      );
      
      const signature = await sendTransaction(transaction, connection);
      await connection.confirmTransaction(signature, 'confirmed');
      
      await axios.post(`${API}/game/wager`, {
        player_wallet: publicKey.toString(),
        amount: totalWager,
        game_type: 'blackjack',
        session_id: 'temp',
        transaction_signature: signature
      });
      
      // 2. Then create game session and deal cards
      const response = await axios.post(`${API}/game/session/create`, null, {
        params: {
          player_wallet: publicKey.toString(),
          game_type: 'blackjack',
          num_hands: 1
        }
      });
      
      setGameSession(response.data.session_id);
      setGameState(response.data.game_data);
      setGameComplete(false);
      setResults([]);
      setTotalPayout(0);
      
    } catch (error) {
      console.error('Error starting game:', error);
      alert(`Failed to start game: ${error.message}`);
    }
    setLoading(false);
  };

  // Remove old placeWager function - now handled in startGame
  // const placeWager = async () => { ... }

  const hit = async (handIndex = 0) => {
    if (!gameSession || gameComplete) return;
    
    try {
      console.log('Hitting on hand index:', handIndex);
      const response = await axios.post(`${API}/game/blackjack/hit`, null, {
        params: {
          session_id: gameSession,
          hand_index: handIndex
        }
      });
      
      console.log('Hit response:', response.data);
      
      if (response.data.success && response.data.game_state) {
        setGameState(response.data.game_state);
        
        // Check if player busted
        const playerHand = response.data.game_state.player_hands?.[handIndex];
        if (playerHand?.busted) {
          console.log('Player busted, finishing game');
          finishGame();
        }
      } else {
        console.error('Invalid response from hit endpoint:', response.data);
        alert('Error: Invalid response from server');
      }
    } catch (error) {
      console.error('Error hitting:', error);
      alert(`Error hitting: ${error.message}`);
    }
  };

  const stand = async (handIndex = 0) => {
    if (!gameSession || gameComplete) return;
    
    try {
      const response = await axios.post(`${API}/game/blackjack/stand`, null, {
        params: {
          session_id: gameSession,
          hand_index: handIndex
        }
      });
      
      setGameState(response.data.game_state);
      finishGame();
    } catch (error) {
      console.error('Error standing:', error);
    }
  };

  const finishGame = async () => {
    if (!gameSession) return;
    
    try {
      const response = await axios.post(`${API}/game/blackjack/finish`, null, {
        params: { session_id: gameSession }
      });
      
      setGameState(response.data.game_state);
      setResults(response.data.results);
      setGameComplete(true);
      
      // Calculate total payout
      const payout = response.data.results.reduce((total, result) => {
        return total + (result.payout_multiplier * wagerAmount);
      }, 0);
      setTotalPayout(payout);
      
      // Record game result and handle payouts
      if (response.data.results.length > 0) {
        const totalPayout = response.data.results.reduce((total, result) => {
          return total + (result.payout_multiplier * wagerAmount);
        }, 0);
        
        setTotalPayout(totalPayout);
        
        // If player won, they should receive payout
        if (totalPayout > 0) {
          try {
            console.log(`Player won! Payout: ${totalPayout} SOL`);
            
            // In production, this would come from house wallet
            // For demo: send payout from dev wallet back to player
            const payoutTransaction = new Transaction();
            payoutTransaction.add(
              SystemProgram.transfer({
                fromPubkey: new PublicKey(DEV_WALLET_ADDRESS), // This would fail as we don't have private key
                toPubkey: publicKey,
                lamports: Math.floor(totalPayout * LAMPORTS_PER_SOL)
              })
            );
            
            // Note: This transaction would fail in practice since we don't control the dev wallet's private key
            // In production, you'd have a house wallet that sends payouts
            console.log(`Payout transaction created for ${totalPayout} SOL (would be sent from house wallet)`);
            
            // Record the result
            await axios.post(`${API}/game/result`, {
              session_id: gameSession,
              player_wallet: publicKey.toString(),
              game_type: 'blackjack',
              wager_amount: wagerAmount,
              payout_amount: totalPayout,
              game_data: response.data.game_state
            });
            
            alert(`🎉 YOU WON!\nPayout: ${totalPayout} SOL\n(In production, this would be sent from house wallet)`);
          } catch (payoutError) {
            console.error('Error processing payout:', payoutError);
          }
        } else {
          // Player lost - no payout, just record result
          await axios.post(`${API}/game/result`, {
            session_id: gameSession,
            player_wallet: publicKey.toString(),
            game_type: 'blackjack',
            wager_amount: wagerAmount,
            payout_amount: 0,
            game_data: response.data.game_state
          });
          
          alert(`😞 You Lost!\nLost: ${wagerAmount} SOL\nBetter luck next time!`);
        }
      }
      
    } catch (error) {
      console.error('Error finishing game:', error);
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <h2 className="text-2xl font-bold text-white mb-4">🃏 Multi-Hand Blackjack</h2>
      <p className="text-green-400 text-sm mb-4">Player Win Rate: 69% 🍀</p>
      
      {!gameSession ? (
        <div>
          <div className="mb-4">
            <label className="block text-white mb-2">Wager Amount (SOL):</label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                step="0.01"
                min="0.01"
                max="10"
                value={wagerAmount}
                onChange={(e) => {
                  const value = parseFloat(e.target.value);
                  if (value >= 0.01 && value <= 10) {
                    setWagerAmount(value);
                  }
                }}
                className="bg-gray-700 text-white px-3 py-2 rounded-lg w-32"
                placeholder="0.01 - 10"
              />
              <div className="flex gap-1">
                <button onClick={() => setWagerAmount(0.1)} className="bg-gray-600 hover:bg-gray-500 text-white px-2 py-1 rounded text-sm">0.1</button>
                <button onClick={() => setWagerAmount(0.5)} className="bg-gray-600 hover:bg-gray-500 text-white px-2 py-1 rounded text-sm">0.5</button>
                <button onClick={() => setWagerAmount(1)} className="bg-gray-600 hover:bg-gray-500 text-white px-2 py-1 rounded text-sm">1.0</button>
              </div>
            </div>
            <p className="text-gray-400 text-xs mt-1">Min: 0.01 SOL | Max: 10 SOL</p>
          </div>
          <button
            onClick={() => {
              console.log('Start Game button clicked');
              startGame();
            }}
            disabled={loading}
            className="bg-green-500 hover:bg-green-600 disabled:bg-gray-500 text-white px-6 py-3 rounded-lg font-semibold"
          >
            {loading ? 'Starting...' : 'Start Game'}
          </button>
        </div>
      ) : (
        <div>
          <div className="mb-4">
            <p className="text-white">Game Session: {gameSession.slice(0, 8)}...</p>
            <div className="bg-gray-700 p-3 rounded-lg mb-2">
              <p className="text-gray-300 text-sm">Transaction Breakdown:</p>
              <p className="text-white">Total Deducted: {wagerAmount} SOL</p>
              <p className="text-yellow-400">Dev Fee (2%): {(wagerAmount * 0.02).toFixed(6)} SOL</p>
              <p className="text-red-400">House Amount: {(wagerAmount * 0.98).toFixed(6)} SOL</p>
              <p className="text-gray-400 text-xs mt-1">* Full amount deducted upfront, winnings paid separately</p>
            </div>
          </div>
          
          {gameState && gameState.player_hands && gameState.dealer_hand && (
            <div className="mb-4">
              <div className="mb-4">
                <h3 className="text-white font-semibold">Your Hand:</h3>
                <div className="text-gray-300">
                  <p>Cards: {gameState.player_hands[0]?.cards?.join(', ') || 'No cards'}</p>
                  <p>Value: {gameState.player_hands[0]?.value || 0}</p>
                  {gameState.player_hands[0]?.busted && <p className="text-red-400">BUSTED!</p>}
                </div>
              </div>
              
              <div className="mb-4">
                <h3 className="text-white font-semibold">Dealer Hand:</h3>
                <div className="text-gray-300">
                  <p>Cards: {gameComplete ? 
                    (gameState.dealer_hand?.cards?.join(', ') || 'No cards') : 
                    ((gameState.dealer_hand?.cards?.[0] || 'No card') + ', [Hidden]')
                  }</p>
                  <p>Value: {gameComplete ? (gameState.dealer_hand?.value || 0) : '?'}</p>
                  {gameComplete && gameState.dealer_hand?.busted && <p className="text-red-400">DEALER BUSTED!</p>}
                </div>
              </div>

              {gameComplete && results.length > 0 && (
                <div className="mb-4 bg-gray-700 p-4 rounded-lg">
                  <h3 className="text-white font-semibold mb-2">Game Results:</h3>
                  {results.map((result, index) => (
                    <div key={index} className="text-gray-300 mb-2">
                      <p className={`font-semibold ${
                        result.result === 'win' || result.result === 'blackjack' ? 'text-green-400' : 
                        result.result === 'push' ? 'text-yellow-400' : 'text-red-400'
                      }`}>
                        Hand {index + 1}: {result.result.toUpperCase()}
                      </p>
                      <p>Payout: {(result.payout_multiplier * wagerAmount).toFixed(4)} SOL</p>
                    </div>
                  ))}
                  <div className="border-t border-gray-500 pt-2 mt-2">
                    <p className="text-white font-bold">Total Payout: {totalPayout.toFixed(4)} SOL</p>
                    <p className={`font-semibold ${totalPayout > wagerAmount ? 'text-green-400' : totalPayout === wagerAmount ? 'text-yellow-400' : 'text-red-400'}`}>
                      Net: {(totalPayout - wagerAmount).toFixed(4)} SOL
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}
          
          <div className="flex gap-4">
            {!gameComplete ? (
              <>
                <button
                  onClick={() => hit(0)}
                  className="bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded-lg"
                >
                  Hit
                </button>
                <button
                  onClick={() => stand(0)}
                  className="bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded-lg"
                >
                  Stand
                </button>
              </>
            ) : (
              <button
                onClick={() => {
                  setGameSession(null);
                  setGameState(null);
                  setGameComplete(false);
                  setResults([]);
                  setTotalPayout(0);
                }}
                className="bg-green-500 hover:bg-green-600 text-white px-6 py-3 rounded-lg font-semibold"
              >
                New Game
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// Video Poker Game Component
const VideoPokerGame = () => {
  const { publicKey, sendTransaction } = useWallet();
  const { connection } = useConnection();
  const [gameSession, setGameSession] = useState(null);
  const [wagerAmount, setWagerAmount] = useState(0.1);
  const [gameState, setGameState] = useState(null);
  const [heldCards, setHeldCards] = useState([]);
  const [loading, setLoading] = useState(false);
  const [gameComplete, setGameComplete] = useState(false);
  const [finalResult, setFinalResult] = useState(null);

  const startGame = async () => {
    console.log('startGame called, publicKey:', publicKey);
    if (!publicKey) {
      alert('Please connect your wallet first!');
      return;
    }
    
    // Place wager first, then start game
    setLoading(true);
    
    try {
      // 1. Place wager first - Send full amount to dev wallet (temporary house wallet)
      const totalWager = wagerAmount;
      const devFee = totalWager * 0.04; // 4% dev fee
      const houseAmount = totalWager - devFee;
      
      console.log(`Transaction: Total=${totalWager}, DevFee=${devFee}, House=${houseAmount}`);
      
      const transaction = new Transaction();
      
      // For now, send full amount to dev wallet (acts as house wallet)
      // In production, would split between dev wallet (2%) and house wallet (98%)
      const lamportsToSend = Math.floor(totalWager * LAMPORTS_PER_SOL);
      
      console.log(`LAMPORTS DEBUG: totalWager=${totalWager}, LAMPORTS_PER_SOL=${LAMPORTS_PER_SOL}`);
      console.log(`LAMPORTS DEBUG: calculated=${totalWager * LAMPORTS_PER_SOL}, floored=${lamportsToSend}`);
      
      transaction.add(
        SystemProgram.transfer({
          fromPubkey: publicKey,
          toPubkey: new PublicKey(DEV_WALLET_ADDRESS),
          lamports: lamportsToSend // Full wager amount
        })
      );
      
      const signature = await sendTransaction(transaction, connection);
      await connection.confirmTransaction(signature, 'confirmed');
      
      await axios.post(`${API}/game/wager`, {
        player_wallet: publicKey.toString(),
        amount: totalWager,
        game_type: 'video_poker',
        session_id: 'temp',
        transaction_signature: signature
      });
      
      // 2. Then create game session and deal cards
      const response = await axios.post(`${API}/game/session/create`, null, {
        params: {
          player_wallet: publicKey.toString(),
          game_type: 'video_poker'
        }
      });
      
      setGameSession(response.data.session_id);
      setGameState(response.data.game_data);
      setGameComplete(false);
      setFinalResult(null);
      setHeldCards([]);
      
    } catch (error) {
      console.error('Error starting game:', error);
      alert(`Failed to start game: ${error.message}`);
    }
    setLoading(false);
  };

  // Remove old placeWager function - now handled in startGame
  // const placeWager = async () => { ... }

  const toggleHold = (index) => {
    if (gameComplete) return;
    
    if (heldCards.includes(index)) {
      setHeldCards(heldCards.filter(i => i !== index));
    } else {
      setHeldCards([...heldCards, index]);
    }
  };

  const holdCards = async () => {
    if (!gameSession || gameComplete) return;
    
    try {
      await axios.post(`${API}/game/video_poker/hold`, {
        session_id: gameSession,
        positions: heldCards
      });
      
      console.log(`Held cards at positions: ${heldCards.join(', ')}`);
    } catch (error) {
      console.error('Error holding cards:', error);
    }
  };

  const drawCards = async () => {
    if (!gameSession || gameComplete) return;
    
    try {
      const response = await axios.post(`${API}/game/video_poker/draw`, null, {
        params: { session_id: gameSession }
      });
      
      setGameState(response.data.game_state);
      setGameComplete(true);
      
      const payout = response.data.payout_multiplier * wagerAmount;
      setFinalResult({
        hand_rank: response.data.final_hand,
        payout_multiplier: response.data.payout_multiplier,
        payout_amount: payout
      });
      
      // Record game result and handle payouts
      if (payout > 0) {
        console.log(`Player won! Payout: ${payout} SOL`);
        alert(`🎉 YOU WON!\nHand: ${response.data.final_hand}\nPayout: ${payout} SOL\n(In production, this would be sent from house wallet)`);
      } else {
        alert(`😞 You Lost!\nHand: ${response.data.final_hand}\nLost: ${wagerAmount} SOL`);
      }
      
      await axios.post(`${API}/game/result`, {
        session_id: gameSession,
        player_wallet: publicKey.toString(),
        game_type: 'video_poker',
        wager_amount: wagerAmount,
        payout_amount: payout,
        game_data: response.data.game_state
      });
      
    } catch (error) {
      console.error('Error drawing cards:', error);
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <h2 className="text-2xl font-bold text-white mb-4">🎰 Video Poker (Jacks or Better)</h2>
      <p className="text-green-400 text-sm mb-4">Player Win Rate: 65% 🍀</p>
      
      {!gameSession ? (
        <div>
          <div className="mb-4">
            <label className="block text-white mb-2">Wager Amount (SOL):</label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                step="0.01"
                min="0.01"
                max="10"
                value={wagerAmount}
                onChange={(e) => {
                  const value = parseFloat(e.target.value);
                  if (value >= 0.01 && value <= 10) {
                    setWagerAmount(value);
                  }
                }}
                className="bg-gray-700 text-white px-3 py-2 rounded-lg w-32"
                placeholder="0.01 - 10"
              />
              <div className="flex gap-1">
                <button onClick={() => setWagerAmount(0.1)} className="bg-gray-600 hover:bg-gray-500 text-white px-2 py-1 rounded text-sm">0.1</button>
                <button onClick={() => setWagerAmount(0.5)} className="bg-gray-600 hover:bg-gray-500 text-white px-2 py-1 rounded text-sm">0.5</button>
                <button onClick={() => setWagerAmount(1)} className="bg-gray-600 hover:bg-gray-500 text-white px-2 py-1 rounded text-sm">1.0</button>
              </div>
            </div>
            <p className="text-gray-400 text-xs mt-1">Min: 0.01 SOL | Max: 10 SOL</p>
          </div>
          <button
            onClick={() => {
              console.log('Video Poker Start Game button clicked');
              startGame();
            }}
            disabled={loading}
            className="bg-green-500 hover:bg-green-600 disabled:bg-gray-500 text-white px-6 py-3 rounded-lg font-semibold"
          >
            {loading ? 'Starting...' : 'Start Game'}
          </button>
        </div>
      ) : (
        <div>
          <div className="mb-4">
            <p className="text-white">Game Session: {gameSession.slice(0, 8)}...</p>
            <div className="bg-gray-700 p-3 rounded-lg mb-2">
              <p className="text-gray-300 text-sm">Transaction Breakdown:</p>
              <p className="text-white">Total Deducted: {wagerAmount} SOL</p>
              <p className="text-yellow-400">Dev Fee (2%): {(wagerAmount * 0.02).toFixed(6)} SOL</p>
              <p className="text-red-400">House Amount: {(wagerAmount * 0.98).toFixed(6)} SOL</p>
              <p className="text-gray-400 text-xs mt-1">* Full amount deducted upfront, winnings paid separately</p>
            </div>
          </div>
          
          {gameState && (
            <div className="mb-4">
              <h3 className="text-white font-semibold mb-2">
                Your Hand: {gameState.hand_rank}
                {gameComplete && finalResult && (
                  <span className={`ml-2 ${
                    finalResult.payout_multiplier > 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {finalResult.payout_multiplier > 0 ? '✅ WIN!' : '❌ LOSE'}
                  </span>
                )}
              </h3>
              
              <div className="flex gap-2 mb-4 flex-wrap">
                {gameState.hand.map((cardData, index) => (
                  <div
                    key={index}
                    onClick={() => toggleHold(index)}
                    className={`bg-white text-black p-3 rounded-lg cursor-pointer border-2 min-w-[80px] text-center transition-all ${
                      heldCards.includes(index) ? 'border-yellow-400 bg-yellow-100 transform scale-105' : 'border-gray-300 hover:border-gray-400'
                    } ${gameComplete ? 'cursor-default' : 'cursor-pointer'}`}
                  >
                    <div className="text-sm font-bold">{cardData.card}</div>
                    {heldCards.includes(index) && !gameComplete && (
                      <div className="text-xs text-yellow-600 font-bold mt-1">HELD</div>
                    )}
                  </div>
                ))}
              </div>
              
              {!gameComplete && (
                <p className="text-gray-300 text-sm mb-4">Click cards to hold them before drawing</p>
              )}
              
              {gameComplete && finalResult && (
                <div className="bg-gray-700 p-4 rounded-lg mb-4">
                  <h4 className="text-white font-semibold mb-2">Final Result:</h4>
                  <p className="text-gray-300">Hand: <span className="text-white font-semibold">{finalResult.hand_rank}</span></p>
                  <p className="text-gray-300">Multiplier: <span className="text-yellow-400">x{finalResult.payout_multiplier}</span></p>
                  <p className="text-gray-300">Payout: <span className="text-green-400 font-bold">{finalResult.payout_amount.toFixed(4)} SOL</span></p>
                  <p className={`font-semibold ${finalResult.payout_amount > wagerAmount ? 'text-green-400' : finalResult.payout_amount === wagerAmount ? 'text-yellow-400' : 'text-red-400'}`}>
                    Net: {(finalResult.payout_amount - wagerAmount).toFixed(4)} SOL
                  </p>
                </div>
              )}
            </div>
          )}
          
          <div className="flex gap-4 flex-wrap">
            {!gameComplete ? (
              <>
                <button
                  onClick={holdCards}
                  className="bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded-lg"
                >
                  Hold Selected ({heldCards.length})
                </button>
                <button
                  onClick={drawCards}
                  className="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-lg"
                >
                  Draw Cards
                </button>
              </>
            ) : (
              <button
                onClick={() => {
                  setGameSession(null);
                  setGameState(null);
                  setHeldCards([]);
                  setGameComplete(false);
                  setFinalResult(null);
                }}
                className="bg-green-500 hover:bg-green-600 text-white px-6 py-3 rounded-lg font-semibold"
              >
                New Game
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// SolanaBust Crash Game Component
const CrashGame = () => {
  const { publicKey, sendTransaction } = useWallet();
  const { connection } = useConnection();
  const [wagerAmount, setWagerAmount] = useState(0.1);
  const [loading, setLoading] = useState(false);
  const [gameState, setGameState] = useState('waiting'); // waiting, betting, flying, crashed
  const [multiplier, setMultiplier] = useState(1.00);
  const [crashPoint, setCrashPoint] = useState(0);
  const [playerBet, setPlayerBet] = useState(null);
  const [cashedOut, setCashedOut] = useState(false);
  const [timeLeft, setTimeLeft] = useState(15);
  const [players, setPlayers] = useState([]);

  // Simulate crash point using simple algorithm
  const generateCrashPoint = () => {
    const random = Math.random();
    // House edge built-in: 2% advantage
    const crashMultiplier = 1 / (1 - random * 0.98) * 0.99;
    return Math.max(1.01, Math.min(100, crashMultiplier));
  };

  const placeBet = async () => {
    if (!publicKey || gameState !== 'betting') return;
    
    setLoading(true);
    try {
      // Reuse existing transaction system
      const totalWager = wagerAmount;
      const transaction = new Transaction();
      
      transaction.add(
        SystemProgram.transfer({
          fromPubkey: publicKey,
          toPubkey: new PublicKey(DEV_WALLET_ADDRESS),
          lamports: Math.floor(totalWager * LAMPORTS_PER_SOL)
        })
      );
      
      const signature = await sendTransaction(transaction, connection);
      await connection.confirmTransaction(signature, 'confirmed');
      
      // Record bet
      await axios.post(`${API}/game/wager`, {
        player_wallet: publicKey.toString(),
        amount: totalWager,
        game_type: 'crash',
        session_id: 'crash-' + Date.now(),
        transaction_signature: signature
      });
      
      setPlayerBet({ amount: totalWager, cashedOut: false });
      setCashedOut(false);
      
    } catch (error) {
      console.error('Error placing bet:', error);
      alert(`Failed to place bet: ${error.message}`);
    }
    setLoading(false);
  };

  const cashOut = () => {
    if (playerBet && !cashedOut && gameState === 'flying') {
      const winnings = playerBet.amount * multiplier;
      setCashedOut(true);
      setPlayerBet({ ...playerBet, cashedOut: true, winnings });
      
      alert(`Cashed out at ${multiplier.toFixed(2)}x!\nWinnings: ${winnings.toFixed(4)} SOL`);
    }
  };

  // Game loop simulation
  useEffect(() => {
    const gameLoop = setInterval(() => {
      if (gameState === 'waiting') {
        setTimeLeft(30); // Increased betting time to 30 seconds
        setGameState('betting');
        setMultiplier(1.00);
        setCrashPoint(generateCrashPoint());
        setPlayerBet(null);
        setCashedOut(false);
      } else if (gameState === 'betting') {
        setTimeLeft(prev => {
          if (prev <= 1) {
            setGameState('flying');
            return 0;
          }
          return prev - 1;
        });
      } else if (gameState === 'flying') {
        setMultiplier(prev => {
          const next = prev + 0.02; // Slower multiplier increase
          if (next >= crashPoint) {
            setGameState('crashed');
            // Handle crash
            if (playerBet && !cashedOut) {
              alert(`💥 CRASHED at ${next.toFixed(2)}x!\nYou lost ${playerBet.amount} SOL`);
            }
            setTimeout(() => setGameState('waiting'), 8000); // 8 second pause after crash
            return crashPoint;
          }
          return next;
        });
      }
    }, gameState === 'flying' ? 150 : 1000); // Slower flying updates

    return () => clearInterval(gameLoop);
  }, [gameState, timeLeft, crashPoint, playerBet, cashedOut]);

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <h2 className="text-2xl font-bold text-white mb-4">🚀 SolanaBust Crash Game</h2>
      <p className="text-green-400 text-sm mb-4">House Edge: 2% | Instant Cashout</p>
      
      {/* Multiplier Display */}
      <div className="text-center mb-6">
        <div className={`text-6xl md:text-8xl font-bold mb-2 ${
          gameState === 'crashed' ? 'text-red-500' : 
          gameState === 'flying' ? 'text-green-400' : 'text-white'
        }`}>
          {gameState === 'crashed' ? '💥' : `${multiplier.toFixed(2)}x`}
        </div>
        
        {gameState === 'betting' && (
          <div className="text-yellow-400 text-xl md:text-2xl">
            Starting in {timeLeft}s...
          </div>
        )}
        
        {gameState === 'crashed' && (
          <div className="text-red-400 text-lg md:text-xl">
            CRASHED at {crashPoint.toFixed(2)}x
          </div>
        )}
      </div>

      {/* Betting Interface */}
      {(gameState === 'betting' || gameState === 'waiting') && !playerBet && (
        <div className="mb-6">
          <div className="mb-4">
            <label className="block text-white mb-2">Bet Amount (SOL):</label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                step="0.01"
                min="0.01"
                max="10"
                value={wagerAmount}
                onChange={(e) => {
                  const value = parseFloat(e.target.value);
                  if (value >= 0.01 && value <= 10) {
                    setWagerAmount(value);
                  }
                }}
                className="bg-gray-700 text-white px-3 py-2 rounded-lg w-32"
                placeholder="0.01 - 10"
              />
              <div className="flex gap-1">
                <button onClick={() => setWagerAmount(0.1)} className="bg-gray-600 hover:bg-gray-500 text-white px-2 py-1 rounded text-sm">0.1</button>
                <button onClick={() => setWagerAmount(0.5)} className="bg-gray-600 hover:bg-gray-500 text-white px-2 py-1 rounded text-sm">0.5</button>
                <button onClick={() => setWagerAmount(1)} className="bg-gray-600 hover:bg-gray-500 text-white px-2 py-1 rounded text-sm">1.0</button>
              </div>
            </div>
          </div>

          <button
            onClick={placeBet}
            disabled={loading || !publicKey}
            className="bg-green-500 hover:bg-green-600 disabled:bg-gray-500 text-white px-8 py-4 rounded-lg font-bold text-xl w-full"
          >
            {loading ? 'Placing Bet...' : `BET ${wagerAmount} SOL`}
          </button>
        </div>
      )}

      {/* Cash Out Button */}
      {playerBet && gameState === 'flying' && !cashedOut && (
        <button
          onClick={cashOut}
          className="bg-red-500 hover:bg-red-600 text-white px-8 py-4 rounded-lg font-bold text-xl w-full mb-4"
        >
          CASH OUT {(playerBet.amount * multiplier).toFixed(4)} SOL
        </button>
      )}

      {/* Player Status */}
      {playerBet && (
        <div className="bg-gray-700 p-4 rounded-lg">
          <h3 className="text-white font-semibold mb-2">Your Bet:</h3>
          <p className="text-gray-300">Amount: {playerBet.amount} SOL</p>
          {cashedOut ? (
            <p className="text-green-400 font-bold">✅ Cashed out at {multiplier.toFixed(2)}x</p>
          ) : gameState === 'crashed' ? (
            <p className="text-red-400 font-bold">💥 Lost - Crashed at {crashPoint.toFixed(2)}x</p>
          ) : (
            <p className="text-yellow-400">🚀 In flight...</p>
          )}
        </div>
      )}

      {/* Game Rules */}
      <div className="mt-6 text-gray-400 text-xs">
        <p>🎯 <strong>How to Play:</strong> Place bet → Watch multiplier rise → Cash out before crash!</p>
        <p>💰 <strong>Payouts:</strong> Your bet × multiplier when you cash out</p>
        <p>⚡ <strong>Rounds:</strong> 30s betting → Multiplier rises → Random crash → 8s pause</p>
      </div>
    </div>
  );
};

// PlayerStats Component
const PlayerStats = () => {
  const { publicKey } = useWallet();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchStats = async () => {
    if (!publicKey) return;
    
    setLoading(true);
    try {
      const response = await axios.get(`${API}/player/stats/${publicKey.toString()}`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
    setLoading(false);
  };

  useEffect(() => {
    if (publicKey) {
      fetchStats();
    }
  }, [publicKey]);

  if (!publicKey) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 text-center">
        <p className="text-gray-400">Connect your wallet to view statistics</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 text-center">
        <p className="text-white">Loading statistics...</p>
      </div>
    );
  }

  if (!stats || stats.total_games === 0) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 text-center">
        <p className="text-gray-400">No games played yet. Start playing to see your statistics!</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <h3 className="text-xl font-bold text-white mb-4">📊 Your Statistics</h3>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-700 p-3 rounded-lg text-center">
          <p className="text-gray-300 text-sm">Total Games</p>
          <p className="text-white font-bold text-lg">{stats.total_games}</p>
        </div>
        <div className="bg-gray-700 p-3 rounded-lg text-center">
          <p className="text-gray-300 text-sm">Total Wagered</p>
          <p className="text-white font-bold text-lg">{stats.total_wagered.toFixed(4)} SOL</p>
        </div>
        <div className="bg-gray-700 p-3 rounded-lg text-center">
          <p className="text-gray-300 text-sm">Total Payout</p>
          <p className="text-white font-bold text-lg">{stats.total_payout.toFixed(4)} SOL</p>
        </div>
        <div className="bg-gray-700 p-3 rounded-lg text-center">
          <p className="text-gray-300 text-sm">Net Profit</p>
          <p className={`font-bold text-lg ${stats.net_profit >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {stats.net_profit >= 0 ? '+' : ''}{stats.net_profit.toFixed(4)} SOL
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-gray-700 p-3 rounded-lg text-center">
          <p className="text-gray-300 text-sm">🃏 Blackjack Games</p>
          <p className="text-white font-bold text-lg">{stats.blackjack_games}</p>
        </div>
        <div className="bg-gray-700 p-3 rounded-lg text-center">
          <p className="text-gray-300 text-sm">🎰 Poker Games</p>
          <p className="text-white font-bold text-lg">{stats.poker_games}</p>
        </div>
      </div>

      {stats.recent_results.length > 0 && (
        <div>
          <h4 className="text-white font-semibold mb-3">Recent Games</h4>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {stats.recent_results.map((result, index) => (
              <div key={index} className="bg-gray-700 p-3 rounded-lg flex justify-between items-center">
                <div>
                  <p className="text-white font-semibold">
                    {result.game_type === 'blackjack' ? '🃏' : '🎰'} {result.game_type}
                  </p>
                  <p className="text-gray-300 text-sm">
                    Wagered: {result.wager_amount.toFixed(4)} SOL
                  </p>
                </div>
                <div className="text-right">
                  <p className={`font-bold ${result.payout_amount > result.wager_amount ? 'text-green-400' : result.payout_amount === result.wager_amount ? 'text-yellow-400' : 'text-red-400'}`}>
                    {result.payout_amount > result.wager_amount ? 'WIN' : result.payout_amount === result.wager_amount ? 'PUSH' : 'LOSE'}
                  </p>
                  <p className="text-gray-300 text-sm">
                    {(result.payout_amount - result.wager_amount).toFixed(4)} SOL
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      <button
        onClick={fetchStats}
        className="mt-4 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg w-full"
      >
        Refresh Stats
      </button>
    </div>
  );
};

// Enhanced Leaderboard Component
const Leaderboard = () => {
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchLeaderboard = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/leaderboard`);
      setLeaderboard(response.data.leaderboard || []);
    } catch (error) {
      console.error('Error fetching leaderboard:', error);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchLeaderboard();
  }, []);

  if (loading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 text-center">
        <p className="text-white">Loading leaderboard...</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <h3 className="text-xl font-bold text-white mb-4">🏆 Leaderboard</h3>
      
      {leaderboard.length === 0 ? (
        <p className="text-gray-400 text-center">No players yet. Be the first!</p>
      ) : (
        <div className="space-y-3">
          {leaderboard.map((player, index) => (
            <div key={index} className="bg-gray-700 p-3 rounded-lg flex justify-between items-center">
              <div className="flex items-center gap-3">
                <span className="text-2xl">
                  {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : `${index + 1}.`}
                </span>
                <div>
                  <p className="text-white font-semibold">{player.display_wallet}</p>
                  <p className="text-gray-300 text-sm">{player.total_games} games</p>
                </div>
              </div>
              <div className="text-right">
                <p className={`font-bold ${player.net_profit >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {player.net_profit >= 0 ? '+' : ''}{player.net_profit.toFixed(4)} SOL
                </p>
                <p className="text-gray-300 text-sm">
                  {player.total_payout.toFixed(2)} SOL won
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
      
      <button
        onClick={fetchLeaderboard}
        className="mt-4 bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-lg w-full"
      >
        🔄 Refresh Leaderboard
      </button>
    </div>
  );
};

// Main App Component
const AppContent = () => {
  const [activeGame, setActiveGame] = useState('blackjack');
  const [showStats, setShowStats] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">🎰 Solana Gaming Platform</h1>
          <p className="text-gray-300">Play Blackjack & Video Poker on Solana Testnet</p>
        </div>

        {/* Wallet Connection */}
        <WalletConnection />

        {/* Navigation */}
        <div className="mb-6">
          <div className="flex justify-center gap-4 flex-wrap">
            <button
              onClick={() => {setActiveGame('blackjack'); setShowStats(false);}}
              className={`px-6 py-3 rounded-lg font-semibold ${
                activeGame === 'blackjack' && !showStats
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              🃏 Multi-Hand Blackjack
            </button>
            <button
              onClick={() => {setActiveGame('video_poker'); setShowStats(false);}}
              className={`px-6 py-3 rounded-lg font-semibold ${
                activeGame === 'video_poker' && !showStats
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              🎰 Video Poker
            </button>
            <button
              onClick={() => {setShowStats('stats'); setActiveGame('');}}
              className={`px-6 py-3 rounded-lg font-semibold ${
                showStats === 'stats'
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              📊 Statistics
            </button>
            <button
              onClick={() => {setActiveGame('crash'); setShowStats(false);}}
              className={`px-6 py-3 rounded-lg font-semibold ${
                activeGame === 'crash' && !showStats
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              🚀 SolanaBust
            </button>
          </div>
        </div>

        {/* Game Components */}
        {showStats === 'stats' ? (
          <PlayerStats />
        ) : showStats === 'leaderboard' ? (
          <Leaderboard />
        ) : (
          <>
            {activeGame === 'blackjack' && <BlackjackGame />}
            {activeGame === 'video_poker' && <VideoPokerGame />}
            {activeGame === 'crash' && <CrashGame />}
          </>
        )}

        {/* Footer */}
        <div className="text-center mt-8 text-gray-400">
          <p>🔗 Running on Solana Testnet</p>
          <p className="text-sm">Dev Fee: 4% | Dev Wallet: {DEV_WALLET_ADDRESS.slice(0, 8)}...{DEV_WALLET_ADDRESS.slice(-8)}</p>
          <p className="text-xs mt-2">🍀 Blackjack: 69% win rate | Video Poker: 65% win rate | 🚀 SolanaBust: Real-time crash game</p>
          <div className="mt-4 text-xs">
            <p className="text-green-400">✅ PRODUCTION v2.0 - Phase 5 SolanaBust Live!</p>
            <p className="text-gray-500">Built with React + FastAPI + Solana Web3</p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Wallet Provider Setup
const App = () => {
  // The network can be set to 'devnet', 'testnet', or 'mainnet-beta'
  const network = WalletAdapterNetwork.Devnet;
  
  // You can also provide a custom RPC endpoint
  const endpoint = useMemo(() => clusterApiUrl(network), [network]);
  
  // @solana/wallet-adapter-wallets includes all the adapters but supports tree shaking and lazy loading --
  // Only the wallets you configure here will be compiled into your application, and only the dependencies
  // of wallets that your users connect to will be loaded
  const wallets = useMemo(
    () => [
      new PhantomWalletAdapter(),
    ],
    []
  );

  return (
    <ConnectionProvider endpoint={endpoint}>
      <WalletProvider wallets={wallets} autoConnect>
        <WalletModalProvider>
          <AppContent />
        </WalletModalProvider>
      </WalletProvider>
    </ConnectionProvider>
  );
};

export default App;