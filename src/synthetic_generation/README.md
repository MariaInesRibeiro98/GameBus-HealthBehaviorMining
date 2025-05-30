# Synthetic Sensor Data Generation

This module provides tools for generating synthetic accelerometer and heart rate data that mimics real-world sensor data patterns from the GameBus platform. The generator creates correlated sensor data with realistic sampling frequencies, gaps, invalid values, and activity-based patterns, following the OCED (Object-Centric Event Data) format.

## Overview

The synthetic data generator is designed to create realistic test data that matches the characteristics of real GameBus sensor data, including:
- Irregular sampling frequencies
- Activity-dependent gaps and invalid values
- Activity-based patterns
- Correlated sensor readings
- Proper data quality flags

## Features

- Generates correlated accelerometer and heart rate data
- Models different activity states (sedentary, light, moderate-vigorous activity)
- Includes realistic sampling frequencies (50 Hz for accelerometer, 12.5 Hz for heart rate)
- Adds realistic gaps with activity-dependent probabilities
- Supports custom time ranges for data generation
- Maintains proper gravity component in accelerometer data
- Generates realistic pulse pressure values for heart rate
- Follows OCED format for compatibility with process mining tools

## Installation

The module is part of the GameBus-HealthBehaviorMining project. Required dependencies:
```bash
pip install numpy pandas scipy
```

## Usage

### Basic Usage

```python
from datetime import datetime
from src.synthetic_generation.synthetic_data_generator import SyntheticSensorDataGenerator

# Create generator with default parameters (24 hours of data from current time)
generator = SyntheticSensorDataGenerator()

# Or specify custom time range
start_time = datetime(2024, 1, 1, 8, 0)  # 8 AM
end_time = datetime(2024, 1, 2, 8, 0)    # Next day 8 AM
generator = SyntheticSensorDataGenerator(
    start_timestamp=start_time,
    end_timestamp=end_time
)

# Generate data
acc_df, hr_df = generator.generate_sensor_data()
```

### Custom Parameters

```python
generator = SyntheticSensorDataGenerator(
    start_timestamp=datetime(2024, 1, 1, 8, 0),
    end_timestamp=datetime(2024, 1, 2, 8, 0),
    movement_threshold=0.294,  # in m/s² (0.03g)
    acc_fs=50.0,             # Hz
    hr_fs=12.5,              # Hz
    invalid_value=-9999
)
```

## Data Characteristics

### Accelerometer Data
- Sampling frequency: 50 Hz
- Components: x, y, z (in m/s²)
- Includes gravity component (9.81 m/s² on z-axis)
- Activity-based magnitude ranges:
  - Sedentary: 9.61 ± 0.20 m/s² (~0.98g ± 0.02g)
  - Light activity: 11.77 ± 0.98 m/s² (~1.2g ± 0.1g)
  - Moderate-Vigorous activity: 17.66 ± 2.94 m/s² (~1.8g ± 0.3g)

### Heart Rate Data
- Sampling frequency: 12.5 Hz
- Components: bpm (beats per minute), pp (pulse pressure)
- Activity-based ranges:
  - Sedentary: 60 ± 5 BPM
  - Light activity: 90 ± 10 BPM
  - Moderate-Vigorous activity: 135 ± 20 BPM

### Data Quality Features
- Invalid values marked with -9999
- Activity-dependent gaps in data:
  - Sedentary periods: 80% probability of gaps
  - Light activity: 40% probability of gaps
  - Moderate-Vigorous activity: 10% probability of gaps
- Gap duration follows gamma distribution (mean ~120s)
- 1% invalid readings in accelerometer data
- 2% invalid readings in heart rate data
- Realistic sampling jitter (±10% of nominal interval)

## Activity States

The generator models three activity states with different characteristics:

1. **Sedentary**
   - Duration: 30 ± 10 minutes
   - Low accelerometer magnitude (9.61 ± 0.20 m/s²)
   - Low heart rate (60 ± 5 BPM)
   - More common during night hours (23:00-06:00)
   - Highest probability of data gaps (80%)

2. **Light Activity**
   - Duration: 15 ± 5 minutes
   - Moderate accelerometer magnitude (11.77 ± 0.98 m/s²)
   - Moderate heart rate (90 ± 10 BPM)
   - Common during day hours
   - Medium probability of data gaps (40%)

3. **Moderate-Vigorous Activity**
   - Duration: 30 ± 10 minutes
   - High accelerometer magnitude (17.66 ± 2.94 m/s²)
   - Elevated heart rate (135 ± 20 BPM)
   - Less frequent during day hours
   - Lowest probability of data gaps (10%)

## Time-of-Day Patterns

The generator incorporates time-of-day patterns in activity selection:
- Night hours (23:00-06:00): Primarily sedentary state
- Day hours: Weighted distribution of activities:
  - Sedentary: 40%
  - Light activity: 40%
  - Moderate-Vigorous activity: 20%

## Output Format

The generator returns two pandas DataFrames that follow the OCED format:

### Accelerometer DataFrame
```python
acc_df.columns = ['timestamp', 'x', 'y', 'z']  # All values in m/s²
```

### Heart Rate DataFrame
```python
hr_df.columns = ['timestamp', 'bpm', 'pp']
```

Both DataFrames use datetime objects for timestamps and include invalid values marked with the specified invalid_value (-9999 by default).

## Integration with OCED

The generated data follows the OCED (Object-Centric Event Data) format defined in `schema/OCED-mHealth.json`. This ensures compatibility with:
- Process mining tools
- Existing GameBus data processing pipelines
- Health behavior analysis workflows

## Example

```python
from datetime import datetime
from src.synthetic_generation.synthetic_data_generator import SyntheticSensorDataGenerator

# Create generator for a specific time range
generator = SyntheticSensorDataGenerator(
    start_timestamp=datetime(2024, 1, 1, 8, 0),
    end_timestamp=datetime(2024, 1, 2, 8, 0)
)

# Generate data
acc_df, hr_df = generator.generate_sensor_data()

# Print some statistics
print("Accelerometer data shape:", acc_df.shape)
print("Heart rate data shape:", hr_df.shape)
print("\nAccelerometer statistics:")
print(acc_df.describe())
print("\nHeart rate statistics:")
print(hr_df.describe())

# Save to OCED format
acc_df.to_json('data/synthetic/accelerometer_events.json', orient='records')
hr_df.to_json('data/synthetic/heartrate_events.json', orient='records')
```

## Notes

- The generator uses numpy's random number generator. For reproducible results, set a random seed before generating data.
- The activity state parameters and time-of-day patterns can be modified by adjusting the `activity_states` dictionary in the class.
- The gap distribution and invalid value frequencies are based on real GameBus data patterns but can be adjusted if needed.
- The generated data is designed to be compatible with the existing GameBus data processing pipeline.
- All accelerometer values are in m/s² (1g = 9.81 m/s²).
- Data gaps are more likely to occur during sedentary periods, reflecting real-world sensor behavior.
 