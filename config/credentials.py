"""
Credentials configuration for GameBus API and Google Places API.
Contains authentication information needed to access various APIs.
"""
import os
import sys

# Default  GameBus API endpoints
BASE_URL = "https://api-new.gamebus.eu/v2"
TOKEN_URL = f"{BASE_URL}/oauth/token"
PLAYER_ID_URL = f"{BASE_URL}/users/current"
ACTIVITIES_URL = f"{BASE_URL}/players/{{}}/activities?sort=-date" 

# Try to import from secret folder for backward compatibility
try:
    from secret.auth import authcode as SECRET_AUTHCODE
    AUTHCODE = SECRET_AUTHCODE
except ImportError:
    # If not available, use default/placeholder
    AUTHCODE = "your_auth_code_here"  # Replace with actual auth code when deploying

# Try to import Google Places API key from secret folder
try:
    from secret.auth import google_places_api_key as SECRET_GOOGLE_PLACES_API_KEY
    GOOGLE_PLACES_API_KEY = SECRET_GOOGLE_PLACES_API_KEY
except ImportError:
    # If not available, use environment variable or placeholder
    GOOGLE_PLACES_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY', 'your_google_places_api_key_here')