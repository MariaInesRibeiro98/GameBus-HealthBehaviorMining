from typing import Dict, List, Union, Any
import json

class ExtendedOCELToStandardOCELCoverter:
    def __init__(self, extended_ocel_data: Dict[str, Any]):
        """
        Initialize the converter with extended OCEL data.
        
        Args:
            ocel_data (Dict[str, Any]): The extended OCEL data to convert
        """
        self.extended_ocel_data = extended_ocel_data
        self.ocel_data = {
            "eventTypes": [],
            "objectTypes": [],
            "events": [],
            "objects": []
        }

    def _convert_event_types(self) -> None:
        """Convert extended OCEL behavior event types to OCEL event types."""
        for event_type in self.extended_ocel_data["behaviorEventTypes"]:
            self.ocel_data["eventTypes"].append({
                "name": event_type["name"],
                "attributes": event_type["attributes"]
            })

    def _convert_object_types(self) -> None:
        """Convert extended OCEL object types to OCEL object types."""
        for obj_type in self.extended_ocel_data["objectTypes"]:
            self.ocel_data["objectTypes"].append({
                "name": obj_type["name"],
                "attributes": obj_type["attributes"]
            })

    def _convert_events(self) -> None:
        """Convert extended OCEL behavior events to OCEL events."""
        for event in self.extended_ocel_data["behaviorEvents"]:
            # Convert relationships to OCEL format
            relationships = []
            if "relationships" in event:
                for rel in event["relationships"]:
                    if rel["type"] == "object":  # Only keep object relationships
                        relationships.append({
                            "objectId": rel["id"],
                            "qualifier": rel["qualifier"]
                        })

            # Convert attributes
            attributes = []
            if "behaviorEventTypeAttributes" in event:
                for attr in event["behaviorEventTypeAttributes"]:
                    attributes.append({
                        "name": attr["name"],
                        "value": str(attr["value"])  # Convert to string to comply with OCEL
                    })

            self.ocel_data["events"].append({
                "id": event["id"],
                "type": event["behaviorEventType"],
                "time": event["time"],
                "attributes": attributes,
                "relationships": relationships
            })

    def _convert_objects(self) -> None:
        """Convert extended OCEL objects to OCEL objects."""
        for obj in self.extended_ocel_data["objects"]:
            # Convert relationships to OCEL format
            relationships = []
            if "relationships" in obj:
                for rel in obj["relationships"]:
                    if rel["type"] == "object":
                        relationships.append({
                            "objectId": rel["id"],
                            "qualifier": rel["qualifier"]
                        })

            # Convert attributes
            attributes = []
            if "attributes" in obj:
                for attr in obj["attributes"]:
                    attributes.append({
                        "name": attr["name"],
                        "value": str(attr["value"]),  # Convert to string to comply with OCEL
                        "time": attr["time"]
                    })

            self.ocel_data["objects"].append({
                "id": obj["id"],
                "type": obj["type"],
                "relationships": relationships,
                "attributes": attributes
            })

    def convert(self) -> Dict[str, Any]:
        """
        Convert extended OCEL data to OCEL format.
        
        Returns:
            Dict[str, Any]: The converted data in OCEL format
        """
        self._convert_event_types()
        self._convert_object_types()
        self._convert_events()
        self._convert_objects()
        return self.ocel_data

    @classmethod
    def from_file(cls, file_path: str) -> 'ExtendedOCELToStandardOCELCoverter':
        """
        Create a converter from an extended OCEL JSON file.
        
        Args:
            file_path (str): Path to the extended OCEL JSON file
            
        Returns:
            ExtendedOCELToStandardOCELCoverter: A converter instance initialized with the file data
        """
        with open(file_path, 'r') as f:
            ocel_data = json.load(f)
        return cls(ocel_data)

    def save_to_file(self, file_path: str) -> None:
        """
        Save the converted OCEL data to a JSON file.
        
        Args:
            file_path (str): Path where the OCEL JSON file should be saved
        """
        with open(file_path, 'w') as f:
            json.dump(self.ocel_data, f, indent=4)
