from flask import render_template, request, jsonify, flash, redirect, url_for
from app import app, db
from models import Token, Portfolio, Trade, ChatMessage
from mock_data import initialize_real_data, update_real_prices, execute_real_trade, sync_real_portfolio
from chatbot import process_chat_message
from blockchain_service import get_blockchain_service
from wallet_service import get_wallet_service, require_wallet_connection
import json
import logging
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO)

@app.route('/')
def dashboard():
    initialize_real_data()
    tokens = Token.query.all()
    
    # Get portfolio for connected wallet only
    wallet_service = get_wallet_service()
    wallet_address = wallet_service.get_connected_wallet()
    
    if wallet_address:
        portfolio = Portfolio.query.filter(
            Portfolio.balance > 0,
            Portfolio.wallet_address == wallet_address
        ).all()
    else:
        portfolio = []
    
    recent_trades = Trade.query.order_by(Trade.created_at.desc()).limit(5).all()

    # Calculate total portfolio value from real balances
    total_value = 0
    for holding in portfolio:
        token = Token.query.filter_by(symbol=holding.token_symbol).first()
        if token:
            total_value += holding.balance * token.price

    return render_template('dashboard_modern.html', 
                         tokens=tokens, 
                         portfolio=portfolio, 
                         recent_trades=recent_trades,
                         total_value=total_value,
                         wallet_connected=wallet_address is not None)

@app.route('/trading')
def trading():
    tokens = Token.query.all()
    return render_template('trading.html', tokens=tokens)

