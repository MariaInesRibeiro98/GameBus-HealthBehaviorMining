import json
from pathlib import Path
from typing import Optional, Dict, Any

def read_json  (file_path: str) -> Dict[str, Any]:
    """
    Read OCEL from a JSON file.
    
    Args:
        file_path (str): The path to the JSON file to load (can be absolute or relative path)
    
    Returns:
        Dict[str, Any]: The loaded JSON data as a dictionary
        
    Raises:
        FileNotFoundError: If the specified JSON file cannot be found
        json.JSONDecodeError: If the JSON file is not properly formatted
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"OCEL data file not found: {path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    return data 
    
