from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import uuid
import orjson
from pathlib import Path
from tqdm import tqdm
from .time_objects import TimeObject


class StressObjectManager:
    """Class for creating and managing stress self-report objects from mood events in OCED data."""
    
    def __init__(self):
        """Initialize the StressObjectManager class."""
        self.stress_object_type = {
            "name": "stress_self_report",
            "attributes": [
                {"name": "stress_value", "type": "number"}  # Stress value reported in mood events
            ]
        }
        self.stress_objects: Dict[str, Dict[str, Any]] = {}  # Maps stress object ID to stress object
        self.time_manager = TimeObject()
    
    def create_stress_object_type(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add the stress self-report object type to the OCED data if it doesn't exist.
        
        Args:
            data (Dict[str, Any]): The OCED data dictionary
            
        Returns:
            Dict[str, Any]: Updated OCED data dictionary with stress self-report object type
        """
        # Create a copy of the input data to modify
        extended_data = data.copy()
        
        # Initialize objectTypes if it doesn't exist
        if 'objectTypes' not in extended_data:
            extended_data['objectTypes'] = []
        
        # Add stress self-report object type if it doesn't exist
        if not any(obj_type['name'] == 'stress_self_report' 
                  for obj_type in extended_data['objectTypes']):
            extended_data['objectTypes'].append(self.stress_object_type)
            print("Stress self-report object type added.")
        
        return extended_data
    
    def _create_stress_object(
        self,
        stress_id: str,
        stress_value: float,
        timestamp: pd.Timestamp,
        extended_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create a stress self-report object.
        
        Args:
            stress_id (str): Unique identifier for the stress object
            stress_value (float): Stress value from the mood event
            timestamp (pd.Timestamp): Timestamp of the stress report
            extended_data (Dict[str, Any]): The OCED data dictionary
            
        Returns:
            Dict[str, Any]: The created stress self-report object
        """
        # Initialize objects list if it doesn't exist
        if extended_data and 'objects' not in extended_data:
            extended_data['objects'] = []
        
        # Create stress self-report object with timestamped attribute
        stress_object = {
            "id": stress_id,
            "type": "stress_self_report",
            "attributes": [
                {
                    "name": "stress_value",
                    "value": stress_value,
                    "time": timestamp.isoformat()
                }
            ],
            "relationships": []
        }
        
        # Add stress object to the data if provided
        if extended_data:
            extended_data['objects'].append(stress_object)
        
        self.stress_objects[stress_id] = stress_object
        
        return stress_object
    
    def _create_day_object(self, date_str: str, extended_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get or create a specific day object for the given date.
        Only creates the day object if it doesn't already exist.
        
        Args:
            date_str (str): Date in YYYY-MM-DD format
            extended_data (Dict[str, Any]): The OCED data dictionary
            
        Returns:
            Dict[str, Any]: The day object
        """
        # First check if the specific day object exists
        day_object = next(
            (obj for obj in extended_data.get('objects', [])
             if obj['type'] == 'day' and any(
                 attr['name'] == 'date' and attr['value'] == date_str 
                 for attr in obj['attributes']
             )),
            None
        )
        
        # If the day object doesn't exist, create only this specific day
        if not day_object:
            print(f"Day object for {date_str} not found, creating it...")
            # Create only this specific day object
            day_object = self.time_manager.create_single_day_object(date_str, extended_data)
            if not day_object:
                raise ValueError(f"Failed to create day object for date {date_str}")
            print(f"Created day object for {date_str}")
        
        return day_object
    
    def _find_nearest_notification(
        self,
        timestamp: pd.Timestamp,
        time_period: timedelta,
        extended_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Find the nearest notification object within the specified time period.
        
        Args:
            timestamp (pd.Timestamp): Reference timestamp
            time_period (timedelta): Time window to look for notifications
            extended_data (Dict[str, Any]): The OCED data dictionary
            
        Returns:
            Optional[str]: ID of the nearest notification object if found, None otherwise
        """
        nearest_notification = None
        min_time_diff = time_period
        
        # Get all notification objects
        for obj in extended_data.get('objects', []):
            if obj['type'] == 'notification':
                # Get the timestamp from the last_action attribute
                for attr in obj['attributes']:
                    if attr['name'] == 'last_action':
                        notif_time = pd.to_datetime(attr['time'])
                        time_diff = abs((timestamp - notif_time).total_seconds())
                        
                        # Check if within time period and closer than current nearest
                        if time_diff <= time_period.total_seconds() and time_diff < min_time_diff.total_seconds():
                            nearest_notification = obj['id']
                            min_time_diff = timedelta(seconds=time_diff)
                        break
        
        return nearest_notification
    
    def create_stress_objects(
        self,
        data: Dict[str, Any],
        user_id: str,
        time_period: timedelta
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Create stress self-report objects from mood events and link them to relevant notifications.
        Each stress self-report object represents a single stress value reported in a mood event.
        The object is linked to the mood event and potentially to a nearby notification
        if one exists within the specified time period.
        
        Args:
            data (Dict[str, Any]): The OCED data dictionary containing mood events
            user_id (str): ID of the user object to relate stress reports to
            time_period (timedelta): Time window to look for nearby notifications
            
        Returns:
            Tuple[Dict[str, Any], List[Dict[str, Any]]]: 
                - Extended OCED data dictionary with stress self-report objects
                - List of created stress self-report objects
        """
        # Create a copy of the input data to modify
        extended_data = data.copy()
        
        # Initialize objects if it doesn't exist
        if 'objects' not in extended_data:
            extended_data['objects'] = []
        
        # Get all mood events
        mood_events = [
            event for event in extended_data.get('behaviorEvents', [])
            if event['behaviorEventType'] == 'mood'
        ]
        
        if not mood_events:
            print("No mood events found in the data.")
            return extended_data, []
        
        print(f"\nFound {len(mood_events)} mood events")
        
        # Check for existing stress objects
        existing_stress_objects = {
            obj['id']: obj for obj in extended_data.get('objects', [])
            if obj['type'] == 'stress_self_report'
        }
        print(f"Found {len(existing_stress_objects)} existing stress self-report objects")
        
        # Sort all events by time
        mood_events.sort(key=lambda x: pd.to_datetime(x['time']))
        
        # Process events chronologically
        for event in tqdm(mood_events, desc="Processing mood events"):
            # Get stress value from event attributes
            stress_value = next(
                (float(attr['value']) for attr in event['behaviorEventTypeAttributes']
                 if attr['name'] == 'stress'),
                None
            )
            
            if stress_value is None:
                print(f"Skipping mood event without stress value")
                continue
            
            event_time = pd.to_datetime(event['time'])
            
            # Check if this event is already linked to a stress object
            existing_links = [
                rel for rel in event.get('relationships', [])
                if rel['type'] == 'object' and rel['qualifier'] == 'reports_stress'
            ]
            
            if existing_links:
                print(f"Event at {event_time} already linked to stress self-report object: {existing_links}")
                continue
            
            # Create a new stress object
            stress_id = str(uuid.uuid4())
            print(f"Creating new stress self-report object {stress_id} for mood event")
            stress_object = self._create_stress_object(
                stress_id=stress_id,
                stress_value=stress_value,
                timestamp=event_time,
                extended_data=extended_data
            )
            
            # Get or create day object
            day_date = event_time.date().isoformat()
            try:
                day_object = self._create_day_object(day_date, extended_data)
            except ValueError as e:
                print(f"Warning: {e}")
                continue
            
            # Add relationships
            stress_object['relationships'].extend([
                {
                    "id": day_object['id'],
                    "type": "object",
                    "qualifier": "occurred_on"
                },
                {
                    "id": user_id,
                    "type": "object",
                    "qualifier": "reported_by"
                }
            ])
            
            # Find nearest notification within time period
            nearest_notification = self._find_nearest_notification(
                timestamp=event_time,
                time_period=time_period,
                extended_data=extended_data
            )
            
            if nearest_notification:
                print(f"Linking stress self-report object to nearby notification {nearest_notification}")
                stress_object['relationships'].append({
                    "id": nearest_notification,
                    "type": "object",
                    "qualifier": "follows_notification"
                })
            
            # Add relationship from mood event to stress object
            event['relationships'].append({
                "id": stress_id,
                "type": "object",
                "qualifier": "reports_stress"
            })
        
        # Get final list of stress objects
        stress_objects = [
            obj for obj in extended_data.get('objects', [])
            if obj['type'] == 'stress_self_report'
        ]
        
        print(f"\nProcessing complete:")
        print(f"- Created {len(stress_objects) - len(existing_stress_objects)} new stress self-report objects")
        print(f"- Total stress self-report objects: {len(stress_objects)}")
        
        return extended_data, stress_objects
    
    def get_stress_object(self, stress_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific stress object by ID.
        
        Args:
            stress_id (str): ID of the stress object
            
        Returns:
            Optional[Dict[str, Any]]: Stress object if found, None otherwise
        """
        return self.stress_objects.get(stress_id)
    
    def get_stress_for_day(self, date_str: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get all stress self-report objects for a specific day.
        
        Args:
            date_str (str): Date in YYYY-MM-DD format
            data (Dict[str, Any]): The OCED data dictionary
            
        Returns:
            List[Dict[str, Any]]: List of stress self-report objects for the specified day
        """
        # Find the day object
        day_object = None
        for obj in data.get('objects', []):
            if obj['type'] == 'day' and any(
                attr['name'] == 'date' and attr['value'] == date_str 
                for attr in obj['attributes']
            ):
                day_object = obj
                break
        
        if not day_object:
            return []
        
        # Get all stress objects for this day
        return [
            obj for obj in data.get('objects', [])
            if obj['type'] == 'stress_self_report'
            and any(rel['id'] == day_object['id'] for rel in obj.get('relationships', []))
        ]
    
    def save_extended_data(self, filename: str, extended_data: Dict[str, Any], compress: bool = False) -> None:
        """
        Save the extended OCED data to a JSON file in the data/transformed directory.
        Uses orjson for fast JSON serialization.
        
        Args:
            filename (str): Name of the file to save (e.g., 'stress_self_reports.json')
            extended_data (Dict[str, Any]): The extended OCED data dictionary containing stress self-report objects
            compress (bool): Whether to compress the output file (default: False)
        """
        # Get the project root directory
        project_root = Path(__file__).parent.parent.parent
        
        # Construct the full path to the data/transformed directory
        output_dir = project_root / 'data' / 'transformed'
        output_path = output_dir / filename
        
        # Create directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Print summary of data to be saved
        stress_objects = [obj for obj in extended_data.get('objects', []) 
                         if obj['type'] == 'stress_self_report']
        mood_events = [event for event in extended_data.get('behaviorEvents', [])
                      if event['behaviorEventType'] == 'mood']
        
        print(f"\nSaving extended data with:")
        print(f"- {len(stress_objects)} stress self-report objects")
        print(f"- {len(mood_events)} mood events")
        print(f"- {len(extended_data.get('objects', []))} total objects")
        print(f"- {len(extended_data.get('behaviorEvents', []))} total behavior events")
        
        # Serialize to JSON bytes using orjson
        json_bytes = orjson.dumps(
            extended_data,
            option=orjson.OPT_INDENT_2
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

    def link_stress_reports_to_notification_events(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        For each stress_self_report object, find the related notification object (via follows_notification).
        For that notification object, find all related notification events (behaviorEvents with relationship to the notification object).
        For each such notification event, add a relationship to the stress_self_report object with qualifier 'reports_stress'.
        Returns the updated data dictionary.
        """
        # Make a copy to avoid mutating input
        extended_data = data.copy()
        # Build lookup for stress_self_report objects
        stress_objects = [
            obj for obj in extended_data.get('objects', [])
            if obj['type'] == 'stress_self_report'
        ]
        # Build lookup for notification objects
        notification_objects = {
            obj['id']: obj for obj in extended_data.get('objects', [])
            if obj['type'] == 'notification'
        }
        # For each stress_self_report object
        for stress_obj in stress_objects:
            # Find related notification object via follows_notification
            notif_rel = next(
                (rel for rel in stress_obj.get('relationships', [])
                 if rel['type'] == 'object' and rel['qualifier'] == 'follows_notification'),
                None
            )
            if not notif_rel:
                continue
            notif_id = notif_rel['id']
            # Find all notification events related to this notification object
            for event in extended_data.get('behaviorEvents', []):
                # Check if event is a notification event and is related to this notification object
                if event.get('behaviorEventType') == 'notification':
                    if any(
                        rel['type'] == 'object' and rel['id'] == notif_id
                        for rel in event.get('relationships', [])
                    ):
                        # Add relationship FROM the notification event TO the stress_self_report object
                        if not any(
                            rel['type'] == 'object' and rel['id'] == stress_obj['id'] and rel['qualifier'] == 'reports_stress'
                            for rel in event.get('relationships', [])
                        ):
                            event.setdefault('relationships', []).append({
                                "id": stress_obj['id'],
                                "type": "object",
                                "qualifier": "reports_stress"
                            })
        return extended_data