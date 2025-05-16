# Location Categorization

This module provides functionality to categorize location data from GameBus using the Google Places API. The main class `LocationCategorizer` enriches raw location data by adding semantic place types to each location point.

## LocationCategorizer

The main class that handles location categorization using the Google Places API.

### Initialization

```python
categorizer = LocationCategorizer(
    api_key: Optional[str] = None,  # Google Places API key
    output_dir: Optional[str] = None,  # Output directory for categorized data
    logger: Optional[logging.Logger] = None  # Custom logger instance
)
```

### Key Methods

#### Data Loading
- `load_player_location_df(player_id: int) -> pd.DataFrame`: Loads location data for a player and returns as DataFrame

#### Data Categorization
- `categorize_location_df(location_df: pd.DataFrame, player_id: int) -> pd.DataFrame`: Categorizes locations in a DataFrame and saves results
- `categorize_player_location(player_id: int) -> pd.DataFrame`: Legacy method that loads and categorizes in one step

#### Data Saving
- `save_categorized_location_json(location_df: pd.DataFrame, player_id: int) -> None`: Saves the categorized DataFrame as a JSON file

#### Utility Methods
- `get_place_type_from_coord(lat: float, lng: float) -> Optional[str]`: Gets place type from coordinates using Google Places API

### Usage Example

```python
from src.categorization.location_categorizer import LocationCategorizer

# Initialize categorizer
categorizer = LocationCategorizer()

# Load and categorize data
df = categorizer.load_player_location_df(player_id=12345)
df_categorized = categorizer.categorize_location_df(df, player_id=12345)

# Save results
categorizer.save_categorized_location_json(df_categorized, player_id=12345)
```

### Command Line Usage

The module can also be used as a command-line tool:

```bash
python src/categorization/location_categorizer.py --player-id 12345
```

### Data Format

#### Input (Raw Location Data)
```json
{
    "LATITUDE": 52.09715270996094,
    "LONGITUDE": 5.109695911407471,
    "ALTIDUDE": 32.20000076293945,
    "SPEED": 3.852000188827515,
    "ERROR": 29,
    "TIMESTAMP": 1745804145
}
```

#### Output (Categorized Location Data)
```json
{
    "LATITUDE": 52.09715270996094,
    "LONGITUDE": 5.109695911407471,
    "ALTIDUDE": 32.20000076293945,
    "SPEED": 3.852000188827515,
    "ERROR": 29,
    "TIMESTAMP": 1745804145,
    "location_type": "university"
}
```

### Features

1. **Efficient API Usage**
   - Caches results for locations within 10 meters
   - Minimizes API calls by reusing place types for nearby locations
   - Handles API errors gracefully

2. **Data Processing**
   - Handles missing or invalid coordinates
   - Converts NaN values to 'NaN' string in JSON output
   - Supports both JSON and CSV output formats

3. **Error Handling**
   - Graceful handling of API failures
   - Logging of warnings and errors
   - Fallback to "unknown" type when API key is missing

### Configuration

1. **API Key**
   - Set in `config/credentials.py` as `GOOGLE_PLACES_API_KEY`
   - Or provide as environment variable
   - Required for place type categorization

2. **Output Directory**
   - Default: `data/categorized/`
   - Created automatically if it doesn't exist
   - Customizable through constructor parameter

### Dependencies
- requests
- pandas
- numpy
- python-dotenv
- logging

### Notes
- The categorizer uses a 20-meter radius for place type queries
- Locations are considered the same if within 10 meters of each other
- API calls have a 5-second timeout
- Missing or invalid coordinates are marked as NaN
- The module includes comprehensive logging for debugging and monitoring 