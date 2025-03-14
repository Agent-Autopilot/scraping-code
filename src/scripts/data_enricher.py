"""Data enrichment module for property management system.

This module analyzes the current JSON data, compares it with the original input data,
and uses GPT to identify and suggest enrichment instructions.
"""

import os
import json
import sys
import logging
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Add parent directory to Python path if needed
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from src.scripts.utils import GPTClient, FileManager, get_data_models_description

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataEnricher:
    """Analyzes property data and suggests enrichment instructions.
    
    This class compares JSON data with text descriptions to identify missing information
    and generate instructions for enrichment. It does NOT apply the changes - that
    responsibility belongs to the DataManager class.
    """
    
    def __init__(self):
        """Initialize the data enricher with OpenAI client."""
        self.gpt_client = GPTClient()
        
    def generate_enrichment_instructions(self, json_path: str, text_path: str, save_suggestions: bool = True) -> List[str]:
        """Analyze JSON and text data to generate enrichment instructions.
        
        Args:
            json_path: Path to the JSON file containing structured property data
            text_path: Path to the text file containing unstructured property description
            save_suggestions: Whether to save the suggestions to files for review
            
        Returns:
            List of natural language instructions for enriching the data
        """
        # Load data
        json_data = FileManager.load_json(json_path)
        text_data = FileManager.load_text(text_path)
        
        if not json_data or not text_data:
            logger.warning("Missing data, cannot proceed with enrichment analysis")
            return []
        
        # Create prompt for GPT
        prompt = self._create_enrichment_prompt(json_data, text_data)
        
        # Get suggestions from GPT
        suggestions_text, instructions = self._get_enrichment_suggestions(prompt)
        
        # Save suggestions to file if requested
        if save_suggestions and suggestions_text:
            self._save_suggestions(json_path, suggestions_text, instructions)
        
        return instructions
    
    def generate_enrichment_instructions_from_data(self, json_data: Dict[str, Any], text_data: str) -> List[str]:
        """Analyze JSON and text data to generate enrichment instructions.
        
        This version works directly with data objects rather than file paths.
        
        Args:
            json_data: Dictionary containing structured property data
            text_data: String containing unstructured property description
            
        Returns:
            List of natural language instructions for enriching the data
        """
        if not json_data or not text_data:
            logger.warning("Missing data, cannot proceed with enrichment analysis")
            return []
        
        # Create prompt for GPT
        prompt = self._create_enrichment_prompt(json_data, text_data)
        
        # Get suggestions from GPT
        _, instructions = self._get_enrichment_suggestions(prompt)
        
        return instructions
    
    def _create_enrichment_prompt(self, json_data: Dict[str, Any], text_data: str) -> str:
        """Create a prompt for GPT to analyze and suggest enrichments."""
        # Get data models description for context
        try:
            data_models_description = get_data_models_description()
        except Exception as e:
            logger.error(f"Error getting data models description: {str(e)}")
            logger.error(traceback.format_exc())
            # Provide a generic description if data models can't be loaded
            data_models_description = "Property management data including properties, units, tenants, leases, and related information."
        
        # Format the JSON data for the prompt
        json_str = json.dumps(json_data, indent=2)
        
        return f"""You are an AI assistant that helps enrich property management data.

I have the following JSON data about a property:
```json
{json_str}
```

And I have this original text description:
```
{text_data}
```

The property management system uses the following data models:
{data_models_description}

Please analyze both the JSON data and the text description, and identify any information from the text that is missing in the JSON data. Then, provide:

1. A list of specific enrichment suggestions
2. A list of instructions that could be used to update the JSON data

Focus on factual information that is clearly stated in the text but missing from the JSON. Do not make assumptions or add information that isn't explicitly mentioned in the text.

Format your response in two sections:
- "Enrichment Suggestions": A detailed explanation of what information is missing and should be added
- "Update Instructions": A list of specific instructions in natural language that could be used to update the JSON data"""

    def _get_enrichment_suggestions(self, prompt: str) -> Tuple[str, List[str]]:
        """Get enrichment suggestions from GPT."""
        try:
            logger.info("Sending data to OpenAI for analysis...")
            logger.info(f"Model: {self.gpt_client.model}")
            
            # Call GPT API
            system_message = "You are an AI assistant that helps enrich property management data."
            response = self.gpt_client.query(prompt, system_message, temperature=0.1)
            
            if not response:
                logger.error("Failed to get a response from GPT")
                return "", []
            
            # Extract instructions from the response
            instructions = self._extract_instructions(response)
            
            return response, instructions
            
        except Exception as e:
            logger.error(f"Error getting enrichment suggestions: {str(e)}")
            logger.error(traceback.format_exc())
            return "", []
    
    def _extract_instructions(self, text: str) -> List[str]:
        """Extract numbered instructions from text."""
        instructions = []
        lines = text.strip().split('\n')
        
        # Look for the "Update Instructions" section
        in_instructions_section = False
        for line in lines:
            # Check if we're entering the instructions section
            if "Update Instructions" in line or "UPDATE INSTRUCTIONS" in line:
                in_instructions_section = True
                continue
                
            # Skip lines until we reach the instructions section
            if not in_instructions_section:
                continue
                
            # Look for lines that start with a number followed by a period
            if line.strip() and line.strip()[0].isdigit() and '. ' in line:
                # Extract the instruction part (after the number and period)
                parts = line.split('. ', 1)
                if len(parts) > 1:
                    instructions.append(parts[1].strip())
        
        # If we didn't find a specific section, fall back to looking for numbered lines anywhere
        if not instructions:
            for line in lines:
                if line.strip() and line.strip()[0].isdigit() and '. ' in line:
                    parts = line.split('. ', 1)
                    if len(parts) > 1:
                        instructions.append(parts[1].strip())
        
        return instructions
    
    def _save_suggestions(self, json_path: str, suggestions_text: str, instructions: List[str]) -> None:
        """Save suggestions and instructions to files for review."""
        try:
            # Determine base path for saving files
            base_dir = os.path.dirname(json_path)
            base_name = os.path.splitext(os.path.basename(json_path))[0]
            
            # Save raw suggestions
            suggestions_path = os.path.join(base_dir, f"{base_name}_enrichment_suggestions.txt")
            FileManager.save_text(suggestions_path, suggestions_text)
            logger.info(f"Saved raw suggestions to {suggestions_path}")
            
            # Save processed instructions
            instructions_path = os.path.join(base_dir, f"{base_name}_enrichment_instructions.txt")
            instructions_content = "\n".join([f"{i+1}. {instruction}" for i, instruction in enumerate(instructions)])
            FileManager.save_text(instructions_path, instructions_content)
            logger.info(f"Saved processed instructions to {instructions_path}")
            
        except Exception as e:
            logger.error(f"Error saving suggestions: {str(e)}")
            logger.error(traceback.format_exc()) 