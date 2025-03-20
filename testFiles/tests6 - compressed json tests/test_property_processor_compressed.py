"""Compressed JSON Test Script

This script processes all property documents in the input_files directory 
and generates streamlined JSON output with an optimized structure.
"""

import os
import sys
import json
import argparse
import copy
from pathlib import Path

# Add parent directory to Python path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(parent_dir)

# Import required modules
from src.property_processor import PropertyProcessor

def setup_directories():
    """Set up input and output directories."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(base_dir, "input_files")
    output_dir = os.path.join(base_dir, "output")
    
    # Create directories if they don't exist
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")
    
    return input_dir, output_dir

def save_json(data, file_path):
    """Save JSON data to a file."""
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✓ Saved JSON to {os.path.basename(file_path)}")
        return True
    except Exception as e:
        print(f"✗ Failed to save JSON: {str(e)}")
        return False

def compress_json(data):
    """Compress JSON by removing empty fields and redundant data.
    
    Args:
        data: JSON data to compress
        
    Returns:
        Compressed JSON data
    """
    print("Compressing JSON data...")
    
    # Make a deep copy to avoid modifying the original
    compressed = copy.deepcopy(data)
    
    def _compress_object(obj):
        """Recursively compress an object by removing empty fields."""
        if not isinstance(obj, dict):
            return obj
            
        # Keys to remove (empty values)
        keys_to_remove = []
        
        # Process each key-value pair
        for key, value in obj.items():
            # Handle nested dictionaries
            if isinstance(value, dict):
                obj[key] = _compress_object(value)
                # If dictionary became empty after compression, mark for removal
                if not obj[key]:
                    keys_to_remove.append(key)
            
            # Handle lists
            elif isinstance(value, list):
                # Compress each item in the list if it's a dictionary
                compressed_list = []
                for item in value:
                    if isinstance(item, dict):
                        compressed_item = _compress_object(item)
                        if compressed_item:  # Only add non-empty items
                            compressed_list.append(compressed_item)
                    elif item:  # Add non-empty primitives
                        compressed_list.append(item)
                
                # Update the list or mark for removal if empty
                if compressed_list:
                    obj[key] = compressed_list
                else:
                    keys_to_remove.append(key)
            
            # Handle primitive values
            elif value in (None, "", [], {}, 0) or (isinstance(value, str) and value.strip() == ""):
                keys_to_remove.append(key)
        
        # Remove empty keys
        for key in keys_to_remove:
            obj.pop(key, None)
            
        return obj
    
    # Start compression from the root
    return _compress_object(compressed)

def merge_json_data(data1, data2):
    """Merge two JSON data structures.
    
    Args:
        data1: First JSON data structure
        data2: Second JSON data structure
        
    Returns:
        Merged JSON data
    """
    print("Merging JSON data...")
    
    # Create a deep copy of data1 to avoid modifying the original
    merged_data = copy.deepcopy(data1)
    
    # Helper function to merge lists
    def merge_lists(list1, list2, id_field="id"):
        """Merge two lists of objects, avoiding duplicates based on ID field."""
        if not list1:
            return list2.copy() if list2 else []
        if not list2:
            return list1.copy() if list1 else []
            
        # Create a map of existing IDs
        id_map = {item.get(id_field): item for item in list1 if isinstance(item, dict) and id_field in item}
        
        # Create a new merged list
        merged_list = list1.copy()
        
        # Add items from list2 that don't exist in list1
        for item in list2:
            if isinstance(item, dict) and id_field in item:
                item_id = item.get(id_field)
                if item_id not in id_map:
                    merged_list.append(item)
                else:
                    # If the item exists, update with non-empty values from data2
                    for key, value in item.items():
                        if value and (key not in id_map[item_id] or not id_map[item_id][key]):
                            id_map[item_id][key] = value
        
        return merged_list
    
    # Merge top-level fields
    for key, value in data2.items():
        if key not in merged_data:
            merged_data[key] = value
        elif isinstance(value, dict) and isinstance(merged_data[key], dict):
            # Merge dictionaries recursively
            for sub_key, sub_value in value.items():
                if sub_key not in merged_data[key] or not merged_data[key][sub_key]:
                    merged_data[key][sub_key] = sub_value
        elif isinstance(value, list) and isinstance(merged_data[key], list):
            # Merge lists, avoiding duplicates
            merged_data[key] = merge_lists(merged_data[key], value)
    
    return merged_data

def process_file(file_path, output_dir, current_data=None, batch_size=10):
    """Process a single file and update the current data.
    
    Args:
        file_path: Path to the file to process
        output_dir: Directory to save output
        current_data: Current JSON data to update (None for first file)
        batch_size: Batch size for instruction processing
        
    Returns:
        Updated JSON data
    """
    file_name = os.path.basename(file_path)
    file_ext = os.path.splitext(file_name)[1].lower()
    
    print(f"\n{'='*50}")
    print(f"Processing: {file_name}")
    print(f"{'='*50}")
    
    # Initialize PropertyProcessor
    processor = PropertyProcessor()
    
    # If we have current data, use it as template
    if current_data:
        processor.template = current_data
    
    # Process based on file type
    if file_ext in ('.pdf', '.docx', '.doc'):
        print("Processing document file...")
        # Extract text
        text = processor.extract_text_from_document(file_path)
        
        # Generate instructions
        print("Generating instructions from text...")
        instructions = processor.generate_instructions_from_text(text)
        
        # Apply instructions
        print(f"Applying {len(instructions.get('instructions', []))} instructions (batch size: {batch_size})...")
        json_data, _ = processor.apply_instructions_to_json(
            processor.template.copy(),
            instructions,
            batch_size=batch_size
        )
        
        # Enrich data using text
        print("Enriching data with additional information...")
        enrichment_instructions = processor.enrich_json_with_text(json_data, text)
        
        if enrichment_instructions:
            print(f"Applying {len(enrichment_instructions)} enrichment instructions...")
            enriched_data, _ = processor.apply_instructions_to_json(
                json_data,
                {"instructions": enrichment_instructions},
                batch_size=batch_size
            )
            json_data = enriched_data
    
    elif file_ext in ('.txt', '.csv'):
        print("Processing text file...")
        # Read text content
        with open(file_path, 'r') as f:
            text = f.read()
        
        # Generate instructions
        print("Generating instructions from text...")
        instructions = processor.generate_instructions_from_text(text)
        
        # Apply instructions
        print(f"Applying {len(instructions.get('instructions', []))} instructions (batch size: {batch_size})...")
        json_data, _ = processor.apply_instructions_to_json(
            processor.template.copy(),
            instructions,
            batch_size=batch_size
        )
    
    elif file_ext in ('.xlsx', '.xls'):
        print("Processing Excel file...")
        # Extract text
        text = processor.extract_text_from_document(file_path)
        
        # Generate instructions
        print("Generating instructions from text...")
        instructions = processor.generate_instructions_from_text(text)
        
        # Apply instructions
        print(f"Applying {len(instructions.get('instructions', []))} instructions (batch size: {batch_size})...")
        json_data, _ = processor.apply_instructions_to_json(
            processor.template.copy(),
            instructions,
            batch_size=batch_size
        )
    
    else:
        print(f"Unsupported file type: {file_ext}")
        return current_data
    
    # Save intermediate result
    output_path = os.path.join(output_dir, f"{os.path.splitext(file_name)[0]}_processed.json")
    save_json(json_data, output_path)
    
    # If this is the first file, return its data
    if not current_data:
        return json_data
    
    # Otherwise, merge with current data
    merged_data = merge_json_data(current_data, json_data)
    
    # Save merged result
    merged_path = os.path.join(output_dir, "current_merged.json")
    save_json(merged_data, merged_path)
    
    return merged_data

def process_all_files(input_dir, output_dir, batch_size=10):
    """Process all files in the input directory.
    
    Args:
        input_dir: Directory containing input files
        output_dir: Directory to save output
        batch_size: Batch size for instruction processing
    """
    # Get all files in the input directory
    files = [os.path.join(input_dir, f) for f in os.listdir(input_dir) 
             if os.path.isfile(os.path.join(input_dir, f))]
    
    if not files:
        print("No files found in input directory!")
        return
    
    print(f"Found {len(files)} files to process")
    
    # Initialize PropertyProcessor for final steps
    processor = PropertyProcessor()
    
    # Process each file and accumulate data
    current_data = None
    for file_path in files:
        current_data = process_file(file_path, output_dir, current_data, batch_size)
    
    if not current_data:
        print("No data was generated from the files!")
        return
    
    # Restructure the final merged data
    print("\nRestructuring final data to optimize parent-child relationships...")
    restructured_data = processor.restructure_json(current_data)
    
    # Save restructured result
    restructured_path = os.path.join(output_dir, "restructured_result.json")
    save_json(restructured_data, restructured_path)
    
    # Compress the restructured data
    print("\nCompressing final data to remove empty fields and redundancies...")
    compressed_data = compress_json(restructured_data)
    
    # Save compressed result
    compressed_path = os.path.join(output_dir, "compressed_result.json")
    save_json(compressed_data, compressed_path)
    
    # Print statistics
    original_size = len(json.dumps(current_data))
    restructured_size = len(json.dumps(restructured_data))
    compressed_size = len(json.dumps(compressed_data))
    
    print("\n" + "="*50)
    print("Processing completed! Results summary:")
    print("="*50)
    print(f"Original data size: {original_size} characters")
    print(f"Restructured data size: {restructured_size} characters")
    print(f"Compressed data size: {compressed_size} characters")
    print(f"Size reduction: {(1 - compressed_size/original_size)*100:.2f}%")
    print("="*50)

def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(description="Process property documents and save optimized JSON output.")
    parser.add_argument("--input", help="Input directory containing documents to process")
    parser.add_argument("--output", help="Output directory for JSON files")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size for processing instructions")
    
    args = parser.parse_args()
    
    # Set up directories
    if args.input and args.output:
        input_dir = args.input
        output_dir = args.output
        os.makedirs(output_dir, exist_ok=True)
    else:
        input_dir, output_dir = setup_directories()
    
    # Process all files
    process_all_files(input_dir, output_dir, args.batch_size)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error during execution: {str(e)}")
        import traceback
        traceback.print_exc() 