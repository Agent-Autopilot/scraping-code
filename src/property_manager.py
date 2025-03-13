"""Main interface for property management system.

This module provides a simple interface for managing properties, combining
the functionality of the data manager and NLP processor.
"""

import os
from typing import Dict, Any, Optional, List
from data_manager import DataManager
from nlp_processor import UpdateProcessor
from data_models import Property, Unit, Tenant, Lease, Document, Photo

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
        update = self.nlp_processor.process_update(text)
        if not update:
            return False
            
        update_type = update['type']
        update_data = update['data']
        
        if update_type == 'property':
            property_data = update_data.get('Property_data')
            if not property_data:
                print("Missing Property_data in update")
                return False
            return self.data_manager.update_property(property_data)
        elif update_type == 'owner':
            owner_data = update_data.get('Owner_data')
            if not owner_data:
                print("Missing Owner_data in update")
                return False
            return self.data_manager.update_owner(owner_data)
        elif update_type == 'tenant':
            unit_number = update_data.pop('unitNumber', None)
            if not unit_number:
                print("Missing unit number for tenant update")
                return False
            return self.data_manager.update_tenant(unit_number, update_data)
        elif update_type == 'lease':
            unit_number = update_data.pop('unitNumber', None)
            if not unit_number:
                print("Missing unit number for lease update")
                return False
            return self.data_manager.update_lease(unit_number, update_data)
        elif update_type == 'unit':
            unit_number = update_data.pop('unitNumber', None)
            if not unit_number:
                print("Missing unit number for unit update")
                return False
            return self.data_manager.update_unit(unit_number, update_data)
        else:
            print(f"Unsupported update type: {update_type}")
            return False
            
    def get_property(self) -> Property:
        """Get the current property data."""
        return self.data_manager.property
        
    def get_units(self) -> List[Unit]:
        """Get all units in the property."""
        return self.data_manager.property.units or []
        
    def get_unit(self, unit_number: str) -> Optional[Unit]:
        """Get a specific unit by number."""
        units = self.get_units()
        return next((u for u in units if u.unitNumber == unit_number), None)
        
    def get_tenant(self, unit_number: str) -> Optional[Tenant]:
        """Get the tenant of a specific unit."""
        unit = self.get_unit(unit_number)
        return unit.currentTenant if unit else None
        
    def get_lease(self, unit_number: str) -> Optional[Lease]:
        """Get the lease for a specific unit."""
        tenant = self.get_tenant(unit_number)
        return tenant.lease if tenant else None
        
    def add_document(self, entity_type: str, entity_id: str, 
                    doc_type: str, url: str, name: Optional[str] = None) -> bool:
        """Add a document to a property or unit.
        
        Args:
            entity_type: 'property' or 'unit'
            entity_id: Property name or unit number
            doc_type: Type of document (e.g., 'lease', 'insurance')
            url: URL to the document
            name: Optional document name
            
        Returns:
            bool: True if document was added successfully
        """
        doc_data = {
            'id': f"{doc_type}-{len(self.get_all_documents()) + 1}",
            'type': doc_type,
            'url': url,
            'name': name
        }
        return self.data_manager.add_document(entity_type, entity_id, doc_data)
        
    def get_all_documents(self) -> List[Document]:
        """Get all documents in the property."""
        docs = self.data_manager.property.documents or []
        for unit in self.get_units():
            if unit.documents:
                docs.extend(unit.documents)
        return docs
        
    def add_photo(self, unit_number: str, url: str, description: Optional[str] = None) -> bool:
        """Add a photo to a unit.
        
        Args:
            unit_number: Unit identifier
            url: URL to the photo
            description: Optional photo description
            
        Returns:
            bool: True if photo was added successfully
        """
        photo_data = {
            'id': f"photo-{len(self.get_all_photos()) + 1}",
            'url': url,
            'description': description
        }
        unit_data = {'photos': [photo_data]}
        return self.data_manager.update_unit(unit_number, unit_data)
        
    def get_all_photos(self) -> List[Photo]:
        """Get all photos in the property."""
        photos = []
        for unit in self.get_units():
            if unit.photos:
                photos.extend(unit.photos)
        return photos

def main():
    """Example usage of the PropertyManager."""
    # Create a new property manager (will create schema.json if it doesn't exist)
    manager = PropertyManager()
    
    # Process some natural language updates
    updates = [
        "Create a new property called Sunset Apartments at 123 Main St, Boston, MA 02108",
        "Add unit 101 with monthly rent of $2000",
        "Add John Doe as tenant in unit 101 with email john@email.com",
        "Upload lease document for unit 101 at https://example.com/lease.pdf"
    ]
    
    for update in updates:
        print(f"\nProcessing: {update}")
        success = manager.process_text_update(update)
        print("Success!" if success else "Failed.")
        
    # Get some information
    property = manager.get_property()
    print(f"\nProperty: {property.name}")
    
    units = manager.get_units()
    for unit in units:
        print(f"\nUnit {unit.unitNumber}:")
        if unit.currentTenant:
            print(f"Tenant: {unit.currentTenant.name}")
            if unit.currentTenant.lease:
                print(f"Rent: ${unit.currentTenant.lease.rentAmount}")

if __name__ == "__main__":
    main() 