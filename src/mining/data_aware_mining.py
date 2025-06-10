from typing import Dict, List, Set, Tuple, Any
import pandas as pd
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.log.obj import EventLog
import networkx as nx

class DataAwareProcessMining:
    """
    A class for implementing data-aware process mining techniques, focusing on decision rule discovery
    and choice pattern labeling in Petri nets.
    """
    
    def __init__(self, 
                 net: PetriNet,
                 initial_marking: Marking,
                 final_marking: Marking,
                 event_log: EventLog):
        """
        Initialize the DataAwareProcessMining class.

        Args:
            net (PetriNet): The discovered Petri net
            initial_marking (Marking): The initial marking of the Petri net
            final_marking (Marking): The final marking of the Petri net
            event_log (EventLog): The event log used for mining
        """
        self.net = net
        self.initial_marking = initial_marking
        self.final_marking = final_marking
        self.event_log = event_log
        
        # Convert event log to DataFrame for easier data analysis
        self.log_df = self._convert_log_to_dataframe()
        
        # Store choice points and their associated transitions
        self.choice_points: Dict[PetriNet.Place, Set[PetriNet.Transition]] = {}
        
    def _convert_log_to_dataframe(self) -> pd.DataFrame:
        """
        Convert the event log to a pandas DataFrame for easier analysis.
        
        Returns:
            pd.DataFrame: The event log as a DataFrame
        """
        # Implementation will depend on the structure of your event log
        # This is a placeholder that should be adapted based on your log format
        log_list = []
        for trace in self.event_log:
            for event in trace:
                log_list.append(dict(event))
        return pd.DataFrame(log_list)
    
    def detect_choice_points(self) -> Dict[PetriNet.Place, Set[PetriNet.Transition]]:
        """
        Automatically identify decision points (choice points) in the Petri net.
        A choice point is a place that has multiple outgoing transitions.

        Returns:
            Dict[PetriNet.Place, Set[PetriNet.Transition]]: Dictionary mapping places to their outgoing transitions
        """
        self.choice_points = {}
        
        # Iterate through all places in the net
        for place in self.net.places:
            # Get all outgoing transitions for this place
            outgoing_transitions = set()
            for arc in place.out_arcs:
                outgoing_transitions.add(arc.target)
            
            # If a place has more than one outgoing transition, it's a choice point
            if len(outgoing_transitions) > 1:
                self.choice_points[place] = outgoing_transitions
        
        return self.choice_points
    
    def get_choice_point_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the detected choice points.

        Returns:
            Dict[str, Any]: Dictionary containing statistics about choice points
        """
        if not self.choice_points:
            self.detect_choice_points()
            
        stats = {
            'total_choice_points': len(self.choice_points),
            'choice_points_details': {}
        }
        
        for place, transitions in self.choice_points.items():
            stats['choice_points_details'][place.name] = {
                'number_of_choices': len(transitions),
                'transition_names': [t.name for t in transitions]
            }
            
        return stats 