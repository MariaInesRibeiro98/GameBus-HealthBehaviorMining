"""
Enhanced Colored Petri Net for Health Behavior Analysis
This implementation creates a colored Petri net that captures concurrent states of:
- Physical activity (sedentary, light, moderate, vigorous)
- Notifications (none, pending, read)
- Stress levels (low, medium, high)
- Locations (home, work, gym, park, other)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Process mining libraries
try:
    import pm4py
    from pm4py.objects.petri_net.obj import PetriNet, Marking
    from pm4py.objects.petri_net.utils import petri_utils
    from pm4py.visualization.petri_net import visualizer as pn_visualizer
    pm4py_available = True
    print("✅ PM4Py library available - Full process mining analysis enabled")
except ImportError:
    pm4py_available = False
    print("⚠️ PM4Py not available - Using alternative visualization methods")

def create_enhanced_petri_net():
    """Create an enhanced colored Petri net for health behavior analysis"""
    
    # Create a new Petri net
    net = PetriNet("enhanced_health_behavior_net")
    
    # Create places for different states
    places = {}
    
    # Physical activity states
    activity_states = ['sedentary', 'active_light', 'active_moderate', 'active_vigorous']
    for state in activity_states:
        places[f'activity_{state}'] = PetriNet.Place(f'activity_{state}')
        net.places.add(places[f'activity_{state}'])
    
    # Notification states
    notification_states = ['no_notification', 'notification_pending', 'notification_read']
    for state in notification_states:
        places[f'notification_{state}'] = PetriNet.Place(f'notification_{state}')
        net.places.add(places[f'notification_{state}'])
    
    # Stress states
    stress_states = ['stress_low', 'stress_medium', 'stress_high']
    for state in stress_states:
        places[state] = PetriNet.Place(state)
        net.places.add(places[state])
    
    # Location states
    location_states = ['at_home', 'at_work', 'at_gym', 'at_park', 'at_other']
    for state in location_states:
        places[state] = PetriNet.Place(state)
        net.places.add(places[state])
    
    # Create transitions for different event types
    transitions = {}
    
    # Physical activity transitions
    activity_transitions = [
        ('start_activity_light', 'sedentary', 'active_light'),
        ('end_activity_light', 'active_light', 'sedentary'),
        ('start_activity_moderate', 'sedentary', 'active_moderate'),
        ('end_activity_moderate', 'active_moderate', 'sedentary'),
        ('start_activity_vigorous', 'sedentary', 'active_vigorous'),
        ('end_activity_vigorous', 'active_vigorous', 'sedentary')
    ]
    
    for trans_name, from_state, to_state in activity_transitions:
        transitions[trans_name] = PetriNet.Transition(trans_name, trans_name)
        net.transitions.add(transitions[trans_name])
        petri_utils.add_arc_from_to(places[f'activity_{from_state}'], transitions[trans_name], net)
        petri_utils.add_arc_from_to(transitions[trans_name], places[f'activity_{to_state}'], net)
    
    # Notification transitions
    notification_transitions = [
        ('receive_notification', 'no_notification', 'notification_pending'),
        ('read_notification', 'notification_pending', 'notification_read'),
        ('clear_notification', 'notification_read', 'no_notification')
    ]
    
    for trans_name, from_state, to_state in notification_transitions:
        transitions[trans_name] = PetriNet.Transition(trans_name, trans_name)
        net.transitions.add(transitions[trans_name])
        petri_utils.add_arc_from_to(places[f'notification_{from_state}'], transitions[trans_name], net)
        petri_utils.add_arc_from_to(transitions[trans_name], places[f'notification_{to_state}'], net)
    
    # Stress reporting transitions with activity influence
    for stress_level in ['low', 'medium', 'high']:
        # Regular stress reporting
        trans_name = f'report_stress_{stress_level}'
        transitions[trans_name] = PetriNet.Transition(trans_name, trans_name)
        net.transitions.add(transitions[trans_name])
        
        # Add arcs from all stress states to allow any stress level reporting
        for from_stress in stress_states:
            petri_utils.add_arc_from_to(places[from_stress], transitions[trans_name], net)
        petri_utils.add_arc_from_to(transitions[trans_name], places[f'stress_{stress_level}'], net)
        
        # Add influence of physical activity on stress reporting
        # When active, higher chance of lower stress reports
        if stress_level == 'low':
            for activity_state in ['active_light', 'active_moderate', 'active_vigorous']:
                petri_utils.add_arc_from_to(places[f'activity_{activity_state}'], transitions[trans_name], net)
                petri_utils.add_arc_from_to(transitions[trans_name], places[f'activity_{activity_state}'], net)
    
    # Location transitions
    for loc in ['home', 'work', 'gym', 'park', 'other']:
        # Enter location
        enter_trans = f'enter_{loc}'
        transitions[enter_trans] = PetriNet.Transition(enter_trans, enter_trans)
        net.transitions.add(transitions[enter_trans])
        
        # Exit location
        exit_trans = f'exit_{loc}'
        transitions[exit_trans] = PetriNet.Transition(exit_trans, exit_trans)
        net.transitions.add(transitions[exit_trans])
        
        # Add arcs for location changes
        for other_loc in location_states:
            if other_loc != f'at_{loc}':
                petri_utils.add_arc_from_to(places[other_loc], transitions[enter_trans], net)
        petri_utils.add_arc_from_to(transitions[enter_trans], places[f'at_{loc}'], net)
        petri_utils.add_arc_from_to(places[f'at_{loc}'], transitions[exit_trans], net)
    
    # Create initial marking
    initial_marking = Marking()
    initial_marking[places['activity_sedentary']] = 1
    initial_marking[places['notification_no_notification']] = 1
    initial_marking[places['stress_medium']] = 1
    initial_marking[places['at_home']] = 1
    
    # Create final marking (empty)
    final_marking = Marking()
    for place in places.values():
        final_marking[place] = 0
    
    return net, initial_marking, final_marking, places, transitions

def visualize_enhanced_petri_net(net, initial_marking, final_marking):
    """Visualize the enhanced Petri net"""
    
    parameters = {
        pn_visualizer.Variants.WO_DECORATION.value.Parameters.FORMAT: "png",
        pn_visualizer.Variants.WO_DECORATION.value.Parameters.DEBUG: False,
        pn_visualizer.Variants.WO_DECORATION.value.Parameters.RANKDIR: "TB",
        pn_visualizer.Variants.WO_DECORATION.value.Parameters.SET_LINEWIDTH: 2.0
    }
    
    gviz = pn_visualizer.apply(net, initial_marking, final_marking, parameters=parameters)
    pn_visualizer.save(gviz, "enhanced_petri_net.png")
    
    print("\nEnhanced Petri Net Statistics:")
    print(f"Places: {len(net.places)}")
    print(f"Transitions: {len(net.transitions)}")
    print(f"Arcs: {len(net.arcs)}")

def analyze_activity_stress_relationship(event_log_df):
    """Analyze how physical activity affects stress reporting"""
    
    # Group by case and analyze stress reports after physical activity
    activity_stress_effects = []
    
    for case_id in event_log_df['case_id'].unique():
        case_events = event_log_df[event_log_df['case_id'] == case_id].sort_values('timestamp')
        
        # Find physical activity events and subsequent stress reports
        for i, event in case_events.iterrows():
            if event['event_type'] == 'physical_activity' and event['lifecycle'] == 'END':
                # Look for stress reports within 30 minutes after activity
                activity_time = event['timestamp']
                activity_type = event['bout_type']
                
                # Find next stress report
                next_stress = case_events[
                    (case_events['event_type'] == 'self_report') & 
                    (case_events['timestamp'] > activity_time) &
                    (case_events['timestamp'] <= activity_time + pd.Timedelta(minutes=30))
                ]
                
                if not next_stress.empty:
                    activity_stress_effects.append({
                        'case_id': case_id,
                        'activity_type': activity_type,
                        'stress_level': next_stress.iloc[0]['stress_level'],
                        'time_diff_minutes': (next_stress.iloc[0]['timestamp'] - activity_time).total_seconds() / 60
                    })
    
    # Convert to DataFrame and analyze
    if activity_stress_effects:
        effects_df = pd.DataFrame(activity_stress_effects)
        
        # Calculate average stress level by activity type
        stress_by_activity = effects_df.groupby('activity_type')['stress_level'].agg(['mean', 'count'])
        print("\nEffect of Physical Activity on Stress Levels:")
        print(stress_by_activity)
        
        # Visualize the relationship
        plt.figure(figsize=(10, 6))
        sns.boxplot(data=effects_df, x='activity_type', y='stress_level')
        plt.title('Stress Levels After Different Types of Physical Activity')
        plt.xlabel('Activity Type')
        plt.ylabel('Reported Stress Level')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('activity_stress_relationship.png')
        plt.show()
        
        return effects_df
    else:
        print("No stress reports found within 30 minutes of physical activity")
        return None

if __name__ == "__main__":
    # Create and visualize the enhanced Petri net
    net, initial_marking, final_marking, places, transitions = create_enhanced_petri_net()
    visualize_enhanced_petri_net(net, initial_marking, final_marking)
    
    # Load and analyze event log data
    try:
        event_log_df = pd.read_json('notebooks/2d_toy_event_log.json')
        activity_stress_effects = analyze_activity_stress_relationship(event_log_df)
    except FileNotFoundError:
        print("Event log file not found. Skipping activity-stress analysis.") 