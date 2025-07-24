
# Flare Network Crypto Trading Dashboard

A Flask-based cryptocurrency trading dashboard focused on the Flare Network ecosystem with AI-powered conversational trading capabilities.

## 🚀 Features

### Core Functionality
- **AI Trading Bot**: Natural language trading interface powered by conversational AI
- **Real-time Price Feeds**: Live price data from Flare FTSO oracles with CoinGecko fallback
- **Portfolio Management**: Track holdings, P&L, and performance metrics
- **Mock Trading**: Paper trading environment for testing strategies
- **WalletConnect Integration**: Connect Web3 wallets for real trading
- **Blockchain Integration**: Direct interaction with Flare Network smart contracts

### Supported Tokens
- **FLR**: Native Flare Network token
- **WFLR**: Wrapped Flare for DeFi protocols
- **ETH**: Ethereum bridged to Flare
- **MATIC**: Polygon token
- **METIS**: Metis ecosystem token
- **APE**: ApeCoin
- **USDT**: Tether stablecoin

### Trading Operations
- **Buy/Sell**: Traditional trading operations
- **Swap**: Token-to-token exchanges
- **Wrap/Unwrap**: Convert between FLR and WFLR
- **Onchain Execution**: Real smart contract interactions (beta)

## 🏗️ Architecture

### Backend Components
- **Flask Application** (`app.py`): Core web framework and database setup
- **Blockchain Service** (`blockchain_service.py`): Flare Network integration, FTSO price feeds, smart contract interactions
- **Wallet Service** (`wallet_service.py`): WalletConnect integration and session management
- **Chatbot** (`chatbot.py`): AI-powered natural language trading interface
- **Mock Data** (`mock_data.py`): Paper trading simulation engine
- **Models** (`models.py`): SQLAlchemy database models

### Frontend Components
- **Modern Dashboard** (`templates/dashboard_modern.html`): Tailwind-styled main interface
- **Trading Interface** (`templates/trading.html`): Traditional trading forms
- **Portfolio View** (`templates/portfolio.html`): Holdings and performance analytics
- **Chat Interface** (`templates/chat.html`): Conversational trading bot

### Data Flow
1. **Initialization**: Database setup with mock data population
2. **Price Updates**: FTSO oracle queries with CoinGecko fallback
3. **Trading**: Natural language commands processed by AI bot
4. **Execution**: Mock trades or real blockchain transactions
5. **Updates**: Real-time portfolio and balance synchronization

## 🛠️ Technology Stack

### Backend
- **Flask 3.0+**: Web framework
- **SQLAlchemy**: Database ORM
- **Web3.py**: Blockchain interaction
- **Requests**: HTTP client for APIs
- **Gunicorn**: WSGI server

### Frontend
- **Tailwind CSS**: Modern styling framework
- **Bootstrap 5**: UI components (legacy support)
- **Chart.js**: Data visualization
- **Font Awesome**: Icon library
- **Vanilla JavaScript**: Client-side interactions

### Blockchain
- **Flare Network**: Primary blockchain
- **FTSO v2**: Price oracle system
- **WalletConnect**: Web3 wallet integration
- **Web3 RPC**: Direct blockchain queries

## 📦 Installation

### Prerequisites
- Python 3.9+
- Git

### Setup Steps

1. **Clone Repository**
   ```bash
   git clone <your-repo-url>
   cd flare-crypto-dashboard
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Variables**
   Create a `.env` file:
   ```env
   # Required for production
   SESSION_SECRET=your-secret-key-here
   DATABASE_URL=sqlite:///crypto_dashboard.db
   
   # Optional blockchain configuration
   FLARE_RPC_URL=https://flare-api.flare.network/ext/C/rpc
   CONTRACT_REGISTRY=0xaD67FE66660Fb8dFE9d6b1b4240d8650e30F6019
   WALLETCONNECT_PROJECT_ID=your-walletconnect-project-id
   
   # External API keys (optional)
   FDC_API_KEY=your-fdc-api-key
   ```

4. **Initialize Database**
   ```bash
   python main.py
   ```

5. **Run Development Server**
   ```bash
   python main.py
   ```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SESSION_SECRET` | Flask session encryption key | Yes | `dev-secret-key-change-in-production` |
