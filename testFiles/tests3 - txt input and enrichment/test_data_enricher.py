"""Test the data enricher module.

This script tests the data enricher by running it on test_schema3.json and input.txt.
"""

import os
import sys
import json
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent.parent.parent
src_path = str(project_root / 'src')
sys.path.append(str(project_root))

from src.data_enricher import DataEnricher

def test_data_enricher():
    """Test the data enricher on test files."""
    # Define paths
    json_path = 'testFiles/tests3 - txt input and enrichment/test_schema3.json'
    text_path = 'testFiles/tests3 - txt input and enrichment/input.txt'
    
    # Make a backup of the original JSON file
    backup_path = 'testFiles/tests3 - txt input and enrichment/test_schema3_backup.json'
    try:
        with open(json_path, 'r') as f:
            original_data = json.load(f)
        
        with open(backup_path, 'w') as f:
            json.dump(original_data, f, indent=2)
        
        print(f"Created backup of original data at {backup_path}")
    except Exception as e:
        print(f"Warning: Could not create backup: {str(e)}")
    
    # Create and run enricher
    print("\nRunning data enricher...")
    enricher = DataEnricher()
    success = enricher.enrich_data(json_path, text_path)
    
    if success:
        print("\nData enrichment completed successfully!")
        
        # Compare original and enriched data
        try:
            with open(json_path, 'r') as f:
                enriched_data = json.load(f)
            
            print("\nChanges made during enrichment:")
            compare_json_data(original_data, enriched_data)
        except Exception as e:
            print(f"Error comparing data: {str(e)}")
    else:
        print("\nData enrichment failed or no enrichments were needed.")
    
    return success

def compare_json_data(original: dict, enriched: dict, path=""):
    """Compare original and enriched JSON data to identify changes."""
    changes = 0
    
    # Helper function to handle nested dictionaries
    def compare_dicts(orig, enr, curr_path):
        nonlocal changes
        
        # Check for added or modified keys
        for key in enr:
            new_path = f"{curr_path}.{key}" if curr_path else key
            
            if key not in orig:
                print(f"  + Added: {new_path} = {enr[key]}")
                changes += 1
            elif isinstance(enr[key], dict) and isinstance(orig[key], dict):
                compare_dicts(orig[key], enr[key], new_path)
            elif enr[key] != orig[key]:
                print(f"  ~ Changed: {new_path} from {orig[key]} to {enr[key]}")
                changes += 1
        
        # Check for removed keys
        for key in orig:
            new_path = f"{curr_path}.{key}" if curr_path else key
            if key not in enr:
                print(f"  - Removed: {new_path} = {orig[key]}")
                changes += 1
    
    # Start comparison
    compare_dicts(original, enriched, path)
    
    if changes == 0:
        print("  No structural changes detected.")
    else:
        print(f"  Total changes: {changes}")

def main():
    """Run data enrichment on test files."""
    # Define paths
    json_path = os.path.join(os.path.dirname(__file__), 'test_schema3.json')
    text_path = os.path.join(os.path.dirname(__file__), 'input.txt')
    
    # Create and run enricher
    enricher = DataEnricher()
    success = enricher.enrich_data(json_path, text_path)
    
    if success:
        print("\nData enrichment completed successfully!")
    else:
        print("\nData enrichment failed or no enrichments were needed.")

if __name__ == "__main__":
    main() 