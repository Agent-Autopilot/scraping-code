import os
import json
from typing import Dict, Any, Optional, Tuple, Union
from dataclasses import asdict
from dotenv import load_dotenv
from openai import OpenAI
from models import *

class UpdateProcessor:
    def __init__(self):
        """Initialize the update processor with OpenAI client"""
        load_dotenv()
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file")
        self.client = OpenAI(api_key=api_key)
        self.schema = self._load_schema()

    def _load_schema(self) -> Dict:
        """Load the current schema file"""
        with open('schema.json', 'r') as f:
            return json.load(f)

    def _create_prompt(self, text_input: str) -> str:
        """Create the prompt for GPT-4"""
        return f"""You are a property management system. Given the following schema and text input, determine what updates need to be made.

Current Schema:
{json.dumps(self.schema, indent=2)}

Text Input: "{text_input}"

Analyze the input and respond with a tuple containing the update type and data in this exact format:
('update_type', {{
    'field1': 'value1',
    'field2': 'value2',
    ...
}})

Valid update types and their required fields:
1. 'tenant': 
   - unit_number: str
   - tenant_data: dict with fields from Tenant class (name, contactInfo, etc.)

2. 'lease':
   - unit_number: str
   - lease_data: dict with fields from Lease class (startDate, endDate, rentAmount, etc.)

3. 'unit':
   - unit_number: str
   - unit_data: dict with fields from Unit class

4. 'document':
   - entity_type: str ('property' or 'unit')
   - entity_id: str
   - document_data: dict with ALL required fields:
     * id: str (e.g., 'doc-123', 'doc-456', etc.)
     * type: str (e.g., 'lease', 'insurance', etc.)
     * url: str
     * name: Optional[str]
     * uploadDate: Optional[str] (use current date if not specified)

For photos, include these fields:
- id: str (e.g., 'photo-123', 'photo-456', etc.)
- url: str
- dateTaken: Optional[str]
- description: Optional[str]

Only respond with the update data tuple or 'NO_UPDATE' if no changes are needed.
Be precise and only include fields that need to be updated.
Always generate unique IDs for new documents and photos using the format shown above.
Ensure all nested objects (like contactInfo) are properly structured."""

    def _query_gpt(self, prompt: str, retry: bool = True) -> Union[Tuple[str, Dict[str, Any]], None]:
        """
        Query GPT-4 and parse its response
        Returns: Tuple of (update_type, update_data) or None if no update needed
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a property management AI assistant. Respond only with the requested tuple format or 'NO_UPDATE'."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1  # Low temperature for more consistent outputs
            )
            
            result = response.choices[0].message.content.strip()
            
            if result == 'NO_UPDATE':
                return None
                
            try:
                # Safely evaluate the response string as a Python tuple
                update = eval(result)
                if not isinstance(update, tuple) or len(update) != 2:
                    raise ValueError("Response must be a tuple of (str, dict)")
                if not isinstance(update[0], str) or not isinstance(update[1], dict):
                    raise ValueError("Tuple must contain (str, dict)")
                return update
            except Exception as e:
                if retry:
                    print("Retrying due to invalid response format...")
                    return self._query_gpt(prompt, retry=False)
                else:
                    print(f"Error parsing GPT response: {str(e)}")
                    return None
                    
        except Exception as e:
            if retry:
                print("Retrying due to API error...")
                return self._query_gpt(prompt, retry=False)
            else:
                print(f"Error querying GPT: {str(e)}")
                return None

    def analyze_text(self, text_input: str) -> Tuple[str, Dict[str, Any]]:
        """
        Analyze text input using GPT-4 to determine what needs to be updated
        Returns: (update_type, update_data) or raises Exception if no valid update
        """
        prompt = self._create_prompt(text_input)
        result = self._query_gpt(prompt)
        
        if result is None:
            raise Exception("No valid update could be determined from the input")
            
        return result

    def validate_update(self, update_type: str, update_data: Dict[str, Any]) -> bool:
        """
        Validate that the update data contains all required fields
        """
        required_fields = {
            'tenant': ['unit_number', 'tenant_data'],
            'lease': ['unit_number', 'lease_data'],
            'unit': ['unit_number', 'unit_data'],
            'document': ['entity_type', 'entity_id', 'document_data']
        }
        
        if update_type not in required_fields:
            print(f"Invalid update type: {update_type}")
            return False
            
        for field in required_fields[update_type]:
            if field not in update_data:
                print(f"Missing required field: {field}")
                return False
                
        # Additional validation for nested objects
        if update_type == 'tenant' and 'tenant_data' in update_data:
            if 'contactInfo' not in update_data['tenant_data']:
                print("Missing contactInfo in tenant_data")
                return False
                
        return True

    def process_update(self, text_input: str, data_manager) -> bool:
        """
        Process a text update and apply it to the data manager
        Returns: True if update was successful, False otherwise
        """
        try:
            # Analyze the text input using GPT-4
            update_type, update_data = self.analyze_text(text_input)
            
            # Validate the update data
            if not self.validate_update(update_type, update_data):
                return False
            
            # Apply the update using the appropriate DataManager method
            if update_type == 'tenant':
                return data_manager.update_tenant(
                    update_data['unit_number'],
                    update_data['tenant_data']
                )
            elif update_type == 'lease':
                return data_manager.update_lease(
                    update_data['unit_number'],
                    update_data['lease_data']
                )
            elif update_type == 'unit':
                return data_manager.update_unit(
                    update_data['unit_number'],
                    update_data['unit_data']
                )
            elif update_type == 'document':
                return data_manager.add_document(
                    update_data['entity_type'],
                    update_data['entity_id'],
                    update_data['document_data']
                )
            else:
                print(f"Unsupported update type: {update_type}")
                return False
                
        except Exception as e:
            print(f"Error processing update: {str(e)}")
            return False

# Example usage in update_data.py:
"""
from update_processor import UpdateProcessor

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