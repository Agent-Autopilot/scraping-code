import json
from models import (
    Address,
    ContactInfo,
    Document,
    Photo,
    Lease,
    Tenant,
    Unit,
    Entity,
    Property
)

def test_schema():
    # Load the JSON data
    with open('schema.json', 'r') as f:
        data = json.load(f)
    
    try:
        # Create Property object
        property_data = data['property']
        
        # Create Address
        address = Address(**property_data['address'])
        print(f"✓ Created Address: {address}")
        
        # Create Owner's ContactInfo and Entity
        owner_contact = ContactInfo(**property_data['owner']['contactInfo'])
        owner = Entity(**{**property_data['owner'], 'contactInfo': owner_contact})
        print(f"✓ Created Entity: {owner}")
        
        # Create Units with Tenants
        units = []
        if 'units' in property_data:
            for unit_data in property_data['units']:
                # Create Tenant's ContactInfo and Lease if exists
                if 'currentTenant' in unit_data:
                    tenant_contact = ContactInfo(**unit_data['currentTenant']['contactInfo'])
                    tenant_data = {**unit_data['currentTenant'], 'contactInfo': tenant_contact}
                    if 'lease' in tenant_data:
                        lease = Lease(**tenant_data['lease'])
                        tenant_data['lease'] = lease
                    tenant = Tenant(**tenant_data)
                    unit_data['currentTenant'] = tenant
                
                # Create Photos if exist
                if 'photos' in unit_data:
                    photos = [Photo(**photo) for photo in unit_data['photos']]
                    unit_data['photos'] = photos
                
                unit = Unit(**unit_data)
                units.append(unit)
            print(f"✓ Created {len(units)} Units")
        
        # Create Property
        property = Property(
            name=property_data['name'],
            address=address,
            owner=owner,
            units=units
        )
        print(f"✓ Created Property: {property.name}")
        
        # Test accessing nested data
        if property.units:
            unit = property.units[0]
            if unit.currentTenant and unit.currentTenant.lease:
                print(f"\nSample Data Access:")
                print(f"Unit {unit.unitNumber} is rented to {unit.currentTenant.name}")
                print(f"Rent: ${unit.currentTenant.lease.rentAmount}")
                print(f"Lease period: {unit.currentTenant.lease.startDate} to {unit.currentTenant.lease.endDate}")
        
        print("\n✓ All tests passed successfully!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    test_schema() 