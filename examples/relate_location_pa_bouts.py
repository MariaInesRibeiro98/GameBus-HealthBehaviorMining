from datetime import datetime
from src.oced.location_objects import LocationEventManager

def run_example():
    print("Example: Relating Location Segments to PA Bouts")
    print("=" * 50)

    # Create sample location segments
    sample_location_segments = [
        {
            'id': 'loc_seg_1',
            'type': 'location_segment',
            'attributes': [
                {'name': 'location_type', 'value': 'home'},
                {'name': 'start_time', 'value': '2024-03-20T08:00:00Z'},
                {'name': 'end_time', 'value': '2024-03-20T09:00:00Z'}
            ]
        },
        {
            'id': 'loc_seg_2',
            'type': 'location_segment',
            'attributes': [
                {'name': 'location_type', 'value': 'work'},
                {'name': 'start_time', 'value': '2024-03-20T10:00:00Z'},
                {'name': 'end_time', 'value': '2024-03-20T11:30:00Z'}
            ]
        }
    ]

    # Create sample PA bouts
    sample_pa_bouts = [
        {
            'id': 'pa_bout_1',
            'type': 'pa_bout',
            'attributes': [
                {'name': 'start_time', 'value': '2024-03-20T08:30:00Z'},
                {'name': 'end_time', 'value': '2024-03-20T09:30:00Z'},
                {'name': 'intensity', 'value': 'moderate'}
            ]
        },
        {
            'id': 'pa_bout_2',
            'type': 'pa_bout',
            'attributes': [
                {'name': 'start_time', 'value': '2024-03-20T10:15:00Z'},
                {'name': 'end_time', 'value': '2024-03-20T10:45:00Z'},
                {'name': 'intensity', 'value': 'vigorous'}
            ]
        }
    ]

    # Create extended data dictionary
    sample_extended_data = {
        'objects': sample_location_segments
    }

    # Create LocationEventManager instance
    location_manager = LocationEventManager()

    # Add relationships
    updated_data = location_manager.relate_location_to_pa_bouts(
        sample_extended_data,
        sample_pa_bouts
    )

    # Print results
    print("\nUpdated Location Segments with Relationships:")
    print("-" * 50)
    
    for segment in updated_data['objects']:
        print(f"\nLocation Segment: {segment['id']}")
        print(f"Location Type: {next(attr['value'] for attr in segment['attributes'] if attr['name'] == 'location_type')}")
        print(f"Time: {next(attr['value'] for attr in segment['attributes'] if attr['name'] == 'start_time')} to "
              f"{next(attr['value'] for attr in segment['attributes'] if attr['name'] == 'end_time')}")
        
        if 'relationships' in segment:
            print("Overlapping PA Bouts:")
            for rel in segment['relationships']:
                if rel['type'] == 'object' and rel['qualifier'] == 'overlaps_with_pa_bout':
                    pa_bout = next(bout for bout in sample_pa_bouts if bout['id'] == rel['id'])
                    print(f"  - PA Bout {pa_bout['id']}:")
                    print(f"    Time: {next(attr['value'] for attr in pa_bout['attributes'] if attr['name'] == 'start_time')} to "
                          f"{next(attr['value'] for attr in pa_bout['attributes'] if attr['name'] == 'end_time')}")
                    print(f"    Intensity: {next(attr['value'] for attr in pa_bout['attributes'] if attr['name'] == 'intensity')}")
        else:
            print("No overlapping PA bouts")
        print("-" * 50)

    print("\nExpected Relationships:")
    print("1. loc_seg_1 (Home, 8:00-9:00) overlaps with pa_bout_1 (8:30-9:30)")
    print("   - Overlap period: 8:30-9:00")
    print("2. loc_seg_2 (Work, 10:00-11:30) overlaps with pa_bout_2 (10:15-10:45)")
    print("   - Overlap period: 10:15-10:45")

if __name__ == "__main__":
    run_example() 