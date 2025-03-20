"""Database management for property updates and modifications."""

import json
import os
from typing import Dict, Any, Optional, List
from dataclasses import asdict
from src.data_models import *
from src.utils import FileManager, convert_numeric_fields, create_entity_if_missing

class DataManager:
    """Manages data persistence and updates for the property management system."""

    def __init__(self, schema_path: Optional[str] = None, template_name: str = 'default'):
        """Initialize the data manager.
        
        Args:
            schema_path: Path to the JSON schema file. If None, creates a new file
                       in the current directory.
            template_name: Name of the template to use for new schemas
        """
        self.schema_path = schema_path or 'schema.json'
        self.data = self._load_schema(template_name)
        self.property = self._initialize_property()

    def _load_schema(self, template_name: str) -> Dict:
        """Load schema from file or create new from template."""
        try:
            # Try to load existing schema
            data = FileManager.load_json(self.schema_path)
            if data:
                return data

            # Create new schema from template
            template_path = os.path.join(os.path.dirname(__file__), 'templates', f"{template_name}.json")
            template = FileManager.load_json(template_path)
            
            if not template:
                template = {"property": {}}  # Minimal template if none found

            # Save new schema
            FileManager.save_json(self.schema_path, template)
            return template
        except Exception as e:
            print(f"Error loading/creating schema: {str(e)}")
            return {"property": {}}

    def _save_data(self) -> None:
        """Save current data to JSON file."""
        try:
            # Update the data with the current property
            self.data["property"] = asdict(self.property)
            
            # Save to file
            FileManager.save_json(self.schema_path, self.data)
        except Exception as e:
            print(f"Error saving data: {str(e)}")

    def _initialize_property(self) -> Property:
        """Initialize property from data or create new."""
        try:
            property_data = self.data.get("property", {})
            return Property.from_dict(property_data)
        except Exception as e:
            print(f"Error initializing property: {str(e)}")
            return Property()

    def _get_unit(self, unit_number: str) -> Optional[Unit]:
        """Get unit by number or return None."""
        if not self.property.units:
            return None
        # Try exact match first
        unit = next((u for u in self.property.units if u.unitNumber == unit_number), None)
        if unit:
            return unit
        # Try case-insensitive match
        unit = next((u for u in self.property.units if u.unitNumber.lower() == unit_number.lower()), None)
        if unit:
            return unit
        # Try matching just the unit letter/number
        unit_id = unit_number.split()[-1]  # Get last part of unit name (e.g., "A" from "Woodbridge Unit A")
        return next((u for u in self.property.units if u.unitNumber.endswith(unit_id)), None)

    def _update_entity(self, entity: Any, data: Dict[str, Any], special_handlers: Dict = None) -> None:
        """Generic entity update helper."""
        for key, value in data.items():
            if special_handlers and key in special_handlers:
                special_handlers[key](value)
            elif isinstance(value, dict):
                if hasattr(entity, key) and getattr(entity, key) is not None:
                    self._update_entity(getattr(entity, key), value)
                else:
                    setattr(entity, key, globals()[key.capitalize()].from_dict(value))
            else:
                setattr(entity, key, value)

    def update_property(self, property_data: Dict[str, Any]) -> bool:
        """Update property information.
        
        Args:
            property_data: Dictionary containing property fields to update
            
        Returns:
            bool: True if update was successful
        """
        try:
            # Create a copy of the current property as a dictionary
            current_property = asdict(self.property)
            
            # Update with new data
            self._update_nested_dict(current_property, property_data)
            
            # Convert back to Property object
            self.property = Property.from_dict(current_property)
            
            # Save changes
            self._save_data()
            return True
        except Exception as e:
            print(f"Error updating property: {str(e)}")
            return False

    def update_owner(self, owner_data: Dict[str, Any]) -> bool:
        """Update owner information.
        
        Args:
            owner_data: Dictionary containing owner fields to update
            
        Returns:
            bool: True if update was successful
        """
        try:
            # Create owner if it doesn't exist
            if not self.property.owner:
                self.property.owner = Entity()
            
            # Create a copy of the current owner as a dictionary
            current_owner = asdict(self.property.owner)
            
            # Update with new data
            self._update_nested_dict(current_owner, owner_data)
            
            # Convert back to Entity object
            self.property.owner = Entity.from_dict(current_owner)
            
            # Save changes
            self._save_data()
            return True
        except Exception as e:
            print(f"Error updating owner: {str(e)}")
            return False

    def update_unit(self, unit_number: str, unit_data: Dict[str, Any]) -> bool:
        """Update unit information.
        
        Args:
            unit_number: Unit identifier
            unit_data: Dictionary containing unit fields to update
            
        Returns:
            bool: True if update was successful
        """
        try:
            # Initialize units list if it doesn't exist
            if not self.property.units:
                self.property.units = []
            
            # Find the unit or create a new one
            unit = next((u for u in self.property.units if u.unitNumber == unit_number), None)
            if not unit:
                unit = Unit(unitNumber=unit_number, propertyId=self.property.name)
                self.property.units.append(unit)
            
            # Create a copy of the current unit as a dictionary
            current_unit = asdict(unit)
            
            # Update with new data
            self._update_nested_dict(current_unit, unit_data)
            
            # Convert back to Unit object
            updated_unit = Unit.from_dict(current_unit)
            
            # Replace the unit in the list
            for i, u in enumerate(self.property.units):
                if u.unitNumber == unit_number:
                    self.property.units[i] = updated_unit
                    break
            else:
                self.property.units.append(updated_unit)
            
            # Save changes
            self._save_data()
            return True
        except Exception as e:
            print(f"Error updating unit: {str(e)}")
            return False

    def update_tenant(self, unit_number: str, tenant_data: Dict[str, Any]) -> bool:
        """Update tenant information for a unit.
        
        Args:
            unit_number: Unit identifier
            tenant_data: Dictionary containing tenant fields to update
            
        Returns:
            bool: True if update was successful
        """
        try:
            # Find the unit or create a new one
            unit = self._get_unit(unit_number)
            if not unit:
                unit_data = {"unitNumber": unit_number, "propertyId": self.property.name}
                if not self.update_unit(unit_number, unit_data):
                    return False
                unit = self._get_unit(unit_number)
            
            # Create tenant if it doesn't exist
            if not unit.currentTenant:
                unit.currentTenant = Tenant()
            
            # Create a copy of the current tenant as a dictionary
            current_tenant = asdict(unit.currentTenant)
            
            # Update with new data
            self._update_nested_dict(current_tenant, tenant_data)
            
            # Set required IDs
            if "name" in tenant_data and not current_tenant.get("lease", {}).get("tenantId"):
                if not current_tenant.get("lease"):
                    current_tenant["lease"] = {}
                current_tenant["lease"]["tenantId"] = tenant_data["name"]
            
            # Convert back to Tenant object
            unit.currentTenant = Tenant.from_dict(current_tenant)
            
            # Save changes
            self._save_data()
            return True
        except Exception as e:
            print(f"Error updating tenant: {str(e)}")
            return False

    def update_lease(self, unit_number: str, lease_data: Dict[str, Any]) -> bool:
        """Update lease information for a unit.
        
        Args:
            unit_number: Unit identifier
            lease_data: Dictionary containing lease fields to update
            
        Returns:
            bool: True if update was successful
        """
        try:
            # Find the unit or create a new one
            unit = self._get_unit(unit_number)
            if not unit:
                unit_data = {"unitNumber": unit_number, "propertyId": self.property.name}
                if not self.update_unit(unit_number, unit_data):
                    return False
                unit = self._get_unit(unit_number)
            
            # Create tenant if it doesn't exist
            if not unit.currentTenant:
                tenant_data = {"name": f"Tenant_{unit_number}"}
                if not self.update_tenant(unit_number, tenant_data):
                    return False
                unit = self._get_unit(unit_number)
            
            # Create lease if it doesn't exist
            if not unit.currentTenant.lease:
                unit.currentTenant.lease = Lease(
                    propertyId=self.property.name,
                    unitId=unit_number,
                    tenantId=unit.currentTenant.name
                )
            
            # Create a copy of the current lease as a dictionary
            current_lease = asdict(unit.currentTenant.lease)
            
            # Set required IDs
            current_lease["propertyId"] = self.property.name
            current_lease["unitId"] = unit_number
            current_lease["tenantId"] = unit.currentTenant.name
            
            # Convert numeric fields
            lease_data = convert_numeric_fields(lease_data, ["rentAmount", "securityDeposit"])
            
            # Update with new data
            self._update_nested_dict(current_lease, lease_data)
            
            # Convert back to Lease object
            unit.currentTenant.lease = Lease.from_dict(current_lease)
            
            # Save changes
            self._save_data()
            return True
        except Exception as e:
            print(f"Error updating lease: {str(e)}")
            return False

    def _update_nested_dict(self, target: Dict, source: Dict) -> None:
        """Update nested dictionary with values from another dictionary.
        
        Args:
            target: Target dictionary to update
            source: Source dictionary with new values
        """
        for key, value in source.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                self._update_nested_dict(target[key], value)
            else:
                target[key] = value

    def add_document(self, entity_type: str, entity_id: str, doc_type: str, url: str, name: Optional[str] = None) -> bool:
        """Add a document to an entity.
        
        Args:
            entity_type: Type of entity ('property', 'owner', 'unit', 'tenant')
            entity_id: ID of the entity (property name, owner name, unit number, tenant name)
            doc_type: Type of document
            url: URL to the document
            name: Optional document name
            
        Returns:
            bool: True if document was added successfully
        """
        try:
            # Create document data
            doc_data = {
                'id': f"{doc_type}-{len(self.get_all_documents()) + 1}",
                'type': doc_type,
                'url': url,
                'name': name
            }
            
            # Add document to the appropriate entity
            if entity_type == 'property':
                if not self.property.documents:
                    self.property.documents = []
                self.property.documents.append(Document.from_dict(doc_data))
            elif entity_type == 'owner':
                if not self.property.owner:
                    self.property.owner = Entity()
                if not self.property.owner.documents:
                    self.property.owner.documents = []
                self.property.owner.documents.append(Document.from_dict(doc_data))
            elif entity_type == 'unit':
                unit = self._get_unit(entity_id)
                if not unit:
                    return False
                if not unit.documents:
                    unit.documents = []
                unit.documents.append(Document.from_dict(doc_data))
            elif entity_type == 'tenant':
                # Find the unit with this tenant
                unit = next((u for u in self.property.units if u.currentTenant and u.currentTenant.name == entity_id), None)
                if not unit:
                    return False
                if not unit.currentTenant.documents:
                    unit.currentTenant.documents = []
                unit.currentTenant.documents.append(Document.from_dict(doc_data))
            else:
                return False
            
            # Save changes
            self._save_data()
            return True
        except Exception as e:
            print(f"Error adding document: {str(e)}")
            return False

    def add_photo(self, unit_number: str, url: str, description: Optional[str] = None) -> bool:
        """Add a photo to a unit.
        
        Args:
            unit_number: Unit identifier
            url: URL to the photo
            description: Optional photo description
            
        Returns:
            bool: True if photo was added successfully
        """
        try:
            # Find the unit
            unit = self._get_unit(unit_number)
            if not unit:
                return False
            
            # Create photo data
            photo_data = {
                'id': f"photo-{len(self.get_all_photos()) + 1}",
                'url': url,
                'description': description
            }
            
            # Add photo to the unit
            if not unit.photos:
                unit.photos = []
            unit.photos.append(Photo.from_dict(photo_data))
            
            # Save changes
            self._save_data()
            return True
        except Exception as e:
            print(f"Error adding photo: {str(e)}")
            return False

    def get_property(self) -> Property:
        """Get the current property."""
        return self.property
        
    def get_units(self) -> List[Unit]:
        """Get all units in the property."""
        return self.property.units or []
        
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
        
    def get_all_documents(self) -> List[Document]:
        """Get all documents across all entities."""
        docs = self.property.documents or []
        
        if self.property.owner and self.property.owner.documents:
            docs.extend(self.property.owner.documents)
            
        for unit in self.get_units():
            if unit.documents:
                docs.extend(unit.documents)
            if unit.currentTenant and unit.currentTenant.documents:
                docs.extend(unit.currentTenant.documents)
                
        return docs
        
    def get_all_photos(self) -> List[Photo]:
        """Get all photos across all units."""
        photos = []
        for unit in self.get_units():
            if unit.photos:
                photos.extend(unit.photos)
        return photos

def main():
    # Initialize the data manager and processor
    manager = DataManager()
    processor = UpdateProcessor()
    
    # Example usage loop
    while True:
        print("\nEnter your update (or 'quit' to exit):")
        user_input = input("> ")
        
        if user_input.lower() == 'quit':
            break
        
        # Process the update using the processor
        success = processor.process_update(user_input, manager)
        
        if success:
            print("Update successful!")
        else:
            print("Update failed.")

if __name__ == "__main__":
    main() 