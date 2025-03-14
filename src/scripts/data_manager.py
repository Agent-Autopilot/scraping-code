"""Data Manager Script

This script provides functionality to apply structured instructions to JSON data files
for property management. It handles creating, updating, and deleting entities based on
the instructions provided.
"""

import os
import sys
import json
import copy
import logging
import traceback
from typing import Dict, Any, List, Optional, Tuple, Union

# Add parent directory to Python path if needed
parent_dir = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataManager:
    """Class for applying structured instructions to JSON data files."""
    
    def __init__(self):
        """Initialize the DataManager."""
        pass
    
    def load_json(self, file_path: str) -> Dict[str, Any]:
        """Load JSON data from a file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Dictionary containing the JSON data, or empty dict if loading fails
        """
        try:
            if not os.path.exists(file_path):
                logger.warning(f"File not found: {file_path}")
                return {}
                
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading JSON from {file_path}: {str(e)}")
            logger.error(traceback.format_exc())
            return {}
    
    def save_json(self, file_path: str, data: Dict[str, Any]) -> bool:
        """Save JSON data to a file.
        
        Args:
            file_path: Path to save the JSON file
            data: Dictionary containing the data to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving JSON to {file_path}: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def find_entity(self, data: Dict[str, Any], entity_type: str, identifier: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[int], Optional[str]]:
        """Find an entity in the data based on its type and identifier.
        
        Args:
            data: The JSON data to search in
            entity_type: Type of entity to find (e.g., 'Property', 'Unit', 'Tenant')
            identifier: Dictionary with 'field' and 'value' to identify the entity
            
        Returns:
            Tuple of (entity, index, collection_key) if found, or (None, None, None) if not found
        """
        # Determine the collection key based on entity type
        collection_key = self._get_collection_key(entity_type)
        if not collection_key:
            logger.error(f"Unknown entity type: {entity_type}")
            return None, None, None
        
        # Check if the collection exists
        if collection_key not in data:
            logger.warning(f"Collection {collection_key} not found in data")
            return None, None, None
        
        # If the entity type is 'Property' and it's a single object (not an array)
        if entity_type == 'Property' and isinstance(data[collection_key], dict):
            # Check if the identifier matches
            if identifier['field'] in data[collection_key] and data[collection_key][identifier['field']] == identifier['value']:
                return data[collection_key], None, collection_key
            return None, None, collection_key
        
        # For collections that are arrays
        if isinstance(data[collection_key], list):
            for i, entity in enumerate(data[collection_key]):
                if identifier['field'] in entity and entity[identifier['field']] == identifier['value']:
                    return entity, i, collection_key
        
        return None, None, collection_key
    
    def _get_collection_key(self, entity_type: str) -> Optional[str]:
        """Get the collection key for a given entity type.
        
        Args:
            entity_type: Type of entity (e.g., 'Property', 'Unit', 'Tenant')
            
        Returns:
            Collection key as string, or None if entity type is unknown
        """
        # Default mapping strategy: convert entity type to lowercase and add 's' if not already plural
        # Special case for 'Property' which is typically singular in the data structure
        if entity_type == 'Property':
            return 'property'
        
        # For other entity types, use a simple pluralization rule
        collection_key = entity_type.lower()
        if not collection_key.endswith('s'):
            collection_key += 's'
            
        return collection_key
    
    def apply_instruction(self, data: Dict[str, Any], instruction: Dict[str, Any]) -> Tuple[Dict[str, Any], bool, str]:
        """Apply a single instruction to the data.
        
        Args:
            data: The JSON data to modify
            instruction: Dictionary containing the instruction details
            
        Returns:
            Tuple of (updated_data, success, message)
        """
        try:
            # Make a deep copy of the data to avoid modifying the original
            updated_data = copy.deepcopy(data)
            
            # Extract instruction details
            action = instruction.get('action')
            entity_type = instruction.get('entity_type')
            identifier = instruction.get('identifier')
            fields = instruction.get('fields', {})
            
            # Validate required fields
            if not action or not entity_type or not identifier:
                return data, False, "Missing required fields in instruction"
            
            # Handle different actions
            if action == 'create':
                return self._create_entity(updated_data, entity_type, identifier, fields)
            elif action == 'update':
                return self._update_entity(updated_data, entity_type, identifier, fields)
            elif action == 'delete':
                return self._delete_entity(updated_data, entity_type, identifier)
            else:
                return data, False, f"Unknown action: {action}"
                
        except Exception as e:
            logger.error(f"Error applying instruction: {str(e)}")
            logger.error(traceback.format_exc())
            return data, False, f"Error: {str(e)}"
    
    def _create_entity(self, data: Dict[str, Any], entity_type: str, identifier: Dict[str, Any], fields: Dict[str, Any]) -> Tuple[Dict[str, Any], bool, str]:
        """Create a new entity in the data.
        
        Args:
            data: The JSON data to modify
            entity_type: Type of entity to create
            identifier: Dictionary with 'field' and 'value' to identify the entity
            fields: Dictionary of fields to set on the new entity
            
        Returns:
            Tuple of (updated_data, success, message)
        """
        # Find the collection key
        collection_key = self._get_collection_key(entity_type)
        if not collection_key:
            return data, False, f"Unknown entity type: {entity_type}"
        
        # Check if the entity already exists
        entity, _, _ = self.find_entity(data, entity_type, identifier)
        if entity:
            return data, False, f"{entity_type} with {identifier['field']}={identifier['value']} already exists"
        
        # Create the new entity
        new_entity = {identifier['field']: identifier['value']}
        new_entity.update(fields)
        
        # Add the entity to the collection
        if entity_type == 'Property' and collection_key == 'property':
            # For Property, replace the entire object
            data[collection_key] = new_entity
        else:
            # For other entities, add to the array
            if collection_key not in data:
                data[collection_key] = []
            data[collection_key].append(new_entity)
        
        return data, True, f"Created {entity_type} with {identifier['field']}={identifier['value']}"
    
    def _update_entity(self, data: Dict[str, Any], entity_type: str, identifier: Dict[str, Any], fields: Dict[str, Any]) -> Tuple[Dict[str, Any], bool, str]:
        """Update an existing entity in the data.
        
        Args:
            data: The JSON data to modify
            entity_type: Type of entity to update
            identifier: Dictionary with 'field' and 'value' to identify the entity
            fields: Dictionary of fields to update on the entity
            
        Returns:
            Tuple of (updated_data, success, message)
        """
        # Find the entity
        entity, index, collection_key = self.find_entity(data, entity_type, identifier)
        
        if not entity:
            return data, False, f"{entity_type} with {identifier['field']}={identifier['value']} not found"
        
        # Update the entity
        if entity_type == 'Property' and index is None:
            # For Property, update the object directly
            for field, value in fields.items():
                data[collection_key][field] = value
        else:
            # For other entities, update the array element
            for field, value in fields.items():
                data[collection_key][index][field] = value
        
        return data, True, f"Updated {entity_type} with {identifier['field']}={identifier['value']}"
    
    def _delete_entity(self, data: Dict[str, Any], entity_type: str, identifier: Dict[str, Any]) -> Tuple[Dict[str, Any], bool, str]:
        """Delete an entity from the data.
        
        Args:
            data: The JSON data to modify
            entity_type: Type of entity to delete
            identifier: Dictionary with 'field' and 'value' to identify the entity
            
        Returns:
            Tuple of (updated_data, success, message)
        """
        # Find the entity
        entity, index, collection_key = self.find_entity(data, entity_type, identifier)
        
        if not entity:
            return data, False, f"{entity_type} with {identifier['field']}={identifier['value']} not found"
        
        # Delete the entity
        if entity_type == 'Property' and index is None:
            # For Property, clear the object
            data[collection_key] = {}
        else:
            # For other entities, remove from the array
            data[collection_key].pop(index)
        
        return data, True, f"Deleted {entity_type} with {identifier['field']}={identifier['value']}"
    
    def apply_instructions(self, json_file_path: str, instructions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply a list of instructions to a JSON file.
        
        Args:
            json_file_path: Path to the JSON file to modify
            instructions: List of instruction dictionaries
            
        Returns:
            Dictionary with results including success, failed instructions, and messages
        """
        # Load the JSON data
        data = self.load_json(json_file_path)
        
        # Initialize results
        results = {
            "success": True,
            "failed_instructions": [],
            "messages": []
        }
        
        # Apply each instruction
        for i, instruction in enumerate(instructions):
            try:
                # Apply the instruction
                data, success, message = self.apply_instruction(data, instruction)
                
                # Record the result
                results["messages"].append(message)
                
                if not success:
                    results["success"] = False
                    results["failed_instructions"].append({
                        "index": i,
                        "instruction": instruction,
                        "error": message
                    })
                    
            except Exception as e:
                error_message = f"Error applying instruction {i}: {str(e)}"
                logger.error(error_message)
                logger.error(traceback.format_exc())
                
                results["success"] = False
                results["messages"].append(error_message)
                results["failed_instructions"].append({
                    "index": i,
                    "instruction": instruction,
                    "error": str(e)
                })
        
        # Save the updated data
        if results["success"] or (results["failed_instructions"] and len(results["failed_instructions"]) < len(instructions)):
            # Only save if at least one instruction succeeded
            if not self.save_json(json_file_path, data):
                results["success"] = False
                results["messages"].append(f"Failed to save updated data to {json_file_path}")
        
        return results 