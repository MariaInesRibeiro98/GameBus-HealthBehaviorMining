import pandas as pd
import numpy as np
from typing import Optional, Union, List, Dict
from dataclasses import dataclass


@dataclass
class BoutConfig:
    """Configuration for bout detection."""
    min_duration: pd.Timedelta  # Minimum duration for a bout
    target_class: str  # The activity class to detect bouts for
    max_invalid_percentage: float = 0.3  # Maximum allowed percentage of invalid values in bout (0 to 1)
    min_valid_target_percentage: float = 0.8  # Minimum percentage of target activity within valid epochs (0 to 1)
    invalid_class: str = "INVALID"  # Label used for invalid classifications


class BoutDetector:
    """
    Detects bouts of specific activity classes from smoothed classification data.
    
    A bout is defined as a period of time where:
    1. The duration is at least min_duration
    2. The percentage of invalid values is at most max_invalid_percentage
    3. Within the valid (non-invalid) epochs, the percentage of target activity 
       is at least min_valid_target_percentage
    """
    
    def __init__(self, config: BoutConfig):
        """
        Initialize the bout detector.
        
        Args:
            config (BoutConfig): Configuration parameters for bout detection
        """
        self.config = config
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate the configuration parameters."""
        if not 0 <= self.config.max_invalid_percentage <= 1:
            raise ValueError("max_invalid_percentage must be between 0 and 1")
        if not 0 <= self.config.min_valid_target_percentage <= 1:
            raise ValueError("min_valid_target_percentage must be between 0 and 1")
    
    def _is_valid_bout(self, bout_stats: Dict[str, int]) -> bool:
        """
        Check if a potential bout meets all criteria.
        
        Args:
            bout_stats: Dictionary containing bout statistics
            
        Returns:
            bool: True if bout meets all criteria
        """
        total_epochs = bout_stats['valid_count'] + bout_stats['invalid_count']
        if total_epochs == 0:
            return False
            
        invalid_percentage = bout_stats['invalid_count'] / total_epochs
        valid_target_percentage = bout_stats['target_count'] / bout_stats['valid_count'] if bout_stats['valid_count'] > 0 else 0
        
        return (invalid_percentage <= self.config.max_invalid_percentage and 
                valid_target_percentage >= self.config.min_valid_target_percentage)
    
    def _get_bout_stats(self, df: pd.DataFrame, start_idx: int, end_idx: int, 
                       class_column: str) -> Dict[str, int]:
        """
        Calculate statistics for a potential bout.
        
        Args:
            df: Input dataframe
            start_idx: Start index of the bout
            end_idx: End index of the bout (inclusive)
            class_column: Name of the column containing class labels
            
        Returns:
            Dictionary containing bout statistics
        """
        bout_df = df.iloc[start_idx:end_idx + 1]
        target_count = (bout_df[class_column] == self.config.target_class).sum()
        invalid_count = (bout_df[class_column] == self.config.invalid_class).sum()
        valid_count = len(bout_df) - invalid_count
        
        return {
            'target_count': target_count,
            'invalid_count': invalid_count,
            'valid_count': valid_count
        }
    
    def detect_bouts(self, df: pd.DataFrame, 
                    class_column: str,
                    start_time_column: str,
                    end_time_column: str) -> pd.DataFrame:
        """
        Detect bouts of the target activity class.
        
        Args:
            df (pd.DataFrame): DataFrame containing smoothed classifications
            class_column (str): Name of the column containing class labels
            start_time_column (str): Name of the column containing start times
            end_time_column (str): Name of the column containing end times
            
        Returns:
            pd.DataFrame with bout information including:
            - bout_id: Unique identifier for each bout
            - start_time: Start time of the bout
            - end_time: End time of the bout
            - duration: Duration of the bout
            - invalid_percentage: Percentage of invalid values in the bout
            - valid_target_percentage: Percentage of target activity within valid epochs
        """
        # Convert time columns to datetime if they aren't already
        df[start_time_column] = pd.to_datetime(df[start_time_column])
        df[end_time_column] = pd.to_datetime(df[end_time_column])
        
        bouts = []
        i = 0
        
        while i < len(df):
            # Skip invalid epochs at the start
            while i < len(df) and df.iloc[i][class_column] == self.config.invalid_class:
                i += 1
            
            if i >= len(df):
                break
                
            # Try to find a valid bout starting from this position
            start_idx = i
            current_stats = self._get_bout_stats(df, start_idx, i, class_column)
            
            # Expand the bout until it becomes invalid or we reach the end
            while i < len(df):
                # Check if adding the next epoch would make the bout invalid
                next_stats = self._get_bout_stats(df, start_idx, i + 1, class_column)
                if not self._is_valid_bout(next_stats):
                    break
                current_stats = next_stats
                i += 1
            
            # If we found a valid bout, add it to the list
            if self._is_valid_bout(current_stats):
                bout_duration = df.iloc[i-1][end_time_column] - df.iloc[start_idx][start_time_column]
                if bout_duration >= self.config.min_duration:
                    total_epochs = current_stats['valid_count'] + current_stats['invalid_count']
                    invalid_percentage = current_stats['invalid_count'] / total_epochs
                    valid_target_percentage = current_stats['target_count'] / current_stats['valid_count']
                    
                    bouts.append({
                        'start_time': df.iloc[start_idx][start_time_column],
                        'end_time': df.iloc[i-1][end_time_column],
                        'invalid_percentage': invalid_percentage,
                        'valid_target_percentage': valid_target_percentage
                    })
            
            # Move to the next position
            i += 1
        
        # Create bout DataFrame
        if bouts:
            bout_df = pd.DataFrame(bouts)
            # Calculate durations
            bout_df['duration'] = bout_df['end_time'] - bout_df['start_time']
            # Reset index to create bout_id
            bout_df = bout_df.reset_index(drop=True)
            bout_df.index.name = 'bout_id'
            bout_df = bout_df.reset_index()
            return bout_df
        else:
            return pd.DataFrame(columns=['bout_id', 'start_time', 'end_time', 'duration', 
                                       'invalid_percentage', 'valid_target_percentage']) 