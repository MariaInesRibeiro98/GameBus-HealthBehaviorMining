import pandas as pd
import numpy as np
from typing import Optional, Union, List
from datetime import timedelta
import matplotlib.pyplot as plt

class BoutDetector:
    """
    A simple class for detecting sustained bouts of physical activity.
    
    This class implements a straightforward approach to detect bouts:
    1. Find consecutive periods of target activity
    2. Apply minimum duration and recovery time rules
    3. Mark valid bouts in the data
    """
    
    def __init__(
        self,
        min_bout_duration: Union[str, timedelta] = '5min',
        activity_threshold: float = 0.8,
        recovery_time: Optional[Union[str, timedelta]] = '1min',
        epoch_duration: Union[str, timedelta] = '1min'
    ):
        """
        Initialize the BoutDetector with basic parameters.
        
        Args:
            min_bout_duration: Minimum duration for a valid bout (e.g., '5min')
            activity_threshold: Minimum percentage (0-1) of epochs that must be of the
                              target activity level within a bout (e.g., 0.8 means 80%
                              of epochs must be target activity)
            recovery_time: Maximum allowed break time within a bout (e.g., '1min')
            epoch_duration: Duration of each epoch in the input data
        """
        self.min_bout_duration = pd.Timedelta(min_bout_duration)
        self.activity_threshold = activity_threshold
        self.recovery_time = pd.Timedelta(recovery_time) if recovery_time else None
        self.epoch_duration = pd.Timedelta(epoch_duration)
        
        # Validate parameters
        if not 0 < activity_threshold <= 1:
            raise ValueError("activity_threshold must be between 0 and 1")
        if self.min_bout_duration < self.epoch_duration:
            raise ValueError("min_bout_duration must be greater than or equal to epoch_duration")
        if self.recovery_time and self.recovery_time >= self.min_bout_duration:
            raise ValueError("recovery_time must be less than min_bout_duration")
    
    def _calculate_centered_window_percentage(
        self,
        df: pd.DataFrame,
        time_column: str,
        activity_column: str,
        target_activity: List[str],
        window_duration: timedelta
    ) -> pd.Series:
        """
        Calculate the percentage of target activity in a window centered on each epoch.
        
        Args:
            df: DataFrame containing activity data
            time_column: Name of the column containing timestamps
            activity_column: Name of the column containing activity levels
            target_activity: List of target activity levels
            window_duration: Duration of the centered window
            
        Returns:
            Series containing the percentage of target activity for each epoch
        """
        half_window = window_duration / 2
        percentages = []
        
        for _, row in df.iterrows():
            center_time = row[time_column]
            window_start = center_time - half_window
            window_end = center_time + half_window
            
            # Get epochs within the window
            window_mask = (df[time_column] >= window_start) & (df[time_column] < window_end)
            window_data = df[window_mask]
            
            # Calculate percentage of target activity
            if len(window_data) > 0:
                percentage = window_data[activity_column].isin(target_activity).mean()
            else:
                percentage = 0.0
                
            percentages.append(percentage)
            
        return pd.Series(percentages, index=df.index)

    def detect_bouts(
        self,
        df: pd.DataFrame,
        time_column: str = 'window_start',
        activity_column: str = 'activity_level_sdvm_mangle',
        target_activity: Union[str, List[str]] = 'MODERATE-VIGOROUS_PA'
    ) -> pd.DataFrame:
        """
        Detect bouts of physical activity in the input DataFrame.
        
        Args:
            df: DataFrame containing activity classifications and timestamps
            time_column: Name of the column containing window start times
            activity_column: Name of the column containing activity levels
            target_activity: Activity level(s) to consider for bout detection
            
        Returns:
            DataFrame with added columns:
            - 'is_bout': Boolean indicating if the window is part of a bout
            - 'bout_id': Unique identifier for each bout
            - 'bout_duration': Duration of the bout
            - 'bout_activity_percentage': Percentage of target activity in the bout
            - 'centered_window_percentage': Percentage of target activity in a window
                                         centered on each epoch
        """
        if not isinstance(target_activity, list):
            target_activity = [target_activity]
            
        # Sort by time to ensure proper ordering
        df = df.sort_values(time_column).copy()
        
        # Initialize bout columns
        df['is_bout'] = False
        df['bout_id'] = -1
        df['bout_duration'] = pd.Timedelta(0)
        df['bout_activity_percentage'] = 0.0
        
        # Calculate centered window percentages
        df['centered_window_percentage'] = self._calculate_centered_window_percentage(
            df,
            time_column,
            activity_column,
            target_activity,
            self.min_bout_duration
        )
        
        # Calculate window end times if not present
        if 'window_end' not in df.columns:
            df['window_end'] = df[time_column] + self.epoch_duration
        
        # Find consecutive periods of target activity
        is_target = df[activity_column].isin(target_activity)
        target_changes = is_target.astype(int).diff()
        
        # Get start and end indices of target activity periods
        bout_starts = df.index[target_changes == 1].tolist()
        bout_ends = df.index[target_changes == -1].tolist()
        
        # Handle edge cases
        if is_target.iloc[0]:
            bout_starts.insert(0, df.index[0])
        if is_target.iloc[-1]:
            bout_ends.append(df.index[-1])
        
        # Process each potential bout
        bout_id = 0
        current_bout_start = None
        last_activity_end = None
        
        for start_idx, end_idx in zip(bout_starts, bout_ends):
            start_time = df.loc[start_idx, time_column]
            end_time = df.loc[end_idx, 'window_end']
            duration = end_time - start_time
            
            # Get all epochs in this period
            period_mask = (df[time_column] >= start_time) & (df[time_column] < end_time)
            period_data = df[period_mask]
            
            # Calculate percentage of target activity
            target_percentage = period_data[activity_column].isin(target_activity).mean()
            
            # Check if this period meets minimum duration and activity threshold
            if duration >= self.min_bout_duration and target_percentage >= self.activity_threshold:
                # If we have a current bout, check if this period can be merged
                if current_bout_start is not None and self.recovery_time is not None:
                    gap = start_time - last_activity_end
                    if gap <= self.recovery_time:
                        # Get all epochs from current bout start to this period end
                        merge_mask = (df[time_column] >= current_bout_start) & (df[time_column] < end_time)
                        merge_data = df[merge_mask]
                        merge_percentage = merge_data[activity_column].isin(target_activity).mean()
                        
                        # Only merge if the combined period still meets activity threshold
                        if merge_percentage >= self.activity_threshold:
                            # Merge with current bout
                            last_activity_end = end_time
                            continue
                
                # Start new bout
                current_bout_start = start_time
                last_activity_end = end_time
                
                # Mark all epochs in this bout
                bout_mask = (df[time_column] >= start_time) & (df[time_column] < end_time)
                df.loc[bout_mask, 'is_bout'] = True
                df.loc[bout_mask, 'bout_id'] = bout_id
                df.loc[bout_mask, 'bout_duration'] = duration
                df.loc[bout_mask, 'bout_activity_percentage'] = target_percentage
                bout_id += 1
        
        return df
    
    def plot_bouts(
        self,
        df: pd.DataFrame,
        time_column: str = 'window_start',
        activity_column: str = 'activity_level_sdvm_mangle',
        figsize: tuple = (15, 10)
    ) -> None:
        """
        Plot detected bouts overlaid on the activity levels.
        
        Args:
            df: DataFrame containing bout detection results
            time_column: Name of the column containing window start times
            activity_column: Name of the column containing activity levels
            figsize: Figure size (width, height) in inches
        """
        # Create figure with three subplots
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=figsize, height_ratios=[2, 1, 1])
        
        # Plot activity levels (top panel)
        activity_order = ['INVALID', 'SEDENTARY', 'LIGHT_PA', 'MODERATE_PA', 
                         'MODERATE-VIGOROUS_PA', 'VIGOROUS_PA']
        activity_map = {level: i for i, level in enumerate(activity_order)}
        
        # Plot each window as a horizontal line
        for _, row in df.iterrows():
            y_pos = activity_map[row[activity_column]]
            ax1.hlines(y=y_pos,
                      xmin=row[time_column],
                      xmax=row['window_end'],
                      colors='#999999',
                      linewidth=2,
                      alpha=0.5)
        
        # Highlight bouts
        for bout_id in df[df['is_bout']]['bout_id'].unique():
            bout_data = df[df['bout_id'] == bout_id]
            bout_start = bout_data[time_column].min()
            bout_end = bout_data['window_end'].max()
            ax1.axvspan(bout_start, bout_end, alpha=0.3, color='#D55E00')
        
        # Customize activity plot
        ax1.set_ylim(-0.5, len(activity_order) - 0.5)
        ax1.set_yticks(range(len(activity_order)))
        ax1.set_yticklabels(activity_order)
        ax1.set_title('Activity Levels with Detected Bouts')
        ax1.grid(True, alpha=0.3, axis='x', linestyle='--')
        
        # Plot bout activity percentages (middle panel)
        bout_data = df[df['is_bout']].copy()
        if not bout_data.empty:
            for bout_id in bout_data['bout_id'].unique():
                bout = bout_data[bout_data['bout_id'] == bout_id]
                ax2.plot(bout[time_column], bout['bout_activity_percentage'],
                        color='#D55E00', linewidth=2)
        
        # Add threshold line
        ax2.axhline(y=self.activity_threshold, color='#666666', linestyle='--', alpha=0.5,
                   label=f'Threshold ({self.activity_threshold:.0%})')
        
        # Customize bout percentage plot
        ax2.set_ylim(0, 1)
        ax2.set_ylabel('Bout Activity Percentage')
        ax2.grid(True, alpha=0.3, linestyle='--')
        ax2.legend()
        
        # Plot centered window percentages (bottom panel)
        ax3.plot(df[time_column], df['centered_window_percentage'],
                color='#0072B2', linewidth=2, label='Centered Window')
        ax3.axhline(y=self.activity_threshold, color='#666666', linestyle='--', alpha=0.5,
                   label=f'Threshold ({self.activity_threshold:.0%})')
        
        # Customize centered window plot
        ax3.set_ylim(0, 1)
        ax3.set_ylabel('Centered Window Activity Percentage')
        ax3.grid(True, alpha=0.3, linestyle='--')
        ax3.legend()
        
        # Format x-axis for all subplots
        for ax in [ax1, ax2, ax3]:
            ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%H:%M'))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        plt.show() 