
# Production Deployment Guide - Flare Crypto Dashboard

This guide provides step-by-step instructions for deploying your Flare Network crypto trading dashboard to production and mainnet.

## 🎯 Pre-Production Checklist

### 1. Security Hardening
- [ ] Generate strong session secret key
- [ ] Configure environment variables properly
- [ ] Enable HTTPS/SSL certificates
- [ ] Implement rate limiting
- [ ] Add CSRF protection
- [ ] Validate all user inputs
- [ ] Audit smart contract interactions

### 2. Environment Setup
- [ ] Production database configuration
- [ ] External API keys obtained
- [ ] WalletConnect project registered
- [ ] Flare Network mainnet RPC configured
- [ ] Monitoring and logging setup

### 3. Testing
- [ ] Full integration testing completed
- [ ] Mock trading thoroughly tested
- [ ] Real blockchain interactions verified on testnet
- [ ] Load testing performed
- [ ] Security audit completed

## 🔐 Step 1: Security Configuration

### Generate Production Secrets
```bash
# Generate a strong session secret
python -c "import secrets; print(secrets.token_hex(32))"
```

### Configure Environment Variables
Set these in Replit Secrets or environment:

```env
# Critical Production Settings
SESSION_SECRET=your-generated-secret-key-64-chars
DATABASE_URL=postgresql://user:password@host:port/database
FLASK_ENV=production
DEBUG=False

# Blockchain Configuration
FLARE_RPC_URL=https://flare-api.flare.network/ext/C/rpc
COSTON2_RPC_URL=https://coston2-api.flare.network/ext/C/rpc
CONTRACT_REGISTRY=0xaD67FE66660Fb8dFE9d6b1b4240d8650e30F6019

# WalletConnect (Required for real trading)
WALLETCONNECT_PROJECT_ID=your-walletconnect-project-id

# External APIs
COINGECKO_API_KEY=your-coingecko-pro-api-key
FDC_API_KEY=your-flare-data-connector-api-key

# Optional Performance
REDIS_URL=redis://localhost:6379/0
```

## 🗄️ Step 2: Database Migration

### Production Database Setup
```python
# Add to app.py for production database configuration
import os
from urllib.parse import urlparse

if os.environ.get('DATABASE_URL'):
    url = urlparse(os.environ['DATABASE_URL'])
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'pool_size': 10,
        'max_overflow': 20
    }
```

### Database Migration Script
```python
# Create migrate.py
from app import app, db
from models import *

def migrate_to_production():
    with app.app_context():
        # Drop all tables (WARNING: This deletes data)
        # db.drop_all()
        
        # Create all tables
        db.create_all()
        
        # Initialize with production data
        initialize_production_data()
        
        print("Database migration completed")

def initialize_production_data():
    # Add real token data for mainnet
    tokens = [
        {'symbol': 'FLR', 'name': 'Flare', 'price': 0.025, 'change_24h': 2.5},
        {'symbol': 'WFLR', 'name': 'Wrapped Flare', 'price': 0.025, 'change_24h': 2.5},
        {'symbol': 'ETH', 'name': 'Ethereum', 'price': 3500, 'change_24h': 1.2},
        {'symbol': 'USDT', 'name': 'Tether USD', 'price': 1.0, 'change_24h': 0.1},
        {'symbol': 'MATIC', 'name': 'Polygon', 'price': 0.8, 'change_24h': -1.5},
        {'symbol': 'METIS', 'name': 'Metis', 'price': 45, 'change_24h': 3.2},
        {'symbol': 'APE', 'name': 'ApeCoin', 'price': 1.2, 'change_24h': -2.1}
    ]
    
    for token_data in tokens:
        token = Token.query.filter_by(symbol=token_data['symbol']).first()
        if not token:
            token = Token(**token_data)
            db.session.add(token)
    
    db.session.commit()

if __name__ == '__main__':
    migrate_to_production()
```

