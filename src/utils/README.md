# Utility Functions

This module provides utility functions for file handling and logging in the GameBus-HealthBehaviorMining project.

## File Handlers

The `file_handlers.py` module provides functions for handling various file operations.

### JSON Operations

#### load_json
```python
def load_json(file_path: str) -> Union[List[Dict[str, Any]], Dict[str, Any]]
```
Loads data from a JSON file.

#### save_json
```python
def save_json(
    data: Union[List[Dict[str, Any]], Dict[str, Any]],
    file_path: str,
    indent: int = 4
) -> None
```
Saves data to a JSON file with proper directory creation and error handling.

### CSV Operations

#### load_csv
```python
def load_csv(file_path: str, **kwargs) -> pd.DataFrame
```
Loads data from a CSV file into a pandas DataFrame.

#### save_csv
```python
def save_csv(df: pd.DataFrame, file_path: str, **kwargs) -> None
```
Saves a pandas DataFrame to a CSV file with proper directory creation.

### File Management

#### copy_file
```python
def copy_file(
    source: str,
    destination: str,
    overwrite: bool = False
) -> None
```
Copies a file from source to destination with optional overwrite.

#### ensure_directory
```python
def ensure_directory(directory: str) -> None
```
Ensures a directory exists, creating it if necessary.

### Usage Examples

```python
from src.utils.file_handlers import (
    load_json, save_json,
    load_csv, save_csv,
    copy_file, ensure_directory
)

# JSON operations
data = load_json("data/raw/player_12345_location.json")
save_json(data, "data/processed/player_12345_location_processed.json")

# CSV operations
df = load_csv("data/raw/player_12345_activity.csv")
save_csv(df, "data/processed/player_12345_activity_processed.csv")

# File management
ensure_directory("data/processed")
copy_file("data/raw/config.json", "data/processed/config.json", overwrite=True)
```

## Logging

The `logging.py` module provides logging setup functionality for the project.

### setup_logging

```python
def setup_logging(
    log_to_file: bool = True,
    log_level: str = None
) -> logging.Logger
```

Sets up logging for the project with both console and file handlers.

#### Parameters
- `log_to_file`: Whether to log to a file (default: True)
- `log_level`: Log level (defaults to settings.LOG_LEVEL)

#### Returns
- Logger instance configured for the project

### Features
1. **Dual Output**
   - Console logging for immediate feedback
   - File logging for persistent records
   - Configurable log levels for each handler

2. **Log File Management**
   - Creates timestamped log files
   - Stores logs in `logs/` directory
   - Automatic directory creation

3. **Formatting**
   - Consistent log format across handlers
   - Includes timestamp, level, and message
   - Configurable through settings

### Usage Example

```python
from src.utils.logging import setup_logging

# Basic usage
logger = setup_logging()
logger.info("Application started")
logger.error("An error occurred", exc_info=True)

# Custom configuration
logger = setup_logging(
    log_to_file=True,
    log_level="DEBUG"
)
logger.debug("Detailed debug information")
```

### Log Format
```
2024-02-20 10:15:30,123 - gamebus_health_mining - INFO - Application started
2024-02-20 10:15:31,456 - gamebus_health_mining - ERROR - An error occurred
```

### Configuration

The logging module uses settings from `config/settings.py`:
- `LOG_LEVEL`: Default log level
- `LOG_FORMAT`: Log message format

### Dependencies
- logging
- os
- sys
- datetime

### Best Practices
1. **Log Levels**
   - Use appropriate log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
   - Include relevant context in log messages
   - Use exc_info=True for exception logging

2. **File Management**
   - Monitor log file sizes
   - Implement log rotation if needed
   - Clean up old log files periodically

3. **Performance**
   - Use appropriate log levels in production
   - Consider disabling file logging for high-frequency operations
   - Use lazy evaluation for expensive log messages 