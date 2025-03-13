"""Database management for property updates and modifications."""

import json
import os
from typing import Dict, Any, Optional
from dataclasses import asdict
from data_models import *

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
            if os.path.exists(self.schema_path):
                with open(self.schema_path, 'r') as f:
                    return json.load(f)

            # Create new schema from template
            template_path = os.path.join(os.path.dirname(__file__), 'templates', f"{template_name}.json")
            if os.path.exists(template_path):
                with open(template_path, 'r') as f:
                    template = json.load(f)
            else:
                template = {"property": {}}  # Minimal template if none found

            # Ensure directory exists and save new schema
            os.makedirs(os.path.dirname(os.path.abspath(self.schema_path)), exist_ok=True)
            with open(self.schema_path, 'w') as f:
                json.dump(template, f, indent=2)
            return template
        except Exception as e:
            print(f"Error loading/creating schema: {str(e)}")
            return {"property": {}}

    def _save_data(self) -> None:
        """Save current data to JSON file."""
        try:
            self.data['property'] = json.loads(Property.to_json(self.property))
            with open(self.schema_path, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Error saving data: {str(e)}")

    def _initialize_property(self) -> Property:
        """Initialize property from schema or create a new one."""
        if 'property' in self.data:
            return Property.from_dict(self.data['property'])
        return Property(name="New Property")

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
        """Update property information."""
        try:
            # Create address if it doesn't exist
            if 'address' in property_data and not self.property.address:
                self.property.address = Address()
                
            # Create owner if it doesn't exist
            if 'owner' in property_data and not self.property.owner:
                self.property.owner = Entity(name="Owner")
                
            self._update_entity(self.property, property_data)
            self._save_data()
            return True
        except Exception as e:
            print(f"Error updating property: {str(e)}")
            return False

    def update_owner(self, owner_data: Dict[str, Any]) -> bool:
        """Update owner information."""
        try:
            # Create owner if it doesn't exist
            if not self.property.owner:
                self.property.owner = Entity(name="Owner")
                
            # Create contact info if it doesn't exist
            if 'contactInfo' in owner_data and not self.property.owner.contactInfo:
                self.property.owner.contactInfo = ContactInfo()
                
            # Create address if it doesn't exist
            if 'address' in owner_data.get('contactInfo', {}) and not self.property.owner.contactInfo.address:
                self.property.owner.contactInfo.address = Address()
                
            self._update_entity(self.property.owner, owner_data)
            self._save_data()
            return True
        except Exception as e:
            print(f"Error updating owner: {str(e)}")
            return False

    def update_unit(self, unit_number: str, unit_data: Dict[str, Any]) -> bool:
        """Update unit information."""
        try:
            unit = self._get_unit(unit_number)
            if not unit:
                # Create new unit if it doesn't exist
                if not self.property.units:
                    self.property.units = []
                unit = Unit(unitNumber=unit_number, propertyId=self.property.name)
                self.property.units.append(unit)
                
            self._update_entity(unit, unit_data)
            self._save_data()
            return True
        except Exception as e:
            print(f"Error updating unit: {str(e)}")
            return False

    def update_tenant(self, unit_number: str, tenant_data: Dict[str, Any]) -> bool:
        """Update tenant information for a specific unit."""
        try:
            unit = self._get_unit(unit_number)
            if not unit:
                # Create unit if it doesn't exist
                if not self.property.units:
                    self.property.units = []
                unit = Unit(unitNumber=unit_number, propertyId=self.property.name)
                self.property.units.append(unit)
                
            # Get tenant name from data
            tenant_name = tenant_data.get('name')
            if not tenant_name:
                print("Tenant name is required")
                return False
                
            # Create tenant if it doesn't exist
            if not unit.currentTenant:
                unit.currentTenant = Tenant(name=tenant_name)
                
            # Create contact info if it doesn't exist
            if 'contactInfo' in tenant_data and not unit.currentTenant.contactInfo:
                unit.currentTenant.contactInfo = ContactInfo()
                
            # Create address if it doesn't exist
            if 'address' in tenant_data.get('contactInfo', {}) and not unit.currentTenant.contactInfo.address:
                unit.currentTenant.contactInfo.address = Address()
                
            self._update_entity(unit.currentTenant, tenant_data)
            self._save_data()
            return True
        except Exception as e:
            print(f"Error updating tenant: {str(e)}")
            return False

    def update_lease(self, unit_number: str, lease_data: Dict[str, Any]) -> bool:
        """Update lease information for a specific unit."""
        try:
            unit = self._get_unit(unit_number)
            if not unit:
                # Create unit if it doesn't exist
                if not self.property.units:
                    self.property.units = []
                unit = Unit(unitNumber=unit_number, propertyId=self.property.name)
                self.property.units.append(unit)
                
            # Create tenant if it doesn't exist
            if not unit.currentTenant:
                # Try to get tenant name from lease data or use a default
                tenant_name = lease_data.get('tenantId', f"Tenant_{unit_number}")
                unit.currentTenant = Tenant(name=tenant_name)
                
            # Set required IDs
            lease_data['propertyId'] = self.property.name
            lease_data['unitId'] = unit.unitNumber
            lease_data['tenantId'] = unit.currentTenant.name

            # Convert numeric fields to float if present
            for field in ['rentAmount', 'securityDeposit', 'nextRentAmount']:
                if field in lease_data and lease_data[field] is not None:
                    lease_data[field] = float(lease_data[field])

            if not unit.currentTenant.lease:
                # Create new lease
                unit.currentTenant.lease = Lease(
                    propertyId=self.property.name,
                    unitId=unit.unitNumber,
                    tenantId=unit.currentTenant.name
                )
                
            # Update lease fields
            current_lease = unit.currentTenant.lease
            for field, value in lease_data.items():
                if hasattr(current_lease, field) and field not in ['propertyId', 'unitId', 'tenantId']:
                    setattr(current_lease, field, value)

            self._save_data()
            return True
        except Exception as e:
            print(f"Error updating lease: {str(e)}")
            return False

    def add_document(self, entity_type: str, entity_id: str, document_data: Dict[str, Any]) -> bool:
        """Add a new document to an entity."""
        try:
            document = Document.from_dict(document_data)
            target = self.property if entity_type == 'property' else self._get_unit(entity_id)
            
            if not target:
                print(f"{entity_type.capitalize()} {entity_id} not found")
                return False

            if not target.documents:
                target.documents = []
            target.documents.append(document)
            
            self._save_data()
            return True
        except Exception as e:
            print(f"Error adding document: {str(e)}")
            return False

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