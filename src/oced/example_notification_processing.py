import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any
from .notification_events import NotificationEventManager

def load_oced_data(filepath: str) -> Dict[str, Any]:
    """
    Load OCED data from a JSON file.
    
    Args:
        filepath (str): Path to the OCED JSON file
        
    Returns:
        Dict[str, Any]: The loaded OCED data
    """
    with open(filepath, 'r') as f:
        return json.load(f)

def process_notifications(
    input_file: str,
    output_file: str,
    user_id: str,
    compress: bool = False
) -> None:
    """
    Process notification events from OCED data and create notification objects.
    
    Args:
        input_file (str): Path to input OCED JSON file
        output_file (str): Name of output file (will be saved in data/transformed)
        user_id (str): ID of the user to process notifications for
        compress (bool): Whether to compress the output file
    """
    # Initialize the notification manager
    notification_manager = NotificationEventManager()
    
    # Load the OCED data
    print(f"Loading OCED data from: {input_file}")
    oced_data = load_oced_data(input_file)
    
    # Add notification object type to the data
    print("Adding notification object type...")
    oced_data = notification_manager.create_notification_object_type(oced_data)
    
    # Create notification objects and link events
    print("Creating notification objects and linking events...")
    extended_data, notification_objects = notification_manager.create_notification_objects(
        data=oced_data,
        user_id=user_id
    )
    
    # Print some statistics
    print("\nNotification Processing Summary:")
    print(f"Total notification objects created: {len(notification_objects)}")
    
    # Count notifications by last action
    action_counts = {}
    for obj in notification_objects:
        last_action = next(
            (attr['value'] for attr in obj['attributes'] 
             if attr['name'] == 'last_action'),
            None
        )
        action_counts[last_action] = action_counts.get(last_action, 0) + 1
    
    print("\nNotifications by last action:")
    for action, count in action_counts.items():
        print(f"- {action}: {count}")
    
    # Save the extended data
    print("\nSaving extended data...")
    notification_manager.save_extended_data(
        filename=output_file,
        extended_data=extended_data,
        compress=compress
    )

def main():
    """Example usage of the notification processing functionality."""
    # Example file paths - adjust these to match your data location
    input_file = "data/raw/oced_data.json"
    output_file = "notifications_processed.json"
    user_id = "user_123"  # Replace with actual user ID
    
    try:
        process_notifications(
            input_file=input_file,
            output_file=output_file,
            user_id=user_id,
            compress=False  # Set to True if you want compressed output
        )
        print("\nNotification processing completed successfully!")
        
    except FileNotFoundError as e:
        print(f"Error: Could not find input file - {e}")
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file - {e}")
    except Exception as e:
        print(f"Error during notification processing: {e}")

if __name__ == "__main__":
    main() 