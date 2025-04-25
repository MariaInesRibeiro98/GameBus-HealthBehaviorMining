"""
File handling utilities for the GameBus-HealthBehaviorMining project.
"""
import os
import json
import pandas as pd
import shutil
import logging
from typing import Dict, List, Any, Union, Optional

# Set up logging
logger = logging.getLogger(__name__)

def load_json(file_path: str) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Load data from a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Loaded JSON data
    """
    try:
        with open(file_path, 'r') as json_file:
            data = json.load(json_file)
        return data
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Failed to load JSON file {file_path}: {e}")
        raise

def save_json(data: Union[List[Dict[str, Any]], Dict[str, Any]], file_path: str, indent: int = 4) -> None:
    """
    Save data to a JSON file.
    
    Args:
        data: Data to save
        file_path: Path to save the file
        indent: Indentation for the JSON file
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w') as json_file:
            json.dump(data, json_file, indent=indent)
        
        logger.info(f"Data saved to {file_path}")
    except (TypeError, OSError) as e:
        logger.error(f"Failed to save JSON file {file_path}: {e}")
        raise

def load_csv(file_path: str, **kwargs) -> pd.DataFrame:
    """
    Load data from a CSV file.
    
    Args:
        file_path: Path to the CSV file
        **kwargs: Additional arguments for pd.read_csv
        
    Returns:
        Pandas DataFrame
    """
    try:
        df = pd.read_csv(file_path, **kwargs)
        return df
    except (pd.errors.EmptyDataError, FileNotFoundError) as e:
        logger.error(f"Failed to load CSV file {file_path}: {e}")
        raise

def save_csv(df: pd.DataFrame, file_path: str, **kwargs) -> None:
    """
    Save data to a CSV file.
    
    Args:
        df: Pandas DataFrame to save
        file_path: Path to save the file
        **kwargs: Additional arguments for df.to_csv
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        df.to_csv(file_path, **kwargs)
        logger.info(f"Data saved to {file_path}")
    except OSError as e:
        logger.error(f"Failed to save CSV file {file_path}: {e}")
        raise

def copy_file(source: str, destination: str, overwrite: bool = False) -> None:
    """
    Copy a file from source to destination.
    
    Args:
        source: Source file path
        destination: Destination file path
        overwrite: Whether to overwrite if file exists
    """
    try:
        if os.path.exists(destination) and not overwrite:
            logger.warning(f"File {destination} already exists. Set overwrite=True to overwrite.")
            return
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        
        shutil.copy2(source, destination)
        logger.info(f"File copied from {source} to {destination}")
    except (FileNotFoundError, OSError) as e:
        logger.error(f"Failed to copy file from {source} to {destination}: {e}")
        raise

def ensure_directory(directory: str) -> None:
    """
    Ensure a directory exists.
    
    Args:
        directory: Directory path
    """
    try:
        os.makedirs(directory, exist_ok=True)
        logger.debug(f"Ensured directory exists: {directory}")
    except OSError as e:
        logger.error(f"Failed to create directory {directory}: {e}")
        raise 