@app.route('/portfolio')
def portfolio():
    # Get portfolio for connected wallet only
    wallet_service = get_wallet_service()
    wallet_address = wallet_service.get_connected_wallet()
    
    if wallet_address:
        portfolio_items = Portfolio.query.filter(
            Portfolio.balance > 0,
            Portfolio.wallet_address == wallet_address
        ).all()
    else:
        portfolio_items = []

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

            # Convert to JSON-serializable format
            portfolio_data.append({
                'token': {
                    'symbol': token.symbol,
                    'name': token.name,
                    'price': token.price
                },
                'holding': {
                    'balance': holding.balance,
                    'avg_buy_price': holding.avg_buy_price
                },
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
                         total_pnl_percent=total_pnl_percent,
                         wallet_connected=wallet_address is not None)

@app.route('/chat')
def chat():
    messages = ChatMessage.query.order_by(ChatMessage.created_at.desc()).limit(20).all()
    return render_template('chat.html', messages=messages[::-1])

@app.route('/api/execute_trade', methods=['POST'])
def execute_trade():
    """Execute real blockchain trades only"""
    wallet_service = get_wallet_service()
    if not wallet_service.is_wallet_connected():
        return jsonify({
            'success': False, 
            'message': 'Wallet connection required for real trading'
        }), 401

    data = request.json
    trade_type = data.get('type')
    token_symbol = data.get('token')
    amount = float(data.get('amount', 0))
    wallet_address = wallet_service.get_connected_wallet()

    try:
        result = execute_real_trade(
            trade_type, 
            token_symbol, 
            amount, 
            data.get('from_token'),
            wallet_address
        )
        
        if result['success']:
            # Sync portfolio with real balances after trade
            sync_real_portfolio(wallet_address)
            
        return jsonify({
            'success': result['success'], 
            'message': result['message'], 
            'trade': result.get('trade'),
            'real_trade': True
        })
    except Exception as e:
        logging.error(f"Real trade execution failed: {e}")
        return jsonify({
            'success': False, 
            'message': f'Real trade execution failed: {str(e)}'
        })

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
    """Refresh prices from live blockchain and market data"""
    try:
        blockchain_service = get_blockchain_service()
        blockchain_service.update_token_prices()

        tokens = Token.query.all()
        return jsonify({
            'success': True,
            'message': 'Prices updated from live blockchain data',
            'tokens': [{
                'symbol': t.symbol,
                'price': t.price,
                'change_24h': t.change_24h,
                'real_data': True
            } for t in tokens]
        })
    except Exception as e:
        logging.error(f"Error refreshing live prices: {e}")
        return jsonify({
            'success': False,
            'message': f'Live price update failed: {str(e)}',
            'tokens': []
        })

# Wallet connection endpoints
@app.route('/api/wallet/config')
def get_wallet_config():
    """Get WalletConnect configuration"""
    wallet_service = get_wallet_service()
    return jsonify(wallet_service.get_wallet_config())

@app.route('/api/wallet/connect', methods=['POST'])
def connect_wallet():
    """Connect a wallet via WalletConnect"""
    try:
        data = request.json
        wallet_address = data.get('address')
        chain_id = data.get('chainId')

        wallet_service = get_wallet_service()
        success = wallet_service.connect_wallet(wallet_address, chain_id)

        if success:
            # Sync portfolio with real blockchain balances
            sync_real_portfolio(wallet_address)

            return jsonify({
                'success': True,
                'message': 'Wallet connected successfully',
                'address': wallet_address,
                'chainId': chain_id
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to connect wallet'
            }), 400

    except Exception as e:
        logging.error(f"Error connecting wallet: {e}")
        return jsonify({
            'success': False,
            'message': f'Connection error: {str(e)}'
        }), 500

@app.route('/api/wallet/disconnect', methods=['POST'])
def disconnect_wallet():
    """Disconnect the current wallet"""
    try:
        wallet_service = get_wallet_service()
        wallet_service.disconnect_wallet()

        return jsonify({
            'success': True,
            'message': 'Wallet disconnected successfully'
        })
    except Exception as e:
        logging.error(f"Error disconnecting wallet: {e}")
        return jsonify({
            'success': False,
            'message': f'Disconnection error: {str(e)}'
        }), 500

@app.route('/api/wallet/status')
def wallet_status():
    """Get current wallet connection status"""
    wallet_service = get_wallet_service()

    return jsonify({
        'connected': wallet_service.is_wallet_connected(),
        'address': wallet_service.get_connected_wallet(),
        'chain': wallet_service.get_chain_info()
    })

@app.route('/api/execute_onchain_trade', methods=['POST'])
def execute_onchain_trade():
    """Execute a real onchain trade via smart contracts"""
    try:
        wallet_service = get_wallet_service()
        if not wallet_service.is_wallet_connected():
            return jsonify({
                'success': False,
                'message': 'Wallet connection required for onchain trading'
            }), 401

        data = request.json
        trade_type = data.get('type')
        from_token = data.get('from_token')
        to_token = data.get('token')
        amount = float(data.get('amount', 0))
        use_oneinch = data.get('use_oneinch', False)

        wallet_address = wallet_service.get_connected_wallet()
        blockchain_service = get_blockchain_service()

        if trade_type == 'swap':
            success, message = blockchain_service.execute_dex_swap(
                from_token, to_token, amount, wallet_address, use_oneinch
            )

            if success:
                # Record the trade
                trade = Trade(
                    trade_type=trade_type,
                    from_token=from_token,
                    to_token=to_token,
                    amount=amount,
                    price=Token.query.filter_by(symbol=to_token).first().price,
                    total_value=amount * Token.query.filter_by(symbol=to_token).first().price
                )
                db.session.add(trade)
                db.session.commit()

            return jsonify({
                'success': success,
                'message': message,
                'onchain': True,
                'use_oneinch': use_oneinch
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Only swap operations supported onchain currently'
            }), 400

    except Exception as e:
        logging.error(f"Error executing onchain trade: {e}")
        return jsonify({
            'success': False,
            'message': f'Onchain trade failed: {str(e)}'
        }), 500

@app.route('/api/execute_dex_swap', methods=['POST'])
def execute_dex_swap():
    """Execute DEX swap with 1inch integration"""
    try:
        wallet_service = get_wallet_service()
        if not wallet_service.is_wallet_connected():
            return jsonify({
                'success': False,
                'message': 'Wallet connection required for DEX trading'
            }), 401

        data = request.json
        from_token = data.get('from_token')
        to_token = data.get('to_token')
        amount = float(data.get('amount', 0))
        use_oneinch = data.get('use_oneinch', False)

        wallet_address = wallet_service.get_connected_wallet()
        blockchain_service = get_blockchain_service()

        success, message = blockchain_service.execute_dex_swap(
            from_token, to_token, amount, wallet_address, use_oneinch
        )

        if success:
            # Record the trade
            trade = Trade(
                trade_type='dex_swap',
                from_token=from_token,
                to_token=to_token,
                amount=amount,
                price=Token.query.filter_by(symbol=to_token).first().price,
                total_value=amount * Token.query.filter_by(symbol=to_token).first().price
            )
            db.session.add(trade)
            db.session.commit()

        return jsonify({
            'success': success,
            'message': message,
            'use_oneinch': use_oneinch,
            'transaction_ready': success
        })

    except Exception as e:
        logging.error(f"Error executing DEX swap: {e}")
        return jsonify({
            'success': False,
            'message': f'DEX swap failed: {str(e)}'
        }), 500

@app.route('/api/execute_cross_chain', methods=['POST'])
def execute_cross_chain():
    """Execute cross-chain swap via bridge"""
    try:
        wallet_service = get_wallet_service()
        if not wallet_service.is_wallet_connected():
            return jsonify({
                'success': False,
                'message': 'Wallet connection required for cross-chain trading'
            }), 401

        data = request.json
        from_token = data.get('from_token')
        amount = float(data.get('amount', 0))
        destination_chain = data.get('destination_chain')
        to_token = data.get('to_token', from_token)
        recipient = data.get('recipient')

        wallet_address = wallet_service.get_connected_wallet()
        if not recipient:
            recipient = wallet_address

        blockchain_service = get_blockchain_service()

        success, message = blockchain_service.execute_cross_chain_swap(
            from_token, amount, destination_chain, to_token, wallet_address, recipient
        )

        if success:
            # Record the trade
            trade = Trade(
                trade_type='cross_chain',
                from_token=from_token,
                to_token=to_token,
                amount=amount,
                price=Token.query.filter_by(symbol=from_token).first().price,
                total_value=amount * Token.query.filter_by(symbol=from_token).first().price
            )
            db.session.add(trade)
            db.session.commit()

        return jsonify({
            'success': success,
            'message': message,
            'destination_chain': destination_chain,
            'transaction_ready': success
        })

    except Exception as e:
        logging.error(f"Error executing cross-chain swap: {e}")
        return jsonify({
            'success': False,
            'message': f'Cross-chain swap failed: {str(e)}'
        }), 500

@app.route('/api/add_liquidity', methods=['POST'])
def add_liquidity():
    """Add liquidity to trading pair"""
    try:
        wallet_service = get_wallet_service()
        if not wallet_service.is_wallet_connected():
            return jsonify({
                'success': False,
                'message': 'Wallet connection required for liquidity provision'
            }), 401

        data = request.json
        token_a = data.get('token_a')
        token_b = data.get('token_b')
        amount_a = float(data.get('amount_a', 0))
        amount_b = float(data.get('amount_b', 0))

        wallet_address = wallet_service.get_connected_wallet()
        blockchain_service = get_blockchain_service()

        success, message = blockchain_service.add_liquidity(
            token_a, token_b, amount_a, amount_b, wallet_address
        )

        if success:
            # Record the liquidity addition
            trade = Trade(
                trade_type='add_liquidity',
                from_token=token_a,
                to_token=token_b,
                amount=amount_a,
                price=amount_b / amount_a if amount_a > 0 else 0,
                total_value=amount_a * Token.query.filter_by(symbol=token_a).first().price + 
                           amount_b * Token.query.filter_by(symbol=token_b).first().price
            )
            db.session.add(trade)
            db.session.commit()

        return jsonify({
            'success': success,
            'message': message,
            'pair': f"{token_a}/{token_b}",
            'transaction_ready': success
        })

    except Exception as e:
        logging.error(f"Error adding liquidity: {e}")
        return jsonify({
            'success': False,
            'message': f'Add liquidity failed: {str(e)}'
        }), 500



@app.route('/api/cross_chain_quote', methods=['POST'])
def get_cross_chain_quote():
    """Get quote for cross-chain swap"""
    try:
        data = request.json
        from_chain = data.get('from_chain', 'flare')
        to_chain = data.get('to_chain', 'ethereum')
        from_token = data.get('from_token')
        to_token = data.get('to_token')
        amount = float(data.get('amount', 0))

        if not all([from_token, to_token, amount]):
            return jsonify({
                'success': False,
                'message': 'Missing required parameters'
            }), 400

        blockchain_service = get_blockchain_service()
        quote = blockchain_service.get_cross_chain_quote(
            from_chain, to_chain, from_token, to_token, amount
        )

        if 'error' in quote:
            return jsonify({
                'success': False,
                'message': quote['error']
            }), 400

        return jsonify({
            'success': True,
            'quote': quote
        })

    except Exception as e:
        logging.error(f"Error getting cross-chain quote: {e}")
        return jsonify({
            'success': False,
            'message': f'Quote failed: {str(e)}'
        }), 500

@app.route('/api/execute_cross_chain_swap', methods=['POST'])
def execute_cross_chain_swap():
    """Execute cross-chain swap"""
    try:
        wallet_service = get_wallet_service()
        if not wallet_service.is_wallet_connected():
            return jsonify({
                'success': False,
                'message': 'Wallet connection required for cross-chain trading'
            }), 401

        data = request.json
        from_chain = data.get('from_chain', 'flare')
        to_chain = data.get('to_chain', 'ethereum')
        from_token = data.get('from_token')
        to_token = data.get('to_token')
        amount = float(data.get('amount', 0))

        wallet_address = wallet_service.get_connected_wallet()
        blockchain_service = get_blockchain_service()

        success, message = blockchain_service.execute_cross_chain_swap(
            from_chain, to_chain, from_token, to_token, amount, wallet_address
        )

        if success:
            # Record the cross-chain trade
            trade = Trade(
                trade_type='cross_chain_swap',
                from_token=from_token,
                to_token=to_token,
                amount=amount,
                price=Token.query.filter_by(symbol=to_token).first().price if Token.query.filter_by(symbol=to_token).first() else 1.0,
                total_value=amount,
                metadata=json.dumps({
                    'from_chain': from_chain,
                    'to_chain': to_chain,
                    'cross_chain': True
                })
            )
            db.session.add(trade)
            db.session.commit()

        return jsonify({
            'success': success,
            'message': message,
            'cross_chain': True
        })

    except Exception as e:
        logging.error(f"Error executing cross-chain swap: {e}")
        return jsonify({
            'success': False,
            'message': f'Cross-chain swap failed: {str(e)}'
        }), 500

@app.route('/api/supported_chains')
def get_supported_chains():
    """Get list of supported chains and their tokens"""
    try:
        blockchain_service = get_blockchain_service()

        chains_info = {}
        for chain, tokens in blockchain_service.cross_chain_tokens.items():
            chains_info[chain] = {
                'name': chain.title(),
                'tokens': list(tokens.keys()),
                'native_token': {
                    'flare': 'FLR',
                    'ethereum': 'ETH',
                    'polygon': 'MATIC',
                    'bsc': 'BNB',
                    'avalanche': 'AVAX'
                }.get(chain, 'ETH'),
                'rpc_connected': chain in blockchain_service.web3_connections and 
                               blockchain_service.web3_connections[chain].is_connected()
            }

        return jsonify({
            'success': True,
            'chains': chains_info
        })

    except Exception as e:
        logging.error(f"Error getting supported chains: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to get chains: {str(e)}'
        }), 500