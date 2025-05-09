# GameBus Data Extraction

This module provides functionality to extract various types of data from the GameBus platform. It includes a client for interacting with the GameBus API and collectors for different types of data.

## Components

### GameBusClient

The `GameBusClient` class handles all interactions with the GameBus API. It provides methods for:
- Authentication and token management
- Player data retrieval
- Pagination handling
- Date-based filtering
- Error handling and retries

### Data Collectors

The module includes several specialized data collectors:

1. **LocationDataCollector**
   - Collects GPS location data
   - Includes latitude, longitude, altitude, speed, and error information
   - Data type: `GEOFENCE`

2. **MoodDataCollector**
   - Collects mood logging data
   - Includes valence, arousal, and stress state values
   - Data type: `LOG_MOOD`

3. **ActivityTypeDataCollector**
   - Collects activity type data from wearable devices
   - Includes activity classification, speed, steps, and distance
   - Data type: `TIZEN(DETAIL)`

4. **HeartRateDataCollector**
   - Collects heart rate monitoring data
   - Includes heart rate values and timestamps
   - Data type: `TIZEN(DETAIL)`

5. **AccelerometerDataCollector**
   - Collects accelerometer data
   - Includes x, y, z axis measurements
   - Data type: `TIZEN(DETAIL)`

6. **NotificationDataCollector**
   - Collects notification data
   - Includes notification actions and timestamps
   - Data type: `NOTIFICATION(DETAIL)`

## Usage

### Basic Usage

```python
from src.extraction.gamebus_client import GameBusClient
from src.extraction.data_collectors import LocationDataCollector

# Initialize client
client = GameBusClient(authcode="your_auth_code")

# Get player token and ID
token = client.get_player_token(username="user@example.com", password="password")
player_id = client.get_player_id(token)

# Create collector
location_collector = LocationDataCollector(client, token, player_id)

# Collect data
data, file_path = location_collector.collect()
```

### Date-based Filtering

All collectors support date-based filtering:

```python
from datetime import datetime

# Collect data from a specific date
start_date = datetime(2024, 1, 1)
data, file_path = location_collector.collect(start_date=start_date)

# Collect data between two dates
end_date = datetime(2024, 2, 1)
data, file_path = location_collector.collect(start_date=start_date, end_date=end_date)
```

### Using the Pipeline

The extraction pipeline provides a command-line interface for data collection:

```bash
# Extract all data
python pipeline.py

# Extract specific data types
python pipeline.py --data-types location mood

# Extract data for a specific user
python pipeline.py --user-id 123

# Extract data within a date range
python pipeline.py --start-date 2024-01-01 --end-date 2024-02-01

# Combine options
python pipeline.py --data-types location mood --start-date 2024-01-01 --user-id 123
```

## Data Format

### Location Data
```json
{
    "LATITUDE": 52.09715270996094,
    "LONGITUDE": 5.109695911407471,
    "ALTIDUDE": 32.20000076293945,
    "SPEED": 3.852000188827515,
    "ERROR": 29,
    "TIMESTAMP": 1745804145,
    "ARM": "Arm 2",
    "activity_id": 3312956,
    "date": 1745804205000,
    "gameDescriptor": "GEOFENCE"
}
```

### Mood Data
```json
{
    "VALENCE_STATE_VALUE": 5,
    "AROUSAL_STATE_VALUE": 5,
    "STRESS_STATE_VALUE": 5,
    "EVENT_TIMESTAMP": 1745773701931,
    "activity_id": 3308348,
    "date": 1746041731000,
    "gameDescriptor": "LOG_MOOD"
}
```

### Activity Type Data
```json
{
    "src": "p",
    "ts": 1745804099854,
    "type": "NOT_MOVING",
    "speed": 0.0,
    "steps": 0.0,
    "walks": 0.0,
    "runs": 0.0,
    "freq": 0.0,
    "distance": 0.0,
    "cals": 0.0,
    "activity_id": 3312954,
    "activity_date": 1745804100000
}
```

## Error Handling

The module includes comprehensive error handling:
- API request retries with exponential backoff
- Authentication error handling
- Data parsing error handling
- File I/O error handling

## Configuration

The module uses several configuration files:
- `config/credentials.py`: API endpoints and authentication
- `config/settings.py`: General settings and constants
- `config/paths.py`: File paths and directories

## Dependencies

- requests
- pandas
- python-dateutil

## Notes

- The GameBus API uses pagination for large datasets
- Data is saved in both JSON and CSV formats
- Timestamps are in milliseconds since epoch
- The module includes logging for debugging and monitoring 