"""Data enrichment module for property management system.

This module analyzes the current JSON data, compares it with the original input data,
and uses GPT to identify and fill in missing information.
"""

import os
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Add src directory to Python path if needed
src_path = str(Path(__file__).parent)
if src_path not in sys.path:
    sys.path.append(src_path)

from src.text_to_instructions import TextToInstructions
from src.property_manager import PropertyManager
from src.utils import GPTClient, FileManager

class DataEnricher:
    """Enriches property data by identifying and filling in missing information."""
    
    def __init__(self):
        """Initialize the data enricher with OpenAI client."""
        self.gpt_client = GPTClient()
        self.text_to_instructions = TextToInstructions()
        
    def analyze_and_enrich(self, json_path: str, text_path: str, save_suggestions: bool = True) -> List[str]:
        """Analyze JSON and text data to identify and suggest enrichments."""
        # Load data
        json_data = FileManager.load_json(json_path)
        text_data = FileManager.load_text(text_path)
        
        if not json_data or not text_data:
            print("Missing data, cannot proceed with enrichment")
            return []
        
        # Create prompt for GPT
        prompt = self._create_enrichment_prompt(json_data, text_data)
        
        # Get suggestions from GPT
        suggestions_text, instructions = self._get_enrichment_suggestions(prompt)
        
        # Save suggestions to file if requested
        if save_suggestions and suggestions_text:
            self._save_suggestions(json_path, suggestions_text, instructions)
        
        return instructions
    
    def _create_enrichment_prompt(self, json_data: Dict[str, Any], text_data: str) -> str:
        """Create a prompt for GPT to analyze and suggest enrichments."""
        return f"""You are a property management data analyst. Your task is to analyze the current property data (in JSON format) and the original input data (in text format) to identify missing or incomplete information that could be filled in, as well as to identify and correct any errors in the existing data.

Please look for:
1. Missing information in the JSON that is present in the text data (e.g., payment dates, contact information)
2. Incomplete fields in the JSON (e.g., addresses missing zip codes)
3. Inconsistencies between the JSON and text data
4. Errors in the JSON data that need to be corrected (e.g., incorrect zip codes, wrong tenant names)
5. Any other information that could be inferred or derived from the existing data

IMPORTANT: Be very careful about making inferences. Do not assume that information about one entity (like an owner) applies to another entity (like a property) unless there is clear evidence. For example, the owner's address zip code should not be applied to the property address unless there is explicit evidence they are the same location.

For each issue you identify, provide a clear explanation and suggestion for how to fix it.

Current JSON data:
```json
{json.dumps(json_data, indent=2)}
```

Original text data:
```
{text_data}
```

Based on your analysis, provide a list of specific updates that should be made to enrich the data and correct any errors. Format your response as a series of natural language instructions that could be processed by a property management system.

For example:
1. Update the zip code for property address to 06525
2. Set lease due date for unit 167 to the 15th of each month
3. Add phone number 203-250-0285 for tenant Sherry in unit 165
4. Correct the property zip code from 10960 to 06525 as it was incorrectly set to the owner's zip code

Only include instructions for information that is missing, incorrect, or inconsistent based on the available data."""

    def _get_enrichment_suggestions(self, prompt: str) -> Tuple[str, List[str]]:
        """Get enrichment suggestions from GPT."""
        try:
            print("\nSending data to OpenAI for analysis...")
            print(f"Model: {self.gpt_client.model}")
            
            system_message = "You are a property management data analyst that identifies missing or incomplete information and corrects errors in property data."
            
            suggestions_text = self.gpt_client.query(prompt, system_message)
            
            if not suggestions_text:
                return "", []
                
            print("\nGPT Analysis Results:")
            print(suggestions_text)
            
            # Convert to instructions
            instructions = self.text_to_instructions.convert_text(suggestions_text)
            
            return suggestions_text, instructions
            
        except Exception as e:
            print(f"Error getting enrichment suggestions: {str(e)}")
            return "", []
    
    def _save_suggestions(self, json_path: str, suggestions_text: str, instructions: List[str]) -> None:
        """Save suggestions and instructions to files for review."""
        try:
            # Determine base path for saving files
            base_dir, base_name = FileManager.get_base_path(json_path)
            
            # Save raw suggestions
            suggestions_path = os.path.join(base_dir, f"{base_name}_enrichment_suggestions.txt")
            FileManager.save_text(suggestions_path, suggestions_text)
            print(f"Saved raw suggestions to {suggestions_path}")
            
            # Save processed instructions
            instructions_path = os.path.join(base_dir, f"{base_name}_enrichment_instructions.txt")
            instructions_content = "\n".join([f"{i+1}. {instruction}" for i, instruction in enumerate(instructions)])
            FileManager.save_text(instructions_path, instructions_content)
            print(f"Saved processed instructions to {instructions_path}")
            
        except Exception as e:
            print(f"Error saving suggestions: {str(e)}")
    
    def apply_enrichments(self, json_path: str, instructions: List[str]) -> bool:
        """Apply enrichment instructions to the JSON data."""
        if not instructions:
            print("No enrichment instructions to apply")
            return False
        
        # Initialize property manager with the JSON file
        manager = PropertyManager(schema_path=json_path)
        
        # Process each instruction
        success_count = 0
        failed_instructions = []
        
        for i, instruction in enumerate(instructions, 1):
            print(f"\nApplying enrichment {i}/{len(instructions)}: {instruction}")
            success = manager.process_text_update(instruction)
            if success:
                success_count += 1
                print("Success!")
            else:
                print(f"Failed to apply enrichment: {instruction}")
                failed_instructions.append(instruction)
        
        # Save failed instructions if any
        if failed_instructions:
            base_dir, base_name = FileManager.get_base_path(json_path)
            failed_path = os.path.join(base_dir, f"{base_name}_failed_enrichments.txt")
            
            failed_content = "\n".join([f"{i+1}. {instruction}" for i, instruction in enumerate(failed_instructions)])
            FileManager.save_text(failed_path, failed_content)
            print(f"\nSaved {len(failed_instructions)} failed instructions to {failed_path}")
        
        print(f"\nApplied {success_count}/{len(instructions)} enrichments successfully.")
        return success_count > 0
    
    def enrich_data(self, json_path: str, text_path: str) -> bool:
        """Analyze and enrich data in one step."""
        instructions = self.analyze_and_enrich(json_path, text_path)
        if instructions:
            return self.apply_enrichments(json_path, instructions)
        return False

def main():
    """Run data enrichment on test files."""
    # Define paths
    json_path = 'testFiles/test_schema3.json'
    text_path = 'testFiles/input.txt'
    
    # Create and run enricher
    enricher = DataEnricher()
    success = enricher.enrich_data(json_path, text_path)
    
    if success:
        print("\nData enrichment completed successfully!")
    else:
        print("\nData enrichment failed or no enrichments were needed.")

if __name__ == "__main__":
    main() 