# Process Mining vs Other Analytical Techniques
# Activity & Stress Monitoring Case Study

"""
This notebook demonstrates the unique advantages of process mining over traditional
analytical techniques using a health monitoring scenario with physical activities,
stress reporting, and location-aware behavioral patterns.
"""

# Import required libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Process mining libraries
try:
    import pm4py
    from pm4py.objects.conversion.log import converter as log_converter
    from pm4py.algo.discovery.inductive import algorithm as inductive_miner
    from pm4py.convert import convert_to_petri_net
    from pm4py.visualization.petri_net import visualizer as pn_visualizer
    from pm4py.visualization.dfg import visualizer as dfg_visualizer
    from pm4py.algo.discovery.dfg import algorithm as dfg_discovery
    from pm4py.statistics.traces.generic.log import case_statistics
    pm4py_available = True
    print("✅ PM4Py library available - Full process mining analysis enabled")
except ImportError:
    pm4py_available = False
    print("⚠️ PM4Py not available - Using alternative visualization methods")

print("📊 Analysis Environment Ready")

# ## 1. Create Synthetic Event Log Data

# Create comprehensive event log with parallel pathways and contextual variables
event_data = []

# Helper function to add events
def add_event(case_id, timestamp, event, location, activity_type=None, notification_type=None, stress_level=None):
    event_data.append({
        'case_id': case_id,
        'timestamp': timestamp,
        'event': event,
        'location': location,
        'activity_type': activity_type,
        'notification_type': notification_type,
        'stress_level': stress_level
    })

# User A - Day 1: Home -> Gym pattern with good compliance
base_time = datetime(2024, 1, 1, 8, 0)
add_event('A-Day1', base_time, 'enter_location', 'home')
add_event('A-Day1', base_time + timedelta(minutes=30), 'physical_activity', 'home', 'light')
add_event('A-Day1', base_time + timedelta(minutes=60), 'notification', 'home', notification_type='received')
add_event('A-Day1', base_time + timedelta(minutes=65), 'self_report', 'home', stress_level=3)
add_event('A-Day1', base_time + timedelta(minutes=120), 'exit_location', 'home')
add_event('A-Day1', base_time + timedelta(minutes=150), 'enter_location', 'gym')
add_event('A-Day1', base_time + timedelta(minutes=180), 'physical_activity', 'gym', 'moderate')
add_event('A-Day1', base_time + timedelta(minutes=210), 'physical_activity', 'gym', 'vigorous')
add_event('A-Day1', base_time + timedelta(minutes=240), 'notification', 'gym', notification_type='received')
add_event('A-Day1', base_time + timedelta(minutes=242), 'self_report', 'gym', stress_level=2)
add_event('A-Day1', base_time + timedelta(minutes=270), 'exit_location', 'gym')

# User A - Day 2: Work stress pattern with missed notifications
base_time = datetime(2024, 1, 2, 8, 0)
add_event('A-Day2', base_time, 'enter_location', 'work')
add_event('A-Day2', base_time + timedelta(minutes=120), 'notification', 'work', notification_type='received')
add_event('A-Day2', base_time + timedelta(minutes=150), 'notification', 'work', notification_type='received')
add_event('A-Day2', base_time + timedelta(minutes=180), 'self_report', 'work', stress_level=7)
add_event('A-Day2', base_time + timedelta(minutes=360), 'physical_activity', 'work', 'light')
add_event('A-Day2', base_time + timedelta(minutes=420), 'notification', 'work', notification_type='received')
add_event('A-Day2', base_time + timedelta(minutes=540), 'exit_location', 'work')

