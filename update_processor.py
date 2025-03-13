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

Analyze the input and respond with a Python tuple containing the update type and data. Use None for null/missing values.
Example formats:

1. Creating a new unit with tenant:
('unit', {{
    'unit_number': '1B',
    'unit_data': {{
        'unitNumber': '1B',
        'propertyId': 'wood-1',  # Use existing property ID
        'currentTenant': {{
            'name': 'Rebecca',
            'contactInfo': {{
                'phone': '+1 (203) 710-9065',
                'email': None,
                'address': None
            }},
            'lease': {{
                'propertyId': 'wood-1',  # Match property ID
                'unitId': '1B',  # Match unit number
                'tenantId': 'tenant-2',  # Generate new ID
                'startDate': '2024-07-01',
                'endDate': '2025-06-30',
                'rentAmount': 2475.0,
                'securityDeposit': 4850.0,
                'dueDate': 1
            }}
        }},
        'photos': [],
        'documents': []
    }}
}})

2. Creating a new tenant in existing unit:
('tenant', {{
    'unit_number': '1A',
    'tenant_data': {{
        'name': 'New Tenant',
        'contactInfo': {{
            'email': 'tenant@email.com',
            'phone': '555-0000',
            'address': None
        }},
        'lease': {{
            'propertyId': 'wood-1',
            'unitId': '1A',
            'tenantId': 'tenant-3',
            'startDate': '2024-01-01',
            'endDate': '2024-12-31',
            'rentAmount': 2000.0,
            'securityDeposit': 2000.0,
            'dueDate': 1
        }}
    }}
}})

3. Creating a new document:
('document', {{
    'entity_type': 'unit',
    'entity_id': '1A',
    'document_data': {{
        'id': 'doc-3',
        'type': 'lease',
        'url': 'https://example.com/new-lease.pdf',
        'name': 'New Lease Agreement',
        'uploadDate': '2024-03-15'
    }}
}})

Valid update types:
1. 'unit' - For creating or updating units
2. 'tenant' - For creating or updating tenant information
3. 'lease' - For creating or updating lease information
4. 'document' - For adding documents
5. 'property' - For updating property information
6. 'owner' - For updating owner information

For the current input, determine if it's a new entity creation or an update to an existing entity.
Include all required fields and IDs for new entities.
Only respond with the update data tuple using the exact format shown above, with None for missing values."""

    def _query_gpt(self, prompt: str, retry: bool = True) -> Union[Tuple[str, Dict[str, Any]], None]:
        """
        Query GPT-4 and parse its response
        Returns: Tuple of (update_type, update_data) or None if no update needed
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a property management AI assistant. Respond only with a valid Python tuple containing a string and a dictionary. Use None for null values."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1  # Low temperature for more consistent outputs
            )
            
            result = response.choices[0].message.content.strip()
            
            if result == 'NO_UPDATE':
                return None
                
            try:
                # Replace "null" with "None" in the response
                result = result.replace('null', 'None')
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
            'document': ['entity_type', 'entity_id', 'document_data'],
            'property': ['property_data'],
            'owner': ['owner_data']
        }
        
        if update_type not in required_fields:
            print(f"Invalid update type: {update_type}")
            return False
            
        for field in required_fields[update_type]:
            if field not in update_data:
                print(f"Missing required field: {field}")
                return False
                
        # Additional validation for new entities
        if update_type == 'unit':
            unit_data = update_data.get('unit_data', {})
            if 'propertyId' not in unit_data:
                # Set default property ID from schema
                unit_data['propertyId'] = self.schema['property'].get('units', [{}])[0].get('propertyId', 'wood-1')
            if 'currentTenant' in unit_data:
                tenant = unit_data['currentTenant']
                if 'lease' in tenant:
                    lease = tenant['lease']
                    if 'propertyId' not in lease:
                        lease['propertyId'] = unit_data['propertyId']
                    if 'unitId' not in lease:
                        lease['unitId'] = unit_data['unitNumber']
                    if 'tenantId' not in lease:
                        # Generate new tenant ID
                        existing_ids = set()
                        for u in self.schema['property'].get('units', []):
                            if u.get('currentTenant', {}).get('lease', {}).get('tenantId'):
                                existing_ids.add(u['currentTenant']['lease']['tenantId'])
                        i = len(existing_ids) + 1
                        while f'tenant-{i}' in existing_ids:
                            i += 1
                        lease['tenantId'] = f'tenant-{i}'
                
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
            elif update_type == 'property':
                return data_manager.update_property(
                    update_data['property_data']
                )
            elif update_type == 'owner':
                return data_manager.update_owner(
                    update_data['owner_data']
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