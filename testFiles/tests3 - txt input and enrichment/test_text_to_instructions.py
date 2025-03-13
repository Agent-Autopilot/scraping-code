"""Test the text to instructions converter.

This script tests the text to instructions converter by running it on input.txt.
"""

import os
import sys
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.text_to_instructions import TextToInstructions

def main():
    """Run text to instructions conversion on test file."""
    # Define path to input file
    input_path = 'testFiles/tests3 - txt input and enrichment/input.txt'
    
    # Load input text
    with open(input_path, 'r') as f:
        text = f.read()
    
    # Create converter and convert text
    converter = TextToInstructions()
    instructions = converter.convert_text(text)
    
    # Save generated instructions
    output_path = 'testFiles/tests3 - txt input and enrichment/generated_instructions.txt'
    with open(output_path, 'w') as f:
        for i, instruction in enumerate(instructions, 1):
            f.write(f"{i}. {instruction}\n")
    
    print(f"\nGenerated {len(instructions)} instructions and saved to {output_path}")

if __name__ == "__main__":
    main() 