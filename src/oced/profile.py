"""
Profile class for creating and transforming OCED (Observed Contextual Event Data) profiles.
"""
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path


class OCEDProfile:
    """
    Class for creating and transforming OCED profiles from JSON files.
    
    This class provides methods to:
    1. Load OCED data from JSON files
    2. Transform mood events to stress self-report events
    3. Transform physical activity bout events to START/END events
    """
    
    def __init__(self, json_file_path: str):
        """
        Initialize the OCED Profile with JSON file path.
        
        Args:
            json_file_path (str): Path to the JSON file containing OCED data
        """
        self.json_file_path = Path(json_file_path)
        self.oced_data = self._load_json_data()
        
    def _load_json_data(self) -> Dict[str, Any]:
        """
        Load OCED data from JSON file.
        
        Returns:
            Dict[str, Any]: The loaded OCED data
        """
        if not self.json_file_path.exists():
            raise FileNotFoundError(f"JSON file not found: {self.json_file_path}")
        
        with open(self.json_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _deep_copy_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a deep copy of a dictionary.
        
        Args:
            data (Dict[str, Any]): The dictionary to copy
            
        Returns:
            Dict[str, Any]: A deep copy of the input dictionary
        """
        if not isinstance(data, dict):
            return data
        
        copied_data = {}
        for key, value in data.items():
            if isinstance(value, dict):
                copied_data[key] = self._deep_copy_dict(value)
            elif isinstance(value, list):
                copied_data[key] = [self._deep_copy_dict(item) if isinstance(item, dict) else item for item in value]
            else:
                copied_data[key] = value
        
        return copied_data
    
    def transform_mood_to_stress_events(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Transform mood events to stress self-report events.
        
        Args:
            data (Optional[Dict[str, Any]]): Data to transform. If None, uses the original data.
        
        Changes:
        1. Renames 'mood' event type to 'stress_self_report'
        2. Updates all mood events to use the new event type and name
        3. Keeps only the 'stress' attribute, removes 'valence' and 'arousal'
        
        Returns:
            Dict[str, Any]: Transformed OCED data with stress events
        """
        if data is None:
            data = self.oced_data
        transformed_data = self._deep_copy_dict(data)
        
        # Initialize eventTypes if it doesn't exist
        if 'eventTypes' not in transformed_data:
            transformed_data['eventTypes'] = []
        
        # Find and update the mood event type to stress_self_report
        mood_event_type = None
        for event_type in transformed_data['eventTypes']:
            if event_type['name'] == 'mood':
                mood_event_type = event_type
                break
        
        if mood_event_type:
            # Update the event type name and keep only stress attribute
            mood_event_type['name'] = 'stress_self_report'
            mood_event_type['attributes'] = [
                {"name": "stress", "type": "number"}
            ]
        else:
            # Add new stress_self_report event type if mood doesn't exist
            transformed_data['eventTypes'].append({
                "name": "stress_self_report",
                "attributes": [
                    {"name": "stress", "type": "number"}
                ]
            })
        
        # Transform mood events to stress events
        if 'events' in transformed_data:
            for event in transformed_data['events']:
                if event.get('type') == 'mood':
                    # Change event type
                    event['type'] = 'stress_self_report'
                    
                    # Change event name if it exists
                    if 'name' in event:
                        event['name'] = 'stress_self_report'
                    
                    # Keep only stress attribute, remove valence and arousal
                    stress_value = None
                    for attr in event.get('attributes', []):
                        if attr['name'] == 'stress':
                            stress_value = attr['value']
                            break
                    
                    # Update attributes to only include stress
                    if stress_value is not None:
                        event['attributes'] = [
                            {"name": "stress", "value": stress_value}
                        ]
                    else:
                        # Remove event if no stress value found
                        event['attributes'] = []
        
        return transformed_data
    
    def transform_physical_activity_to_start_end_events(self, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Transform physical activity bout events to START and END events.
        
        Args:
            data (Optional[Dict[str, Any]]): Data to transform. If None, uses the original data.
        
        Changes:
        1. Creates 'physical_activity_bout_START' and 'physical_activity_bout_END' event types
        2. Transforms events based on their 'lifecycle' attribute
        3. Keeps only the 'bout_type' attribute in transformed events
        
        Returns:
            Dict[str, Any]: Transformed OCED data with START/END events
        """
        if data is None:
            data = self.oced_data
        transformed_data = self._deep_copy_dict(data)
        
        # Initialize eventTypes if it doesn't exist
        if 'eventTypes' not in transformed_data:
            transformed_data['eventTypes'] = []
        
        # Add new event types
        start_event_type = {
            "name": "physical_activity_bout_START",
            "attributes": [
                {"name": "bout_type", "type": "string"}
            ]
        }
        
        end_event_type = {
            "name": "physical_activity_bout_END",
            "attributes": [
                {"name": "bout_type", "type": "string"}
            ]
        }
        
        # Add event types if they don't exist
        existing_names = [et['name'] for et in transformed_data['eventTypes']]
        if 'physical_activity_bout_START' not in existing_names:
            transformed_data['eventTypes'].append(start_event_type)
        if 'physical_activity_bout_END' not in existing_names:
            transformed_data['eventTypes'].append(end_event_type)
        
        # Transform physical activity bout events
        if 'events' in transformed_data:
            for event in transformed_data['events']:
                if event.get('type') == 'physical_activity_bout':
                    # Extract lifecycle and bout_type
                    lifecycle = None
                    bout_type = None
                    
                    for attr in event.get('attributes', []):
                        if attr['name'] == 'lifecycle':
                            lifecycle = attr['value']
                        elif attr['name'] == 'bout_type':
                            bout_type = attr['value']
                    
                    # Determine new event type based on lifecycle
                    if lifecycle and lifecycle.upper() in ['START', 'BEGIN', 'STARTED']:
                        event['type'] = 'physical_activity_bout_START'
                    elif lifecycle and lifecycle.upper() in ['END', 'FINISH', 'COMPLETE', 'FINISHED']:
                        event['type'] = 'physical_activity_bout_END'
                    else:
                        # Skip events with unknown lifecycle
                        continue
                    
                    # Keep only bout_type attribute
                    if bout_type is not None:
                        event['attributes'] = [
                            {"name": "bout_type", "value": bout_type}
                        ]
                    else:
                        event['attributes'] = []
        
        return transformed_data
    
    def create_transformed_profile(self, transform_mood: bool = True, transform_physical_activity: bool = True) -> Dict[str, Any]:
        """
        Create a complete transformed profile.
        
        Args:
            transform_mood (bool): Whether to transform mood events to stress events
            transform_physical_activity (bool): Whether to transform physical activity events to START/END events
            
        Returns:
            Dict[str, Any]: The complete transformed profile
        """
        profile_data = self._deep_copy_dict(self.oced_data)
        
        if transform_mood:
            profile_data = self.transform_mood_to_stress_events(profile_data)
        
        if transform_physical_activity:
            profile_data = self.transform_physical_activity_to_start_end_events(profile_data)
        
        return profile_data
    
    def save_profile(self, output_path: str, profile_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Save the profile to a JSON file.
        
        Args:
            output_path (str): Path where to save the profile JSON file
            profile_data (Optional[Dict[str, Any]]): Profile data to save. If None, uses the original data.
        """
        if profile_data is None:
            profile_data = self.oced_data
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, indent=2, ensure_ascii=False)
    
    def get_event_statistics(self, profile_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get statistics about events in the profile.
        
        Args:
            profile_data (Optional[Dict[str, Any]]): Profile data to analyze. If None, uses the original data.
            
        Returns:
            Dict[str, Any]: Statistics about the events
        """
        if profile_data is None:
            profile_data = self.oced_data
        
        stats = {
            'total_events': 0,
            'event_types': {},
            'sensor_events': 0,
            'behavior_events': 0
        }
        
        # Count events (OCEL format)
        events = profile_data.get('events', [])
        stats['behavior_events'] = len(events)
        stats['total_events'] = len(events)
        
        for event in events:
            event_type = event.get('type', 'unknown')
            stats['event_types'][event_type] = stats['event_types'].get(event_type, 0) + 1
        
        return stats 