"""
Blockchain Service for Flare Network Integration
Handles real onchain interactions, price feeds, and smart contract calls
"""

import os
import logging
import requests
from web3 import Web3
from typing import Dict, List, Optional, Tuple
from models import Token, Portfolio, Trade
from app import db

logger = logging.getLogger(__name__)

class FlareBlockchainService:
    """Service to interact with Flare Network and retrieve real data using FTSO and FDC"""
    
    def __init__(self):
        # Flare Network RPC endpoints (official from dev.flare.network)
        self.flare_rpc = os.environ.get('FLARE_RPC_URL', 'https://flare-api.flare.network/ext/C/rpc')
        self.coston2_rpc = os.environ.get('COSTON2_RPC_URL', 'https://coston2-api.flare.network/ext/C/rpc')
        self.songbird_rpc = os.environ.get('SONGBIRD_RPC_URL', 'https://songbird-api.flare.network/ext/C/rpc')
        
        # Initialize Web3 connection to Flare mainnet
        self.w3 = Web3(Web3.HTTPProvider(self.flare_rpc))
        
        # FTSOv2 Contract Registry (official from dev.flare.network)
        # Using official ContractRegistry address for Flare mainnet
        self.contract_registry = os.environ.get('CONTRACT_REGISTRY', '0xaD67FE66660Fb8dFE9d6b1b4240d8650e30F6019')
        
        # FDC (Flare Data Connector) endpoints
        self.fdc_data_availability = 'https://flr-data-availability.flare.network/api/v1/fdc'
        self.coston2_fdc_data_availability = 'https://ctn2-data-availability.flare.network/api/v1/fdc'
        
        # Real token contract addresses on Flare Network
        self.token_addresses = {
            'WFLR': '0x1D80c49BbBCd1C0911346656B529DF9E5c2F783d',  # Official Wrapped FLR
            'FLR': '0x0000000000000000000000000000000000000001',   # Native FLR (special address)
        }
        
        # DEX Contract Integration
        self.dex_contract_address = os.environ.get('DEX_CONTRACT_ADDRESS', '')
        self.dex_contract_abi = [
            {
                "inputs": [
                    {"name": "tokenIn", "type": "address"},
                    {"name": "tokenOut", "type": "address"},
                    {"name": "amountIn", "type": "uint256"}
                ],
                "name": "swap",
                "outputs": [{"name": "amountOut", "type": "uint256"}],
                "type": "function"
            },
            {
                "inputs": [
                    {"name": "tokenIn", "type": "address"},
                    {"name": "tokenOut", "type": "address"},
                    {"name": "amountIn", "type": "uint256"},
                    {"name": "minReturn", "type": "uint256"},
                    {"name": "oneInchData", "type": "bytes"}
                ],
                "name": "swapWithOneInch",
                "outputs": [{"name": "amountOut", "type": "uint256"}],
                "type": "function"
            },
            {
                "inputs": [{"name": "amount", "type": "uint256"}],
                "name": "swapFLRtoWFLR",
                "outputs": [],
                "type": "function"
            },
            {
                "inputs": [
                    {"name": "tokenIn", "type": "address"},
                    {"name": "amountIn", "type": "uint256"},
                    {"name": "destinationChain", "type": "string"},
                    {"name": "tokenOut", "type": "address"},
                    {"name": "recipient", "type": "address"}
                ],
                "name": "crossChainSwap",
                "outputs": [],
                "type": "function"
            },
            {
                "inputs": [
                    {"name": "tokenA", "type": "address"},
                    {"name": "tokenB", "type": "address"},
                    {"name": "amountA", "type": "uint256"},
                    {"name": "amountB", "type": "uint256"}
                ],
                "name": "addLiquidity",
                "outputs": [],
                "type": "function"
            }
        ]
        
        # FTSO Feed IDs for price data
        self.ftso_feed_ids = {
            'FLR/USD': '0x01464c522f555344000000000000000000000000000000000000000000000000',
            'BTC/USD': '0x0142544320202020000000000000000000000000000000000000000000000000', 
            'ETH/USD': '0x01455448202020200000000000000000000000000000000000000000000000000',
            'XRP/USD': '0x01585250202020200000000000000000000000000000000000000000000000000',
            'USDT/USD': '0x0155534454202020000000000000000000000000000000000000000000000000',
        }
    
    def get_live_prices(self) -> Dict[str, float]:
        """
        Fetch live prices from Flare FTSO oracles
        Falls back to external APIs if FTSO not available
        """
        try:
            # Try to get prices from FTSO first
            ftso_prices = self._get_ftso_prices()
            if ftso_prices:
                return ftso_prices
            
            # Fallback to external price API
            return self._get_external_prices()
            
        except Exception as e:
            logger.error(f"Error fetching live prices: {e}")
            return {}
    
    def _get_ftso_prices(self) -> Dict[str, float]:
        """Get prices from Flare Time Series Oracles (FTSOv2)"""
        try:
            if not self.w3.is_connected():
                logger.warning("Web3 not connected to Flare network")
                return {}
            
            # FTSOv2 Interface ABI (official from dev.flare.network)
            ftso_v2_abi = [
                {
                    "inputs": [{"name": "_feedIds", "type": "bytes21[]"}],
                    "name": "getFeedsById",
                    "outputs": [
                        {"name": "_values", "type": "uint256[]"},
                        {"name": "_decimals", "type": "int8[]"},
                        {"name": "_timestamp", "type": "uint64"}
                    ],
                    "type": "function"
                }
            ]
            
            # Get FTSOv2 contract from registry
            registry_abi = [
                {
                    "inputs": [],
                    "name": "getFtsoV2",
                    "outputs": [{"name": "", "type": "address"}],
                    "type": "function"
                }
            ]
            
            registry_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.contract_registry),
                abi=registry_abi
            )
            
            ftso_v2_address = registry_contract.functions.getFtsoV2().call()
            
            ftso_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(ftso_v2_address),
                abi=ftso_v2_abi
            )
            
            # Get feed IDs as bytes
            feed_ids = [Web3.to_bytes(hexstr=feed_id) for feed_id in self.ftso_feed_ids.values()]
            
            # Call getFeedsById
            values, decimals, timestamp = ftso_contract.functions.getFeedsById(feed_ids).call()
            
            # Convert to price dictionary
            prices = {}
            feed_symbols = list(self.ftso_feed_ids.keys())
            
            for i, (symbol, value, decimal) in enumerate(zip(feed_symbols, values, decimals)):
                # Convert from feed format to USD price
                token_symbol = symbol.split('/')[0]
                price = value / (10 ** abs(decimal))
                
                # Map to our token symbols
                if token_symbol == 'FLR':
                    prices['FLR'] = price
                    prices['WFLR'] = price  # WFLR should have same price as FLR
                elif token_symbol == 'BTC':
                    # We don't have BTC but use for reference
                    pass
                elif token_symbol == 'ETH':
                    prices['ETH'] = price
                elif token_symbol == 'XRP':
                    # Map to other tokens - this is simplified
                    prices['MATIC'] = price * 0.0003  # Rough conversion
                elif token_symbol == 'USDT':
                    prices['USDT'] = price
            
            logger.info(f"Retrieved FTSO prices: {prices}")
            return prices
            
        except Exception as e:
            logger.error(f"FTSO price fetch error: {e}")
            return {}
    
    def _get_external_prices(self) -> Dict[str, float]:
        """Use real external price APIs including CoinGecko"""
        try:
            # Use CoinGecko API for real price data
            url = "https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': 'flare-networks,wrapped-flare,ethereum,matic-network,metis-token,apecoin,tether',
                'vs_currencies': 'usd'
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                prices = {
                    'FLR': data.get('flare-networks', {}).get('usd', 0),
                    'WFLR': data.get('wrapped-flare', {}).get('usd', 0) or data.get('flare-networks', {}).get('usd', 0),
                    'ETH': data.get('ethereum', {}).get('usd', 0),
                    'MATIC': data.get('matic-network', {}).get('usd', 0),
                    'METIS': data.get('metis-token', {}).get('usd', 0),
                    'APE': data.get('apecoin', {}).get('usd', 0),
                    'USDT': data.get('tether', {}).get('usd', 1.0),
                }
                
                logger.info(f"Retrieved external API prices: {prices}")
                return prices
                
        except Exception as e:
            logger.error(f"External API price fetch error: {e}")
        
        return {}
    
    def update_token_prices(self):
        """Update database with live prices"""
        try:
            live_prices = self.get_live_prices()
            
            for symbol, price in live_prices.items():
                token = Token.query.filter_by(symbol=symbol).first()
                if token:
                    old_price = token.price
                    token.price = price
                    token.change_24h = ((price - old_price) / old_price * 100) if old_price > 0 else 0
            
            db.session.commit()
            logger.info("Token prices updated successfully")
            
        except Exception as e:
            logger.error(f"Error updating token prices: {e}")
            db.session.rollback()
    
    def get_wallet_balance(self, wallet_address: str, token_symbol: str) -> float:
        """Get real wallet balance for a token"""
        try:
            if not self.w3.is_connected():
                return 0.0
            
            token_address = self.token_addresses.get(token_symbol)
            if not token_address or token_address == '0x0000000000000000000000000000000000000000':
                return 0.0
            
            # ERC20 token ABI (balanceOf function)
            erc20_abi = [
                {
                    "inputs": [{"name": "_owner", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "balance", "type": "uint256"}],
                    "type": "function"
                }
            ]
            
            contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=erc20_abi
            )
            
            balance_wei = contract.functions.balanceOf(
                Web3.to_checksum_address(wallet_address)
            ).call()
            
            # Convert from wei to tokens (assuming 18 decimals)
            balance = balance_wei / (10 ** 18)
            return balance
            
        except Exception as e:
            logger.error(f"Error getting wallet balance: {e}")
            return 0.0
    
    def get_fdc_attestation_data(self, attestation_type: str, request_data: dict) -> Optional[dict]:
        """
        Get attestation data from Flare Data Connector (FDC)
        Supports AddressValidity, EVMTransaction, and JsonApi attestation types
        """
        try:
            # FDC Data Availability endpoint
            url = f"{self.fdc_data_availability}/proof-by-request-round"
            
            headers = {
                'accept': 'application/json',
                'Content-Type': 'application/json',
                'x-api-key': os.environ.get('FDC_API_KEY', '00000000-0000-0000-0000-000000000000')
            }
            
            # Example request for address validation
            payload = {
                "votingRoundId": request_data.get('votingRoundId', 1028678),
                "requestBytes": request_data.get('requestBytes', '')
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"FDC request failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting FDC attestation data: {e}")
            return None
    
    def validate_address_with_fdc(self, address: str, network: str) -> bool:
        """
        Validate an address using FDC AddressValidity attestation
        """
        try:
            request_data = {
                'votingRoundId': 1028678,  # This would be dynamically calculated
                'requestBytes': self._encode_address_validation_request(address, network)
            }
            
            attestation_data = self.get_fdc_attestation_data('AddressValidity', request_data)
            
            if attestation_data and attestation_data.get('status') == 'VALID':
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error validating address with FDC: {e}")
            return False
    
    def _encode_address_validation_request(self, address: str, network: str) -> str:
        """
        Encode address validation request for FDC
        This would use the proper ABI encoding for the request
        """
        # Simplified encoding - real implementation would use proper ABI encoding
        return f"0x4164647265737356616c696469747900000000000000000000000000000000{address.replace('0x', '')}"
    
    def execute_dex_swap(self, from_token: str, to_token: str, amount: float, wallet_address: str, use_oneinch: bool = False) -> Tuple[bool, str]:
        """
        Execute a swap using our DEX contract with optional 1inch aggregation
        """
        try:
            if not self.w3.is_connected():
                return False, "Web3 not connected to Flare network"
            
            if not self.dex_contract_address:
                return False, "DEX contract not deployed"
            
            # Validate wallet address
            is_valid = self.validate_address_with_fdc(wallet_address, 'flare')
            if not is_valid:
                return False, f"Invalid wallet address: {wallet_address}"
            
            # Get token addresses
            from_token_address = self.token_addresses.get(from_token)
            to_token_address = self.token_addresses.get(to_token)
            
            if not from_token_address or not to_token_address:
                return False, f"Token addresses not found for {from_token} or {to_token}"
            
            # Create contract instance
            dex_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.dex_contract_address),
                abi=self.dex_contract_abi
            )
            
            # Convert amount to wei
            amount_wei = Web3.to_wei(amount, 'ether')
            
            if from_token == 'FLR' and to_token == 'WFLR':
                # Special case for FLR to WFLR wrapping
                tx_data = dex_contract.functions.swapFLRtoWFLR(amount_wei).build_transaction({
                    'from': wallet_address,
                    'gas': 100000,
                    'gasPrice': Web3.to_wei('25', 'gwei'),
                    'nonce': self.w3.eth.get_transaction_count(wallet_address)
                })
                
                logger.info(f"Built FLR->WFLR wrap transaction: {amount} FLR")
                return True, f"Wrap transaction ready: {amount} FLR → WFLR"
                
            elif use_oneinch:
                # Use 1inch aggregator
                oneinch_data = self._get_oneinch_swap_data(from_token, to_token, amount)
                if not oneinch_data:
                    return False, "Failed to get 1inch swap data"
                
                min_return = int(oneinch_data['toAmount']) * 95 // 100  # 5% slippage
                
                tx_data = dex_contract.functions.swapWithOneInch(
                    Web3.to_checksum_address(from_token_address),
                    Web3.to_checksum_address(to_token_address),
                    amount_wei,
                    min_return,
                    oneinch_data['tx']['data']
                ).build_transaction({
                    'from': wallet_address,
                    'gas': 300000,
                    'gasPrice': Web3.to_wei('25', 'gwei'),
                    'nonce': self.w3.eth.get_transaction_count(wallet_address)
                })
                
                logger.info(f"Built 1inch swap transaction: {amount} {from_token} -> {to_token}")
                return True, f"1inch swap ready: {amount} {from_token} → {to_token}"
                
            else:
                # Use internal liquidity pool
                tx_data = dex_contract.functions.swap(
                    Web3.to_checksum_address(from_token_address),
                    Web3.to_checksum_address(to_token_address),
                    amount_wei
                ).build_transaction({
                    'from': wallet_address,
                    'gas': 200000,
                    'gasPrice': Web3.to_wei('25', 'gwei'),
                    'nonce': self.w3.eth.get_transaction_count(wallet_address)
                })
                
                logger.info(f"Built internal swap transaction: {amount} {from_token} -> {to_token}")
                return True, f"Internal swap ready: {amount} {from_token} → {to_token}"
            
        except Exception as e:
            logger.error(f"Error building DEX swap: {e}")
            return False, f"DEX swap failed: {str(e)}"
    
    def execute_cross_chain_swap(self, from_token: str, amount: float, destination_chain: str, to_token: str, wallet_address: str, recipient: str) -> Tuple[bool, str]:
        """
        Execute a cross-chain swap via bridge
        """
        try:
            if not self.w3.is_connected():
                return False, "Web3 not connected to Flare network"
            
            if not self.dex_contract_address:
                return False, "DEX contract not deployed"
            
            from_token_address = self.token_addresses.get(from_token)
            to_token_address = self.token_addresses.get(to_token, "0x0000000000000000000000000000000000000000")
            
            if not from_token_address:
                return False, f"Token address not found for {from_token}"
            
            dex_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.dex_contract_address),
                abi=self.dex_contract_abi
            )
            
            amount_wei = Web3.to_wei(amount, 'ether')
            
            tx_data = dex_contract.functions.crossChainSwap(
                Web3.to_checksum_address(from_token_address),
                amount_wei,
                destination_chain,
                Web3.to_checksum_address(to_token_address),
                Web3.to_checksum_address(recipient)
            ).build_transaction({
                'from': wallet_address,
                'gas': 400000,
                'gasPrice': Web3.to_wei('25', 'gwei'),
                'nonce': self.w3.eth.get_transaction_count(wallet_address)
            })
            
            logger.info(f"Built cross-chain swap: {amount} {from_token} -> {destination_chain}")
            return True, f"Cross-chain swap ready: {amount} {from_token} → {destination_chain}"
            
        except Exception as e:
            logger.error(f"Error building cross-chain swap: {e}")
            return False, f"Cross-chain swap failed: {str(e)}"
    
    def add_liquidity(self, token_a: str, token_b: str, amount_a: float, amount_b: float, wallet_address: str) -> Tuple[bool, str]:
        """
        Add liquidity to a trading pair
        """
        try:
            if not self.w3.is_connected():
                return False, "Web3 not connected to Flare network"
            
            if not self.dex_contract_address:
                return False, "DEX contract not deployed"
            
            token_a_address = self.token_addresses.get(token_a)
            token_b_address = self.token_addresses.get(token_b)
            
            if not token_a_address or not token_b_address:
                return False, f"Token addresses not found for {token_a} or {token_b}"
            
            dex_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.dex_contract_address),
                abi=self.dex_contract_abi
            )
            
            amount_a_wei = Web3.to_wei(amount_a, 'ether')
            amount_b_wei = Web3.to_wei(amount_b, 'ether')
            
            tx_data = dex_contract.functions.addLiquidity(
                Web3.to_checksum_address(token_a_address),
                Web3.to_checksum_address(token_b_address),
                amount_a_wei,
                amount_b_wei
            ).build_transaction({
                'from': wallet_address,
                'gas': 250000,
                'gasPrice': Web3.to_wei('25', 'gwei'),
                'nonce': self.w3.eth.get_transaction_count(wallet_address)
            })
            
            logger.info(f"Built add liquidity: {amount_a} {token_a} + {amount_b} {token_b}")
            return True, f"Add liquidity ready: {amount_a} {token_a} + {amount_b} {token_b}"
            
        except Exception as e:
            logger.error(f"Error building add liquidity: {e}")
            return False, f"Add liquidity failed: {str(e)}"
    
    def _get_oneinch_swap_data(self, from_token: str, to_token: str, amount: float) -> Optional[dict]:
        """
        Get swap data from 1inch API
        """
        try:
            # 1inch API for Flare (chainId 14)
            url = "https://api.1inch.io/v5.0/14/swap"
            
            from_token_address = self.token_addresses.get(from_token)
            to_token_address = self.token_addresses.get(to_token)
            
            if not from_token_address or not to_token_address:
                return None
            
            params = {
                'fromTokenAddress': from_token_address,
                'toTokenAddress': to_token_address,
                'amount': str(Web3.to_wei(amount, 'ether')),
                'fromAddress': self.dex_contract_address,
                'slippage': 1,
                'disableEstimate': True
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"1inch API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting 1inch data: {e}")
            return None
    
    def execute_swap_on_enosys(self, from_token: str, to_token: str, amount: float, wallet_address: str) -> Tuple[bool, str]:
        """
        Legacy method - redirect to new DEX swap
        """
        return self.execute_dex_swap(from_token, to_token, amount, wallet_address, use_oneinch=False)

# Global service instance
blockchain_service = FlareBlockchainService()

def get_blockchain_service() -> FlareBlockchainService:
    """Get the blockchain service instance"""
    return blockchain_service