import pandas as pd
import numpy as np

def resample_data(df, freq_ms=20, max_gap_ms=1000):
    """
    Resample sensor data to a consistent sampling frequency using linear interpolation.
    Data points separated by gaps larger than max_gap_ms will not be interpolated.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        Input DataFrame with timestamp index
    freq_ms : int
        Resampling frequency in milliseconds (e.g., 20 for 50Hz, 100 for 10Hz)
    max_gap_ms : int
        Maximum allowed gap in milliseconds between data points for interpolation
    
    Returns:
    --------
    pandas.DataFrame
        Resampled DataFrame with NaN values where gaps exceed max_gap_ms
    """
    # Convert timestamp to datetime if it's not already
    if not isinstance(df.index, pd.DatetimeIndex):
        # Convert to seconds by dividing by 1000 if the timestamps are in milliseconds
        if df.index.max() > 1e12:  # If timestamps are in milliseconds
            df.index = pd.to_datetime(df.index / 1000, unit='s')
        else:
            df.index = pd.to_datetime(df.index, unit='s')
    
    # Calculate the original sampling frequency
    time_diffs = df.index.to_series().diff()
    original_freq_ms = time_diffs.median().total_seconds() * 1000
    
    # If the requested frequency is different from original, print a warning
    if abs(original_freq_ms - freq_ms) > 1:  # Allow 1ms tolerance
        print(f"Warning: Original sampling frequency ({original_freq_ms:.1f}ms) differs from requested frequency ({freq_ms}ms)")
    
    # Convert frequency to pandas frequency string
    freq_str = f"{freq_ms}ms"
    
    # Resample to create new time points
    df_resampled = df.resample(freq_str).asfreq()
    
    # Calculate time differences between consecutive non-NaN values
    time_diffs = df_resampled.index.to_series().diff()
    
    # Create a mask for gaps larger than max_gap_ms
    large_gaps = time_diffs > pd.Timedelta(milliseconds=max_gap_ms)
    
    # Apply linear interpolation
    df_resampled = df_resampled.interpolate(method='linear')
    
    # Set values to NaN where gaps are too large
    for col in df_resampled.columns:
        df_resampled.loc[large_gaps, col] = np.nan
    
    return df_resampled 