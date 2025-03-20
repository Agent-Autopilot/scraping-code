"""JSON Updater Script

This script provides a simplified way to update JSON data based on natural language instructions.
It uses OpenAI's structured output feature to ensure the returned JSON follows a specific schema.

Key benefits:
1. Directly returns the complete updated JSON from natural language instructions
2. Uses schema validation to ensure proper data structure
3. Eliminates need for complex action-based logic
"""

import os
import sys
import json
import logging
import traceback
from typing import Dict, Any, List, Optional, Tuple, Union

# Add parent directory to Python path if needed
parent_dir = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import utils for GPT client
from .utils import GPTClient, get_data_models_description, generate_json_schema_from_dataclasses

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JSONUpdater:
    """Class for updating JSON data based on natural language instructions."""
    
    def __init__(self):
        """Initialize the JSONUpdater."""
        self.gpt_client = GPTClient()
    
    def update_json(self, data: Dict[str, Any], instruction: str) -> Tuple[Dict[str, Any], bool, str]:
        """Update JSON data based on a natural language instruction.
        
        Args:
            data: The current JSON data
            instruction: A natural language instruction for updating the data
            
        Returns:
            Tuple of (updated_data, success, message)
        """
        try:
            # Log the instruction
            logger.info(f"Processing instruction: {instruction}")
            
            # Get data models description for context
            data_models_description = get_data_models_description()
            
            # Get JSON schema from dataclasses
            schema = generate_json_schema_from_dataclasses()
            
            # If schema generation failed, fall back to generating from data
            if not schema:
                logger.warning("Schema generation from dataclasses failed, falling back to data-based schema")
                schema = self._build_basic_schema_from_data(data)
            
            # Create prompt for GPT
            prompt = f"""You are a property management system that processes natural language updates into structured JSON.

The property management system uses the following data models:
{data_models_description}

Current data:
```json
{json.dumps(data, indent=2)}
```

Your task is to update the above JSON data based on this instruction:
"{instruction}"

Please return the COMPLETE modified JSON data structure that incorporates the changes from the instruction. Do not return just the changes or explanations.

Guidelines:
1. Preserve all existing fields and values that aren't affected by the instruction
2. Convert dates to YYYY-MM-DD format
3. Phone numbers should be just digits without formatting
4. Currency values should be numbers without $ signs
5. If the instruction is unclear, make a reasonable assumption based on the context
6. Follow the exact schema of the original data"""

            # Get response from GPT using structured output and JSON schema
            system_message = "You are a property management system that updates JSON data based on natural language instructions."
            
            # Use OpenAI's function calling/structured output feature with schema
            response = self.gpt_client.client.chat.completions.create(
                model=self.gpt_client.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            # Extract the response content
            response_content = response.choices[0].message.content
            
            if not response_content:
                logger.error("Failed to get response from GPT")
                return data, False, "Failed to get response from OpenAI"
                
            # Parse the response as JSON
            try:
                updated_data = json.loads(response_content)
                logger.info("Successfully processed instruction and received updated JSON")
                return updated_data, True, f"Successfully updated JSON based on instruction: {instruction}"
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse GPT response as JSON: {str(e)}")
                return data, False, f"Failed to parse response as JSON: {str(e)}"
                
        except Exception as e:
            logger.error(f"Error processing instruction: {str(e)}")
            logger.error(traceback.format_exc())
            return data, False, f"Error: {str(e)}"
    
    def _build_basic_schema_from_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build a basic JSON schema based on the structure of the data.
        
        Args:
            data: The JSON data to build a schema from
            
        Returns:
            A JSON schema dict
        """
        try:
            # Import the necessary libraries for generating the schema
            try:
                from genson import SchemaBuilder
                
                # Create a schema builder
                builder = SchemaBuilder()
                builder.add_object(data)
                
                # Get the schema
                schema = builder.to_schema()
                logger.info("Generated JSON schema from data structure")
                return schema
            except ImportError:
                # If genson is not available, create a basic schema
                logger.warning("genson library not available, creating a basic schema")
                schema = {
                    "type": "object",
                    "properties": {}
                }
                
                # Add properties based on the top-level keys in the data
                for key, value in data.items():
                    if isinstance(value, dict):
                        schema["properties"][key] = {"type": "object"}
                    elif isinstance(value, list):
                        schema["properties"][key] = {"type": "array"}
                    elif isinstance(value, str):
                        schema["properties"][key] = {"type": "string"}
                    elif isinstance(value, int) or isinstance(value, float):
                        schema["properties"][key] = {"type": "number"}
                    elif isinstance(value, bool):
                        schema["properties"][key] = {"type": "boolean"}
                    else:
                        schema["properties"][key] = {}
                
                return schema
                
        except Exception as e:
            logger.error(f"Error building JSON schema: {str(e)}")
            logger.error(traceback.format_exc())
            return {"type": "object"}
    
    def update_json_batch(self, data: Dict[str, Any], instructions: List[str], batch_size: int = 10) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[str]]:
        """Process a batch of instructions together to update JSON data.
        
        Args:
            data: The current JSON data
            instructions: List of natural language instructions
            batch_size: Maximum number of instructions to process in a single batch
            
        Returns:
            Tuple of (updated_data, failed_instructions, messages)
        """
        # Initialize lists for results
        failed_instructions = []
        messages = []
        
        # Process instructions in batches
        for i in range(0, len(instructions), batch_size):
            batch = instructions[i:i+batch_size]
            
            if not batch:
                continue
            
            # Log the batch
            logger.info(f"Processing batch of {len(batch)} instructions (#{i+1} to #{i+len(batch)})")
            
            # Get data models description for context
            data_models_description = get_data_models_description()
            
            # Create a prompt for batch processing
            instructions_list = "\n".join([f"{j+1}. {instr}" for j, instr in enumerate(batch)])
            
            prompt = f"""You are a property management system that processes natural language updates into structured JSON.

The property management system uses the following data models:
{data_models_description}

Current data:
```json
{json.dumps(data, indent=2)}
```

Your task is to update the above JSON data based on the following batch of instructions:

{instructions_list}

Apply these instructions IN ORDER, one after another, with each instruction building on the results of the previous one.
Please return the COMPLETE modified JSON data structure after applying ALL instructions. 
Do not return intermediate steps, explanations, or just the changes.

Guidelines:
1. Preserve all existing fields and values that aren't affected by the instructions
2. Convert dates to YYYY-MM-DD format
3. Phone numbers should be just digits without formatting
4. Currency values should be numbers without $ signs
5. If an instruction is unclear, make a reasonable assumption based on the context
6. Follow the exact schema of the original data
7. DO NOT CREATE DUPLICATE FIELDS OR OBJECTS - update the existing ones instead
8. When adding new items to arrays, don't duplicate existing entries
9. Ensure the final JSON is well-formed and maintains the original structure"""

            try:
                # Get response from GPT
                system_message = "You are a property management system that updates JSON data based on batches of natural language instructions."
                
                response = self.gpt_client.client.chat.completions.create(
                    model=self.gpt_client.model,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                
                # Extract the response content
                response_content = response.choices[0].message.content
                
                if not response_content:
                    error_msg = "Failed to get response from GPT for batch"
                    logger.error(error_msg)
                    messages.append(error_msg)
                    failed_instructions.extend(batch)
                    continue
                    
                # Parse the response as JSON
                try:
                    updated_data = json.loads(response_content)
                    logger.info(f"Successfully processed batch of {len(batch)} instructions")
                    messages.append(f"Successfully processed batch of {len(batch)} instructions")
                    data = updated_data  # Update data for next batch
                except json.JSONDecodeError as e:
                    error_msg = f"Failed to parse batch response as JSON: {str(e)}"
                    logger.error(error_msg)
                    messages.append(error_msg)
                    failed_instructions.extend(batch)
                    
            except Exception as e:
                error_msg = f"Error processing batch: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                messages.append(error_msg)
                failed_instructions.extend(batch)
        
        return data, failed_instructions, messages
    
    def process_instructions(self, json_file_path: str, instructions: List[str], batch_size: int = 10) -> Dict[str, Any]:
        """Process a list of instructions and apply them to a JSON file.
        
        Args:
            json_file_path: Path to the JSON file to modify
            instructions: List of natural language instructions
            batch_size: Number of instructions to process in a single batch
            
        Returns:
            Dictionary with results including success, failed instructions, and messages
        """
        # Load the JSON data
        data = self.load_json(json_file_path)
        
        # Initialize results
        results = {
            "success": True,
            "failed_instructions": [],
            "messages": []
        }
        
        if not instructions:
            logger.warning("No instructions provided")
            return results
            
        # Process instructions in batches
        if batch_size > 1:
            logger.info(f"Processing {len(instructions)} instructions in batches of up to {batch_size}")
            updated_data, failed_batch_instructions, batch_messages = self.update_json_batch(data, instructions, batch_size)
            
            # Update results
            results["messages"].extend(batch_messages)
            
            # Record failed instructions
            if failed_batch_instructions:
                results["success"] = False
                for i, instruction in enumerate(failed_batch_instructions):
                    results["failed_instructions"].append({
                        "index": i,
                        "instruction": instruction,
                        "error": "Failed in batch processing"
                    })
            
            # Update data with batch results
            data = updated_data
        else:
            # Traditional one-by-one processing
            logger.info(f"Processing {len(instructions)} instructions one by one")
            
            # Apply each instruction
            for i, instruction in enumerate(instructions):
                try:
                    # Update the JSON with the instruction
                    updated_data, success, message = self.update_json(data, instruction)
                    
                    # Record the result
                    results["messages"].append(message)
                    
                    if success:
                        # Update the data for the next instruction
                        data = updated_data
                    else:
                        results["success"] = False
                        results["failed_instructions"].append({
                            "index": i,
                            "instruction": instruction,
                            "error": message
                        })
                        
                except Exception as e:
                    error_message = f"Error processing instruction {i}: {str(e)}"
                    logger.error(error_message)
                    logger.error(traceback.format_exc())
                    
                    results["success"] = False
                    results["messages"].append(error_message)
                    results["failed_instructions"].append({
                        "index": i,
                        "instruction": instruction,
                        "error": str(e)
                    })
        
        # Save the updated data
        if results["success"] or (results["failed_instructions"] and len(results["failed_instructions"]) < len(instructions)):
            # Only save if at least one instruction succeeded
            if not self.save_json(json_file_path, data):
                results["success"] = False
                results["messages"].append(f"Failed to save updated data to {json_file_path}")
        
        return results
    
    def load_json(self, file_path: str) -> Dict[str, Any]:
        """Load JSON data from a file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Dictionary containing the JSON data, or empty dict if loading fails
        """
        try:
            if not os.path.exists(file_path):
                logger.warning(f"File not found: {file_path}")
                return {}
                
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading JSON from {file_path}: {str(e)}")
            logger.error(traceback.format_exc())
            return {}
    
    def save_json(self, file_path: str, data: Dict[str, Any]) -> bool:
        """Save JSON data to a file.
        
        Args:
            file_path: Path to save the JSON file
            data: Dictionary containing the data to save
            
        Returns:
            bool: True if save was successful
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving JSON to {file_path}: {str(e)}")
            logger.error(traceback.format_exc())
            return False

# Simple helper function for direct use
def update_json_with_instruction(data: Dict[str, Any], instruction: str) -> Tuple[Dict[str, Any], bool, str]:
    """Update JSON data with a natural language instruction using OpenAI.
    
    Args:
        data: Current JSON data
        instruction: Natural language instruction
        
    Returns:
        Tuple of (updated_data, success, message)
    """
    updater = JSONUpdater()
    return updater.update_json(data, instruction)

# Backwards compatibility function
def apply_instructions(json_file_path: str, instructions: List[Union[Dict[str, Any], str]]) -> Dict[str, Any]:
    """Apply a list of instructions to a JSON file.
    
    This function is maintained for backwards compatibility with the old interface.
    
    Args:
        json_file_path: Path to the JSON file to modify
        instructions: List of instruction dictionaries or strings
        
    Returns:
        Dictionary with results
    """
    updater = JSONUpdater()
    
    # Convert any dictionary instructions to strings
    string_instructions = []
    for instruction in instructions:
        if isinstance(instruction, dict):
            # Convert old instruction format to a natural language instruction
            if 'action' in instruction and 'entity_type' in instruction and 'identifier' in instruction:
                action = instruction['action']
                entity_type = instruction['entity_type']
                identifier = instruction['identifier']
                fields = instruction.get('fields', {})
                
                # Build a natural language instruction
                nl_instruction = f"{action.capitalize()} {entity_type} with {identifier['field']}={identifier['value']}"
                if fields and action != 'delete':
                    field_strs = [f"{k}={v}" for k, v in fields.items()]
                    nl_instruction += f" and set {', '.join(field_strs)}"
                
                string_instructions.append(nl_instruction)
            else:
                logger.warning(f"Skipping invalid instruction: {instruction}")
        else:
            string_instructions.append(instruction)
    
    return updater.process_instructions(json_file_path, string_instructions) 