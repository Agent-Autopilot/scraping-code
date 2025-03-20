"""Process natural language updates into structured property management instructions.

This module handles the conversion of natural language text into structured
update instructions for the property management system using OpenAI's language models.
The specific model can be configured via the GPT_MODEL environment variable.
"""

import os
from typing import Dict, Any, Optional, Tuple
import json

# Import utility classes
from src.utils import GPTClient, FileManager

class UpdateProcessor:
    """Process natural language updates into structured instructions using OpenAI's language models.
    
    The model used for processing is configurable via the GPT_MODEL environment variable.
    """
    
    def __init__(self, schema_path: Optional[str] = None):
        """Initialize the update processor with GPT client and schema.
        
        Args:
            schema_path: Optional path to the schema file. If None, looks for
                       'schema.json' in the current directory.
        """
        self.gpt_client = GPTClient()
        self.schema_path = schema_path or 'schema.json'
        self.schema = self._load_schema()
        
    def _load_schema(self) -> Dict[str, Any]:
        """Load the property management schema from JSON file."""
        schema = FileManager.load_json(self.schema_path)
        return schema if schema else {}
            
    def _create_prompt(self, text: str) -> str:
        """Create a prompt for the language model to analyze text input.
        
        Args:
            text: The natural language update text to analyze
            
        Returns:
            A formatted prompt for the language model
        """
        # Include the current schema in the prompt if available
        schema_context = ""
        if self.schema:
            schema_context = f"""
Current property management data:
```json
{json.dumps(self.schema, indent=2)}
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

    def _query_gpt(self, prompt: str, max_retries: int = 3) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Query the GPT model to process the update.
        
        Args:
            prompt: The prompt to send to the model
            max_retries: Maximum number of retry attempts
            
        Returns:
            A tuple of (analysis, instructions) or None if processing fails
        """
        system_message = "You are a property management system that processes natural language updates into structured instructions."
        
        try:
            # Use the GPTClient to query the model
            response = self.gpt_client.query(prompt, system_message)
            
            if not response:
                return None
                
            # Extract the JSON object from the response
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
                    print("Error: Invalid response structure from GPT")
                    return None
                    
                return result["analysis"], result["instructions"]
                
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON response: {str(e)}")
                print(f"Raw response: {response}")
                return None
                
        except Exception as e:
            print(f"Error querying GPT: {str(e)}")
            return None
            
    def process_update(self, text: str) -> Optional[Dict[str, Any]]:
        """Process a natural language update into structured instructions.
        
        Args:
            text: The natural language update text to process
            
        Returns:
            A dictionary with analysis and instructions, or None if processing fails
        """
        prompt = self._create_prompt(text)
        result = self._query_gpt(prompt)
        
        if not result:
            return None
            
        analysis, instructions = result
        
        return {
            "analysis": analysis,
            "instructions": instructions
        }

# Example usage in data_manager.py:
"""
from nlp_processor import UpdateProcessor

def main():
    manager = DataManager()
    processor = UpdateProcessor()
    
    while True:
        print("\nEnter your update (or 'quit' to exit):")
        user_input = input("> ")
        
        if user_input.lower() == 'quit':
            break
        
        success = processor.process_update(user_input, manager)
        
        if success:
            print("Update successful!")
        else:
            print("Update failed.")
""" 