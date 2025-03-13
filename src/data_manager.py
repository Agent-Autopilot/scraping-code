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
        """Initialize Property object from JSON data."""
        return Property.from_dict(self.data.get('property', {}))

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
            self._update_entity(self.property, property_data)
            self._save_data()
            return True
        except Exception as e:
            print(f"Error updating property: {str(e)}")
            return False

    def update_owner(self, owner_data: Dict[str, Any]) -> bool:
        """Update owner information."""
        try:
            self._update_entity(self.property.owner, owner_data)
            self._save_data()
            return True
        except Exception as e:
            print(f"Error updating owner: {str(e)}")
            return False

    def update_unit(self, unit_number: str, unit_data: Dict[str, Any]) -> bool:
        """Update or create a unit."""
        try:
            unit = self._get_unit(unit_number)
            if not unit:
                if not self.property.units:
                    self.property.units = []
                unit_data['unitNumber'] = unit_number
                unit_data['propertyId'] = self.property.name  # Set propertyId to property name
                self.property.units.append(Unit.from_dict(unit_data))
            else:
                def handle_photos(photos):
                    if not unit.photos:
                        unit.photos = []
                    for photo_data in photos:
                        unit.photos.append(Photo.from_dict(photo_data))

                special_handlers = {'photos': handle_photos}
                self._update_entity(unit, unit_data, special_handlers)

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
                print(f"Unit {unit_number} not found")
                return False

            if not unit.currentTenant:
                # Ensure contactInfo exists
                if 'contactInfo' not in tenant_data:
                    tenant_data['contactInfo'] = {}
                unit.currentTenant = Tenant.from_dict(tenant_data)
            else:
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
            if not unit or not unit.currentTenant:
                print(f"No tenant in unit {unit_number}")
                return False

            # Set required IDs
            lease_data['propertyId'] = self.property.name
            lease_data['unitId'] = unit.unitNumber
            lease_data['tenantId'] = unit.currentTenant.name

            # Convert numeric fields to float
            for field in ['rentAmount', 'securityDeposit', 'nextRentAmount']:
                if field in lease_data:
                    lease_data[field] = float(lease_data[field])

            if not unit.currentTenant.lease:
                # For new leases, ensure rentAmount is set
                if 'rentAmount' not in lease_data:
                    lease_data['rentAmount'] = 0.0
                unit.currentTenant.lease = Lease.from_dict(lease_data)
            else:
                # For updates to existing lease
                current_lease = unit.currentTenant.lease
                if 'rentAmount' in lease_data:
                    current_lease.rentAmount = lease_data['rentAmount']
                if 'securityDeposit' in lease_data:
                    current_lease.securityDeposit = lease_data['securityDeposit']
                if 'nextRentAmount' in lease_data:
                    current_lease.nextRentAmount = lease_data['nextRentAmount']
                if 'startDate' in lease_data:
                    current_lease.startDate = lease_data['startDate']
                if 'endDate' in lease_data:
                    current_lease.endDate = lease_data['endDate']

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