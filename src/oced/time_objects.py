from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import uuid
import orjson
from pathlib import Path
from tqdm import tqdm
from collections import defaultdict
import os


class TimeObject:
    """Class for creating and managing time-based objects from OCED data."""
    
    def __init__(self):
        """Initialize the TimeObject class."""
        self.day_objects: Dict[str, Dict[str, Any]] = {}  # Maps date to day object
        self.week_objects: Dict[str, Dict[str, Any]] = {}  # Maps week start date to week object
        self.day_object_type = {
            "name": "day",
            "attributes": [
                {"name": "date", "type": "string"},
                {"name": "day_of_week", "type": "string"}
            ]
        }
        self.week_object_type = {
            "name": "week",
            "attributes": [
                {"name": "week_start_date", "type": "string"},
                {"name": "week_number", "type": "integer"},
                {"name": "year", "type": "integer"}
            ]
        }
    
    def create_day_objects(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """
        Create day objects from the OCED data according to OCED-mHealth schema and establish relationships.
        
        Args:
            data (Dict[str, Any]): The OCED data dictionary containing events
            
        Returns:
            Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]: 
                - Extended OCED data dictionary with day objects and relationships
                - Dictionary mapping dates to day objects
        """
        # Create a copy of the input data to modify
        extended_data = data.copy()
        
        # Initialize day objects list if it doesn't exist
        if 'objects' not in extended_data:
            extended_data['objects'] = []
        
        # Add day object type if it doesn't exist
        if not any(obj_type['name'] == 'day' for obj_type in extended_data.get('objectTypes', [])):
            if 'objectTypes' not in extended_data:
                extended_data['objectTypes'] = []
            extended_data['objectTypes'].append(self.day_object_type)
        
        print("Day object type added.")
        
        # Get all events and their timestamps
        all_events = []
        for event in extended_data.get('sensorEvents', []):
            event['event_type'] = 'sensor'
            all_events.append(event)
        for event in extended_data.get('behaviorEvents', []):
            event['event_type'] = 'behavior'
            all_events.append(event)
        
        print(f"Total events collected: {len(all_events)}")
        print(f"Original sensor events: {len(extended_data.get('sensorEvents', []))}")
        print(f"Original behavior events: {len(extended_data.get('behaviorEvents', []))}")
        
        # Extract unique dates with progress bar
        print("Extracting unique dates...")
        timestamps = []
        for event in tqdm(all_events, desc="Processing timestamps", unit="event"):
            timestamps.append(event['time'])
        
        # Convert to pandas Series and process dates
        timestamps_series = pd.Series(timestamps)
        datetimes = pd.to_datetime(timestamps_series, format='ISO8601')
        dates = set(str(dt.date()) for dt in datetimes)
        print(f"Unique dates found: {len(dates)}")
        
        # Create a mapping of timestamps to dates for quick lookup
        print("Creating date mapping...")
        date_mapping = {}
        for ts, dt in tqdm(zip(timestamps, datetimes), desc="Creating date mapping", total=len(timestamps), unit="event"):
            date_mapping[ts] = str(dt.date())
        
        # Create day objects for each unique date
        for date_str in sorted(dates):
            dt = pd.to_datetime(date_str)
            # Use pandas Timestamp methods for day of week
            day_of_week = dt.day_name()
            
            # Create day object according to schema
            day_object = {
                "id": str(uuid.uuid4()),
                "type": "day",
                "attributes": [
                    {
                        "name": "date",
                        "value": date_str,
                        "time": dt.isoformat()
                    },
                    {
                        "name": "day_of_week",
                        "value": day_of_week,
                        "time": dt.isoformat()
                    }
                ],
                "relationships": []
            }
            
            # Add day object to the data
            extended_data['objects'].append(day_object)
            self.day_objects[date_str] = day_object

        print(f"Created {len(self.day_objects)} day objects")
        
        # Group events by date for batch processing
        events_by_date = defaultdict(lambda: {'sensor': [], 'behavior': []})
        for event in all_events:
            date_str = date_mapping[event['time']]
            events_by_date[date_str][event['event_type']].append(event)

        # Process relationships in batches by date
        relationships_added = 0
        for date_str, events in tqdm(events_by_date.items(), desc="Adding relationships", unit="date"):
            day_object = self.day_objects[date_str]
            relationship = {
                "id": day_object['id'],
                "type": "object",
                "qualifier": "occurred_on"
            }
            
            # Add relationships to all events for this date at once
            for event_type in ['sensor', 'behavior']:
                for event in events[event_type]:
                    if 'relationships' not in event:
                        event['relationships'] = []
                    event['relationships'].append(relationship)
                    relationships_added += 1

        print(f"Added {relationships_added} relationships to events")
        
        # Verify relationships were added to extended_data
        sensor_events_with_relationships = sum(1 for event in extended_data.get('sensorEvents', []) 
                                            if 'relationships' in event and event['relationships'])
        behavior_events_with_relationships = sum(1 for event in extended_data.get('behaviorEvents', []) 
                                               if 'relationships' in event and event['relationships'])
        print(f"Verification - Events with relationships in extended_data:")
        print(f"  Sensor events: {sensor_events_with_relationships}")
        print(f"  Behavior events: {behavior_events_with_relationships}")
        
        return extended_data, self.day_objects
    
    def create_week_objects(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """
        Create week objects from the OCED data according to OCED-mHealth schema and establish relationships.
        Weeks start on Monday.
        
        Args:
            data (Dict[str, Any]): The OCED data dictionary containing events
            
        Returns:
            Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]: 
                - Extended OCED data dictionary with week objects and relationships
                - Dictionary mapping week start dates to week objects
        """
        # Create a copy of the input data to modify
        extended_data = data.copy()
        
        # Initialize objects list if it doesn't exist
        if 'objects' not in extended_data:
            extended_data['objects'] = []
        
        # Add week object type if it doesn't exist
        if not any(obj_type['name'] == 'week' for obj_type in extended_data.get('objectTypes', [])):
            if 'objectTypes' not in extended_data:
                extended_data['objectTypes'] = []
            extended_data['objectTypes'].append(self.week_object_type)
        
        print("Week object type added.")
        
        # Get all dates from existing day objects
        if not self.day_objects:
            print("No day objects found. Please create day objects first.")
            return extended_data, self.week_objects
        
        # Convert dates to pandas datetime and find unique weeks
        dates = pd.to_datetime(list(self.day_objects.keys()))
        
        # Calculate week start dates (Monday) for each date
        # Convert to Series first to use dt accessor
        dates_series = pd.Series(dates)
        week_starts = dates_series - pd.to_timedelta(dates_series.dt.dayofweek, unit='D')
        unique_weeks = sorted(set(week_starts))
        
        print(f"Found {len(unique_weeks)} unique weeks")
        
        # Create week objects
        for week_start in unique_weeks:
            week_number = week_start.isocalendar()[1]
            year = week_start.year
            
            # Create week object according to schema
            week_object = {
                "id": str(uuid.uuid4()),
                "type": "week",
                "attributes": [
                    {
                        "name": "week_start_date",
                        "value": str(week_start.date()),
                        "time": week_start.isoformat()
                    },
                    {
                        "name": "week_number",
                        "value": week_number,
                        "time": week_start.isoformat()
                    },
                    {
                        "name": "year",
                        "value": year,
                        "time": week_start.isoformat()
                    }
                ],
                "relationships": []
            }
            
            # Add week object to the data
            extended_data['objects'].append(week_object)
            self.week_objects[str(week_start.date())] = week_object
            
            # Add relationships to days in this week
            week_end = week_start + pd.Timedelta(days=6)
            days_in_week = [day for day in self.day_objects.values() 
                          if week_start.date() <= pd.to_datetime(day['attributes'][0]['value']).date() <= week_end.date()]
            
            for day in days_in_week:
                # Add relationship from week to day
                week_to_day = {
                    "id": day['id'],
                    "type": "object",
                    "qualifier": "contains"
                }
                week_object['relationships'].append(week_to_day)
                
                # Add relationship from day to week
                day_to_week = {
                    "id": week_object['id'],
                    "type": "object",
                    "qualifier": "belongs_to"
                }
                if 'relationships' not in day:
                    day['relationships'] = []
                day['relationships'].append(day_to_week)
        
        print(f"Created {len(self.week_objects)} week objects")
        return extended_data, self.week_objects
    
    def save_extended_data(self, filename: str, extended_data: Dict[str, Any], compress: bool = False) -> None:
        """
        Save the extended OCED data to a JSON file in the data/oced directory.
        Uses orjson for fast JSON serialization.
        
        Args:
            filename (str): Name of the file to save (e.g., 'extended_data.json')
            extended_data (Dict[str, Any]): The extended OCED data dictionary
            compress (bool): Whether to compress the output file (default: False)
        """
        # Get the project root directory (assuming this file is in src/data_loading)
        project_root = Path(__file__).parent.parent.parent
        
        # Construct the full path to the data/oced directory
        output_dir = project_root / 'data' / 'transformed'
        output_path = output_dir / filename
        
        # Create directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Serialize to JSON bytes using orjson (much faster than json)
        json_bytes = orjson.dumps(
            extended_data,
            option=orjson.OPT_INDENT_2  # orjson automatically handles datetime serialization
        )
        
        if compress:
            import gzip
            output_path = output_path.with_suffix('.json.gz')
            with gzip.open(output_path, 'wb') as f:
                f.write(json_bytes)
        else:
            with open(output_path, 'wb') as f:
                f.write(json_bytes)
        
        print(f"Saved extended data to: {output_path}")
    
    def get_day(self, date_str: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific day object by date.
        
        Args:
            date_str (str): Date in YYYY-MM-DD format
            
        Returns:
            Optional[Dict[str, Any]]: Day object if found, None otherwise
        """
        return self.day_objects.get(date_str)
    
    def get_week(self, week_start_date: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific week object by its start date.
        
        Args:
            week_start_date (str): Week start date in YYYY-MM-DD format (must be a Monday)
            
        Returns:
            Optional[Dict[str, Any]]: Week object if found, None otherwise
        """
        return self.week_objects.get(week_start_date)
    
    def get_days_by_weekday(self, weekday: str) -> List[Dict[str, Any]]:
        """
        Get all days that fall on a specific weekday.
        
        Args:
            weekday (str): Day of the week (e.g., 'Monday', 'Tuesday', etc.)
            
        Returns:
            List[Dict[str, Any]]: List of day objects for the specified weekday
        """
        return [
            day for day in self.day_objects.values()
            if any(attr['name'] == 'day_of_week' and attr['value'].lower() == weekday.lower()
                  for attr in day['attributes'])
        ]
    
    def get_events_for_day(self, date_str: str, data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all events (both sensor and behavior) for a specific day.
        
        Args:
            date_str (str): Date in YYYY-MM-DD format
            data (Dict[str, Any]): The OCED data dictionary
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: Dictionary with 'sensor' and 'behavior' keys,
                                            each containing a list of events
        """
        day_object = self.get_day(date_str)
        if not day_object:
            return {'sensor': [], 'behavior': []}
        
        events = {'sensor': [], 'behavior': []}
        
        # Check sensor events
        for event in data.get('sensorEvents', []):
            if any(rel['id'] == day_object['id'] for rel in event.get('relationships', [])):
                events['sensor'].append(event)
        
        # Check behavior events
        for event in data.get('behaviorEvents', []):
            if any(rel['id'] == day_object['id'] for rel in event.get('relationships', [])):
                events['behavior'].append(event)
        
        return events
    
    def get_days_in_week(self, week_start_date: str) -> List[Dict[str, Any]]:
        """
        Get all days that belong to a specific week.
        
        Args:
            week_start_date (str): Week start date in YYYY-MM-DD format (must be a Monday)
            
        Returns:
            List[Dict[str, Any]]: List of day objects in the specified week
        """
        week_object = self.get_week(week_start_date)
        if not week_object:
            return []
            
        return [
            self.day_objects[day_id] for day_id in self.day_objects
            if any(rel['id'] == week_object['id'] 
                  for rel in self.day_objects[day_id].get('relationships', []))
        ] 