| `DATABASE_URL` | Database connection string | No | `sqlite:///crypto_dashboard.db` |
| `FLARE_RPC_URL` | Flare Network RPC endpoint | No | Official Flare RPC |
| `CONTRACT_REGISTRY` | Flare contract registry address | No | Official registry |
| `WALLETCONNECT_PROJECT_ID` | WalletConnect project ID | No | Empty (wallet features disabled) |
| `FDC_API_KEY` | Flare Data Connector API key | No | Default test key |

### Blockchain Configuration

The app supports multiple networks:
- **Flare Mainnet** (Chain ID: 14)
- **Coston2 Testnet** (Chain ID: 16)
- **Songbird** (Chain ID: 19)

## 🎯 Usage

### Trading Commands

The AI bot understands natural language commands:

**Basic Trading:**
- "Buy 100 WFLR"
- "Sell 50 ETH"
- "Swap 200 USDT for FLR"
- "Wrap 500 FLR to WFLR"

**Information Queries:**
- "What's the price of ETH?"
- "Show my portfolio"
- "What tokens can I trade?"
- "How much FLR do I have?"

**Market Analysis:**
- "Tell me about Flare Network"
- "Explain wrapped tokens"
- "What's the best token to buy?"

### Web Interface

1. **Dashboard**: Overview of portfolio and recent trades
2. **Trading**: Traditional form-based trading interface
3. **Portfolio**: Detailed holdings and performance metrics
4. **Chat**: Primary AI-powered trading interface

## 🔐 Security Features

- **Session Management**: Secure Flask sessions
- **Input Validation**: SQL injection prevention
- **Rate Limiting**: API abuse protection
- **CSRF Protection**: Cross-site request forgery prevention
- **Wallet Validation**: Address format verification
- **Transaction Signing**: Secure Web3 interactions

## 📊 API Endpoints

### Trading APIs
- `POST /api/execute_trade` - Execute mock trades
- `POST /api/execute_onchain_trade` - Execute real blockchain trades
- `GET /api/price_data/<symbol>` - Get price chart data
- `GET /api/refresh_prices` - Update live prices

### Wallet APIs
- `GET /api/wallet/config` - WalletConnect configuration
- `POST /api/wallet/connect` - Connect Web3 wallet
- `POST /api/wallet/disconnect` - Disconnect wallet
- `GET /api/wallet/status` - Wallet connection status

### Chat API
- `POST /api/chat` - Process natural language commands

## 🧪 Testing

### Mock Trading
The application includes a comprehensive mock trading system:
- Simulated order execution
- Portfolio balance updates
- Trade history tracking
- P&L calculations

### Real Trading
For live trading, ensure:
1. WalletConnect project ID configured
2. Wallet connected to Flare Network
3. Sufficient token balances
4. Network connectivity

## 🚀 Deployment

### Replit Deployment (Recommended)

1. **Prepare Environment**
   - Set production environment variables
   - Configure database for production scale
   - Update session secret

2. **Deploy**
   - Use Replit's Deploy feature
   - Select Autoscale deployment
   - Configure custom domain if needed

### Manual Deployment

1. **Production Server Setup**
   ```bash
   gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 60 main:app
   ```

2. **Database Migration**
   - Consider PostgreSQL for production
   - Set up regular backups
   - Configure connection pooling

3. **Monitoring**
   - Set up logging
   - Configure error tracking
   - Monitor blockchain connectivity

## 🔧 Troubleshooting

### Common Issues

**FTSO Price Fetch Errors:**
- Check Flare Network connectivity
- Verify contract registry address
- Falls back to CoinGecko automatically

**Wallet Connection Issues:**
- Verify WalletConnect project ID
- Check network compatibility
- Ensure Web3 wallet is installed

**Database Errors:**
- Check file permissions
- Verify database schema
- Run initialization script

### Debug Mode

Enable detailed logging:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Performance Optimization

### Caching
- Price data caching (5-minute intervals)
- Database query optimization
- Static asset caching

### Rate Limiting
- API request throttling
- Blockchain query batching
- External API usage limits

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add comprehensive tests
4. Submit pull request

### Development Guidelines
- Follow PEP 8 style guide
- Add docstrings to all functions
- Include error handling
- Test with mock data first

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Flare Network team for blockchain infrastructure
- WalletConnect for Web3 integration
- CoinGecko for price data fallback
- Bootstrap and Tailwind CSS for UI frameworks

## 📞 Support

For support and questions:
- Check the troubleshooting section
- Review error logs
- Test with mock data first
- Verify blockchain connectivity

---

**⚠️ Disclaimer**: This software is for educational and testing purposes. Always verify transactions and use appropriate risk management when trading with real funds.
