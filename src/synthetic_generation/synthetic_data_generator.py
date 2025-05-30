import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from scipy import stats
from typing import Dict, Tuple, List, Optional
from tqdm import tqdm
import time

class SyntheticSensorDataGenerator:
    def __init__(self, 
                 start_timestamp: Optional[datetime] = None,
                 end_timestamp: Optional[datetime] = None,
                 movement_threshold: float = 0.49005,  # 0.05g = 0.4905 m/s²
                 acc_fs: float = 50.0,             # Hz
                 hr_fs: float = 12.5,              # Hz
                 invalid_value: float = -9999,     # For invalid readings
                 gap_value: float = -5555,         # For marking gaps (will be removed)
                 verbose: bool = True):
        """
        Initialize the synthetic sensor data generator.
        
        Args:
            start_timestamp: Start time for data generation (defaults to current time)
            end_timestamp: End time for data generation (defaults to start_time + 24h)
            movement_threshold: Threshold for movement detection in m/s² (default: 0.4905 m/s² = 0.05g)
            acc_fs: Accelerometer sampling frequency in Hz (default: 50 Hz)
            hr_fs: Heart rate sampling frequency in Hz (default: 12.5 Hz)
            invalid_value: Value used to mark invalid readings (default: -9999)
            gap_value: Value used to mark gaps before removal (default: -5555)
            verbose: Whether to print progress information (default: True)
        """
        self.start_timestamp = start_timestamp or datetime.now()
        self.end_timestamp = end_timestamp or (self.start_timestamp + timedelta(hours=24))
        self.duration_hours = (self.end_timestamp - self.start_timestamp).total_seconds() / 3600
        self.movement_threshold = movement_threshold
        self.acc_fs = acc_fs
        self.hr_fs = hr_fs
        self.invalid_value = invalid_value
        self.gap_value = gap_value
        self.verbose = verbose
        
        if self.verbose:
            print(f"\nInitializing SyntheticSensorDataGenerator:")
            print(f"Time period: {self.start_timestamp} to {self.end_timestamp}")
            print(f"Duration: {self.duration_hours:.1f} hours")
            print(f"Sampling frequencies: Accelerometer={self.acc_fs}Hz, Heart Rate={self.hr_fs}Hz")
            print(f"Movement threshold: {self.movement_threshold} m/s² ({self.movement_threshold/9.81:.3f} g)")
        
        # Define activity states with their characteristics
        # Note: Accelerometer values are in m/s²
        # All axes (x, y, z) have bell-shaped distributions around 0
        # The total magnitude is specified as the Euclidean norm of the acceleration vector
        # Sedentary: < 0.05g above 1g (total < 1.05g = 10.30 m/s²)
        # Light: 0.05g to 0.1g above 1g (total 1.05g to 1.1g = 10.30 to 10.79 m/s²)
        # Moderate-vigorous: > 0.1g above 1g (total > 1.1g = > 10.79 m/s²)
        self.activity_states = {
            'sedentary': {
                'duration': (30, 10),  # mean ± std in minutes
                'acc_magnitude': (10.15, 0.15),  # mean ± std in m/s² (1.035g ± 0.015g)
                'axis_std': 0.5,       # std of each axis acceleration in m/s²
                'hr_mean': (60, 5),    # mean ± std in BPM
                'hr_std': (3, 1),      # mean ± std in BPM
                'pp_mean': (40, 5),    # mean ± std in mmHg
                'pp_std': (5, 2),      # mean ± std in mmHg
                'day_weight': 0.4,     # probability during day hours
                'night_weight': 0.9    # probability during night hours
            },
            'light_activity': {
                'duration': (15, 5),
                'acc_magnitude': (10.54, 0.25),  # mean ± std in m/s² (1.075g ± 0.025g)
                'axis_std': 1.0,       # std of each axis acceleration in m/s²
                'hr_mean': (90, 10),
                'hr_std': (5, 2),
                'pp_mean': (50, 8),
                'pp_std': (8, 3),
                'day_weight': 0.4,
                'night_weight': 0.1
            },
            'moderate_vigorous_activity': {
                'duration': (30, 10),
                'acc_magnitude': (11.28, 0.49),  # mean ± std in m/s² (1.15g ± 0.05g)
                'axis_std': 2.0,       # std of each axis acceleration in m/s²
                'hr_mean': (135, 20),
                'hr_std': (10, 3),
                'pp_mean': (60, 10),
                'pp_std': (12, 4),
                'day_weight': 0.2,
                'night_weight': 0.0
            }
        }

    def _get_activity_weights(self, hour: int) -> Dict[str, float]:
        """
        Get activity state weights based on time of day.
        
        Args:
            hour: Hour of the day (0-23)
            
        Returns:
            Dictionary mapping activity states to their weights
        """
        is_night = 23 <= hour or hour < 6
        return {
            state: params['night_weight' if is_night else 'day_weight']
            for state, params in self.activity_states.items()
        }

    def generate_activity_sequence(self) -> List[Tuple[str, float]]:
        """
        Generate a sequence of activity states and their durations.
        
        Returns:
            List of tuples (activity_state, duration_minutes)
        """
        current_time = self.start_timestamp
        sequence = []
        
        while current_time < self.end_timestamp:
            hour = current_time.hour
            weights = self._get_activity_weights(hour)
            
            # Select activity state based on weights
            activity = np.random.choice(
                list(weights.keys()),
                p=list(weights.values())
            )
            
            # Generate duration for this activity
            mean_dur, std_dur = self.activity_states[activity]['duration']
            duration = max(1, np.random.normal(mean_dur, std_dur))
            
            # Ensure we don't exceed end time
            if current_time + timedelta(minutes=duration) > self.end_timestamp:
                duration = (self.end_timestamp - current_time).total_seconds() / 60
            
            sequence.append((activity, duration))
            current_time += timedelta(minutes=duration)
        
        return sequence
    
    def generate_sensor_data_without_gaps(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Generate correlated accelerometer and heart rate data without gaps.
        All accelerometer readings are valid, while heart rate readings may have
        invalid values marked with self.invalid_value.
        
        For accelerometer data:
        - All axes (x, y, z) have bell-shaped distributions around 0
        - The standard deviation of each axis increases with activity level
        - The total magnitude is maintained according to activity state
        - No axis has a preferred orientation
        
        Returns:
            Tuple of (accelerometer_df, heartrate_df) where each DataFrame contains:
            - timestamp: Datetime index
            - sensor values: x, y, z for accelerometer (in m/s²); bpm, pp for heart rate
            - Heart rate invalid values marked with self.invalid_value
        """
        start_time = time.time()
        if self.verbose:
            print("\nGenerating synthetic sensor data (without gaps)...")
        
        # Generate activity sequence
        if self.verbose:
            print("Generating activity sequence...")
        activity_sequence = self.generate_activity_sequence()
        if self.verbose:
            print(f"Generated {len(activity_sequence)} activity periods")
        
        # Initialize data storage
        acc_data = []
        hr_data = []
        current_time = self.start_timestamp
        
        # Generate data for each activity period
        if self.verbose:
            print("\nGenerating sensor values for each activity period...")
            activity_iterator = tqdm(activity_sequence, desc="Processing activities")
        else:
            activity_iterator = activity_sequence
            
        for activity, duration in activity_iterator:
            if self.verbose and not isinstance(activity_iterator, tqdm):
                print(f"Processing {activity} period ({duration:.1f} minutes)")
            
            # Generate timestamps for this activity period
            acc_timestamps = self._generate_timestamps(
                current_time,
                duration,
                self.acc_fs
            )
            hr_timestamps = self._generate_timestamps(
                current_time,
                duration,
                self.hr_fs
            )
            
            # Generate sensor values based on activity state
            params = self.activity_states[activity]
            
            # Generate accelerometer data (in m/s²) - all readings are valid
            # First determine the target magnitude for this activity
            target_magnitude = params['acc_magnitude'][0]  # Use mean magnitude
            axis_std = params['axis_std']
            
            # Generate all axes with bell-shaped distributions around 0
            # We need to adjust the standard deviation to achieve the target magnitude
            # For independent normal distributions, the expected magnitude is:
            # E[sqrt(x² + y² + z²)] = sqrt(3) * std * sqrt(2/π)
            # So we need to scale the std to achieve our target magnitude
            scale_factor = target_magnitude / (np.sqrt(3) * np.sqrt(2/np.pi))
            adjusted_std = axis_std * scale_factor
            
            # Generate the components with adjusted standard deviation
            x = np.random.normal(0, adjusted_std, len(acc_timestamps))
            y = np.random.normal(0, adjusted_std, len(acc_timestamps))
            z = np.random.normal(0, adjusted_std, len(acc_timestamps))
            
            # Verify magnitude and distribution are correct (for debugging)
            if self.verbose:
                actual_magnitudes = np.sqrt(x**2 + y**2 + z**2)
                mean_mag = np.mean(actual_magnitudes)
                std_mag = np.std(actual_magnitudes)
                mean_g = mean_mag / 9.81
                std_g = std_mag / 9.81
                mean_above_1g = mean_g - 1.0
                std_above_1g = std_g
                print(f"\nAccelerometer statistics for {activity}:")
                print(f"  Total magnitude:")
                print(f"    Target: {params['acc_magnitude'][0]:.2f} ± {params['acc_magnitude'][1]:.2f} m/s² "
                      f"({params['acc_magnitude'][0]/9.81:.3f} ± {params['acc_magnitude'][1]/9.81:.3f} g, "
                      f"{(params['acc_magnitude'][0]/9.81 - 1.0):.3f} ± {params['acc_magnitude'][1]/9.81:.3f} g above 1g)")
                print(f"    Actual: {mean_mag:.2f} ± {std_mag:.2f} m/s² "
                      f"({mean_g:.3f} ± {std_g:.3f} g, "
                      f"{mean_above_1g:.3f} ± {std_above_1g:.3f} g above 1g)")
                print(f"  Component distributions:")
                print(f"    Base std: {axis_std:.2f} m/s²")
                print(f"    Adjusted std: {adjusted_std:.2f} m/s²")
                for axis, name in [(x, 'x'), (y, 'y'), (z, 'z')]:
                    mean = np.mean(axis)
                    std = np.std(axis)
                    # Test for normality using skewness and kurtosis
                    skew = stats.skew(axis)
                    kurt = stats.kurtosis(axis)
                    print(f"    {name}: mean={mean:.2f} ± {std:.2f} m/s²")
                    print(f"      Skewness: {skew:.2f} (should be close to 0 for normal)")
                    print(f"      Kurtosis: {kurt:.2f} (should be close to 0 for normal)")
                    # Print histogram statistics
                    hist, bins = np.histogram(axis, bins=20, density=True)
                    centers = (bins[:-1] + bins[1:]) / 2
                    print(f"      Most common value: {centers[np.argmax(hist)]:.2f} m/s²")
                    print(f"      % within ±1 std: {np.mean(np.abs(axis) < std)*100:.1f}% (should be ~68%)")
                    print(f"      % within ±2 std: {np.mean(np.abs(axis) < 2*std)*100:.1f}% (should be ~95%)")
            
            # Generate heart rate data with some invalid readings
            hr_invalid_mask = np.random.random(len(hr_timestamps)) < 0.02  # 2% invalid
            hr = np.zeros(len(hr_timestamps))
            pp = np.zeros(len(hr_timestamps))
            
            valid_hr_indices = ~hr_invalid_mask
            if np.any(valid_hr_indices):
                hr[valid_hr_indices] = np.random.normal(
                    params['hr_mean'][0],
                    params['hr_mean'][1],
                    np.sum(valid_hr_indices)
                )
                pp[valid_hr_indices] = np.random.normal(
                    params['pp_mean'][0],
                    params['pp_mean'][1],
                    np.sum(valid_hr_indices)
                )
            
            # Store accelerometer data (all valid)
            for i, dt in enumerate(acc_timestamps):
                acc_data.append({
                    'timestamp': dt,
                    'x': x[i],
                    'y': y[i],
                    'z': z[i]
                })
            
            # Store heart rate data (some invalid)
            for i, dt in enumerate(hr_timestamps):
                if hr_invalid_mask[i]:
                    hr_data.append({
                        'timestamp': dt,
                        'bpm': self.invalid_value,
                        'pp': self.invalid_value
                    })
                else:
                    hr_data.append({
                        'timestamp': dt,
                        'bpm': hr[i],
                        'pp': pp[i]
                    })
            
            # Update current time for next activity
            current_time = acc_timestamps[-1] + timedelta(seconds=1/self.acc_fs)
        
        # Convert to DataFrames
        if self.verbose:
            print("\nConverting data to DataFrames...")
        acc_df = pd.DataFrame(acc_data)
        hr_df = pd.DataFrame(hr_data)
        
        if self.verbose:
            print(f"Generated {len(acc_df):,} accelerometer samples")
            print(f"Generated {len(hr_df):,} heart rate samples")
            elapsed_time = time.time() - start_time
            print(f"\nData generation completed in {elapsed_time:.1f} seconds")
            print("\nData statistics:")
            print(f"Accelerometer data shape: {acc_df.shape}")
            print(f"Heart rate data shape: {hr_df.shape}")
            
            # Print statistics about invalid heart rate readings
            hr_invalid = (hr_df['bpm'] == self.invalid_value).sum()
            print(f"\nInvalid heart rate readings:")
            print(f"Heart rate: {hr_invalid:,} out of {len(hr_df):,} ({hr_invalid/len(hr_df)*100:.1f}%)")
        
        return acc_df, hr_df

    def generate_sensor_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Generate correlated accelerometer and heart rate data with gaps.
        
        Returns:
            Tuple of (accelerometer_df, heartrate_df) where each DataFrame contains:
            - timestamp: Datetime index
            - sensor values: x, y, z for accelerometer (in m/s²); bpm, pp for heart rate
            - invalid values marked with self.invalid_value
            - Gaps are represented by missing data points
        """
        # First generate data without gaps
        acc_df, hr_df = self.generate_sensor_data_without_gaps()
        
        # Then add gaps
        if self.verbose:
            print("\nAdding correlated gaps to the data...")
        acc_df, hr_df = self._add_correlated_gaps(acc_df, hr_df)
        
        if self.verbose:
            # Calculate and print gap statistics
            acc_gaps = self._calculate_gap_statistics(acc_df)
            hr_gaps = self._calculate_gap_statistics(hr_df)
            
            print("\nGap Statistics:")
            print("Accelerometer:")
            print(f"  Number of gaps: {acc_gaps['num_gaps']}")
            print(f"  Mean gap duration: {acc_gaps['mean_gap_duration']:.1f} seconds")
            print(f"  Max gap duration: {acc_gaps['max_gap_duration']:.1f} seconds")
            print("Heart Rate:")
            print(f"  Number of gaps: {hr_gaps['num_gaps']}")
            print(f"  Mean gap duration: {hr_gaps['mean_gap_duration']:.1f} seconds")
            print(f"  Max gap duration: {hr_gaps['max_gap_duration']:.1f} seconds")
        
        return acc_df, hr_df

    def _add_correlated_gaps(self, acc_df: pd.DataFrame, hr_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Add correlated gaps to both accelerometer and heart rate data.
        Gaps are more likely during sedentary periods and are synchronized between sensors.
        Invalid heart rate readings are considered when determining suitable gap positions.
        
        Parameters:
            acc_df: DataFrame with accelerometer data (all valid)
            hr_df: DataFrame with heart rate data (some invalid)
            
        Returns:
            Tuple of (accelerometer_df, heartrate_df) with gaps represented by missing data points
        """
        if self.verbose:
            print("Generating correlated gaps...")
        
        # Sort both DataFrames by timestamp
        acc_df = acc_df.sort_values('timestamp')
        hr_df = hr_df.sort_values('timestamp')
        
        # Get activity sequence for the time period
        activity_sequence = self.generate_activity_sequence()
        
        # Calculate target number of gaps
        target_gaps = 120
        
        if self.verbose:
            print(f"Target number of gaps: {target_gaps}")
        
        # Generate gap durations with realistic distribution
        gap_durations = np.random.gamma(shape=2, scale=200, size=target_gaps * 2)
        
        # Create a list of potential gap positions with their activity states
        if self.verbose:
            print("Identifying potential gap positions...")
        potential_gaps = []
        current_time = self.start_timestamp
        
        # First, create a list of all timestamps with their activity states
        # Use accelerometer timestamps as base since it has higher sampling rate
        for activity, duration_minutes in activity_sequence:
            duration = timedelta(minutes=float(duration_minutes))
            end_time = current_time + duration
            
            # Get timestamps for this activity period
            mask = (acc_df['timestamp'] >= current_time) & (acc_df['timestamp'] < end_time)
            timestamps = acc_df.loc[mask, 'timestamp'].values
            
            if len(timestamps) > 0:
                # Calculate activity-based gap probabilities based on magnitude above 1g
                if activity == 'sedentary':
                    gap_prob = 0.8  # High probability during sedentary (< 0.05g above 1g)
                elif activity == 'light_activity':
                    gap_prob = 0.4  # Medium probability during light (0.05g to 0.1g above 1g)
                else:  # moderate_vigorous_activity
                    gap_prob = 0.1  # Low probability during moderate-vigorous (> 0.1g above 1g)
                
                for ts in timestamps:
                    potential_gaps.append((ts, gap_prob, activity))
            
            current_time = end_time
        
        # Sort potential gaps by timestamp
        potential_gaps.sort(key=lambda x: x[0])
        
        if self.verbose:
            print(f"Found {len(potential_gaps):,} potential gap positions")
            print("Inserting correlated gaps...")
        
        # Track number of gaps actually inserted
        gaps_inserted = 0
        max_attempts = target_gaps * 3
        attempts = 0
        
        # Use tqdm for progress bar if verbose
        iterator = tqdm(range(max_attempts), desc="Inserting gaps") if self.verbose else range(max_attempts)
        
        for _ in iterator:
            if gaps_inserted >= target_gaps:
                break
                
            attempts += 1
            duration_seconds = gap_durations[gaps_inserted]
            gap_duration = timedelta(seconds=float(duration_seconds))
            
            # Find a suitable position for the gap
            suitable_positions = []
            search_window = min(1000, len(potential_gaps))
            
            for i, (ts, prob, activity) in enumerate(potential_gaps[:search_window]):
                next_idx = i + 1
                while (next_idx < len(potential_gaps) and 
                       potential_gaps[next_idx][2] == activity and
                       next_idx - i < search_window):
                    next_ts = potential_gaps[next_idx][0]
                    time_diff = next_ts - ts
                    if isinstance(time_diff, timedelta) and time_diff >= gap_duration:
                        suitable_positions.append((i, prob))
                        break
                    next_idx += 1
            
            if suitable_positions:
                positions, probs = zip(*suitable_positions)
                probs = np.array(probs) / sum(probs)
                pos_idx = np.random.choice(len(positions), p=probs)
                start_idx = positions[pos_idx]
                
                start_ts = potential_gaps[start_idx][0]
                end_ts = start_ts + gap_duration
                
                # Remove data points from both sensors during the gap
                acc_mask = (acc_df['timestamp'] >= start_ts) & (acc_df['timestamp'] < end_ts)
                hr_mask = (hr_df['timestamp'] >= start_ts) & (hr_df['timestamp'] < end_ts)
                
                acc_df = acc_df[~acc_mask]
                hr_df = hr_df[~hr_mask]
                
                # Remove the used positions from potential gaps
                last_gap_idx = start_idx
                while (last_gap_idx + 1 < len(potential_gaps) and 
                       potential_gaps[last_gap_idx + 1][0] < end_ts):
                    last_gap_idx += 1
                
                potential_gaps = potential_gaps[:start_idx] + potential_gaps[last_gap_idx + 1:]
                gaps_inserted += 1
                
                if self.verbose:
                    print(f"Successfully inserted gap {gaps_inserted} of {target_gaps} (duration: {duration_seconds:.1f} seconds)")
                
                if isinstance(iterator, tqdm):
                    iterator.set_postfix(gaps_inserted=gaps_inserted)
        
        if self.verbose:
            if gaps_inserted < target_gaps:
                print(f"\nWarning: Could only insert {gaps_inserted} out of {target_gaps} target gaps "
                      f"after {attempts} attempts")
            else:
                print(f"\nSuccessfully inserted {gaps_inserted} correlated gaps")
        
        return acc_df, hr_df

    def _calculate_gap_statistics(self, df: pd.DataFrame) -> Dict:
        """Calculate statistics about gaps in the data."""
        # Sort by timestamp
        df = df.sort_values('timestamp')
        
        # Calculate time differences between consecutive timestamps
        time_diffs = df['timestamp'].diff()
        
        # Find gaps (periods where time difference > 60 seconds)
        gap_durations = time_diffs[time_diffs > timedelta(seconds=60)].dt.total_seconds().tolist()
        
        return {
            'num_gaps': len(gap_durations),
            'mean_gap_duration': np.mean(gap_durations) if gap_durations else 0,
            'max_gap_duration': max(gap_durations) if gap_durations else 0
        }

    def _generate_timestamps(self, start_time: datetime, duration: float, fs: float) -> np.ndarray:
        """
        Generate timestamps with realistic jitter.
        
        Parameters:
            start_time: Start datetime
            duration: Duration in minutes
            fs: Sampling frequency in Hz
            
        Returns:
            Array of timestamps as datetime objects
        """
        # Convert duration from minutes to seconds
        duration_seconds = duration * 60
        n_samples = int(duration_seconds * fs)
        base_intervals = np.ones(n_samples) / fs
        
        # Add jitter to intervals
        jitter = np.random.normal(0, 0.1/fs, n_samples)  # 10% jitter
        intervals = base_intervals + jitter
        
        # Convert intervals to timedelta objects and generate timestamps
        timestamps = [start_time]
        for interval in intervals:
            timestamps.append(timestamps[-1] + timedelta(seconds=interval))
        
        return np.array(timestamps[:-1])  # Remove the last timestamp as it might exceed duration 