# Data Preprocessing

This module provides functionality for preprocessing sensor data from GameBus, with a focus on resampling and time series data handling.

## Resampling

The `resampling.py` module provides functionality to resample sensor data to a consistent sampling frequency using linear interpolation.

### resample_data

```python
def resample_data(
    df: pd.DataFrame,
    freq_ms: int = 20,  # Resampling frequency in milliseconds
    max_gap_ms: int = 1000  # Maximum allowed gap for interpolation
) -> pd.DataFrame
```

Resamples sensor data to a consistent sampling frequency using linear interpolation. Data points separated by gaps larger than `max_gap_ms` will not be interpolated.

#### Parameters
- `df`: Input DataFrame with timestamp index
- `freq_ms`: Resampling frequency in milliseconds (e.g., 20 for 50Hz, 100 for 10Hz)
- `max_gap_ms`: Maximum allowed gap in milliseconds between data points for interpolation

#### Returns
- Resampled DataFrame with NaN values where gaps exceed `max_gap_ms`

#### Features
1. **Automatic Timestamp Handling**
   - Converts timestamps to datetime if not already in that format
   - Handles both millisecond and second timestamps
   - Warns if original sampling frequency differs from requested frequency

2. **Gap Handling**
   - Uses linear interpolation for gaps smaller than `max_gap_ms`
   - Sets values to NaN for gaps larger than `max_gap_ms`
   - Preserves data quality by not interpolating across large gaps

3. **Data Validation**
   - Checks for timestamp format
   - Validates sampling frequency
   - Handles missing or invalid data points

### Usage Example

```python
import pandas as pd
from src.preprocessing.resampling import resample_data

# Create sample data
data = {
    'timestamp': [1000, 1020, 1060, 1100],  # Timestamps in milliseconds
    'value': [1.0, 2.0, 3.0, 4.0]
}
df = pd.DataFrame(data)
df.set_index('timestamp', inplace=True)

# Resample to 20ms frequency (50Hz)
df_resampled = resample_data(df, freq_ms=20, max_gap_ms=1000)

# Resample to 100ms frequency (10Hz)
df_resampled_10hz = resample_data(df, freq_ms=100, max_gap_ms=1000)
```

### Input/Output Format

#### Input DataFrame
```
timestamp    value
1000         1.0
1020         2.0
1060         3.0
1100         4.0
```

#### Output DataFrame (20ms frequency)
```
timestamp    value
1000         1.0
1020         2.0
1040         2.5
1060         3.0
1080         3.5
1100         4.0
```

### Notes
- The function assumes timestamps are in milliseconds if they are larger than 1e12
- Linear interpolation is used for gaps smaller than `max_gap_ms`
- Large gaps (> `max_gap_ms`) are filled with NaN values
- The function warns if the original sampling frequency differs significantly from the requested frequency
- All timestamps are converted to pandas DatetimeIndex for consistent handling

### Dependencies
- pandas
- numpy

### Best Practices
1. **Sampling Frequency**
   - Choose a frequency that matches your analysis needs
   - Consider the original sampling rate of your sensors
   - Be aware that higher frequencies require more storage

2. **Gap Handling**
   - Set `max_gap_ms` based on your data characteristics
   - Consider the typical gaps in your sensor data
   - Be cautious with interpolation across large gaps

3. **Memory Usage**
   - Resampling can increase memory usage significantly
   - Consider downsampling for long time series
   - Process data in chunks if memory is limited 