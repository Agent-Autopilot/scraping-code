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

# Import utils directly
from .utils import GPTClient, FileManager, get_data_models_description

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
        
        return f"""You are a property management data analyst. Your task is to analyze the current property data (in JSON format) and the original input data (in text format) to identify missing or incomplete information that could be filled in, as well as to identify and correct any errors in the existing data.

The property management system uses the following data models:
{data_models_description}

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
            logger.info("Sending data to OpenAI for analysis...")
            logger.info(f"Model: {self.gpt_client.model}")
            
            # Call GPT API
            system_message = "You are a property management data analyst that identifies missing or incomplete information and corrects errors in property data."
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
        
        # Look for lines that start with a number followed by a period
        for line in lines:
            if line.strip() and line.strip()[0].isdigit() and '. ' in line:
                # Extract the instruction part (after the number and period)
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