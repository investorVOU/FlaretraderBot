import re
from mock_data import execute_mock_trade
from models import Token

def process_chat_message(message):
    """
    Process chat message and extract trading commands including DEX functions
    Returns response and trade information
    """
    message = message.lower().strip()

    # Help command
    if any(word in message for word in ['help', 'commands', 'what can you do']):
        return get_help_response(), None

    # Price query
    price_match = re.search(r'(?:price|cost|value)\s+(?:of\s+)?(\w+)', message)
    if price_match:
        token_symbol = price_match.group(1).upper()
        return get_price_response(token_symbol), None

    # Portfolio/balance query
    if any(word in message for word in ['portfolio', 'balance', 'holdings', 'what do i have']):
        return get_portfolio_response(), None

    # DEX-specific commands

    # 1inch swap: "swap 100 WFLR for ETH using 1inch"
    oneinch_match = re.search(r'swap\s+(\d+(?:\.\d+)?)\s+(\w+)\s+for\s+(\w+)\s+using\s+1inch', message)
    if oneinch_match:
        amount = float(oneinch_match.group(1))
        from_token = oneinch_match.group(2).upper()
        to_token = oneinch_match.group(3).upper()
        #return execute_dex_swap_command(from_token, to_token, amount, use_oneinch=True)
        return "DEX swap via 1inch is not implemented yet", None

    # Cross-chain swap: "bridge 50 FLR to ethereum for ETH"
    bridge_match = re.search(r'bridge\s+(\d+(?:\.\d+)?)\s+(\w+)\s+to\s+(\w+)(?:\s+for\s+(\w+))?', message)
    if bridge_match:
        amount = float(bridge_match.group(1))
        from_token = bridge_match.group(2).upper()
        destination_chain = bridge_match.group(3).lower()
        to_token = bridge_match.group(4).upper() if bridge_match.group(4) else from_token
        #return execute_cross_chain_command(from_token, amount, destination_chain, to_token)
        return "Cross-chain swaps are not implemented yet", None

    # Add liquidity: "add liquidity 100 FLR 200 WFLR"
    liquidity_match = re.search(r'add\s+liquidity\s+(\d+(?:\.\d+)?)\s+(\w+)\s+(\d+(?:\.\d+)?)\s+(\w+)', message)
    if liquidity_match:
        amount_a = float(liquidity_match.group(1))
        token_a = liquidity_match.group(2).upper()
        amount_b = float(liquidity_match.group(3))
        token_b = liquidity_match.group(4).upper()
        #return execute_add_liquidity_command(token_a, token_b, amount_a, amount_b)
        return "Adding liquidity is not implemented yet", None

    # Wrap tokens: "wrap 500 FLR" or "unwrap 300 WFLR"
    wrap_match = re.search(r'(wrap|unwrap)\s+(\d+(?:\.\d+)?)\s+(\w+)', message)
    if wrap_match:
        action = wrap_match.group(1)
        amount = float(wrap_match.group(2))
        token = wrap_match.group(3).upper()

        if action == 'wrap' and token == 'FLR':
            #return execute_dex_swap_command('FLR', 'WFLR', amount, use_oneinch=False)
            result = execute_mock_trade('swap', 'WFLR', amount, 'FLR')
            if result['success']:
                return f"🔄 Successfully wrapped {amount} FLR to WFLR! Wrapped tokens are now in your portfolio.", f"Wrapped {amount} FLR to WFLR"
            else:
                return f"❌ {result['message']}", None
        elif action == 'unwrap' and token == 'WFLR':
            #return execute_dex_swap_command('WFLR', 'FLR', amount, use_oneinch=False)
            result = execute_mock_trade('swap', 'FLR', amount, 'WFLR')
            if result['success']:
                return f"🔄 Successfully unwrapped {amount} WFLR to FLR! Unwrapped tokens are now in your portfolio.", f"Unwrapped {amount} WFLR to FLR"
            else:
                return f"❌ {result['message']}", None
        else:
            return f"❌ Invalid wrap command. Use 'wrap [amount] FLR' or 'unwrap [amount] WFLR'", None

    # Trading commands (existing)
    # Buy command: "buy 100 WFLR"
    buy_match = re.search(r'buy\s+(\d+(?:\.\d+)?)\s+(\w+)', message)
    if buy_match:
        amount = float(buy_match.group(1))
        token = buy_match.group(2).upper()
        #return execute_trade_command('buy', token, amount)
        result = execute_mock_trade('buy', token, amount)

        if result['success']:
            return result['message'], f"Bought {amount} {token}"
        else:
            return f"❌ {result['message']}", None

    # Sell command: "sell 50 ETH"
    sell_match = re.search(r'sell\s+(\d+(?:\.\d+)?)\s+(\w+)', message)
    if sell_match:
        amount = float(sell_match.group(1))
        token = sell_match.group(2).upper()
        #return execute_trade_command('sell', token, amount)
        result = execute_mock_trade('sell', token, amount)

        if result['success']:
            return result['message'], f"Sold {amount} {token}"
        else:
            return f"❌ {result['message']}", None

    # Swap command: "swap 100 USDT for WFLR"
    swap_match = re.search(r'swap\s+(\d+(?:\.\d+)?)\s+(\w+)\s+for\s+(\w+)', message)
    if swap_match:
        amount = float(swap_match.group(1))
        from_token = swap_match.group(2).upper()
        to_token = swap_match.group(3).upper()
        #return execute_trade_command('swap', to_token, amount, from_token)
        result = execute_mock_trade('swap', to_token, amount, from_token)

        if result['success']:
            return result['message'], f"Swapped {amount} {from_token} for {to_token}"
        else:
            return f"❌ {result['message']}", None

    # Default response with suggestions
    #return get_default_response(), None
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

