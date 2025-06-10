from typing import Dict, List, Set, Tuple, Any, Optional
import pandas as pd
import numpy as np
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.log.obj import EventLog
import networkx as nx
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.preprocessing import LabelEncoder
from collections import defaultdict

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
        
        # Store mined decision trees for choice points
        self.decision_trees: Dict[str, Dict[str, Any]] = {}
        
    def _convert_log_to_dataframe(self) -> pd.DataFrame:
        """
        Convert the event log to a pandas DataFrame for easier analysis.
        
        Returns:
            pd.DataFrame: The event log as a DataFrame
        """
        log_list = []
        for trace in self.event_log:
            for event in trace:
                # Convert event to dictionary, handling both dict and object cases
                if isinstance(event, dict):
                    event_dict = event
                else:
                    event_dict = dict(event)
                log_list.append(event_dict)
        return pd.DataFrame(log_list)
    
    def detect_choice_points(self) -> None:
        """
        Detect choice points (places with multiple outgoing transitions) in the Petri net.
        """
        print("\n=== Detecting Choice Points ===")
        print("All transitions in net:")
        for t in self.net.transitions:
            print(f"  - {t.name} (label: {getattr(t, 'label', None)})")
            
        print("\nAll places in net:")
        for p in self.net.places:
            print(f"  - {p.name}")
            print("    Outgoing arcs:")
            for arc in p.out_arcs:
                print(f"      -> {arc.target.name} (label: {getattr(arc.target, 'label', None)})")
            print("    Incoming arcs:")
            for arc in p.in_arcs:
                print(f"      <- {arc.source.name} (label: {getattr(arc.source, 'label', None)})")
        
        # Reset choice points
        self.choice_points = {}
        
        # Find places with multiple outgoing transitions
        for place in self.net.places:
            # Get all outgoing transitions
            outgoing_transitions = set(arc.target for arc in place.out_arcs)
            
            print(f"\nAnalyzing place {place.name}:")
            print(f"  Number of outgoing transitions: {len(outgoing_transitions)}")
            print("  Outgoing transitions:")
            for t in outgoing_transitions:
                print(f"    - {t.name} (label: {getattr(t, 'label', None)})")
            
            # If there are multiple outgoing transitions, it's a choice point
            if len(outgoing_transitions) > 1:
                print(f"  -> This is a choice point!")
                self.choice_points[place] = outgoing_transitions
            else:
                print("  -> Not a choice point")
        
        print("\nFinal choice points found:")
        for place, transitions in self.choice_points.items():
            print(f"\nPlace: {place.name}")
            print("Transitions:")
            for t in transitions:
                print(f"  - {t.name} (label: {getattr(t, 'label', None)})")

    def get_choice_point_names(self) -> List[str]:
        """
        Get a list of all choice point names in the Petri net.

        Returns:
            List[str]: List of choice point names
        """
        if not self.choice_points:
            self.detect_choice_points()
        return [place.name for place in self.choice_points.keys()]

    def mine_decision_tree(self, 
                          place_name: str, 
                          attributes: List[str],
                          max_depth: int = 5,
                          min_samples_split: int = 2) -> None:
        """
        Mine a decision tree for a specific choice point using selected attributes.
        Handles categorical attributes by encoding them.
        
        Args:
            place_name: Name of the place to mine decision tree for
            attributes: List of attribute names to use as features
            max_depth: Maximum depth of the decision tree
            min_samples_split: Minimum number of samples required to split a node
        """
        print("\n=== Mining Decision Tree ===")
        print(f"Place: {place_name}")
        print(f"Attributes: {attributes}")
        
        # Find the place object by name
        target_place = None
        for place in self.choice_points.keys():
            if place.name == place_name:
                target_place = place
                break
                
        if target_place is None:
            available_places = [p.name for p in self.choice_points.keys()]
            print(f"Error: Place '{place_name}' not found. Available places: {available_places}")
            return
            
        transitions = self.choice_points[target_place]
        print(f"\nFound {len(transitions)} transitions for this choice point:")
        for trans in transitions:
            print(f"  - {trans.name} (label: {getattr(trans, 'label', 'no label')})")
        
        # Get traces and their chosen transitions
        trace_data, chosen_transitions = self._find_traces_for_choice_point(
            place_name, transitions, attributes
        )
        
        if not trace_data:
            print("\nError: No valid traces found for decision tree mining")
            return
            
        print(f"\nFound {len(trace_data)} valid traces for decision tree")
        
        # Prepare data for decision tree
        from sklearn.preprocessing import LabelEncoder
        import numpy as np
        
        # Create label encoders for each categorical attribute
        attribute_encoders = {attr: LabelEncoder() for attr in attributes}
        
        # Prepare feature matrix X
        X = []
        for data in trace_data:
            features = []
            for attr in attributes:
                value = str(data[attr])  # Convert to string to handle any type
                # Fit and transform the value
                encoded_value = attribute_encoders[attr].fit_transform([value])[0]
                features.append(encoded_value)
            X.append(features)
        X = np.array(X)
        
        # Get transition labels for encoding
        transition_labels = []
        for trans in chosen_transitions:
            # Find the transition object
            for t in transitions:
                if t.name == trans:
                    label = getattr(t, 'label', t.name)  # Use label if exists, otherwise use name
                    transition_labels.append(label)
                    break
        
        # Encode target transitions using their labels
        transition_encoder = LabelEncoder()
        y = transition_encoder.fit_transform(transition_labels)
        
        print("\nTraining data summary:")
        print(f"Number of samples: {len(X)}")
        print(f"Number of features: {len(attributes)}")
        print(f"Number of classes: {len(transition_encoder.classes_)}")

        print("X:")
        print(X)

        print("y:")
        print(y)

        print("attributes:")
        print(attributes)
        
        # Print encoding information for each attribute
        print("\nAttribute encodings:")
        for attr in attributes:
            print(f"\n{attr}:")
            for i, label in enumerate(attribute_encoders[attr].classes_):
                print(f"  {label} -> {i}")
                
        print("\nTransition encodings (by label):")
        for i, label in enumerate(transition_encoder.classes_):
            print(f"  {label} -> {i}")
        
        # Print class distribution
        from collections import Counter
        class_counts = Counter(transition_labels)
        print("\nClass distribution:")
        for label, count in class_counts.items():
            print(f"  {label}: {count} samples ({count/len(y)*100:.1f}%)")
        
        # Create and train the classifier
        from sklearn.tree import DecisionTreeClassifier
        clf = DecisionTreeClassifier(
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            random_state=42
        )
        clf.fit(X, y)
        
        # Print tree structure with original labels
        print("\nDecision Tree Structure:")
        from sklearn.tree import export_text
        
        # Create feature names that include the encoding information
        feature_names = []
        for attr in attributes:
            encoding_info = [f"{label}->{i}" for i, label in enumerate(attribute_encoders[attr].classes_)]
            feature_names.append(f"{attr} ({', '.join(encoding_info)})")
            
        tree_text = export_text(clf, feature_names=feature_names)
        print(tree_text)
        
        # Print feature importances
        print("\nFeature Importances:")
        for attr, importance in zip(attributes, clf.feature_importances_):
            print(f"  {attr}: {importance:.3f}")
            
        # Print classification metrics
        from sklearn.metrics import classification_report
        y_pred = clf.predict(X)
        print("\nClassification Report:")
        print(classification_report(y, y_pred, 
                                  target_names=transition_encoder.classes_,
                                  digits=3))
        
        # Store results
        self.decision_trees[place_name] = {
            'classifier': clf,
            'transition_encoder': transition_encoder,
            'attribute_encoders': attribute_encoders,
            'attributes': attributes,
            'transitions': list(transitions),
            'feature_importances': dict(zip(attributes, clf.feature_importances_)),
            'class_distribution': dict(class_counts)
        }
        
        print("\nDecision tree mining completed successfully!")
    
    def get_decision_tree_rules(self, place_name: str) -> str:
        """
        Get the decision rules for a specific choice point in a readable format.
        
        Args:
            place_name: Name of the place to get rules for
            
        Returns:
            String containing the decision rules
        """
        if place_name not in self.decision_trees:
            print(f"Error: No decision tree found for place {place_name}")
            return ""
            
        tree_info = self.decision_trees[place_name]
        clf = tree_info['classifier']
        attribute_encoders = tree_info['attribute_encoders']
        transition_encoder = tree_info['transition_encoder']
        attributes = tree_info['attributes']
        
        # Get the tree structure
        from sklearn.tree import export_text
        
        # Create feature names that include the encoding information
        feature_names = []
        for attr in attributes:
            encoding_info = [f"{label}->{i}" for i, label in enumerate(attribute_encoders[attr].classes_)]
            feature_names.append(f"{attr} ({', '.join(encoding_info)})")
            
        # Get tree text and replace class numbers with transition labels
        tree_text = export_text(clf, feature_names=feature_names)
        
        # Replace class numbers with transition labels
        for i, label in enumerate(transition_encoder.classes_):
            tree_text = tree_text.replace(f"class: {i}", f"class: {label}")
        
        # Add a header with encoding information
        rules = ["Decision Rules for " + place_name + ":\n"]
        rules.append("Attribute Encodings:")
        for attr in attributes:
            rules.append(f"\n{attr}:")
            for i, label in enumerate(attribute_encoders[attr].classes_):
                rules.append(f"  {label} -> {i}")
                
        rules.append("\nTransition Encodings (by label):")
        for i, label in enumerate(transition_encoder.classes_):
            rules.append(f"  {label} -> {i}")
            
        rules.append("\nDecision Tree Structure:")
        rules.append(tree_text)
        
        # Add feature importances
        rules.append("\nFeature Importances:")
        for attr, importance in tree_info['feature_importances'].items():
            rules.append(f"  {attr}: {importance:.3f}")
            
        # Add class distribution
        rules.append("\nClass Distribution:")
        total = sum(tree_info['class_distribution'].values())
        for label, count in tree_info['class_distribution'].items():
            rules.append(f"  {label}: {count} samples ({count/total*100:.1f}%)")
            
        return "\n".join(rules)

    def print_decision_rules(self, place_name: str) -> None:
        """
        Print the decision rules for a specific choice point.
        
        Args:
            place_name: Name of the place to print rules for
        """
        rules = self.get_decision_tree_rules(place_name)
        if rules:
            print(rules)
    
    def get_feature_importances(self, place_name: str) -> Dict[str, float]:
        """
        Get the feature importances for a specific choice point.

        Args:
            place_name (str): Name of the place (choice point)

        Returns:
            Dict[str, float]: Dictionary mapping attribute names to their importance scores
        """
        if place_name not in self.decision_trees:
            raise ValueError(f"No decision tree found for place '{place_name}'")
            
        return self.decision_trees[place_name]['feature_importances']
    
    def predict_transition(self, 
                         place_name: str, 
                         attribute_values: Dict[str, Any]) -> str:
        """
        Predict which transition will be taken at a choice point based on attribute values.

        Args:
            place_name (str): Name of the place (choice point)
            attribute_values (Dict[str, Any]): Dictionary mapping attribute names to their values

        Returns:
            str: Name of the predicted transition
        """
        if place_name not in self.decision_trees:
            raise ValueError(f"No decision tree found for place '{place_name}'")
            
        tree_info = self.decision_trees[place_name]
        model = tree_info['model']
        attributes = tree_info['attributes']
        label_encoders = tree_info['label_encoders']
        transition_names = tree_info['transition_names']
        
        # Prepare the input features
        X = []
        for attr in attributes:
            value = attribute_values.get(attr)
            if value is None:
                raise ValueError(f"Missing value for attribute '{attr}'")
                
            # Encode categorical values if needed
            if attr in label_encoders:
                value = label_encoders[attr].transform([value])[0]
            X.append(value)
            
        # Make prediction
        prediction = model.predict([X])[0]
        return transition_names[prediction]

    def _find_traces_for_choice_point(self, 
                                    place_name: str, 
                                    transitions: Set[PetriNet.Transition],
                                    attributes: List[str]) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Find traces that pass through a specific choice point and their chosen transitions.
        
        For each trace, we:
        1. Find when we reach our target place (by looking at incoming arcs to transitions)
        2. Record the state (attributes) at that point
        3. Record which transition was taken from that place
        """
        print("\n=== Finding Traces for Choice Point ===")
        print(f"Looking for traces at place: {place_name}")
        
        # First, get all transitions that can be taken FROM this place
        target_place = None
        for place in self.net.places:
            if place.name == place_name:
                target_place = place
                break
                
        if target_place is None:
            raise ValueError(f"Place '{place_name}' not found")
            
        # Get all transitions that can be taken from this place, using their labels
        outgoing_transitions = {}
        for arc in target_place.out_arcs:
            trans = arc.target
            label = getattr(trans, 'label', None)
            if label is None:
                label = trans.name  # Use name if no label
            print(f"  Transition: {trans.name}")
            print(f"    Label: {label}")
            outgoing_transitions[label] = trans
            
        print("\nTransitions that can be taken from this place (by label):")
        for label, trans in outgoing_transitions.items():
            print(f"  - {label} (transition: {trans.name})")
        
        # Store the data for each trace
        trace_data = []  # Will store the state (attributes) when we reach the place
        chosen_transitions = []  # Will store which transition was taken
        
        # Process each trace
        for trace_idx, trace in enumerate(self.event_log):
            print(f"\nProcessing trace {trace_idx + 1}")
            print(f"Number of events: {len(trace)}")
            
            # For each event in the trace
            for i, event in enumerate(trace):
                # Get event name using get()
                event_name = event.get('concept:name', '')
                print(f"\n  Checking event {i}: {event_name}")
                
                # Check if this event matches any of our transition labels
                if event_name in outgoing_transitions:
                    trans = outgoing_transitions[event_name]
                    print(f"    Found a transition from our place: {trans.name} (label: {event_name})")
                    
                    # Get the state (attributes) at this point
                    state = {}
                    for attr in attributes:
                        value = event.get(attr, None)
                        print(f"    Attribute {attr}: {value}")
                        state[attr] = value
                    
                    # For single-event traces, this is the only transition
                    if len(trace) == 1:
                        print("    Single-event trace - using this transition")
                        trace_data.append(state)
                        chosen_transitions.append(trans.name)  # Store the transition name, not label
                        break
                    
                    # For multi-event traces, this transition was taken from our place
                    print("    Multi-event trace - this transition was taken from our place")
                    trace_data.append(state)
                    chosen_transitions.append(trans.name)  # Store the transition name, not label
                    break  # We found our transition, no need to look further in this trace
        
        print(f"\nFound {len(trace_data)} instances where a transition was taken from {place_name}")
        if trace_data:
            print("\nSample of found data:")
            for i, (state, trans) in enumerate(zip(trace_data[:3], chosen_transitions[:3])):
                print(f"\nInstance {i + 1}:")
                print(f"  State: {state}")
                print(f"  Chosen transition: {trans}")
        
        return trace_data, chosen_transitions 

    def set_transition_label(self, transition_name: str, new_label: str) -> None:
        """
        Set or modify the label of a transition in the Petri net.
        
        Args:
            transition_name: Name of the transition to modify
            new_label: New label to set for the transition
        """
        for trans in self.net.transitions:
            if trans.name == transition_name:
                trans.label = new_label
                print(f"Set label '{new_label}' for transition {transition_name}")
                return
        print(f"Warning: Transition {transition_name} not found in net")

    def print_transition_labels(self) -> None:
        """
        Print all transitions and their current labels in the net.
        """
        print("\nCurrent transition labels in net:")
        for trans in self.net.transitions:
            label = getattr(trans, 'label', None)
            print(f"Transition: {trans.name}")
            print(f"  Label: {label if label else '(no label)'}") 