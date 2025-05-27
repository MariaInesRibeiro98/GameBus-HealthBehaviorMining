import pandas as pd
import numpy as np
from typing import Literal
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

class PhysicalActivityClassifier:
    """
    A class for classifying physical activity levels based on accelerometer data.
    """
    
    # Unified activity level categories
    ActivityLevel = Literal[
        'INVALID', 'SEDENTARY', 'LIGHT_PA', 'MODERATE_PA', 'MODERATE-VIGOROUS_PA', 'VIGOROUS_PA'
    ]

    # ENMO thresholds
    ENMO_MVPA_THRESHOLD = 0.11
    ENMO_LPA_THRESHOLD = 0.05

    # SDVM/Mangle thresholds
    SDVM_LIGHT_THRESHOLD = 0.26
    SDVM_MODERATE_THRESHOLD = 0.79
    MANGLE_LIGHT_THRESHOLD = -52
    MANGLE_MODERATE_THRESHOLD = -52

    # Unified color mapping for all activity levels
    ACTIVITY_COLORS = {
        'MODERATE-VIGOROUS_PA': '#D55E00',  # Vermillion (dark orange-red)
        'VIGOROUS_PA': '#D55E00',           # Vermillion (dark orange-red)
        'LIGHT_PA': '#56B4E9',              # Sky blue
        'MODERATE_PA': '#009E73',           # Bluish green
        'SEDENTARY': '#0072B2',             # Blue
        'INVALID': '#999999'                # Medium grey
    }
    
    @classmethod
    def classify_activity_levels_enmo(cls, df: pd.DataFrame, enmo_column: str = 'enmo') -> pd.DataFrame:
        """
        Classify physical activity levels based on ENMO values.
        Adds 'activity_level_enmo' column with values: 'MODERATE-VIGOROUS_PA', 'LIGHT_PA', 'SEDENTARY', or 'INVALID'.
        """
        result_df = df.copy()
        if enmo_column not in df.columns:
            raise ValueError(f"Column '{enmo_column}' not found in DataFrame")
        result_df['activity_level_enmo'] = 'INVALID'
        mask_mvpa = df[enmo_column] >= cls.ENMO_MVPA_THRESHOLD
        mask_lpa = (df[enmo_column] >= cls.ENMO_LPA_THRESHOLD) & (df[enmo_column] < cls.ENMO_MVPA_THRESHOLD)
        mask_sedentary = (df[enmo_column] < cls.ENMO_LPA_THRESHOLD) & (df[enmo_column] > 0)
        result_df.loc[mask_mvpa, 'activity_level_enmo'] = 'MODERATE-VIGOROUS_PA'
        result_df.loc[mask_lpa, 'activity_level_enmo'] = 'LIGHT_PA'
        result_df.loc[mask_sedentary, 'activity_level_enmo'] = 'SEDENTARY'
        return result_df
    
    @classmethod
    def plot_activity_levels_enmo(cls, df: pd.DataFrame, time_column: str = 'window_start', 
                                 window_end_column: str = 'window_end',
                                 activity_column: str = 'activity_level_enmo', 
                                 figsize: tuple = (15, 8)) -> None:
        """
        Plot ENMO-based activity levels over time using horizontal lines that span the full window duration.
        Each line represents a time window and its activity level, with proper time axis and clear activity level representation.
        
        Parameters:
            df (pd.DataFrame): DataFrame containing activity levels and window times
            time_column (str): Name of the column containing window start times (default: 'window_start')
            window_end_column (str): Name of the column containing window end times (default: 'window_end')
            activity_column (str): Name of the column containing activity levels (default: 'activity_level_enmo')
            figsize (tuple): Figure size (width, height) in inches (default: (15, 8))
        """
        if time_column not in df.columns:
            raise ValueError(f"Column '{time_column}' not found in DataFrame")
        if window_end_column not in df.columns:
            raise ValueError(f"Column '{window_end_column}' not found in DataFrame")
        if activity_column not in df.columns:
            raise ValueError(f"Column '{activity_column}' not found in DataFrame")
            
        # Sort dataframe by time to ensure proper ordering
        df = df.sort_values(time_column)
        
        # Define activity levels and their y-axis positions
        activity_order = ['INVALID', 'SEDENTARY', 'LIGHT_PA', 'MODERATE_PA', 'MODERATE-VIGOROUS_PA', 'VIGOROUS_PA']
        activity_map = {level: i for i, level in enumerate(activity_order)}
        
        # Create figure with clean style
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=figsize)
        
        # Set background color and grid style
        ax.set_facecolor('#f0f0f0')  # Lighter grey background
        fig.patch.set_facecolor('white')
        
        # Set y-axis limits and ticks
        ax.set_ylim(-0.5, len(activity_order) - 0.5)
        ax.set_yticks(range(len(activity_order)))
        ax.set_yticklabels(activity_order, fontsize=10)
        
        # Set x-axis limits to span the entire time range
        time_start = df[time_column].min()
        time_end = df[window_end_column].max()
        ax.set_xlim(time_start, time_end)
        
        # Plot each window as a horizontal line with increased linewidth for better visibility
        for _, row in df.iterrows():
            y_pos = activity_map[row[activity_column]]
            ax.hlines(y=y_pos,
                     xmin=row[time_column],
                     xmax=row[window_end_column],
                     colors=cls.ACTIVITY_COLORS.get(row[activity_column], '#999999'),
                     linewidth=4,  # Increased linewidth
                     alpha=0.9)    # Increased opacity
        
        # Customize the plot
        ax.grid(True, alpha=0.3, axis='x', linestyle='--', color='#666666')  # Darker grid lines
        ax.set_title('Physical Activity Levels (ENMO) Over Time', pad=20, fontsize=12, fontweight='bold')
        ax.set_xlabel('Time', labelpad=10, fontsize=10)
        ax.set_ylabel('Activity Level', labelpad=10, fontsize=10)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%H:%M'))
        plt.xticks(rotation=45, fontsize=9)
        
        # Add legend for activity levels with increased linewidth
        legend_elements = [plt.Line2D([0], [0], color=color, label=level, linewidth=4)
                          for level, color in cls.ACTIVITY_COLORS.items()]
        ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.15, 1),
                 framealpha=0.95, edgecolor='#666666', fontsize=9)
        
        # Remove top and right spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        plt.show()
    
    @classmethod
    def classify_activity_levels_sdvm_mangle(cls, df: pd.DataFrame, sdvm_column: str = 'sdvm', mangle_column: str = 'mangle') -> pd.DataFrame:
        """
        Classify activity levels based on standard deviation of vector magnitude (sdvm) and mean acceleration angle relative to vertical (mangle).
        Adds 'activity_level_sdvm_mangle' column with values: 'LIGHT_PA', 'MODERATE_PA', 'VIGOROUS_PA', or 'INVALID'.
        
        Classification rules:
        1. First check for invalid values (-9999) in either feature
        2. Then apply activity level classification based on thresholds:
           - Light PA: Low SDVM (≤ 0.26) with high angle (> -52)
           - Moderate PA: Two conditions:
             a. Low SDVM (≤ 0.26) with low angle (≤ -52)
             b. Medium SDVM (0.26-0.79) with high angle (> -52)
           - Vigorous PA: Two conditions:
             a. Medium SDVM (0.26-0.79) with low angle (≤ -52)
             b. High SDVM (> 0.79)
        """
        result_df = df.copy()
        if sdvm_column not in df.columns:
            raise ValueError(f"Column '{sdvm_column}' not found in DataFrame")
        if mangle_column not in df.columns:
            raise ValueError(f"Column '{mangle_column}' not found in DataFrame")
            
        # Initialize all as INVALID
        result_df['activity_level_sdvm_mangle'] = 'INVALID'
        
        # Get feature values
        sdvm = result_df[sdvm_column]
        mangle = result_df[mangle_column]
        
        # Create mask for valid data points (not -9999)
        valid_mask = (sdvm != -9999) & (mangle != -9999)
        
        # Only classify valid data points
        if valid_mask.any():
            # Get valid data
            valid_sdvm = sdvm[valid_mask]
            valid_mangle = mangle[valid_mask]
            
            # Create masks for each activity level
            mask_light = (valid_sdvm <= cls.SDVM_LIGHT_THRESHOLD) & (valid_mangle > cls.MANGLE_LIGHT_THRESHOLD)
            mask_moderate_1 = (valid_sdvm <= cls.SDVM_LIGHT_THRESHOLD) & (valid_mangle <= cls.MANGLE_LIGHT_THRESHOLD)
            mask_moderate_2 = (valid_sdvm > cls.SDVM_LIGHT_THRESHOLD) & (valid_sdvm <= cls.SDVM_MODERATE_THRESHOLD) & (valid_mangle > cls.MANGLE_MODERATE_THRESHOLD)
            mask_vigorous_1 = (valid_sdvm > cls.SDVM_LIGHT_THRESHOLD) & (valid_sdvm <= cls.SDVM_MODERATE_THRESHOLD) & (valid_mangle <= cls.MANGLE_MODERATE_THRESHOLD)
            mask_vigorous_2 = (valid_sdvm > cls.SDVM_MODERATE_THRESHOLD)
            
            # Apply classifications only to valid data points
            result_df.loc[valid_mask & mask_light, 'activity_level_sdvm_mangle'] = 'LIGHT_PA'
            result_df.loc[valid_mask & (mask_moderate_1 | mask_moderate_2), 'activity_level_sdvm_mangle'] = 'MODERATE_PA'
            result_df.loc[valid_mask & (mask_vigorous_1 | mask_vigorous_2), 'activity_level_sdvm_mangle'] = 'VIGOROUS_PA'
        
        return result_df

    @classmethod
    def plot_activity_levels_sdvm_mangle(cls, df: pd.DataFrame, time_column: str = 'window_start',
                                        window_end_column: str = 'window_end',
                                        activity_column: str = 'activity_level_sdvm_mangle', 
                                        figsize: tuple = (15, 8)) -> None:
        """
        Plot activity levels (SDVM/Mangle method) over time using horizontal lines that span the full window duration.
        Each line represents a time window and its activity level, with proper time axis and clear activity level representation.
        
        Parameters:
            df (pd.DataFrame): DataFrame containing activity levels and window times
            time_column (str): Name of the column containing window start times (default: 'window_start')
            window_end_column (str): Name of the column containing window end times (default: 'window_end')
            activity_column (str): Name of the column containing activity levels (default: 'activity_level_sdvm_mangle')
            figsize (tuple): Figure size (width, height) in inches (default: (15, 8))
        """
        if time_column not in df.columns:
            raise ValueError(f"Column '{time_column}' not found in DataFrame")
        if window_end_column not in df.columns:
            raise ValueError(f"Column '{window_end_column}' not found in DataFrame")
        if activity_column not in df.columns:
            raise ValueError(f"Column '{activity_column}' not found in DataFrame")
            
        # Sort dataframe by time to ensure proper ordering
        df = df.sort_values(time_column)
        
        # Define activity levels and their y-axis positions
        activity_order = ['INVALID', 'SEDENTARY', 'LIGHT_PA', 'MODERATE_PA', 'MODERATE-VIGOROUS_PA', 'VIGOROUS_PA']
        activity_map = {level: i for i, level in enumerate(activity_order)}
        
        # Create figure with clean style
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=figsize)
        
        # Set background color and grid style
        ax.set_facecolor('#f0f0f0')  # Lighter grey background
        fig.patch.set_facecolor('white')
        
        # Set y-axis limits and ticks
        ax.set_ylim(-0.5, len(activity_order) - 0.5)
        ax.set_yticks(range(len(activity_order)))
        ax.set_yticklabels(activity_order, fontsize=10)
        
        # Set x-axis limits to span the entire time range
        time_start = df[time_column].min()
        time_end = df[window_end_column].max()
        ax.set_xlim(time_start, time_end)
        
        # Plot each window as a horizontal line with increased linewidth for better visibility
        for _, row in df.iterrows():
            y_pos = activity_map[row[activity_column]]
            ax.hlines(y=y_pos,
                     xmin=row[time_column],
                     xmax=row[window_end_column],
                     colors=cls.ACTIVITY_COLORS.get(row[activity_column], '#999999'),
                     linewidth=4,  # Increased linewidth
                     alpha=0.9)    # Increased opacity
        
        # Customize the plot
        ax.grid(True, alpha=0.3, axis='x', linestyle='--', color='#666666')  # Darker grid lines
        ax.set_title('Physical Activity Levels (SDVM/Mangle) Over Time', pad=20, fontsize=12, fontweight='bold')
        ax.set_xlabel('Time', labelpad=10, fontsize=10)
        ax.set_ylabel('Activity Level', labelpad=10, fontsize=10)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%H:%M'))
        plt.xticks(rotation=45, fontsize=9)
        
        # Add legend for activity levels with increased linewidth
        legend_elements = [plt.Line2D([0], [0], color=color, label=level, linewidth=4)
                          for level, color in cls.ACTIVITY_COLORS.items()]
        ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.15, 1),
                 framealpha=0.95, edgecolor='#666666', fontsize=9)
        
        # Remove top and right spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.tight_layout()
        plt.show() 