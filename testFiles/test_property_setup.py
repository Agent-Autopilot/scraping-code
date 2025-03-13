"""Test property management system setup with a duplex property."""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add src directory to Python path
src_path = str(Path(__file__).parent.parent / 'src')
sys.path.append(src_path)

from property_manager import PropertyManager

def setup_property():
    """Set up test property with two units using natural language commands."""
    # Initialize with test schema path
    schema_path = 'testFiles/test_schema2.json'
    
    # Only delete the schema if we're starting from scratch
    if not any(os.path.exists(p) for p in ['testFiles/test_schema2.json', 'testFiles/test_schema.json']):
        if os.path.exists(schema_path):
            os.remove(schema_path)
    
    manager = PropertyManager(schema_path=schema_path)
    
    # Create property and set owner details
    updates = [
        "Create a new property called Woodbridge Duplex at 10 Miles Ave, Woodbridge, CT 06525",
        "Set the owner to Woodbridge Community Partners LLC, which is an LLC",
        "Update the owner's email to vadim.tantsyura@gmail.com and phone to 6282599139",
        "Set the owner's address to 3 Willow Ct, Nyack, NY 10960",
        "Create unit Woodbridge Unit A",
        "Add tenant Rebecca to unit Woodbridge Unit A",
        "Set lease for Woodbridge Unit A starting July 1 2024 ending June 30 2025 with rent $2,475 and security deposit $4,850",
        "Create unit Woodbridge Unit B",
        "Add tenant Priscilla to unit Woodbridge Unit B",
        "Set lease for Woodbridge Unit B starting May 7 2024 ending April 30 2025 with rent $2,650 and security deposit $5,032"
    ]
    
    # Process each update
    for update in updates:
        print(f"\nProcessing: {update}")
        success = manager.process_text_update(update)
        if not success:
            print(f"Failed to process update: {update}")
            return False
        print("Success!")
    
    return verify_setup(manager)

def verify_setup(manager):
    """Verify the property setup is correct."""
    property = manager.get_property()
    
    # Verify property and owner details
    assert property.name == 'Woodbridge Duplex', f"Wrong property name: {property.name}"
    assert property.address.street == '10 Miles Ave', f"Wrong street: {property.address.street}"
    assert property.address.city == 'Woodbridge', f"Wrong city: {property.address.city}"
    assert property.address.state == 'CT', f"Wrong state: {property.address.state}"
    assert property.address.zip == '06525', f"Wrong zip: {property.address.zip}"
    
    owner = property.owner
    assert owner.name == 'Woodbridge Community Partners LLC', f"Wrong owner name: {owner.name}"
    assert owner.type == 'LLC', f"Wrong owner type: {owner.type}"
    assert owner.contactInfo.email == 'vadim.tantsyura@gmail.com', f"Wrong email: {owner.contactInfo.email}"
    assert owner.contactInfo.phone == '6282599139', f"Wrong phone: {owner.contactInfo.phone}"
    assert owner.contactInfo.address.street == '3 Willow Ct', f"Wrong owner street: {owner.contactInfo.address.street}"
    assert owner.contactInfo.address.city == 'Nyack', f"Wrong owner city: {owner.contactInfo.address.city}"
    assert owner.contactInfo.address.state == 'NY', f"Wrong owner state: {owner.contactInfo.address.state}"
    assert owner.contactInfo.address.zip == '10960', f"Wrong owner zip: {owner.contactInfo.address.zip}"
    
    # Verify units
    units = manager.get_units()
    assert len(units) == 2, f"Wrong number of units: {len(units)}"
    
    # Verify Unit A
    unit_a = manager.get_unit('Woodbridge Unit A')
    assert unit_a is not None, "Unit A not found"
    assert unit_a.currentTenant.name == 'Rebecca', f"Wrong tenant name: {unit_a.currentTenant.name}"
    assert unit_a.currentTenant.lease.rentAmount == 2475, f"Wrong rent: {unit_a.currentTenant.lease.rentAmount}"
    assert unit_a.currentTenant.lease.securityDeposit == 4850, f"Wrong deposit: {unit_a.currentTenant.lease.securityDeposit}"
    assert unit_a.currentTenant.lease.startDate == '2024-07-01', f"Wrong start date: {unit_a.currentTenant.lease.startDate}"
    assert unit_a.currentTenant.lease.endDate == '2025-06-30', f"Wrong end date: {unit_a.currentTenant.lease.endDate}"
    
    # Verify Unit B
    unit_b = manager.get_unit('Woodbridge Unit B')
    assert unit_b is not None, "Unit B not found"
    assert unit_b.currentTenant.name == 'Priscilla', f"Wrong tenant name: {unit_b.currentTenant.name}"
    assert unit_b.currentTenant.lease.rentAmount == 2650, f"Wrong rent: {unit_b.currentTenant.lease.rentAmount}"
    assert unit_b.currentTenant.lease.securityDeposit == 5032, f"Wrong deposit: {unit_b.currentTenant.lease.securityDeposit}"
    assert unit_b.currentTenant.lease.startDate == '2024-05-07', f"Wrong start date: {unit_b.currentTenant.lease.startDate}"
    assert unit_b.currentTenant.lease.endDate == '2025-04-30', f"Wrong end date: {unit_b.currentTenant.lease.endDate}"
    
    print("All verifications passed successfully!")
    return True

def main():
    """Run the test setup and verification."""
    try:
        if setup_property():
            print("\nProperty setup completed successfully!")
            print("Test schema saved to: testFiles/test_schema.json")
        else:
            print("\nProperty setup failed!")
    except AssertionError as e:
        print(f"\nVerification failed: {str(e)}")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")

if __name__ == "__main__":
    main() 