import unittest
from datetime import datetime, timedelta
import pandas as pd
import os
import sys
import json
from pathlib import Path

# Add the project root directory to the Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from src.extraction.gamebus_client import GameBusClient
from src.extraction.data_collectors import (
    LocationDataCollector,
    MoodDataCollector,
    ActivityTypeDataCollector,
    HeartRateDataCollector,
    AccelerometerDataCollector,
    NotificationDataCollector
)
from config.credentials import AUTHCODE
from config.paths import USERS_FILE_PATH

class TestDataExtraction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment before running tests."""
        # Load test user credentials
        users_df = pd.read_csv(USERS_FILE_PATH, delimiter=';')
        cls.test_user = users_df.iloc[0]  # Use first user for testing
        
        # Initialize GameBus client
        cls.client = GameBusClient(AUTHCODE)
        
        # Get player token and ID
        cls.token = cls.client.get_player_token(cls.test_user['Username'], cls.test_user['Password'])
        cls.player_id = cls.client.get_player_id(cls.token)
        
        # Create test data collectors
        cls.collectors = {
            'location': LocationDataCollector(cls.client, cls.token, cls.player_id),
            'mood': MoodDataCollector(cls.client, cls.token, cls.player_id),
            'activity': ActivityTypeDataCollector(cls.client, cls.token, cls.player_id),
            'heartrate': HeartRateDataCollector(cls.client, cls.token, cls.player_id),
            'accelerometer': AccelerometerDataCollector(cls.client, cls.token, cls.player_id),
            'notification': NotificationDataCollector(cls.client, cls.token, cls.player_id)
        }

    def test_no_date_filtering(self):
        """Test data extraction without date filtering."""
        for data_type, collector in self.collectors.items():
            with self.subTest(data_type=data_type):
                # Collect data without date filtering
                data, _ = collector.collect()
                
                # Verify that data was collected
                self.assertIsNotNone(data)
                self.assertIsInstance(data, list)
                self.assertGreater(len(data), 0)
                
                # Verify data structure
                if data:
                    self.assertIsInstance(data[0], dict)
                    self.assertIn('activity_date', data[0])

    def test_date_filtering(self):
        """Test data extraction with date filtering."""
        # Set up date range (last 7 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        for data_type, collector in self.collectors.items():
            with self.subTest(data_type=data_type):
                # Collect data with date filtering
                data, _ = collector.collect(start_date=start_date, end_date=end_date)
                
                # Verify that data was collected
                self.assertIsNotNone(data)
                self.assertIsInstance(data, list)
                
                # If data exists, verify date filtering
                if data:
                    for item in data:
                        # Convert activity_date to datetime
                        activity_date = datetime.fromtimestamp(int(item['activity_date']) / 1000)
                        
                        # Verify date is within range
                        self.assertGreaterEqual(activity_date, start_date)
                        self.assertLessEqual(activity_date, end_date)

    def test_invalid_date_range(self):
        """Test data extraction with invalid date range."""
        # Set up invalid date range (end date before start date)
        end_date = datetime.now()
        start_date = end_date + timedelta(days=1)  # Start date after end date
        
        for data_type, collector in self.collectors.items():
            with self.subTest(data_type=data_type):
                # Collect data with invalid date range
                data, _ = collector.collect(start_date=start_date, end_date=end_date)
                
                # Verify that no data was collected
                self.assertEqual(len(data), 0)

    def test_specific_date_range(self):
        """Test data extraction with a specific date range."""
        # Set up specific date range (e.g., last 24 hours)
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=24)
        
        for data_type, collector in self.collectors.items():
            with self.subTest(data_type=data_type):
                # Collect data with specific date range
                data, _ = collector.collect(start_date=start_date, end_date=end_date)
                
                # Verify that data was collected
                self.assertIsNotNone(data)
                self.assertIsInstance(data, list)
                
                # If data exists, verify date filtering
                if data:
                    for item in data:
                        # Convert activity_date to datetime
                        activity_date = datetime.fromtimestamp(int(item['activity_date']) / 1000)
                        
                        # Verify date is within range
                        self.assertGreaterEqual(activity_date, start_date)
                        self.assertLessEqual(activity_date, end_date)

if __name__ == '__main__':
    unittest.main() 