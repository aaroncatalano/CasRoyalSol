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

  // Generate a random username for the user
  const generateUsername = () => {
    const adjectives = ['Lucky', 'Crypto', 'Solana', 'Diamond', 'Golden', 'Silver', 'Rocket', 'Moon'];
    const nouns = ['Trader', 'Whale', 'Bull', 'Bear', 'Hodler', 'Ape', 'Wolf', 'Lion'];
    const adjective = adjectives[Math.floor(Math.random() * adjectives.length)];
    const noun = nouns[Math.floor(Math.random() * nouns.length)];
    const number = Math.floor(Math.random() * 900) + 100;
    return `${adjective}${noun}${number}`;
  };

  const [username] = useState(() => generateUsername());

  useEffect(() => {
    // Start polling for multiplayer data
    const pollMultiplayerData = async () => {
      try {
        // Fetch multiplayer status
        const statusResponse = await fetch(`${BACKEND_URL}/api/multiplayer/status`);
        if (statusResponse.ok) {
          const statusData = await statusResponse.json();
          setIsConnected(statusData.connected);
          setPlayerStats({
            username,
            activePlayers: statusData.active_players.length,
            totalOnline: statusData.total_online
          });
          setActivePlayers(statusData.active_players);
          
          if (onPlayerUpdate) {
            onPlayerUpdate({ totalOnline: statusData.total_online });
          }
        }

        // Fetch chat messages
        const chatResponse = await fetch(`${BACKEND_URL}/api/multiplayer/chat/messages?limit=20`);
        if (chatResponse.ok) {
          const chatData = await chatResponse.json();
          const newMessages = chatData.messages || [];
          
          // Only scroll if there are new messages
          const hasNewMessages = newMessages.length > chatMessages.length || 
            (newMessages.length > 0 && chatMessages.length > 0 && 
             newMessages[newMessages.length - 1].id !== chatMessages[chatMessages.length - 1]?.id);
          
          setChatMessages(newMessages);
          
          // Only scroll to bottom if there are actually new messages
          if (hasNewMessages && showChat) {
            scrollToBottom();
          }
        }

        // Fetch announcements
        const announcementsResponse = await fetch(`${BACKEND_URL}/api/multiplayer/announcements?limit=10`);
        if (announcementsResponse.ok) {
          const announcementsData = await announcementsResponse.json();
          setAnnouncements(announcementsData.announcements || []);
        }

      } catch (error) {
        console.error('Error polling multiplayer data:', error);
        setIsConnected(false);
      }
    };

    // Initial fetch
    pollMultiplayerData();

    // Set up polling interval (every 3 seconds)
    pollingInterval.current = setInterval(pollMultiplayerData, 3000);

    return () => {
      if (pollingInterval.current) {
        clearInterval(pollingInterval.current);
      }
    };
  }, [BACKEND_URL, username, onPlayerUpdate, chatMessages.length, showChat]);

  const scrollToBottom = () => {
    // Only scroll the chat container, not the entire page
    setTimeout(() => {
      if (messagesEndRef.current && showChat) {
        messagesEndRef.current.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'nearest',
          inline: 'nearest'
        });
      }
    }, 100);
  };

  const sendChatMessage = async () => {
    if (!publicKey || !isConnected || !chatInput.trim()) return;
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/multiplayer/chat/send`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username,
          message: chatInput.trim()
        })
      });

      if (response.ok) {
        setChatInput('');
        // Message will appear in next poll cycle
      }
    } catch (error) {
      console.error('Error sending chat message:', error);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendChatMessage();
    }
  };

  // Public methods for external components
  const reportBet = (amount, gameType) => {
    console.log(`Reported bet: ${amount} SOL in ${gameType}`);
    // In a real implementation, this would send the bet info to the server
  };

  const reportCashOut = (winnings, multiplier, gameType) => {
    console.log(`Reported cash out: ${winnings} SOL at ${multiplier}x in ${gameType}`);
    // In a real implementation, this would send the cash out info to the server
  };

  // Expose methods to parent component
  useEffect(() => {
    if (window) {
      window.multiplayerActions = {
        reportBet,
        reportCashOut
      };
    }
  }, []);

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
            {activePlayers.slice(0, 5).map((player, index) => (
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
            {announcements.slice(0, 3).map((announcement, index) => (
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
                  <div>
                    <span className="text-purple-400 ml-1">{msg.username}:</span>
                    <span className="text-gray-300 ml-1">{msg.message}</span>
                  </div>
                </div>
              ))}
              {chatMessages.length === 0 && (
                <div className="text-gray-500 text-center text-xs">No messages yet. Be the first to chat!</div>
              )}
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