"""Test property management system setup with a duplex property."""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add src directory to Python path
src_path = str(Path(__file__).parent.parent / 'src')
sys.path.append(src_path)

from property_manager import PropertyManager
from text_to_instructions import TextToInstructions

def get_updates_from_file(input_path: str) -> list:
    """Convert input file text into property management instructions."""
    try:
        with open(input_path, 'r') as f:
            text = f.read()
        
        converter = TextToInstructions()
        return converter.convert_text(text)
    except Exception as e:
        print(f"Error processing input file: {str(e)}")
        return []

def setup_property():
    """Set up properties using natural language commands."""
    # Initialize with test schema path
    schema_path = 'testFiles/test_schema2.json'
    input_path = 'testFiles/input.txt'
    
    # Delete existing schema file
    if os.path.exists(schema_path):
        os.remove(schema_path)
    
    # Initialize property manager
    manager = PropertyManager(schema_path=schema_path)
    
    # Get updates from input file
    updates = get_updates_from_file(input_path)
    
    # Process updates
    if updates:
        print("\nProcessing updates from input.txt:")
        for update in updates:
            print(f"\nProcessing: {update}")
            success = manager.process_text_update(update)
            if not success:
                print(f"Failed to process update: {update}")
            else:
                print("Success!")
    
    return True

def main():
    """Run the test setup."""
    try:
        if setup_property():
            print("\nProperty setup completed successfully!")
            print("Test schema saved to: testFiles/test_schema2.json")
        else:
            print("\nProperty setup failed!")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")

if __name__ == "__main__":
    main() 