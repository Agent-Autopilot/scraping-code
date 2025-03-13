"""Process text updates for property management system."""

import os
from typing import List, Dict, Any
from nlp_processor import UpdateProcessor
from data_manager import DataManager

def process_text_updates(text: str) -> List[Dict[str, Any]]:
    """Process text updates and return list of processed instructions.
    
    Args:
        text: Input text containing update instructions
        
    Returns:
        List of dictionaries containing processed update instructions
    """
    processor = UpdateProcessor()
    updates = []
    
    # Split text into individual updates using empty lines as separators
    instructions = [instr.strip() for instr in text.split('\n\n') if instr.strip()]
    
    for instruction in instructions:
        try:
            update = processor.process_update(instruction)
            if update:
                updates.append(update)
        except Exception as e:
            print(f"Error processing instruction: {str(e)}")
            continue
            
    return updates

def apply_updates(updates: List[Dict[str, Any]], data_manager: DataManager) -> bool:
    """Apply processed updates to the database.
    
    Args:
        updates: List of update instructions to apply
        data_manager: DataManager instance to apply updates
        
    Returns:
        bool: True if all updates were successful, False otherwise
    """
    success = True
    update_handlers = {
        'property': lambda data: data_manager.update_property(data),
        'owner': lambda data: data_manager.update_owner(data),
        'tenant': lambda data: _handle_tenant_update(data_manager, data),
        'lease': lambda data: _handle_lease_update(data_manager, data),
        'document': lambda data: _handle_document_update(data_manager, data),
        'unit': lambda data: _handle_unit_update(data_manager, data)
    }
    
    for update in updates:
        try:
            update_type = update.get('type')
            update_data = update.get('data', {})
            
            if not update_type or not update_data:
                print("Invalid update format: missing type or data")
                success = False
                continue
                
            handler = update_handlers.get(update_type)
            if handler:
                if not handler(update_data):
                    success = False
            else:
                print(f"Unsupported update type: {update_type}")
                success = False
                
        except Exception as e:
            print(f"Error applying update: {str(e)}")
            success = False
            
    return success

def _handle_tenant_update(data_manager: DataManager, data: Dict[str, Any]) -> bool:
    """Handle tenant update with unit number validation."""
    unit_number = data.pop('unitNumber', None)
    if not unit_number:
        print("Missing unit number for tenant update")
        return False
    return data_manager.update_tenant(unit_number, data)

def _handle_lease_update(data_manager: DataManager, data: Dict[str, Any]) -> bool:
    """Handle lease update with unit number validation."""
    unit_number = data.pop('unitNumber', None)
    if not unit_number:
        print("Missing unit number for lease update")
        return False
    return data_manager.update_lease(unit_number, data)

def _handle_document_update(data_manager: DataManager, data: Dict[str, Any]) -> bool:
    """Handle document update with entity validation."""
    entity_type = data.pop('entityType', None)
    entity_id = data.pop('entityId', None)
    if not entity_type or not entity_id:
        print("Missing entity type or ID for document update")
        return False
    return data_manager.add_document(entity_type, entity_id, data)

def _handle_unit_update(data_manager: DataManager, data: Dict[str, Any]) -> bool:
    """Handle unit update with unit number validation."""
    unit_number = data.pop('unitNumber', None)
    if not unit_number:
        print("Missing unit number for unit update")
        return False
    return data_manager.update_unit(unit_number, data)

def main() -> bool:
    """Main entry point for processing updates.
    
    Returns:
        bool: True if all updates were successful, False otherwise
    """
    try:
        input_file = 'temp_input.txt'
        if not os.path.exists(input_file):
            print(f"Input file {input_file} not found")
            return False
            
        with open(input_file, 'r') as f:
            text = f.read().strip()
            
        if not text:
            print("No updates provided")
            return False
            
        updates = process_text_updates(text)
        if not updates:
            print("No valid updates found")
            return False
            
        data_manager = DataManager()
        success = apply_updates(updates, data_manager)
        print("All updates applied successfully" if success else "Some updates failed")
        return success
            
    except Exception as e:
        print(f"Error in main: {str(e)}")
        return False

if __name__ == '__main__':
    main() 