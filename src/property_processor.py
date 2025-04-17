"""Property Processor Interface

This module provides a unified interface for processing property documents,
creating structured JSON data, and enriching it with missing information.
"""

import os
import json
import logging
import uuid
from typing import Dict, Any, Optional, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import from scripts
from src.scripts.document_converter import extract_relevant_text
from src.scripts.text_to_instructions import UpdateProcessor
from src.scripts.apply_instructions import JSONUpdater
from src.scripts.data_enricher import DataEnricher
from src.scripts.json_restructurer import JSONRestructurer
from src.scripts.utils import FileManager

class PropertyProcessor:
    """Unified interface for processing property documents and data.
    
    This class combines the functionality of document conversion, NLP processing,
    data management, and data enrichment into a single interface.
    """
    
    def __init__(self, template_path: Optional[str] = None):
        """Initialize the PropertyProcessor.
        
        Args:
            template_path: Optional path to a JSON template file. If None, an empty template will be used.
        """
        self.update_processor = UpdateProcessor()
        self.data_manager = JSONUpdater()
        self.data_enricher = DataEnricher()
        self.json_restructurer = JSONRestructurer()
        self.template_path = template_path
        
        # Load or create template
        self.template = self._load_template()
        
    def _load_template(self) -> Dict[str, Any]:
        """Load the template JSON or create an empty one if not provided."""
        if self.template_path and os.path.exists(self.template_path):
            template = FileManager.load_json(self.template_path)
            if template:
                logger.info(f"Loaded template from {self.template_path}")
                return template
                
        # Create empty template with proper structure
        logger.info("Creating empty template")
        return {
            "property": {
                "name": "Default Property",
                "address": "",
                "city": "",
                "state": "",
                "zipCode": "",
                "owner": "",
                "propertyType": "",
                "yearBuilt": "",
                "totalUnits": "",
                "contactInfo": {}
            },
            "units": [],
            "tenants": [],
            "leases": []
        }
    
    def extract_text_from_document(self, document_path: str, save_path: Optional[str] = None) -> str:
        """Extract relevant text from a document.
        
        Args:
            document_path: Path to the document file (PDF, DOCX, TXT, etc.)
            save_path: Optional path to save the extracted text
            
        Returns:
            Extracted relevant text as a string
        """
        logger.info(f"Extracting text from {document_path}")
        text = extract_relevant_text(document_path)
        
        # Save extracted text if requested
        if save_path:
            FileManager.save_text(save_path, text)
            logger.info(f"Saved extracted text to {save_path}")
            
        return text
    
    def generate_instructions_from_text(self, text: str, save_path: Optional[str] = None) -> Dict[str, Any]:
        """Generate structured instructions from text.
        
        Args:
            text: Text to process
            save_path: Optional path to save the generated instructions
            
        Returns:
            Dictionary containing the structured instructions
        """
        logger.info("Generating structured instructions from text")
        instructions = self.update_processor.process_update(text)
        
        # Save instructions if requested
        if save_path and instructions:
            FileManager.save_json(save_path, instructions)
            logger.info(f"Saved structured instructions to {save_path}")
            
        return instructions
    
    def restructure_json(self, 
                       json_data: Dict[str, Any], 
                       save_path: Optional[str] = None) -> Dict[str, Any]:
        """Restructure JSON data to maximize parent-child relationships.
        
        This method uses OpenAI to analyze ID references in the data and
        create a more hierarchical structure where entities are nested
        within their logical parent entities.
        
        Args:
            json_data: The JSON data to restructure
            save_path: Optional path to save the restructured JSON
            
        Returns:
            The restructured JSON data
        """
        logger.info("Restructuring JSON to optimize parent-child relationships...")
        
        # Use the JSONRestructurer to restructure the data
        restructured_data = self.json_restructurer.restructure_json(json_data)
        
        # Save the restructured data if requested
        if save_path and restructured_data:
            FileManager.save_json(save_path, restructured_data)
            logger.info(f"Saved restructured JSON to {save_path}")
        
        return restructured_data
    
    def ensure_model_ids(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure all models have unique IDs and properly reference each other.
        
        This method recursively traverses the JSON structure and:
        1. Adds missing IDs to objects
        2. Updates reference fields to point to the correct IDs
        
        Args:
            data: The JSON data to process
            
        Returns:
            The updated JSON data with proper IDs and references
        """
        def generate_id() -> str:
            """Generate a unique ID string."""
            return str(uuid.uuid4())
        
        def process_object(obj: Dict[str, Any], parent_key: str = "") -> Dict[str, Any]:
            """Process an object to ensure it has an ID and proper references."""
            if not isinstance(obj, dict):
                return obj
                
            # Add ID if missing
            if "id" in obj and not obj["id"]:
                obj["id"] = generate_id()
                
            # Get a list of keys to safely iterate over
            keys = list(obj.keys())
            
            # Process nested objects and maintain ID references
            for key in keys:
                value = obj[key]
                # Skip null values
                if value is None:
                    continue
                    
                # Process nested objects
                if isinstance(value, dict):
                    # Add ID reference if the field ends with 'Id' and the corresponding object exists
                    ref_field = f"{key}Id"
                    if ref_field not in obj and "id" in value:
                        obj[ref_field] = value["id"] if value["id"] else generate_id()
                        if not value["id"]:
                            value["id"] = obj[ref_field]
                            
                    # Recursively process the nested object
                    obj[key] = process_object(value, key)
                    
                # Process lists
                elif isinstance(value, list):
                    # Handle list of objects
                    new_list = []
                    ids_list = []
                    
                    for item in value:
                        if isinstance(item, dict):
                            processed_item = process_object(item, key)
                            if "id" in processed_item and processed_item["id"]:
                                ids_list.append(processed_item["id"])
                            new_list.append(processed_item)
                        else:
                            new_list.append(item)
                            
                    obj[key] = new_list
                    
                    # Add reference list if missing
                    list_ref_field = f"{key}Ids"
                    if ids_list and list_ref_field not in obj:
                        obj[list_ref_field] = ids_list
                        
            return obj
            
        # Make a deep copy of the data to avoid modifying the original
        data_copy = json.loads(json.dumps(data))
        
        # Start processing from the root
        return process_object(data_copy)
        
    def apply_instructions_to_json(self, 
                                  json_data: Dict[str, Any], 
                                  instructions: Dict[str, Any],
                                  save_path: Optional[str] = None,
                                  save_failed_path: Optional[str] = None,
                                  batch_size: int = 10) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Apply structured instructions to JSON data.
        
        Args:
            json_data: The JSON data to modify
            instructions: Dictionary containing the structured instructions
            save_path: Optional path to save the updated JSON
            save_failed_path: Optional path to save failed instructions
            batch_size: Number of instructions to process in a single batch
            
        Returns:
            Tuple of (updated_json_data, results)
        """
        logger.info("Applying instructions to JSON data")
        
        # Create a JSONUpdater instance
        data_manager = JSONUpdater()
        
        # Extract instructions list
        instruction_list = instructions.get("instructions", []) if instructions else []
        
        if not instruction_list:
            logger.warning("No instructions to apply")
            return json_data, {"success": True, "failed_instructions": [], "messages": ["No instructions to apply"]}
        
        logger.info(f"Processing {len(instruction_list)} instructions with batch_size={batch_size}")
        
        # Process instructions in batches
        updated_data, failed_instructions, messages = data_manager.update_json_batch(
            json_data.copy(), instruction_list, batch_size
        )
        
        # Ensure all models have proper IDs and references
        updated_data = self.ensure_model_ids(updated_data)
        
        # Format results
        results = {
            "success": len(failed_instructions) == 0,
            "failed_instructions": [
                {"index": i, "instruction": instr, "error": "Failed in batch processing"}
                for i, instr in enumerate(failed_instructions)
            ],
            "messages": messages
        }
        
        # Save updated JSON if requested
        if save_path:
            FileManager.save_json(save_path, updated_data)
            logger.info(f"Saved updated JSON to {save_path}")
        
        # Save failed instructions if requested
        if save_failed_path and results.get("failed_instructions"):
            FileManager.save_json(save_failed_path, {
                "failed_instructions": results.get("failed_instructions", []),
                "messages": results.get("messages", [])
            })
            logger.info(f"Saved failed instructions to {save_failed_path}")
        
        return updated_data, results
    
    def enrich_json_with_text(self, 
                             json_data: Dict[str, Any], 
                             text: str,
                             save_enrichment_path: Optional[str] = None) -> List[str]:
        """Enrich JSON data with information from text.
        
        Args:
            json_data: The JSON data to enrich
            text: Text containing additional information
            save_enrichment_path: Optional path to save enrichment instructions
            
        Returns:
            List of enrichment instructions
        """
        logger.info("Enriching JSON data with text information")
        
        # Generate enrichment instructions
        enrichment_instructions = self.data_enricher.generate_enrichment_instructions_from_data(json_data, text)
        
        # Save enrichment instructions if requested
        if save_enrichment_path and enrichment_instructions:
            enrichment_content = "\n".join([f"{i+1}. {instruction}" for i, instruction in enumerate(enrichment_instructions)])
            FileManager.save_text(save_enrichment_path, enrichment_content)
            logger.info(f"Saved enrichment instructions to {save_enrichment_path}")
        
        return enrichment_instructions
    
    def process_document(self, 
                        document_path: str, 
                        output_dir: Optional[str] = None,
                        save_intermediates: bool = True,
                        restructure_output: bool = False) -> Dict[str, Any]:
        """Process a document to create and enrich a JSON representation.
        
        This is the main function that combines all steps:
        1. Extract text from document
        2. Generate structured instructions from text
        3. Apply instructions to create/update JSON
        4. Enrich JSON with any missing information
        5. Optionally restructure the JSON to optimize parent-child relationships
        
        Args:
            document_path: Path to the document file
            output_dir: Directory to save output files (if None, uses document directory)
            save_intermediates: Whether to save intermediate results
            restructure_output: Whether to restructure the final JSON
            
        Returns:
            The final enriched JSON data
        """
        # Determine output directory
        if not output_dir:
            output_dir = os.path.dirname(document_path)
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Get base filename without extension
        base_name = os.path.splitext(os.path.basename(document_path))[0]
        
        # Step 1: Extract text from document
        extracted_text_path = os.path.join(output_dir, f"{base_name}_extracted_text.txt") if save_intermediates else None
        text = self.extract_text_from_document(document_path, extracted_text_path)
        
        if not text or text.startswith("Error"):
            logger.error(f"Failed to extract text from document: {text}")
            return {}
        
        # Step 2: Generate structured instructions from text
        instructions_path = os.path.join(output_dir, f"{base_name}_instructions.json") if save_intermediates else None
        instructions = self.generate_instructions_from_text(text, instructions_path)
        
        if not instructions or "error" in instructions:
            logger.error(f"Failed to generate instructions: {instructions.get('error', 'Unknown error')}")
            return {}
        
        # Step 3: Apply instructions to create/update JSON
        json_path = os.path.join(output_dir, f"{base_name}.json")
        failed_path = os.path.join(output_dir, f"{base_name}_failed_instructions.json") if save_intermediates else None
        json_data, results = self.apply_instructions_to_json(
            self.template.copy(), instructions, json_path, failed_path
        )
        
        if not json_data or not results["success"]:
            logger.warning(f"Some instructions failed: {len(results.get('failed_instructions', []))} failures")
        
        # Step 4: Enrich JSON with any missing information using the original text
        enrichment_path = os.path.join(output_dir, f"{base_name}_enrichment_instructions.txt") if save_intermediates else None
        enrichment_instructions = self.enrich_json_with_text(json_data, text, enrichment_path)
        
        # Apply enrichment instructions if any
        if enrichment_instructions:
            logger.info(f"Found {len(enrichment_instructions)} enrichment instructions")
            enriched_path = os.path.join(output_dir, f"{base_name}_enriched.json")
            
            # Process enrichment instructions in a batch to prevent duplication
            batch_size = min(10, len(enrichment_instructions))
            enriched_data, enrichment_results = self.apply_instructions_to_json(
                json_data, 
                {"instructions": enrichment_instructions}, 
                enriched_path,
                batch_size=batch_size
            )
            
            # Final step: Ensure all models have proper IDs and references
            enriched_data = self.ensure_model_ids(enriched_data)
            
            # Save the final enriched data with proper IDs
            if save_intermediates:
                FileManager.save_json(enriched_path, enriched_data)
            
            # Step 5: Restructure the JSON if requested
            if restructure_output:
                restructured_path = os.path.join(output_dir, f"{base_name}_restructured.json")
                restructured_data = self.restructure_json(enriched_data, restructured_path)
                return restructured_data
            else:
                return enriched_data
        else:
            # Ensure all models have proper IDs and references as a final step
            json_data = self.ensure_model_ids(json_data)
            
            # Re-save the JSON with proper IDs
            FileManager.save_json(json_path, json_data)
            
            # Step 5: Restructure the JSON if requested
            if restructure_output:
                restructured_path = os.path.join(output_dir, f"{base_name}_restructured.json")
                restructured_data = self.restructure_json(json_data, restructured_path)
                return restructured_data
            else:
                return json_data

# Convenience function for direct use
def process_property_document(document_path: str, 
                             template_path: Optional[str] = None,
                             output_dir: Optional[str] = None,
                             save_intermediates: bool = True,
                             restructure_output: bool = False) -> Dict[str, Any]:
    """Process a property document to create and enrich a JSON representation.
    
    Args:
        document_path: Path to the document file
        template_path: Optional path to a JSON template file
        output_dir: Directory to save output files (if None, uses document directory)
        save_intermediates: Whether to save intermediate results
        restructure_output: Whether to restructure the final JSON
        
    Returns:
        The final enriched JSON data
    """
    processor = PropertyProcessor(template_path)
    return processor.process_document(document_path, output_dir, save_intermediates, restructure_output) 