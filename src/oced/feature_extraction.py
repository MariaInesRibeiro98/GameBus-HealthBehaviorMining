import numpy as np
import pandas as pd

class FeatureExtractor:
    """
    A class for extracting features from accelerometer data.
    
    This class provides methods to calculate various features from
    triaxial accelerometer data, such as ENMO (Euclidean Norm Minus One).
    """
    
    def __init__(self, df):
        """
        Initialize the FeatureExtractor with a DataFrame.

        Parameters:
            df (pd.DataFrame): Input DataFrame containing accelerometer data
        """
        self.df = df.copy()  # Create a copy to avoid modifying original data
        self.features = {}   # Dictionary to store calculated features

    def calculate_enmo(self, axis_cols=('x', 'y', 'z'), output_col='enmo'):
        """
        Calculate ENMO (Euclidean Norm Minus One) feature.
        ENMO = max(0, sqrt(x² + y² + z²) - 1)
        This represents the deviation from 1g, with negative values set to 0.
        Returns -9999 if any axis has an invalid value (-9999).

        Parameters:
            axis_cols (tuple): Names of the accelerometer columns (x, y, z)
            output_col (str): Name of the column to store the ENMO values

        Returns:
            pd.Series: The calculated ENMO values, with -9999 for invalid data points

        Raises:
            ValueError: If any of the specified columns are not in the DataFrame
        """
        # Verify all columns exist
        missing_cols = [col for col in axis_cols if col not in self.df.columns]
        if missing_cols:
            raise ValueError(f"Columns not found in DataFrame: {missing_cols}")

        # Create a mask for invalid data points (any axis has -9999)
        invalid_mask = (self.df[list(axis_cols)] == -9999).any(axis=1)
        
        # Initialize ENMO array with -9999
        enmo = pd.Series(-9999, index=self.df.index)
        
        # Calculate ENMO only for valid data points
        valid_mask = ~invalid_mask
        if valid_mask.any():
            # Calculate vector magnitude for valid points
            squared_sum = sum(self.df.loc[valid_mask, col]**2 for col in axis_cols)
            magnitude = np.sqrt(squared_sum)
            
            # Calculate ENMO for valid points
            enmo.loc[valid_mask] = np.maximum(0, magnitude - 1)
        
        # Store the feature
        self.df[output_col] = enmo
        self.features[output_col] = enmo
        
        return enmo

    def calculate_vector_magnitude(self, axis_cols=('x', 'y', 'z'), output_col='vm'):
        """
        Calculate Vector Magnitude (VM) feature.
        VM = sqrt(x² + y² + z²)
        Returns -9999 if any axis has an invalid value (-9999).

        Parameters:
            axis_cols (tuple): Names of the accelerometer columns (x, y, z)
            output_col (str): Name of the column to store the VM values

        Returns:
            pd.Series: The calculated VM values, with -9999 for invalid data points

        Raises:
            ValueError: If any of the specified columns are not in the DataFrame
        """
        # Verify all columns exist
        missing_cols = [col for col in axis_cols if col not in self.df.columns]
        if missing_cols:
            raise ValueError(f"Columns not found in DataFrame: {missing_cols}")

        # Create a mask for invalid data points (any axis has -9999)
        invalid_mask = (self.df[list(axis_cols)] == -9999).any(axis=1)
        
        # Initialize VM array with -9999
        vm = pd.Series(-9999, index=self.df.index)
        
        # Calculate VM only for valid data points
        valid_mask = ~invalid_mask
        if valid_mask.any():
            # Calculate vector magnitude for valid points
            squared_sum = sum(self.df.loc[valid_mask, col]**2 for col in axis_cols)
            vm.loc[valid_mask] = np.sqrt(squared_sum)
        
        # Store the feature
        self.df[output_col] = vm
        self.features[output_col] = vm
        
        return vm

    def calculate_vertical_angle(self, axis_cols=('x', 'y', 'z'), vm_col='vm', output_col='vertical_angle'):
        """
        Calculate the angle of acceleration relative to vertical.
        The angle is calculated as: 90 * arcsin(x / vector_magnitude) / (pi/2)
        This gives an angle in degrees where:
        - 0° means the device is vertical (x-axis pointing up)
        - 90° means the device is horizontal (x-axis pointing sideways)
        Returns -9999 if any axis has an invalid value (-9999).

        Parameters:
            axis_cols (tuple): Names of the accelerometer columns (x, y, z)
            vm_col (str): Name of the vector magnitude column (must be calculated first)
            output_col (str): Name of the column to store the angle values

        Returns:
            pd.Series: The calculated angles in degrees, with -9999 for invalid data points

        Raises:
            ValueError: If any of the specified columns are not in the DataFrame
            KeyError: If vector magnitude hasn't been calculated yet
        """
        # Verify all columns exist
        missing_cols = [col for col in axis_cols if col not in self.df.columns]
        if missing_cols:
            raise ValueError(f"Columns not found in DataFrame: {missing_cols}")
        
        if vm_col not in self.df.columns:
            raise KeyError(f"Vector magnitude column '{vm_col}' not found. Calculate vector magnitude first.")

        # Create a mask for invalid data points (any axis has -9999 or VM is -9999)
        invalid_mask = ((self.df[list(axis_cols)] == -9999).any(axis=1) | 
                       (self.df[vm_col] == -9999))
        
        # Initialize angle array with -9999
        angle = pd.Series(-9999, index=self.df.index)
        
        # Calculate angle only for valid data points
        valid_mask = ~invalid_mask
        if valid_mask.any():
            # Get x-axis values and vector magnitude for valid points
            x_values = self.df.loc[valid_mask, axis_cols[0]]
            vm_values = self.df.loc[valid_mask, vm_col]
            
            # Calculate angle using arcsin(x/VM)
            # We clip the ratio to [-1, 1] to avoid numerical errors
            ratio = np.clip(x_values / vm_values, -1, 1)
            angle_rad = np.arcsin(ratio)
            
            # Convert to degrees and scale to 0-90 range
            angle.loc[valid_mask] = 90 * angle_rad / (np.pi/2)
        
        # Store the feature
        self.df[output_col] = angle
        self.features[output_col] = angle
        
        return angle

    def calculate_windowed_statistics(self, window_seconds, target_col='vm', hr_col='hr', 
                                    min_valid_hr=40, invalid_value=-9999, 
                                    min_valid_percent=50, stats=None):
        """
        Calculate statistics for a target column in non-overlapping time windows,
        using a percentage-based approach to handle invalid values.
        
        For each window:
        1. Check if percentage of valid samples meets threshold
        2. If threshold met, calculate statistics only on valid values
        3. If threshold not met, mark window as invalid
        
        Parameters:
            window_seconds (int): Window size in seconds
            target_col (str): Name of the column to calculate statistics for (e.g., 'vm', 'enmo', etc.)
            hr_col (str): Name of the heart rate column
            min_valid_hr (float): Minimum valid heart rate (values below this are considered invalid)
            invalid_value (float): Value used to mark invalid data
            min_valid_percent (float): Minimum percentage of valid samples required in a window (0-100)
            stats (list): List of statistics to calculate. If None, calculates all available.
                         Options: ['mean', 'std', 'min', 'max', 'median', 'skew', 'kurt']
        
        Returns:
            pd.DataFrame: DataFrame with statistics for each window, with invalid_value for invalid windows
        """
        # Default statistics if none specified
        if stats is None:
            stats = ['mean', 'std', 'min', 'max', 'median']
        
        # Verify requested statistics are valid
        valid_stats = ['mean', 'std', 'min', 'max', 'median', 'skew', 'kurt']
        invalid_stats = [s for s in stats if s not in valid_stats]
        if invalid_stats:
            raise ValueError(f"Invalid statistics requested: {invalid_stats}")
        
        # Verify target column exists
        if target_col not in self.df.columns:
            raise ValueError(f"Target column '{target_col}' not found in DataFrame")
        
        # Calculate window size in samples
        window_size = int(window_seconds * 25)  # sampling rate is 25 Hz
        
        # Create mask for valid samples
        valid_target_mask = (self.df[target_col] != invalid_value)
        valid_hr_mask = (self.df[hr_col] >= min_valid_hr)
        valid_mask = valid_target_mask & valid_hr_mask
        
        # Initialize results dictionary
        results = {}
        window_metadata = {
            'valid_samples_percent': [],
            'valid_samples_count': [],
            'total_samples': [],
            'window_start': [],
            'window_end': []
        }
        
        # Process each window
        for i in range(0, len(self.df), window_size):
            window_end = min(i + window_size, len(self.df))
            window_slice = slice(i, window_end)
            window_mask = valid_mask.iloc[window_slice]
            
            # Calculate percentage of valid samples
            valid_count = window_mask.sum()
            total_count = len(window_mask)
            valid_percent = (valid_count / total_count) * 100
            
            # Store metadata
            window_metadata['valid_samples_percent'].append(valid_percent)
            window_metadata['valid_samples_count'].append(valid_count)
            window_metadata['total_samples'].append(total_count)
            window_metadata['window_start'].append(self.df.index[i])
            window_metadata['window_end'].append(self.df.index[window_end - 1])
            
            # Check if window meets minimum valid percentage threshold
            if valid_percent >= min_valid_percent:
                # Get valid values for this window
                valid_values = self.df.loc[window_mask.index[window_mask], target_col]
                
                # Calculate statistics only on valid values
                for stat in stats:
                    if stat == 'mean':
                        results.setdefault(f'{target_col}_mean', []).append(valid_values.mean())
                    elif stat == 'std':
                        results.setdefault(f'{target_col}_std', []).append(valid_values.std())
                    elif stat == 'min':
                        results.setdefault(f'{target_col}_min', []).append(valid_values.min())
                    elif stat == 'max':
                        results.setdefault(f'{target_col}_max', []).append(valid_values.max())
                    elif stat == 'median':
                        results.setdefault(f'{target_col}_median', []).append(valid_values.median())
                    elif stat == 'skew':
                        results.setdefault(f'{target_col}_skew', []).append(valid_values.skew())
                    elif stat == 'kurt':
                        results.setdefault(f'{target_col}_kurt', []).append(valid_values.kurt())
            else:
                # Not enough valid samples, mark all statistics as invalid
                for stat in stats:
                    results.setdefault(f'{target_col}_{stat}', []).append(invalid_value)
        
        # Convert to DataFrame
        results_df = pd.DataFrame(results)
        
        # Add metadata columns
        for key, values in window_metadata.items():
            results_df[key] = values
        
        return results_df

    def get_valid_epochs(self, window_seconds, target_col='vm', hr_col='hr',
                        min_valid_hr=40, invalid_value=-9999, min_valid_percent=50):
        """
        Get a DataFrame containing only the valid epochs based on validation criteria.
        An epoch is considered valid if it meets the minimum percentage of valid samples
        and contains valid heart rate values.
        
        Parameters:
            window_seconds (int): Window size in seconds
            target_col (str): Name of the column to validate (e.g., 'vm', 'enmo', etc.)
            hr_col (str): Name of the heart rate column
            min_valid_hr (float): Minimum valid heart rate (values below this are considered invalid)
            invalid_value (float): Value used to mark invalid data
            min_valid_percent (float): Minimum percentage of valid samples required in a window (0-100)
        
        Returns:
            pd.DataFrame: DataFrame containing only the valid epochs with their metadata
        """
        # Verify target column exists
        if target_col not in self.df.columns:
            raise ValueError(f"Target column '{target_col}' not found in DataFrame")
        
        # Calculate window size in samples
        window_size = int(window_seconds * 25)  # sampling rate is 25 Hz
        
        # Create mask for valid samples
        valid_target_mask = (self.df[target_col] != invalid_value)
        valid_hr_mask = (self.df[hr_col] >= min_valid_hr)
        valid_mask = valid_target_mask & valid_hr_mask
        
        # Initialize lists to store valid epoch data
        valid_epochs = []
        
        # Process each window
        for i in range(0, len(self.df), window_size):
            window_end = min(i + window_size, len(self.df))
            window_slice = slice(i, window_end)
            window_mask = valid_mask.iloc[window_slice]
            
            # Calculate percentage of valid samples
            valid_count = window_mask.sum()
            total_count = len(window_mask)
            valid_percent = (valid_count / total_count) * 100
            
            # Check if window meets minimum valid percentage threshold
            if valid_percent >= min_valid_percent:
                # Get the data for this valid window
                window_data = self.df.iloc[window_slice].copy()
                
                # Add metadata columns
                window_data['epoch_valid_percent'] = valid_percent
                window_data['epoch_valid_count'] = valid_count
                window_data['epoch_total_count'] = total_count
                window_data['epoch_start'] = self.df.index[i]
                window_data['epoch_end'] = self.df.index[window_end - 1]
                
                valid_epochs.append(window_data)
        
        # Combine all valid epochs into a single DataFrame
        if valid_epochs:
            valid_df = pd.concat(valid_epochs, axis=0)
            # Sort by index to maintain chronological order
            valid_df = valid_df.sort_index()
            return valid_df
        else:
            # Return empty DataFrame with same columns if no valid epochs found
            return pd.DataFrame(columns=self.df.columns.tolist() + 
                              ['epoch_valid_percent', 'epoch_valid_count', 
                               'epoch_total_count', 'epoch_start', 'epoch_end'])

    def get_data_with_features(self):
        """
        Get a copy of the original DataFrame with all calculated features added as new columns.
        This includes the original accelerometer data plus any features calculated using
        calculate_enmo(), calculate_vector_magnitude(), and calculate_vertical_angle().

        Returns:
            pd.DataFrame: A copy of the original DataFrame with all calculated features
        """
        return self.df.copy()


