"""
GameBus API client for interacting with the GameBus platform.
"""
import requests
import logging
import time
from typing import Dict, List, Optional, Any, Union
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime

from config.credentials import BASE_URL, TOKEN_URL, PLAYER_ID_URL, ACTIVITIES_URL
from config.settings import (
    MAX_RETRIES, 
    REQUEST_TIMEOUT, 
    CONNECT_TIMEOUT,
    RETRY_DELAY,
    VALID_GAME_DESCRIPTORS
)

# Set up logging
logger = logging.getLogger(__name__)

class GameBusClient:
    """
    Client for interacting with the GameBus API.
    """
    
    def __init__(self, authcode: str):
        """
        Initialize the GameBus client.
        
        Args:
            authcode: Authentication code for GameBus API
        """
        self.authcode = authcode
        self.base_url = BASE_URL
        self.token_url = TOKEN_URL
        self.player_id_url = PLAYER_ID_URL
        self.activities_url = ACTIVITIES_URL
        
        # Configure session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=MAX_RETRIES,
            backoff_factor=RETRY_DELAY,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def _make_request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        """
        Make an HTTP request with proper timeout and retry handling.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL to request
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object or None if request failed
        """
        try:
            # Set timeouts if not provided
            if 'timeout' not in kwargs:
                kwargs['timeout'] = (CONNECT_TIMEOUT, REQUEST_TIMEOUT)
            
            # Log the full URL and parameters
            if 'params' in kwargs:
                full_url = f"{url}?{requests.compat.urlencode(kwargs['params'])}"
                logger.debug(f"Making {method} request to: {full_url}")
            else:
                logger.debug(f"Making {method} request to: {url}")
            
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.Timeout as e:
            logger.error(f"Request timed out: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return None
    
    def get_player_token(self, username: str, password: str) -> Optional[str]:
        """
        Get an access token for the player.
        
        Args:
            username: Player's username/email
            password: Player's password
            
        Returns:
            Access token or None if authentication failed
        """
        payload = {
            "grant_type": "password",
            "username": username,
            "password": password
        }
        headers = {
            "Authorization": f"Basic {self.authcode}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        
        response = self._make_request("POST", self.token_url, headers=headers, data=payload)
        if response:
            token = response.json().get("access_token")
            logger.info("Token fetched successfully")
            return token
        return None
    
    def get_player_id(self, token: str) -> Optional[int]:
        """
        Get the player ID using the access token.
        
        Args:
            token: Access token
            
        Returns:
            Player ID or None if retrieval failed
        """
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        response = self._make_request("GET", self.player_id_url, headers=headers)
        if response:
            player_data = response.json()
            player_id = player_data.get("player", {}).get("id")
            logger.info("Player ID fetched successfully")
            return player_id
        return None
    
    def get_player_data(self, token: str, player_id: int, game_descriptor: str, 
                       page_size: int = 50, start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get player data for a specific game descriptor.
        
        Args:
            token: Access token
            player_id: Player ID
            game_descriptor: Type of data to retrieve (e.g., "GEOFENCE", "LOG_MOOD")
            page_size: Number of items per page
            start_date: Optional start date for filtering data
            end_date: Optional end date for filtering data
            
        Returns:
            List of player data points
        """
        if game_descriptor not in VALID_GAME_DESCRIPTORS:
            raise ValueError(f"Invalid game_descriptor. Valid values are: {', '.join(VALID_GAME_DESCRIPTORS)}")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Start with base URL
        base_url = f"{self.base_url}/players/{player_id}/activities"
        
        # Build query parameters
        params = {
            "sort": "-date",
            "size": page_size
        }
        
        # Add game descriptor filter
        if game_descriptor == "SELFREPORT":
            params["excludedGds"] = ""
        else:
            params["gds"] = game_descriptor
        
        # Add date filtering parameters if provided
        if start_date:
            start_timestamp = int(start_date.timestamp() * 1000)
            params["from"] = start_timestamp
            logger.info(f"Filtering data from: {start_date} (timestamp: {start_timestamp})")
        
        if end_date:
            end_timestamp = int(end_date.timestamp() * 1000)
            params["to"] = end_timestamp
            logger.info(f"Filtering data to: {end_date} (timestamp: {end_timestamp})")
        
        all_player_data = []
        page = 0
        
        while True:
            # Add page parameter
            params["page"] = page
            
            # Make request with parameters
            response = self._make_request("GET", base_url, headers=headers, params=params)
            
            if not response:
                logger.error(f"Failed to retrieve data for page {page}")
                break
            
            player_data = response.json()
            if not player_data:
                break
            
            # Log the first item's date for debugging
            if player_data and len(player_data) > 0:
                first_item_date = datetime.fromtimestamp(player_data[0].get('date', 0) / 1000)
                logger.info(f"First item date on page {page}: {first_item_date}")
            
            all_player_data.extend(player_data)
            logger.info(f"Successfully retrieved page {page} with {len(player_data)} items")
            page += 1
            
            # Add a small delay between requests to avoid overwhelming the API
            time.sleep(0.5)
        
        logger.info(f"Total data points fetched: {len(all_player_data)}")
        return all_player_data 