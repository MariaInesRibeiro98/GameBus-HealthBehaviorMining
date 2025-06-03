from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Literal
import pandas as pd
import uuid
import orjson
from pathlib import Path
from tqdm import tqdm
from .time_objects import TimeObject
import math

class LocationEventManager:
    """Class for creating and managing location events and objects from location sensor data."""
    
    def __init__(self):
        """Initialize the LocationEventManager class."""
        self.location_event_type = {
            "name": "location_event",
            "attributes": [
                {"name": "lifecycle", "type": "string"},  # "Entering" or "Exiting"
                {"name": "location_type", "type": "string"}  # Type of location (e.g., "home", "work", "in_transit")
            ]
        }
        self.location_object_type = {
            "name": "location_segment",
            "attributes": [
                {"name": "location_type", "type": "string"},
                {"name": "start_time", "type": "string"},
                {"name": "end_time", "type": "string"}
            ]
        }
        self.location_events: List[Dict[str, Any]] = []
        self.location_objects: Dict[str, Dict[str, Any]] = {}  # Maps location segment ID to location object
        self.time_manager = TimeObject()
    
    def create_location_event_type(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add the location event type to the OCED data if it doesn't exist."""
        extended_data = data.copy()
        if 'behaviorEventTypes' not in extended_data:
            extended_data['behaviorEventTypes'] = []
        if not any(event_type['name'] == 'location_event' 
                  for event_type in extended_data['behaviorEventTypes']):
            extended_data['behaviorEventTypes'].append(self.location_event_type)
        return extended_data
    
    def create_location_object_type(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add the location segment object type to the OCED data if it doesn't exist."""
        extended_data = data.copy()
        if 'objectTypes' not in extended_data:
            extended_data['objectTypes'] = []
        if not any(obj_type['name'] == 'location_segment' 
                  for obj_type in extended_data['objectTypes']):
            extended_data['objectTypes'].append(self.location_object_type)
        return extended_data
    
    def _create_location_event(
        self,
        event_id: str,
        lifecycle: str,
        location_type: str,
        timestamp: pd.Timestamp,
        sensor_event_id: str,
        extended_data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """Create a location event (Entering or Exiting)."""
        # Get day object for this timestamp using the new method
        day_date = timestamp.date().isoformat()
        day_object = self._create_day_object(day_date, extended_data)
        
        location_event = {
            "id": event_id,
            "behaviorEventType": "location_event",
            "time": timestamp.isoformat(),
            "attributes": [
                {
                    "name": "lifecycle",
                    "value": lifecycle
                },
                {
                    "name": "location_type",
                    "value": location_type
                }
            ],
            "relationships": [
                {
                    "type": "object",
                    "id": sensor_event_id,
                    "qualifier": "derived_from"
                },
                {
                    "type": "object",
                    "id": user_id,
                    "qualifier": "performed_by"
                },
                {
                    "type": "object",
                    "id": day_object['id'],
                    "qualifier": "occurred_on"
                }
            ]
        }
        extended_data['behaviorEvents'].append(location_event)
        self.location_events.append(location_event)
        return location_event, day_object['id']
    
    def _create_location_object(
        self,
        location_id: str,
        location_type: str,
        start_time: pd.Timestamp,
        end_time: pd.Timestamp,
        enter_event_id: str,
        exit_event_id: str,
        extended_data: Dict[str, Any],
        user_id: str,
        day_id: str
    ) -> Dict[str, Any]:
        """Create a location segment object linking enter and exit events."""
        # Convert timestamps to ISO format strings for time fields
        start_time_str = start_time.isoformat()
        end_time_str = end_time.isoformat()
        
        # Format datetime values as strings for value fields
        start_time_value = start_time.strftime("%Y-%m-%d %H:%M:%S")
        end_time_value = end_time.strftime("%Y-%m-%d %H:%M:%S")
        
        location_object = {
            "id": location_id,
            "type": "location_segment",
            "attributes": [
                {
                    "name": "location_type",
                    "value": location_type,
                    "time": start_time_str
                },
                {
                    "name": "start_time",
                    "value": start_time_value,
                    "time": start_time_str
                },
                {
                    "name": "end_time",
                    "value": end_time_value,
                    "time": end_time_str
                }
            ],
            "relationships": [
                {
                    "type": "behaviorEvent",
                    "id": enter_event_id,
                    "qualifier": "enters"
                },
                {
                    "type": "behaviorEvent",
                    "id": exit_event_id,
                    "qualifier": "exits"
                },
                {
                    "type": "object",
                    "id": user_id,
                    "qualifier": "performed_by"
                },
                {
                    "type": "object",
                    "id": day_id,
                    "qualifier": "occurred_on"
                }
            ]
        }
        extended_data['objects'].append(location_object)
        self.location_objects[location_id] = location_object
        return location_object

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

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the Haversine distance between two points in meters.
        
        Args:
            lat1, lon1: Coordinates of first point
            lat2, lon2: Coordinates of second point
            
        Returns:
            float: Distance in meters
        """
        R = 6371000  # Earth's radius in meters
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance

    def _get_location_state(
        self,
        lat: float,
        lon: float,
        prev_lat: Optional[float],
        prev_lon: Optional[float],
        prev_time: Optional[datetime],
        curr_time: datetime,
        location_geofences: Dict[str, Dict[str, Any]],
        transit_distance_threshold: float,
        transit_time_threshold: timedelta,
        is_invalid_gps: bool = False,
        invalid_gps_duration: Optional[timedelta] = None,
        invalid_gps_duration_threshold: Optional[timedelta] = None,
        prev_state: Optional[str] = None,
        prev_location: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        """
        Determine the location state based on coordinates and previous state.
        For overlapping geofences, assigns the point to the geofence with the closest center.
        Handles invalid GPS coordinates (200, 200) by maintaining previous geofence state under certain conditions.
        
        Args:
            lat, lon: Current coordinates (may be invalid GPS values)
            prev_lat, prev_lon: Previous coordinates (if any)
            prev_time: Previous timestamp (if any)
            curr_time: Current timestamp
            location_geofences: Dictionary of location geofences
            transit_distance_threshold: Distance threshold for transit (meters)
            transit_time_threshold: Time threshold for transit
            is_invalid_gps: Whether the current coordinates are invalid GPS values (200, 200)
            invalid_gps_duration: Duration of the current invalid GPS period (if any)
            invalid_gps_duration_threshold: Maximum duration to maintain previous state during invalid GPS
            prev_state: Previous location state
            prev_location: Previous location name (if in a geofence)
            
        Returns:
            Tuple[str, Optional[str]]: (state, location_name)
            state can be: "in_transit", "geofence", "other", or "invalid_gps"
            location_name is the name of the geofence if state is "geofence", None otherwise
        """
        # Handle invalid GPS coordinates (200, 200)
        if is_invalid_gps:
            # If we have a previous state and it was in a geofence
            if prev_state == "geofence" and prev_location is not None:
                # Check if invalid GPS duration exceeds threshold
                if invalid_gps_duration is not None and invalid_gps_duration_threshold is not None:
                    if invalid_gps_duration > invalid_gps_duration_threshold:
                        return "invalid_gps", None
                # Maintain previous geofence state
                return "geofence", prev_location
            # If not in a geofence before invalid GPS
            elif prev_state is not None:
                # For short invalid GPS periods, maintain "other" state
                if invalid_gps_duration is not None and invalid_gps_duration_threshold is not None:
                    if invalid_gps_duration <= invalid_gps_duration_threshold:
                        return "other", None
                # For longer periods, return "invalid_gps" state
                return "invalid_gps", None
            # If no previous state, return "invalid_gps"
            return "invalid_gps", None

        # Check for transit (only for valid GPS values)
        if prev_lat is not None and prev_lon is not None and prev_time is not None:
            distance = self._calculate_distance(lat, lon, prev_lat, prev_lon)
            time_diff = curr_time - prev_time
            
            if distance > transit_distance_threshold and time_diff < transit_time_threshold:
                return "in_transit", None
        
        # Check geofences - find the closest one that contains the point
        closest_geofence = None
        min_distance = float('inf')
        
        for loc_name, geofence in location_geofences.items():
            # Calculate distance to geofence center
            distance_to_center = self._calculate_distance(
                lat, lon,
                geofence['latitude'],
                geofence['longitude']
            )
            
            # If point is within geofence radius and closer than current closest
            if distance_to_center <= geofence['radius'] and distance_to_center < min_distance:
                closest_geofence = loc_name
                min_distance = distance_to_center
        
        if closest_geofence is not None:
            return "geofence", closest_geofence
        
        # If not in transit and not in any geofence
        return "other", None

    def create_location_events_and_objects(
        self,
        data: Dict[str, Any],
        sensor_events: List[Dict[str, Any]],
        user_id: str,
        location_geofences: Dict[str, Dict[str, Any]],
        transit_distance_threshold: float = 50.0,
        transit_time_threshold: timedelta = timedelta(minutes=2),
        min_segment_duration: timedelta = timedelta(minutes=5),
        invalid_gps_duration_threshold: timedelta = timedelta(minutes=30),
        default_home_geofence: str = "home"  # Name of the home geofence
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Create location events and objects from location sensor data.
        Only creates events for the final merged segments.
        """
        extended_data = data.copy()
        
        # Initialize required lists if they don't exist
        if 'behaviorEvents' not in extended_data:
            extended_data['behaviorEvents'] = []
        if 'objects' not in extended_data:
            extended_data['objects'] = []
        
        # Sort sensor events by time
        sorted_events = sorted(
            sensor_events,
            key=lambda x: datetime.fromisoformat(x['time'].replace('Z', '+00:00'))
        )
        
        if not sorted_events:
            return extended_data, []
        
        # Group events by day
        events_by_day = {}
        for event in sorted_events:
            event_time = datetime.fromisoformat(event['time'].replace('Z', '+00:00'))
            day_str = event_time.strftime('%Y-%m-%d')
            if day_str not in events_by_day:
                events_by_day[day_str] = []
            events_by_day[day_str].append(event)
        
        # Process each day separately
        all_segments = []  # Store intermediate segments before merging
        
        for day_str, day_events in events_by_day.items():
            # Get day object for this date using the new method
            day_object = self._create_day_object(day_str, extended_data)
            day_id = day_object['id']
            
            # Initialize tracking variables for this day
            current_state = None
            current_location = None
            segment_start_time = None
            segment_start_event = None
            prev_lat = None
            prev_lon = None
            prev_time = None
            invalid_gps_start_time = None
            is_first_valid_point = True
            
            # Process each sensor event for this day
            for i, event in enumerate(day_events):
                # Extract event data
                event_time = datetime.fromisoformat(event['time'].replace('Z', '+00:00'))
                
                # Extract coordinates, handling invalid GPS values (200, 200)
                try:
                    lat = next(attr['value'] for attr in event['sensorEventTypeAttributes'] 
                              if attr['name'] == 'latitude')
                    lon = next(attr['value'] for attr in event['sensorEventTypeAttributes'] 
                              if attr['name'] == 'longitude')
                    is_invalid_gps = (lat == 200.0 and lon == 200.0)
                except (StopIteration, ValueError):
                    lat = lon = 200.0
                    is_invalid_gps = True
                
                # Calculate invalid GPS duration if applicable
                invalid_gps_duration = None
                if is_invalid_gps:
                    if invalid_gps_start_time is None:
                        invalid_gps_start_time = event_time
                    invalid_gps_duration = event_time - invalid_gps_start_time
                else:
                    invalid_gps_start_time = None
                
                # Special handling for first valid point of the day
                if is_first_valid_point and is_invalid_gps:
                    # Assume user is at home for first invalid points
                    state = "geofence"
                    location_name = default_home_geofence
                else:
                    # Determine location state
                    state, location_name = self._get_location_state(
                        lat, lon, prev_lat, prev_lon, prev_time, event_time,
                        location_geofences, transit_distance_threshold, transit_time_threshold,
                        is_invalid_gps, invalid_gps_duration, invalid_gps_duration_threshold,
                        current_state, current_location
                    )
                
                # Handle state changes
                if state != current_state or (state == "geofence" and location_name != current_location):
                    # If we have a previous segment, check if it's long enough
                    if segment_start_time is not None:
                        segment_duration = event_time - segment_start_time
                        if segment_duration >= min_segment_duration:
                            # Store segment information (without creating events yet)
                            all_segments.append({
                                'location_type': current_location if current_state == "geofence" else current_state,
                                'start_time': segment_start_time,
                                'end_time': event_time,
                                'start_event': segment_start_event,
                                'end_event': event,
                                'day_id': day_id  # Store day_id with segment
                            })
                    
                    # Update tracking variables
                    current_state = state
                    current_location = location_name
                    segment_start_time = event_time
                    segment_start_event = event
                
                # Update previous values (only for valid GPS values)
                if not is_invalid_gps:
                    prev_lat = lat
                    prev_lon = lon
                    prev_time = event_time
                    is_first_valid_point = False
            
            # Handle the last segment of the day
            if segment_start_time is not None and segment_start_event is not None:
                last_event = day_events[-1]
                last_time = datetime.fromisoformat(last_event['time'].replace('Z', '+00:00'))
                segment_duration = last_time - segment_start_time
                
                if segment_duration >= min_segment_duration:
                    all_segments.append({
                        'location_type': current_location if current_state == "geofence" else current_state,
                        'start_time': segment_start_time,
                        'end_time': last_time,
                        'start_event': segment_start_event,
                        'end_event': last_event,
                        'day_id': day_id  # Store day_id with segment
                    })
        
        # Merge consecutive segments of the same type
        merged_segments = []
        i = 0
        while i < len(all_segments):
            current = all_segments[i]
            
            # Look ahead for consecutive segments of the same type
            j = i + 1
            while j < len(all_segments):
                next_segment = all_segments[j]
                if next_segment['location_type'] != current['location_type']:
                    break
                
                # Merge segments
                current['end_time'] = next_segment['end_time']
                current['end_event'] = next_segment['end_event']
                j += 1
            
            merged_segments.append(current)
            i = j
        
        # Create events and objects only for the final merged segments
        location_events = []
        location_objects = {}
        
        for segment in merged_segments:
            # Create enter event
            enter_event_id = str(uuid.uuid4())
            enter_event, day_id = self._create_location_event(
                enter_event_id,
                "Entering",
                segment['location_type'],
                segment['start_time'],
                segment['start_event']['id'],
                extended_data,
                user_id
            )
            location_events.append(enter_event)
            
            # Create exit event
            exit_event_id = str(uuid.uuid4())
            exit_event, _ = self._create_location_event(
                exit_event_id,
                "Exiting",
                segment['location_type'],
                segment['end_time'],
                segment['end_event']['id'],
                extended_data,
                user_id
            )
            location_events.append(exit_event)
            
            # Create location segment object
            segment_id = str(uuid.uuid4())
            segment_obj = self._create_location_object(
                segment_id,
                segment['location_type'],
                segment['start_time'],
                segment['end_time'],
                enter_event_id,
                exit_event_id,
                extended_data,
                user_id,
                day_id
            )
            location_objects[segment_id] = segment_obj
        
        # Update location_events and location_objects
        self.location_events = location_events
        self.location_objects = location_objects
        
        return extended_data, self.location_events

    def relate_location_to_pa_bouts(
        self,
        extended_data: Dict[str, Any],
        pa_event_type: str = "pa_bout_event"  # Type of PA bout atomic events
    ) -> Dict[str, Any]:
        """
        Add relationships from PA bout objects to overlapping location segments.
        Uses the relationships between PA bout atomic events and location segments to determine
        which location segments each PA bout overlaps with.
        
        Args:
            extended_data (Dict[str, Any]): The OCED data dictionary containing all objects and events
            pa_event_type (str): The type of PA bout atomic events to process
            
        Returns:
            Dict[str, Any]: Updated extended data with new relationships in PA bout objects
        """
        # First, ensure all PA events are related to locations
        extended_data = self.relate_pa_events_to_locations(extended_data, pa_event_type)
        
        # Get all PA bout objects
        pa_bout_objects = [
            obj for obj in extended_data.get('objects', [])
            if obj['type'] == 'physical_activity_bout'
        ]
        
        # Get all PA bout atomic events
        pa_events = [
            event for event in extended_data.get('behaviorEvents', [])
            if event['behaviorEventType'] == "physical_activity_bout"
        ]
        
        # Create a mapping of bout ID to its events by looking at event relationships
        bout_to_events = {}
        for event in pa_events:
            # Look for the relationship in the event's relationships
            for rel in event.get('relationships', []):
                if (rel['type'] == 'object' and 
                    rel['qualifier'] in ['starts', 'ends'] and 
                    any(bout['id'] == rel['id'] for bout in pa_bout_objects)):
                    bout_id = rel['id']
                    if bout_id not in bout_to_events:
                        bout_to_events[bout_id] = []
                    bout_to_events[bout_id].append(event)
                    # Don't break here as an event might both start and end a bout
        
        print(f"Found {len(bout_to_events)} bouts with associated events")
        for bout_id, events in bout_to_events.items():
            print(f"Bout {bout_id} has {len(events)} events")
            # Print the qualifiers for each event in this bout
            for event in events:
                bout_rels = [rel for rel in event.get('relationships', [])
                           if rel['type'] == 'object' and rel['id'] == bout_id]
                print(f"  Event {event['id']} relationships: {[rel['qualifier'] for rel in bout_rels]}")
        
        # For each PA bout, find overlapping location segments based on its events
        for bout in pa_bout_objects:
            bout_id = bout['id']
            if bout_id not in bout_to_events:
                print(f"Warning: PA bout {bout_id} has no associated events, skipping...")
                continue
            
            # Get all location segments that any of the bout's events occurred in
            bout_location_segments = set()
            for event in bout_to_events[bout_id]:
                location_rels = [
                    rel for rel in event.get('relationships', [])
                    if rel['qualifier'] == 'occurred_in_location'
                ]
                for rel in location_rels:
                    bout_location_segments.add(rel['id'])
            
            # Add relationships to the bout object
            if 'relationships' not in bout:
                bout['relationships'] = []
            
            # Add relationships to each location segment
            for loc_segment_id in bout_location_segments:
                # Check if relationship already exists
                if not any(
                    rel['type'] == 'object' and 
                    rel['id'] == loc_segment_id and 
                    rel['qualifier'] == 'overlaps_with_location'
                    for rel in bout['relationships']
                ):
                    bout['relationships'].append({
                        'type': 'object',
                        'id': loc_segment_id,
                        'qualifier': 'overlaps_with_location'
                    })
            
            print(f"Bout {bout_id} overlaps with {len(bout_location_segments)} location segments")
        
        return extended_data

    def relate_pa_events_to_locations(
        self,
        extended_data: Dict[str, Any],
        pa_event_type: str = "pa_bout_event"  # Default type for PA bout atomic events
    ) -> Dict[str, Any]:
        """
        Add relationships from PA bout atomic events to overlapping location segments.
        For each PA event, finds the location segment that contains its timestamp and adds
        a relationship to the PA event.
        
        Args:
            extended_data (Dict[str, Any]): The OCED data dictionary containing all objects and events
            pa_event_type (str): The type of PA bout atomic events to process
            
        Returns:
            Dict[str, Any]: Updated extended data with new relationships in PA events
        """
        # Get all location segment objects
        location_segments = [
            obj for obj in extended_data.get('objects', [])
            if obj['type'] == 'location_segment'
        ]
        
        # Get all PA bout atomic events
        pa_events = [
            event for event in extended_data.get('behaviorEvents', [])
            if event['behaviorEventType'] == 'physical_activity_bout'
        ]
        
        # For each PA event, find the containing location segment
        for pa_event in pa_events:
            # Get PA event timestamp
            try:
                event_time = datetime.fromisoformat(pa_event['time'].replace('Z', '+00:00'))
            except (ValueError, KeyError):
                print(f"Warning: PA event {pa_event['id']} has invalid time format, skipping...")
                continue
            
            # Find the location segment that contains this timestamp
            for loc_segment in location_segments:
                # Get location segment start and end times
                loc_start_time = None
                loc_end_time = None
                for attr in loc_segment['attributes']:
                    if attr['name'] == 'start_time':
                        loc_start_time = datetime.fromisoformat(attr['value'].replace('Z', '+00:00'))
                    elif attr['name'] == 'end_time':
                        loc_end_time = datetime.fromisoformat(attr['value'].replace('Z', '+00:00'))
                
                if not loc_start_time or not loc_end_time:
                    print(f"Warning: Location segment {loc_segment['id']} missing start or end time, skipping...")
                    continue
                
                # Check if PA event timestamp falls within this location segment
                if loc_start_time <= event_time <= loc_end_time:
                    # Add relationship to PA event
                    if 'relationships' not in pa_event:
                        pa_event['relationships'] = []
                    
                    # Check if relationship already exists
                    if not any(
                        rel['type'] == 'object' and 
                        rel['id'] == loc_segment['id'] and 
                        rel['qualifier'] == 'occurred_in_location'
                        for rel in pa_event['relationships']
                    ):
                        pa_event['relationships'].append({
                            'type': 'object',
                            'id': loc_segment['id'],
                            'qualifier': 'occurred_in_location'
                        })
                    break  # Found the containing segment, no need to check others
        
        return extended_data

    def add_location_attribute_to_pa_events(
        self,
        extended_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add location attributes to physical activity bout events based on their associated location segments.
        First adds the location attribute type to the behavior event type, then adds the attribute
        to each event with the location type from its associated location segment.
        
        Args:
            extended_data (Dict[str, Any]): The OCED data dictionary containing all objects and events
            
        Returns:
            Dict[str, Any]: Updated extended data with location attributes added to PA bout events
        """
        # First, add the location attribute to the behavior event type if it doesn't exist
        pa_event_type = "physical_activity_bout"
        event_type = next(
            (et for et in extended_data.get('behaviorEventTypes', [])
             if et['name'] == pa_event_type),
            None
        )
        
        if event_type is None:
            print(f"Warning: Behavior event type {pa_event_type} not found")
            return extended_data
        
        # Add location attribute to event type if it doesn't exist
        if not any(attr['name'] == 'location' for attr in event_type.get('behaviorEventTypeAttributes', [])):
            if 'behaviorEventTypeAttributes' not in event_type:
                event_type['behaviorEventTypeAttributes'] = []
            event_type['behaviorEventTypeAttributes'].append({
                "name": "location",
                "type": "string"
            })
            print(f"Added location attribute to {pa_event_type} event type")
        
        # Get all PA bout events
        pa_events = [
            event for event in extended_data.get('behaviorEvents', [])
            if event['behaviorEventType'] == pa_event_type
        ]
        
        # Get all location segments for quick lookup
        location_segments = {
            obj['id']: obj for obj in extended_data.get('objects', [])
            if obj['type'] == 'location_segment'
        }
        
        # Add location attribute to each event
        for event in pa_events:
            # Find the location segment this event occurred in
            location_rel = next(
                (rel for rel in event.get('relationships', [])
                 if rel['type'] == 'object' and 
                 rel['qualifier'] == 'occurred_in_location' and
                 rel['id'] in location_segments),
                None
            )
            
            if location_rel:
                # Get the location type from the segment
                loc_segment = location_segments[location_rel['id']]
                location_type = next(
                    (attr['value'] for attr in loc_segment['attributes']
                     if attr['name'] == 'location_type'),
                    None
                )
                
                if location_type:
                    # Add or update the location attribute
                    if 'behaviorEventTypeAttributes' not in event:
                        event['behaviorEventTypeAttributes'] = []
                    
                    # Remove existing location attribute if it exists
                    event['behaviorEventTypeAttributes'] = [
                        attr for attr in event['behaviorEventTypeAttributes']
                        if attr['name'] != 'location'
                    ]
                    
                    # Add new location attribute (without time field)
                    event['behaviorEventTypeAttributes'].append({
                        "name": "location",
                        "value": location_type
                    })
        
        # Print statistics
        events_with_location = sum(
            1 for event in pa_events
            if any(attr['name'] == 'location' for attr in event.get('behaviorEventTypeAttributes', []))
        )
        
        print(f"\nLocation attribute statistics:")
        print(f"Total PA bout events: {len(pa_events)}")
        print(f"Events with location attribute: {events_with_location}")
        print(f"Events without location attribute: {len(pa_events) - events_with_location}")
        print(f"Coverage: {(events_with_location/len(pa_events))*100:.1f}%")
        
        return extended_data