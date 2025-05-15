# Location Categorizer

This module (`location_categorizer.py`) enriches raw location data from GameBus by categorizing each location point using the Google Places API. It minimizes API calls by caching unique locations and exports the enriched data for downstream analysis.

## Features
- Loads raw location data for a specified player.
- For each unique location (within 10 meters), queries the Google Places API to determine the primary place type.
- Caches results to avoid redundant API calls.
- Adds a `location_type` column to the data.
- Exports the enriched data to `data/categorized/` in both JSON and CSV formats.
- Handles missing values by converting them to the string `'NaN'` in the output JSON.

## Usage

### As a Script

```bash
python src/categorization/location_categorizer.py --player-id 107631
```

- Requires the Google Places API key to be set in your environment or in `config/credentials.py`.
- Input: Raw location JSON file from extraction (e.g., `data/raw/player_107631_location.json`).
- Output: Categorized location files in `data/categorized/` (e.g., `player_107631_location_categorized.json`, `player_107631_location_categorized.csv`, and `player_107631_categorized_location.json`).

### As a Module

You can import and use the `LocationCategorizer` class in your own scripts:

```python
from src.categorization.location_categorizer import LocationCategorizer

categorizer = LocationCategorizer()
df = categorizer.load_player_location_df(player_id)
df_categorized = categorizer.categorize_location_df(df, player_id)
categorizer.save_categorized_location_json(df_categorized, player_id)
```

## Methods
- `load_player_location_df(player_id)`: Loads raw location data for a player and returns a DataFrame.
- `categorize_location_df(location_df, player_id)`: Categorizes the DataFrame and saves results to CSV/JSON.
- `save_categorized_location_json(location_df, player_id)`: Saves the DataFrame as a JSON file, converting NaN values to the string `'NaN'`.
- `categorize_player_location(player_id)`: Legacy method that loads and categorizes in one step.

## Data Format

### Input (raw location data)
```json
{
    "LATITUDE": 52.09715270996094,
    "LONGITUDE": 5.109695911407471,
    ...
}
```

### Output (categorized location data)
```json
{
    "LATITUDE": 52.09715270996094,
    "LONGITUDE": 5.109695911407471,
    ...
    "location_type": "university"
}
```

- Missing values are represented as the string `'NaN'` in the output JSON.

## Configuration
- Google Places API key: Set in `config/credentials.py` or as the `GOOGLE_PLACES_API_KEY` environment variable.
- Output directory: `data/categorized/` (created if it does not exist).

## Dependencies
- requests
- pandas
- numpy
- python-dotenv

## Notes
- The script is designed to be efficient and avoid unnecessary API calls.
- If the API key is missing, the script will label locations as `unknown`. 