# User B - Day 1: Multi-location active day with parallel activities
base_time = datetime(2024, 1, 1, 7, 0)
add_event('B-Day1', base_time, 'enter_location', 'home')
add_event('B-Day1', base_time + timedelta(minutes=30), 'physical_activity', 'home', 'light')
add_event('B-Day1', base_time + timedelta(minutes=60), 'notification', 'home', notification_type='received')
add_event('B-Day1', base_time + timedelta(minutes=60), 'self_report', 'home', stress_level=4)  # Parallel
add_event('B-Day1', base_time + timedelta(minutes=120), 'exit_location', 'home')
add_event('B-Day1', base_time + timedelta(minutes=150), 'enter_location', 'park')
add_event('B-Day1', base_time + timedelta(minutes=180), 'physical_activity', 'park', 'moderate')
add_event('B-Day1', base_time + timedelta(minutes=210), 'physical_activity', 'park', 'vigorous')
add_event('B-Day1', base_time + timedelta(minutes=240), 'notification', 'park', notification_type='received')
add_event('B-Day1', base_time + timedelta(minutes=241), 'self_report', 'park', stress_level=2)
add_event('B-Day1', base_time + timedelta(minutes=300), 'exit_location', 'park')
add_event('B-Day1', base_time + timedelta(minutes=360), 'enter_location', 'work')
add_event('B-Day1', base_time + timedelta(minutes=480), 'notification', 'work', notification_type='received')
add_event('B-Day1', base_time + timedelta(minutes=510), 'self_report', 'work', stress_level=5)
add_event('B-Day1', base_time + timedelta(minutes=660), 'exit_location', 'work')

# User C - Day 1: Non-compliant pattern
base_time = datetime(2024, 1, 1, 9, 0)
add_event('C-Day1', base_time, 'enter_location', 'work')
add_event('C-Day1', base_time + timedelta(minutes=60), 'notification', 'work', notification_type='received')
add_event('C-Day1', base_time + timedelta(minutes=120), 'notification', 'work', notification_type='received')
add_event('C-Day1', base_time + timedelta(minutes=180), 'notification', 'work', notification_type='received')
add_event('C-Day1', base_time + timedelta(minutes=300), 'physical_activity', 'work', 'light')
add_event('C-Day1', base_time + timedelta(minutes=480), 'exit_location', 'work')
# Note: No self-reports despite multiple notifications

# Convert to DataFrame
df = pd.DataFrame(event_data)
df['timestamp'] = pd.to_datetime(df['timestamp'])

print(f"📋 Event Log Created: {len(df)} events across {df['case_id'].nunique()} cases")
print(f"🏃 Event Types: {', '.join(df['event'].unique())}")
print(f"📍 Locations: {', '.join(df['location'].unique())}")

# Display sample of event log
print("\n📄 Sample Event Log:")
print(df.head(10).to_string(index=False))

# Display the full event log structure
print(f"\n📋 Complete Event Log Structure:")
print(f"Total Events: {len(df)}")
print(f"Unique Cases: {df['case_id'].nunique()}")
print(f"Event Types: {df['event'].nunique()}")
print(f"Locations: {df['location'].nunique()}")
print(f"Time Span: {df['timestamp'].min()} to {df['timestamp'].max()}")

# Show event type distribution
event_counts = df['event'].value_counts()
print(f"\n📊 Event Type Distribution:")
for event_type, count in event_counts.items():
    print(f"  {event_type}: {count} ({count/len(df)*100:.1f}%)")

# ## 2. Process Mining Analysis

if pm4py_available:
    # Convert to PM4Py event log format
    df_pm4py = df.copy()
    df_pm4py = df_pm4py.rename(columns={
        'case_id': 'case:concept:name',
        'event': 'concept:name',
        'timestamp': 'time:timestamp'
    })
    
    # Create event log
    event_log = log_converter.apply(df_pm4py)
    
    print(f"\n🔄 PM4Py Event Log Created: {len(event_log)} traces")
    
    # Discover Directly-Follows Graph
    dfg = dfg_discovery.apply(event_log)
    
    # Discover process model using Inductive Miner and convert to Petri net
    process_tree = inductive_miner.apply(event_log)
    net, initial_marking, final_marking = convert_to_petri_net(process_tree)
    
    print("\n📊 Process Discovery Complete")
    print("🔍 Directly-Follows Graph discovered with transition frequencies")
    print("🕸️ Petri Net model discovered using Inductive Miner")
    
    # Generate Petri Net visualization
    try:
        gviz = pn_visualizer.apply(net, initial_marking, final_marking)
        pn_visualizer.save(gviz, "petri_net_activity_stress.png")
        print("✅ Petri Net saved as 'petri_net_activity_stress.png'")
        
        # Also generate DFG visualization
        gviz_dfg = dfg_visualizer.apply(dfg, log=event_log, variant=dfg_visualizer.Variants.FREQUENCY)
        dfg_visualizer.save(gviz_dfg, "dfg_activity_stress.png")
        print("✅ Directly-Follows Graph saved as 'dfg_activity_stress.png'")
        
    except Exception as e:
        print(f"⚠️ Visualization generation failed: {e}")
        print("💡 This might be due to missing Graphviz installation")
        
    # Display basic statistics about the discovered model
    print(f"\n📈 Petri Net Statistics:")
    print(f"   Places: {len(net.places)}")
    print(f"   Transitions: {len(net.transitions)}")
    print(f"   Arcs: {len(net.arcs)}")
    
