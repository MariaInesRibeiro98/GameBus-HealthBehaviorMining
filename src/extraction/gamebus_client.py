"""
GameBus API client for interacting with the GameBus platform.
"""
import requests
import logging
from typing import Dict, List, Optional, Any, Union

from config.credentials import BASE_URL, TOKEN_URL, PLAYER_ID_URL, ACTIVITIES_URL
from config.settings import MAX_RETRIES, REQUEST_TIMEOUT, VALID_GAME_DESCRIPTORS

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
        
        try:
            response = requests.post(self.token_url, headers=headers, data=payload, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            token = response.json().get("access_token")
            logger.info("Token fetched successfully")
            return token
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get player token: {e}")
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
        
        try:
            response = requests.get(self.player_id_url, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            player_data = response.json()
            player_id = player_data.get("player", {}).get("id")
            logger.info("Player ID fetched successfully")
            return player_id
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get player ID: {e}")
            return None
    
    def get_player_data(self, token: str, player_id: int, game_descriptor: str, 
                       page_size: int = 50) -> List[Dict[str, Any]]:
        """
        Get player data for a specific game descriptor.
        
        Args:
            token: Access token
            player_id: Player ID
            game_descriptor: Type of data to retrieve (e.g., "GEOFENCE", "LOG_MOOD")
            page_size: Number of items per page
            
        Returns:
            List of player data points
        """
        if game_descriptor not in VALID_GAME_DESCRIPTORS:
            raise ValueError(f"Invalid game_descriptor. Valid values are: {', '.join(VALID_GAME_DESCRIPTORS)}")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Construct URL based on game descriptor
        if game_descriptor == "SELFREPORT":
            data_url = (self.activities_url + "&excludedGds=").format(player_id)
        else:
            data_url = (self.activities_url + "&gds={}").format(player_id, game_descriptor)
        
        all_player_data = []
        page = 0
        
        while True:
            paginated_url = f"{data_url}&page={page}&size={page_size}"
            try:
                response = requests.get(paginated_url, headers=headers, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                logger.info(f"Player data fetched successfully for page {page}")
                
                player_data = response.json()
                if not player_data:
                    break
                
                all_player_data.extend(player_data)
                page += 1
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to retrieve data for page {page}: {e}")
                # Retry logic could be implemented here
                break
        
        logger.info(f"Total data points fetched: {len(all_player_data)}")
        return all_player_data 