def execute_dex_swap_command(from_token, to_token, amount, use_oneinch=False):
    """Execute DEX swap via smart contract"""
    try:
        #wallet_service = get_wallet_service()
        #if not wallet_service.is_wallet_connected():
        #    return "🔗 Please connect your wallet first to use DEX features!", None

        #blockchain_service = get_blockchain_service()
        #wallet_address = wallet_service.get_connected_wallet()

        #success, message = blockchain_service.execute_dex_swap(
        #    from_token, to_token, amount, wallet_address, use_oneinch
        #)
        success = True
        message = f"Swapped {amount} {from_token} for {to_token}"

        if success:
            trade_info = {
                'type': 'dex_swap',
                'from_token': from_token,
                'to_token': to_token,
                'amount': amount,
                'onchain': True,
                'use_oneinch': use_oneinch
            }

            aggregator = " via 1inch" if use_oneinch else " via internal DEX"
            return f"🔥 {message}{aggregator}\n\n💡 Sign the transaction in your wallet to complete the swap!", trade_info
        else:
            return f"❌ DEX swap failed: {message}", None

    except Exception as e:
        return f"❌ DEX swap error: {str(e)}", None

def execute_cross_chain_command(from_token, amount, destination_chain, to_token):
    """Execute cross-chain swap via bridge"""
    try:
        #wallet_service = get_wallet_service()
        #if not wallet_service.is_wallet_connected():
        #    return "🔗 Please connect your wallet first to use cross-chain features!", None

        #blockchain_service = get_blockchain_service()
        #wallet_address = wallet_service.get_connected_wallet()

        #success, message = blockchain_service.execute_cross_chain_swap(
        #    from_token, amount, destination_chain, to_token, wallet_address, wallet_address
        #)
        success = True
        message = f"Bridged {amount} {from_token} to {destination_chain} for {to_token}"

        if success:
            trade_info = {
                'type': 'cross_chain_swap',
                'from_token': from_token,
                'to_token': to_token,
                'amount': amount,
                'destination_chain': destination_chain,
                'onchain': True
            }

            return f"🌉 {message}\n\n💡 Sign the transaction to bridge {amount} {from_token} to {destination_chain}!", trade_info
        else:
            return f"❌ Cross-chain swap failed: {message}", None

    except Exception as e:
        return f"❌ Cross-chain error: {str(e)}", None

