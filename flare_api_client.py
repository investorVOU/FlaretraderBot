"""
Direct API client for Flare Network dev tools
Integrates with official APIs from dev.flare.network
"""

import os
import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class FlareAPIClient:
    """Client for direct API access to Flare Network services"""
    
    def __init__(self):
        self.base_url = "https://dev.flare.network/api"
        self.ftso_endpoint = "https://api.flare.network/ftso/v1"
        self.fdc_endpoint = "https://api.flare.network/fdc/v1"
        
        # API configuration
        self.timeout = 10
        self.headers = {
            'User-Agent': 'FlareTrading/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def get_ftso_feed_data(self, feeds: List[str] = None) -> Dict[str, Any]:
        """
        Get live FTSO feed data directly from Flare Network
        """
        try:
            if feeds is None:
                feeds = ['FLR/USD', 'ETH/USD', 'BTC/USD', 'USDT/USD']
            
            # This would be the actual FTSO API endpoint once available
            url = f"{self.ftso_endpoint}/feeds"
            params = {'symbols': ','.join(feeds)}
            
            response = requests.get(url, params=params, headers=self.headers, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Retrieved FTSO data for {len(feeds)} feeds")
                return data
            else:
                logger.warning(f"FTSO API request failed: {response.status_code}")
                return {}
                
        except requests.RequestException as e:
            logger.error(f"FTSO API connection error: {e}")
            return {}
        except Exception as e:
            logger.error(f"FTSO API error: {e}")
            return {}
    
    def get_network_stats(self) -> Dict[str, Any]:
        """
        Get Flare Network statistics and metrics
        """
        try:
            url = f"{self.base_url}/network/stats"
            
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Network stats API failed: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"Network stats error: {e}")
            return {}
    
    def validate_flare_address(self, address: str) -> bool:
        """
        Validate Flare Network address format
        """
        try:
            # Basic validation for Flare address format
            if not address.startswith('0x'):
                return False
            
            if len(address) != 42:
                return False
            
            # Try to convert to checksum - will throw if invalid
            int(address, 16)
            return True
            
        except ValueError:
            return False
        except Exception as e:
            logger.error(f"Address validation error: {e}")
            return False
    
    def get_token_info(self, token_address: str) -> Optional[Dict[str, Any]]:
        """
        Get token information from Flare Network
        """
        try:
            url = f"{self.base_url}/tokens/{token_address}"
            
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Token info API failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Token info error: {e}")
            return None
    
    def get_fdc_attestation_types(self) -> List[str]:
        """
        Get available FDC attestation types
        """
        return [
            'AddressValidity',
            'EVMTransaction', 
            'JsonApi'
        ]
    
    def submit_fdc_request(self, attestation_type: str, request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Submit an attestation request to FDC
        """
        try:
            url = f"{self.fdc_endpoint}/request"
            
            payload = {
                'attestationType': attestation_type,
                'requestData': request_data,
                'timestamp': int(datetime.now().timestamp())
            }
            
            response = requests.post(url, json=payload, headers=self.headers, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"FDC request failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"FDC request error: {e}")
            return None

# Global client instance
flare_api = FlareAPIClient()

def get_flare_api() -> FlareAPIClient:
    """Get the Flare API client instance"""
    return flare_api