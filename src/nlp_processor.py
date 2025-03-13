"""Process natural language updates into structured property management instructions.

This module handles the conversion of natural language text into structured
update instructions for the property management system using OpenAI's language models.
The specific model can be configured via the GPT_MODEL environment variable.
"""

import os
import json
from typing import Dict, Any, Optional, Tuple
from openai import OpenAI
from dotenv import load_dotenv

class UpdateProcessor:
    """Process natural language updates into structured instructions using OpenAI's language models.
    
    The model used for processing is gpt-4o-mini.
    """
    
    def __init__(self, schema_path: Optional[str] = None):
        """Initialize the update processor with OpenAI client and schema.
        
        Args:
            schema_path: Optional path to the schema file. If None, looks for
                       'schema.json' in the current directory.
        
        Loads configuration from environment variables:
        - OPENAI_API_KEY: Required for API access
        - GPT_MODEL: Uses gpt-4o-mini by default
        """
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = os.getenv('GPT_MODEL', 'gpt-4o-mini')  # Use environment variable with fallback
        self.schema_path = schema_path or 'schema.json'
        self.schema = self._load_schema()
        
    def _load_schema(self) -> Dict[str, Any]:
        """Load the property management schema from JSON file."""
        try:
            if os.path.exists(self.schema_path):
                with open(self.schema_path, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading schema: {str(e)}")
            return {}
            
    def _create_prompt(self, text: str) -> str:
        """Create a prompt for the language model to analyze text input.
        
        Args:
            text: Natural language text to analyze
            
        Returns:
            Formatted prompt string for the language model
        """
        examples = '''
1. Creating/updating property:
Input: "Create a new property called Sample Property at 100 Main St, Sample City, ST 12345"
Output: ('property', {'Property_data': {'name': 'Sample Property', 'address': {'street': '100 Main St', 'city': 'Sample City', 'state': 'ST', 'zip': '12345'}}})

2. Setting owner information:
Input: "Set the owner to Sample Owner LLC, which is an LLC"
Output: ('owner', {'Owner_data': {'name': 'Sample Owner LLC', 'type': 'LLC'}})

3. Updating owner contact info:
Input: "Update the owner's email to sample@email.com and phone to 1234567890"
Output: ('owner', {'Owner_data': {'contactInfo': {'email': 'sample@email.com', 'phone': '1234567890'}}})

4. Setting owner address:
Input: "Set the owner's address to 200 Business St, Business City, ST 12345"
Output: ('owner', {'Owner_data': {'contactInfo': {'address': {'street': '200 Business St', 'city': 'Business City', 'state': 'ST', 'zip': '12345'}}}})

5. Adding/updating unit:
Input: "Create unit A1"
Output: ('unit', {'unitNumber': 'A1'})

6. Adding tenant:
Input: "Add tenant Sample Tenant to unit A1"
Output: ('tenant', {'unitNumber': 'A1', 'name': 'Sample Tenant', 'contactInfo': {}})

7. Setting lease terms:
Input: "Set lease for unit A1 starting Jan 1 2024 ending Dec 31 2024 with rent $1000 and security deposit $2000"
Output: ('lease', {'unitNumber': 'A1', 'startDate': '2024-01-01', 'endDate': '2024-12-31', 'rentAmount': 1000, 'securityDeposit': 2000})

8. Setting rent and deposit:
Input: "Set rent for unit A1 to $1000 with security deposit $2000"
Output: ('lease', {'unitNumber': 'A1', 'rentAmount': 1000, 'securityDeposit': 2000})
'''

        prompt = f"""You are a property management system that converts natural language instructions into structured data.
Analyze this text and convert it into a property management update:

Text: {text}

Your task is to:
1. Identify the type of update (property, owner, unit, tenant, lease, or document)
2. Extract relevant information and structure it according to the schema
3. Return a Python tuple with (update_type, data_dict)

Examples of valid updates:
{examples}

Important rules:
- For property updates, wrap data in 'Property_data'
- For owner updates, wrap data in 'Owner_data'
- Always include unit numbers for unit/tenant/lease updates
- Format dates as YYYY-MM-DD
- Remove currency symbols and commas from numbers
- Include all address components (street, city, state, zip)
- For lease updates, always include rentAmount (default to 0 if not specified)
- For owner contact updates, wrap in contactInfo
- For rent updates, use the lease update type with rentAmount field

Analyze the input text and return a single Python tuple following these formats, or None if the input is invalid.

Remember:
- Keep numbers as integers (no currency symbols or commas)
- Format dates consistently as YYYY-MM-DD
- Include all required fields for the update type
- Maintain the exact structure shown in the examples

Now, analyze this text and respond with a single Python tuple or None:
{text}"""

        return prompt
        
    def _query_gpt(self, prompt: str, max_retries: int = 3) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Query the configured language model with retry logic.
        
        Uses the model specified by GPT_MODEL environment variable.
        
        Args:
            prompt: The formatted prompt to send to the model
            max_retries: Maximum number of retry attempts
            
        Returns:
            Tuple of update type and data, or None if processing fails
        """
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a property management system that converts natural language to structured data."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1
                )
                
                result = response.choices[0].message.content.strip()
                if result.lower() == 'none':
                    return None
                    
                # Clean up the response to ensure valid Python syntax
                # Remove code blocks if present
                if result.startswith('```'):
                    result = result.split('```')[1]
                    if result.startswith('python'):
                        result = result[6:]
                result = result.strip()
                
                # Try to parse as Python tuple
                try:
                    import ast
                    # Convert string tuple to actual tuple
                    update = ast.literal_eval(result)
                    if not isinstance(update, tuple) or len(update) != 2:
                        raise ValueError("Invalid response format - not a tuple of length 2")
                        
                    update_type, update_data = update
                    if not isinstance(update_type, str):
                        raise ValueError("Invalid update type - not a string")
                    if not isinstance(update_data, dict):
                        raise ValueError("Invalid update data - not a dictionary")
                        
                    return update
                    
                except (ValueError, SyntaxError) as e:
                    print(f"Error parsing response on attempt {attempt + 1}: {str(e)}")
                    print(f"Raw response: {result}")
                    if attempt == max_retries - 1:
                        raise
                    continue
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"GPT processing failed after {max_retries} attempts: {str(e)}")
                    return None
                continue
                
    def process_update(self, text: str) -> Optional[Dict[str, Any]]:
        """Process natural language text into a structured update.
        
        Uses the configured language model to analyze and structure the input.
        
        Args:
            text: Natural language text describing the update
            
        Returns:
            Dictionary containing update type and data, or None if processing fails
        """
        if not text.strip():
            return None
            
        prompt = self._create_prompt(text)
        result = self._query_gpt(prompt)
        
        if not result:
            return None
            
        update_type, update_data = result
        
        # Validate update type and data
        if update_type not in {'property', 'owner', 'tenant', 'lease', 'document', 'unit'}:
            print(f"Invalid update type: {update_type}")
            return None
            
        if not isinstance(update_data, dict):
            print("Invalid update data format")
            return None
            
        return {
            'type': update_type,
            'data': update_data
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