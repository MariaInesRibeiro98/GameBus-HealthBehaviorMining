# GameBus to OCED Transformer

This module provides functionality to transform GameBus data into the OCED-mHealth schema format. The main class `GameBusToOCEDTransformer` handles the conversion of various data types including accelerometer, activity type, heart rate, location, mood, and notification data.

## GameBusToOCEDTransformer

The main transformer class that converts GameBus data to OCED-mHealth schema format.

### Initialization

```python
transformer = GameBusToOCEDTransformer(
    player_id: str,
    intervention_start: datetime,
    intervention_end: datetime,
    intervention_goal: str
)
```

### Key Methods

#### Data Loading
- `load_data_to_dataframe(file_path: str) -> pd.DataFrame`: Loads GameBus data from a JSON file into a pandas DataFrame
- `load_all_player_data(player_id: str, data_dir: str = "data") -> Dict[str, pd.DataFrame]`: Loads all GameBus data for a player into DataFrames

#### Data Transformation
- `transform_accelerometer_data(df: pd.DataFrame) -> None`: Transforms accelerometer data to sensor events
- `transform_activity_data(df: pd.DataFrame) -> None`: Transforms activity type data to sensor events
- `transform_heartrate_data(df: pd.DataFrame) -> None`: Transforms heart rate data to sensor events
- `transform_location_data(df: pd.DataFrame) -> None`: Transforms location data to sensor events
- `transform_mood_data(df: pd.DataFrame) -> None`: Transforms mood data to behavior events
- `transform_notification_data(df: pd.DataFrame) -> None`: Transforms notification data to behavior events

#### Utility Methods
- `_convert_timestamp(timestamp: Union[int, float, str]) -> str`: Converts epoch timestamp to ISO format datetime string
- `save_to_file(output_path: str) -> None`: Saves the transformed data to a JSON file
- `analyze_oced_data() -> None`: Analyzes and prints statistics about the transformed OCED data

### Data Structure

The transformer creates an OCED data structure with the following components:

1. **Sensor Event Types**
   - Accelerometer (x, y, z, activity_id)
   - Activity Type (type, speed, steps, walks, runs, freq, distance, calories)
   - Heart Rate (bpm, pp)
   - Location (latitude, longitude, altitude, speed, error)

2. **Behavior Event Types**
   - Mood (valence, arousal, stress)
   - Notification (action)

3. **Object Types**
   - Player (id)
   - Intervention (goal, start_date, end_date)

### Usage Example

```python
from datetime import datetime
from src.transformation.gamebus_to_oced_transformer import GameBusToOCEDTransformer

# Initialize transformer
transformer = GameBusToOCEDTransformer(
    player_id="12345",
    intervention_start=datetime(2024, 1, 1),
    intervention_end=datetime(2024, 2, 1),
    intervention_goal="Improve physical activity"
)

# Load and transform data
data = transformer.load_all_player_data("12345")
transformer.transform_accelerometer_data(data["accelerometer"])
transformer.transform_activity_data(data["activity_type"])
transformer.transform_heartrate_data(data["heartrate"])
transformer.transform_location_data(data["location"])
transformer.transform_mood_data(data["mood"])
transformer.transform_notification_data(data["notifications"])

# Save and analyze results
transformer.save_to_file("output/oced_data.json")
transformer.analyze_oced_data()
```

### Output Format

The transformed data follows the OCED-mHealth schema format:

```json
{
    "sensorEventTypes": [...],
    "behaviorEventTypes": [...],
    "objectTypes": [...],
    "sensorEvents": [...],
    "behaviorEvents": [...],
    "objects": [...]
}
```

### Dependencies
- pandas
- numpy
- uuid
- datetime
- json
- logging

### Notes
- All timestamps are converted to ISO format
- Each event is assigned a unique UUID
- The transformer maintains relationships between objects and events
- Data validation and error handling are implemented throughout the transformation process 