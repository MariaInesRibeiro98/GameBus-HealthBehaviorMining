"""
Credentials configuration for GameBus API.
Contains authentication information needed to access the GameBus API.
"""
import os
import sys

# Try to import from secret folder for backward compatibility
try:
    from secret.auth import authcode as SECRET_AUTHCODE
    AUTHCODE = SECRET_AUTHCODE
except ImportError:
    # If not available, use default/placeholder
    AUTHCODE = "your_auth_code_here"  # Replace with actual auth code when deploying

# Default API endpoints
BASE_URL = "https://api-new.gamebus.eu/v2"
TOKEN_URL = f"{BASE_URL}/oauth/token"
PLAYER_ID_URL = f"{BASE_URL}/users/current"
ACTIVITIES_URL = f"{BASE_URL}/players/{{}}/activities?sort=-date" 