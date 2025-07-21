from app import db
from models import Token, Portfolio, Trade
import random
from datetime import datetime

def initialize_mock_data():
    """Initialize the database with mock token data if not already present."""
    
    # Check if tokens already exist
    if Token.query.count() > 0:
        return
    
    # Flare Network and supported tokens
    mock_tokens = [
        {'symbol': 'WFLR', 'name': 'Wrapped Flare', 'price': 0.0342, 'market_cap': 1500000000, 'volume_24h': 25000000, 'change_24h': 2.45},
        {'symbol': 'FLR', 'name': 'Flare', 'price': 0.0338, 'market_cap': 1480000000, 'volume_24h': 30000000, 'change_24h': 1.82},
        {'symbol': 'MATIC', 'name': 'Polygon', 'price': 0.8945, 'market_cap': 8500000000, 'volume_24h': 450000000, 'change_24h': -1.23},
        {'symbol': 'METIS', 'name': 'Metis', 'price': 45.67, 'market_cap': 320000000, 'volume_24h': 15000000, 'change_24h': 3.89},
        {'symbol': 'USDT', 'name': 'Tether USD', 'price': 1.0001, 'market_cap': 95000000000, 'volume_24h': 28000000000, 'change_24h': 0.01},
        {'symbol': 'ETH', 'name': 'Ethereum', 'price': 3245.78, 'market_cap': 390000000000, 'volume_24h': 15000000000, 'change_24h': 0.95},
        {'symbol': 'APE', 'name': 'ApeCoin', 'price': 1.234, 'market_cap': 780000000, 'volume_24h': 95000000, 'change_24h': -2.67}
    ]
    
    for token_data in mock_tokens:
        token = Token(**token_data)
        db.session.add(token)
    
    # Initialize portfolio with some mock holdings
    mock_portfolio = [
        {'token_symbol': 'WFLR', 'balance': 5000.0, 'avg_buy_price': 0.0320},
        {'token_symbol': 'ETH', 'balance': 2.5, 'avg_buy_price': 3100.00},
        {'token_symbol': 'MATIC', 'balance': 1500.0, 'avg_buy_price': 0.8200},
        {'token_symbol': 'USDT', 'balance': 1000.0, 'avg_buy_price': 1.0000}
    ]
    
    for portfolio_data in mock_portfolio:
        portfolio_item = Portfolio(**portfolio_data)
        db.session.add(portfolio_item)
    
    # Add some mock trade history
    mock_trades = [
        {'trade_type': 'buy', 'to_token': 'WFLR', 'amount': 1000.0, 'price': 0.0340, 'total_value': 34.0, 'created_at': datetime.now()},
        {'trade_type': 'swap', 'from_token': 'USDT', 'to_token': 'ETH', 'amount': 0.5, 'price': 3200.0, 'total_value': 1600.0},
        {'trade_type': 'sell', 'from_token': 'MATIC', 'to_token': 'MATIC', 'amount': 500.0, 'price': 0.8800, 'total_value': 440.0}
    ]
    
    for trade_data in mock_trades:
        trade = Trade(**trade_data)
        db.session.add(trade)
    
    db.session.commit()

def get_current_prices():
    """Update token prices with realistic fluctuations."""
    tokens = Token.query.all()
    
    for token in tokens:
        # Simulate price movement (±5% random change)
        change_percent = random.uniform(-5.0, 5.0)
        new_price = token.price * (1 + change_percent / 100)
        
        # Ensure USDT stays close to $1
        if token.symbol == 'USDT':
            new_price = random.uniform(0.9990, 1.0010)
            change_percent = ((new_price - 1.0) / 1.0) * 100
        
        token.price = round(new_price, 6)
        token.change_24h = round(change_percent, 2)
        
        # Update volume with some randomness
        token.volume_24h = token.volume_24h * random.uniform(0.8, 1.2)
    
    db.session.commit()

def execute_mock_trade(trade_type, token_symbol, amount, from_token=None):
    """Execute a mock trade and update portfolio."""
    try:
        token = Token.query.filter_by(symbol=token_symbol.upper()).first()
        if not token:
            return {'success': False, 'message': f'Token {token_symbol} not found'}
        
        if amount <= 0:
            return {'success': False, 'message': 'Amount must be greater than 0'}
        
        # Get or create portfolio entry
        portfolio_entry = Portfolio.query.filter_by(token_symbol=token_symbol.upper()).first()
        if not portfolio_entry:
            portfolio_entry = Portfolio(token_symbol=token_symbol.upper(), balance=0.0, avg_buy_price=0.0)
            db.session.add(portfolio_entry)
        
        trade_value = amount * token.price
        
        if trade_type == 'buy':
            # Update portfolio balance and average price
            total_cost = (portfolio_entry.balance * portfolio_entry.avg_buy_price) + trade_value
            new_balance = portfolio_entry.balance + amount
            portfolio_entry.avg_buy_price = total_cost / new_balance if new_balance > 0 else token.price
            portfolio_entry.balance = new_balance
            
            message = f'Successfully bought {amount} {token_symbol.upper()} for ${trade_value:.2f}'
            
        elif trade_type == 'sell':
            if portfolio_entry.balance < amount:
                return {'success': False, 'message': f'Insufficient {token_symbol.upper()} balance'}
            
            portfolio_entry.balance -= amount
            message = f'Successfully sold {amount} {token_symbol.upper()} for ${trade_value:.2f}'
            
        elif trade_type == 'swap':
            if not from_token:
                return {'success': False, 'message': 'From token required for swap'}
            
            from_portfolio = Portfolio.query.filter_by(token_symbol=from_token.upper()).first()
            if not from_portfolio or from_portfolio.balance < amount:
                return {'success': False, 'message': f'Insufficient {from_token.upper()} balance'}
            
            # Remove from source token
            from_portfolio.balance -= amount
            
            # Calculate swap amount based on prices
            from_token_obj = Token.query.filter_by(symbol=from_token.upper()).first()
            swap_value = amount * from_token_obj.price
            to_amount = swap_value / token.price
            
            # Add to destination token
            total_cost = (portfolio_entry.balance * portfolio_entry.avg_buy_price) + swap_value
            new_balance = portfolio_entry.balance + to_amount
            portfolio_entry.avg_buy_price = total_cost / new_balance if new_balance > 0 else token.price
            portfolio_entry.balance = new_balance
            
            message = f'Successfully swapped {amount} {from_token.upper()} for {to_amount:.6f} {token_symbol.upper()}'
            amount = to_amount  # For trade record
        
        # Record the trade
        trade = Trade(
            trade_type=trade_type,
            from_token=from_token.upper() if from_token else None,
            to_token=token_symbol.upper(),
            amount=amount,
            price=token.price,
            total_value=trade_value
        )
        db.session.add(trade)
        db.session.commit()
        
        return {
            'success': True, 
            'message': message,
            'trade': {
                'type': trade_type,
                'token': token_symbol.upper(),
                'amount': amount,
                'price': token.price,
                'total_value': trade_value
            }
        }
        
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'Trade failed: {str(e)}'}
