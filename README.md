# GameBus-HealthBehaviorMining

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Project Status: Active Development](https://img.shields.io/badge/Project%20Status-Active%20Development-green)](https://github.com/yourusername/GameBus-HealthBehaviorMining)

A comprehensive framework for extracting, processing, and analyzing health behavior data from the GameBus platform using process mining techniques. This project aims to transform raw health and activity data into meaningful insights through object-centric event logs (OCEL), enabling detailed analysis of health behaviors and patterns.

## 🎯 Project Goals

- Extract and process health behavior data from GameBus platform
- Transform raw sensor data into structured event logs
- Enable process mining analysis of health behaviors
- Support research in health behavior patterns and interventions
- Provide a foundation for personalized health insights

## 📋 Features

- **Data Extraction**: Comprehensive extraction of multiple data types from GameBus API
  - GPS location data with categorization
  - Activity type data
  - Heart rate monitoring
  - Accelerometer readings
  - Mood logging
  - Notification data

- **Location Categorization**: Intelligent location enrichment using Google Places API
  - Automatic categorization of GPS points
  - Support for modular processing
  - Flexible output formats (CSV/JSON)

- **Process Mining Ready**: 
  - OCEL 2.0 compliant output
  - Custom mHealth extensions
  - Support for complex event analysis

## 🏗️ Project Structure

```
GameBus-HealthBehaviorMining/
├── config/                         # Configuration files
│   ├── credentials.py              # GameBus and Google API credentials
│   ├── paths.py                    # Path configurations
│   └── settings.py                 # General settings
├── src/                            # Source code
│   ├── extraction/                 # Data extraction from GameBus
│   │   ├── gamebus_client.py       # GameBus API client
│   │   ├── data_collectors.py      # Data collectors for different data types
│   │   └── README.md              # Detailed extraction documentation
│   ├── categorization/             # Location data categorization
│   │   ├── location_categorizer.py # Categorize locations using Google Places API
│   │   └── README.md              # Categorization service documentation
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
│   ├── categorized/                # Categorized/enriched data (location types)
│   ├── preprocessed/               # Cleaned and normalized data (future)
│   ├── features/                   # Features for activity recognition (future)
│   ├── activities/                 # Recognized activities (future)
│   └── ocel/                       # Generated OCEL data (future)
└── pipeline.py                     # Main pipeline runner
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- GameBus API credentials
- Google Places API key (for location categorization)
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/GameBus-HealthBehaviorMining.git
cd GameBus-HealthBehaviorMining
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
# On Windows
.\venv\Scripts\activate
# On Unix or MacOS
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure the project:
   - Create a `secret` folder with your credentials (see Configuration section)
   - Or update the credentials directly in the config files

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

## 💻 Usage

### Using the Pipeline

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

After extraction, run the categorization service to enrich location data:

```bash
python src/categorization/location_categorizer.py --player-id 107631
```

Or, use the modular approach in your own scripts:

```python
from src.categorization.location_categorizer import LocationCategorizer

categorizer = LocationCategorizer()
df = categorizer.load_player_location_df(player_id)
df_categorized = categorizer.categorize_location_df(df, player_id)
categorizer.save_categorized_location_json(df_categorized, player_id)
```

For more detailed information about the extraction and categorization functionality, see `src/extraction/README.md` and `src/categorization/README.md`.

### Using Notebooks

Open and run the Jupyter notebooks in the `notebooks/` directory:

```
jupyter notebook notebooks/01_data_extraction.ipynb
```

## 📊 Data Types

The framework extracts and processes the following types of data from GameBus:

1. **Location Data**
   - GPS coordinates (latitude, longitude)
   - Altitude
   - Speed
   - Error margin
   - Timestamps
   - **Categorized location data**: Adds a `location_type` field (e.g., university, park, etc.)
   - **Missing values in the output JSON are represented as the string `'NaN'`.**

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

## 🔄 OCEL Format

The project implements the Object-Centric Event Log (OCEL) 2.0 standard with mHealth-specific extensions. This format enables:

- **Object-Centric Analysis**: Track multiple objects (e.g., users, locations, activities) simultaneously
- **Complex Event Relationships**: Capture rich relationships between events and objects
- **Temporal Analysis**: Support for detailed temporal analysis of health behaviors
- **Sensor Data Integration**: Seamless integration of various sensor readings
- **Process Mining Compatibility**: Ready for use with process mining tools

The schema is defined in `schema/mHealth-OCEL2.0.json`.

## 🤝 Contributing

We welcome contributions to improve this framework! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

Please read our [Contributing Guidelines](CONTRIBUTING.md) for more details.

## 📝 Future Work

- [ ] Implement preprocessing pipeline
- [ ] Add activity recognition module


## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- GameBus platform for providing the API
- OCED standard for process mining
- Google Places API for location categorization
- All contributors and users of this framework

## 📧 Contact

For questions and support, please open an issue in the GitHub repository or contact the maintainers.
