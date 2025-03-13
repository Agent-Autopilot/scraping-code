"""Main interface for property management system.

This module provides a simple interface for managing properties, combining
the functionality of the data manager and NLP processor.
"""

import os
from typing import Dict, Any, Optional, List
from src.data_manager import DataManager
from src.nlp_processor import UpdateProcessor
from src.data_models import Property, Unit, Tenant, Lease, Document, Photo
from src.bulk_processor import process_text_updates

class PropertyManager:
    """High-level interface for property management operations."""
    
    def __init__(self, schema_path: Optional[str] = None, template_name: str = 'default'):
        """Initialize the property manager.
        
        Args:
            schema_path: Optional path to the schema file. If None, creates
                       'schema.json' in the current directory.
            template_name: Name of the template to use for new schemas (without .json extension)
        """
        self.schema_path = schema_path
        self.data_manager = DataManager(schema_path, template_name)
        self.nlp_processor = UpdateProcessor(schema_path)
        
    def process_text_update(self, text: str) -> bool:
        """Process a natural language update.
        
        Args:
            text: Natural language description of the update
            
        Returns:
            bool: True if update was successful
        """
        # Get the analysis and instructions from the NLP processor
        result = self.nlp_processor.process_update(text)
        if not result:
            return False
            
        # The new format returns analysis and instructions directly
        instructions = result.get('instructions', [])
        if not instructions:
            print("No instructions generated from update")
            return False
            
        # Process each instruction
        # For simplicity, we'll consider the update successful if at least one instruction succeeds
        success = False
        for instruction in instructions:
            # Process each instruction individually
            if self.process_single_instruction(instruction):
                success = True
                
        return success
    
    def process_single_instruction(self, instruction: str) -> bool:
        """Process a single natural language instruction.
        
        This is a simplified version that just passes the instruction back to process_text_update
        but could be expanded to handle different types of instructions directly.
        
        Args:
            instruction: Natural language instruction
            
        Returns:
            bool: True if instruction was processed successfully
        """
        # Use the bulk processor to process the instruction
        results = process_text_updates([instruction], self.data_manager)
        return len(results['failed']) == 0
        
    def get_property(self) -> Property:
        """Get the property from the data manager."""
        return self.data_manager.get_property()
        
    def get_units(self) -> List[Unit]:
        """Get all units from the data manager."""
        return self.data_manager.get_units()
        
    def get_unit(self, unit_number: str) -> Optional[Unit]:
        """Get a specific unit by number."""
        return self.data_manager.get_unit(unit_number)
        
    def get_tenant(self, unit_number: str) -> Optional[Tenant]:
        """Get the tenant for a specific unit."""
        return self.data_manager.get_tenant(unit_number)
        
    def get_lease(self, unit_number: str) -> Optional[Lease]:
        """Get the lease for a specific unit."""
        return self.data_manager.get_lease(unit_number)
        
    def add_document(self, entity_type: str, entity_id: str, 
                    doc_type: str, url: str, name: Optional[str] = None) -> bool:
        """Add a document to an entity.
        
        Args:
            entity_type: Type of entity ('property', 'owner', 'unit', 'tenant')
            entity_id: ID of the entity (property name, owner name, unit number, tenant name)
            doc_type: Type of document (e.g., 'lease', 'inspection', 'receipt')
            url: URL or path to the document
            name: Optional name for the document
            
        Returns:
            bool: True if document was added successfully
        """
        return self.data_manager.add_document(entity_type, entity_id, doc_type, url, name)
        
    def get_all_documents(self) -> List[Document]:
        """Get all documents across all entities.
        
        Returns:
            List of all documents
        """
        return self.data_manager.get_all_documents()
        
    def add_photo(self, unit_number: str, url: str, description: Optional[str] = None) -> bool:
        """Add a photo to a unit.
        
        Args:
            unit_number: Unit number
            url: URL or path to the photo
            description: Optional description of the photo
            
        Returns:
            bool: True if photo was added successfully
        """
        return self.data_manager.add_photo(unit_number, url, description)
        
    def get_all_photos(self) -> List[Photo]:
        """Get all photos across all units.
        
        Returns:
            List of all photos
        """
        return self.data_manager.get_all_photos()

def main():
    """Example usage of the property manager."""
    manager = PropertyManager()
    
    # Example: Process a natural language update
    update = "Create a new property called Sample Property at 123 Main St, Sample City, ST 12345"
    success = manager.process_text_update(update)
    
    if success:
        print("Update successful!")
        property_data = manager.get_property()
        print(f"Property: {property_data.name}")
        print(f"Address: {property_data.address.street}, {property_data.address.city}, {property_data.address.state} {property_data.address.zip}")
    else:
        print("Update failed.")

if __name__ == "__main__":
    main() 