else:
    print("\n⚠️ Using alternative process analysis without PM4Py")
    
    # Create a simple process flow visualization using matplotlib
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    # Create a simplified process flow diagram
    process_steps = ['enter_location', 'physical_activity', 'notification', 'self_report', 'exit_location']
    locations = df['location'].unique()
    
    # Create a flow diagram showing the general process
    import matplotlib.patches as patches
    
    y_positions = {step: i for i, step in enumerate(process_steps)}
    x_positions = {loc: i for i, loc in enumerate(locations)}
    
    # Draw process boxes
    for step in process_steps:
        rect = patches.Rectangle((0, y_positions[step]-0.3), 3, 0.6, 
                               linewidth=1, edgecolor='blue', facecolor='lightblue', alpha=0.7)
        ax.add_patch(rect)
        ax.text(1.5, y_positions[step], step.replace('_', ' ').title(), 
                ha='center', va='center', fontweight='bold')
    
    # Draw arrows between steps
    for i in range(len(process_steps)-1):
        ax.annotate('', xy=(1.5, y_positions[process_steps[i+1]]+0.3), 
                   xytext=(1.5, y_positions[process_steps[i]]-0.3),
                   arrowprops=dict(arrowstyle='->', lw=2, color='red'))
    
    ax.set_xlim(-0.5, 8)
    ax.set_ylim(-0.5, len(process_steps)-0.5)
    ax.set_title('Simplified Process Flow (Alternative to Petri Net)', fontsize=14, fontweight='bold')
    ax.axis('off')
    
    # Add location context
    for i, loc in enumerate(locations):
        ax.text(5 + i*1.5, 2, loc.title(), ha='center', va='center', 
                bbox=dict(boxstyle="round,pad=0.3", facecolor='yellow', alpha=0.7),
                fontweight='bold')
    
    ax.text(6, -0.2, 'Context: Different locations affect process execution', 
            ha='center', va='center', style='italic')
    
# Add this section after the Petri Net generation to create a custom visualization
# ## 2.1 Custom Process Model Visualization

