from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import uuid
import orjson
from pathlib import Path
from tqdm import tqdm
import os
from .time_objects import TimeObject


class BoutEventManager:
    """Class for creating and managing physical activity bout events from OCED data."""
    
    def __init__(self):
        """Initialize the BoutEventManager class."""
        self.bout_event_type = {
            "name": "physical_activity_bout",
            "attributes": [
                {"name": "lifecycle", "type": "string"},
                {"name": "bout_type", "type": "string"}
            ]
        }
        self.bout_object_type = {
            "name": "physical_activity_bout",
            "attributes": [
                {"name": "bout_type", "type": "string"}
            ]
        }
        self.bout_events: List[Dict[str, Any]] = []
        self.bout_objects: Dict[str, Dict[str, Any]] = {}  # Maps bout ID to bout object
        self.time_manager = TimeObject()
    
    def create_bout_object_type(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add the physical activity bout object type to the OCED data if it doesn't exist.
        
        Args:
            data (Dict[str, Any]): The OCED data dictionary
            
        Returns:
            Dict[str, Any]: Updated OCED data dictionary with bout object type
        """
        # Create a copy of the input data to modify
        extended_data = data.copy()
        
        # Initialize objectTypes if it doesn't exist
        if 'objectTypes' not in extended_data:
            extended_data['objectTypes'] = []
        
        # Add bout object type if it doesn't exist
        if not any(obj_type['name'] == 'physical_activity_bout' 
                  for obj_type in extended_data['objectTypes']):
            extended_data['objectTypes'].append(self.bout_object_type)
            print("Physical activity bout object type added.")
        
        return extended_data
    
    def _create_bout_object(
        self,
        bout_id: str,
        bout_type: str,
        start_time: pd.Timestamp,
        end_time: pd.Timestamp,
        extended_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a bout object for a physical activity bout.
        
        Args:
            bout_id (str): Unique identifier for the bout
            bout_type (str): Type of physical activity bout (LIGHT_PA or MODERATE-VIGOROUS_PA)
            start_time (pd.Timestamp): Start time of the bout
            end_time (pd.Timestamp): End time of the bout
            extended_data (Dict[str, Any]): The OCED data dictionary
            
        Returns:
            Dict[str, Any]: The created bout object
        """
        # Initialize objects list if it doesn't exist
        if 'objects' not in extended_data:
            extended_data['objects'] = []
        
        # Create bout object with both start and end times
        bout_object = {
            "id": bout_id,
            "type": "physical_activity_bout",
            "attributes": [
                {
                    "name": "bout_type",
                    "value": bout_type,
                    "time": start_time.isoformat()
                },
                {
                    "name": "start_time",
                    "value": start_time.isoformat(),
                    "time": start_time.isoformat()
                },
                {
                    "name": "end_time",
                    "value": end_time.isoformat(),
                    "time": end_time.isoformat()
                }
            ],
            "relationships": []
        }
        
        # Add bout object to the data
        extended_data['objects'].append(bout_object)
        self.bout_objects[bout_id] = bout_object
        
        return bout_object
    
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
    
    def create_bout_event_type(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add the physical activity bout event type to the OCED data if it doesn't exist.
        
        Args:
            data (Dict[str, Any]): The OCED data dictionary
            
        Returns:
            Dict[str, Any]: Updated OCED data dictionary with bout event type
        """
        # Create a copy of the input data to modify
        extended_data = data.copy()
        
        # Initialize behaviorEventTypes if it doesn't exist
        if 'behaviorEventTypes' not in extended_data:
            extended_data['behaviorEventTypes'] = []
        
        # Add bout event type if it doesn't exist
        if not any(event_type['name'] == 'physical_activity_bout' 
                  for event_type in extended_data['behaviorEventTypes']):
            extended_data['behaviorEventTypes'].append(self.bout_event_type)
            print("Physical activity bout event type added.")
        
        return extended_data
    
    def create_bout_events(
        self,
        data: Dict[str, Any],
        bout_df: pd.DataFrame,
        user_id: str,
        bout_type: str,
        time_column: str = 'window_start',
        end_time_column: str = 'window_end'
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Create physical activity bout events and objects from the bout detection DataFrame.
        Only creates new objects and events if they don't already exist.
        
        Args:
            data (Dict[str, Any]): The OCED data dictionary containing day objects
            bout_df (pd.DataFrame): DataFrame containing bout detection results (all bouts of the same type)
            user_id (str): ID of the user object to relate events to
            bout_type (str): Type of physical activity bout ('LIGHT_PA' or 'MODERATE-VIGOROUS_PA')
            time_column (str): Name of the column containing start timestamps
            end_time_column (str): Name of the column containing end timestamps
            
        Returns:
            Tuple[Dict[str, Any], List[Dict[str, Any]]]: 
                - Extended OCED data dictionary with bout events and objects
                - List of created bout events
        """
        # Create a copy of the input data to modify
        extended_data = data.copy()
        
        # Initialize behaviorEvents if it doesn't exist
        if 'behaviorEvents' not in extended_data:
            extended_data['behaviorEvents'] = []
        
        # Initialize objects if it doesn't exist
        if 'objects' not in extended_data:
            extended_data['objects'] = []
        
        # Validate bout type
        if bout_type not in ['LIGHT_PA', 'MODERATE-VIGOROUS_PA']:
            raise ValueError("bout_type must be either 'LIGHT_PA' or 'MODERATE-VIGOROUS_PA'")
        
        # Get all unique bout periods (consecutive rows with same activity level)
        bout_df = bout_df.sort_values(time_column)
        bout_df['activity_change'] = bout_df[time_column].ne(bout_df[time_column].shift())
        bout_df['bout_group'] = bout_df['activity_change'].cumsum()
        
        # Get all unique bout groups
        unique_bouts = bout_df['bout_group'].unique()
        
        print(f"Processing {len(unique_bouts)} unique {bout_type} bouts...")
        
        # Helper function to check if a bout object already exists
        def bout_exists(start_time: pd.Timestamp, end_time: pd.Timestamp, bout_type: str) -> Optional[Dict[str, Any]]:
            for obj in extended_data['objects']:
                if obj['type'] != 'physical_activity_bout':
                    continue
                    
                # Check if this is a bout object of the right type
                bout_type_attr = next((attr for attr in obj['attributes'] 
                                     if attr['name'] == 'bout_type' and attr['value'] == bout_type), None)
                if not bout_type_attr:
                    continue
                
                # Get the bout's start and end events
                start_event = next((event for event in extended_data['behaviorEvents']
                                  if event['behaviorEventType'] == 'physical_activity_bout'
                                  and event['behaviorEventTypeAttributes'][0]['value'] == 'START'
                                  and any(rel['id'] == obj['id'] and rel['qualifier'] == 'starts'
                                        for rel in event['relationships'])), None)
                                        
                end_event = next((event for event in extended_data['behaviorEvents']
                                if event['behaviorEventType'] == 'physical_activity_bout'
                                and event['behaviorEventTypeAttributes'][0]['value'] == 'END'
                                and any(rel['id'] == obj['id'] and rel['qualifier'] == 'ends'
                                      for rel in event['relationships'])), None)
                
                if not start_event or not end_event:
                    continue
                
                # Check if times match
                if (pd.to_datetime(start_event['time']) == start_time and 
                    pd.to_datetime(end_event['time']) == end_time):
                    return obj
            
            return None
        
        # Process each bout
        for bout_group in tqdm(unique_bouts, desc=f"Creating {bout_type} bout events", unit="bout"):
            # Get all rows for this bout
            bout_data = bout_df[bout_df['bout_group'] == bout_group]
            
            if len(bout_data) == 0:
                continue
            
            # Get bout start and end times
            start_time = pd.to_datetime(bout_data[time_column].min())
            end_time = pd.to_datetime(bout_data[end_time_column].max())  # Use actual end time from data
            
            # Check if this bout already exists
            existing_bout = bout_exists(start_time, end_time, bout_type)
            if existing_bout:
                print(f"Skipping existing bout from {start_time} to {end_time}")
                continue
            
            # Get or create day object using TimeObject
            day_date = start_time.date().isoformat()
            try:
                day_object = self._create_day_object(day_date, extended_data)
            except ValueError as e:
                print(f"Warning: {e}")
                continue
            
            # Generate unique ID for this bout
            bout_id = str(uuid.uuid4())
            
            # Create bout object
            bout_object = self._create_bout_object(
                bout_id=bout_id,
                bout_type=bout_type,
                start_time=start_time,
                end_time=end_time,
                extended_data=extended_data
            )
            
            # Add relationship from bout object to day
            bout_object['relationships'].append({
                "id": day_object['id'],
                "type": "object",
                "qualifier": "occurred_on"
            })
            
            # Add relationship from bout object to user
            bout_object['relationships'].append({
                "id": user_id,
                "type": "object",
                "qualifier": "performed_by"
            })
            
            # Create START event
            start_event = {
                "id": str(uuid.uuid4()),
                "behaviorEventType": "physical_activity_bout",
                "time": start_time.isoformat(),  # ISO8601 format
                "behaviorEventTypeAttributes": [
                    {"name": "lifecycle", "value": "START"},
                    {"name": "bout_type", "value": bout_type}
                ],
                "relationships": [
                    {
                        "id": bout_object['id'],
                        "type": "object",
                        "qualifier": "starts"
                    },
                    {
                        "id": day_object['id'],
                        "type": "object",
                        "qualifier": "occurred_on"
                    },
                    {
                        "id": user_id,
                        "type": "object",
                        "qualifier": "performed_by"
                    }
                ]
            }
            
            # Create END event
            end_event = {
                "id": str(uuid.uuid4()),
                "behaviorEventType": "physical_activity_bout",
                "time": end_time.isoformat(),  # ISO8601 format
                "behaviorEventTypeAttributes": [
                    {"name": "lifecycle", "value": "END"},
                    {"name": "bout_type", "value": bout_type}
                ],
                "relationships": [
                    {
                        "id": bout_object['id'],
                        "type": "object",
                        "qualifier": "ends"
                    },
                    {
                        "id": day_object['id'],
                        "type": "object",
                        "qualifier": "occurred_on"
                    },
                    {
                        "id": user_id,
                        "type": "object",
                        "qualifier": "performed_by"
                    }
                ]
            }
            
            # Add events to the data
            extended_data['behaviorEvents'].extend([start_event, end_event])
            self.bout_events.extend([start_event, end_event])
        
        print(f"Created {len(self.bout_events)} bout events ({len(self.bout_events)//2} bouts)")
        print(f"Created {len(self.bout_objects)} bout objects")
        return extended_data, self.bout_events
    
    def get_bout_object(self, bout_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific bout object by ID.
        
        Args:
            bout_id (str): ID of the bout object
            
        Returns:
            Optional[Dict[str, Any]]: Bout object if found, None otherwise
        """
        return self.bout_objects.get(bout_id)
    
    def get_bouts_for_day(self, date_str: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get all bout objects for a specific day.
        
        Args:
            date_str (str): Date in YYYY-MM-DD format
            data (Dict[str, Any]): The OCED data dictionary
            
        Returns:
            List[Dict[str, Any]]: List of bout objects for the specified day
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
        
        # Get all bout objects for this day
        return [
            obj for obj in data.get('objects', [])
            if obj['type'] == 'physical_activity_bout'
            and any(rel['id'] == day_object['id'] for rel in obj.get('relationships', []))
        ]

    def save_extended_data(self, filename: str, extended_data: Dict[str, Any], compress: bool = False) -> None:
        """
        Save the extended OCED data to a JSON file in the data/transformed directory.
        Uses orjson for fast JSON serialization.
        
        Args:
            filename (str): Name of the file to save (e.g., 'physical_activity_bouts.json')
            extended_data (Dict[str, Any]): The extended OCED data dictionary containing bout events and objects
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
        bout_objects = [obj for obj in extended_data.get('objects', []) 
                       if obj['type'] == 'physical_activity_bout']
        bout_events = [event for event in extended_data.get('behaviorEvents', [])
                      if event['behaviorEventType'] == 'physical_activity_bout']
        
        print(f"\nSaving extended data with:")
        print(f"- {len(bout_objects)} bout objects")
        print(f"- {len(bout_events)} bout events ({len(bout_events)//2} bouts)")
        print(f"- {len(extended_data.get('objects', []))} total objects")
        print(f"- {len(extended_data.get('behaviorEvents', []))} total behavior events")
        
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

    def link_bout_events_to_report_objects(
        self,
        data: Dict[str, Any],
        time_period: timedelta = timedelta(hours=3)
    ) -> Dict[str, Any]:
        """
        For each physical activity bout START event, find the closest report event (mood events) 
        within a configurable time period that occurs AFTER the bout event. If a report event 
        is found, find its related report object (stress_self_report) and relate BOTH the START 
        and corresponding END events to this object.
        
        Args:
            data (Dict[str, Any]): The OCED data dictionary containing bout events and report events
            time_period (timedelta): Time window to look for nearby report events that occur after 
                                   the bout START event (default: 3 hours)
            
        Returns:
            Dict[str, Any]: Updated OCED data dictionary with new relationships in bout START and END events
        """
        # Create a copy of the input data to modify
        extended_data = data.copy()
        
        # Get all physical activity bout events
        bout_events = [
            event for event in extended_data.get('behaviorEvents', [])
            if event['behaviorEventType'] == 'physical_activity_bout'
        ]
        
        # Get all mood events (report events)
        mood_events = [
            event for event in extended_data.get('behaviorEvents', [])
            if event['behaviorEventType'] == 'mood'
        ]
        
        # Get all stress_self_report objects
        stress_objects = {
            obj['id']: obj for obj in extended_data.get('objects', [])
            if obj['type'] == 'stress_self_report'
        }
        
        if not bout_events:
            print("No physical activity bout events found in the data.")
            return extended_data
        
        if not mood_events:
            print("No mood events (report events) found in the data.")
            return extended_data
        
        # Separate START and END events
        start_events = [
            event for event in bout_events
            if event['behaviorEventTypeAttributes'][0]['value'] == 'START'
        ]
        
        end_events = [
            event for event in bout_events
            if event['behaviorEventTypeAttributes'][0]['value'] == 'END'
        ]
        
        print(f"\nProcessing {len(start_events)} bout START events")
        print(f"Looking for mood events within {time_period} AFTER each bout START event")
        
        linked_count = 0
        
        # Process each START event
        for start_event in tqdm(start_events, desc="Linking bout events to report objects"):
            start_time = pd.to_datetime(start_event['time'])
            
            # Find the closest mood event within the time period that occurs AFTER the START event
            closest_mood_event = None
            min_time_diff = time_period
            
            for mood_event in mood_events:
                mood_time = pd.to_datetime(mood_event['time'])
                
                # Only consider mood events that occur after the START event
                if mood_time > start_time:
                    time_diff = (mood_time - start_time).total_seconds()
                    
                    # Check if within time period and closer than current closest
                    if time_diff <= time_period.total_seconds() and time_diff < min_time_diff.total_seconds():
                        closest_mood_event = mood_event
                        min_time_diff = timedelta(seconds=time_diff)
            
            if not closest_mood_event:
                continue
            
            # Find the stress_self_report object related to this mood event
            stress_object_id = None
            for rel in closest_mood_event.get('relationships', []):
                if (rel['type'] == 'object' and 
                    rel['qualifier'] == 'reports_stress' and 
                    rel['id'] in stress_objects):
                    stress_object_id = rel['id']
                    break
            
            if not stress_object_id:
                continue
            
            # Find the corresponding END event for this bout object
            bout_object_id = None
            for rel in start_event.get('relationships', []):
                if (rel['type'] == 'object' and 
                    rel['qualifier'] == 'starts'):
                    bout_object_id = rel['id']
                    break
            
            if not bout_object_id:
                continue
            
            # Find the END event for this bout object
            corresponding_end_event = None
            for end_event in end_events:
                for rel in end_event.get('relationships', []):
                    if (rel['type'] == 'object' and 
                        rel['qualifier'] == 'ends' and 
                        rel['id'] == bout_object_id):
                        corresponding_end_event = end_event
                        break
                if corresponding_end_event:
                    break
            
            if not corresponding_end_event:
                continue
            
            # Add relationship from START event to stress_self_report object
            if 'relationships' not in start_event:
                start_event['relationships'] = []
            
            # Check if relationship already exists for START event
            if not any(
                rel['type'] == 'object' and 
                rel['id'] == stress_object_id and 
                rel['qualifier'] == 'related_to_report'
                for rel in start_event['relationships']
            ):
                start_event['relationships'].append({
                    "id": stress_object_id,
                    "type": "object",
                    "qualifier": "related_to_report"
                })
                linked_count += 1
            
            # Add relationship from END event to stress_self_report object
            if 'relationships' not in corresponding_end_event:
                corresponding_end_event['relationships'] = []
            
            # Check if relationship already exists for END event
            if not any(
                rel['type'] == 'object' and 
                rel['id'] == stress_object_id and 
                rel['qualifier'] == 'related_to_report'
                for rel in corresponding_end_event['relationships']
            ):
                corresponding_end_event['relationships'].append({
                    "id": stress_object_id,
                    "type": "object",
                    "qualifier": "related_to_report"
                })
                linked_count += 1
        
        print(f"\nLinking complete:")
        print(f"- Linked {linked_count} bout events (both START and END) to stress_self_report objects")
        print(f"- Time window used: {time_period}")
        print(f"- Processed {len(start_events)} START events to find corresponding END events")
        
        return extended_data

    def link_self_report_events_to_bout_objects(
        self,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        For each mood event (self report event), find the related stress_self_report object,
        then find ALL physical activity bout events that are related to this stress_self_report object
        with qualifier "related_to_report". Finally, add relationships from the mood event to ALL
        the physical activity bout objects with qualifier "influenced_by".
        
        Args:
            data (Dict[str, Any]): The OCED data dictionary containing mood events, bout events, 
                                  and their related objects
            
        Returns:
            Dict[str, Any]: Updated OCED data dictionary with new relationships in mood events
        """
        # Create a copy of the input data to modify
        extended_data = data.copy()
        
        # Get all mood events (self report events)
        mood_events = [
            event for event in extended_data.get('behaviorEvents', [])
            if event['behaviorEventType'] == 'mood'
        ]
        
        # Get all physical activity bout events
        bout_events = [
            event for event in extended_data.get('behaviorEvents', [])
            if event['behaviorEventType'] == 'physical_activity_bout'
        ]
        
        # Get all stress_self_report objects
        stress_objects = {
            obj['id']: obj for obj in extended_data.get('objects', [])
            if obj['type'] == 'stress_self_report'
        }
        
        # Get all physical activity bout objects
        bout_objects = {
            obj['id']: obj for obj in extended_data.get('objects', [])
            if obj['type'] == 'physical_activity_bout'
        }
        
        if not mood_events:
            print("No mood events found in the data.")
            return extended_data
        
        if not bout_events:
            print("No physical activity bout events found in the data.")
            return extended_data
        
        print(f"\nProcessing {len(mood_events)} mood events")
        print("Linking mood events to physical activity bout objects...")
        
        linked_count = 0
        
        # Process each mood event
        for mood_event in tqdm(mood_events, desc="Linking mood events to bout objects"):
            # Find the related stress_self_report object for this mood event
            stress_object_id = None
            for rel in mood_event.get('relationships', []):
                if (rel['type'] == 'object' and 
                    rel['qualifier'] == 'reports_stress' and 
                    rel['id'] in stress_objects):
                    stress_object_id = rel['id']
                    break
            
            if not stress_object_id:
                continue
            
            # Find ALL physical activity bout events that are related to this stress_self_report object
            related_bout_events = []
            for bout_event in bout_events:
                for rel in bout_event.get('relationships', []):
                    if (rel['type'] == 'object' and 
                        rel['qualifier'] == 'related_to_report' and 
                        rel['id'] == stress_object_id):
                        related_bout_events.append(bout_event)
                        break
            
            if not related_bout_events:
                continue
            
            # Collect all unique physical activity bout object IDs related to these bout events
            bout_object_ids = set()
            for bout_event in related_bout_events:
                for rel in bout_event.get('relationships', []):
                    if (rel['type'] == 'object' and 
                        rel['qualifier'] in ['starts', 'ends'] and 
                        rel['id'] in bout_objects):
                        bout_object_ids.add(rel['id'])
            
            if not bout_object_ids:
                continue
            
            # Add relationships from mood event to ALL physical activity bout objects
            if 'relationships' not in mood_event:
                mood_event['relationships'] = []
            
            # Add relationships for each unique bout object ID
            for bout_object_id in bout_object_ids:
                # Check if relationship already exists
                if not any(
                    rel['type'] == 'object' and 
                    rel['id'] == bout_object_id and 
                    rel['qualifier'] == 'influenced_by'
                    for rel in mood_event['relationships']
                ):
                    mood_event['relationships'].append({
                        "id": bout_object_id,
                        "type": "object",
                        "qualifier": "influenced_by"
                    })
                    linked_count += 1
        
        print(f"\nLinking complete:")
        print(f"- Linked {linked_count} mood events to physical activity bout objects")
        print(f"- Total relationships created: {linked_count}")
        print(f"- Relationship qualifier used: 'influenced_by'")
        print(f"- Each mood event can be linked to multiple bout objects")
        
        return extended_data
        