def execute_add_liquidity_command(token_a, token_b, amount_a, amount_b):
    """Add liquidity to trading pair"""
    try:
        #wallet_service = get_wallet_service()
        #if not wallet_service.is_wallet_connected():
        #    return "🔗 Please connect your wallet first to add liquidity!", None

        #blockchain_service = get_blockchain_service()
        #wallet_address = wallet_service.get_connected_wallet()

        #success, message = blockchain_service.add_liquidity(
        #    token_a, token_b, amount_a, amount_b, wallet_address
        #)
        success = True
        message = f"Added {amount_a} {token_a} and {amount_b} {token_b} to liquidity pool."

        if success:
            trade_info = {
                'type': 'add_liquidity',
                'token_a': token_a,
                'token_b': token_b,
                'amount_a': amount_a,
                'amount_b': amount_b,
                'onchain': True
            }

            return f"💧 {message}\n\n💡 Sign the transaction to provide liquidity to the {token_a}/{token_b} pool!", trade_info
        else:
            return f"❌ Add liquidity failed: {message}", None

    except Exception as e:
        return f"❌ Liquidity error: {str(e)}", None
def get_help_response():
    """Return help message with available commands including DEX features"""
    return """🤖 **Flare Trading Bot Commands:**

📈 **Basic Trading:**
• `buy [amount] [token]` - Buy tokens (e.g., "buy 100 WFLR")
• `sell [amount] [token]` - Sell tokens (e.g., "sell 50 ETH")
• `swap [amount] [from] for [to]` - Swap tokens (e.g., "swap 100 USDT for WFLR")

🔥 **DEX Features:**
• `swap [amount] [from] for [to] using 1inch` - Use 1inch aggregator for best rates
• `wrap [amount] FLR` - Convert FLR to WFLR
• `unwrap [amount] WFLR` - Convert WFLR to FLR
• `bridge [amount] [token] to [chain]` - Cross-chain swaps
• `add liquidity [amount1] [token1] [amount2] [token2]` - Provide liquidity

🌉 **Cross-Chain:**
• `bridge 50 FLR to ethereum` - Bridge assets to other chains
• Supported chains: ethereum, polygon, arbitrum, optimism

💰 **Information:**
• `price [token]` - Get current price (e.g., "price WFLR")
• `balance` - View your portfolio
• `help` - Show this help message

🔥 **Supported Tokens:**
FLR, WFLR, ETH, MATIC, METIS, APE, USDT

💡 **Pro Tips:**
- Connect your wallet for real onchain trading
- Use "using 1inch" for better swap rates
- Commands are case-insensitive
- Ask "What's the best rate for swapping FLR to ETH?"

🔗 **Getting Started:**
1. Connect your MetaMask wallet
2. Ensure you're on Flare Network (Chain ID: 14)
3. Start trading with natural language commands!"""

def get_default_response():
    """Return a default response with suggestions"""
    return "Sorry, I didn't understand that. Try 'help' for available commands."

def get_price_response(token_symbol):
    """Return price information for a token"""
    token = Token.query.filter_by(symbol=token_symbol).first()

    if token:
        change_emoji = "📈" if token.change_24h >= 0 else "📉"
        return f"💰 {token.name} ({token.symbol}): ${token.price:.6f} {change_emoji} {token.change_24h:+.2f}% (24h)", None
    else:
        return f"❌ Token {token_symbol} not found. Supported tokens: WFLR, FLR, MATIC, METIS, USDT, ETH, APE", None

def get_portfolio_response():
    """Return portfolio information"""
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

def execute_trade_command(trade_type, token, amount, from_token=None):
    """Execute basic trade command (buy, sell, swap)"""
    result = execute_mock_trade(trade_type, token, amount, from_token)

    if result['success']:
        if trade_type == 'buy':
            return result['message'], f"Bought {amount} {token}"
        elif trade_type == 'sell':
            return result['message'], f"Sold {amount} {token}"
        elif trade_type == 'swap':
            return result['message'], f"Swapped {amount} {from_token} for {token}"
    else:
        return f"❌ {result['message']}", None

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