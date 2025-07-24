from app import db
from datetime import datetime
from sqlalchemy import Float, String, DateTime, Integer, Text

class Token(db.Model):
    id = db.Column(Integer, primary_key=True)
    symbol = db.Column(String(10), unique=True, nullable=False)
    name = db.Column(String(100), nullable=False)
    price = db.Column(Float, nullable=False)
    market_cap = db.Column(Float)
    volume_24h = db.Column(Float)
    change_24h = db.Column(Float)
    created_at = db.Column(DateTime, default=datetime.utcnow)

class Portfolio(db.Model):
    id = db.Column(Integer, primary_key=True)
    token_symbol = db.Column(String(10), nullable=False)
    balance = db.Column(Float, nullable=False, default=0.0)
    avg_buy_price = db.Column(Float, nullable=False, default=0.0)
    wallet_address = db.Column(String(42), nullable=True)  # Real wallet address
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Trade(db.Model):
    id = db.Column(Integer, primary_key=True)
    trade_type = db.Column(String(20), nullable=False)  # 'buy', 'sell', 'swap'
    from_token = db.Column(String(10), nullable=True)
    to_token = db.Column(String(10), nullable=False)
    amount = db.Column(Float, nullable=False)
    price = db.Column(Float, nullable=False)
    total_value = db.Column(Float, nullable=False)
    wallet_address = db.Column(String(42), nullable=True)  # Real wallet address
    tx_hash = db.Column(String(66), nullable=True)  # Blockchain transaction hash
    status = db.Column(String(20), default='completed')
    created_at = db.Column(DateTime, default=datetime.utcnow)
    metadata = db.Column(Text, nullable=True)  # JSON metadata for additional info

class ChatMessage(db.Model):
    id = db.Column(Integer, primary_key=True)
    message = db.Column(Text, nullable=False)
    response = db.Column(Text, nullable=False)
    trade_executed = db.Column(String(200))
    created_at = db.Column(DateTime, default=datetime.utcnow)