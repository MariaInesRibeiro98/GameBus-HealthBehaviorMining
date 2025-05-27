import pandas as pd
import numpy as np
from typing import Optional, Union, List
from dataclasses import dataclass


@dataclass
class SmoothingConfig:
    """Configuration for the smoothing classifier."""
    window_size: int  # Size of the window in number of epochs (must be odd number)
    invalid_threshold: float  # Maximum allowed percentage of INVALID values in window (0 to 1)
    invalid_class: str = "INVALID"  # Label used for invalid classifications


class SmoothingClassifier:
    """
    A classifier that applies smoothing to physical activity classifications using a centered window approach.
    
    This class implements a smoothing technique that:
    1. For each epoch, uses a centered window of surrounding epochs
    2. Allows for a certain percentage of INVALID values in the window
    3. Assigns the most frequent valid class to the current epoch
    """
    
    def __init__(self, config: SmoothingConfig):
        """
        Initialize the smoothing classifier.
        
        Args:
            config (SmoothingConfig): Configuration parameters for the smoothing
        """
        self.config = config
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate the configuration parameters."""
        if not 0 <= self.config.invalid_threshold <= 1:
            raise ValueError("Invalid threshold must be between 0 and 1")
        if self.config.window_size < 3:
            raise ValueError("Window size must be at least 3")
        if self.config.window_size % 2 == 0:
            raise ValueError("Window size must be an odd number to ensure centered windows")
    
    def smooth(self, df: pd.DataFrame, class_column: str, 
              start_time_column: str, end_time_column: str) -> pd.DataFrame:
        """
        Apply smoothing to the classification results.
        
        Args:
            df (pd.DataFrame): Input dataframe containing classifications
            class_column (str): Name of the column containing class labels
            start_time_column (str): Name of the column containing start times
            end_time_column (str): Name of the column containing end times
            
        Returns:
            pd.DataFrame: DataFrame with smoothed classifications
        """
        # Create a copy to avoid modifying the original
        result_df = df.copy()
        
        # Calculate half window size (number of epochs on each side)
        half_window = self.config.window_size // 2
        
        # Initialize the smoothed column
        result_df['smoothed_class'] = result_df[class_column]
        
        # Apply centered window for each epoch
        for i in range(len(df)):
            # Calculate window boundaries
            start_idx = max(0, i - half_window)
            end_idx = min(len(df), i + half_window + 1)
            
            # Get the window
            window = df.iloc[start_idx:end_idx]
            
            # Count invalid values in window
            invalid_count = (window[class_column] == self.config.invalid_class).sum()
            invalid_ratio = invalid_count / len(window)
            
            # Skip if too many invalid values
            if invalid_ratio > self.config.invalid_threshold:
                continue
            
            # Get valid classifications
            valid_classes = window[window[class_column] != self.config.invalid_class][class_column]
            
            if len(valid_classes) > 0:
                # Get most frequent class
                most_frequent = valid_classes.mode().iloc[0]
                # Assign to current epoch
                result_df.iloc[i, result_df.columns.get_loc('smoothed_class')] = most_frequent
        
        return result_df 