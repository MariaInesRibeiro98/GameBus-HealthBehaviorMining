"""
Path configurations for the GameBus-HealthBehaviorMining project.
"""
import os
import sys

# Get the project root directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Data directories
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PREPROCESSED_DATA_DIR = os.path.join(DATA_DIR, "preprocessed")
FEATURES_DATA_DIR = os.path.join(DATA_DIR, "features")
ACTIVITIES_DATA_DIR = os.path.join(DATA_DIR, "activities")
OCEL_DATA_DIR = os.path.join(DATA_DIR, "ocel")

# Schema directory
SCHEMA_DIR = os.path.join(PROJECT_ROOT, "schema")

# Try to import from secret folder for backward compatibility
try:
    from secret.users import GB_users_path
    USERS_FILE_PATH = GB_users_path
except ImportError:
    # If not available, use default location
    USERS_FILE_PATH = os.path.join(PROJECT_ROOT, "config", "users.csv")

# Try to import output path from secret
try:
    from secret.output import output_path
    OUTPUT_PATH = output_path
except ImportError:
    # If not available, use data/raw as default
    OUTPUT_PATH = RAW_DATA_DIR

# Ensure directories exist
for directory in [DATA_DIR, RAW_DATA_DIR, PREPROCESSED_DATA_DIR, 
                 FEATURES_DATA_DIR, ACTIVITIES_DATA_DIR, OCEL_DATA_DIR]:
    os.makedirs(directory, exist_ok=True) 