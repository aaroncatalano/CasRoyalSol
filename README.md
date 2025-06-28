# 🎰 Solana Gaming Platform

A hyper-casual gaming platform featuring **Multi-Hand Blackjack** and **Video Poker** on Solana testnet with real cryptocurrency transactions.

## 🚀 Features

- **Multi-Hand Blackjack** with 69% player win rate
- **Video Poker** (Jacks or Better) with 65% player win rate  
- **Phantom Wallet Integration** for real SOL transactions
- **2% Developer Fee** on all wagers
- **Real-time Balance Updates**
- **Game Statistics & History**
- **Responsive Gaming UI**

## 🛠 Tech Stack

**Frontend:** React 19 + Solana Web3.js + Tailwind CSS  
**Backend:** FastAPI + MongoDB + Solana Python SDK  
**Blockchain:** Solana Testnet + Phantom Wallet

## 📋 Prerequisites

- **Node.js** 16+ and **Yarn**
- **Python** 3.11+ and **pip**
- **MongoDB** (local or cloud)
- **Phantom Wallet** browser extension

## ⚡ Quick Start

### 1. Clone & Install

```bash
# Frontend dependencies
cd frontend
yarn install

# Backend dependencies  
cd ../backend
pip install -r requirements.txt
```

### 2. Environment Setup

**Frontend (.env):**
```bash
REACT_APP_BACKEND_URL=http://localhost:8001
```

**Backend (.env):**
```bash
MONGO_URL=mongodb://localhost:27017
DB_NAME=solana_gaming
```

### 3. Start Services

**Backend:**
```bash
cd backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

**Frontend:**
```bash
cd frontend  
yarn start
```

**MongoDB:**
```bash
mongod --dbpath /data/db
```

## 📦 Dependencies

### Frontend Libraries
```json
{
  "@solana/web3.js": "^1.98.2",
  "@solana/wallet-adapter-react": "^0.15.39", 
  "@solana/wallet-adapter-phantom": "^0.9.28",
  "react": "^19.0.0",
  "axios": "^1.8.4",
  "tailwindcss": "^3.4.17"
}
```

### Backend Libraries
```txt
fastapi==0.110.1
uvicorn==0.25.0
solana>=0.36.7
motor==3.3.1
pymongo==4.5.0
python-dotenv>=1.0.1
```

## 🎮 Game Configuration

- **Testnet Token:** `Gh9ZwEmdLJ8DscKNTkTqPbNwLNNBjuSzaG9Vp2KGtKJr`
- **Dev Wallet:** `A7GZMJLFzGSPn1nYHsGhLbU5pby4q96AessVHn5qVXFZ`
- **Network:** Solana Devnet
- **Min Bet:** 0.01 SOL
- **Max Bet:** 10 SOL

## 🔗 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/wallet/connect` | POST | Connect Phantom wallet |
| `/api/game/session/create` | POST | Start new game |
| `/api/game/wager` | POST | Place bet with 2% fee |
| `/api/game/blackjack/hit` | POST | Hit in blackjack |
| `/api/game/video_poker/draw` | POST | Draw cards in poker |
| `/api/player/stats/{wallet}` | GET | Player statistics |

## 🏗 Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React App     │────│   FastAPI       │────│   MongoDB       │
│   (Port 3000)   │    │   (Port 8001)   │    │   (Port 27017)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                        │
         │                        │
         ▼                        ▼
┌─────────────────┐    ┌─────────────────┐
│ Phantom Wallet  │    │ Solana Testnet  │
│   Extension     │    │   Blockchain    │
└─────────────────┘    └─────────────────┘
```

## 🧪 Testing

```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests  
cd frontend
yarn test
```

## 🚀 Deployment

**Production Build:**
```bash
cd frontend
yarn build

cd ../backend  
pip install gunicorn
gunicorn server:app --host 0.0.0.0 --port 8001
```

## 🔒 Security Notes

- Uses Solana testnet (no real money)
- All transactions are on-chain and verifiable
- 2% dev fee automatically deducted
- Private keys never leave user's wallet

## 📊 Game Rules

**Blackjack:**
- Standard rules with dealer hits to 17
- Blackjack pays 2.5x
- Push returns 1x
- 69% player win rate bias

**Video Poker:**
- Jacks or Better variant
- Royal Flush pays 250x
- Jacks or Better pays 1x
- 65% player win rate bias

## 🐛 Troubleshooting

**Wallet Issues:**
- Install Phantom wallet extension
- Switch to Solana Devnet
- Get testnet SOL from faucet

**Connection Issues:**
- Check MongoDB is running
- Verify environment variables
- Ensure ports 3000, 8001, 27017 are available

## 📄 License

MIT License - Built for educational purposes on Solana testnet.

---

**⚠️ TESTNET ONLY - No real money involved**