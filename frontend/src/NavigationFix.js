// NAVIGATION COMPONENT REPLACEMENT
// Copy this into main App.js navigation section

<div className="mb-6">
  <div className="flex justify-center gap-2 flex-wrap">
    <button
      onClick={() => {setActiveGame('blackjack'); setShowStats(false);}}
      className={`px-4 py-3 rounded-lg font-semibold text-sm ${
        activeGame === 'blackjack' && !showStats
          ? 'bg-purple-600 text-white'
          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
      }`}
    >
      🃏 Blackjack
    </button>
    <button
      onClick={() => {setActiveGame('video_poker'); setShowStats(false);}}
      className={`px-4 py-3 rounded-lg font-semibold text-sm ${
        activeGame === 'video_poker' && !showStats
          ? 'bg-purple-600 text-white'
          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
      }`}
    >
      🎰 Poker
    </button>
    <button
      onClick={() => {setActiveGame('crash'); setShowStats(false);}}
      className={`px-4 py-3 rounded-lg font-semibold text-sm ${
        activeGame === 'crash' && !showStats
          ? 'bg-red-600 text-white'
          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
      }`}
    >
      🚀 SolanaBust
    </button>
    <button
      onClick={() => {setShowStats('stats'); setActiveGame('');}}
      className={`px-4 py-3 rounded-lg font-semibold text-sm ${
        showStats === 'stats'
          ? 'bg-purple-600 text-white'
          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
      }`}
    >
      📊 Stats
    </button>
    <button
      onClick={() => {setShowStats('leaderboard'); setActiveGame('');}}
      className={`px-4 py-3 rounded-lg font-semibold text-sm ${
        showStats === 'leaderboard'
          ? 'bg-purple-600 text-white'
          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
      }`}
    >
      🏆 Board
    </button>
  </div>
</div>

// GAME COMPONENTS SECTION
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