def create_custom_petri_net_visualization(df):
    """Create a custom Petri Net-style visualization of our process"""
    
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    
    # Define the process structure based on our event log
    places = ['Start', 'At_Location', 'Activity_Done', 'Notified', 'Reported', 'End']
    transitions = ['enter_location', 'physical_activity', 'notification', 'self_report', 'exit_location']
    
    # Position places (circles) and transitions (rectangles)
    place_positions = {
        'Start': (1, 5),
        'At_Location': (3, 5),
        'Activity_Done': (5, 6),
        'Notified': (5, 4),
        'Reported': (7, 5),
        'End': (9, 5)
    }
    
    transition_positions = {
        'enter_location': (2, 5),
        'physical_activity': (4, 6),
        'notification': (4, 4),
        'self_report': (6, 5),
        'exit_location': (8, 5)
    }
    
    # Draw places as circles
    for place, (x, y) in place_positions.items():
        circle = plt.Circle((x, y), 0.3, color='lightblue', ec='blue', linewidth=2)
        ax.add_patch(circle)
        ax.text(x, y, place.replace('_', '\n'), ha='center', va='center', 
                fontsize=8, fontweight='bold')
    
    # Draw transitions as rectangles
    for transition, (x, y) in transition_positions.items():
        rect = patches.Rectangle((x-0.4, y-0.2), 0.8, 0.4, 
                               linewidth=2, edgecolor='red', facecolor='lightcoral')
        ax.add_patch(rect)
        ax.text(x, y, transition.replace('_', '\n'), ha='center', va='center', 
                fontsize=7, fontweight='bold')
    
    # Draw arcs (arrows)
    arcs = [
        ('Start', 'enter_location'),
        ('enter_location', 'At_Location'),
        ('At_Location', 'physical_activity'),
        ('At_Location', 'notification'),
        ('physical_activity', 'Activity_Done'),
        ('notification', 'Notified'),
        ('Activity_Done', 'self_report'),
        ('Notified', 'self_report'),
        ('self_report', 'Reported'),
        ('Reported', 'exit_location'),
        ('exit_location', 'End')
    ]
    
    for source, target in arcs:
        if source in place_positions:
            x1, y1 = place_positions[source]
        else:
            x1, y1 = transition_positions[source]
            
        if target in place_positions:
            x2, y2 = place_positions[target]
        else:
            x2, y2 = transition_positions[target]
        
        # Calculate arrow positions to avoid overlap with shapes
        dx, dy = x2 - x1, y2 - y1
        length = np.sqrt(dx**2 + dy**2)
        if length > 0:
            dx_norm, dy_norm = dx/length, dy/length
            start_x, start_y = x1 + 0.3*dx_norm, y1 + 0.3*dy_norm
            end_x, end_y = x2 - 0.3*dx_norm, y2 - 0.3*dy_norm
            
            ax.annotate('', xy=(end_x, end_y), xytext=(start_x, start_y),
                       arrowprops=dict(arrowstyle='->', lw=1.5, color='black'))
    
    # Add parallel path indication
    ax.annotate('', xy=(4.5, 5.5), xytext=(4.5, 4.5),
               arrowprops=dict(arrowstyle='<->', lw=2, color='green'))
    ax.text(4.8, 5, 'Parallel\nPaths', ha='left', va='center', 
            fontsize=8, color='green', fontweight='bold')
    
    # Add location context boxes
    locations = ['Home', 'Gym', 'Work', 'Park']
    colors = ['lightgreen', 'orange', 'lightcoral', 'lightblue']
    
    for i, (loc, color) in enumerate(zip(locations, colors)):
        rect = patches.Rectangle((0.2, 7-i*0.6), 1.5, 0.4, 
                               linewidth=1, edgecolor='gray', facecolor=color, alpha=0.7)
        ax.add_patch(rect)
        ax.text(0.95, 7.2-i*0.6, f'{loc} Context', ha='center', va='center', 
                fontsize=8, fontweight='bold')
    
    ax.set_xlim(0, 10)
    ax.set_ylim(3, 8)
    ax.set_title('Custom Petri Net: Activity & Stress Monitoring Process\n(Shows Parallel Paths and Location Context)', 
                fontsize=14, fontweight='bold')
    ax.axis('off')
    
    # Add legend
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='lightblue', 
                  markersize=10, markeredgecolor='blue', label='Places (Process States)'),
        plt.Line2D([0], [0], marker='s', color='w', markerfacecolor='lightcoral', 
                  markersize=8, markeredgecolor='red', label='Transitions (Activities)'),
        plt.Line2D([0], [0], color='black', linewidth=2, label='Process Flow'),
        plt.Line2D([0], [0], color='green', linewidth=2, label='Parallel Execution')
    ]
    ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.98, 0.98))
    
    plt.tight_layout()
    plt.savefig('custom_petri_net_visualization.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return fig

# Generate the custom Petri Net visualization
custom_petri_fig = create_custom_petri_net_visualization(df)
print("✅ Custom Petri Net visualization saved as 'custom_petri_net_visualization.png'")

# ## 3. Process Mining Insights

def analyze_process_patterns(df):
    """Extract process-specific insights that other techniques would miss"""
    
    patterns = []
    
    # Group by case to analyze individual process instances
    for case_id in df['case_id'].unique():
        case_events = df[df['case_id'] == case_id].sort_values('timestamp')
        
        # Extract process pattern
        event_sequence = ' → '.join(case_events['event'].tolist())
        locations = case_events['location'].unique()
        
        # Calculate metrics
        notifications = len(case_events[case_events['event'] == 'notification'])
        self_reports = len(case_events[case_events['event'] == 'self_report'])
        activities = len(case_events[case_events['event'] == 'physical_activity'])
        
        compliance_rate = self_reports / notifications if notifications > 0 else 0
        avg_stress = case_events['stress_level'].mean()
        
        # Detect parallel activities (same timestamp)
        parallel_activities = case_events.groupby('timestamp').size().max() > 1
        
        patterns.append({
            'case_id': case_id,
            'process_pattern': event_sequence,
            'locations': list(locations),
            'compliance_rate': compliance_rate,
            'avg_stress': avg_stress,
            'notifications': notifications,
            'self_reports': self_reports,
            'activities': activities,
            'has_parallel_activities': parallel_activities,
            'process_duration': (case_events['timestamp'].max() - case_events['timestamp'].min()).total_seconds() / 3600
        })
    
    return pd.DataFrame(patterns)

process_patterns = analyze_process_patterns(df)

print("\n🎯 Process Mining Patterns Discovered:")
print("="*60)

for _, pattern in process_patterns.iterrows():
    print(f"\n📋 Case: {pattern['case_id']}")
    print(f"🔄 Process Flow: {pattern['process_pattern'][:100]}...")
    print(f"📍 Locations: {', '.join(pattern['locations'])}")
    print(f"✅ Compliance Rate: {pattern['compliance_rate']:.1%}")
    print(f"😰 Avg Stress: {pattern['avg_stress']:.1f}")
    print(f"⚡ Parallel Activities: {'Yes' if pattern['has_parallel_activities'] else 'No'}")
    print(f"⏱️ Duration: {pattern['process_duration']:.1f} hours")

# ## 4. Traditional Time Series Analysis

def create_time_series_view(df):
    """Show what traditional time series analysis would reveal"""
    
    # Aggregate by hour
    df['hour'] = df['timestamp'].dt.hour
    
    time_series = df.groupby('hour').agg({
        'stress_level': 'mean',
        'event': 'count'
    }).reset_index()
    
    time_series.columns = ['hour', 'avg_stress', 'event_count']
    
    # Add activity counts
    activity_counts = df[df['event'] == 'physical_activity'].groupby(
        df[df['event'] == 'physical_activity']['timestamp'].dt.hour
    ).size().reindex(range(24), fill_value=0)
    
    time_series = time_series.merge(
        activity_counts.reset_index().rename(columns={'timestamp': 'hour', 0: 'activity_count'}),
        on='hour', how='left'
    ).fillna(0)
    
    return time_series

time_series_data = create_time_series_view(df)

# Visualize time series
fig, axes = plt.subplots(2, 2, figsize=(15, 10))
fig.suptitle('Analytical Technique Comparison', fontsize=16, fontweight='bold')

# Time Series View
axes[0, 0].plot(time_series_data['hour'], time_series_data['avg_stress'], 'r-o', label='Avg Stress')
axes[0, 0].set_title('Time Series Analysis')
axes[0, 0].set_xlabel('Hour of Day')
axes[0, 0].set_ylabel('Average Stress Level')
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3)

