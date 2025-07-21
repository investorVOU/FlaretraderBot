"""
Wallet Service for WalletConnect Integration
Handles wallet connections and user authentication
"""

import os
import logging
from typing import Optional, Dict, Any
from flask import session, request

logger = logging.getLogger(__name__)

class WalletService:
    """Service to handle wallet connections via WalletConnect"""
    
    def __init__(self):
        # WalletConnect configuration
        self.project_id = os.environ.get('WALLETCONNECT_PROJECT_ID', '')
        self.app_name = "Flare Trading Bot"
        self.app_description = "AI-powered trading on Flare Network"
        self.app_url = os.environ.get('REPLIT_DEV_DOMAIN', 'localhost:5000')
        self.app_icons = ["https://avatars.githubusercontent.com/u/37784886"]
        
        # Supported chains (Flare Network)
        self.supported_chains = {
            'flare': {
                'chainId': 14,
                'name': 'Flare Network',
                'currency': 'FLR',
                'explorerUrl': 'https://flare-explorer.flare.network/',
                'rpcUrl': 'https://flare-api.flare.network/ext/C/rpc'
            },
            'coston': {
                'chainId': 16,
                'name': 'Coston Testnet',
                'currency': 'C2FLR',
                'explorerUrl': 'https://coston-explorer.flare.network/',
                'rpcUrl': 'https://coston-api.flare.network/ext/C/rpc'
            }
        }
    
    def get_wallet_config(self) -> Dict[str, Any]:
        """Get WalletConnect configuration for frontend"""
        return {
            'projectId': self.project_id,
            'metadata': {
                'name': self.app_name,
                'description': self.app_description,
                'url': f"https://{self.app_url}",
                'icons': self.app_icons
            },
            'chains': list(self.supported_chains.values())
        }
    
    def connect_wallet(self, wallet_address: str, chain_id: int) -> bool:
        """Store wallet connection in session"""
        try:
            # Validate wallet address format
            if not wallet_address.startswith('0x') or len(wallet_address) != 42:
                return False
            
            # Validate chain ID
            valid_chains = [chain['chainId'] for chain in self.supported_chains.values()]
            if chain_id not in valid_chains:
                return False
            
            # Store in session
            session['wallet_address'] = wallet_address
            session['chain_id'] = chain_id
            session['wallet_connected'] = True
            
            logger.info(f"Wallet connected: {wallet_address} on chain {chain_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error connecting wallet: {e}")
            return False
    
    def disconnect_wallet(self):
        """Clear wallet connection from session"""
        try:
            session.pop('wallet_address', None)
            session.pop('chain_id', None)
            session.pop('wallet_connected', None)
            logger.info("Wallet disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting wallet: {e}")
    
    def get_connected_wallet(self) -> Optional[str]:
        """Get currently connected wallet address"""
        if session.get('wallet_connected'):
            return session.get('wallet_address')
        return None
    
    def is_wallet_connected(self) -> bool:
        """Check if a wallet is connected"""
        return session.get('wallet_connected', False)
    
    def get_chain_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the connected chain"""
        if not self.is_wallet_connected():
            return None
        
        chain_id = session.get('chain_id')
        for chain_info in self.supported_chains.values():
            if chain_info['chainId'] == chain_id:
                return chain_info
        return None
    
    def sign_message(self, message: str, wallet_address: str) -> Optional[str]:
        """
        Request message signing from connected wallet
        This would be handled on the frontend with WalletConnect
        """
        try:
            # In a real implementation, this would:
            # 1. Send signing request to frontend
            # 2. Frontend uses WalletConnect to request signature
            # 3. User signs in their wallet
            # 4. Signature is returned to backend
            
            # For now, return a mock signature
            if self.get_connected_wallet() == wallet_address:
                return f"0xmocksignature{hash(message)}"
            return None
            
        except Exception as e:
            logger.error(f"Error signing message: {e}")
            return None

# Global service instance
wallet_service = WalletService()

def get_wallet_service() -> WalletService:
    """Get the wallet service instance"""
    return wallet_service

def require_wallet_connection():
    """Decorator to require wallet connection for routes"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not wallet_service.is_wallet_connected():
                return {"error": "Wallet connection required"}, 401
            return func(*args, **kwargs)
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator