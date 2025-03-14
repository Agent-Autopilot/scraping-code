"""Test script to convert document extracted text to JSON.

This script takes the extracted text from a document, converts it to instructions,
and processes those instructions to create a JSON file.
"""

import os
import sys
import json
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.text_to_instructions import TextToInstructions
from src.property_manager import PropertyManager

def main():
    """Convert document extracted text to JSON."""
    # Define paths
    extracted_text_path = 'testFiles/tests4 - document conversion/APT A Lease - Extracted.txt'
    instructions_path = 'testFiles/tests4 - document conversion/APT A Lease - Instructions.txt'
    json_output_path = 'testFiles/tests4 - document conversion/APT A Lease - Data.json'
    
    # Load extracted text
    with open(extracted_text_path, 'r') as f:
        text = f.read()
    
    print(f"Processing extracted text from: {extracted_text_path}")
    
    # Create converter and convert text to instructions
    converter = TextToInstructions()
    instructions = converter.convert_text(text)
    
    # Save generated instructions
    with open(instructions_path, 'w') as f:
        for i, instruction in enumerate(instructions, 1):
            f.write(f"{i}. {instruction}\n")
    
    print(f"Generated {len(instructions)} instructions and saved to {instructions_path}")
    
    # Create a property manager and process the instructions
    property_manager = PropertyManager()
    
    # Create a new schema
    schema = {
        "properties": []
    }
    
    # Process each instruction
    failed_instructions = []
    succeeded_instructions = []
    for instruction in instructions:
        try:
            # Process the instruction
            success = property_manager.process_single_instruction(instruction)
            if success:
                succeeded_instructions.append(instruction)
            else:
                failed_instructions.append(f"{instruction} - Error: Instruction processing failed")
        except Exception as e:
            failed_instructions.append(f"{instruction} - Error: {str(e)}")
    
    # Save failed instructions if any
    if failed_instructions:
        with open('testFiles/tests4 - document conversion/failed_instructions.txt', 'w') as f:
            for instruction in failed_instructions:
                f.write(f"{instruction}\n")
        print(f"Warning: {len(failed_instructions)} instructions failed. See failed_instructions.txt")
    
    # Save the resulting JSON
    with open(json_output_path, 'w') as f:
        json.dump(property_manager.data_manager.data, f, indent=2)
    
    print(f"Created JSON file: {json_output_path}")
    
    # Print summary of instructions
    if succeeded_instructions:
        print(f"\nSuccessfully processed {len(succeeded_instructions)} instructions:")
        for i, instruction in enumerate(succeeded_instructions, 1):
            print(f"  {i}. {instruction}")
    
    print(f"\nAll instructions generated from the document:")
    for i, instruction in enumerate(instructions, 1):
        print(f"  {i}. {instruction}")

if __name__ == "__main__":
    main() 