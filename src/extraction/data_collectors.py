"""
Data collectors for different types of GameBus data.
"""
import ast
import json
import pandas as pd
import logging
import os
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime

from config.settings import VALID_GAME_DESCRIPTORS, VALID_PROPERTY_KEYS
from config.paths import RAW_DATA_DIR
from src.extraction.gamebus_client import GameBusClient

# Set up logging
logger = logging.getLogger(__name__)

class DataCollector:
    """
    Base class for collecting data from GameBus.
    """
    
    def __init__(self, client: GameBusClient, token: str, player_id: int):
        """
        Initialize the data collector.
        
        Args:
            client: GameBus client
            token: Access token
            player_id: Player ID
        """
        self.client = client
        self.token = token
        self.player_id = player_id
    
    def _save_raw_data(self, data: List[Dict[str, Any]], filename: str) -> str:
        """
        Save raw data to a JSON file.
        
        Args:
            data: Data to save
            filename: Name of the file
            
        Returns:
            Path to the saved file
        """
        os.makedirs(RAW_DATA_DIR, exist_ok=True)
        file_path = os.path.join(RAW_DATA_DIR, filename)
        
        with open(file_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)
        
        logger.info(f"Data saved to {file_path}")
        return file_path
    
    def _save_csv_data(self, data: List[Dict[str, Any]], filename: str) -> str:
        """
        Save data to a CSV file.
        
        Args:
            data: Data to save
            filename: Name of the file
            
        Returns:
            Path to the saved file
        """
        os.makedirs(RAW_DATA_DIR, exist_ok=True)
        file_path = os.path.join(RAW_DATA_DIR, filename)
        
        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False)
        
        logger.info(f"Data saved to {file_path}")
        return file_path
    
    def _parse_general_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Parse general GameBus data.
        
        Args:
            raw_data: Raw data from GameBus
            
        Returns:
            Parsed data
        """
        data_list = []
        
        for data_point in raw_data:
            data = {}
            for property_instance in data_point.get("propertyInstances", []):
                property_key = property_instance.get("property", {}).get("translationKey")
                property_value = property_instance.get("value")
                data[property_key] = property_value
            
            # Add activity metadata
            data["activity_id"] = data_point.get("id")
            data["date"] = data_point.get("date")
            data["gameDescriptor"] = data_point.get("gameDescriptor", {}).get("translationKey")
            
            data_list.append(data)
            
        return data_list
    
    def _parse_tizen_data(self, raw_data: List[Dict[str, Any]], property_key: str) -> List[Dict[str, Any]]:
        """
        Parse Tizen-specific data.
        
        Args:
            raw_data: Raw data from GameBus
            property_key: Property key to extract
            
        Returns:
            Parsed data
        """
        if property_key not in VALID_PROPERTY_KEYS:
            raise ValueError(f"Invalid property_key. Valid values are: {', '.join(VALID_PROPERTY_KEYS)}")
        
        data_list = []
        
        for data_point in raw_data:
            activity_id = data_point.get("id")
            activity_date = data_point.get("date")
            
            for property_instance in data_point.get("propertyInstances", []):
                prop_key = property_instance.get("property", {}).get("translationKey")
                property_value = property_instance.get("value")
                
                if prop_key == "ACTIVITY_TYPE" and property_key == "ACTIVITY_TYPE":
                    try:
                        property_value_dict = ast.literal_eval(property_value)
                        # Add activity metadata
                        property_value_dict["activity_id"] = activity_id
                        property_value_dict["activity_date"] = activity_date
                        data_list.append(property_value_dict)
                    except (ValueError, SyntaxError) as e:
                        logger.error(f"Failed to parse ACTIVITY_TYPE: {e}")
                
                elif prop_key == "HRM_LOG" and property_key == "HRM_LOG":
                    try:
                        property_value_list = ast.literal_eval(property_value)
                        for item in property_value_list:
                            # Add activity metadata
                            item["activity_id"] = activity_id
                            item["activity_date"] = activity_date
                            data_list.append(item)
                    except (ValueError, SyntaxError) as e:
                        logger.error(f"Failed to parse HRM_LOG: {e}")
                
                elif prop_key == "ACCELEROMETER_LOG" and property_key == "ACCELEROMETER_LOG":
                    try:
                        property_value_list = ast.literal_eval(property_value)
                        for item in property_value_list:
                            # Add activity metadata
                            item["activity_id"] = activity_id
                            item["activity_date"] = activity_date
                            data_list.append(item)
                    except (ValueError, SyntaxError) as e:
                        logger.error(f"Failed to parse ACCELEROMETER_LOG: {e}")
        
        return data_list

    def collect(self, start_date: Optional[datetime] = None, 
                end_date: Optional[datetime] = None) -> Tuple[List[Dict[str, Any]], str]:
        """
        Collect data from GameBus.
        
        Args:
            start_date: Optional start date for filtering data
            end_date: Optional end date for filtering data
            
        Returns:
            Tuple of (parsed data, file path)
        """
        raise NotImplementedError("Subclasses must implement collect()")


class LocationDataCollector(DataCollector):
    """
    Collector for GPS location data.
    """
    
    def collect(self, start_date: Optional[datetime] = None, 
                end_date: Optional[datetime] = None) -> Tuple[List[Dict[str, Any]], str]:
        """
        Collect GPS location data.
        
        Args:
            start_date: Optional start date for filtering data
            end_date: Optional end date for filtering data
            
        Returns:
            Tuple of (parsed data, file path)
        """
        raw_data = self.client.get_player_data(self.token, self.player_id, "GEOFENCE",
                                             start_date=start_date, end_date=end_date)
        parsed_data = self._parse_general_data(raw_data)
        file_path = self._save_raw_data(parsed_data, f"player_{self.player_id}_location.json")
        return parsed_data, file_path


class MoodDataCollector(DataCollector):
    """
    Collector for mood logging data.
    """
    
    def collect(self, start_date: Optional[datetime] = None, 
                end_date: Optional[datetime] = None) -> Tuple[List[Dict[str, Any]], str]:
        """
        Collect mood logging data.
        
        Args:
            start_date: Optional start date for filtering data
            end_date: Optional end date for filtering data
            
        Returns:
            Tuple of (parsed data, file path)
        """
        raw_data = self.client.get_player_data(self.token, self.player_id, "LOG_MOOD",
                                             start_date=start_date, end_date=end_date)
        parsed_data = self._parse_general_data(raw_data)
        file_path = self._save_raw_data(parsed_data, f"player_{self.player_id}_mood.json")
        return parsed_data, file_path


class ActivityTypeDataCollector(DataCollector):
    """
    Collector for activity type data.
    """
    
    def collect(self, start_date: Optional[datetime] = None, 
                end_date: Optional[datetime] = None) -> Tuple[List[Dict[str, Any]], str]:
        """
        Collect activity type data.
        
        Args:
            start_date: Optional start date for filtering data
            end_date: Optional end date for filtering data
            
        Returns:
            Tuple of (parsed data, file path)
        """
        raw_data = self.client.get_player_data(self.token, self.player_id, "TIZEN(DETAIL)",
                                             start_date=start_date, end_date=end_date)
        parsed_data = self._parse_tizen_data(raw_data, "ACTIVITY_TYPE")
        file_path = self._save_raw_data(parsed_data, f"player_{self.player_id}_activity_type.json")
        return parsed_data, file_path


class HeartRateDataCollector(DataCollector):
    """
    Collector for heart rate data.
    """
    
    def collect(self, start_date: Optional[datetime] = None, 
                end_date: Optional[datetime] = None) -> Tuple[List[Dict[str, Any]], str]:
        """
        Collect heart rate data.
        
        Args:
            start_date: Optional start date for filtering data
            end_date: Optional end date for filtering data
            
        Returns:
            Tuple of (parsed data, file path)
        """
        raw_data = self.client.get_player_data(self.token, self.player_id, "TIZEN(DETAIL)",
                                             start_date=start_date, end_date=end_date)
        parsed_data = self._parse_tizen_data(raw_data, "HRM_LOG")
        file_path = self._save_raw_data(parsed_data, f"player_{self.player_id}_heartrate.json")
        return parsed_data, file_path


class AccelerometerDataCollector(DataCollector):
    """
    Collector for accelerometer data.
    """
    
    def collect(self, start_date: Optional[datetime] = None, 
                end_date: Optional[datetime] = None) -> Tuple[List[Dict[str, Any]], str]:
        """
        Collect accelerometer data.
        
        Args:
            start_date: Optional start date for filtering data
            end_date: Optional end date for filtering data
            
        Returns:
            Tuple of (parsed data, file path)
        """
        raw_data = self.client.get_player_data(self.token, self.player_id, "TIZEN(DETAIL)",
                                             start_date=start_date, end_date=end_date)
        parsed_data = self._parse_tizen_data(raw_data, "ACCELEROMETER_LOG")
        file_path = self._save_raw_data(parsed_data, f"player_{self.player_id}_accelerometer.json")
        return parsed_data, file_path


class NotificationDataCollector(DataCollector):
    """
    Collector for notification data.
    """
    
    def collect(self, start_date: Optional[datetime] = None, 
                end_date: Optional[datetime] = None) -> Tuple[List[Dict[str, Any]], str]:
        """
        Collect notification data.
        
        Args:
            start_date: Optional start date for filtering data
            end_date: Optional end date for filtering data
            
        Returns:
            Tuple of (parsed data, file path)
        """
        raw_data = self.client.get_player_data(self.token, self.player_id, "NOTIFICATION(DETAIL)",
                                             start_date=start_date, end_date=end_date)
        parsed_data = self._parse_general_data(raw_data)
        file_path = self._save_raw_data(parsed_data, f"player_{self.player_id}_notifications.json")
        return parsed_data, file_path 