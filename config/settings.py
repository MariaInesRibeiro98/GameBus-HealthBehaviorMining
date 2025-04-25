"""
General settings for the GameBus-HealthBehaviorMining project.
"""

# GameBus API configuration
DEFAULT_PAGE_SIZE = 50
MAX_RETRIES = 3
REQUEST_TIMEOUT = 30  # seconds

# Data collection settings
VALID_GAME_DESCRIPTORS = [
    "GEOFENCE",           # Location data
    "LOG_MOOD",           # Mood logging data
    "TIZEN(DETAIL)",      # Watch/wearable data
    "NOTIFICATION(DETAIL)",  # Notification data
    "SELFREPORT"          # Self-reported data
]

# Property keys for different data types
VALID_PROPERTY_KEYS = [
    "UNKNOWN",
    "ACTIVITY_TYPE",      # Activity type data
    "HRM_LOG",            # Heart rate monitoring data
    "ACCELEROMETER_LOG"   # Accelerometer data
]

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s" 