## 🌐 Step 3: Mainnet Configuration

### Update Blockchain Service for Mainnet
```python
# Update blockchain_service.py mainnet configuration
class FlareBlockchainService:
    def __init__(self):
        # Production RPC URLs
        self.flare_rpc = 'https://flare-api.flare.network/ext/C/rpc'
        self.songbird_rpc = 'https://songbird-api.flare.network/ext/C/rpc'
        
        # Production contract addresses
        self.contract_registry = '0xaD67FE66660Fb8dFE9d6b1b4240d8650e30F6019'
        
        # Real token contracts on Flare mainnet
        self.token_addresses = {
            'WFLR': '0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d',
            'USDT': '0xf56e6317dC9B91F36bCDBEA4ee6c1aFd6C537e30',
            # Add other mainnet token addresses
        }
        
        # Production Web3 connection
        self.w3 = Web3(Web3.HTTPProvider(self.flare_rpc))
        
        # Enable production mode
        self.production_mode = os.environ.get('FLASK_ENV') == 'production'
```

### Real Trading Integration
```python
# Update routes.py for production trading
@app.route('/api/execute_onchain_trade', methods=['POST'])
def execute_onchain_trade():
    """Execute real onchain trades - PRODUCTION VERSION"""
    try:
        # Ensure production environment
        if not os.environ.get('FLASK_ENV') == 'production':
            return jsonify({
                'success': False,
                'message': 'Real trading only available in production'
            }), 400
        
        # Require wallet connection
        wallet_service = get_wallet_service()
        if not wallet_service.is_wallet_connected():
            return jsonify({
                'success': False,
                'message': 'Wallet connection required'
            }), 401
        
        # Additional production safety checks
        data = request.json
        amount = float(data.get('amount', 0))
        
        # Minimum trade amount check
        if amount < 0.01:
            return jsonify({
                'success': False,
                'message': 'Minimum trade amount: 0.01'
            }), 400
        
        # Maximum trade amount check (safety limit)
        if amount > 10000:
            return jsonify({
                'success': False,
                'message': 'Maximum trade amount: 10,000'
            }), 400
        
        # Execute real trade
        blockchain_service = get_blockchain_service()
        success, message = blockchain_service.execute_real_trade(
            data.get('type'),
            data.get('from_token'),
            data.get('token'),
            amount,
            wallet_service.get_connected_wallet()
        )
        
        return jsonify({
            'success': success,
            'message': message,
            'production': True
        })
        
    except Exception as e:
        logging.error(f"Production trade error: {e}")
        return jsonify({
            'success': False,
            'message': 'Trade execution failed'
        }), 500
```

## 🚀 Step 4: Replit Production Deployment

### 1. Configure Replit Secrets
Go to Replit Secrets and add all production environment variables:

```
SESSION_SECRET=your-64-char-secret
DATABASE_URL=your-production-database-url
WALLETCONNECT_PROJECT_ID=your-project-id
COINGECKO_API_KEY=your-api-key
FLASK_ENV=production
DEBUG=False
```

### 2. Update Run Configuration
```bash
# Set production run command
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 60 --access-logfile - --error-logfile - main:app
```

### 3. Deploy on Replit
1. Click the **Deploy** button in Replit
2. Choose **Autoscale** deployment
3. Configure deployment settings:
   - **Machine**: 1vCPU, 2GB RAM (minimum)
   - **Max machines**: 3-5 (based on expected traffic)
   - **Domain**: Choose your custom domain
   - **Build command**: Leave blank
   - **Run command**: `gunicorn --bind 0.0.0.0:5000 --workers 4 main:app`

### 4. Configure Custom Domain
1. In deployment settings, add your custom domain
2. Configure DNS records:
   ```
   Type: CNAME
   Name: www
   Value: your-repl-name.username.repl.co
   ```

## 📊 Step 5: Monitoring and Logging

