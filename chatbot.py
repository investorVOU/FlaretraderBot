import re
import json
from mock_data import execute_mock_trade
from models import Token
from blockchain_service import get_blockchain_service

def process_chat_message(message):
    """
    Enhanced chatbot that handles trading commands and general questions
    """
    message_lower = message.lower().strip()

    # Supported chains information
    supported_chains = {
        'flare': {'name': 'Flare Network', 'currency': 'FLR', 'chainId': 14},
        'ethereum': {'name': 'Ethereum', 'currency': 'ETH', 'chainId': 1},
        'polygon': {'name': 'Polygon', 'currency': 'MATIC', 'chainId': 137},
        'bsc': {'name': 'Binance Smart Chain', 'currency': 'BNB', 'chainId': 56},
        'avalanche': {'name': 'Avalanche', 'currency': 'AVAX', 'chainId': 43114},
        'coston': {'name': 'Coston Testnet', 'currency': 'C2FLR', 'chainId': 16}
    }

    # Chain support questions
    if any(phrase in message_lower for phrase in ['what chains', 'which chains', 'supported chains', 'chains do you support']):
        chain_list = []
        for chain, info in supported_chains.items():
            chain_list.append(f"• **{info['name']}** ({info['currency']}) - Chain ID: {info['chainId']}")

        return f"""🌐 **Supported Blockchain Networks:**

{chr(10).join(chain_list)}

**Features Available:**
✅ Cross-chain swaps via LayerZero/Wormhole bridges
✅ 1inch DEX aggregation for best rates  
✅ Native FLR ↔ WFLR wrapping
✅ Liquidity provision to pools
✅ Real-time FTSO price feeds
✅ AI-powered trading assistance

Connect your wallet to start trading across all these networks! 🚀""", None

    # Help and features questions
    if any(phrase in message_lower for phrase in ['help', 'what can you do', 'features', 'commands']):
        return """🤖 **AI Trading Assistant - Available Commands:**

**💰 Basic Trading:**
• "Buy 100 FLR" - Purchase tokens
• "Sell 50 ETH" - Sell tokens  
• "Swap 100 FLR for ETH" - Token swaps

**🌉 Cross-Chain Trading:**
• "Bridge 100 FLR to Ethereum"
• "Swap 50 FLR to ETH on Polygon"
• "Get cross-chain quote for 100 FLR to MATIC"

**🔄 DEX Operations:**
• "Add liquidity FLR/WFLR 100/100"
• "Remove liquidity from FLR/ETH pool"
• "Use 1inch for best rates"

**💡 Information:**
• "What chains do you support?"
• "Show my portfolio"
• "Current FLR price"
• "Get gas estimates"

Just ask me naturally - I understand context and can help with any trading operation! 🚀""", None

    # Portfolio questions
    if any(phrase in message_lower for phrase in ['portfolio', 'my holdings', 'balance']):
        return """📊 **Portfolio Overview:**

To view your complete portfolio with real balances, please connect your wallet first using the "Connect Wallet" button.

Once connected, I can show you:
• Real-time token balances across all chains
• Portfolio value and P&L
• Recent transaction history
• Yield farming positions
• Cross-chain assets

Connect your wallet to get started! 💼""", None

    # Price questions
    if any(phrase in message_lower for phrase in ['price', 'current price', 'how much']):
        tokens = ['flr', 'eth', 'btc', 'matic', 'bnb', 'avax']
        mentioned_token = None
        for token in tokens:
            if token in message_lower:
                mentioned_token = token.upper()
                break

        if mentioned_token:
            try:
                token_obj = Token.query.filter_by(symbol=mentioned_token).first()
                if token_obj:
                    change_indicator = "📈" if token_obj.change_24h > 0 else "📉"
                    return f"""💰 **{mentioned_token} Price Update:**

Current Price: **${token_obj.price:.6f}**
24h Change: {change_indicator} **{token_obj.change_24h:+.2f}%**

*Powered by Flare Network FTSO price feeds*

Ready to trade? Just say "buy {mentioned_token}" or "swap to {mentioned_token}"! 🚀""", None
            except:
                pass

        return """💰 **Current Market Prices:**

Use commands like:
• "FLR price" - Get FLR current price
• "ETH price" - Get Ethereum price  
• "Show all prices" - View all token prices

Connect your wallet for real-time portfolio values! 📊""", None

    # Gas and fee questions
    if any(phrase in message_lower for phrase in ['gas', 'fee', 'cost', 'estimate']):
        return """⛽ **Gas & Fee Information:**

**Flare Network:** ~0.001 FLR per transaction
**Ethereum:** 15-50 Gwei (varies by network congestion)
**Polygon:** ~30 Gwei
**BSC:** ~5 Gwei  
**Avalanche:** ~25 nAVAX

**Cross-Chain Bridge Fees:**
• LayerZero: 0.1-0.5% + destination gas
• Wormhole: ~$5-15 fixed fee

I'll always show you estimated fees before executing trades! 💡""", None

    # Friendly greetings
    if any(phrase in message_lower for phrase in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
        return """👋 **Hello! I'm your AI Trading Assistant!**

I'm here to help you trade across multiple blockchains including Flare, Ethereum, Polygon, BSC, and Avalanche.

**Quick Start:**
1. Connect your wallet using the button above
2. Ask me anything like "buy 100 FLR" or "what chains do you support?"
3. I'll handle the rest with smart routing and best prices!

What would you like to trade today? 🚀""", None

    # Trading pattern matching
    # Buy pattern
    buy_pattern = r'buy\s+(\d+(?:\.\d+)?)\s+(\w+)'
    buy_match = re.search(buy_pattern, message_lower)
    if buy_match:
        amount = float(buy_match.group(1))
        token = buy_match.group(2).upper()

        try:
            result = execute_mock_trade('buy', token, amount)
            if result['success']:
                return f"✅ Successfully bought {amount} {token}! {result['message']}", result.get('trade')
            else:
                return f"❌ Trade failed: {result['message']}", None
        except Exception as e:
            return f"❌ Error executing buy order: {str(e)}", None

    # Sell pattern  
    sell_pattern = r'sell\s+(\d+(?:\.\d+)?)\s+(\w+)'
    sell_match = re.search(sell_pattern, message_lower)
    if sell_match:
        amount = float(sell_match.group(1))
        token = sell_match.group(2).upper()

        try:
            result = execute_mock_trade('sell', token, amount)
            if result['success']:
                return f"✅ Successfully sold {amount} {token}! {result['message']}", result.get('trade')
            else:
                return f"❌ Trade failed: {result['message']}", None
        except Exception as e:
            return f"❌ Error executing sell order: {str(e)}", None

    # Swap pattern
    swap_pattern = r'swap\s+(\d+(?:\.\d+)?)\s+(\w+)\s+(?:for|to)\s+(\w+)'
    swap_match = re.search(swap_pattern, message_lower)
    if swap_match:
        amount = float(swap_match.group(1))
        from_token = swap_match.group(2).upper()
        to_token = swap_match.group(3).upper()

        return f"""🔄 **Swap Request Detected:**

**From:** {amount} {from_token}
**To:** {to_token}

Connect your wallet to execute this swap with:
• Real-time price quotes
• Multiple DEX routing via 1inch
• Cross-chain bridging if needed
• Minimal slippage protection

Ready to proceed? Connect wallet and confirm! 🚀""", None

    # Bridge/Cross-chain pattern
    if any(phrase in message_lower for phrase in ['bridge', 'cross chain', 'cross-chain']):
        return """🌉 **Cross-Chain Bridge:**

I can help you bridge assets between:
• Flare ↔ Ethereum
• Flare ↔ Polygon  
• Flare ↔ BSC
• Flare ↔ Avalanche

**Example commands:**
• "Bridge 100 FLR to Ethereum"
• "Send 50 FLR to Polygon as MATIC"
• "Cross-chain swap 100 FLR to ETH"

Connect your wallet to start bridging! 🚀""", None

    # Default friendly response
    return """🤖 **I'm here to help with your trading needs!**

I didn't quite understand that request, but I can help you with:

**💰 Trading:** "buy 100 FLR", "sell 50 ETH", "swap FLR for ETH"
**🌉 Cross-chain:** "bridge to Ethereum", "what chains do you support?"
**📊 Info:** "FLR price", "show portfolio", "help"

Try asking me something specific, or type "help" to see all available commands! 😊""", None