import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Optional, Dict, Any
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


def plot_location_segments(location_objects: List[Dict[str, Any]], 
                         target_date: Optional[datetime] = None,
                         figsize: tuple = (15, 5),
                         title: Optional[str] = None) -> tuple:
    """
    Plot location segments as a continuous timeline with colored bars for a single day.
    
    Args:
        location_objects (List[Dict[str, Any]]): List of location segment objects
        target_date (datetime, optional): Date to plot. If None, uses the date of the first segment
        figsize (tuple): Figure size (width, height)
        title (str, optional): Plot title. If None, generates title with date
        
    Returns:
        tuple: (fig, ax) matplotlib figure and axis objects
    """
    # Create figure and axis
    fig, ax = plt.subplots(figsize=figsize)
    
    # Convert location objects to DataFrame for easier manipulation
    segments_df = pd.DataFrame([
        {
            'location_type': next(attr['value'] for attr in obj['attributes'] 
                                if attr['name'] == 'location_type'),
            'start_time': pd.to_datetime(next(attr['value'] for attr in obj['attributes'] 
                                            if attr['name'] == 'start_time')),
            'end_time': pd.to_datetime(next(attr['value'] for attr in obj['attributes'] 
                                          if attr['name'] == 'end_time'))
        }
        for obj in location_objects
    ])
    
    # Sort segments by start time
    segments_df = segments_df.sort_values('start_time')
    
    # If no target date provided, use the date of the first segment
    if target_date is None:
        target_date = segments_df['start_time'].iloc[0].date()
    else:
        target_date = pd.to_datetime(target_date).date()
    
    # Filter segments for the target date
    segments_df = segments_df[
        (segments_df['start_time'].dt.date == target_date) |
        (segments_df['end_time'].dt.date == target_date)
    ]
    
    if len(segments_df) == 0:
        raise ValueError(f"No location segments found for date {target_date}")
    
    # Adjust start and end times to be within the target date
    segments_df['start_time'] = segments_df['start_time'].apply(
        lambda x: max(x, pd.Timestamp(target_date))
    )
    segments_df['end_time'] = segments_df['end_time'].apply(
        lambda x: min(x, pd.Timestamp(target_date) + pd.Timedelta(days=1))
    )
    
    # Get unique location types and assign colors
    location_types = segments_df['location_type'].unique()
    colors = plt.cm.Set3(np.linspace(0, 1, len(location_types)))
    color_map = dict(zip(location_types, colors))
    
    # Plot each segment as a horizontal bar
    for _, segment in segments_df.iterrows():
        ax.barh(y=0,  # Single row for all segments
                width=(segment['end_time'] - segment['start_time']).total_seconds() / 3600,  # Convert to hours
                left=segment['start_time'],
                color=color_map[segment['location_type']],
                alpha=0.7,
                label=segment['location_type'] if segment['location_type'] not in ax.get_legend_handles_labels()[1] else "")
    
    # Set title
    if title is None:
        title = f"Location Segments for {target_date.strftime('%Y-%m-%d')}"
    ax.set_title(title)
    
    # Customize plot
    ax.set_xlabel('Time')
    ax.set_yticks([])  # Hide y-axis ticks since we only have one row
    
    # Set x-axis limits to the target date
    ax.set_xlim(
        pd.Timestamp(target_date),
        pd.Timestamp(target_date) + pd.Timedelta(days=1)
    )
    
    # Format x-axis
    ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%H:%M'))
    ax.xaxis.set_major_locator(plt.matplotlib.dates.HourLocator(interval=2))  # Show ticks every 2 hours
    plt.xticks(rotation=45)
    
    # Add grid
    ax.grid(True, alpha=0.3)
    
    # Add legend (only unique location types)
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), 
             loc='center left', bbox_to_anchor=(1, 0.5))
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    
    return fig, ax 