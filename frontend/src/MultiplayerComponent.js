import React, { useState, useEffect, useRef } from 'react';

const MultiplayerComponent = ({ publicKey, currentGame, onPlayerUpdate, onAnnouncementUpdate }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [playerStats, setPlayerStats] = useState({
    username: '',
    activePlayers: 0,
    totalOnline: 0
  });
  const [announcements, setAnnouncements] = useState([]);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [activePlayers, setActivePlayers] = useState([]);
  const [showChat, setShowChat] = useState(true);
  const messagesEndRef = useRef(null);
  const pollingInterval = useRef(null);

  // Get backend URL from environment
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    // Initialize Socket.IO connection
    const newSocket = io(BACKEND_URL, {
      transports: ['websocket', 'polling'],
      timeout: 20000,
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000
    });

    // Connection event handlers
    newSocket.on('connect', () => {
      console.log('✅ Connected to multiplayer server');
      setIsConnected(true);
      
      // Join current game if set
      if (currentGame) {
        newSocket.emit('join_game', { game_type: currentGame });
      }
    });

    newSocket.on('disconnect', () => {
      console.log('❌ Disconnected from multiplayer server');
      setIsConnected(false);
    });

    // Welcome message
    newSocket.on('welcome', (data) => {
      console.log('Welcome message:', data);
      setPlayerStats(prev => ({ ...prev, username: data.username }));
      addSystemMessage(`Welcome ${data.username}! You're now connected.`);
    });

    // Player count updates
    newSocket.on('player_count_update', (data) => {
      setPlayerStats(prev => ({ ...prev, totalOnline: data.count }));
      if (onPlayerUpdate) {
        onPlayerUpdate({ totalOnline: data.count });
      }
    });

    // Active players in current game
    newSocket.on('active_players_update', (data) => {
      if (data.game_type === currentGame) {
        setActivePlayers(data.players);
        setPlayerStats(prev => ({ ...prev, activePlayers: data.count }));
      }
    });

    // Chat messages
    newSocket.on('chat_message', (data) => {
      setChatMessages(prev => [...prev.slice(-49), data]); // Keep last 50 messages
      scrollToBottom();
    });

    newSocket.on('chat_history', (data) => {
      setChatMessages(data.messages || []);
      scrollToBottom();
    });

    // Game announcements
    newSocket.on('big_win_announcement', (data) => {
      console.log('🎉 Big win announcement:', data);
      setAnnouncements(prev => [data, ...prev.slice(0, 19)]); // Keep last 20
      addSystemMessage(data.message, 'big-win');
      if (onAnnouncementUpdate) {
        onAnnouncementUpdate(data);
      }
    });

    newSocket.on('cash_out_announcement', (data) => {
      console.log('💰 Cash out announcement:', data);
      setAnnouncements(prev => [data, ...prev.slice(0, 19)]);
      addSystemMessage(data.message, 'cash-out');
    });

    newSocket.on('player_bet_placed', (data) => {
      addSystemMessage(data.message, 'bet-placed');
    });

    newSocket.on('recent_announcements', (data) => {
      setAnnouncements(data.announcements || []);
    });

    setSocket(newSocket);

    return () => {
      newSocket.close();
    };
  }, [BACKEND_URL, currentGame, onPlayerUpdate, onAnnouncementUpdate]);

  // Join game when currentGame changes
  useEffect(() => {
    if (socket && isConnected && currentGame) {
      socket.emit('join_game', { game_type: currentGame });
    }
  }, [socket, isConnected, currentGame]);

  const scrollToBottom = () => {
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  const addSystemMessage = (message, type = 'info') => {
    const systemMessage = {
      username: 'System',
      message,
      timestamp: new Date().toISOString(),
      type: 'system',
      messageType: type
    };
    setChatMessages(prev => [...prev.slice(-49), systemMessage]);
    scrollToBottom();
  };

  const sendChatMessage = () => {
    if (!socket || !isConnected || !chatInput.trim()) return;
    
    socket.emit('send_chat', { message: chatInput.trim() });
    setChatInput('');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendChatMessage();
    }
  };

  // Public methods for external components
  const reportBet = (amount, gameType) => {
    if (socket && isConnected) {
      socket.emit('place_bet', {
        amount,
        game_type: gameType
      });
    }
  };

  const reportCashOut = (winnings, multiplier, gameType) => {
    if (socket && isConnected) {
      socket.emit('cash_out', {
        winnings,
        multiplier,
        game_type: gameType
      });
    }
  };

  // Expose methods to parent component
  useEffect(() => {
    if (window) {
      window.multiplayerActions = {
        reportBet,
        reportCashOut,
        addSystemMessage
      };
    }
  }, [socket, isConnected]);

  const getMessageTypeClass = (messageType) => {
    switch (messageType) {
      case 'big-win':
        return 'text-yellow-300 font-bold';
      case 'cash-out':
        return 'text-green-300';
      case 'bet-placed':
        return 'text-blue-300';
      default:
        return 'text-gray-300';
    }
  };

  const formatTimestamp = (timestamp) => {
    try {
      return new Date(timestamp).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return '';
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg p-4 h-full">
      {/* Connection Status */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-white font-semibold">Live Activity</h3>
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`}></div>
          <span className="text-sm text-gray-300">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Player Stats */}
      <div className="grid grid-cols-2 gap-2 mb-4 text-sm">
        <div className="bg-gray-700 rounded p-2 text-center">
          <div className="text-white font-bold">{playerStats.totalOnline}</div>
          <div className="text-gray-400">Players Online</div>
        </div>
        <div className="bg-gray-700 rounded p-2 text-center">
          <div className="text-white font-bold">{playerStats.activePlayers}</div>
          <div className="text-gray-400">In Game</div>
        </div>
      </div>

      {/* Username Display */}
      {playerStats.username && (
        <div className="mb-4 p-2 bg-purple-900 rounded">
          <span className="text-purple-300 text-sm">Your username: </span>
          <span className="text-white font-semibold">{playerStats.username}</span>
        </div>
      )}

      {/* Active Players List */}
      {activePlayers.length > 0 && (
        <div className="mb-4">
          <h4 className="text-white text-sm font-semibold mb-2">Active Players</h4>
          <div className="space-y-1 max-h-20 overflow-y-auto">
            {activePlayers.map((player, index) => (
              <div key={index} className="flex justify-between items-center text-xs">
                <span className="text-gray-300">{player.username}</span>
                <div className="flex items-center gap-1">
                  <span className="text-yellow-400">{player.bet_category.icon}</span>
                  <span className="text-gray-400">{player.bet_category.label}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Announcements */}
      {announcements.length > 0 && (
        <div className="mb-4">
          <h4 className="text-white text-sm font-semibold mb-2">Recent Big Wins</h4>
          <div className="space-y-1 max-h-24 overflow-y-auto">
            {announcements.slice(0, 5).map((announcement, index) => (
              <div key={index} className="text-xs text-yellow-300">
                {announcement.is_big_win && '🎉'} {announcement.message}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Chat Section */}
      <div className="border-t border-gray-600 pt-4">
        <div className="flex justify-between items-center mb-2">
          <h4 className="text-white text-sm font-semibold">Live Chat</h4>
          <button
            onClick={() => setShowChat(!showChat)}
            className="text-purple-400 text-xs hover:text-purple-300"
          >
            {showChat ? 'Hide' : 'Show'}
          </button>
        </div>

        {showChat && (
          <>
            {/* Chat Messages */}
            <div className="bg-gray-900 rounded p-2 h-32 overflow-y-auto mb-2 space-y-1">
              {chatMessages.map((msg, index) => (
                <div key={index} className="text-xs">
                  <span className="text-gray-500">{formatTimestamp(msg.timestamp)}</span>
                  {msg.type === 'system' ? (
                    <div className={`${getMessageTypeClass(msg.messageType)} ml-1`}>
                      {msg.message}
                    </div>
                  ) : (
                    <div>
                      <span className="text-purple-400 ml-1">{msg.username}:</span>
                      <span className="text-gray-300 ml-1">{msg.message}</span>
                    </div>
                  )}
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* Chat Input */}
            {publicKey && isConnected ? (
              <div className="flex gap-1">
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type a message..."
                  className="flex-1 bg-gray-700 text-white px-2 py-1 rounded text-xs"
                  maxLength={200}
                  disabled={!isConnected}
                />
                <button
                  onClick={sendChatMessage}
                  disabled={!isConnected || !chatInput.trim()}
                  className="bg-purple-600 hover:bg-purple-500 disabled:bg-gray-600 text-white px-2 py-1 rounded text-xs"
                >
                  Send
                </button>
              </div>
            ) : (
              <div className="text-gray-500 text-xs text-center">
                {!publicKey ? 'Connect wallet to chat' : 'Connecting...'}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default MultiplayerComponent;