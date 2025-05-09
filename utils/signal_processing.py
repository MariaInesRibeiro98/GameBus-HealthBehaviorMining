import pandas as pd
import numpy as np
from typing import Union, Optional

def recalibrate_sampling_frequency(
    df: pd.DataFrame,
    timestamp_col: str = 'timestamp',
    max_gap: str = '1S'
) -> pd.DataFrame:
    """
    Recalibrate the sampling frequency of sensor data using linear interpolation.
    Uses the median time interval from the original data as the target frequency.
    
    Args:
        df (pd.DataFrame): Input DataFrame containing sensor data
        timestamp_col (str): Name of the timestamp column
        max_gap (str): Maximum allowed gap between samples (e.g., '1S', '500ms')
    
    Returns:
        pd.DataFrame: Recalibrated DataFrame with uniform sampling frequency
    """
    # Ensure timestamp column is datetime
    df[timestamp_col] = pd.to_datetime(df[timestamp_col])
    
    # Remove duplicate timestamps by keeping the first occurrence
    df = df.drop_duplicates(subset=[timestamp_col], keep='first')
    
    # Sort by timestamp to ensure correct order
    df = df.sort_values(by=timestamp_col)
    
    # Calculate time differences between consecutive samples
    time_diffs = df[timestamp_col].diff()
    
    # Calculate median time interval (excluding the first NaN value)
    median_interval = time_diffs.iloc[1:].median()
    
    # Create new timestamps with uniform intervals based on median
    new_timestamps = pd.date_range(
        start=df[timestamp_col].iloc[0],
        end=df[timestamp_col].iloc[-1],
        freq=median_interval
    )
    
    # Create a new DataFrame with the desired timestamps
    df_recalibrated = pd.DataFrame({timestamp_col: new_timestamps})
    
    # Add new timestamps to the original DataFrame
    df_combined = pd.concat([
        df,
        pd.DataFrame({timestamp_col: new_timestamps})
    ])
    
    # Sort by timestamp
    df_combined = df_combined.sort_values(by=timestamp_col)
    
    # Calculate gaps
    gaps = df_combined[timestamp_col].diff() > pd.Timedelta(max_gap)
    
    # Interpolate all columns at once
    df_combined = df_combined.interpolate(method='linear')
    
    # Set values to NaN where gaps are too large
    df_combined.loc[gaps] = np.nan
    
    # Keep only the new timestamps
    df_recalibrated = df_combined.loc[df_combined[timestamp_col].isin(new_timestamps)]
    
    # Remove any duplicates that might have been created during interpolation
    df_recalibrated = df_recalibrated.drop_duplicates(subset=[timestamp_col], keep='first')
    
    return df_recalibrated

# Example usage:
if __name__ == "__main__":
    # Create sample data with irregular intervals and duplicates
    dates = pd.to_datetime([
        '2024-01-01 00:00:00.000',
        '2024-01-01 00:00:00.100',
        '2024-01-01 00:00:00.100',  # Duplicate timestamp
        '2024-01-01 00:00:00.250',  # Gap > 100ms
        '2024-01-01 00:00:00.350',
        '2024-01-01 00:00:01.500',  # Gap > 1s
        '2024-01-01 00:00:01.600',
        '2024-01-01 00:00:01.700'
    ])
    data = np.random.randn(len(dates))
    df = pd.DataFrame({'timestamp': dates, 'value': data})
    
    # Recalibrate using median interval
    df_recalibrated = recalibrate_sampling_frequency(
        df=df,
        timestamp_col='timestamp',
        max_gap='1S'
    )
    
    print("Original data:")
    print(df)
    print("\nRecalibrated data:")
    print(df_recalibrated) 