### Production Logging Configuration
```python
# Add to app.py
import logging
from logging.handlers import RotatingFileHandler
import os

if os.environ.get('FLASK_ENV') == 'production':
    # Configure production logging
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler('logs/trading.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Trading Dashboard startup')
```

### Health Check Endpoint
```python
# Add to routes.py
@app.route('/health')
def health_check():
    """Production health check endpoint"""
    try:
        # Check database connectivity
        db.session.execute('SELECT 1')
        
        # Check blockchain connectivity
        blockchain_service = get_blockchain_service()
        connected = blockchain_service.w3.is_connected()
        
        # Check external APIs
        prices = blockchain_service._get_external_prices()
        api_status = len(prices) > 0
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'blockchain': 'connected' if connected else 'error',
            'external_apis': 'connected' if api_status else 'error',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500
```

## 🔧 Step 6: Performance Optimization

### Caching Implementation
```python
# Add Redis caching for production
import redis
from functools import wraps
import json

redis_client = redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))

def cache_prices(minutes=5):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"prices:{func.__name__}"
            
            # Try to get from cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Get fresh data
            result = func(*args, **kwargs)
            
            # Cache for specified minutes
            redis_client.setex(cache_key, minutes * 60, json.dumps(result))
            
            return result
        return wrapper
    return decorator

# Apply to price functions
@cache_prices(minutes=5)
def get_live_prices(self):
    # Existing implementation
    pass
```

### Database Connection Pooling
```python
# Update app.py for production database performance
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 300,
    'pool_pre_ping': True,
    'pool_size': 20,
    'max_overflow': 30,
    'pool_timeout': 30,
}
```

## 🔒 Step 7: Security Hardening

### Rate Limiting
```python
# Add Flask-Limiter for production
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Apply to sensitive endpoints
@app.route('/api/execute_onchain_trade', methods=['POST'])
@limiter.limit("10 per minute")
def execute_onchain_trade():
    # Existing implementation
    pass
```

### CSRF Protection
```python
# Add Flask-WTF for CSRF protection
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)

# Add CSRF token to forms
# Update templates to include {{ csrf_token() }}
```

## 📋 Step 8: Production Checklist

### Pre-Launch
- [ ] All environment variables configured
- [ ] Database migrated and tested
- [ ] SSL certificates installed
- [ ] Custom domain configured
- [ ] Monitoring setup complete
- [ ] Backup systems configured
- [ ] Load testing completed
- [ ] Security audit passed

### Post-Launch
- [ ] Monitor error logs
- [ ] Check performance metrics
- [ ] Verify blockchain connectivity
- [ ] Test all trading functions
- [ ] Monitor user feedback
- [ ] Set up automated backups
- [ ] Schedule regular maintenance

### Ongoing Maintenance
- [ ] Weekly security updates
- [ ] Monthly performance reviews
- [ ] Quarterly security audits
- [ ] Regular database maintenance
- [ ] Monitor API rate limits
- [ ] Update token contracts as needed

## 🚨 Emergency Procedures

### If Trading Issues Occur
1. Disable onchain trading immediately
2. Switch to mock trading mode
3. Investigate blockchain connectivity
4. Check smart contract status
5. Notify users of maintenance

### If Database Issues Occur
1. Enable read-only mode
2. Restore from latest backup
3. Verify data integrity
4. Gradually re-enable features

### Contact Information
- Set up monitoring alerts
- Establish incident response team
- Create communication channels
- Document emergency procedures

---

**⚠️ CRITICAL WARNINGS**

1. **Test Everything**: Never deploy directly to production without thorough testing
2. **Backup Strategy**: Implement automated daily backups
3. **Security First**: Regular security audits are essential
4. **Start Small**: Begin with limited trading amounts
5. **Monitor Closely**: Watch all systems 24/7 initially
6. **User Safety**: Implement trading limits and safety checks
7. **Legal Compliance**: Ensure compliance with local regulations

**This is financial software - any bugs can result in real financial losses. Proceed with extreme caution.**
