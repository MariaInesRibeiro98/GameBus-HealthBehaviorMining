import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from synthetic_data_generator import SyntheticSensorDataGenerator
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional

def test_sensor_generation():
    """Test basic sensor data generation without gaps."""
    print("\n=== Testing Basic Sensor Data Generation ===")
    
    # Create generator with a short time period for testing
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=2)  # 2 hours of data
    
    generator = SyntheticSensorDataGenerator(
        start_timestamp=start_time,
        end_timestamp=end_time,
        verbose=True
    )
    
    # Generate data without gaps
    acc_df, hr_df = generator.generate_sensor_data_without_gaps()
    
    # Print basic statistics
    print("\nAccelerometer Data Statistics:")
    print(f"Number of samples: {len(acc_df)}")
    print(f"Time range: {acc_df['timestamp'].min()} to {acc_df['timestamp'].max()}")
    print(f"Sampling rate: {len(acc_df) / ((end_time - start_time).total_seconds()):.1f} Hz")
    
    # Calculate statistics only for valid readings
    valid_mask = (acc_df['x'] != generator.invalid_value) & \
                 (acc_df['y'] != generator.invalid_value) & \
                 (acc_df['z'] != generator.invalid_value)
    
    print(f"\nValid readings: {valid_mask.sum()} out of {len(acc_df)} ({valid_mask.mean()*100:.1f}%)")
    
    if valid_mask.any():
        print("\nAccelerometer magnitude statistics (valid readings only):")
        acc_magnitudes = np.sqrt(
            acc_df.loc[valid_mask, 'x']**2 + 
            acc_df.loc[valid_mask, 'y']**2 + 
            acc_df.loc[valid_mask, 'z']**2
        )
        print(f"Mean magnitude: {acc_magnitudes.mean():.2f} m/s² ({acc_magnitudes.mean()/9.81:.3f} g)")
        print(f"Std magnitude: {acc_magnitudes.std():.2f} m/s² ({acc_magnitudes.std()/9.81:.3f} g)")
        print(f"Magnitude above 1g: {(acc_magnitudes.mean()/9.81 - 1.0):.3f} ± {acc_magnitudes.std()/9.81:.3f} g")
    else:
        print("\nNo valid accelerometer readings found!")
    
    print("\nHeart Rate Data Statistics:")
    print(f"Number of samples: {len(hr_df)}")
    print(f"Time range: {hr_df['timestamp'].min()} to {hr_df['timestamp'].max()}")
    print(f"Sampling rate: {len(hr_df) / ((end_time - start_time).total_seconds()):.1f} Hz")
    
    # Calculate heart rate statistics only for valid readings
    hr_valid_mask = hr_df['bpm'] != generator.invalid_value
    print(f"\nValid readings: {hr_valid_mask.sum()} out of {len(hr_df)} ({hr_valid_mask.mean()*100:.1f}%)")
    
    if hr_valid_mask.any():
        print(f"Mean heart rate (valid readings only): {hr_df.loc[hr_valid_mask, 'bpm'].mean():.1f} BPM")
        print(f"Std heart rate (valid readings only): {hr_df.loc[hr_valid_mask, 'bpm'].std():.1f} BPM")
    else:
        print("\nNo valid heart rate readings found!")
    
    # Plot a small section of the data
    plot_duration = timedelta(minutes=5)
    plot_start = start_time + timedelta(minutes=10)  # Start 10 minutes in
    plot_end = plot_start + plot_duration
    
    # Filter data for plotting
    acc_plot = acc_df[(acc_df['timestamp'] >= plot_start) & (acc_df['timestamp'] < plot_end)]
    hr_plot = hr_df[(hr_df['timestamp'] >= plot_start) & (hr_df['timestamp'] < plot_end)]
    
    # Create plots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # Plot accelerometer data
    valid_mask_plot = (acc_plot['x'] != generator.invalid_value) & \
                     (acc_plot['y'] != generator.invalid_value) & \
                     (acc_plot['z'] != generator.invalid_value)
    
    # Plot only valid readings
    acc_plot_valid = acc_plot[valid_mask_plot]
    if len(acc_plot_valid) > 0:
        ax1.plot(acc_plot_valid['timestamp'], acc_plot_valid['x'], label='x')
        ax1.plot(acc_plot_valid['timestamp'], acc_plot_valid['y'], label='y')
        ax1.plot(acc_plot_valid['timestamp'], acc_plot_valid['z'], label='z')
    
    # Mark invalid readings
    invalid_times = acc_plot[~valid_mask_plot]['timestamp']
    if len(invalid_times) > 0:
        ax1.plot(invalid_times, [generator.invalid_value] * len(invalid_times), 
                'rx', label='Invalid', markersize=10)
    
    ax1.set_title('Accelerometer Data (5 minutes)')
    ax1.set_ylabel('Acceleration (m/s²)')
    ax1.legend()
    ax1.grid(True)
    
    # Plot heart rate data
    hr_valid_mask_plot = hr_plot['bpm'] != generator.invalid_value
    hr_plot_valid = hr_plot[hr_valid_mask_plot]
    
    if len(hr_plot_valid) > 0:
        ax2.plot(hr_plot_valid['timestamp'], hr_plot_valid['bpm'], 'r-', label='Heart Rate')
    
    # Mark invalid readings
    invalid_times_hr = hr_plot[~hr_valid_mask_plot]['timestamp']
    if len(invalid_times_hr) > 0:
        ax2.plot(invalid_times_hr, [generator.invalid_value] * len(invalid_times_hr), 
                'rx', label='Invalid', markersize=10)
    
    ax2.set_title('Heart Rate Data (5 minutes)')
    ax2.set_ylabel('Heart Rate (BPM)')
    ax2.legend()
    ax2.grid(True)
    
    plt.tight_layout()
    plt.show()
    
    # After generating data, add:
    print("\nPlotting sensor data...")
    fig = plot_sensor_data(acc_df, hr_df)
    plt.show()
    
    return acc_df, hr_df

