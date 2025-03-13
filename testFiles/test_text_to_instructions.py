"""Test converting unstructured text to property management instructions.

This script reads unstructured text from input.txt, converts it to property
management instructions, and then processes those instructions to create
a property schema file.
"""

import os
import sys
from pathlib import Path

# Add src directory to Python path
src_path = str(Path(__file__).parent.parent / 'src')
sys.path.append(src_path)

from text_to_instructions import TextToInstructions
from property_manager import PropertyManager

def main():
    """Convert input.txt to instructions and process them to create test_schema3.json."""
    # Initialize the text to instructions converter
    converter = TextToInstructions()
    
    # Read the input file
    input_file_path = 'testFiles/input.txt'
    with open(input_file_path, 'r') as file:
        input_text = file.read()
    
    print(f"Reading input from: {input_file_path}")
    
    # Convert the text to instructions
    print("\nConverting text to instructions...")
    instructions = converter.convert_text(input_text)
    
    if not instructions:
        print("Error: Failed to convert text to instructions.")
        return
    
    print(f"\nGenerated {len(instructions)} instructions.")
    
    # Save the generated instructions to a file
    instructions_file_path = 'testFiles/generated_instructions.txt'
    with open(instructions_file_path, 'w') as file:
        for i, instruction in enumerate(instructions, 1):
            file.write(f"{i}. {instruction}\n")
    
    print(f"Instructions saved to: {instructions_file_path}")
    
    # Initialize the property manager with a new schema file
    schema_path = 'testFiles/test_schema3.json'
    if os.path.exists(schema_path):
        os.remove(schema_path)
    
    manager = PropertyManager(schema_path=schema_path)
    
    # Process each instruction
    print("\nProcessing instructions...")
    success_count = 0
    failed_instructions = []
    
    for i, instruction in enumerate(instructions, 1):
        print(f"\nProcessing instruction {i}/{len(instructions)}: {instruction}")
        success = manager.process_text_update(instruction)
        if success:
            success_count += 1
            print("Success!")
        else:
            print(f"Failed to process instruction: {instruction}")
            failed_instructions.append(f"{i}. {instruction}")
    
    print(f"\nProcessed {success_count}/{len(instructions)} instructions successfully.")
    print(f"Property schema saved to: {schema_path}")
    
    # Save failed instructions to a file if there are any
    if failed_instructions:
        failed_file_path = 'testFiles/failed_instructions.txt'
        with open(failed_file_path, 'w') as file:
            file.write(f"Failed instructions ({len(failed_instructions)}/{len(instructions)}):\n\n")
            for instruction in failed_instructions:
                file.write(f"{instruction}\n")
        print(f"Failed instructions saved to: {failed_file_path}")
    
    # Print a summary of the property
    property = manager.get_property()
    if property:
        print(f"\nProperty Summary:")
        print(f"Name: {property.name}")
        print(f"Address: {property.address.street}, {property.address.city}, {property.address.state} {property.address.zip}")
        print(f"Owner: {property.owner.name}")
        
        units = manager.get_units()
        print(f"\nUnits: {len(units)}")
        for unit in units:
            tenant_name = unit.currentTenant.name if hasattr(unit, 'currentTenant') and unit.currentTenant else "VACANT"
            print(f"- Unit {unit.unitNumber}: {tenant_name}")
    
if __name__ == "__main__":
    main() 