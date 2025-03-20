"""JSON Restructurer Script

This script uses OpenAI to analyze and restructure a JSON object based on ID relationships.
It identifies potential parent-child relationships between entities and reorganizes the JSON
structure to maximize hierarchical relationships.

The restructurer identifies relationships through ID fields and reference fields,
converting a flat structure into a hierarchical one that better represents the data model.
"""

import os
import sys
import json
import logging
import traceback
from typing import Dict, Any, List, Optional, Tuple, Set

# Add parent directory to Python path if needed
parent_dir = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import utils for GPT client
from .utils import GPTClient, get_data_models_description

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JSONRestructurer:
    """Class for restructuring JSON data based on ID relationships using OpenAI."""
    
    def __init__(self):
        """Initialize the JSONRestructurer."""
        self.gpt_client = GPTClient()
    
    def restructure_json(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Restructure a JSON object to maximize parent-child relationships.
        
        Args:
            data: The JSON data to restructure
            
        Returns:
            The restructured JSON data
        """
        try:
            # Log the start of restructuring
            logger.info("Starting JSON restructuring...")
            
            # First, analyze the existing ID relationships
            relationships = self._analyze_relationships(data)
            
            # Get the data models description for context
            data_models_description = get_data_models_description()
            
            # Build a prompt that includes the relationship analysis
            prompt = self._build_restructuring_prompt(data, relationships, data_models_description)
            
            # Get the restructured JSON from OpenAI
            restructured_data = self._get_restructured_json(prompt)
            
            if restructured_data:
                logger.info("Successfully restructured JSON data")
            else:
                logger.error("Failed to restructure JSON data, returning original")
                return data
                
            return restructured_data
            
        except Exception as e:
            logger.error(f"Error restructuring JSON: {str(e)}")
            logger.error(traceback.format_exc())
            return data  # Return original data on error
    
    def _analyze_relationships(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Analyze ID relationships in the JSON data.
        
        Args:
            data: The JSON data to analyze
            
        Returns:
            Dictionary mapping entity types to their relationship descriptions
        """
        relationships = {}
        entity_ids = {}
        
        # First pass: collect all entities with IDs
        self._collect_entity_ids(data, entity_ids)
        
        # Second pass: identify relationships
        for entity_type, entities in entity_ids.items():
            entity_relationships = []
            
            for entity_id, entity in entities.items():
                # Look for *Id fields that could reference other entities
                for field, value in entity.items():
                    if field.endswith('Id') and isinstance(value, str) and value:
                        referenced_type = field[:-2]  # Remove 'Id' suffix
                        entity_relationships.append(f"{entity_type} with ID '{entity_id}' references {referenced_type} with ID '{value}'")
            
            if entity_relationships:
                relationships[entity_type] = entity_relationships
        
        return relationships
    
    def _collect_entity_ids(self, obj: Any, entity_ids: Dict[str, Dict[str, Any]], path: str = ""):
        """Recursively collect entities with IDs from the JSON structure.
        
        Args:
            obj: The current object being processed
            entity_ids: Dictionary to populate with entity IDs
            path: Current path in the JSON structure
        """
        if isinstance(obj, dict):
            # Check if this is an entity with an ID
            if 'id' in obj:
                # Try to determine the entity type
                entity_type = path.split('.')[-1]
                if entity_type.endswith('s') and len(entity_type) > 1:
                    # Singularize simple plural entity types (e.g., 'tenants' -> 'tenant')
                    entity_type = entity_type[:-1]
                
                if entity_type not in entity_ids:
                    entity_ids[entity_type] = {}
                
                entity_ids[entity_type][obj['id']] = obj
            
            # Recursively process all fields
            for key, value in obj.items():
                new_path = f"{path}.{key}" if path else key
                self._collect_entity_ids(value, entity_ids, new_path)
                
        elif isinstance(obj, list):
            # Process list items
            for i, item in enumerate(obj):
                new_path = f"{path}[{i}]"
                self._collect_entity_ids(item, entity_ids, new_path)
    
    def _build_restructuring_prompt(self, 
                                    data: Dict[str, Any], 
                                    relationships: Dict[str, List[str]],
                                    data_models_description: str) -> str:
        """Build a prompt for OpenAI to restructure the JSON.
        
        Args:
            data: The original JSON data
            relationships: The analyzed relationships
            data_models_description: Description of data models
            
        Returns:
            A prompt string for OpenAI
        """
        # Format relationships for the prompt
        relationship_text = ""
        for entity_type, relation_list in relationships.items():
            relationship_text += f"\n### {entity_type} Relationships:\n"
            for relation in relation_list:
                relationship_text += f"- {relation}\n"
        
        # If no relationships were found, add a note
        if not relationship_text:
            relationship_text = "\nNo explicit ID relationships were found. Please infer relationships from the data structure and field names."
        
        return f"""You are an expert data architect specializing in JSON restructuring. Your task is to analyze and restructure a JSON object to maximize parent-child relationships based on ID references.

The following describes the property management data models used in the system:
{data_models_description}

I've analyzed the input JSON and found these ID relationships:
{relationship_text}

Original JSON structure:
```json
{json.dumps(data, indent=2)}
```

Please restructure this JSON to create a more hierarchical representation with nested parent-child relationships. Follow these guidelines:

1. Analyze the existing structure and ID references to identify potential parent-child relationships.
2. Move child entities inside their parent entities when a relationship can be established.
3. Maintain all existing data and ensure no information is lost during restructuring.
4. Use the ID references to connect entities (e.g., if a tenant has a propertyId, it should be nested under that property).
5. Prefer deeper hierarchies over flat structures when it makes logical sense.
6. Keep ID reference fields even when restructuring to maintain data integrity.
7. Optimize the structure so that entities are placed where they provide the most context.
8. Consider that properties can contain units, units can contain tenants, tenants can have leases, etc.
9. Focus on creating a structure that would be most helpful for understanding the relationships at a glance.

Return ONLY the restructured JSON with no additional explanation or commentary. The response should be valid JSON that could be directly parsed.
"""
    
    def _get_restructured_json(self, prompt: str) -> Dict[str, Any]:
        """Get restructured JSON from OpenAI based on the prompt.
        
        Args:
            prompt: The prompt for OpenAI
            
        Returns:
            The restructured JSON data or None if failed
        """
        try:
            # Log request to OpenAI
            logger.info("Sending restructuring request to OpenAI...")
            
            # Call OpenAI with structured output as JSON object
            system_message = "You are a data architect that restructures JSON to maximize parent-child relationships."
            
            response = self.gpt_client.client.chat.completions.create(
                model=self.gpt_client.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            
            # Extract the response content
            response_content = response.choices[0].message.content
            
            if not response_content:
                logger.error("Empty response from OpenAI")
                return None
                
            # Parse the response as JSON
            try:
                restructured_data = json.loads(response_content)
                logger.info("Successfully parsed restructured JSON from OpenAI")
                return restructured_data
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse OpenAI response as JSON: {str(e)}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting restructured JSON from OpenAI: {str(e)}")
            logger.error(traceback.format_exc())
            return None

# Convenience function for direct use
def restructure_json(data: Dict[str, Any]) -> Dict[str, Any]:
    """Restructure a JSON object to maximize parent-child relationships.
    
    Args:
        data: The JSON data to restructure
        
    Returns:
        The restructured JSON data
    """
    restructurer = JSONRestructurer()
    return restructurer.restructure_json(data) 