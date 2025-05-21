"""
Transformer class to convert GameBus data to OCED-mHealth schema format.
"""
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import logging
import pandas as pd
from pathlib import Path
import pandas as pd
from collections import defaultdict

logger = logging.getLogger(__name__)

class GameBusToOCEDTransformer:
    def __init__(self, player_id: str, intervention_start: datetime, intervention_end: datetime, intervention_goal: str):
        """
        Initialize the transformer.
        
        Args:
            player_id: GameBus player ID
            intervention_start: Start date of the intervention
            intervention_end: End date of the intervention
            intervention_goal: Goal or purpose of the intervention
        """
        self.player_id = player_id
        self.intervention_start = intervention_start
        self.intervention_end = intervention_end
        self.intervention_goal = intervention_goal
        self.intervention_id = str(uuid.uuid4())
        self.player_object_id = str(uuid.uuid4())
        
        # Initialize the base structure
        self.oced_data = {
            "sensorEventTypes": self._create_sensor_event_types(),
            "behaviorEventTypes": self._create_behavior_event_types(),
            "objectTypes": self._create_object_types(),
            "sensorEvents": [],
            "behaviorEvents": [],
            "objects": self._create_base_objects()
        }
    
    @staticmethod
    def _convert_timestamp(timestamp: Union[int, float, str]) -> str:
        """
        Convert epoch timestamp (milliseconds or seconds) to ISO format datetime string.
        
        Args:
            timestamp: Epoch timestamp in milliseconds or seconds
            
        Returns:
            ISO format datetime string
        """
        try:
            # Convert to float first to handle both string and numeric inputs
            ts = float(timestamp)
            
            # Check if timestamp is in milliseconds (13 digits) or seconds (10 digits)
            if ts > 1e12:  # milliseconds
                ts = ts / 1000.0
            
            # Convert to datetime and format as ISO string
            return datetime.fromtimestamp(ts).isoformat()
        except (ValueError, TypeError, OSError) as e:
            logger.error(f"Error converting timestamp {timestamp}: {e}")
            return ""
    
    @staticmethod
    def load_data_to_dataframe(file_path: str) -> pd.DataFrame:
        """
        Load GameBus data from a JSON file into a pandas DataFrame.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            DataFrame containing the data
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Error loading data from {file_path}: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def load_all_player_data(player_id: str, data_dir: str = "data") -> Dict[str, pd.DataFrame]:
        """
        Load all GameBus data for a player into DataFrames.
        
        Args:
            player_id: Player ID
            data_dir: Base directory containing the data
            
        Returns:
            Dictionary mapping data types to DataFrames
        """
        # Get the absolute path to the workspace root
        workspace_root = Path(__file__).parent.parent.parent
        data_dir = workspace_root / data_dir
        data = {}
        
        # Load raw data
        raw_files = {
            "accelerometer": f"player_{player_id}_accelerometer.json",
            "activity_type": f"player_{player_id}_activity_type.json",
            "heartrate": f"player_{player_id}_heartrate.json",
            "mood": f"player_{player_id}_mood.json",
            "notifications": f"player_{player_id}_notifications.json",
            #---- Comment if you want the categorized location data
            "location": f"player_{player_id}_location.json" 
        } 
        
        for data_type, filename in raw_files.items():
            file_path = data_dir / "raw" / filename
            if file_path.exists():
                data[data_type] = GameBusToOCEDTransformer.load_data_to_dataframe(str(file_path))
            else:
                logger.warning(f"File not found: {file_path}")
        # --- Uncomment if you want the categorized location data 
        # Load categorized location data
        #location_file = data_dir / "categorized" / f"player_{player_id}_categorized_location.json"
        #if location_file.exists():
        #    data["location"] = GameBusToOCEDTransformer.load_data_to_dataframe(str(location_file))
        #else:
        #    logger.warning(f"File not found: {location_file}")
        
        return data
    
    def _create_sensor_event_types(self) -> List[Dict[str, Any]]:
        """Create sensor event type definitions."""
        return [
            {
                "name": "accelerometer",
                "attributes": [
                    {"name": "x", "type": "number"},
                    {"name": "y", "type": "number"},
                    {"name": "z", "type": "number"},
                    {"name": "activity_id", "type": "string"}
                ]
            },
            {
                "name": "activity_type",
                "attributes": [
                    {"name": "type", "type": "string"},
                    {"name": "speed", "type": "number"},
                    {"name": "steps", "type": "number"},
                    {"name": "walks", "type": "number"},
                    {"name": "runs", "type": "number"},
                    {"name": "freq", "type": "number"},
                    {"name": "distance", "type": "number"},
                    {"name": "calories", "type": "number"}
                ]
            },
            {
                "name": "heartrate",
                "attributes": [
                    {"name": "bpm", "type": "number"},
                    {"name": "pp", "type": "number"}
                ]
            },
            {
                "name": "location",
                "attributes": [
                    {"name": "latitude", "type": "number"},
                    {"name": "longitude", "type": "number"},
                    {"name": "altitude", "type": "number"},
                    {"name": "speed", "type": "number"},
                    {"name": "error", "type": "number"},
                    #---- Uncomment if you want the categorized location data
                    #{"name": "location_type", "type": "string"}
                ]
            }
        ]
    
    def _create_behavior_event_types(self) -> List[Dict[str, Any]]:
        """Create behavior event type definitions."""
        return [
            {
                "name": "mood",
                "attributes": [
                    {"name": "valence", "type": "number"},
                    {"name": "arousal", "type": "number"},
                    {"name": "stress", "type": "number"}
                ]
            },
            {
                "name": "notification",
                "attributes": [
                    {"name": "action", "type": "string"}
                ]
            }
        ]
    
    def _create_object_types(self) -> List[Dict[str, Any]]:
        """Create object type definitions."""
        return [
            {
                "name": "player",
                "attributes": [
                    {"name": "id", "type": "string"}
                ]
            },
            {
                "name": "intervention",
                "attributes": [
                    {"name": "goal", "type": "string"},
                    {"name": "start_date", "type": "string"},
                    {"name": "end_date", "type": "string"}
                ]
            }
        ]
    
    def _create_base_objects(self) -> List[Dict[str, Any]]:
        """Create base objects (player and intervention)."""
        return [
            {
                "id": self.player_object_id,
                "type": "player",
                "attributes": [
                    {
                        "name": "id",
                        "value": self.player_id,
                        "time": self.intervention_start.isoformat()
                    }
                ],
                "relationships": [
                    {
                        "id": self.intervention_id,
                        "type": "object",
                        "qualifier": "participant"
                    }
                ]
            },
            {
                "id": self.intervention_id,
                "type": "intervention",
                "attributes": [
                    {
                        "name": "goal",
                        "value": self.intervention_goal,
                        "time": self.intervention_start.isoformat()
                    },
                    {
                        "name": "start_date",
                        "value": self.intervention_start.isoformat(),
                        "time": self.intervention_start.isoformat()
                    },
                    {
                        "name": "end_date",
                        "value": self.intervention_end.isoformat(),
                        "time": self.intervention_start.isoformat()
                    }
                ],
                "relationships": [
                    {
                        "id": self.player_object_id,
                        "type": "object",
                        "qualifier": "participant"
                    }
                ]
            }
        ]
    
    def transform_accelerometer_data(self, df: pd.DataFrame) -> None:
        """Transform accelerometer data to sensor events."""
        if df.empty:
            return
            
        for _, row in df.iterrows():
            try:
                sensor_event = {
                    "id": str(uuid.uuid4()),
                    "sensorEventType": "accelerometer",
                    "time": self._convert_timestamp(row.get("ts", "")),
                    "sensorEventTypeAttributes": [
                        {"name": "x", "value": float(row.get("x", 0))},
                        {"name": "y", "value": float(row.get("y", 0))},
                        {"name": "z", "value": float(row.get("z", 0))}
                    ],
                    "relationships": [
                        {
                            "id": self.player_object_id,
                            "type": "object",
                            "qualifier": "source"
                        }
                    ]
                }
                self.oced_data["sensorEvents"].append(sensor_event)
            except Exception as e:
                logger.error(f"Error transforming accelerometer data point: {e}")
    
    def transform_activity_data(self, df: pd.DataFrame) -> None:
        """Transform activity type data to sensor events."""
        if df.empty:
            return
            
        for _, row in df.iterrows():
            try:
                sensor_event = {
                    "id": str(uuid.uuid4()),
                    "sensorEventType": "activity_type",
                    "time": self._convert_timestamp(row.get("ts", "")),
                    "sensorEventTypeAttributes": [
                        {"name": "type", "value": str(row.get("type", "unknown"))},
                        {"name": "speed", "value": float(row.get("speed"))},
                        {"name": "steps", "value": int(row.get("steps"))},
                        {"name": "walks", "value": int(row.get("walks"))},
                        {"name": "runs", "value": int(row.get("runs"))},
                        {"name": "freq", "value": float(row.get("freq"))},
                        {"name": "distance", "value": float(row.get("distance"))},
                        {"name": "calories", "value": float(row.get("cals"))}
                    ],
                    "relationships": [
                        {
                            "id": self.player_object_id,
                            "type": "object",
                            "qualifier": "source"
                        }
                    ]
                }
                self.oced_data["sensorEvents"].append(sensor_event)
            except Exception as e:
                logger.error(f"Error transforming activity data point: {e}")
    
    def transform_heartrate_data(self, df: pd.DataFrame) -> None:
        """Transform heartrate data to sensor events."""
        if df.empty:
            return
            
        for _, row in df.iterrows():
            try:
                sensor_event = {
                    "id": str(uuid.uuid4()),
                    "sensorEventType": "heartrate",
                    "time": self._convert_timestamp(row.get("ts", "")),
                    "sensorEventTypeAttributes": [
                        {"name": "bpm", "value": float(row.get("hr"))},
                        {"name": "pp", "value": float(row.get("pp"))}
                    ],
                    "relationships": [
                        {
                            "id": self.player_object_id,
                            "type": "object",
                            "qualifier": "source"
                        }
                    ]
                }
                self.oced_data["sensorEvents"].append(sensor_event)
            except Exception as e:
                logger.error(f"Error transforming heartrate data point: {e}")
    
    def transform_location_data(self, df: pd.DataFrame) -> None:
        """Transform location data to sensor events."""
        if df.empty:
            return
            
        for _, row in df.iterrows():
            try:
                sensor_event = {
                    "id": str(uuid.uuid4()),
                    "sensorEventType": "location",
                    "time": self._convert_timestamp(row.get("TIMESTAMP", "")),
                    "sensorEventTypeAttributes": [
                        {"name": "latitude", "value": float(row.get("LATITUDE"))},
                        {"name": "longitude", "value": float(row.get("LONGITUDE"))},
                        {"name": "altitude", "value": float(row.get("ALTIDUDE"))},
                        {"name": "speed", "value": float(row.get("SPEED"))},
                        {"name": "error", "value": float(row.get("ERROR"))},
                        #---- Uncomment if you want the categorized location data
                        #{"name": "location_type", "value": str(row.get("location_type", "unknown"))}
                    ],
                    "relationships": [
                        {
                            "id": self.player_object_id,
                            "type": "object",
                            "qualifier": "source"
                        }
                    ]
                }
                self.oced_data["sensorEvents"].append(sensor_event)
            except Exception as e:
                logger.error(f"Error transforming location data point: {e}")
    
    def transform_mood_data(self, df: pd.DataFrame) -> None:
        """Transform mood data to behavior events."""
        if df.empty:
            return
            
        for _, row in df.iterrows():
            try:
                behavior_event = {
                    "id": str(uuid.uuid4()),
                    "behaviorEventType": "mood",
                    "time": self._convert_timestamp(row.get("EVENT_TIMESTAMP", "")),
                    "behaviorEventTypeAttributes": [
                        {"name": "valence", "value": int(row.get("VALENCE_STATE_VALUE"))},
                        {"name": "arousal", "value": int(row.get("AROUSAL_STATE_VALUE"))},
                        {"name": "stress", "value": int(row.get("STRESS_STATE_VALUE"))}
                    ],
                    "relationships": [
                        {
                            "id": self.player_object_id,
                            "type": "object",
                            "qualifier": "source"
                        }
                    ]
                }
                self.oced_data["behaviorEvents"].append(behavior_event)
            except Exception as e:
                logger.error(f"Error transforming mood data point: {e}")
    
    def transform_notification_data(self, df: pd.DataFrame) -> None:
        """Transform notification data to behavior events."""
        if df.empty:
            return
            
        for _, row in df.iterrows():
            try:
                behavior_event = {
                    "id": str(uuid.uuid4()),
                    "behaviorEventType": "notification",
                    "time": self._convert_timestamp(row.get("EVENT_TIMESTAMP", "")),
                    "behaviorEventTypeAttributes": [
                        {"name": "action", "value": str(row.get("ACTION", "unknown"))}
                    ],
                    "relationships": [
                        {
                            "id": self.player_object_id,
                            "type": "object",
                            "qualifier": "source"
                        }
                    ]
                }
                self.oced_data["behaviorEvents"].append(behavior_event)
            except Exception as e:
                logger.error(f"Error transforming notification data point: {e}")
    
    def save_to_file(self, output_path: str) -> None:
        """Save the transformed data to a JSON file."""
        try:
            with open(output_path, 'w') as f:
                json.dump(self.oced_data, f, indent=2)
            logger.info(f"Transformed data saved to {output_path}")
        except Exception as e:
            logger.error(f"Error saving transformed data: {e}")
            raise 

    def analyze_oced_data(self) -> None:
        """Analyze and print statistics about the transformed OCED data."""
        # Initialize counters
        stats = {
            'Total Objects': len(self.oced_data['objects']),
            'Total Sensor Events': len(self.oced_data['sensorEvents']),
            'Total Behavior Events': len(self.oced_data['behaviorEvents']),
            'Sensor Event Types': len(self.oced_data['sensorEventTypes']),
            'Behavior Event Types': len(self.oced_data['behaviorEventTypes']),
            'Object Types': len(self.oced_data['objectTypes'])
        }
        
        # Count events by type
        sensor_events_by_type = defaultdict(int)
        for event in self.oced_data['sensorEvents']:
            sensor_events_by_type[event['sensorEventType']] += 1
        
        behavior_events_by_type = defaultdict(int)
        for event in self.oced_data['behaviorEvents']:
            behavior_events_by_type[event['behaviorEventType']] += 1
        
        # Create summary tables
        sensor_events_df = pd.DataFrame({
            'Event Type': list(sensor_events_by_type.keys()),
            'Count': list(sensor_events_by_type.values())
        })
        
        behavior_events_df = pd.DataFrame({
            'Event Type': list(behavior_events_by_type.keys()),
            'Count': list(behavior_events_by_type.values())
        })
        
        # Print summary
        print("OCED Data Statistics:")
        print("-------------------")
        for key, value in stats.items():
            print(f"{key}: {value}")
        
        print("\nSensor Events by Type:")
        print(sensor_events_df.to_string(index=False))
        
        print("\nBehavior Events by Type:")
        print(behavior_events_df.to_string(index=False))
        
        # Print attribute information
        print("\nSensor Event Type Attributes:")
        for event_type in self.oced_data['sensorEventTypes']:
            print(f"\n{event_type['name'].title()}:")
            for attr in event_type['attributes']:
                print(f"  - {attr['name']} ({attr['type']})")
        
        print("\nBehavior Event Type Attributes:")
        for event_type in self.oced_data['behaviorEventTypes']:
            print(f"\n{event_type['name'].title()}:")
            for attr in event_type['attributes']:
                print(f"  - {attr['name']} ({attr['type']})")