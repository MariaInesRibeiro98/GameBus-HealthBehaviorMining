import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Optional, Dict
from datetime import datetime, timedelta


def plot_activity_bouts(smoothed_df: pd.DataFrame, 
                       bouts_dfs: Dict[str, pd.DataFrame],
                       start_time_column: str,
                       end_time_column: str,
                       activity_classes: List[str] = ['LIGHT', 'MVPA'],
                       colors: Optional[dict] = None,
                       figsize: tuple = (15, 5),
                       title: str = "Activity Bouts Over Time") -> None:
    """
    Plot activity bouts as horizontal lines over time.
    
    Args:
        smoothed_df (pd.DataFrame): DataFrame containing smoothed classifications
        bouts_dfs (Dict[str, pd.DataFrame]): Dictionary mapping activity classes to their bout DataFrames
        start_time_column (str): Name of the column containing start times
        end_time_column (str): Name of the column containing end times
        activity_classes (List[str]): List of activity classes to plot
        colors (dict, optional): Dictionary mapping activity classes to colors
        figsize (tuple): Figure size (width, height)
        title (str): Plot title
    """
    # Set default colors if not provided
    if colors is None:
        colors = {
            'LIGHT': 'lightgreen',
            'MVPA': 'darkgreen',
            'SEDENTARY': 'lightgray',
            'INVALID': 'red'
        }
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=figsize)
    
    # Get time range
    #start_time = smoothed_df[start_time_column].min()
    #end_time = smoothed_df[end_time_column].max()
    
    # Assign y-positions for each activity class
    y_positions = {activity: i for i, activity in enumerate(activity_classes)}
    
    # Plot bouts as horizontal lines for each activity class
    for activity in activity_classes:
        if activity in bouts_dfs:
            bouts_df = bouts_dfs[activity]
            y_pos = y_positions[activity]
            
            # Plot each bout as a horizontal line
            for _, bout in bouts_df.iterrows():
                ax.hlines(y=y_pos, 
                         xmin=bout[start_time_column], 
                         xmax=bout[end_time_column],
                         colors=colors.get(activity, 'gray'),
                         linewidth=3,
                         alpha=0.7,
                         label=f'{activity} Bout' if _ == 0 else "")  # Label only once per activity
    
    # Customize plot
    ax.set_yticks(list(range(len(activity_classes))))
    ax.set_yticklabels(activity_classes)
    ax.set_xlabel('Time')
    ax.set_title(title)
    
    # Format x-axis
    ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%H:%M'))
    plt.xticks(rotation=45)
    
    # Add grid
    ax.grid(True, alpha=0.3)
    
    # Set y-axis limits with some padding
    ax.set_ylim(-0.5, len(activity_classes) - 0.5)
    
    # Add legend (only for unique activity classes)
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc='upper right')
    
    # Adjust layout
    plt.tight_layout()
    
    return fig, ax


def plot_activity_bouts_with_stats(smoothed_df: pd.DataFrame,
                                 bouts_dfs: Dict[str, pd.DataFrame],
                                 start_time_column: str,
                                 end_time_column: str,
                                 activity_classes: List[str] = ['LIGHT', 'MVPA'],
                                 colors: Optional[dict] = None,
                                 figsize: tuple = (15, 8)) -> None:
    """
    Plot activity bouts over time with statistics.
    
    Args:
        smoothed_df (pd.DataFrame): DataFrame containing smoothed classifications
        bouts_dfs (Dict[str, pd.DataFrame]): Dictionary mapping activity classes to their bout DataFrames
        start_time_column (str): Name of the column containing start times
        end_time_column (str): Name of the column containing end times
        activity_classes (List[str]): List of activity classes to plot
        colors (dict, optional): Dictionary mapping activity classes to colors
        figsize (tuple): Figure size (width, height)
    """
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, 
                                  gridspec_kw={'height_ratios': [3, 1]})
    
    # Plot bouts in the top subplot
    plot_activity_bouts(smoothed_df, bouts_dfs,
                       start_time_column, end_time_column,
                       activity_classes, colors, figsize=(figsize[0], figsize[1]*0.7),
                       title="Activity Bouts Over Time")
    
    # Calculate and plot statistics in the bottom subplot
    total_duration = (smoothed_df[end_time_column].max() - 
                     smoothed_df[start_time_column].min())
    
    # Calculate bout durations by activity class
    bout_stats = []
    for activity in activity_classes:
        if activity in bouts_dfs:
            bouts_df = bouts_dfs[activity]
            total_bout_duration = (bouts_df[end_time_column] - bouts_df[start_time_column]).sum()
            percentage = (total_bout_duration / total_duration) * 100
            bout_stats.append({
                'activity': activity,
                'duration': total_bout_duration,
                'percentage': percentage
            })
    
    # Plot statistics
    stats_df = pd.DataFrame(bout_stats)
    bars = ax2.bar(stats_df['activity'], stats_df['percentage'],
                  color=[colors.get(act, 'gray') for act in stats_df['activity']])
    
    # Add percentage labels on top of bars
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}%',
                ha='center', va='bottom')
    
    ax2.set_ylabel('Percentage of Total Time')
    ax2.set_title('Activity Bout Statistics')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig, (ax1, ax2) 