import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from jsonschema import validate, ValidationError

def apply(data_file: str, schema_file: Optional[str] = None) -> Tuple[bool, List[str]]:
    """
    Validate if the data follows the extended-OCEL schema.
    
    Args:
        data_file (str): Path to the JSON file containing the extended-OCEL data
        schema_file (Optional[str]): Path to the JSON schema file. If None, uses the default schema
        
    Returns:
        Tuple[bool, List[str]]: A tuple containing:
            - bool: True if validation passes, False otherwise
            - List[str]: List of validation error messages if any
            
    Raises:
        FileNotFoundError: If either the data file or schema file cannot be found
        json.JSONDecodeError: If either file is not properly formatted JSON
    """
    # Use default schema if none provided
    if schema_file is None:
        schema_file = str(Path(__file__).parent.parent / "schema" / "extended-OCEL.json")
    
    # Load schema
    schema_path = Path(schema_file)
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = json.load(f)
    
    # Load data
    data_path = Path(data_file)
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    # Validate data against schema
    errors = []
    try:
        validate(instance=data, schema=schema)
        return True, []
    except ValidationError as e:
        errors.append(str(e))
        return False, errors
    except Exception as e:
        errors.append(f"Unexpected error during validation: {str(e)}")
        return False, errors
