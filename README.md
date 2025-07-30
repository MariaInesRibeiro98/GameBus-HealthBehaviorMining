# GameBus-HealthBehaviorMining

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Project Status: Active Development](https://img.shields.io/badge/Project%20Status-Active%20Development-green)](https://github.com/yourusername/GameBus-HealthBehaviorMining)

A comprehensive framework for extracting, processing, and analyzing health behavior data from the GameBus platform using Object-Centric Process Mining (OCPM) techniques. This project implements the Object-Centric Event Log (OCEL) standard with sensor data extensions to transform raw health and activity data into meaningful insights through object-centric event logs, enabling detailed analysis of health behaviors and patterns.

## 🎯 Project Goals

- Extract and process multi-modal health behavior data from the GameBus platform
- Transform raw sensor data into the extended Object-Centric Event Data (OCEL) format
- Enable advanced process mining analysis of health behaviors using OCPM techniques
- Support research in health behavior patterns, interventions, and personalized health insights
- Provide a foundation for data-driven and process-centric health behavior analysis and intervention design
- Facilitate the study of complex health behavior processes through object-centric modeling


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
│   ├── oced/                       # Object-Centric Event Data processing
│   │   ├── oced_data_query.py      # OCED data querying and management
│   │   ├── time_objects.py         # Temporal object creation and management
│   │   ├── location_objects.py     # Location-based object processing
│   │   ├── stress_objects.py       # Stress and mood object management
│   │   ├── notification_events.py  # Notification event processing
│   │   ├── bout_events.py          # Physical activity bout event creation
│   │   ├── physical_activity_classifier.py # Activity classification algorithms
│   │   ├── bout_detection.py       # Bout detection algorithms
│   │   ├── feature_extraction.py   # Feature extraction for activity recognition
│   │   ├── data_resampling.py      # Sensor data resampling utilities
│   │   ├── acc_calibration.py      # Accelerometer calibration
│   │   ├── smoothing.py            # Data smoothing algorithms
│   │   └── visualization.py        # Data visualization utilities
│   ├── extended_ocel/              # Extended OCEL processing
│   │   ├── covert_to_ocel.py       # OCED to OCEL conversion
│   │   ├── read_json.py            # JSON data reading utilities
│   │   ├── select_sample.py        # Sample selection for analysis
│   │   └── validation.py           # Data validation utilities
│   ├── transformation/             # Data transformation utilities
│   │   ├── gamebus_to_oced_transformer.py # GameBus to OCED transformation
│   │   └── README.md              # Transformation documentation
│   ├── preprocessing/              # Data preprocessing utilities
│   │   ├── resampling.py           # Data resampling algorithms
│   │   └── README.md              # Preprocessing documentation
├── notebooks/                      # Jupyter notebooks
│   ├── 01.1_data_extraction__from_source.ipynb    # Data extraction demonstration
│   ├── 01.2_data_extraction__to_oced.ipynb        # OCED transformation
│   ├── 01.3_data_extraction__create_time_objects.ipynb # Temporal object creation
│   ├── 01.4_data_extraction__create_notification_objects.ipynb # Notification processing
│   ├── 01.5_data_extraction__create_self-report_objects.ipynb # Self-report processing
│   ├── 01.6_data_extraction__create_location_objects_events_attributes.ipynb # Location processing
│   ├── 01.7_data_extraction__link_notification_self-report_events_objects.ipynb # Event linking
│   ├── 01.8_data_extraction__link_bout_events_self-report_objects.ipynb # Bout linking
│   ├── 01.9_data_extraction__link_bout_events_to_report_objects.ipynb # Report linking
│   ├── 02_activity_recognition.ipynb              # Activity recognition analysis
│   ├── 03.0_querying__sample_selection.ipynb      # Sample selection
│   ├── 03.1_querying__backward_compatibility.ipynb # Backward compatibility
│   ├── 03.2_querying__rename_event_types.ipynb    # Event type management
│   ├── 03.3_querying__filter_per_object_event.ipynb # Object filtering
│   └── 04_discovery_.ipynb                        # Process discovery
├── schema/                         # Extended OCEL Schema & Validation
│   ├── extended-OCEL-schema.json   # Extended OCEL JSON schema for sensor data
│   ├── extended_OCEL-minimal_sample.json # Sample data file demonstrating the format
│   ├── OCEL-2.0-Standard.json      # Standard OCEL 2.0 schema for reference
│   └── drafts/                     # Schema drafts and examples
├── examples/                       # Example data and scripts
│   ├── GB-users.csv               # Example user data
│   ├── profile_example.py         # Profile example
│   └── relate_location_pa_bouts.py # Location-PA bout analysis
├── requirements.txt                # Python dependencies
├── README.md                       # Project documentation
└── .gitignore                      # Git ignore rules
```

## 📚 Notebook Workflow & Extended OCEL Schema

### 🔬 Extended OCEL Format

The project introduces an **extended Object-Centric Event Log (OCEL) format** specifically designed for sensor data and health behavior analysis:

- **`schema/extended-OCEL-schema.json`**: Complete JSON schema defining the extended OCEL structure
- **`schema/extended_OCEL-minimal_sample.json`**: Sample data file demonstrating the format
- **`src/extended_ocel/validation.py`**: Validation methods to ensure data compliance

The extended OCEL format supports:
- **Sensor Events**: High-frequency sensor data (accelerometer, heart rate, location)
- **Behavior Events**: User interactions and self-reports
- **Object Relationships**: Complex relationships between events and objects
- **Temporal Context**: Time-based object creation and linking

### 📖 Notebook Summary

The notebooks follow a comprehensive workflow for health behavior analysis:

#### **Phase 1: Data Extraction & Transformation**
- **`01.1_data_extraction__from_source.ipynb`**: Extract data from GameBus-Experiencer app using Samsung Active 2 smartwatch
- **`01.2_data_extraction__to_oced.ipynb`**: Transform GameBus data into extended OCEL format, handling sensor and behavioral data
- **`01.3_data_extraction__create_time_objects.ipynb`**: Create temporal objects (days, weeks) and relate them to events
- **`01.4_data_extraction__create_notification_objects.ipynb`**: Create notification objects from notification events
- **`01.5_data_extraction__create_self-report_objects.ipynb`**: Create stress self-report objects from mood events
- **`01.6_data_extraction__create_location_objects_events_attributes.ipynb`**: Process location data and create location objects
- **`01.7_data_extraction__link_notification_self-report_events_objects.ipynb`**: Link self-report objects to notification events
- **`01.8_data_extraction__link_bout_events_self-report_objects.ipynb`**: Link physical activity bouts to self-report objects
- **`01.9_data_extraction__link_bout_events_to_report_objects.ipynb`**: Link bout events to stress self-report objects within time windows

#### **Phase 2: Activity Recognition**
- **`02_activity_recognition.ipynb`**: Recognize physical activity bouts using accelerometer and heart rate data with decision tree classification

#### **Phase 3: Data Querying & Filtering**
- **`03.0_querying__sample_selection.ipynb`**: Select representative samples from extended OCEL data
- **`03.1_querying__backward_compatibility.ipynb`**: Convert extended OCEL to standard format for PM4Py compatibility
- **`03.2_querying__rename_event_types.ipynb`**: Handle event type naming for specific analysis profiles
- **`03.3_querying__filter_per_object_event.ipynb`**: Filter OCEL data by object types and events

#### **Phase 4: Process Discovery**
- **`04_discovery_.ipynb`**: Perform process mining analysis on health behavior patterns, focusing on stress-behavior correlations and notification engagement

### 🔍 Validation & Quality Assurance

The framework includes comprehensive validation methods in `src/extended_ocel/validation.py`:
- **Schema Validation**: Ensures data follows the extended OCEL schema
- **Data Integrity Checks**: Validates relationships and object references
- **Format Compliance**: Verifies JSON structure and required fields

## 🚀 Getting Started

<div align="center">

# ⚠️ IMPORTANT: DATA SETUP REQUIRED ⚠️

**The `data/` folder is hidden from this repository for privacy reasons.**

This folder contains sensitive health data extracted from the GameBus platform and is **essential for running the notebooks**.

### 🔧 What You Need to Do:

1. **Create the data directory structure:**
   ```bash
   mkdir -p data/raw data/categorized data/ocel
   ```

2. **Extract your own data** using the provided notebooks and scripts

3. **Follow the data extraction workflow** in the notebooks starting with `01.1_data_extraction__from_source.ipynb`

**Without this data, the notebooks will not run properly!**

</div>

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

2. (Optional) Create and activate a virtual environment:
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

> **💡 Note**: Virtual environments are optional but recommended if you want to avoid potential package conflicts with other Python projects. For research and development, you can also install dependencies globally.

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



## 🤝 Contributing

We welcome contributions to improve this framework! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

Please read our [Contributing Guidelines](CONTRIBUTING.md) for more details.

## 📝 Future Work

- [ ] Enhanced activity recognition algorithms
- [ ] Advanced process discovery techniques
- [ ] Real-time data processing capabilities
- [ ] Integration with additional health platforms
- [ ] Advanced visualization and dashboard features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- GameBus platform for providing the API and data access
- OCEL/OCED standards for process mining
- Google Places API for location categorization
- PM4Py community for process mining tools
- All contributors and users of this framework

## 📧 Contact

For questions and support, please open an issue in the GitHub repository or contact the maintainers.
