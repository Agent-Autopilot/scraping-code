"""Process text updates for property management system.

This module provides functions for processing multiple text updates at once
and applying them to the property management system.
"""

import os
from typing import List, Dict, Any, Tuple
from src.text_to_instructions import TextToInstructions
from src.data_manager import DataManager
from src.utils import FileManager

def process_text_updates(instructions: List[str], data_manager: DataManager) -> Dict[str, List[str]]:
    """Process a list of text instructions and apply them to the data manager.
    
    Args:
        instructions: List of natural language instructions to process
        data_manager: DataManager instance to apply updates to
        
    Returns:
        Dictionary with 'successful' and 'failed' lists of instructions
    """
    results = {
        'successful': [],
        'failed': []
    }
    
    for instruction in instructions:
        try:
            # Try to apply the instruction directly
            success = apply_instruction(instruction, data_manager)
            
            if success:
                results['successful'].append(instruction)
            else:
                results['failed'].append(instruction)
                
        except Exception as e:
            print(f"Error processing instruction '{instruction}': {str(e)}")
            results['failed'].append(instruction)
            
    return results

def apply_instruction(instruction: str, data_manager: DataManager) -> bool:
    """Apply a single natural language instruction to the data manager.
    
    Args:
        instruction: Natural language instruction to apply
        data_manager: DataManager instance to apply the instruction to
        
    Returns:
        bool: True if the instruction was applied successfully
    """
    # This is a simplified implementation that tries to identify the type of update
    # from the instruction text and apply it accordingly
    
    instruction_lower = instruction.lower()
    
    try:
        # Property updates
        if "create a new property" in instruction_lower or "update property" in instruction_lower:
            # Extract property details from the instruction
            property_data = {}
            
            # Look for property name
            if "called" in instruction_lower:
                name_start = instruction.find("called") + 7
                name_end = instruction.find("at", name_start)
                if name_end == -1:
                    name_end = len(instruction)
                property_data["name"] = instruction[name_start:name_end].strip()
            
            # Look for address
            if "at" in instruction_lower:
                address_start = instruction.find("at") + 3
                address = instruction[address_start:].strip()
                
                # Try to parse the address components
                address_parts = address.split(",")
                if len(address_parts) >= 2:
                    property_data["address"] = {
                        "street": address_parts[0].strip()
                    }
                    
                    # Try to parse city, state, zip
                    location_parts = address_parts[1].strip().split()
                    if len(location_parts) >= 2:
                        property_data["address"]["city"] = " ".join(location_parts[:-2])
                        property_data["address"]["state"] = location_parts[-2]
                        property_data["address"]["zip"] = location_parts[-1]
            
            return data_manager.update_property(property_data)
            
        # Owner updates
        elif "owner" in instruction_lower:
            owner_data = {}
            
            # Look for owner name
            if "to" in instruction_lower:
                name_start = instruction.find("to") + 3
                name_end = instruction.find(",", name_start)
                if name_end == -1:
                    name_end = len(instruction)
                owner_data["name"] = instruction[name_start:name_end].strip()
            
            # Look for contact info
            if "email" in instruction_lower:
                email_start = instruction.find("email") + 6
                email_end = instruction.find(" ", email_start)
                if email_end == -1:
                    email_end = len(instruction)
                
                if "contactInfo" not in owner_data:
                    owner_data["contactInfo"] = {}
                owner_data["contactInfo"]["email"] = instruction[email_start:email_end].strip()
            
            if "phone" in instruction_lower:
                phone_start = instruction.find("phone") + 6
                phone_end = instruction.find(" ", phone_start)
                if phone_end == -1:
                    phone_end = len(instruction)
                
                if "contactInfo" not in owner_data:
                    owner_data["contactInfo"] = {}
                owner_data["contactInfo"]["phone"] = instruction[phone_start:phone_end].strip()
            
            return data_manager.update_owner(owner_data)
            
        # Unit updates
        elif "unit" in instruction_lower and not ("tenant" in instruction_lower or "lease" in instruction_lower):
            # Extract unit number
            unit_start = instruction.find("unit") + 5
            unit_end = instruction.find(" ", unit_start)
            if unit_end == -1:
                unit_end = len(instruction)
            unit_number = instruction[unit_start:unit_end].strip()
            
            unit_data = {}
            
            return data_manager.update_unit(unit_number, unit_data)
            
        # Tenant updates
        elif "tenant" in instruction_lower:
            # Extract unit number
            unit_number = None
            if "unit" in instruction_lower:
                unit_start = instruction.find("unit") + 5
                unit_end = instruction.find(" ", unit_start)
                if unit_end == -1:
                    unit_end = len(instruction)
                unit_number = instruction[unit_start:unit_end].strip()
            
            # Extract tenant name
            tenant_data = {}
            if "named" in instruction_lower:
                name_start = instruction.find("named") + 6
                name_end = instruction.find(" to ", name_start)
                if name_end == -1:
                    name_end = len(instruction)
                tenant_data["name"] = instruction[name_start:name_end].strip()
            
            if not unit_number:
                return False
                
            return data_manager.update_tenant(unit_number, tenant_data)
            
        # Lease updates
        elif "lease" in instruction_lower:
            # Extract unit number
            unit_number = None
            if "unit" in instruction_lower:
                unit_start = instruction.find("unit") + 5
                unit_end = instruction.find(" ", unit_start)
                if unit_end == -1:
                    unit_end = len(instruction)
                unit_number = instruction[unit_start:unit_end].strip()
            
            lease_data = {}
            
            # Look for rent amount
            if "rent" in instruction_lower:
                rent_start = instruction.find("rent") + 5
                rent_end = instruction.find(" ", rent_start)
                if rent_end == -1:
                    rent_end = len(instruction)
                
                rent_str = instruction[rent_start:rent_end].strip()
                if rent_str.startswith("$"):
                    rent_str = rent_str[1:]
                
                try:
                    lease_data["rentAmount"] = float(rent_str)
                except ValueError:
                    pass
            
            # Look for due date
            if "due" in instruction_lower:
                due_start = instruction.find("due") + 4
                due_end = instruction.find(" ", due_start)
                if due_end == -1:
                    due_end = len(instruction)
                
                lease_data["dueDate"] = instruction[due_start:due_end].strip()
            
            if not unit_number:
                return False
                
            return data_manager.update_lease(unit_number, lease_data)
            
        # If we can't determine the type, return False
        return False
        
    except Exception as e:
        print(f"Error applying instruction: {str(e)}")
        return False

def process_text_file(file_path: str, data_manager: DataManager) -> Tuple[List[str], List[str]]:
    """Process a text file containing natural language instructions.
    
    Args:
        file_path: Path to the text file
        data_manager: DataManager instance to apply updates to
        
    Returns:
        Tuple of (successful_instructions, failed_instructions)
    """
    # Load the text file
    text = FileManager.load_text(file_path)
    if not text:
        print(f"Error: Could not load text from {file_path}")
        return ([], [])
    
    # Convert text to instructions
    converter = TextToInstructions()
    instructions = converter.convert_text(text)
    
    # Process the instructions
    results = process_text_updates(instructions, data_manager)
    
    return (results['successful'], results['failed'])

def main():
    """Example usage of the bulk processor."""
    # Initialize data manager
    data_manager = DataManager()
    
    # Example text file path
    file_path = "input.txt"
    
    # Process the text file
    successful, failed = process_text_file(file_path, data_manager)
    
    # Print results
    print(f"Successfully processed {len(successful)} instructions")
    print(f"Failed to process {len(failed)} instructions")
    
    if failed:
        print("\nFailed instructions:")
        for i, instruction in enumerate(failed, 1):
            print(f"{i}. {instruction}")

if __name__ == "__main__":
    main() 