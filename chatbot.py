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
    
    # Enhanced conversational patterns for questions
    if any(phrase in message for phrase in ['how do', 'what can', 'tell me about', 'explain', 'how does']):
        if 'work' in message or 'trading' in message:
            return """I'm your conversational AI assistant for trading on Flare Network! Here's how we can work together:

**Natural Trading:**
Just tell me what you want to do naturally:
• "I want to buy 100 WFLR" or simply "buy 100 WFLR"
• "Can you sell 50 ETH for me?" or "sell 50 ETH"
• "Swap some USDT for WFLR" or "exchange 100 USDT for WFLR"

**Ask Questions:**
• "What's the current price of ETH?"
• "Show me my portfolio"
• "What tokens can I trade here?"

**Learn More:**
• "Tell me about Flare Network"
• "How does wrapping work?"

I understand context and can have real conversations about your trades and the crypto market. No need for exact commands - just chat naturally!""", None
    
    # Check for token information requests
    if any(phrase in message for phrase in ['tell me about', 'what is', 'explain']) and any(token in message for token in ['flr', 'wflr', 'eth', 'matic', 'metis', 'usdt', 'ape']):
        return """I'd be happy to explain about these tokens! Here's what's available on Flare Network:

**FLR & WFLR:** FLR is Flare's native token. WFLR is the wrapped version used in DeFi protocols. You can wrap/unwrap between them anytime.

**ETH:** Ethereum bridged to Flare Network for lower fees and faster transactions.

**MATIC:** Polygon's native token, available for cross-chain trading.

**METIS:** From the Metis ecosystem, offering DeFi opportunities on Flare.

**USDT:** The popular stablecoin for stable value trading.

**APE:** ApeCoin from the Bored Ape ecosystem.

All are tradeable with real-time pricing from Flare's FTSO oracles. What would you like to know more about?""", None

    # Enhanced conversational responses for unrecognized input
    conversational_responses = [
        "I'm not sure I understood that. Could you try asking in a different way? For example, 'buy 100 WFLR' or 'what's the price of ETH?'",
        "Hmm, I didn't catch that. I can help you trade, check prices, or view your portfolio. What would you like to do?",
        "I'm here to help with trading on Flare Network! Try asking me about token prices, making trades, or checking your balance.",
        "That's a bit unclear to me. I understand commands like 'buy tokens', 'check prices', or 'show portfolio'. What can I help you with?",
        "I'd love to help, but I'm not sure what you're asking for. Try something like 'buy 50 WFLR' or 'what tokens are available?'"
    ]
    
    import random
    return random.choice(conversational_responses), None
