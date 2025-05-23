import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional, List

class SensorEventAbstraction:
    def __init__(self, **sensor_dfs):
        """
        Initialize the SensorEventAbstraction class with any number of sensor dataframes.
        
        Args:
            **sensor_dfs: Keyword arguments where each key is a sensor name and value is a DataFrame.
                        Each DataFrame must have a 'timestamp' column and any number of data columns.
                        Example: accelerometer=acc_df, heartrate=hr_df, temperature=temp_df
        
        Example:
            sensor_abstraction = SensorEventAbstraction(
                accelerometer=acc_df,  # columns: ['timestamp', 'x', 'y', 'z']
                heartrate=hr_df,      # columns: ['timestamp', 'bpm', 'pp']
                temperature=temp_df    # columns: ['timestamp', 'temp']
            )
        """
        self.sensor_dfs = {}
        self.sync_df = None
        self.data_quality_mask = None  # Will store boolean mask for data quality
        self.sentinel_value = -9999  # Sentinel value for invalid data
        
        # Process each sensor dataframe
        for sensor_name, df in sensor_dfs.items():
            if not isinstance(df, pd.DataFrame):
                raise TypeError(f"Sensor data for '{sensor_name}' must be a pandas DataFrame")
            
            if 'timestamp' not in df.columns:
                raise ValueError(f"DataFrame for '{sensor_name}' must contain a 'timestamp' column")
            
            # Make a copy and ensure timestamp is datetime
            df_copy = df.copy()
            df_copy['timestamp'] = pd.to_datetime(df_copy['timestamp'])
            
            # Sort by timestamp
            df_copy = df_copy.sort_values('timestamp')
            
            # Store the processed dataframe
            self.sensor_dfs[sensor_name] = df_copy
    
    def create_sync_timestamps(self, sampling_freq=25):
        """
        Create a synchronized timestamp series at the specified sampling frequency.
        
        Args:
            sampling_freq (int): Sampling frequency in Hz (default: 25 Hz)
            
        Returns:
            pd.DatetimeIndex: Synchronized timestamps at specified frequency
        """
        if not self.sensor_dfs:
            raise ValueError("No sensor data available")
        
        # Find the overall start and end times across all sensors
        start_times = [df['timestamp'].min() for df in self.sensor_dfs.values()]
        end_times = [df['timestamp'].max() for df in self.sensor_dfs.values()]
        
        start_time = max(start_times)
        end_time = min(end_times)
        
        # Create evenly spaced timestamps using frequency
        timestamps = pd.date_range(
            start=start_time,
            end=end_time,
            freq=f'{1000/sampling_freq}ms'  # Convert Hz to milliseconds
        )
        
        return timestamps
    
    def interpolate_sensor_data(self, timestamps, max_gap_seconds):
        """
        Interpolate all sensor data to the synchronized timestamps, respecting maximum gap thresholds.
        Uses a sentinel value for invalid data and maintains a data quality mask.
        
        Args:
            timestamps (pd.DatetimeIndex): Synchronized timestamps
            max_gap_seconds (float): Maximum acceptable gap between consecutive sensor events in seconds.
                                   Timestamps falling within larger gaps will be marked as invalid.
            
        Returns:
            tuple: (pd.DataFrame, pd.DataFrame) containing:
                - Synchronized and interpolated sensor data (using sentinel_value for invalid data)
                - Boolean mask indicating valid data (True) vs invalid data (False)
        """
        # Create empty dataframe with synchronized timestamps
        sync_df = pd.DataFrame(index=timestamps)
        sync_df.index.name = 'timestamp'
        
        # Create data quality mask (True = valid data, False = invalid data)
        # First create a combined mask for all sensors
        combined_quality_mask = pd.Series(True, index=timestamps)
        
        # Convert timestamps to numpy array of seconds since start, ensuring float64 type
        timestamps_seconds = (timestamps - timestamps[0]).total_seconds().astype(np.float64)
        
        # First pass: identify invalid periods for all sensors
        for sensor_name, df in self.sensor_dfs.items():
            # Sort by timestamp to ensure correct gap detection
            df = df.sort_values('timestamp')
            
            # Calculate time differences between consecutive events
            time_diffs = df['timestamp'].diff().dt.total_seconds().astype(np.float64)
            
            # Identify valid segments (where gaps are <= max_gap_seconds)
            valid_segments = []
            current_segment_start = 0
            in_segment = False
            
            for i in range(1, len(df)):
                if time_diffs.iloc[i] <= max_gap_seconds:
                    if not in_segment:
                        # Start of a new segment
                        current_segment_start = i - 1
                        in_segment = True
                else:
                    if in_segment:
                        # End of current segment
                        if i - current_segment_start >= 2:  # Only add segments with at least 2 points
                            valid_segments.append((current_segment_start, i))
                        in_segment = False
            
            # Handle the last segment if we're still in one
            if in_segment and len(df) - current_segment_start >= 2:
                valid_segments.append((current_segment_start, len(df)))
            
            # Create a mask for this sensor's valid periods
            sensor_valid_mask = pd.Series(False, index=timestamps)
            
            # Mark timestamps within valid segments as True
            for start_idx, end_idx in valid_segments:
                segment_start = df['timestamp'].iloc[start_idx]
                segment_end = df['timestamp'].iloc[end_idx - 1]  # -1 because end_idx is exclusive
                mask = (timestamps >= segment_start) & (timestamps <= segment_end)
                sensor_valid_mask[mask] = True
            
            # Update combined mask - if any sensor is invalid, the combined mask is invalid
            combined_quality_mask = combined_quality_mask & sensor_valid_mask
        
        # Second pass: interpolate data using the combined quality mask
        quality_mask = pd.DataFrame(False, index=timestamps, columns=[])
        
        for sensor_name, df in self.sensor_dfs.items():
            # Get all columns except timestamp
            data_columns = [col for col in df.columns if col != 'timestamp']
            
            # Sort by timestamp to ensure correct gap detection
            df = df.sort_values('timestamp')
            
            # For each data column, interpolate within valid segments only
            for col in data_columns:
                col_name = f'{sensor_name}_{col}'
                # Initialize column with sentinel value
                sync_df[col_name] = self.sentinel_value
                # Initialize quality mask column using the combined mask
                quality_mask[col_name] = combined_quality_mask.copy()
                
                # Only interpolate where the combined mask is True
                valid_mask = combined_quality_mask
                if np.any(valid_mask):
                    # Get all timestamps and values
                    sensor_timestamps = np.array(
                        (df['timestamp'] - timestamps[0]).dt.total_seconds(),
                        dtype=np.float64
                    )
                    sensor_values = np.array(
                        df[col],
                        dtype=np.float64
                    )
                    
                    # Interpolate only for valid timestamps
                    interpolated_values = np.interp(
                        timestamps_seconds[valid_mask],
                        sensor_timestamps,
                        sensor_values
                    )
                    # Update sync_df with interpolated values
                    sync_df.loc[valid_mask, col_name] = interpolated_values
        
        return sync_df, quality_mask
    
    def synchronize_sensors(self, sampling_freq=25, max_gap_seconds=1.0):
        """
        Synchronize all sensor dataframes to a common sampling frequency using linear interpolation.
        Respects maximum gap thresholds to avoid interpolating across large gaps.
        
        Args:
            sampling_freq (int): Target sampling frequency in Hz (default: 25 Hz)
            max_gap_seconds (float): Maximum acceptable gap between consecutive sensor events in seconds.
                                   Timestamps falling within larger gaps will be marked as invalid.
                                   Default is 1.0 second.
            
        Returns:
            pd.DataFrame: Synchronized and interpolated sensor data (using sentinel_value for invalid data)
        """
        # Create synchronized timestamps
        sync_timestamps = self.create_sync_timestamps(sampling_freq)
        
        # Interpolate sensor data and get quality mask
        self.sync_df, self.data_quality_mask = self.interpolate_sensor_data(sync_timestamps, max_gap_seconds)
        
        return self.sync_df
    
    def get_valid_data(self, sensor_name=None, column=None):
        """
        Get a view of the synchronized data with only valid values (excluding sentinel values).
        
        Args:
            sensor_name (str, optional): Filter for a specific sensor
            column (str, optional): Filter for a specific column
            
        Returns:
            pd.DataFrame: DataFrame containing only valid data points
        """
        if self.sync_df is None:
            raise ValueError("Data has not been synchronized yet. Call synchronize_sensors() first.")
        
        # Get the relevant columns
        if sensor_name is not None:
            if column is not None:
                cols = [f"{sensor_name}_{column}"]
            else:
                cols = [col for col in self.sync_df.columns if col.startswith(f"{sensor_name}_")]
        else:
            cols = self.sync_df.columns
        
        # Create a copy of the data
        valid_data = self.sync_df[cols].copy()
        
        # Replace sentinel values with NaN for easier filtering
        valid_data = valid_data.replace(self.sentinel_value, np.nan)
        
        return valid_data
    
    def get_data_quality_stats(self):
        """
        Get statistics about data quality across all synchronized sensors.
        Since we now use a combined quality mask, these statistics apply to all sensors.
        
        Returns:
            dict: Dictionary containing data quality statistics:
                - total_samples: Total number of synchronized timestamps
                - valid_samples: Number of timestamps where all sensors have valid data
                - invalid_samples: Number of timestamps where any sensor has invalid data
                - valid_percentage: Percentage of timestamps with valid data
                - invalid_percentage: Percentage of timestamps with invalid data
                - total_duration: Total duration of the dataset in seconds
                - valid_duration: Total duration of valid data in seconds
                - invalid_duration: Total duration of invalid data in seconds
                - gap_stats: Dictionary with statistics about gaps:
                    - num_gaps: Number of distinct gaps in the data
                    - max_gap_duration: Duration of the longest gap in seconds
                    - mean_gap_duration: Average duration of gaps in seconds
                    - median_gap_duration: Median duration of gaps in seconds
        """
        if not hasattr(self, 'data_quality_mask'):
            raise ValueError("Sensors must be synchronized before getting quality stats")
            
        if len(self.data_quality_mask.columns) == 0:
            return {
                'total_samples': 0,
                'valid_samples': 0,
                'invalid_samples': 0,
                'valid_percentage': 0.0,
                'invalid_percentage': 0.0,
                'total_duration': 0.0,
                'valid_duration': 0.0,
                'invalid_duration': 0.0,
                'gap_stats': {
                    'num_gaps': 0,
                    'max_gap_duration': 0.0,
                    'mean_gap_duration': 0.0,
                    'median_gap_duration': 0.0
                }
            }
            
        # Get the combined quality mask (using any column since they're all the same)
        combined_mask = self.data_quality_mask.iloc[:, 0]
        
        # Basic sample statistics
        total_samples = len(combined_mask)
        valid_samples = combined_mask.sum()
        invalid_samples = total_samples - valid_samples
        
        # Calculate percentages
        valid_percentage = (valid_samples / total_samples) * 100 if total_samples > 0 else 0.0
        invalid_percentage = (invalid_samples / total_samples) * 100 if total_samples > 0 else 0.0
        
        # Calculate durations
        timestamps = self.data_quality_mask.index
        total_duration = (timestamps[-1] - timestamps[0]).total_seconds()
        
        # Calculate gap statistics
        transitions = np.where(combined_mask.diff().fillna(False))[0]
        gap_durations = []
        
        # Handle edge cases
        if not combined_mask.iloc[0]:  # If first point is invalid
            transitions = np.concatenate(([0], transitions))
        if not combined_mask.iloc[-1]:  # If last point is invalid
            transitions = np.concatenate((transitions, [len(combined_mask) - 1]))
            
        # Calculate gap durations
        for i in range(0, len(transitions) - 1, 2):
            if i + 1 < len(transitions):
                start_idx = transitions[i]
                end_idx = transitions[i + 1]
                if not combined_mask.iloc[start_idx]:  # Only process invalid periods
                    start_time = timestamps[start_idx]
                    end_time = timestamps[end_idx]
                    duration = (end_time - start_time).total_seconds()
                    gap_durations.append(duration)
        
        # Calculate gap statistics
        gap_stats = {
            'num_gaps': len(gap_durations),
            'max_gap_duration': max(gap_durations) if gap_durations else 0.0,
            'mean_gap_duration': np.mean(gap_durations) if gap_durations else 0.0,
            'median_gap_duration': np.median(gap_durations) if gap_durations else 0.0
        }
        
        # Calculate valid and invalid durations
        valid_duration = sum(duration for duration in gap_durations if duration > 0)
        invalid_duration = total_duration - valid_duration
        
        return {
            'total_samples': total_samples,
            'valid_samples': valid_samples,
            'invalid_samples': invalid_samples,
            'valid_percentage': valid_percentage,
            'invalid_percentage': invalid_percentage,
            'total_duration': total_duration,
            'valid_duration': valid_duration,
            'invalid_duration': invalid_duration,
            'gap_stats': gap_stats
        }
    
    def get_sync_stats(self):
        """
        Get statistics about the synchronized data.
        Now returns combined statistics since all sensors share the same quality mask.
        
        Returns:
            dict: Dictionary containing synchronization statistics:
                - sampling_frequency: The sampling frequency used for synchronization
                - max_gap_seconds: The maximum allowed gap duration
                - num_sensors: Number of sensors being synchronized
                - sensor_names: List of sensor names
                - sensor_columns: Dictionary mapping sensor names to their data columns
                - data_quality: Dictionary containing data quality statistics (from get_data_quality_stats)
        """
        if not hasattr(self, 'sync_df'):
            raise ValueError("Sensors must be synchronized before getting sync stats")
            
        # Get data quality statistics
        quality_stats = self.get_data_quality_stats()
        
        # Get sensor information
        sensor_info = {}
        for col in self.sync_df.columns:
            if col != 'timestamp':
                sensor_name, data_col = col.split('_', 1)
                if sensor_name not in sensor_info:
                    sensor_info[sensor_name] = []
                sensor_info[sensor_name].append(data_col)
        
        return {
            'num_sensors': len(sensor_info),
            'sensor_names': list(sensor_info.keys()),
            'sensor_columns': sensor_info,
            'data_quality': quality_stats
        }
    
    def get_sensor_names(self) -> List[str]:
        """
        Get list of sensor names that were provided during initialization.
        
        Returns:
            List[str]: List of sensor names
        """
        return list(self.sensor_dfs.keys())
    
    def get_sensor_columns(self, sensor_name: str) -> List[str]:
        """
        Get list of columns for a specific sensor.
        
        Args:
            sensor_name (str): Name of the sensor
            
        Returns:
            List[str]: List of column names for the specified sensor
        """
        if sensor_name not in self.sensor_dfs:
            raise ValueError(f"Unknown sensor name: {sensor_name}")
        
        return [col for col in self.sensor_dfs[sensor_name].columns if col != 'timestamp']
    
    def get_invalid_periods(self, min_duration_seconds=0.0):
        """
        Get periods where data is invalid (has gaps) across all synchronized sensors.
        Since we use a combined quality mask, these periods represent times where ANY sensor has invalid data.
        
        Args:
            min_duration_seconds (float): Minimum duration of invalid period to include (default: 0.0)
            
        Returns:
            dict: Dictionary with a single key 'all_sensors' containing a list of invalid periods.
                  Each invalid period is represented as a tuple of (start_time, end_time, duration_seconds):
                  - start_time: datetime object indicating when the invalid period starts
                  - end_time: datetime object indicating when the invalid period ends
                  - duration_seconds: float indicating the duration of the invalid period in seconds
                  
        Example:
            {
                'all_sensors': [
                    (datetime(2025, 5, 11, 10, 0, 0), datetime(2025, 5, 11, 10, 5, 0), 300.0),
                    (datetime(2025, 5, 11, 15, 0, 0), datetime(2025, 5, 11, 15, 10, 0), 600.0)
                ]
            }
        """
        if not hasattr(self, 'data_quality_mask'):
            raise ValueError("Sensors must be synchronized before getting invalid periods")
            
        # Get the combined quality mask (using any column since they're all the same now)
        if len(self.data_quality_mask.columns) == 0:
            return {'all_sensors': []}
            
        # Use the first column's mask since all columns have the same mask
        combined_mask = self.data_quality_mask.iloc[:, 0]
        
        # Find transitions between valid and invalid periods
        transitions = np.where(combined_mask.diff().fillna(False))[0]
        
        invalid_periods = []
        
        # Handle edge cases
        if len(transitions) == 0:
            if not combined_mask.iloc[0]:  # If first point is invalid
                start_time = self.data_quality_mask.index[0]
                end_time = self.data_quality_mask.index[-1]
                duration = (end_time - start_time).total_seconds()
                if duration >= min_duration_seconds:
                    invalid_periods.append((start_time, end_time, duration))
        else:
            # Add first period if it starts with invalid data
            if not combined_mask.iloc[0]:
                start_time = self.data_quality_mask.index[0]
                end_time = self.data_quality_mask.index[transitions[0]]
                duration = (end_time - start_time).total_seconds()
                if duration >= min_duration_seconds:
                    invalid_periods.append((start_time, end_time, duration))
            
            # Process all transitions
            for i in range(0, len(transitions), 2):
                if i + 1 < len(transitions):
                    start_idx = transitions[i]
                    end_idx = transitions[i + 1]
                    if not combined_mask.iloc[start_idx]:  # Only process invalid periods
                        start_time = self.data_quality_mask.index[start_idx]
                        end_time = self.data_quality_mask.index[end_idx]
                        duration = (end_time - start_time).total_seconds()
                        if duration >= min_duration_seconds:
                            invalid_periods.append((start_time, end_time, duration))
            
            # Add last period if it ends with invalid data
            if not combined_mask.iloc[-1]:
                start_time = self.data_quality_mask.index[transitions[-1]]
                end_time = self.data_quality_mask.index[-1]
                duration = (end_time - start_time).total_seconds()
                if duration >= min_duration_seconds:
                    invalid_periods.append((start_time, end_time, duration))
        
        return {'all_sensors': invalid_periods}
    
    def get_invalid_periods_df(self, min_duration_seconds=0.0):
        """
        Get invalid periods as a pandas DataFrame.
        
        Args:
            min_duration_seconds (float): Minimum duration of invalid period to include (default: 0.0)
            
        Returns:
            pandas.DataFrame: DataFrame containing invalid periods with columns:
                - start_time: datetime object indicating when the invalid period starts
                - end_time: datetime object indicating when the invalid period ends
                - duration_seconds: float indicating the duration of the invalid period in seconds
                
        Example:
            >>> invalid_periods_df = sensor_abstraction.get_invalid_periods_df()
            >>> print(invalid_periods_df)
                        start_time             end_time  duration_seconds
            0 2025-05-11 10:00:00 2025-05-11 10:05:00            300.0
            1 2025-05-11 15:00:00 2025-05-11 15:10:00            600.0
        """
        invalid_periods = self.get_invalid_periods(min_duration_seconds)
        
        # Convert the list of tuples to a DataFrame
        df = pd.DataFrame(invalid_periods['all_sensors'], 
                         columns=['start_time', 'end_time', 'duration_seconds'])
        
        # Sort by start_time
        df = df.sort_values('start_time')
        
        # Reset index
        df = df.reset_index(drop=True)
        
        return df
    
    def get_valid_periods_df(self, min_duration_seconds=0.0):
        """
        Get a pandas DataFrame containing valid periods across all synchronized sensors.
        
        Args:
            min_duration_seconds (float, optional): Minimum duration in seconds for a period to be included.
                Defaults to 0.0, which includes all valid periods.
        
        Returns:
            pandas.DataFrame: DataFrame containing valid periods with columns:
                - start_time: datetime of period start
                - end_time: datetime of period end
                - duration_seconds: duration of the period in seconds
        
        Example:
            >>> valid_periods_df = sensor_abstraction.get_valid_periods_df()
            >>> print(valid_periods_df.head())
            >>> # Calculate some statistics
            >>> print(f"Total number of valid periods: {len(valid_periods_df)}")
            >>> print(f"Total valid duration: {valid_periods_df['duration_seconds'].sum()/3600:.1f} hours")
            >>> print(f"Average valid period duration: {valid_periods_df['duration_seconds'].mean():.1f} seconds")
            >>> print(f"Longest valid period: {valid_periods_df['duration_seconds'].max():.1f} seconds")
        """
        if not hasattr(self, 'data_quality_mask'):
            raise ValueError("Sensors must be synchronized before getting valid periods")
        
        # Get timestamps and mask
        timestamps = self.data_quality_mask.index
        mask = self.data_quality_mask.iloc[:, 0]  # Use first column since all are same
        
        # Find transitions between valid and invalid periods
        transitions = np.where(mask.diff().fillna(False))[0]
        
        # Initialize list to store valid periods
        valid_periods = []
        
        # Handle edge cases and process transitions
        if len(transitions) == 0:
            if mask.iloc[0]:  # If first point is valid
                valid_periods.append((timestamps[0], timestamps[-1]))
        else:
            # Add first period if it starts with valid data
            if mask.iloc[0]:
                valid_periods.append((timestamps[0], timestamps[transitions[0]]))
            
            # Process all transitions
            for i in range(0, len(transitions), 2):
                if i + 1 < len(transitions):
                    start_idx = transitions[i]
                    end_idx = transitions[i + 1]
                    if mask.iloc[start_idx]:  # Only process valid periods
                        valid_periods.append((timestamps[start_idx], timestamps[end_idx]))
            
            # Add last period if it ends with valid data
            if mask.iloc[-1]:
                valid_periods.append((timestamps[transitions[-1]], timestamps[-1]))
        
        # Convert to DataFrame and filter by minimum duration
        if valid_periods:
            df = pd.DataFrame(valid_periods, columns=['start_time', 'end_time'])
            df['duration_seconds'] = (df['end_time'] - df['start_time']).dt.total_seconds()
            df = df[df['duration_seconds'] >= min_duration_seconds]
            df = df.sort_values('start_time').reset_index(drop=True)
        else:
            df = pd.DataFrame(columns=['start_time', 'end_time', 'duration_seconds'])
        
        return df
    
    def get_validity_stats(self):
        """
        Get detailed statistics about valid and invalid periods, including both counts and durations.
        Validity is calculated based on total duration of valid periods vs total time span.
        
        Returns:
            dict: Dictionary containing statistics about valid and invalid periods:
                - valid_periods: number of valid periods
                - invalid_periods: number of invalid periods
                - valid_duration: total duration of valid periods in seconds
                - invalid_duration: total duration of invalid periods in seconds
                - total_time_span: total time span of the data in seconds
                - valid_percentage: percentage of total time span that is valid
                - invalid_percentage: percentage of total time span that is invalid
                - avg_valid_duration: average duration of valid periods in seconds
                - avg_invalid_duration: average duration of invalid periods in seconds
        """
        if not hasattr(self, 'data_quality_mask'):
            raise ValueError("Sensors must be synchronized before getting validity stats")
        
        # Get timestamps and mask
        timestamps = self.data_quality_mask.index
        mask = self.data_quality_mask.iloc[:, 0]  # Use first column since all are same
        
        # Calculate total time span
        total_time_span = (timestamps[-1] - timestamps[0]).total_seconds()
        
        # Calculate time differences between consecutive timestamps
        time_diffs = np.diff(timestamps.astype(np.int64)) / 1e9  # Convert to seconds
        
        # Calculate valid duration by summing time differences where mask is True
        # We need to use mask[:-1] because time_diffs is one element shorter than mask
        valid_duration = np.sum(time_diffs[mask[:-1].values])
        invalid_duration = total_time_span - valid_duration
        
        # Find transitions to get period counts and average durations
        transitions = np.where(mask.diff().fillna(False))[0]
        
        # Initialize lists to store periods
        valid_periods = []
        invalid_periods = []
        
        # Handle edge cases and process transitions
        if len(transitions) == 0:
            if mask.iloc[0]:  # If first point is valid
                valid_periods.append((timestamps[0], timestamps[-1]))
            else:  # If first point is invalid
                invalid_periods.append((timestamps[0], timestamps[-1]))
        else:
            # Add first period if it starts with valid data
            if mask.iloc[0]:
                valid_periods.append((timestamps[0], timestamps[transitions[0]]))
            else:
                invalid_periods.append((timestamps[0], timestamps[transitions[0]]))
            
            # Process all transitions
            for i in range(0, len(transitions), 2):
                if i + 1 < len(transitions):
                    start_idx = transitions[i]
                    end_idx = transitions[i + 1]
                    if mask.iloc[start_idx]:  # Process valid periods
                        valid_periods.append((timestamps[start_idx], timestamps[end_idx]))
                    else:  # Process invalid periods
                        invalid_periods.append((timestamps[start_idx], timestamps[end_idx]))
            
            # Add last period if it ends with valid data
            if mask.iloc[-1]:
                valid_periods.append((timestamps[transitions[-1]], timestamps[-1]))
            else:
                invalid_periods.append((timestamps[transitions[-1]], timestamps[-1]))
        
        # Calculate average durations
        valid_durations = [(end - start).total_seconds() for start, end in valid_periods]
        invalid_durations = [(end - start).total_seconds() for start, end in invalid_periods]
        
        # Calculate statistics
        stats = {
            'valid_periods': len(valid_periods),
            'invalid_periods': len(invalid_periods),
            'valid_duration': valid_duration,
            'invalid_duration': invalid_duration,
            'total_time_span': total_time_span,
            'valid_percentage': (valid_duration / total_time_span) * 100,
            'invalid_percentage': (invalid_duration / total_time_span) * 100,
            'avg_valid_duration': np.mean(valid_durations) if valid_durations else 0,
            'avg_invalid_duration': np.mean(invalid_durations) if invalid_durations else 0
        }
        
        return stats
    
    def print_validity_stats(self):
        """
        Print detailed statistics about valid and invalid periods in a readable format.
        Validity is calculated based on total duration of valid periods vs total time span.
        """
        stats = self.get_validity_stats()
        
        print("\nValidity Statistics:")
        print(f"\nTotal Time Span: {stats['total_time_span']/3600:.1f} hours")
        
        print("\nBy Duration:")
        print(f"Valid duration: {stats['valid_duration']/3600:.1f} hours ({stats['valid_percentage']:.1f}% of total time)")
        print(f"Invalid duration: {stats['invalid_duration']/3600:.1f} hours ({stats['invalid_percentage']:.1f}% of total time)")
        
        print("\nPeriod Counts:")
        print(f"Number of valid periods: {stats['valid_periods']:,}")
        print(f"Number of invalid periods: {stats['invalid_periods']:,}")
        
        print("\nAverage Durations:")
        print(f"Average valid period: {stats['avg_valid_duration']:.1f} seconds")
        print(f"Average invalid period: {stats['avg_invalid_duration']:.1f} seconds")
    
    def plot_valid_periods_hist(self, min_duration_seconds=0.0, bins=50, figsize=(10, 6)):
        """
        Plot a histogram of valid periods durations.
        
        Args:
            min_duration_seconds (float, optional): Minimum duration in seconds for a period to be included.
                Defaults to 0.0, which includes all valid periods.
            bins (int, optional): Number of bins for the histogram. Defaults to 50.
            figsize (tuple, optional): Figure size (width, height) in inches. Defaults to (10, 6).
        
        Example:
            >>> # Plot all valid periods
            >>> sensor_abstraction.plot_valid_periods_hist()
            >>> 
            >>> # Plot only valid periods longer than 1 minute
            >>> sensor_abstraction.plot_valid_periods_hist(min_duration_seconds=60)
            >>> 
            >>> # Customize the plot
            >>> sensor_abstraction.plot_valid_periods_hist(bins=30, figsize=(12, 8))
        """
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        # Get valid periods DataFrame
        valid_periods_df = self.get_valid_periods_df(min_duration_seconds)
        
        if len(valid_periods_df) == 0:
            print("No valid periods found with the given minimum duration.")
            return
        
        # Create the plot
        plt.figure(figsize=figsize)
        
        # Plot histogram
        sns.histplot(data=valid_periods_df['duration_seconds'], bins=bins)
        
        # Add mean line
        mean_duration = valid_periods_df['duration_seconds'].mean()
        plt.axvline(mean_duration, color='r', linestyle='--', 
                    label=f'Mean: {mean_duration:.1f}s')
        
        # Customize the plot
        plt.title('Distribution of Valid Periods Duration')
        plt.xlabel('Duration (seconds)')
        plt.ylabel('Count')
        plt.legend()
        
        # Add statistics as text
        stats_text = (
            f"Total valid periods: {len(valid_periods_df):,}\n"
            f"Mean duration: {mean_duration:.1f}s\n"
            f"Median duration: {valid_periods_df['duration_seconds'].median():.1f}s\n"
            f"Max duration: {valid_periods_df['duration_seconds'].max():.1f}s\n"
            f"Min duration: {valid_periods_df['duration_seconds'].min():.1f}s\n"
            f"Total valid time: {valid_periods_df['duration_seconds'].sum()/3600:.1f}h"
        )
        plt.text(0.95, 0.95, stats_text,
                 transform=plt.gca().transAxes,
                 verticalalignment='top',
                 horizontalalignment='right',
                 bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        plt.show()
    
    def plot_invalid_periods_hist(self, min_duration_seconds=0.0, bins=50, figsize=(10, 6)):
        """
        Plot a histogram of invalid periods durations.
        
        Args:
            min_duration_seconds (float, optional): Minimum duration in seconds for a period to be included.
                Defaults to 0.0, which includes all invalid periods.
            bins (int, optional): Number of bins for the histogram. Defaults to 50.
            figsize (tuple, optional): Figure size (width, height) in inches. Defaults to (10, 6).
        
        Example:
            >>> # Plot all invalid periods
            >>> sensor_abstraction.plot_invalid_periods_hist()
            >>> 
            >>> # Plot only invalid periods longer than 1 minute
            >>> sensor_abstraction.plot_invalid_periods_hist(min_duration_seconds=60)
            >>> 
            >>> # Customize the plot
            >>> sensor_abstraction.plot_invalid_periods_hist(bins=30, figsize=(12, 8))
        """
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        # Get invalid periods DataFrame
        invalid_periods_df = self.get_invalid_periods_df(min_duration_seconds)
        
        if len(invalid_periods_df) == 0:
            print("No invalid periods found with the given minimum duration.")
            return
        
        # Create the plot
        plt.figure(figsize=figsize)
        
        # Plot histogram
        sns.histplot(data=invalid_periods_df['duration_seconds'], bins=bins)
        
        # Add mean line
        mean_duration = invalid_periods_df['duration_seconds'].mean()
        plt.axvline(mean_duration, color='r', linestyle='--', 
                    label=f'Mean: {mean_duration:.1f}s')
        
        # Customize the plot
        plt.title('Distribution of Invalid Periods Duration')
        plt.xlabel('Duration (seconds)')
        plt.ylabel('Count')
        plt.legend()
        
        # Add statistics as text
        stats_text = (
            f"Total invalid periods: {len(invalid_periods_df):,}\n"
            f"Mean duration: {mean_duration:.1f}s\n"
            f"Median duration: {invalid_periods_df['duration_seconds'].median():.1f}s\n"
            f"Max duration: {invalid_periods_df['duration_seconds'].max():.1f}s\n"
            f"Min duration: {invalid_periods_df['duration_seconds'].min():.1f}s\n"
            f"Total invalid time: {invalid_periods_df['duration_seconds'].sum()/3600:.1f}h"
        )
        plt.text(0.95, 0.95, stats_text,
                 transform=plt.gca().transAxes,
                 verticalalignment='top',
                 horizontalalignment='right',
                 bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        plt.show() 