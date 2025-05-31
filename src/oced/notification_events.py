from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import uuid
import orjson
from pathlib import Path
from tqdm import tqdm
from .time_objects import TimeObject


class NotificationEventManager:
    """Class for creating and managing notification events and objects from OCED data."""
    
    def __init__(self):
        """Initialize the NotificationEventManager class."""
        self.notification_object_type = {
            "name": "notification",
            "attributes": [
                {"name": "last_action", "type": "string"}  # Last action performed on the notification (RECEIVED/READ)
            ]
        }
        self.notification_events: List[Dict[str, Any]] = []
        self.notification_objects: Dict[str, Dict[str, Any]] = {}  # Maps notification ID to notification object
        self.time_manager = TimeObject()
    
    def create_notification_object_type(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add the notification object type to the OCED data if it doesn't exist.
        
        Args:
            data (Dict[str, Any]): The OCED data dictionary
            
        Returns:
            Dict[str, Any]: Updated OCED data dictionary with notification object type
        """
        # Create a copy of the input data to modify
        extended_data = data.copy()
        
        # Initialize objectTypes if it doesn't exist
        if 'objectTypes' not in extended_data:
            extended_data['objectTypes'] = []
        
        # Add notification object type if it doesn't exist
        if not any(obj_type['name'] == 'notification' 
                  for obj_type in extended_data['objectTypes']):
            extended_data['objectTypes'].append(self.notification_object_type)
            print("Notification object type added.")
        
        return extended_data
    
    def _create_notification_object(
        self,
        notification_id: str,
        action: str,
        timestamp: pd.Timestamp,
        extended_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create a notification object.
        
        Args:
            notification_id (str): Unique identifier for the notification
            action (str): Last action performed on the notification (RECEIVED/READ)
            timestamp (pd.Timestamp): Timestamp for the last action
            extended_data (Dict[str, Any]): The OCED data dictionary
            
        Returns:
            Dict[str, Any]: The created notification object
        """
        # Initialize objects list if it doesn't exist
        if extended_data and 'objects' not in extended_data:
            extended_data['objects'] = []
        
        # Create notification object with timestamped attribute
        notification_object = {
            "id": notification_id,
            "type": "notification",
            "attributes": [
                {
                    "name": "last_action",
                    "value": action,
                    "time": timestamp.isoformat()
                }
            ],
            "relationships": []
        }
        
        # Add notification object to the data if provided
        if extended_data:
            extended_data['objects'].append(notification_object)
        
        self.notification_objects[notification_id] = notification_object
        
        return notification_object
    
    def _update_notification_object_action(
        self,
        notification_id: str,
        action: str,
        timestamp: pd.Timestamp,
        extended_data: Dict[str, Any]
    ) -> None:
        """
        Update the last_action attribute of a notification object.
        
        Args:
            notification_id (str): ID of the notification object to update
            action (str): New last action (RECEIVED/READ)
            timestamp (pd.Timestamp): Timestamp of the new action
            extended_data (Dict[str, Any]): The OCED data dictionary
        """
        # Find and update the notification object in both our cache and the extended data
        notification_object = self.notification_objects.get(notification_id)
        if notification_object:
            # Update in our cache
            for attr in notification_object['attributes']:
                if attr['name'] == 'last_action':
                    attr['value'] = action
                    attr['time'] = timestamp.isoformat()
                    break
            
            # Update in extended data
            for obj in extended_data.get('objects', []):
                if obj['id'] == notification_id:
                    for attr in obj['attributes']:
                        if attr['name'] == 'last_action':
                            attr['value'] = action
                            attr['time'] = timestamp.isoformat()
                            break
                    break
    
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
    
    def create_notification_objects(
        self,
        data: Dict[str, Any],
        user_id: str
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Create notification objects and link them to existing notification events.
        Each notification object represents a single notification that can be received and read.
        The object is created when a notification is received and linked to any subsequent read events.
        The last_action attribute tracks the most recent action (RECEIVED/READ) performed on the notification.
        
        Args:
            data (Dict[str, Any]): The OCED data dictionary containing notification events
            user_id (str): ID of the user object to relate notifications to
            
        Returns:
            Tuple[Dict[str, Any], List[Dict[str, Any]]]: 
                - Extended OCED data dictionary with notification objects
                - List of created notification objects
        """
        # Create a copy of the input data to modify
        extended_data = data.copy()
        
        # Initialize objects if it doesn't exist
        if 'objects' not in extended_data:
            extended_data['objects'] = []
        
        # Get all notification events
        notification_events = [
            event for event in extended_data.get('behaviorEvents', [])
            if event['behaviorEventType'] == 'notification'
        ]
        
        if not notification_events:
            print("No notification events found in the data.")
            return extended_data, []
        
        print(f"\nFound {len(notification_events)} notification events")
        
        # Check for existing notification objects
        existing_notifications = {
            obj['id']: obj for obj in extended_data.get('objects', [])
            if obj['type'] == 'notification'
        }
        print(f"Found {len(existing_notifications)} existing notification objects")
        
        # Sort all events by time
        notification_events.sort(key=lambda x: pd.to_datetime(x['time']))
        
        # Track notification objects by their received time
        notification_map = {}  # Maps received_time to notification_id
        
        # Process events chronologically
        for event in tqdm(notification_events, desc="Processing notification events"):
            # Get action from event attributes
            action = next(
                (attr['value'].upper() for attr in event['behaviorEventTypeAttributes']
                 if attr['name'] == 'action'),
                None
            )
            
            if not action or action not in ['RECEIVED', 'READ']:
                print(f"Skipping event with invalid action: {action}")
                continue
            
            event_time = pd.to_datetime(event['time'])
            
            # Check if this event is already linked to a notification object
            existing_links = [
                rel for rel in event.get('relationships', [])
                if rel['type'] == 'object' and rel['qualifier'] in ['notifies', 'reads']
            ]
            
            if existing_links:
                print(f"Event at {event_time} already linked to notification(s): {existing_links}")
                continue
            
            if action == 'RECEIVED':
                # Check if we already have a notification object for this event
                # We can do this by checking if the event is already linked to a notification
                if existing_links:
                    notification_id = existing_links[0]['id']
                    print(f"Using existing notification object {notification_id} for received event")
                else:
                    # Create a new notification object for this received event
                    notification_id = str(uuid.uuid4())
                    print(f"Creating new notification object {notification_id} for received event")
                    notification_object = self._create_notification_object(
                        notification_id=notification_id,
                        action='RECEIVED',
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
                    notification_object['relationships'].extend([
                        {
                            "id": day_object['id'],
                            "type": "object",
                            "qualifier": "occurred_on"
                        },
                        {
                            "id": user_id,
                            "type": "object",
                            "qualifier": "received_by"
                        }
                    ])
                
                # Add relationship from received event to notification object
                event['relationships'].append({
                    "id": notification_id,
                    "type": "object",
                    "qualifier": "notifies"
                })
                
                # Store this notification in our map
                notification_map[event_time] = notification_id
                
            elif action == 'READ':
                # Find the most recent received notification that occurred before this read event
                matching_notifications = [
                    (received_time, notif_id) 
                    for received_time, notif_id in notification_map.items()
                    if received_time < event_time
                ]
                
                if matching_notifications:
                    # Get the most recent received notification
                    received_time, notification_id = max(matching_notifications, key=lambda x: x[0])
                    print(f"Linking read event to notification {notification_id} (received at {received_time})")
                    
                    # Update the notification object's last_action to READ
                    self._update_notification_object_action(
                        notification_id=notification_id,
                        action='READ',
                        timestamp=event_time,
                        extended_data=extended_data
                    )
                    
                    # Add relationship from read event to notification object
                    event['relationships'].append({
                        "id": notification_id,
                        "type": "object",
                        "qualifier": "reads"
                    })
                else:
                    print(f"Warning: Found read event at {event_time} without matching received event")
        
        # Get final list of notification objects
        notification_objects = [
            obj for obj in extended_data.get('objects', [])
            if obj['type'] == 'notification'
        ]
        
        print(f"\nProcessing complete:")
        print(f"- Created {len(notification_objects) - len(existing_notifications)} new notification objects")
        print(f"- Total notification objects: {len(notification_objects)}")
        
        return extended_data, notification_objects
    
    def get_notification_object(self, notification_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific notification object by ID.
        
        Args:
            notification_id (str): ID of the notification object
            
        Returns:
            Optional[Dict[str, Any]]: Notification object if found, None otherwise
        """
        return self.notification_objects.get(notification_id)
    
    def get_notifications_for_day(self, date_str: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get all notification objects for a specific day.
        
        Args:
            date_str (str): Date in YYYY-MM-DD format
            data (Dict[str, Any]): The OCED data dictionary
            
        Returns:
            List[Dict[str, Any]]: List of notification objects for the specified day
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
        
        # Get all notification objects for this day
        return [
            obj for obj in data.get('objects', [])
            if obj['type'] == 'notification'
            and any(rel['id'] == day_object['id'] for rel in obj.get('relationships', []))
        ]
    
    def save_extended_data(self, filename: str, extended_data: Dict[str, Any], compress: bool = False) -> None:
        """
        Save the extended OCED data to a JSON file in the data/transformed directory.
        Uses orjson for fast JSON serialization.
        
        Args:
            filename (str): Name of the file to save (e.g., 'notifications.json')
            extended_data (Dict[str, Any]): The extended OCED data dictionary containing notification objects
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
        notification_objects = [obj for obj in extended_data.get('objects', []) 
                              if obj['type'] == 'notification']
        notification_events = [event for event in extended_data.get('behaviorEvents', [])
                             if event['behaviorEventType'] == 'notification']
        
        print(f"\nSaving extended data with:")
        print(f"- {len(notification_objects)} notification objects")
        print(f"- {len(notification_events)} notification events")
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