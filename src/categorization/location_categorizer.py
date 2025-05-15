import os
import pandas as pd
import numpy as np
from typing import Optional
from dotenv import load_dotenv
import requests
import math

# Project imports
from config.paths import RAW_DATA_DIR, DATA_DIR
from config.credentials import GOOGLE_PLACES_API_KEY
from src.utils.logging import setup_logging
from src.utils.file_handlers import load_json, save_json, save_csv, ensure_directory

# Output directory for categorized data
CATEGORIZED_DIR = os.path.join(DATA_DIR, "categorized")
ensure_directory(CATEGORIZED_DIR)

# Set up logging
logger = setup_logging(log_level="INFO")
logger.info("Location categorization script started.")

# Load environment variables (for Google Places API key)
load_dotenv()

def haversine(lat1, lon1, lat2, lon2):
        lon1, lat1, lon2, lat2 = map(math.radians, [float(lon1), float(lat1), float(lon2), float(lat2)])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371000  # meters
        return c * r


class LocationCategorizer:
    def __init__(self, api_key: Optional[str] = None, output_dir: Optional[str] = None, logger=None):
        self.api_key = api_key or GOOGLE_PLACES_API_KEY
        self.output_dir = output_dir or CATEGORIZED_DIR
        self.logger = logger or setup_logging(log_level="INFO")
        ensure_directory(self.output_dir)
    

    def get_place_type_from_coord(self, lat: float, lng: float) -> Optional[str]:
        url = "https://places.googleapis.com/v1/places:searchNearby"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "places.displayName,places.types,places.primaryType",
        }
        payload = {
            "maxResultCount": 5,
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lng},
                    "radius": 20
                }
            },
            "rankPreference": "DISTANCE"
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=5)
            resp.raise_for_status()
            places = resp.json().get("places", [])
            if not places:
                return "other"
            return places[0].get("primaryType", "other")
        except Exception as e:
            self.logger.warning(f"API call failed for ({lat}, {lng}): {e}")
            return "api_error"

    def load_player_location_df(self, player_id: int) -> pd.DataFrame:
        """Load location data for a player and return as DataFrame."""
        location_file = os.path.join(RAW_DATA_DIR, f"player_{player_id}_location.json")
        try:
            location_data = load_json(location_file)
            self.logger.info(f"Loaded {len(location_data)} location data points for player {player_id}")
            location_df = pd.DataFrame(location_data)
        except Exception as e:
            self.logger.error(f"Error loading location data: {e}")
            return pd.DataFrame()
        return location_df

    def categorize_location_df(self, location_df: pd.DataFrame, player_id: int) -> pd.DataFrame:
        """Categorize locations in a DataFrame and save results."""
        if location_df.empty:
            self.logger.error("Input DataFrame is empty.")
            return location_df
        location_df = location_df.copy()
        location_df['location_type'] = pd.NA
        processed_locations = []  # List of dicts: {lat, lon, locationtype}

        for idx, row in location_df.iterrows():
            lat, lon = row['LATITUDE'], row['LONGITUDE']
            if pd.isna(lat) or pd.isna(lon) or (float(lat) == 200 and float(lon) == 200):
                location_df.loc[idx, 'location_type'] = np.nan
                continue
            found = False
            for entry in processed_locations:
                if pd.notna(entry['latitude']) and pd.notna(entry['longitude']):
                    if haversine(lat, lon, entry['latitude'], entry['longitude']) < 10:
                        location_df.loc[idx, 'location_type'] = entry['locationtype']
                        found = True
                        break
            if not found:
                if not self.api_key:
                    location_type = "unknown"
                else:
                    location_type = self.get_place_type_from_coord(lat, lon)
                location_df.loc[idx, 'location_type'] = location_type
                processed_locations.append({'latitude': lat, 'longitude': lon, 'locationtype': location_type})

        # Export enriched dataframe
        output_json = os.path.join(self.output_dir, f"player_{player_id}_location_categorized.json")
        output_csv = os.path.join(self.output_dir, f"player_{player_id}_location_categorized.csv")
        save_json(location_df.to_dict(orient='records'), output_json)
        save_csv(location_df, output_csv, index=False)
        self.logger.info(f"Categorized data saved to {output_json} and {output_csv}")
        return location_df

    def save_categorized_location_json(self, location_df: pd.DataFrame, player_id: int) -> None:
        """Save the categorized DataFrame as a JSON file in the categorized folder, converting NaN to 'NaN' string."""
        output_json = os.path.join(self.output_dir, f"player_{player_id}_categorized_location.json")
        # Convert NaN/NA values to the string 'NaN' for JSON export
        df_to_save = location_df.copy().replace({np.nan: 'NaN', pd.NA: 'NaN'})
        save_json(df_to_save.to_dict(orient='records'), output_json)
        self.logger.info(f"Categorized location data saved to {output_json}")

    def categorize_player_location(self, player_id: int) -> pd.DataFrame:
        """Legacy method: loads and categorizes in one step."""
        location_df = self.load_player_location_df(player_id)
        return self.categorize_location_df(location_df, player_id)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Categorize GameBus location data by place type.")
    parser.add_argument("--player-id", type=int, required=True, help="Player ID to process")
    args = parser.parse_args()
    categorizer = LocationCategorizer()
    # Use the new split methods for clarity
    df = categorizer.load_player_location_df(args.player_id)
    categorizer.categorize_location_df(df, args.player_id)