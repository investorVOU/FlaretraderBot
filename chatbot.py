import re
from mock_data import execute_mock_trade
from models import Token

def process_chat_message(message):
    """Process chat message and execute trading commands if applicable."""
    message = message.lower().strip()
    
    # Define patterns for trading commands
    buy_pattern = r'buy (\d+\.?\d*) (\w+)(?:\s+with\s+(\w+))?'
    sell_pattern = r'sell (\d+\.?\d*) (\w+)'
    swap_pattern = r'swap (\d+\.?\d*) (\w+) for (\w+)'
    wrap_pattern = r'wrap (\d+\.?\d*) (\w+)(?: to (\w+))?'
    price_pattern = r'(?:price|what.* price) (?:of )?(\w+)'
    balance_pattern = r'(?:balance|holdings?|portfolio)'
    help_pattern = r'help|commands?'
    
    # Check for buy command
    buy_match = re.search(buy_pattern, message)
    if buy_match:
        amount = float(buy_match.group(1))
        token = buy_match.group(2).upper()
        
        result = execute_mock_trade('buy', token, amount)
        
        if result['success']:
            return result['message'], f"Bought {amount} {token}"
        else:
            return f"❌ {result['message']}", None
    
    # Check for sell command
    sell_match = re.search(sell_pattern, message)
    if sell_match:
        amount = float(sell_match.group(1))
        token = sell_match.group(2).upper()
        
        result = execute_mock_trade('sell', token, amount)
        
        if result['success']:
            return result['message'], f"Sold {amount} {token}"
        else:
            return f"❌ {result['message']}", None
    
    # Check for swap command
    swap_match = re.search(swap_pattern, message)
    if swap_match:
        amount = float(swap_match.group(1))
        from_token = swap_match.group(2).upper()
        to_token = swap_match.group(3).upper()
        
        result = execute_mock_trade('swap', to_token, amount, from_token)
        
        if result['success']:
            return result['message'], f"Swapped {amount} {from_token} for {to_token}"
        else:
            return f"❌ {result['message']}", None
    
    # Check for wrap command (FLR to WFLR)
    wrap_match = re.search(wrap_pattern, message)
    if wrap_match:
        amount = float(wrap_match.group(1))
        from_token = wrap_match.group(2).upper()
        to_token = wrap_match.group(3).upper() if wrap_match.group(3) else 'WFLR'
        
        # Handle wrapping logic
        if from_token == 'FLR' and to_token == 'WFLR':
            result = execute_mock_trade('swap', to_token, amount, from_token)
            if result['success']:
                return f"🔄 Successfully wrapped {amount} FLR to WFLR! Wrapped tokens are now in your portfolio.", f"Wrapped {amount} FLR to WFLR"
            else:
                return f"❌ {result['message']}", None
        elif from_token == 'WFLR' and to_token == 'FLR':
            result = execute_mock_trade('swap', to_token, amount, from_token)
            if result['success']:
                return f"🔄 Successfully unwrapped {amount} WFLR to FLR! Unwrapped tokens are now in your portfolio.", f"Unwrapped {amount} WFLR to FLR"
            else:
                return f"❌ {result['message']}", None
        else:
            return f"❌ Wrapping is only supported between FLR and WFLR tokens.", None
    
    # Check for price query
    price_match = re.search(price_pattern, message)
    if price_match:
        token_symbol = price_match.group(1).upper()
        token = Token.query.filter_by(symbol=token_symbol).first()
        
        if token:
            change_emoji = "📈" if token.change_24h >= 0 else "📉"
            return f"💰 {token.name} ({token.symbol}): ${token.price:.6f} {change_emoji} {token.change_24h:+.2f}% (24h)", None
        else:
            return f"❌ Token {token_symbol} not found. Supported tokens: WFLR, FLR, MATIC, METIS, USDT, ETH, APE", None
    
    # Check for balance/portfolio query
    if re.search(balance_pattern, message):
        from models import Portfolio
        portfolio_items = Portfolio.query.filter(Portfolio.balance > 0).all()
        
        if not portfolio_items:
            return "📊 Your portfolio is empty. Start trading to build your holdings!", None
        
        portfolio_text = "📊 Your Portfolio:\n"
        total_value = 0
        
        for item in portfolio_items:
            token = Token.query.filter_by(symbol=item.token_symbol).first()
            if token:
                value = item.balance * token.price
                total_value += value
                portfolio_text += f"• {item.balance:.4f} {item.token_symbol} = ${value:.2f}\n"
        
        portfolio_text += f"\n💎 Total Value: ${total_value:.2f}"
        return portfolio_text, None
    
    # Check for help command
    if re.search(help_pattern, message):
        help_text = """🤖 **Trading Bot Commands:**

**💰 Trading:**
• `buy 100 WFLR` - Buy tokens
• `sell 50 ETH` - Sell tokens  
• `swap 100 USDT for WFLR` - Swap tokens
• `wrap 200 FLR to WFLR` - Wrap FLR tokens

**📊 Information:**
• `price WFLR` - Get token price
• `balance` - View portfolio
• `help` - Show this help

**📈 Supported Tokens:**
WFLR, FLR, MATIC, METIS, USDT, ETH, APE

*Examples:*
- "Buy 100 WFLR"
- "Swap 50 FLR for MATIC" 
- "Wrap 200 FLR to WFLR"
- "What's the price of ETH?"
"""
        return help_text, None
    
    # Check for general market/token info requests
    if any(word in message for word in ['market', 'tokens', 'supported', 'available']):
        return """📊 **Supported Tokens on Flare Network:**
        
**Core Flare Tokens:**
• FLR - Native Flare token
• WFLR - Wrapped Flare (for DeFi)

**Multi-Chain Assets:**
• ETH - Ethereum 
• MATIC - Polygon
• METIS - Metis
• APE - ApeCoin
• USDT - Tether USD (stablecoin)

All tokens are available for trading via buy/sell/swap commands. Use 'wrap FLR' to convert to WFLR for DeFi protocols.""", None
    
    # Check for general trading questions
    if any(word in message for word in ['how', 'what', 'trading', 'work']):
        return """🤖 **How Trading Works:**
        
I'm your AI trading assistant for the Flare Network. Simply tell me what you want to do:

**Trading Commands:**
• "buy 100 WFLR" - Purchase tokens
• "sell 50 ETH" - Sell your holdings
• "swap 100 USDT for WFLR" - Exchange tokens
• "wrap 200 FLR to WFLR" - Convert to wrapped tokens

**Information:**
• "price ETH" - Get current prices
• "balance" - Check your portfolio
• "help" - See all commands

Just type naturally - I understand various ways of saying the same thing!""", None

    # Default response for unrecognized commands
    responses = [
        "🤔 I didn't understand that command. Try 'help' to see what I can do, or ask me 'how does trading work?'",
        "💡 Try commands like 'buy 100 WFLR', 'swap 50 USDT for ETH', or 'price MATIC'. Need help? Just ask!",
        "❓ I'm here to help with trading! Use commands like 'buy', 'sell', 'swap', or ask me about prices and balances.",
        "🚀 Ready to trade! Try 'buy [amount] [token]' or 'swap [amount] [from] for [to]'. Type 'help' for more options."
    ]
    
    import random
    return random.choice(responses), None
