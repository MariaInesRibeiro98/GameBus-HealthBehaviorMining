"""
Main pipeline runner for the GameBus-HealthBehaviorMining project.
"""
import argparse
import pandas as pd
import logging
from typing import List, Dict, Any

from config.credentials import AUTHCODE
from config.paths import USERS_FILE_PATH
from src.extraction.gamebus_client import GameBusClient
from src.extraction.data_collectors import (
    LocationDataCollector, 
    MoodDataCollector,
    ActivityTypeDataCollector,
    HeartRateDataCollector,
    AccelerometerDataCollector,
    NotificationDataCollector
)
from src.utils.logging import setup_logging

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='GameBus Health Behavior Mining Pipeline')
    
    parser.add_argument('--extract-only', action='store_true',
                        help='Only run the extraction step')
    parser.add_argument('--user-id', type=int, 
                        help='Specific user ID to process')
    parser.add_argument('--data-types', nargs='+', default=['all'],
                        choices=['all', 'location', 'mood', 'activity', 'heartrate', 'accelerometer', 'notification'],
                        help='Data types to collect')
    parser.add_argument('--log-level', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Logging level')
    
    return parser.parse_args()

def load_users(users_file: str) -> pd.DataFrame:
    """
    Load users from a CSV file.
    
    Args:
        users_file: Path to users CSV file
        
    Returns:
        DataFrame of users
    """
    try:
        df = pd.read_csv(users_file, delimiter=';')
        return df
    except Exception as e:
        logging.error(f"Failed to load users file: {e}")
        raise

def run_extraction(user_row: pd.Series, data_types: List[str]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Run the extraction step for a single user.
    
    Args:
        user_row: User data row from DataFrame
        data_types: Types of data to collect
        
    Returns:
        Dictionary of collected data by type
    """
    username = user_row['Username']
    password = user_row['Password']
    
    logger = logging.getLogger(__name__)
    logger.info(f"Processing user: {username}")
    
    # Initialize GameBus client
    client = GameBusClient(AUTHCODE)
    
    # Get player token and ID
    token = client.get_player_token(username, password)
    if not token:
        logger.error(f"Failed to get token for user {username}")
        return {}
    
    player_id = client.get_player_id(token)
    if not player_id:
        logger.error(f"Failed to get player ID for user {username}")
        return {}
    
    logger.info(f"Successfully authenticated user {username} with player ID {player_id}")
    
    # Collect data based on requested types
    results = {}
    
    collectors = {
        'location': LocationDataCollector(client, token, player_id),
        'mood': MoodDataCollector(client, token, player_id),
        'activity': ActivityTypeDataCollector(client, token, player_id),
        'heartrate': HeartRateDataCollector(client, token, player_id),
        'accelerometer': AccelerometerDataCollector(client, token, player_id),
        'notification': NotificationDataCollector(client, token, player_id)
    }
    
    types_to_collect = list(collectors.keys()) if 'all' in data_types else data_types
    
    for data_type in types_to_collect:
        if data_type in collectors:
            logger.info(f"Collecting {data_type} data for user {username}")
            try:
                data, file_path = collectors[data_type].collect()
                results[data_type] = data
                logger.info(f"Collected {len(data)} {data_type} data points, saved to {file_path}")
            except Exception as e:
                logger.error(f"Failed to collect {data_type} data for user {username}: {e}")
    
    return results

def main():
    """Main function to run the pipeline."""
    args = parse_args()
    
    # Set up logging
    logger = setup_logging(log_level=args.log_level)
    logger.info("Starting GameBus Health Behavior Mining Pipeline")
    
    # Load users
    users_df = load_users(USERS_FILE_PATH)
    logger.info(f"Loaded {len(users_df)} users")
    
    # Process specific user or all users
    if args.user_id:
        user_row = users_df[users_df['UserID'] == args.user_id].iloc[0]
        results = run_extraction(user_row, args.data_types)
    else:
        all_results = {}
        for _, user_row in users_df.iterrows():
            user_results = run_extraction(user_row, args.data_types)
            all_results[user_row['Username']] = user_results
    
    # Only run extraction if requested
    if args.extract_only:
        logger.info("Extraction complete. Skipping transformation and abstraction steps.")
        return
    
    # Future steps would be added here:
    # - Preprocessing
    # - Activity recognition
    # - OCEL generation
    
    logger.info("Pipeline completed successfully")

if __name__ == "__main__":
    main() 