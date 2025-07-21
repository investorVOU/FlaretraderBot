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

**📊 Information:**
• `price WFLR` - Get token price
• `balance` - View portfolio
• `help` - Show this help

**📈 Supported Tokens:**
WFLR, FLR, MATIC, METIS, USDT, ETH, APE

*Examples:*
- "Buy 100 WFLR"
- "Swap 50 FLR for MATIC" 
- "What's the price of ETH?"
"""
        return help_text, None
    
    # Default response for unrecognized commands
    responses = [
        "🤔 I didn't understand that command. Type 'help' to see available commands.",
        "💡 Try commands like 'buy 100 WFLR', 'sell 50 ETH', or 'price MATIC'.",
        "❓ Need help? Type 'help' to see all available trading commands.",
        "🚀 Ready to trade! Use commands like 'buy', 'sell', 'swap', or 'price'."
    ]
    
    import random
    return random.choice(responses), None
