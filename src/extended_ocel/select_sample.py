import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from collections import defaultdict

def select_sample(input_file: str, output_file: str, schema_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Select the first occurrence of each type from a large extended-OCEL JSON file.
    
    This function creates a minimal sample by selecting:
    - One item from each sensorEventType
    - One item from each behaviorEventType  
    - One item from each objectType
    - One sensorEvent from each sensorEventType
    - One behaviorEvent from each behaviorEventType
    - One object from each objectType
    
    Args:
        input_file (str): Path to the input JSON file containing the full extended-OCEL data
        output_file (str): Path where the minimal sample will be saved
        schema_file (Optional[str]): Path to the JSON schema file for validation
        
    Returns:
        Dict[str, Any]: The minimal sample data
        
    Raises:
        FileNotFoundError: If the input file cannot be found
        json.JSONDecodeError: If the input file is not properly formatted JSON
        ValueError: If the input data doesn't follow the expected structure
    """
    # Load input data
    input_path = Path(input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    # Validate required structure
    required_keys = ["sensorEventTypes", "behaviorEventTypes", "objectTypes", 
                    "sensorEvents", "behaviorEvents", "objects"]
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Required key '{key}' not found in input data")
        if not isinstance(data[key], list):
            raise ValueError(f"Key '{key}' must be an array")
    
    # Initialize sample structure
    sample = {
        "sensorEventTypes": [],
        "behaviorEventTypes": [],
        "objectTypes": [],
        "sensorEvents": [],
        "behaviorEvents": [],
        "objects": []
    }
    
    # Track which types we've already selected to avoid duplicates
    selected_sensor_event_types = set()
    selected_behavior_event_types = set()
    selected_object_types = set()
    
    # Select first occurrence of each sensorEventType
    for item in data["sensorEventTypes"]:
        if "name" in item and item["name"] not in selected_sensor_event_types:
            sample["sensorEventTypes"].append(item)
            selected_sensor_event_types.add(item["name"])
    
    # Select first occurrence of each behaviorEventType
    for item in data["behaviorEventTypes"]:
        if "name" in item and item["name"] not in selected_behavior_event_types:
            sample["behaviorEventTypes"].append(item)
            selected_behavior_event_types.add(item["name"])
    
    # Select first occurrence of each objectType
    for item in data["objectTypes"]:
        if "name" in item and item["name"] not in selected_object_types:
            sample["objectTypes"].append(item)
            selected_object_types.add(item["name"])
    
    # Select first occurrence of each sensorEvent type
    selected_sensor_events = set()
    for item in data["sensorEvents"]:
        if "sensorEventType" in item and item["sensorEventType"] not in selected_sensor_events:
            sample["sensorEvents"].append(item)
            selected_sensor_events.add(item["sensorEventType"])
    
    # Select first occurrence of each behaviorEvent type
    selected_behavior_events = set()
    for item in data["behaviorEvents"]:
        if "behaviorEventType" in item and item["behaviorEventType"] not in selected_behavior_events:
            sample["behaviorEvents"].append(item)
            selected_behavior_events.add(item["behaviorEventType"])
    
    # Select first occurrence of each object type
    selected_objects = set()
    for item in data["objects"]:
        if "type" in item and item["type"] not in selected_objects:
            sample["objects"].append(item)
            selected_objects.add(item["type"])
    
    # Save the sample
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(sample, f, indent=2)
    
    # Optional: Validate against schema if provided
    if schema_file:
        try:
            from .validation import apply
            is_valid, errors = apply(str(output_path), schema_file)
            if not is_valid:
                print(f"Warning: Generated sample has validation errors: {errors}")
        except ImportError:
            print("Warning: Could not import validation module")
    
    return sample

def get_sample_statistics(sample_data: Dict[str, Any]) -> Dict[str, int]:
    """
    Get statistics about the generated sample.
    
    Args:
        sample_data (Dict[str, Any]): The sample data
        
    Returns:
        Dict[str, int]: Statistics showing the count of items in each array
    """
    return {
        "sensorEventTypes": len(sample_data.get("sensorEventTypes", [])),
        "behaviorEventTypes": len(sample_data.get("behaviorEventTypes", [])),
        "objectTypes": len(sample_data.get("objectTypes", [])),
        "sensorEvents": len(sample_data.get("sensorEvents", [])),
        "behaviorEvents": len(sample_data.get("behaviorEvents", [])),
        "objects": len(sample_data.get("objects", []))
    }

def compare_sizes(original_file: str, sample_file: str) -> Dict[str, Any]:
    """
    Compare the sizes of original and sample files.
    
    Args:
        original_file (str): Path to the original file
        sample_file (str): Path to the sample file
        
    Returns:
        Dict[str, Any]: Comparison statistics
    """
    original_path = Path(original_file)
    sample_path = Path(sample_file)
    
    if not original_path.exists():
        raise FileNotFoundError(f"Original file not found: {original_path}")
    if not sample_path.exists():
        raise FileNotFoundError(f"Sample file not found: {sample_path}")
    
    original_size = original_path.stat().st_size
    sample_size = sample_path.stat().st_size
    
    return {
        "original_size_bytes": original_size,
        "sample_size_bytes": sample_size,
        "reduction_percentage": round((1 - sample_size / original_size) * 100, 2),
        "original_size_mb": round(original_size / (1024 * 1024), 2),
        "sample_size_mb": round(sample_size / (1024 * 1024), 2)
    } 