# Activity Distribution
location_activity = df[df['event'] == 'physical_activity']['location'].value_counts()
axes[0, 1].bar(location_activity.index, location_activity.values, color='green', alpha=0.7)
axes[0, 1].set_title('Activity Distribution by Location')
axes[0, 1].set_xlabel('Location')
axes[0, 1].set_ylabel('Activity Count')

# Process Compliance by Location
compliance_by_location = df.groupby('location').apply(
    lambda x: len(x[x['event'] == 'self_report']) / max(len(x[x['event'] == 'notification']), 1)
).reset_index()
compliance_by_location.columns = ['location', 'compliance_rate']

axes[1, 0].bar(compliance_by_location['location'], compliance_by_location['compliance_rate'], 
               color='blue', alpha=0.7)
axes[1, 0].set_title('Process Mining: Compliance by Location')
axes[1, 0].set_xlabel('Location')
axes[1, 0].set_ylabel('Compliance Rate')
axes[1, 0].set_ylim(0, 1)

# Stress by Process Pattern
stress_by_case = process_patterns[['case_id', 'avg_stress', 'locations']].dropna()
stress_by_case['location_type'] = stress_by_case['locations'].apply(
    lambda x: 'work' if 'work' in x else ('gym' if 'gym' in x else 'home/park')
)

sns.boxplot(data=stress_by_case, x='location_type', y='avg_stress', ax=axes[1, 1])
axes[1, 1].set_title('Stress Levels by Process Context')
axes[1, 1].set_xlabel('Primary Location Context')
axes[1, 1].set_ylabel('Average Stress Level')

plt.tight_layout()
plt.show()

# ## 5. Sequential Pattern Mining Simulation

