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

# Import utils directly from the scripts package
from .utils import GPTClient, get_data_models_description

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
    
    def _create_prompt(self, text: str, schema: Optional[Dict[str, Any]] = None) -> str:
        """Create a prompt for the language model to analyze text input.
        
        Args:
            text: The natural language update text to analyze
            schema: Optional schema to include in the prompt
            
        Returns:
            A formatted prompt for the language model
        """
        # Include the current schema in the prompt if available
        schema_context = ""
        if schema:
            schema_context = f"""
Current property management data:
```json
{json.dumps(schema, indent=2)}
```
"""

        return f"""You are a property management system that processes natural language updates into structured instructions.

{schema_context}

I'll provide you with a natural language update about a property. Your task is to:

1. Analyze the text to identify the specific updates being requested
2. Convert these updates into structured instructions that the property management system can process
3. Return a JSON object with the following structure:
   - "analysis": A brief explanation of what updates are being made
   - "instructions": A list of specific update instructions in natural language

For example, if the input is:
"The tenant in unit 101 is moving out on June 30th, and the new tenant John Smith (phone: 555-1234) will move in on July 15th with rent of $1200"

Your response should be:
```json
{{
  "analysis": "This update involves a tenant change in unit 101, with move-out and move-in dates, and new lease details.",
  "instructions": [
    "Update the move-out date for the current tenant in unit 101 to 2023-06-30",
    "Add a new tenant named John Smith to unit 101",
    "Set John Smith's phone number to 5551234",
    "Create a new lease for John Smith in unit 101 starting on 2023-07-15 with rent $1200"
  ]
}}
```

Important guidelines:
1. Convert all dates to YYYY-MM-DD format
2. Remove any formatting from phone numbers (just digits)
3. Remove any formatting from currency values (just digits)
4. Break complex updates into simple, atomic instructions
5. If the update is unclear or ambiguous, include a note in your analysis
6. If the property or unit doesn't exist in the current data, assume it should be created
7. For lease updates, include all relevant details (start date, end date, rent amount, etc.)

Now, process this update:
"{text}"

Return only the JSON object with your analysis and instructions.
"""
    
    def process_update(self, text: str, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a natural language update into structured instructions.
        
        Args:
            text: The natural language text to process
            schema: Optional JSON schema to use instead of the default
            
        Returns:
            A dictionary containing the analysis and instructions, or an error message
        """
        try:
            # Use provided schema, instance schema, or None
            schema_to_use = schema if schema is not None else self.schema
            
            # Create the prompt with the text included
            prompt = self._create_prompt(text, schema_to_use)
            
            # Call the GPT API with system message
            system_message = "You are a property management system that processes natural language updates into structured instructions."
            response = self.gpt_client.query(prompt, system_message, temperature=0.1)
            
            if not response:
                logger.error("Failed to get a response from GPT")
                return {"error": "Failed to process update using GPT"}
            
            # Try to parse the result as JSON
            try:
                # Handle case where response might be wrapped in ```json ... ``` blocks
                if "```json" in response:
                    json_str = response.split("```json")[1].split("```")[0].strip()
                elif "```" in response:
                    json_str = response.split("```")[1].strip()
                    if json_str.startswith("json"):
                        json_str = json_str[4:].strip()
                else:
                    json_str = response.strip()
                
                result = json.loads(json_str)
                
                # Validate the response structure
                if "analysis" not in result or "instructions" not in result:
                    logger.error("Error: Invalid response structure from GPT")
                    return {"error": "Invalid response structure", "raw_response": response}
                
                # Return the result directly without parsing
                return result
                
            except json.JSONDecodeError:
                logger.error(f"Failed to parse GPT response as JSON: {response}")
                
                # Try to extract JSON from the response if it contains other text
                try:
                    # Look for JSON-like content between curly braces
                    start_idx = response.find('{')
                    end_idx = response.rfind('}') + 1
                    
                    if start_idx >= 0 and end_idx > start_idx:
                        json_str = response[start_idx:end_idx]
                        json_result = json.loads(json_str)
                        return json_result
                except:
                    pass
                
                return {
                    "error": "Failed to parse response as JSON",
                    "raw_response": response
                }
                
        except Exception as e:
            logger.error(f"Error processing update: {str(e)}")
            logger.error(traceback.format_exc())
            return {"error": f"Error processing update: {str(e)}"} 