def test_gap_insertion(acc_df, hr_df):
    """Test gap insertion on existing data."""
    print("\n=== Testing Gap Insertion ===")
    
    # Create a new generator with the same parameters
    generator = SyntheticSensorDataGenerator(
        start_timestamp=acc_df['timestamp'].min(),
        end_timestamp=acc_df['timestamp'].max(),
        verbose=True
    )
    
    # Make copies of the dataframes
    acc_with_gaps = acc_df.copy()
    hr_with_gaps = hr_df.copy()
    
    # Add gaps
    print("\nStarting gap insertion...")
    acc_with_gaps, hr_with_gaps = generator._add_correlated_gaps(acc_with_gaps, hr_with_gaps)
    
    # Calculate gap statistics
    def calculate_gaps(df):
        df = df.sort_values('timestamp')
        time_diffs = df['timestamp'].diff()
        gaps = time_diffs[time_diffs > timedelta(seconds=60)]
        return {
            'num_gaps': len(gaps),
            'mean_duration': gaps.dt.total_seconds().mean() if len(gaps) > 0 else 0,
            'max_duration': gaps.dt.total_seconds().max() if len(gaps) > 0 else 0,
            'gaps': gaps.dt.total_seconds().tolist()  # Store all gap durations
        }
    
    acc_gaps = calculate_gaps(acc_with_gaps)
    hr_gaps = calculate_gaps(hr_with_gaps)
    
    print("\nGap Statistics:")
    print("Accelerometer:")
    print(f"  Number of gaps: {acc_gaps['num_gaps']}")
    print(f"  Mean gap duration: {acc_gaps['mean_duration']:.1f} seconds")
    print(f"  Max gap duration: {acc_gaps['max_duration']:.1f} seconds")
    if acc_gaps['num_gaps'] > 0:
        print("  First 5 gap durations:", [f"{d:.1f}s" for d in acc_gaps['gaps'][:5]])
    
    print("\nHeart Rate:")
    print(f"  Number of gaps: {hr_gaps['num_gaps']}")
    print(f"  Mean gap duration: {hr_gaps['mean_duration']:.1f} seconds")
    print(f"  Max gap duration: {hr_gaps['max_duration']:.1f} seconds")
    if hr_gaps['num_gaps'] > 0:
        print("  First 5 gap durations:", [f"{d:.1f}s" for d in hr_gaps['gaps'][:5]])
    
    # Plot data with gaps
    plot_duration = timedelta(minutes=5)
    plot_start = acc_df['timestamp'].min() + timedelta(minutes=10)
    plot_end = plot_start + plot_duration
    
    # Filter data for plotting
    acc_plot = acc_with_gaps[(acc_with_gaps['timestamp'] >= plot_start) & 
                            (acc_with_gaps['timestamp'] < plot_end)]
    hr_plot = hr_with_gaps[(hr_with_gaps['timestamp'] >= plot_start) & 
                          (hr_with_gaps['timestamp'] < plot_end)]
    
    # Create plots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # Plot accelerometer data with gaps
    ax1.plot(acc_plot['timestamp'], acc_plot['x'], label='x')
    ax1.plot(acc_plot['timestamp'], acc_plot['y'], label='y')
    ax1.plot(acc_plot['timestamp'], acc_plot['z'], label='z')
    ax1.set_title('Accelerometer Data with Gaps (5 minutes)')
    ax1.set_ylabel('Acceleration (m/s²)')
    ax1.legend()
    ax1.grid(True)
    
    # Plot heart rate data with gaps
    ax2.plot(hr_plot['timestamp'], hr_plot['bpm'], 'r-', label='Heart Rate')
    ax2.set_title('Heart Rate Data with Gaps (5 minutes)')
    ax2.set_ylabel('Heart Rate (BPM)')
    ax2.grid(True)
    
    plt.tight_layout()
    plt.show()
    
    # After adding gaps, add:
    print("\nPlotting sensor data with gaps...")
    fig = plot_sensor_data(acc_df, hr_df)
    plt.show()
    
    return acc_with_gaps, hr_with_gaps

