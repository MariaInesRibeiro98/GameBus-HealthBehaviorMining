import pandas as pd
import numpy as np
from typing import Literal
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

class PhysicalActivityClassifier:
    """
    A class for classifying physical activity levels based on accelerometer data.
    """
    
    # Define activity level thresholds
    MVPA_THRESHOLD = 0.11  # Moderate to Vigorous Physical Activity threshold
    LPA_THRESHOLD = 0.05  # Light Physical Activity threshold
    
    # Define activity level categories
    ActivityLevel = Literal['MVPA', 'LPA', 'SEDENTARY', 'INVALID']

        
    # Define colors for each activity level
    ACTIVITY_COLORS = {
        'MVPA': '#FF0000',      # Red
        'LPA': '#FFA500',       # Orange
        'SEDENTARY': '#00FF00', # Green
        'INVALID': '#808080'    # Gray
    }
    
    @classmethod
    def classify_activity_levels(cls, df: pd.DataFrame, enmo_column: str = 'enmo') -> pd.DataFrame:
        """
        Classify physical activity levels based on ENMO values.
        
        Parameters
        ----------
        df : pd.DataFrame
            Input DataFrame containing accelerometer data with ENMO values
        enmo_column : str, default='enmo'
            Name of the column containing ENMO values
            
        Returns
        -------
        pd.DataFrame
            A copy of the input DataFrame with an additional 'activity_level' column
            containing the classification ('MVPA', 'LPA', 'SEDENTARY', or 'INVALID')
        """
        # Create a copy of the input DataFrame
        result_df = df.copy()
        
        # Check if the ENMO column exists
        if enmo_column not in df.columns:
            raise ValueError(f"Column '{enmo_column}' not found in DataFrame")
            
        # Initialize the activity level column with 'INVALID'
        result_df['activity_level'] = 'INVALID'
        
        # Classify based on ENMO thresholds
        mask_mvpa = df[enmo_column] >= cls.MVPA_THRESHOLD
        mask_lpa = (df[enmo_column] >= cls.LPA_THRESHOLD) & (df[enmo_column] < cls.MVPA_THRESHOLD)
        mask_sedentary = (df[enmo_column] < cls.LPA_THRESHOLD) & (df[enmo_column] > 0 )
        
        # Apply classifications
        result_df.loc[mask_mvpa, 'activity_level'] = 'MVPA'
        result_df.loc[mask_lpa, 'activity_level'] = 'LPA'
        result_df.loc[mask_sedentary, 'activity_level'] = 'SEDENTARY'
        
        return result_df 
    
    @classmethod
    def plot_activity_levels(cls, df: pd.DataFrame, time_column: str = 'timestamp', 
                           activity_column: str = 'activity_level',
                           figsize: tuple = (15, 5)) -> None:
        """
        Plot activity levels over time.
        
        Parameters
        ----------
        df : pd.DataFrame
            DataFrame containing the classified activity levels
        time_column : str, default='timestamp'
            Name of the column containing timestamps
        activity_column : str, default='activity_level'
            Name of the column containing activity levels
        figsize : tuple, default=(15, 5)
            Figure size (width, height) in inches
        """
        if time_column not in df.columns:
            raise ValueError(f"Column '{time_column}' not found in DataFrame")
        if activity_column not in df.columns:
            raise ValueError(f"Column '{activity_column}' not found in DataFrame")
            
        # Create a mapping of activity levels to numeric values for plotting
        activity_order = ['INVALID', 'SEDENTARY', 'LPA', 'MVPA']
        activity_map = {level: i for i, level in enumerate(activity_order)}
        
        # Convert activity levels to numeric values
        activity_values = df[activity_column].map(activity_map)
        
        # Create the plot
        plt.figure(figsize=figsize)
        
        # Create a scatter plot
        scatter = plt.scatter(df[time_column], activity_values, 
                            c=[cls.ACTIVITY_COLORS[level] for level in df[activity_column]],
                            s=50, alpha=0.6)
        
        # Customize the plot
        plt.yticks(range(len(activity_order)), activity_order)
        plt.grid(True, alpha=0.3)
        plt.title('Physical Activity Levels Over Time')
        plt.xlabel('Time')
        plt.ylabel('Activity Level')
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=45)
        
        # Adjust layout to prevent label cutoff
        plt.tight_layout()
        
        # Show the plot
        plt.show() 