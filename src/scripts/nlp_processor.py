"""NLP Processor Script

This script provides functionality to process natural language text into structured
instructions for property management updates. It uses GPT to analyze text and generate
structured instructions based on a provided JSON schema.
"""

import os
import sys
import json
import logging
import traceback
from typing import Dict, Any, List, Optional, Union

# Add parent directory to Python path if needed
parent_dir = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import from scripts.utils
from src.scripts.utils import GPTClient, get_data_models_description

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UpdateProcessor:
    """Class for processing natural language updates into structured instructions."""
    
    def __init__(self, schema_path: Optional[str] = None):
        """Initialize the UpdateProcessor with an optional schema path.
        
        Args:
            schema_path: Path to the JSON schema file. If None, a default template will be used.
        """
        self.gpt_client = GPTClient()
        self.schema_path = schema_path
        self.schema = self._load_schema() if schema_path else None
        
    def _load_schema(self) -> Dict[str, Any]:
        """Load the JSON schema from the specified path."""
        try:
            with open(self.schema_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading schema: {str(e)}")
            logger.error(traceback.format_exc())
            return {}
    
    def _create_system_prompt(self, schema: Optional[Dict[str, Any]] = None) -> str:
        """Create a system prompt for the GPT model based on the schema."""
        # Get data models description
        try:
            data_models_description = get_data_models_description()
        except Exception as e:
            logger.error(f"Error getting data models description: {str(e)}")
            logger.error(traceback.format_exc())
            # Provide a generic description if data models can't be loaded
            data_models_description = "Property management data including properties, units, tenants, leases, and related information."
        
        # Create the base system prompt
        system_prompt = f"""You are an AI assistant that processes natural language updates for a property management system.
Your task is to analyze the provided text and extract structured instructions for updating property information.

The property management system uses the following data models:
{data_models_description}

"""
        
        # Add schema information if provided
        if schema:
            schema_str = json.dumps(schema, indent=2)
            system_prompt += f"""You should generate instructions that conform to the following JSON schema:
{schema_str}

"""
        else:
            # Default instruction format if no schema is provided
            system_prompt += """If no specific schema is provided, you should generate instructions in the following format:
{
  "analysis": {
    "intent": "string describing the main intent of the update",
    "entities": ["list of entities mentioned in the update"],
    "confidence": 0-1 value indicating confidence in the analysis
  },
  "instructions": [
    {
      "action": "create|update|delete",
      "entity_type": "string representing the type of entity",
      "identifier": {
        "field": "name of the field used to identify the entity",
        "value": "value of the identifier field"
      },
      "fields": {
        "field_name": "new_value",
        ...
      }
    },
    ...
  ]
}

"""
        
        # Add guidelines for processing updates
        system_prompt += """IMPORTANT GUIDELINES:
1. Break complex updates into simple, atomic instructions.
2. For each instruction, clearly identify the entity type and how to identify the specific entity.
3. Only include fields that need to be updated, created, or deleted.
4. Convert dates to ISO format (YYYY-MM-DD).
5. Remove formatting from phone numbers and currency values.
6. If the update is ambiguous, include multiple possible interpretations as separate instructions.
7. If you cannot determine a specific field value with confidence, use null for that field.
8. Include an analysis section with your interpretation of the update's intent and entities mentioned.
9. If the text doesn't contain any actionable instructions, return an empty instructions array with an appropriate analysis.
10. Be flexible with entity types - don't assume a fixed set of entity types.

Your response must be valid JSON that can be parsed by a computer program."""
        
        return system_prompt
    
    def process_update(self, text: str, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a natural language update into structured instructions.
        
        Args:
            text: The natural language text to process
            schema: Optional JSON schema to use instead of the default
            
        Returns:
            A dictionary containing the analysis and instructions
        """
        try:
            # Use provided schema, instance schema, or None
            schema_to_use = schema if schema is not None else self.schema
            
            # Create the system prompt
            system_prompt = self._create_system_prompt(schema_to_use)
            
            # Create the user prompt
            user_prompt = f"""Please analyze the following update and generate structured instructions:

{text}"""
            
            # Call the GPT API
            result = self.gpt_client.query(user_prompt, system_prompt, temperature=0.1)
            
            if not result:
                logger.error("Failed to get a response from GPT")
                return {"error": "Failed to process update using GPT"}
            
            # Try to parse the result as JSON
            try:
                json_result = json.loads(result)
                return json_result
            except json.JSONDecodeError:
                logger.error(f"Failed to parse GPT response as JSON: {result}")
                
                # Try to extract JSON from the response if it contains other text
                try:
                    # Look for JSON-like content between curly braces
                    start_idx = result.find('{')
                    end_idx = result.rfind('}') + 1
                    
                    if start_idx >= 0 and end_idx > start_idx:
                        json_str = result[start_idx:end_idx]
                        json_result = json.loads(json_str)
                        return json_result
                except:
                    pass
                
                return {
                    "error": "Failed to parse response as JSON",
                    "raw_response": result
                }
                
        except Exception as e:
            logger.error(f"Error processing update: {str(e)}")
            logger.error(traceback.format_exc())
            return {"error": f"Error processing update: {str(e)}"} 