def plot_sensor_data(acc_df: pd.DataFrame, hr_df: pd.DataFrame, 
                    start_time: Optional[datetime] = None,
                    duration_minutes: float = 5.0):
    """
    Plot accelerometer magnitude and heart rate over time.
    
    Args:
        acc_df: DataFrame with accelerometer data (x, y, z columns)
        hr_df: DataFrame with heart rate data (bpm column)
        start_time: Start time for the plot (defaults to start of data)
        duration_minutes: Duration to plot in minutes (default: 5 minutes)
    """
    # Set style
    plt.style.use('seaborn')
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), sharex=True)
    
    # Set start time if not provided
    if start_time is None:
        start_time = acc_df['timestamp'].iloc[0]
    end_time = start_time + timedelta(minutes=duration_minutes)
    
    # Filter data for the time window
    acc_mask = (acc_df['timestamp'] >= start_time) & (acc_df['timestamp'] <= end_time)
    hr_mask = (hr_df['timestamp'] >= start_time) & (hr_df['timestamp'] <= end_time)
    
    acc_plot = acc_df[acc_mask]
    hr_plot = hr_df[hr_mask]
    
    # Calculate accelerometer magnitude
    acc_magnitude = np.sqrt(acc_plot['x']**2 + acc_plot['y']**2 + acc_plot['z']**2)
    
    # Plot accelerometer magnitude
    ax1.plot(acc_plot['timestamp'], acc_magnitude, 'b-', label='Accelerometer Magnitude', alpha=0.7)
    ax1.set_ylabel('Acceleration (m/s²)')
    ax1.set_title('Accelerometer Magnitude')
    ax1.grid(True)
    
    # Add gravity reference line
    ax1.axhline(y=9.81, color='r', linestyle='--', alpha=0.5, label='Gravity (9.81 m/s²)')
    ax1.legend()
    
    # Plot heart rate
    # Filter out invalid values for plotting
    valid_hr = hr_plot[hr_plot['bpm'] != -9999]
    ax2.plot(valid_hr['timestamp'], valid_hr['bpm'], 'g-', label='Heart Rate', alpha=0.7)
    ax2.set_ylabel('Heart Rate (BPM)')
    ax2.set_title('Heart Rate')
    ax2.grid(True)
    ax2.legend()
    
    # Format x-axis
    plt.gcf().autofmt_xdate()  # Rotate and align the tick labels
    ax2.set_xlabel('Time')
    
    # Add a title for the entire figure
    plt.suptitle(f'Sensor Data from {start_time.strftime("%Y-%m-%d %H:%M:%S")} '
                f'to {end_time.strftime("%Y-%m-%d %H:%M:%S")}', y=1.02)
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    
    return fig

if __name__ == "__main__":
    # First test basic sensor data generation without gaps
    print("Testing sensor data generation (without gaps)...")
    acc_df, hr_df = test_sensor_generation()
    
    # Then test gap insertion separately
    print("\nTesting gap insertion on the generated data...")
    acc_with_gaps, hr_with_gaps = test_gap_insertion(acc_df, hr_df) 