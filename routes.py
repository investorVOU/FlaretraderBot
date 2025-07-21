from flask import render_template, request, jsonify, flash, redirect, url_for
from app import app, db
from models import Token, Portfolio, Trade, ChatMessage
from mock_data import initialize_mock_data, get_current_prices, execute_mock_trade
from chatbot import process_chat_message
import json
from datetime import datetime, timedelta

@app.route('/')
def dashboard():
    initialize_mock_data()
    tokens = Token.query.all()
    portfolio = Portfolio.query.all()
    recent_trades = Trade.query.order_by(Trade.created_at.desc()).limit(5).all()
    
    # Calculate total portfolio value
    total_value = 0
    for holding in portfolio:
        token = Token.query.filter_by(symbol=holding.token_symbol).first()
        if token:
            total_value += holding.balance * token.price
    
    return render_template('dashboard.html', 
                         tokens=tokens, 
                         portfolio=portfolio, 
                         recent_trades=recent_trades,
                         total_value=total_value)

@app.route('/trading')
def trading():
    tokens = Token.query.all()
    return render_template('trading.html', tokens=tokens)

@app.route('/portfolio')
def portfolio():
    portfolio_items = Portfolio.query.all()
    tokens = Token.query.all()
    
    # Calculate portfolio metrics
    portfolio_data = []
    total_value = 0
    total_cost = 0
    
    for holding in portfolio_items:
        token = Token.query.filter_by(symbol=holding.token_symbol).first()
        if token and holding.balance > 0:
            current_value = holding.balance * token.price
            cost_basis = holding.balance * holding.avg_buy_price
            pnl = current_value - cost_basis
            pnl_percent = (pnl / cost_basis * 100) if cost_basis > 0 else 0
            
            portfolio_data.append({
                'token': token,
                'holding': holding,
                'current_value': current_value,
                'cost_basis': cost_basis,
                'pnl': pnl,
                'pnl_percent': pnl_percent
            })
            
            total_value += current_value
            total_cost += cost_basis
    
    total_pnl = total_value - total_cost
    total_pnl_percent = (total_pnl / total_cost * 100) if total_cost > 0 else 0
    
    return render_template('portfolio.html', 
                         portfolio_data=portfolio_data,
                         total_value=total_value,
                         total_cost=total_cost,
                         total_pnl=total_pnl,
                         total_pnl_percent=total_pnl_percent)

@app.route('/chat')
def chat():
    messages = ChatMessage.query.order_by(ChatMessage.created_at.desc()).limit(20).all()
    return render_template('chat.html', messages=messages[::-1])

@app.route('/api/execute_trade', methods=['POST'])
def execute_trade():
    data = request.json
    trade_type = data.get('type')
    token_symbol = data.get('token')
    amount = float(data.get('amount', 0))
    
    try:
        result = execute_mock_trade(trade_type, token_symbol, amount, data.get('from_token'))
        if result['success']:
            return jsonify({'success': True, 'message': result['message'], 'trade': result['trade']})
        else:
            return jsonify({'success': False, 'message': result['message']})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Trade execution failed: {str(e)}'})

@app.route('/api/chat', methods=['POST'])
def chat_api():
    message = request.json.get('message', '').strip()
    
    if not message:
        return jsonify({'response': 'Please enter a message.'})
    
    try:
        response, trade_info = process_chat_message(message)
        
        # Save chat message
        chat_message = ChatMessage(
            message=message,
            response=response,
            trade_executed=trade_info if trade_info else None
        )
        db.session.add(chat_message)
        db.session.commit()
        
        return jsonify({
            'response': response,
            'trade_executed': trade_info is not None,
            'trade_info': trade_info
        })
    except Exception as e:
        return jsonify({'response': f'Error processing message: {str(e)}'})

@app.route('/api/price_data/<symbol>')
def get_price_data(symbol):
    # Generate mock price data for charts
    import random
    
    token = Token.query.filter_by(symbol=symbol.upper()).first()
    if not token:
        return jsonify({'error': 'Token not found'})
    
    # Generate 24 hours of price data (hourly)
    current_price = token.price
    price_data = []
    labels = []
    
    for i in range(24):
        time = datetime.now() - timedelta(hours=23-i)
        # Simulate price fluctuation
        change = random.uniform(-0.05, 0.05)  # ±5% change
        price = current_price * (1 + change * (i / 24))
        
        price_data.append(round(price, 6))
        labels.append(time.strftime('%H:%M'))
    
    return jsonify({
        'labels': labels,
        'data': price_data,
        'current_price': current_price
    })

@app.route('/api/refresh_prices')
def refresh_prices():
    get_current_prices()  # This updates the database with new mock prices
    tokens = Token.query.all()
    return jsonify({
        'tokens': [{
            'symbol': t.symbol,
            'price': t.price,
            'change_24h': t.change_24h
        } for t in tokens]
    })
