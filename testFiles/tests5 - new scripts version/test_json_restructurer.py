"""Test script for JSON restructuring functionality.

This script takes a JSON file as input, restructures it to maximize parent-child relationships,
and saves the restructured result to a new file.
"""

import os
import sys
import json
import logging

# Add parent directory to Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(parent_dir)

# Import JSONRestructurer
from src.scripts.json_restructurer import JSONRestructurer
from src.property_processor import PropertyProcessor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_json_restructurer(json_file_path, output_file_path=None):
    """Test the JSON restructurer by restructuring the given JSON file.
    
    Args:
        json_file_path: Path to the JSON file to restructure
        output_file_path: Optional path to save the restructured JSON to
        
    Returns:
        The restructured JSON data
    """
    # Log the start of the test
    logger.info(f"Testing JSONRestructurer with {json_file_path}")
    
    # Check if input file exists
    if not os.path.exists(json_file_path):
        logger.error(f"Input file not found: {json_file_path}")
        return None
    
    # Load the JSON data
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        logger.info(f"Loaded JSON data from {json_file_path}")
    except Exception as e:
        logger.error(f"Error loading JSON data: {str(e)}")
        return None
    
    # Initialize PropertyProcessor to use its restructuring functionality
    processor = PropertyProcessor()
    
    # Restructure the JSON data
    logger.info("Restructuring JSON data...")
    restructured_data = processor.restructure_json(data)
    
    # Calculate how much more nested the structure became
    orig_depth = calculate_max_depth(data)
    new_depth = calculate_max_depth(restructured_data)
    logger.info(f"Original structure depth: {orig_depth}")
    logger.info(f"Restructured structure depth: {new_depth}")
    logger.info(f"Depth increase: {new_depth - orig_depth}")
    
    # Save the restructured JSON if an output path is provided
    if output_file_path:
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
        with open(output_file_path, 'w') as f:
            json.dump(restructured_data, f, indent=2)
        logger.info(f"Saved restructured JSON to {output_file_path}")
    
    # Print a summary of the changes
    print_restructure_summary(data, restructured_data)
    
    return restructured_data

def calculate_max_depth(obj, current_depth=0):
    """Calculate the maximum nesting depth of a JSON object.
    
    Args:
        obj: The JSON object to analyze
        current_depth: The current depth (for recursion)
        
    Returns:
        The maximum nesting depth
    """
    if isinstance(obj, dict):
        if not obj:  # Empty dict
            return current_depth
        return max(calculate_max_depth(value, current_depth + 1) for value in obj.values())
    elif isinstance(obj, list):
        if not obj:  # Empty list
            return current_depth
        return max(calculate_max_depth(item, current_depth + 1) for item in obj)
    else:
        return current_depth

def print_restructure_summary(original, restructured):
    """Print a summary of the changes made during restructuring.
    
    Args:
        original: The original JSON data
        restructured: The restructured JSON data
    """
    logger.info("=== Restructuring Summary ===")
    
    # Count top-level keys
    orig_keys = set(original.keys())
    new_keys = set(restructured.keys())
    
    # Changed keys
    added_keys = new_keys - orig_keys
    removed_keys = orig_keys - new_keys
    
    logger.info(f"Original top-level keys: {len(orig_keys)}")
    logger.info(f"Restructured top-level keys: {len(new_keys)}")
    
    if added_keys:
        logger.info(f"Added top-level keys: {', '.join(added_keys)}")
    if removed_keys:
        logger.info(f"Removed top-level keys: {', '.join(removed_keys)}")
    
    # Check if entities were moved
    logger.info("Entity movements:")
    
    # Check if tenants were moved
    orig_tenant_count = count_entities(original, "tenants")
    new_tenant_count = count_entities(restructured, "tenants")
    if orig_tenant_count != new_tenant_count:
        logger.info(f"Tenants: {orig_tenant_count} → {new_tenant_count} at top level")
    
    # Check if leases were moved
    orig_lease_count = count_entities(original, "leases")
    new_lease_count = count_entities(restructured, "leases")
    if orig_lease_count != new_lease_count:
        logger.info(f"Leases: {orig_lease_count} → {new_lease_count} at top level")
    
    # Check if units were moved
    orig_unit_count = count_entities(original, "units")
    new_unit_count = count_entities(restructured, "units")
    if orig_unit_count != new_unit_count:
        logger.info(f"Units: {orig_unit_count} → {new_unit_count} at top level")
    
    logger.info("=== End of Summary ===")

def count_entities(data, key):
    """Count the number of entities in a list at the given key.
    
    Args:
        data: The JSON data to analyze
        key: The key to count entities for
        
    Returns:
        The number of entities
    """
    if key in data and isinstance(data[key], list):
        return len(data[key])
    return 0

if __name__ == "__main__":
    # Path to the final_result.json file in output5 directory
    base_dir = os.path.abspath(os.path.dirname(__file__))
    input_file = os.path.join(base_dir, "output5", "final_result.json")
    output_file = os.path.join(base_dir, "output5", "restructured_result.json")
    
    # Test the JSONRestructurer
    restructured_data = test_json_restructurer(input_file, output_file)
    
    if restructured_data:
        logger.info("JSON restructuring test completed successfully")
    else:
        logger.error("JSON restructuring test failed") 