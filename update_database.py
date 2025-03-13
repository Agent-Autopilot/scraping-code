import json
from typing import Dict, Any, Optional
from models import *
from update_processor import UpdateProcessor
from dataclasses import asdict

class DataManager:
    def __init__(self, json_file: str = 'schema.json'):
        self.json_file = json_file
        self.data = self._load_data()
        self.property = self._initialize_property()

    def _load_data(self) -> Dict:
        """Load data from JSON file"""
        with open(self.json_file, 'r') as f:
            return json.load(f)

    def _save_data(self) -> None:
        """Save current data to JSON file"""
        # Convert property object back to dictionary
        self.data['property'] = json.loads(Property.to_json(self.property))
        with open(self.json_file, 'w') as f:
            json.dump(self.data, f, indent=2)

    def _initialize_property(self) -> Property:
        """Initialize Property object from JSON data"""
        return Property.from_dict(self.data['property'])

    def update_property(self, property_data: Dict[str, Any]) -> bool:
        """Update property information"""
        try:
            # Update property fields
            for key, value in property_data.items():
                if key == 'address':
                    # Handle address update
                    if isinstance(value, dict):
                        self.property.address = Address.from_dict(value)
                    else:
                        print("Invalid address format")
                        return False
                else:
                    setattr(self.property, key, value)

            # Update JSON data
            self._save_data()
            return True

        except Exception as e:
            print(f"Error updating property: {str(e)}")
            return False

    def update_owner(self, owner_data: Dict[str, Any]) -> bool:
        """Update owner information"""
        try:
            # Update owner fields
            for key, value in owner_data.items():
                if key == 'contactInfo':
                    # Handle contact info update
                    if isinstance(value, dict):
                        if hasattr(self.property.owner.contactInfo, 'address') and 'address' in value:
                            # Handle nested address update
                            value['address'] = Address.from_dict(value['address'])
                        for contact_key, contact_value in value.items():
                            setattr(self.property.owner.contactInfo, contact_key, contact_value)
                    else:
                        print("Invalid contactInfo format")
                        return False
                else:
                    setattr(self.property.owner, key, value)

            # Update JSON data
            self._save_data()
            return True

        except Exception as e:
            print(f"Error updating owner: {str(e)}")
            return False

    def update_tenant(self, unit_number: str, tenant_data: Dict[str, Any]) -> bool:
        """Update tenant information"""
        try:
            # Find the unit
            unit = next((u for u in self.property.units if u.unitNumber == unit_number), None)
            if not unit:
                print(f"Unit {unit_number} not found")
                return False

            # Update tenant data
            if not unit.currentTenant:
                # Create new tenant with contact info
                if 'contactInfo' not in tenant_data:
                    print("Missing contactInfo for new tenant")
                    return False
                unit.currentTenant = Tenant.from_dict(tenant_data)
            else:
                # Update only provided fields
                for key, value in tenant_data.items():
                    if key == 'contactInfo':
                        # Update contact info fields
                        for contact_key, contact_value in value.items():
                            setattr(unit.currentTenant.contactInfo, contact_key, contact_value)
                    elif key == 'lease':
                        # Update or create lease
                        if unit.currentTenant.lease:
                            for lease_key, lease_value in value.items():
                                setattr(unit.currentTenant.lease, lease_key, lease_value)
                        else:
                            unit.currentTenant.lease = Lease.from_dict(value)
                    else:
                        setattr(unit.currentTenant, key, value)

            # Update JSON data
            self._save_data()
            return True

        except Exception as e:
            print(f"Error updating tenant: {str(e)}")
            return False

    def update_lease(self, unit_number: str, lease_data: Dict[str, Any]) -> bool:
        """Update lease information"""
        try:
            # Find the unit
            unit = next((u for u in self.property.units if u.unitNumber == unit_number), None)
            if not unit:
                print(f"Unit {unit_number} not found")
                return False

            if not unit.currentTenant:
                print(f"No tenant in unit {unit_number}")
                return False

            # Update lease data
            if not unit.currentTenant.lease:
                unit.currentTenant.lease = Lease.from_dict(lease_data)
            else:
                # Update only provided fields
                for key, value in lease_data.items():
                    setattr(unit.currentTenant.lease, key, value)

            # Update JSON data
            self._save_data()
            return True

        except Exception as e:
            print(f"Error updating lease: {str(e)}")
            return False

    def add_document(self, entity_type: str, entity_id: str, document_data: Dict[str, Any]) -> bool:
        """Add a new document to an entity"""
        try:
            # Create new document
            document = Document.from_dict(document_data)
            
            # Find the entity and add document
            if entity_type == 'property':
                if not self.property.documents:
                    self.property.documents = []
                self.property.documents.append(document)
            elif entity_type == 'unit':
                unit = next((u for u in self.property.units if u.unitNumber == entity_id), None)
                if not unit:
                    print(f"Unit {entity_id} not found")
                    return False
                if not unit.documents:
                    unit.documents = []
                unit.documents.append(document)
            else:
                print(f"Unsupported entity type: {entity_type}")
                return False

            # Update JSON data
            self._save_data()
            return True

        except Exception as e:
            print(f"Error adding document: {str(e)}")
            return False

    def update_unit(self, unit_number: str, unit_data: Dict[str, Any]) -> bool:
        """Update unit information or create a new unit"""
        try:
            # Find the unit or create a new one
            unit = next((u for u in self.property.units if u.unitNumber == unit_number), None)
            if not unit:
                # Create new unit
                if not self.property.units:
                    self.property.units = []
                unit_data['unitNumber'] = unit_number  # Ensure unit number is set
                new_unit = Unit.from_dict(unit_data)
                self.property.units.append(new_unit)
            else:
                # Update existing unit
                for key, value in unit_data.items():
                    if key == 'photos':
                        # Handle photos update
                        if not unit.photos:
                            unit.photos = []
                        for photo_data in value:
                            unit.photos.append(Photo.from_dict(photo_data))
                    elif key == 'currentTenant':
                        # Handle tenant update
                        if isinstance(value, dict):
                            unit.currentTenant = Tenant.from_dict(value)
                    else:
                        setattr(unit, key, value)

            # Update JSON data
            self._save_data()
            return True

        except Exception as e:
            print(f"Error updating unit: {str(e)}")
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