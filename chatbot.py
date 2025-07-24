
import re
import json
from mock_data import execute_mock_trade
from models import Token
from blockchain_service import get_blockchain_service

def process_chat_message(message):
    """Enhanced AI chatbot with cross-chain capabilities and friendly personality"""
    message = message.lower().strip()
    
    # Cross-chain patterns
    cross_chain_pattern = r'(?:bridge|swap|send|transfer) (\d+\.?\d*) (\w+) (?:from (\w+) )?to (\w+)(?: (?:chain|network))?'
    cross_chain_quote_pattern = r'(?:quote|price|cost|fee).* (\d+\.?\d*) (\w+) (?:from (\w+) )?to (\w+)'
    
    # Enhanced trading patterns
    buy_pattern = r'(?:buy|purchase|get|acquire) (\d+\.?\d*) (\w+)(?:\s+(?:with|using)\s+(\w+))?(?:\s+on\s+(\w+))?'
    sell_pattern = r'(?:sell|dump|liquidate) (\d+\.?\d*) (\w+)(?:\s+on\s+(\w+))?'
    swap_pattern = r'(?:swap|exchange|trade) (\d+\.?\d*) (\w+) (?:for|to) (\w+)(?:\s+on\s+(\w+))?'
    wrap_pattern = r'(?:wrap|unwrap) (\d+\.?\d*) (\w+)(?: to (\w+))?'
    
    # Information patterns
    price_pattern = r'(?:price|cost|value|worth).* (\w+)(?:\s+on\s+(\w+))?'
    balance_pattern = r'(?:balance|holdings?|portfolio|wallet)'
    gas_pattern = r'(?:gas|fees?|cost).* (?:on )?(\w+)'
    chains_pattern = r'(?:chains?|networks?|supported)'
    
    # Conversational patterns
    greeting_pattern = r'(?:hi|hello|hey|good\s+(?:morning|afternoon|evening)|greetings?)'
    help_pattern = r'help|commands?|what.* (?:can|do)|how.* work'
    thanks_pattern = r'thanks?|thank you|thx|appreciate'
    
    # Check for cross-chain swap requests
    cross_chain_match = re.search(cross_chain_pattern, message)
    if cross_chain_match:
        amount = float(cross_chain_match.group(1))
        from_token = cross_chain_match.group(2).upper()
        from_chain = cross_chain_match.group(3) or 'flare'
        to_chain = cross_chain_match.group(4).lower()
        
        # Map common chain aliases
        chain_aliases = {
            'eth': 'ethereum',
            'matic': 'polygon',
            'poly': 'polygon',
            'bnb': 'bsc',
            'binance': 'bsc',
            'avax': 'avalanche'
        }
        to_chain = chain_aliases.get(to_chain, to_chain)
        
        # Assume same token on destination chain or ETH as default
        to_token = from_token if from_token in ['USDT', 'USDC'] else 'ETH'
        
        blockchain_service = get_blockchain_service()
        quote = blockchain_service.get_cross_chain_quote(from_chain, to_chain, from_token, to_token, amount)
        
        if 'error' in quote:
            return f"❌ Cross-chain quote failed: {quote['error']}", None
        
        response = f"""🌉 **Cross-Chain Swap Quote:**

**Route:** {quote['from_chain'].title()} → {quote['to_chain'].title()}
**Trade:** {amount} {from_token} → {quote['amount_out']:.6f} {to_token}

**💰 Fees Breakdown:**
• Bridge Fee: ${quote['bridge_fee']:.2f}
• Gas Estimate: ${quote['gas_estimate']:.2f}
• Total Fees: ${quote['total_fee_usd']:.2f}

**📊 Trade Details:**
• Price Impact: {quote['price_impact']:.2f}%
• Est. Time: {quote['estimated_time']}
• Route: {quote['route']['name']}

Would you like me to execute this cross-chain swap? Just say "execute" or "confirm"!"""
        
        return response, f"Cross-chain quote: {amount} {from_token} to {to_token}"
    
    # Check for cross-chain quote requests
    quote_match = re.search(cross_chain_quote_pattern, message)
    if quote_match:
        amount = float(quote_match.group(1))
        from_token = quote_match.group(2).upper()
        from_chain = quote_match.group(3) or 'flare'
        to_chain = quote_match.group(4).lower()
        
        blockchain_service = get_blockchain_service()
        quote = blockchain_service.get_cross_chain_quote(from_chain, to_chain, from_token, from_token, amount)
        
        if 'error' not in quote:
            return f"💰 Cross-chain transfer quote: {amount} {from_token} from {from_chain} to {to_chain} will cost ${quote['total_fee_usd']:.2f} in fees and take approximately {quote['estimated_time']}.", None
        else:
            return f"❌ Unable to get quote: {quote['error']}", None
    
    # Enhanced buy command with chain support
    buy_match = re.search(buy_pattern, message)
    if buy_match:
        amount = float(buy_match.group(1))
        token = buy_match.group(2).upper()
        payment_token = buy_match.group(3).upper() if buy_match.group(3) else None
        chain = buy_match.group(4).lower() if buy_match.group(4) else 'flare'
        
        if chain != 'flare':
            return f"🔗 I can help you buy {token} on {chain.title()}! However, cross-chain purchases require connecting to that network. For now, I'll execute this on Flare Network. Use 'bridge' commands for cross-chain transfers.", None
        
        result = execute_mock_trade('buy', token, amount, payment_token)
        
        if result['success']:
            return f"""✅ **Purchase Successful!** 

Bought **{amount} {token}** for ${amount * Token.query.filter_by(symbol=token).first().price:.2f}! 🎉

Your new {token} tokens are now safely in your portfolio. Want to see your updated balance? Just ask me "show balance"!""", f"Bought {amount} {token}"
        else:
            return f"❌ Purchase failed: {result['message']} 😔 Don't worry though, try adjusting the amount or check your balance!", None
    
    # Enhanced sell command
    sell_match = re.search(sell_pattern, message)
    if sell_match:
        amount = float(sell_match.group(1))
        token = sell_match.group(2).upper()
        chain = sell_match.group(3).lower() if sell_match.group(3) else 'flare'
        
        result = execute_mock_trade('sell', token, amount)
        
        if result['success']:
            return f"""💰 **Sale Completed!**

Successfully sold **{amount} {token}** for ${amount * Token.query.filter_by(symbol=token).first().price:.2f}! 

The funds have been added to your account. Great timing on that trade! 📈""", f"Sold {amount} {token}"
        else:
            return f"❌ Sale failed: {result['message']} 😕 This might be due to insufficient balance or market conditions.", None
    
    # Enhanced swap command
    swap_match = re.search(swap_pattern, message)
    if swap_match:
        amount = float(swap_match.group(1))
        from_token = swap_match.group(2).upper()
        to_token = swap_match.group(3).upper() 
        chain = swap_match.group(4).lower() if swap_match.group(4) else 'flare'
        
        result = execute_mock_trade('swap', to_token, amount, from_token)
        
        if result['success']:
            return f"""🔄 **Swap Executed Successfully!**

Swapped **{amount} {from_token}** → **{to_token}** on {chain.title()} Network! 

This was a smart move! The swap has been completed and your new tokens are ready. Want to see how this affected your portfolio? 📊""", f"Swapped {amount} {from_token} for {to_token}"
        else:
            return f"❌ Swap failed: {result['message']} 🤔 This could be due to insufficient liquidity or balance issues.", None
    
    # Enhanced wrap/unwrap
    wrap_match = re.search(wrap_pattern, message)
    if wrap_match:
        amount = float(wrap_match.group(1))
        from_token = wrap_match.group(2).upper()
        to_token = wrap_match.group(3).upper() if wrap_match.group(3) else ('WFLR' if from_token == 'FLR' else 'FLR')
        
        if (from_token == 'FLR' and to_token == 'WFLR') or (from_token == 'WFLR' and to_token == 'FLR'):
            result = execute_mock_trade('swap', to_token, amount, from_token)
            if result['success']:
                action = "Wrapped" if to_token == 'WFLR' else "Unwrapped"
                return f"""🔄 **{action} Successfully!**

{action} **{amount} {from_token}** to **{to_token}**! 

Your {to_token} tokens are now ready for DeFi protocols! Wrapping/unwrapping is essential for participating in the DeFi ecosystem. 🌟""", f"{action} {amount} {from_token} to {to_token}"
            else:
                return f"❌ {result['message']} 😞", None
        else:
            return f"❌ I can only wrap/unwrap between FLR and WFLR tokens. These are 1:1 conversions that make FLR compatible with DeFi protocols! 🔧", None
    
    # Enhanced price queries
    price_match = re.search(price_pattern, message)
    if price_match:
        token_symbol = price_match.group(1).upper()
        chain = price_match.group(2).lower() if price_match.group(2) else 'flare'
        token = Token.query.filter_by(symbol=token_symbol).first()
        
        if token:
            change_emoji = "📈" if token.change_24h >= 0 else "📉"
            trend = "bullish" if token.change_24h > 2 else "bearish" if token.change_24h < -2 else "stable"
            
            return f"""💰 **{token.name} ({token.symbol}) Price:**

**${token.price:.6f}** {change_emoji} **{token.change_24h:+.2f}%** (24h)

The market is looking **{trend}** for {token.symbol} right now! {
    "Great time to buy the dip! 🎯" if token.change_24h < -5 else 
    "Nice gains! 🚀" if token.change_24h > 5 else 
    "Steady as she goes! ⚖️"
}

Want to make a trade? Just tell me what you'd like to do!""", None
        else:
            return f"""❌ **Token {token_symbol} not found!** 🤔

**Supported tokens:** WFLR, FLR, MATIC, METIS, USDT, ETH, APE

Try asking about one of these, or let me know if you'd like me to add support for more tokens! I'm always learning! 🧠✨""", None
    
    # Enhanced balance/portfolio query
    if re.search(balance_pattern, message):
        from models import Portfolio
        portfolio_items = Portfolio.query.filter(Portfolio.balance > 0).all()
        
        if not portfolio_items:
            return """📊 **Your Portfolio**

Your portfolio is currently empty! 💼✨

**Ready to start trading?** Here are some ideas:
• Buy some WFLR to get started
• Try "buy 100 WFLR" 
• Ask me "what tokens can I trade?"

I'm here to help you build an amazing portfolio! 🌟""", None
        
        portfolio_text = "📊 **Your Portfolio:**\n\n"
        total_value = 0
        best_performer = None
        best_performance = -float('inf')
        
        for item in portfolio_items:
            token = Token.query.filter_by(symbol=item.token_symbol).first()
            if token:
                value = item.balance * token.price
                total_value += value
                profit_loss = value - (item.balance * item.avg_buy_price)
                pl_percent = (profit_loss / (item.balance * item.avg_buy_price) * 100) if item.avg_buy_price > 0 else 0
                
                if pl_percent > best_performance:
                    best_performance = pl_percent
                    best_performer = token.symbol
                
                emoji = "📈" if pl_percent > 0 else "📉" if pl_percent < 0 else "➡️"
                portfolio_text += f"• **{item.balance:.4f} {item.token_symbol}** = ${value:.2f} {emoji} {pl_percent:+.1f}%\n"
        
        portfolio_text += f"\n💎 **Total Value: ${total_value:.2f}**"
        
        if best_performer:
            portfolio_text += f"\n🏆 **Best Performer: {best_performer}** (+{best_performance:.1f}%)"
        
        portfolio_text += f"\n\n{'🎉 Great portfolio! Keep up the good work!' if total_value > 1000 else '📈 Nice start! Ready to grow this portfolio?'}"
        
        return portfolio_text, None
    
    # Gas and fee information
    gas_match = re.search(gas_pattern, message)
    if gas_match:
        chain = gas_match.group(1).lower()
        chain_aliases = {'eth': 'ethereum', 'matic': 'polygon', 'bnb': 'bsc'}
        chain = chain_aliases.get(chain, chain)
        
        gas_info = {
            'ethereum': {'cost': '$20-80', 'speed': 'Fast', 'note': 'High but secure'},
            'flare': {'cost': '$0.01-0.10', 'speed': 'Very Fast', 'note': 'Ultra-low fees!'},
            'polygon': {'cost': '$0.001-0.01', 'speed': 'Fast', 'note': 'Great for small trades'},
            'bsc': {'cost': '$0.10-0.50', 'speed': 'Fast', 'note': 'Good middle ground'}
        }
        
        info = gas_info.get(chain)
        if info:
            return f"""⛽ **Gas Fees on {chain.title()}:**

💰 **Cost:** {info['cost']}
⚡ **Speed:** {info['speed']}
📝 **Note:** {info['note']}

{f"Flare Network offers some of the lowest fees in crypto! Perfect for frequent trading. 🎯" if chain == 'flare' else f"Consider using Flare Network for lower fees when possible!"}""", None
    
    # Supported chains info
    if re.search(chains_pattern, message):
        return """🌐 **Supported Networks & Features:**

**🔥 Flare Network** (Primary)
• Native FLR & WFLR tokens
• Ultra-low gas fees ($0.01)
• FTSO price oracles
• ⭐ Best for: All trading activities

**🔗 Cross-Chain Support:**
• **Ethereum** - Premium DeFi hub
• **Polygon** - Fast & cheap L2
• **BSC** - Binance ecosystem  
• **Avalanche** - High throughput

**🌉 Bridge Features:**
• LayerZero integration
• 1inch aggregator
• Native Flare bridges
• Real-time fee estimation

Want to try a cross-chain swap? Just say something like "bridge 100 USDT to Ethereum"! 🚀""", None
    
    # Greeting responses
    if re.search(greeting_pattern, message):
        greetings = [
            "Hello there! 👋 I'm your friendly Flare Network trading assistant! Ready to explore some DeFi magic? ✨",
            "Hey! 🌟 Great to see you! I'm here to help you navigate the exciting world of cross-chain trading on Flare Network!",
            "Hi! 😊 Welcome back to your trading companion! What amazing trades shall we execute today?",
            "Greetings, trader! 🚀 I'm pumped to help you make some profitable moves in the crypto markets today!"
        ]
        import random
        return random.choice(greetings), None
    
    # Thanks responses
    if re.search(thanks_pattern, message):
        thanks_responses = [
            "You're absolutely welcome! 😊 Happy to help you succeed in crypto trading! 🎯",
            "Anytime! 🌟 That's what I'm here for - making crypto trading easier and more fun!",
            "My pleasure! 💫 Keep those successful trades coming! 📈",
            "Glad I could help! 🤝 Remember, I'm always here when you need trading assistance!"
        ]
        import random
        return random.choice(thanks_responses), None
    
    # Help and capabilities
    if re.search(help_pattern, message):
        return """🤖 **Your AI Trading Assistant - Full Capabilities!**

**💰 Basic Trading:**
• `buy 100 WFLR` - Purchase tokens
• `sell 50 ETH` - Sell tokens  
• `swap 100 USDT for WFLR` - Token swaps
• `wrap 200 FLR to WFLR` - Wrap/unwrap

**🌉 Cross-Chain Trading:**
• `bridge 50 USDT to Ethereum` - Cross-chain transfers
• `quote 100 FLR to Polygon` - Get bridge quotes
• `swap 10 ETH on Ethereum` - Chain-specific trades

**📊 Information & Analysis:**
• `price of ETH` - Real-time prices
• `balance` - Portfolio overview
• `gas fees on Ethereum` - Fee estimates
• `supported chains` - Available networks

**🤖 I'm Conversational!**
I understand natural language, so you can ask me anything like:
• "What's the best way to get USDT on Polygon?"
• "How much would it cost to bridge 500 WFLR to Ethereum?"
• "Show me my portfolio performance"

**🎯 Pro Tips:**
• I provide real-time quotes with fees
• I suggest optimal routes for trades
• I track your portfolio automatically
• I'm always learning and improving!

Ready to make some profitable trades? 🚀""", None
    
    # Market and general crypto questions
    if any(word in message for word in ['market', 'defi', 'crypto', 'blockchain', 'flare', 'oracle']):
        if 'flare' in message or 'ftso' in message or 'oracle' in message:
            return """🔥 **Flare Network - The Oracle Blockchain!**

**What makes Flare special:**
• **FTSO Oracles** - Decentralized price feeds without external dependencies
• **Ultra-low fees** - Trade for pennies, not dollars!
• **EVM Compatible** - All your favorite DeFi tools work here
• **State Connectors** - Prove events from other blockchains

**Why Trade on Flare:**
• 📊 **Accurate Prices** - Real-time data from FTSO oracles
• ⚡ **Lightning Fast** - 1-2 second block times
• 💰 **Cost Effective** - $0.01 average transaction cost
• 🌉 **Cross-Chain Ready** - Built for multi-chain DeFi

**Available Assets:**
• FLR (native token) & WFLR (wrapped for DeFi)
• Bridged ETH, USDT, and other major tokens
• Growing ecosystem of native tokens

Ready to experience the future of DeFi on Flare? Let's start trading! 🚀""", None
        
        elif 'market' in message:
            return """📈 **Crypto Market Insights**

I'm constantly monitoring prices across all supported networks! Here's what I can help you with:

• **Real-time prices** from multiple sources
• **Cross-chain arbitrage** opportunities  
• **Gas fee optimization** across networks
• **Portfolio tracking** and performance analysis

**Current Focus Areas:**
• Flare Network native tokens (FLR/WFLR)
• Major DeFi tokens (ETH, USDT, USDC)
• Cross-chain bridge opportunities

Want to see specific market data? Just ask me about any token price or market conditions! 📊✨""", None
    
    # Advanced features and trading tips
    if any(phrase in message for phrase in ['advanced', 'tips', 'strategy', 'optimize', 'best']):
        return """🎯 **Advanced Trading Tips & Strategies**

**🔥 Flare Network Advantages:**
• Use FTSO oracles for the most accurate pricing
• Take advantage of ultra-low fees for frequent trading
• Bridge assets during low-traffic periods for better rates

**💡 Cross-Chain Optimization:**
• **Small trades (<$100):** Use Polygon or BSC for low fees
• **Large trades (>$10k):** Prefer Ethereum for maximum security
• **DeFi activities:** Flare Network for best fee/security balance

**⚡ Gas Fee Strategies:**
• Monitor gas prices and trade during low-traffic hours
• Batch multiple operations when possible
• Use Layer 2 solutions for cost savings

**🎨 Portfolio Tips:**
• Diversify across chains and tokens
• Keep some stablecoins for opportunities
• Use wrapping/unwrapping strategically for DeFi access

**🌉 Bridge Timing:**
• Check multiple routes for best rates
• Consider time vs. cost trade-offs
• Monitor bridge liquidity before large transfers

Want specific advice for your situation? Just tell me about your trading goals! 🚀""", None
    
    # Fallback conversational responses
    conversational_responses = [
        "I'd love to help you with that! 😊 Could you be more specific? For example, try asking about token prices, executing trades, or checking your portfolio!",
        "Hmm, I'm not quite sure what you're looking for there! 🤔 I'm great at helping with trading, prices, cross-chain swaps, and portfolio management. What would you like to explore?",
        "That's interesting! 💭 I'm specialized in crypto trading and cross-chain operations. Try asking me about buying tokens, checking prices, or bridging assets between chains!",
        "I want to help! 🌟 I understand trading commands, price queries, portfolio questions, and cross-chain operations. What crypto adventure shall we embark on?",
        "Great question! 🎯 I'm your DeFi trading companion. Ask me about token swaps, cross-chain bridges, gas fees, or anything related to trading on Flare Network and beyond!"
    ]
    
    import random
    return random.choice(conversational_responses), None
