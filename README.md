# GameBus-HealthBehaviorMining

A framework for extracting, processing, and analyzing health behavior data from the GameBus platform using process mining techniques.

## Project Structure

```
GameBus-HealthBehaviorMining/
├── config/                         # Configuration files
│   ├── credentials.py              # GameBus API credentials
│   ├── paths.py                    # Path configurations
│   └── settings.py                 # General settings
├── src/                            # Source code
│   ├── extraction/                 # Data extraction from GameBus
│   │   ├── gamebus_client.py       # GameBus API client
│   │   ├── data_collectors.py      # Data collectors for different data types
│   │   └── README.md              # Detailed extraction documentation
│   ├── preprocessing/              # Data preprocessing and cleaning (TBD)
│   ├── activity_recognition/       # Human activity recognition (TBD)
│   ├── ocel_generation/            # OCEL format generation (TBD)
│   └── utils/                      # Utility functions
│       ├── logging.py              # Logging utilities
│       └── file_handlers.py        # File handling utilities
├── notebooks/                      # Jupyter notebooks
│   └── 01_data_extraction.ipynb    # Data extraction demonstration
├── schema/                         # OCEL JSON schemas
│   ├── OCEL2.0.json                # OCEL 2.0 schema
│   └── mHealth-OCEL2.0.json        # mHealth extension of OCEL 2.0 schema
├── data/                           # Data directory
│   ├── raw/                        # Raw extracted data
│   ├── preprocessed/               # Cleaned and normalized data (future)
│   ├── features/                   # Features for activity recognition (future)
│   ├── activities/                 # Recognized activities (future)
│   └── ocel/                       # Generated OCEL data (future)
└── pipeline.py                     # Main pipeline runner
```

## Framework Workflow

1. **Data Extraction**: Extract raw data from the GameBus API, including:
   - GPS location data (latitude, longitude, altitude, speed)
   - Activity type data (walking, running, etc.)
   - Heart rate monitoring
   - Accelerometer readings
   - Mood logging
   - Notification data
   
   The extraction supports date-based filtering to retrieve data within specific time ranges.

2. **Preprocessing** (To be implemented): Clean and normalize the raw data, handle missing values, synchronize timestamps, etc.

3. **Activity Recognition** (To be implemented): Recognize human activities from the sensor data using machine learning techniques.

4. **OCEL Generation** (To be implemented): Transform the preprocessed data and recognized activities into the Object-Centric Event Log (OCEL) format for process mining.

## Getting Started

### Prerequisites

- Python 3.8+
- GameBus API credentials

### Installation

1. Clone the repository
2. Install dependencies:
```
pip install -r requirements.txt
```

3. Configure the project:
   - Create a `secret` folder with your GameBus credentials (see below)
   - Or update the credentials directly in the config files (these will be ignored by Git)

### Configuration

This project can be configured in two ways:

1. **Using the secret folder (for backward compatibility):**
   Create a `secret` folder with:
   - `auth.py`: Contains `authcode` variable for GameBus API authentication
   - `users.py`: Contains `GB_users_path` variable pointing to your users CSV file
   - `output.py`: Contains `output_path` variable for data output location

2. **Using the config files directly:**
   - Update credentials in `config/credentials.py` 
   - Add your users CSV file to `config/users.csv`
   - Output will go to the `data/raw` directory by default

**Important Note about Users CSV File Format:**
- The users CSV file must have the header row with exact column names: `Username;Password`
- Note that `Username` starts with a capital letter
- The delimiter must be a semicolon (`;`)
- Example:
  ```
  Username;Password
  user@example.com;password123
  ```

For detailed instructions, see `config/README.md`.

### Usage

#### Using the Pipeline

The pipeline supports various options for data extraction:

```bash
# Extract all data types
python pipeline.py --extract-only

# Extract specific data types
python pipeline.py --extract-only --data-types location mood activity heartrate

# Extract data for a specific user
python pipeline.py --extract-only --user-id 123

# Extract data within a date range
python pipeline.py --extract-only --start-date 2024-01-01 --end-date 2024-02-01

# Combine options
python pipeline.py --extract-only --data-types location mood --start-date 2024-01-01 --user-id 123
```

For more detailed information about the extraction functionality, see `src/extraction/README.md`.

#### Using Notebooks

Open and run the Jupyter notebooks in the `notebooks/` directory:

```
jupyter notebook notebooks/01_data_extraction.ipynb
```

## Data Types

The framework extracts the following types of data from GameBus:

1. **Location Data**
   - GPS coordinates (latitude, longitude)
   - Altitude
   - Speed
   - Error margin
   - Timestamps

2. **Mood Data**
   - Valence (pleasure-displeasure)
   - Arousal (activation-deactivation)
   - Stress state
   - Event timestamps

3. **Activity Type Data**
   - Activity classification (walking, running, etc.)
   - Speed
   - Steps count
   - Distance
   - Calories burned

4. **Heart Rate Data**
   - Heart rate values
   - Timestamps

5. **Accelerometer Data**
   - X, Y, Z axis measurements
   - Timestamps

6. **Notification Data**
   - Notification actions
   - Timestamps

## OCEL Format

The project uses the Object-Centric Event Log (OCEL) format for process mining, with extensions specific to mHealth data. The schema includes:

- Event types (activities)
- Object types (entities)
- Sensor readings 
- Relationships between objects and events

## License

This project is licensed under the MIT License.

## Acknowledgments

- GameBus platform for providing the API
- OCEL standard for process mining
