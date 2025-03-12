import json
import shutil
from update_database import DataManager
from update_processor import UpdateProcessor

def backup_schema():
    """Create a backup of the schema file"""
    shutil.copy('schema.json', 'schema.backup.json')

def restore_schema():
    """Restore the schema from backup"""
    shutil.move('schema.backup.json', 'schema.json')

def test_updates():
    """Test various update scenarios"""
    try:
        # Create backup of schema
        backup_schema()

        # Initialize manager and processor
        manager = DataManager()
        processor = UpdateProcessor()

        # Test cases
        test_cases = [
            "Update unit 1A's tenant phone number to 555-9999",
            "Change the rent for unit 1A to $1600 starting from March 1st, 2024",
            "Add a new photo to unit 1A: https://example.com/photo2.jpg taken on 2024-02-01 showing the kitchen",
            "Add a new lease document for unit 1A: https://example.com/lease.pdf uploaded today",
            "Invalid update that should fail"
        ]

        print("\nRunning test cases...")
        for test in test_cases:
            print(f"\nTest input: {test}")
            success = processor.process_update(test, manager)
            print(f"Result: {'Success' if success else 'Failed'}")

            if success:
                # Verify the changes were saved
                with open('schema.json', 'r') as f:
                    current_data = json.load(f)
                print("Changes saved to schema.json")

    except Exception as e:
        print(f"Test failed with error: {str(e)}")
    finally:
        # Restore original schema
        restore_schema()

if __name__ == "__main__":
    test_updates() 