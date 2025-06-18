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

  useEffect(() => {
    if (connected && publicKey) {
      fetchBalance();
      connectWalletToBackend();
    }
  }, [connected, publicKey]);

  const fetchBalance = async () => {
    if (!publicKey) return;
    
    try {
      const balance = await connection.getBalance(publicKey);
      setBalance(balance / LAMPORTS_PER_SOL);
    } catch (error) {
      console.error('Error fetching balance:', error);
    }
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
        </div>
        <button 
          onClick={requestAirdrop}
          disabled={loading}
          className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-500 text-white px-4 py-2 rounded-lg"
        >
          {loading ? 'Requesting...' : 'Get Testnet SOL'}
        </button>
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

  const startGame = async () => {
    if (!publicKey) return;
    
    setLoading(true);
    try {
      const response = await axios.post(`${API}/game/session/create`, null, {
        params: {
          player_wallet: publicKey.toString(),
          game_type: 'blackjack',
          num_hands: 1
        }
      });
      
      setGameSession(response.data.session_id);
      setGameState(response.data.game_data);
    } catch (error) {
      console.error('Error starting game:', error);
      alert('Failed to start game');
    }
    setLoading(false);
  };

  const placeWager = async () => {
    if (!publicKey || !gameSession) return;
    
    setLoading(true);
    try {
      // Create transaction for wager
      const transaction = new Transaction().add(
        SystemProgram.transfer({
          fromPubkey: publicKey,
          toPubkey: new PublicKey(DEV_WALLET_ADDRESS),
          lamports: wagerAmount * LAMPORTS_PER_SOL
        })
      );

      const signature = await sendTransaction(transaction, connection);
      await connection.confirmTransaction(signature);

      // Submit wager to backend
      const response = await axios.post(`${API}/game/wager`, {
        player_wallet: publicKey.toString(),
        amount: wagerAmount,
        game_type: 'blackjack',
        session_id: gameSession,
        transaction_signature: signature
      });

      alert(`Wager placed! Transaction: ${signature}`);
      console.log('Wager response:', response.data);
    } catch (error) {
      console.error('Error placing wager:', error);
      alert('Failed to place wager');
    }
    setLoading(false);
  };

  const hit = async () => {
    if (!gameSession) return;
    
    try {
      const response = await axios.post(`${API}/game/blackjack/hit`, null, {
        params: {
          session_id: gameSession,
          hand_index: 0
        }
      });
      
      alert(`You drew: ${response.data.card}`);
    } catch (error) {
      console.error('Error hitting:', error);
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <h2 className="text-2xl font-bold text-white mb-4">Multi-Hand Blackjack</h2>
      
      {!gameSession ? (
        <div>
          <div className="mb-4">
            <label className="block text-white mb-2">Wager Amount (SOL):</label>
            <input
              type="number"
              step="0.01"
              min="0.01"
              value={wagerAmount}
              onChange={(e) => setWagerAmount(parseFloat(e.target.value))}
              className="bg-gray-700 text-white px-3 py-2 rounded-lg w-32"
            />
          </div>
          <button
            onClick={startGame}
            disabled={loading || !publicKey}
            className="bg-green-500 hover:bg-green-600 disabled:bg-gray-500 text-white px-6 py-3 rounded-lg font-semibold"
          >
            {loading ? 'Starting...' : 'Start Game'}
          </button>
        </div>
      ) : (
        <div>
          <div className="mb-4">
            <p className="text-white">Game Session: {gameSession.slice(0, 8)}...</p>
            <p className="text-gray-300">Wager: {wagerAmount} SOL</p>
          </div>
          
          {gameState && (
            <div className="mb-4">
              <div className="mb-4">
                <h3 className="text-white font-semibold">Your Hand:</h3>
                <div className="text-gray-300">
                  <p>Cards: {gameState.player_hands[0].cards.join(', ')}</p>
                  <p>Value: {gameState.player_hands[0].value}</p>
                  {gameState.player_hands[0].busted && <p className="text-red-400">BUSTED!</p>}
                </div>
              </div>
              
              <div className="mb-4">
                <h3 className="text-white font-semibold">Dealer Hand:</h3>
                <div className="text-gray-300">
                  <p>Cards: {gameState.dealer_hand.cards.join(', ')}</p>
                  <p>Value: {gameState.dealer_hand.value}</p>
                  {gameState.dealer_hand.busted && <p className="text-red-400">DEALER BUSTED!</p>}
                </div>
              </div>
            </div>
          )}
          
          <div className="flex gap-4">
            <button
              onClick={placeWager}
              disabled={loading}
              className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-500 text-white px-4 py-2 rounded-lg"
            >
              {loading ? 'Processing...' : 'Place Wager'}
            </button>
            <button
              onClick={hit}
              className="bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded-lg"
            >
              Hit
            </button>
            <button
              onClick={() => {
                setGameSession(null);
                setGameState(null);
              }}
              className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg"
            >
              New Game
            </button>
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

  const startGame = async () => {
    if (!publicKey) return;
    
    setLoading(true);
    try {
      const response = await axios.post(`${API}/game/session/create`, null, {
        params: {
          player_wallet: publicKey.toString(),
          game_type: 'video_poker'
        }
      });
      
      setGameSession(response.data.session_id);
      setGameState(response.data.game_data);
      setHeldCards([]);
    } catch (error) {
      console.error('Error starting game:', error);
      alert('Failed to start game');
    }
    setLoading(false);
  };

  const placeWager = async () => {
    if (!publicKey || !gameSession) return;
    
    setLoading(true);
    try {
      const transaction = new Transaction().add(
        SystemProgram.transfer({
          fromPubkey: publicKey,
          toPubkey: new PublicKey(DEV_WALLET_ADDRESS),
          lamports: wagerAmount * LAMPORTS_PER_SOL
        })
      );

      const signature = await sendTransaction(transaction, connection);
      await connection.confirmTransaction(signature);

      const response = await axios.post(`${API}/game/wager`, {
        player_wallet: publicKey.toString(),
        amount: wagerAmount,
        game_type: 'video_poker',
        session_id: gameSession,
        transaction_signature: signature
      });

      alert(`Wager placed! Transaction: ${signature}`);
      console.log('Wager response:', response.data);
    } catch (error) {
      console.error('Error placing wager:', error);
      alert('Failed to place wager');
    }
    setLoading(false);
  };

  const toggleHold = (index) => {
    if (heldCards.includes(index)) {
      setHeldCards(heldCards.filter(i => i !== index));
    } else {
      setHeldCards([...heldCards, index]);
    }
  };

  const holdCards = async () => {
    if (!gameSession) return;
    
    try {
      await axios.post(`${API}/game/video_poker/hold`, {
        session_id: gameSession,
        positions: heldCards
      });
      
      alert(`Held cards at positions: ${heldCards.join(', ')}`);
    } catch (error) {
      console.error('Error holding cards:', error);
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <h2 className="text-2xl font-bold text-white mb-4">Video Poker (Jacks or Better)</h2>
      
      {!gameSession ? (
        <div>
          <div className="mb-4">
            <label className="block text-white mb-2">Wager Amount (SOL):</label>
            <input
              type="number"
              step="0.01"
              min="0.01"
              value={wagerAmount}
              onChange={(e) => setWagerAmount(parseFloat(e.target.value))}
              className="bg-gray-700 text-white px-3 py-2 rounded-lg w-32"
            />
          </div>
          <button
            onClick={startGame}
            disabled={loading || !publicKey}
            className="bg-green-500 hover:bg-green-600 disabled:bg-gray-500 text-white px-6 py-3 rounded-lg font-semibold"
          >
            {loading ? 'Starting...' : 'Start Game'}
          </button>
        </div>
      ) : (
        <div>
          <div className="mb-4">
            <p className="text-white">Game Session: {gameSession.slice(0, 8)}...</p>
            <p className="text-gray-300">Wager: {wagerAmount} SOL</p>
          </div>
          
          {gameState && (
            <div className="mb-4">
              <h3 className="text-white font-semibold mb-2">Your Hand: {gameState.hand_rank}</h3>
              <div className="flex gap-2 mb-4">
                {gameState.hand.map((cardData, index) => (
                  <div
                    key={index}
                    onClick={() => toggleHold(index)}
                    className={`bg-white text-black p-3 rounded-lg cursor-pointer border-2 ${
                      heldCards.includes(index) ? 'border-yellow-400 bg-yellow-100' : 'border-gray-300'
                    }`}
                  >
                    <div className="text-center">
                      <div className="text-sm font-bold">{cardData.card}</div>
                      {heldCards.includes(index) && (
                        <div className="text-xs text-yellow-600 font-bold">HELD</div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
              <p className="text-gray-300 text-sm mb-4">Click cards to hold them before drawing</p>
            </div>
          )}
          
          <div className="flex gap-4">
            <button
              onClick={placeWager}
              disabled={loading}
              className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-500 text-white px-4 py-2 rounded-lg"
            >
              {loading ? 'Processing...' : 'Place Wager'}
            </button>
            <button
              onClick={holdCards}
              className="bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded-lg"
            >
              Hold Selected Cards
            </button>
            <button
              onClick={() => {
                setGameSession(null);
                setGameState(null);
                setHeldCards([]);
              }}
              className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg"
            >
              New Game
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

// Main App Component
const AppContent = () => {
  const [activeGame, setActiveGame] = useState('blackjack');

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

        {/* Game Selection */}
        <div className="mb-6">
          <div className="flex justify-center gap-4">
            <button
              onClick={() => setActiveGame('blackjack')}
              className={`px-6 py-3 rounded-lg font-semibold ${
                activeGame === 'blackjack'
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              🃏 Multi-Hand Blackjack
            </button>
            <button
              onClick={() => setActiveGame('video_poker')}
              className={`px-6 py-3 rounded-lg font-semibold ${
                activeGame === 'video_poker'
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              🎰 Video Poker
            </button>
          </div>
        </div>

        {/* Game Components */}
        {activeGame === 'blackjack' && <BlackjackGame />}
        {activeGame === 'video_poker' && <VideoPokerGame />}

        {/* Footer */}
        <div className="text-center mt-8 text-gray-400">
          <p>🔗 Running on Solana Testnet</p>
          <p className="text-sm">Dev Fee: 2% | Dev Wallet: {DEV_WALLET_ADDRESS.slice(0, 8)}...{DEV_WALLET_ADDRESS.slice(-8)}</p>
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