def find_sequential_patterns(df, min_support=0.3):
    """Simulate sequential pattern mining results"""
    
    patterns = {}
    
    # Extract sequences for each case
    for case_id in df['case_id'].unique():
        case_events = df[df['case_id'] == case_id].sort_values('timestamp')
        events = case_events['event'].tolist()
        
        # Generate 2-grams and 3-grams
        for i in range(len(events)-1):
            pattern = f"{events[i]} → {events[i+1]}"
            patterns[pattern] = patterns.get(pattern, 0) + 1
            
            if i < len(events)-2:
                pattern_3 = f"{events[i]} → {events[i+1]} → {events[i+2]}"
                patterns[pattern_3] = patterns.get(pattern_3, 0) + 1
    
    # Calculate support
    total_cases = df['case_id'].nunique()
    frequent_patterns = {
        pattern: count/total_cases 
        for pattern, count in patterns.items() 
        if count/total_cases >= min_support
    }
    
    return frequent_patterns

sequential_patterns = find_sequential_patterns(df)

print("\n🔗 Sequential Pattern Mining Results:")
print("="*50)
for pattern, support in sorted(sequential_patterns.items(), key=lambda x: x[1], reverse=True):
    print(f"Pattern: {pattern}")
    print(f"Support: {support:.1%}\n")

# ## 6. Comparative Analysis Summary

print("\n📊 COMPARATIVE ANALYSIS SUMMARY")
print("="*70)

print("\n🎯 PROCESS MINING UNIQUE INSIGHTS:")
print("-" * 40)
print("✅ Complete process flows with branching logic")
print("✅ Contextual behavioral variants by location")
print("✅ Individual compliance patterns and deviations")
print("✅ Parallel activity detection and analysis")
print("✅ End-to-end process performance metrics")
print("✅ Resource-specific behavioral patterns")

print("\n📈 TIME SERIES ANALYSIS LIMITATIONS:")
print("-" * 45)
print("❌ No process flow or sequence information")
print("❌ Cannot identify behavioral variants")
print("❌ Missing causal relationships")
print("❌ Aggregate view obscures individual patterns")
print("❌ No compliance or conformance analysis")

print("\n🔗 SEQUENTIAL MINING LIMITATIONS:")
print("-" * 42)
print("❌ No branching logic or conditional paths")
print("❌ Limited contextual integration")
print("❌ Cannot handle parallel activities")
print("❌ No resource or case-level analysis")
print("❌ Missing process variants identification")

print("\n🏆 KEY PROCESS MINING ADVANTAGES FOR THIS CASE:")
print("-" * 55)
print("1. 🏠 Location Context Integration: Shows how physical environment")
print("   affects entire behavioral process, not just individual activities")
print("\n2. 🔄 Behavioral Variant Discovery: Identifies that same user follows")
print("   completely different patterns based on location context")
print("\n3. ✅ Compliance Analysis: Reveals WHERE and WHY users deviate")
print("   from intended self-monitoring behaviors")
print("\n4. ⚡ Parallel Execution Detection: Identifies users who can handle")
print("   simultaneous activities vs. those requiring sequential approach")
print("\n5. 🎯 Holistic Process Intelligence: Links environmental factors")
print("   to complete process execution patterns, enabling targeted interventions")

# ## 7. Actionable Insights from Process Mining

print("\n💡 ACTIONABLE INSIGHTS FROM PROCESS MINING:")
print("="*55)

print("\n🏢 Work Environment Intervention Needed:")
print("   - Work location disrupts self-monitoring compliance")
print("   - Consider workplace-specific notification strategies")
print("   - Higher stress levels correlate with poor process adherence")

print("\n🏃‍♂️ Exercise Locations Optimize Behavior:")
print("   - Gym and park locations show highest compliance rates")
print("   - Exercise activities correlate with lower stress AND better reporting")
print("   - Consider promoting outdoor/gym activities for dual benefits")

print("\n👤 Individual Process Patterns:")
print("   - User A: Location-dependent compliance (good at home/gym, poor at work)")
print("   - User B: Capable of parallel activities, highly adaptable")
print("   - User C: Generally non-compliant, needs different intervention approach")

print("\n🎯 Process Optimization Recommendations:")
print("   - Implement location-aware notification timing")
print("   - Design parallel activity support for capable users")
print("   - Create work-specific stress management protocols")
print("   - Use exercise promotion as dual intervention strategy")

print("\n" + "="*70)
print("📋 Analysis Complete - Process Mining provides comprehensive")
print("   behavioral insights impossible with traditional techniques!")
print("="*70)