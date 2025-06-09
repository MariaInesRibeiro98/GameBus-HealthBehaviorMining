import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import pandas as pd
from datetime import datetime


class OCEDDataQuery:
    """Class for querying and extracting different types of events from OCED (Observed Contextual Event Data) JSON files."""
    
    def __init__(self):
        """
        Initialize the OCED data query interface.
        """
        # Get the project root directory (parent of src directory)
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / "data" / "transformed"
        self.data: Optional[Dict[str, Any]] = None
    
    def load_json(self, filename: str) -> Dict[str, Any]:
        """
        Load the OCED data from a specified JSON file.
        
        Args:
            filename (str): The name of the JSON file to load (e.g., 'player_107631_oced_data.json')
                           The file should be located in the data/transformed directory.
        
        Returns:
            Dict[str, Any]: The loaded JSON data as a dictionary
            
        Raises:
            FileNotFoundError: If the specified JSON file cannot be found
            json.JSONDecodeError: If the JSON file is not properly formatted
        """
        file_path = self.data_dir / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"OCED data file not found: {file_path}")
        
        with open(file_path, 'r') as f:
            self.data = json.load(f)
        
        return self.data
    
    def get_players_by_ids(self, player_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Query player objects from the loaded data that match the given player IDs.
        
        Args:
            player_ids (List[str]): List of player IDs to search for
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary mapping player IDs to their corresponding player objects.
                                      Only includes players that were found in the data.
                                      
            
        Raises:
            ValueError: If no data has been loaded yet
        """
        if self.data is None:
            raise ValueError("No data has been loaded. Call load_json() first.")
            
        # Get all objects from the data
        objects = self.data.get('objects', [])
        print(objects)
        
        # Filter for player objects with matching IDs
        player_objects = {}
        for obj in objects:
            if obj.get('type') == 'player':
                # Find the id attribute
                for attr in obj.get('attributes', []):
                    if attr.get('name') == 'id':
                        player_id = attr.get('value')
                        if player_id in player_ids:
                            player_objects[player_id] = obj
                        break
        
        return player_objects
    
    def get_notification_events(self, data: Dict[str, Any]) -> pd.DataFrame:
        """
        Extract notification events from the behaviorEvents in the data dictionary.
        
        Args:
            data (Dict[str, Any]): The dictionary returned by load_json containing the OCED data
        
        Returns:
            pd.DataFrame: A DataFrame containing notification events with columns:
                         - timestamp: The time of the notification event
                         - action: The action value from behaviorEventTypeAttributes (e.g., RECEIVED, READ)
                         - location: The location value from behaviorEventTypeAttributes (e.g., invalid, in_transit, gym)
                         - occurred_on: The object ID from the occurred_on relationship (if available)
        """
        # Get the behaviorEvents from the data
        behavior_events = data.get('behaviorEvents', [])
        
        # Filter for notification events and extract required fields
        notification_events = []
        for event in behavior_events:
            if event.get('behaviorEventType') == 'notification':
                # Initialize notification attributes
                notification_data = {'timestamp': event['time']}
                
                # Extract notification attributes from behaviorEventTypeAttributes
                for attr in event.get('behaviorEventTypeAttributes', []):
                    attr_name = attr.get('name')
                    if attr_name in ['action', 'location']:
                        notification_data[attr_name] = attr.get('value')
                
                # Extract occurred_on relationship if it exists
                for rel in event.get('relationships', []):
                    if rel.get('qualifier') == 'occurred_on':
                        notification_data['occurred_on'] = rel.get('object')
                        break
                
                # Add the event even if no attributes were found
                notification_events.append(notification_data)
        
        if not notification_events:
            print("Warning: No notification events found in the data")
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(notification_events)
        
        # Convert timestamp to datetime if it's not already
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601')
        
        # Sort by timestamp
        df = df.sort_values('timestamp')
        
        return df
    
    def get_mood_events_2D(self, data: Dict[str, Any]) -> pd.DataFrame:
        """
        Extract mood events from the behaviorEvents in the data dictionary.
        
        Args:
            data (Dict[str, Any]): The dictionary returned by load_json containing the OCED data
        
        Returns:
            pd.DataFrame: A DataFrame containing mood events with columns:
                         - timestamp: The time of the mood event
                         - valence: The valence value from behaviorEventTypeAttributes
                         - arousal: The arousal value from behaviorEventTypeAttributes
                         - stress: The stress value from behaviorEventTypeAttributes
                         - location: The location value from behaviorEventTypeAttributes (if available)
                         - occurred_on: The object ID from the occurred_on relationship (if available)
        """
        # Get the behaviorEvents from the data
        behavior_events = data.get('behaviorEvents', [])
        
        # Filter for mood events and extract required fields
        mood_events = []
        for event in behavior_events:
            if event.get('behaviorEventType') == 'mood':
                # Initialize mood attributes
                mood_data = {'timestamp': event['time']}
                
                # Extract mood attributes from behaviorEventTypeAttributes
                for attr in event.get('behaviorEventTypeAttributes', []):
                    attr_name = attr.get('name')
                    if attr_name in ['valence', 'arousal', 'stress', 'location']:
                        mood_data[attr_name] = attr.get('value')
                
                # Extract occurred_on relationship if it exists
                for rel in event.get('relationships', []):
                    if rel.get('qualifier') == 'occurred_on':
                        mood_data['occurred_on'] = rel.get('object')
                        break
                
                # Only add if we found at least one mood attribute
                if len(mood_data) > 1:  # More than just timestamp
                    mood_events.append(mood_data)
        
        if not mood_events:
            print("Warning: No mood events found in the data")
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(mood_events)
        
        # Convert timestamp to datetime if it's not already
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601')
        
        # Sort by timestamp
        df = df.sort_values('timestamp')
        
        return df
    
    def get_location_sensor_events(self, data: Dict[str, Any]) -> pd.DataFrame:
        """
        Extract location events from the sensorEvents in the data dictionary.
        
        Args:
            data (Dict[str, Any]): The dictionary returned by load_json containing the OCED data
        
        Returns:
            pd.DataFrame: A DataFrame containing location events with columns:
                         - timestamp: The time of the location event
                         - latitude: The latitude value from sensorEventTypeAttributes
                         - longitude: The longitude value from sensorEventTypeAttributes
                         - altitude: The altitude value from sensorEventTypeAttributes
                         - speed: The speed value from sensorEventTypeAttributes
                         - error: The error value from sensorEventTypeAttributes
        """
        # Get the sensorEvents from the data
        sensor_events = data.get('sensorEvents', [])
        
        # Filter for location events and extract required fields
        location_events = []
        for event in sensor_events:
            if event.get('sensorEventType') == 'location':
                # Initialize location attributes
                location_data = {'timestamp': event['time']}
                
                # Extract location attributes from sensorEventTypeAttributes
                for attr in event.get('sensorEventTypeAttributes', []):
                    attr_name = attr.get('name')
                    if attr_name in ['latitude', 'longitude', 'altitude', 'speed', 'error']:
                        # Convert numeric values to float
                        try:
                            location_data[attr_name] = float(attr.get('value'))
                        except (ValueError, TypeError):
                            location_data[attr_name] = None
                
                # Only add if we found at least latitude and longitude
                if 'latitude' in location_data and 'longitude' in location_data:
                    location_events.append(location_data)
        
        if not location_events:
            print("Warning: No location events found in the data")
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(location_events)
        
        # Convert timestamp to datetime if it's not already
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601')
        
        # Sort by timestamp
        df = df.sort_values('timestamp')
        
        return df
    
    def get_accelerometer_events(self, data: Dict[str, Any], start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Extract accelerometer events from the sensorEvents in the data dictionary.
        
        Args:
            data (Dict[str, Any]): The dictionary returned by load_json containing the OCED data
            start_date (Optional[datetime]): Optional start date to filter events. If provided, only events after this date will be included.
            end_date (Optional[datetime]): Optional end date to filter events. If provided, only events before this date will be included.
        
        Returns:
            pd.DataFrame: A DataFrame containing accelerometer events with columns:
                         - timestamp: The time of the accelerometer event
                         - x: The x-axis acceleration value from sensorEventTypeAttributes
                         - y: The y-axis acceleration value from sensorEventTypeAttributes
                         - z: The z-axis acceleration value from sensorEventTypeAttributes
        """
        # Print date filtering parameters
        print(f"Date filtering parameters:")
        print(f"  Start date: {start_date}")
        print(f"  End date: {end_date}")
        
        # Get the sensorEvents from the data
        sensor_events = data.get('sensorEvents', [])
        print(f"Total number of sensor events found: {len(sensor_events)}")
        
        # Print unique sensor event types to see what's available
        event_types = set(event.get('sensorEventType') for event in sensor_events)
        print(f"Available sensor event types: {event_types}")
        
        # Filter for accelerometer events and extract required fields
        accelerometer_events = []
        for event in sensor_events:
            event_type = event.get('sensorEventType')
            if event_type == 'accelerometer':
                # Initialize accelerometer attributes
                accel_data = {'timestamp': event['time']}
                
                # Extract accelerometer attributes from sensorEventTypeAttributes
                for attr in event.get('sensorEventTypeAttributes', []):
                    attr_name = attr.get('name')
                    if attr_name in ['x', 'y', 'z']:
                        # Convert numeric values to float
                        try:
                            accel_data[attr_name] = float(attr.get('value'))
                        except (ValueError, TypeError):
                            accel_data[attr_name] = None
                
                # Only add if we found all three coordinates
                if all(coord in accel_data for coord in ['x', 'y', 'z']):
                    accelerometer_events.append(accel_data)
        
        print(f"Number of accelerometer events found: {len(accelerometer_events)}")
        
        if not accelerometer_events:
            print("Warning: No accelerometer events found in the data")
            # Print a sample event to see its structure
            if sensor_events:
                print("Sample sensor event structure:")
                print(json.dumps(sensor_events[0], indent=2))
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(accelerometer_events)
        
        # Convert timestamp to datetime if it's not already
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601')
        
        # Print date range of data before filtering
        print(f"Date range of data before filtering:")
        print(f"  Earliest timestamp: {df['timestamp'].min()}")
        print(f"  Latest timestamp: {df['timestamp'].max()}")
        
        # Apply date filtering if start_date or end_date is provided
        if start_date is not None:
            df = df[df['timestamp'] >= start_date]
            print(f"After start date filtering: {len(df)} events remaining")
        if end_date is not None:
            df = df[df['timestamp'] <= end_date]
            print(f"After end date filtering: {len(df)} events remaining")
        
        # Sort by timestamp
        df = df.sort_values('timestamp')
        
        return df
    
    def get_heartrate_events(self, data: Dict[str, Any], start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Extract heartrate events from the sensorEvents in the data dictionary.
        
        Args:
            data (Dict[str, Any]): The dictionary returned by load_json containing the OCED data
            start_date (Optional[datetime]): Optional start date to filter events. If provided, only events after this date will be included.
            end_date (Optional[datetime]): Optional end date to filter events. If provided, only events before this date will be included.
        
        Returns:
            pd.DataFrame: A DataFrame containing heartrate events with columns:
                         - timestamp: The time of the heartrate event
                         - bpm: The beats per minute value from sensorEventTypeAttributes
                         - pp: The pulse pressure value from sensorEventTypeAttributes
        """
        # Print date filtering parameters
        print(f"Date filtering parameters:")
        print(f"  Start date: {start_date}")
        print(f"  End date: {end_date}")
        
        # Get the sensorEvents from the data
        sensor_events = data.get('sensorEvents', [])
        print(f"Total number of sensor events found: {len(sensor_events)}")
        
        # Print unique sensor event types to see what's available
        event_types = set(event.get('sensorEventType') for event in sensor_events)
        print(f"Available sensor event types: {event_types}")
        
        # Filter for heartrate events and extract required fields
        heartrate_events = []
        for event in sensor_events:
            event_type = event.get('sensorEventType')
            if event_type == 'heartrate':
                # Initialize heartrate attributes
                hr_data = {'timestamp': event['time']}
                
                # Extract heartrate attributes from sensorEventTypeAttributes
                for attr in event.get('sensorEventTypeAttributes', []):
                    attr_name = attr.get('name')
                    if attr_name in ['bpm', 'pp']:
                        # Convert numeric values to float
                        try:
                            hr_data[attr_name] = float(attr.get('value'))
                        except (ValueError, TypeError):
                            hr_data[attr_name] = None
                
                # Only add if we found at least bpm
                if 'bpm' in hr_data:
                    heartrate_events.append(hr_data)
        
        print(f"Number of heartrate events found: {len(heartrate_events)}")
        
        if not heartrate_events:
            print("Warning: No heartrate events found in the data")
            # Print a sample event to see its structure
            if sensor_events:
                print("Sample sensor event structure:")
                print(json.dumps(sensor_events[0], indent=2))
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(heartrate_events)
        
        # Convert timestamp to datetime if it's not already
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601')
        
        # Print date range of data before filtering
        print(f"Date range of data before filtering:")
        print(f"  Earliest timestamp: {df['timestamp'].min()}")
        print(f"  Latest timestamp: {df['timestamp'].max()}")
        
        # Apply date filtering if start_date or end_date is provided
        if start_date is not None:
            df = df[df['timestamp'] >= start_date]
            print(f"After start date filtering: {len(df)} events remaining")
        if end_date is not None:
            df = df[df['timestamp'] <= end_date]
            print(f"After end date filtering: {len(df)} events remaining")
        
        # Sort by timestamp
        df = df.sort_values('timestamp')
        
        return df
    
    def get_activity_events(self, data: Dict[str, Any]) -> pd.DataFrame:
        """
        Extract activity_type events from the sensorEvents in the data dictionary.
        
        Args:
            data (Dict[str, Any]): The dictionary returned by load_json containing the OCED data
        
        Returns:
            pd.DataFrame: A DataFrame containing activity events with columns:
                         - timestamp: The time of the activity event
                         - type: The activity type from sensorEventTypeAttributes
                         - speed: The speed value from sensorEventTypeAttributes
                         - steps: The steps value from sensorEventTypeAttributes
                         - walks: The walks value from sensorEventTypeAttributes
                         - runs: The runs value from sensorEventTypeAttributes
                         - freq: The frequency value from sensorEventTypeAttributes
                         - distance: The distance value from sensorEventTypeAttributes
                         - calories: The calories value from sensorEventTypeAttributes
        """
        # Get the sensorEvents from the data
        sensor_events = data.get('sensorEvents', [])
        
        # Filter for activity_type events and extract required fields
        activity_events = []
        for event in sensor_events:
            if event.get('sensorEventType') == 'activity_type':
                # Initialize activity attributes
                activity_data = {'timestamp': event['time']}
                
                # Extract activity attributes from sensorEventTypeAttributes
                for attr in event.get('sensorEventTypeAttributes', []):
                    attr_name = attr.get('name')
                    if attr_name in ['type', 'speed', 'steps', 'walks', 'runs', 'freq', 'distance', 'calories']:
                        # Convert numeric values to float, except for 'type'
                        if attr_name == 'type':
                            activity_data[attr_name] = attr.get('value')
                        else:
                            try:
                                activity_data[attr_name] = float(attr.get('value'))
                            except (ValueError, TypeError):
                                activity_data[attr_name] = None
                
                # Only add if we found at least the activity type
                if 'type' in activity_data:
                    activity_events.append(activity_data)
        
        if not activity_events:
            print("Warning: No activity events found in the data")
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(activity_events)
        
        # Convert timestamp to datetime if it's not already
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601')
        
        # Sort by timestamp
        df = df.sort_values('timestamp')
        
        return df
    
    def get_location_behavior_events(self, data: Dict[str, Any]) -> pd.DataFrame:
        """
        Extract location events from the behaviorEvents in the data dictionary.
        
        Args:
            data (Dict[str, Any]): The dictionary returned by load_json containing the OCED data
        
        Returns:
            pd.DataFrame: A DataFrame containing location events with columns:
                         - timestamp: The time of the location event
                         - lifecycle: The lifecycle value from behaviorEventTypeAttributes (e.g., Entering, Exiting)
                         - location_type: The type of location from behaviorEventTypeAttributes (e.g., home, gym, other)
                         - occurred_on: The object ID from the occurred_on relationship (if available)
        """
        # Get the behaviorEvents from the data
        behavior_events = data.get('behaviorEvents', [])
        
        # Print total number of events found
        print(f"Total number of behavior events found: {len(behavior_events)}")
        
        # Filter for location events and extract required fields
        location_events = []
        for event in behavior_events:
            if event.get('behaviorEventType') == 'location_event':
                # Print detailed debugging info for the first event
                if len(location_events) == 0:
                    print("\nDetailed analysis of first location event:")
                    print("1. Event type:", event.get('behaviorEventType'))
                    print("2. Time:", event.get('time'))
                    print("3. All available keys:", list(event.keys()))
                    print("4. behaviorEventTypeAttributes:", event.get('behaviorEventTypeAttributes'))
                    print("5. relationships:", event.get('relationships'))
                    print("\nFull event structure:")
                    print(json.dumps(event, indent=2))
                
                # Initialize location attributes
                location_data = {'timestamp': event['time']}
                
                # Extract location attributes from behaviorEventTypeAttributes
                for attr in event.get('behaviorEventTypeAttributes', []):
                    attr_name = attr.get('name')
                    print(f"Found attribute: {attr_name}")  # Debug print
                    if attr_name in ['lifecycle', 'location_type']:
                        location_data[attr_name] = attr.get('value')
                
                # Extract occurred_on relationship if it exists
                for rel in event.get('relationships', []):
                    if rel.get('qualifier') == 'occurred_on':
                        location_data['occurred_on'] = rel.get('object')
                        break
                
                # Add the event even if no attributes were found
                location_events.append(location_data)
        
        print(f"\nNumber of location events found: {len(location_events)}")
        if location_events:
            print("Sample location event data:", location_events[0])
            print("\nColumns in final DataFrame:", list(location_events[0].keys()))
        
        if not location_events:
            print("Warning: No location events found in the data")
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(location_events)
        
        # Convert timestamp to datetime if it's not already
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601')
        
        # Sort by timestamp
        df = df.sort_values('timestamp')
        
        return df
    
    def get_physical_activity_bout_events(self, data: Dict[str, Any]) -> pd.DataFrame:
        """
        Extract physical activity bout events from the behaviorEvents in the data dictionary.
        
        Args:
            data (Dict[str, Any]): The dictionary returned by load_json containing the OCED data
        
        Returns:
            pd.DataFrame: A DataFrame containing physical activity bout events with columns:
                         - timestamp: The time of the physical activity bout event
                         - bout_type: The type of physical activity bout (e.g., MODERATE-VIGOROUS_PA, LIGHT_PA)
                         - lifecycle: The lifecycle value (e.g., START, END)
                         - location: The location where the activity occurred (e.g., home, gym, in_transit)
                         - occurred_on: The object ID from the occurred_on relationship (if available)
        """
        # Get the behaviorEvents from the data
        behavior_events = data.get('behaviorEvents', [])
        
        # Filter for physical activity bout events and extract required fields
        pa_bout_events = []
        for event in behavior_events:
            if event.get('behaviorEventType') == 'physical_activity_bout':
                # Initialize physical activity bout attributes
                pa_data = {'timestamp': event['time']}
                
                # Extract physical activity bout attributes from behaviorEventTypeAttributes
                for attr in event.get('behaviorEventTypeAttributes', []):
                    attr_name = attr.get('name')
                    if attr_name in ['bout_type', 'lifecycle', 'location']:
                        pa_data[attr_name] = attr.get('value')
                
                # Extract occurred_on relationship if it exists
                for rel in event.get('relationships', []):
                    if rel.get('qualifier') == 'occurred_on':
                        pa_data['occurred_on'] = rel.get('object')
                        break
                
                # Add the event even if no attributes were found
                pa_bout_events.append(pa_data)
        
        if not pa_bout_events:
            print("Warning: No physical activity bout events found in the data")
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(pa_bout_events)
        
        # Convert timestamp to datetime if it's not already
        #df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601')
        
        # Sort by timestamp
        #df = df.sort_values('timestamp')
        
        return df
    
    def analyze_schema(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze the schema of the OCED data and count objects by type, including their attributes.
        
        Args:
            data (Optional[Dict[str, Any]]): The OCED data dictionary to analyze. If None, uses the currently loaded data.
        
        Returns:
            Dict[str, Any]: A dictionary containing schema analysis results with counts of different object types,
                           event types, and their attributes.
        
        Raises:
            ValueError: If no data is provided and no data has been loaded yet
        """
        # Use provided data or currently loaded data
        data_to_analyze = data if data is not None else self.data
        if data_to_analyze is None:
            raise ValueError("No data provided and no data has been loaded. Call load_json() first or provide data.")
        
        # Initialize results dictionary
        results = {
            'object_types': {},
            'event_types': {
                'sensor': {},
                'behavior': {}
            },
            'object_attributes': {},  # New: Store attribute analysis for each object type
            'event_attributes': {     # New: Store attribute analysis for each event type
                'sensor': {},
                'behavior': {}
            },
            'total_objects': 0,
            'total_events': {
                'sensor': 0,
                'behavior': 0
            }
        }
        
        # Helper function to analyze attributes
        def analyze_attributes(items, item_type, category):
            for item in items:
                # Get the type of the item
                if category == 'object':
                    item_type = item.get('type', 'unknown')
                elif category == 'sensor':
                    item_type = item.get('sensorEventType', 'unknown')
                else:  # behavior
                    item_type = item.get('behaviorEventType', 'unknown')
                
                # Initialize attribute analysis for this type if not exists
                if category == 'object':
                    if item_type not in results['object_attributes']:
                        results['object_attributes'][item_type] = {
                            'attributes': {},
                            'relationships': set(),
                            'example': None
                        }
                    attr_dict = results['object_attributes'][item_type]
                else:
                    if item_type not in results['event_attributes'][category]:
                        results['event_attributes'][category][item_type] = {
                            'attributes': {},
                            'example': None
                        }
                    attr_dict = results['event_attributes'][category][item_type]
                
                # Store an example of this type (first one encountered)
                if attr_dict['example'] is None:
                    attr_dict['example'] = item
                
                # Analyze attributes
                if category == 'object':
                    # Analyze object attributes
                    for attr in item.get('attributes', []):
                        attr_name = attr.get('name', 'unknown')
                        attr_type = type(attr.get('value')).__name__
                        if attr_name not in attr_dict['attributes']:
                            attr_dict['attributes'][attr_name] = {
                                'type': attr_type,
                                'count': 0,
                                'example_values': set()
                            }
                        attr_dict['attributes'][attr_name]['count'] += 1
                        attr_dict['attributes'][attr_name]['example_values'].add(str(attr.get('value')))
                    
                    # Analyze relationships
                    for rel in item.get('relationships', []):
                        attr_dict['relationships'].add(rel.get('qualifier', 'unknown'))
                else:
                    # Analyze event attributes
                    if category == 'sensor':
                        attr_list = item.get('sensorEventTypeAttributes', [])
                    else:  # behavior
                        attr_list = item.get('behaviorEventTypeAttributes', [])
                    
                    for attr in attr_list:
                        attr_name = attr.get('name', 'unknown')
                        attr_type = type(attr.get('value')).__name__
                        if attr_name not in attr_dict['attributes']:
                            attr_dict['attributes'][attr_name] = {
                                'type': attr_type,
                                'count': 0,
                                'example_values': set()
                            }
                        attr_dict['attributes'][attr_name]['count'] += 1
                        attr_dict['attributes'][attr_name]['example_values'].add(str(attr.get('value')))
        
        # Analyze objects and their attributes
        objects = data_to_analyze.get('objects', [])
        analyze_attributes(objects, None, 'object')
        
        # Count object types
        for obj in objects:
            obj_type = obj.get('type', 'unknown')
            results['object_types'][obj_type] = results['object_types'].get(obj_type, 0) + 1
            results['total_objects'] += 1
        
        # Analyze sensor events and their attributes
        sensor_events = data_to_analyze.get('sensorEvents', [])
        analyze_attributes(sensor_events, None, 'sensor')
        
        # Count sensor event types
        for event in sensor_events:
            event_type = event.get('sensorEventType', 'unknown')
            results['event_types']['sensor'][event_type] = results['event_types']['sensor'].get(event_type, 0) + 1
            results['total_events']['sensor'] += 1
        
        # Analyze behavior events and their attributes
        behavior_events = data_to_analyze.get('behaviorEvents', [])
        analyze_attributes(behavior_events, None, 'behavior')
        
        # Count behavior event types
        for event in behavior_events:
            event_type = event.get('behaviorEventType', 'unknown')
            results['event_types']['behavior'][event_type] = results['event_types']['behavior'].get(event_type, 0) + 1
            results['total_events']['behavior'] += 1
        
        # Print a formatted report
        print("\nOCED Data Schema Analysis Report")
        print("=" * 40)
        
        print("\nObject Types and Their Attributes:")
        print("-" * 40)
        for obj_type, count in sorted(results['object_types'].items()):
            print(f"\n{obj_type} (count: {count}):")
            if obj_type in results['object_attributes']:
                attr_info = results['object_attributes'][obj_type]
                print("  Attributes:")
                for attr_name, attr_data in sorted(attr_info['attributes'].items()):
                    print(f"    - {attr_name}:")
                    print(f"      Type: {attr_data['type']}")
                    print(f"      Count: {attr_data['count']}")
                    print(f"      Example values: {', '.join(list(attr_data['example_values'])[:3])}")
                if attr_info['relationships']:
                    print("  Relationships:")
                    for rel in sorted(attr_info['relationships']):
                        print(f"    - {rel}")
        
        print("\nSensor Event Types and Their Attributes:")
        print("-" * 40)
        for event_type, count in sorted(results['event_types']['sensor'].items()):
            print(f"\n{event_type} (count: {count}):")
            if event_type in results['event_attributes']['sensor']:
                attr_info = results['event_attributes']['sensor'][event_type]
                print("  Attributes:")
                for attr_name, attr_data in sorted(attr_info['attributes'].items()):
                    print(f"    - {attr_name}:")
                    print(f"      Type: {attr_data['type']}")
                    print(f"      Count: {attr_data['count']}")
                    print(f"      Example values: {', '.join(list(attr_data['example_values'])[:3])}")
        
        print("\nBehavior Event Types and Their Attributes:")
        print("-" * 40)
        for event_type, count in sorted(results['event_types']['behavior'].items()):
            print(f"\n{event_type} (count: {count}):")
            if event_type in results['event_attributes']['behavior']:
                attr_info = results['event_attributes']['behavior'][event_type]
                print("  Attributes:")
                for attr_name, attr_data in sorted(attr_info['attributes'].items()):
                    print(f"    - {attr_name}:")
                    print(f"      Type: {attr_data['type']}")
                    print(f"      Count: {attr_data['count']}")
                    print(f"      Example values: {', '.join(list(attr_data['example_values'])[:3])}")
        
        print("\nSummary:")
        print("-" * 20)
        print(f"Total Objects: {results['total_objects']}")
        print(f"Total Sensor Events: {results['total_events']['sensor']}")
        print(f"Total Behavior Events: {results['total_events']['behavior']}")
        print(f"Total Events: {results['total_events']['sensor'] + results['total_events']['behavior']}")
        
        return results
    
