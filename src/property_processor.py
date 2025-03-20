"""Property Processor Interface

This module provides a unified interface for processing property documents,
creating structured JSON data, and enriching it with missing information.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import from scripts
from .scripts.document_converter import extract_relevant_text
from .scripts.text_to_instructions import UpdateProcessor
from .scripts.apply_instructions import JSONUpdater
from .scripts.data_enricher import DataEnricher
from .scripts.utils import FileManager

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
                        save_intermediates: bool = True) -> Dict[str, Any]:
        """Process a document to create and enrich a JSON representation.
        
        This is the main function that combines all steps:
        1. Extract text from document
        2. Generate structured instructions from text
        3. Apply instructions to create/update JSON
        4. Enrich JSON with any missing information
        
        Args:
            document_path: Path to the document file
            output_dir: Directory to save output files (if None, uses document directory)
            save_intermediates: Whether to save intermediate results
            
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
            self.template.copy(), 
            instructions, 
            json_path, 
            failed_path
        )
        
        # Step 4: Enrich JSON with any missing information
        enrichment_path = os.path.join(output_dir, f"{base_name}_enrichment_instructions.txt") if save_intermediates else None
        enrichment_instructions = self.enrich_json_with_text(json_data, text, enrichment_path)
        
        # Apply enrichment instructions if any
        if enrichment_instructions:
            logger.info(f"Found {len(enrichment_instructions)} enrichment instructions")
            
            # Convert natural language instructions to structured format
            structured_enrichments = []
            for instruction in enrichment_instructions:
                enrichment_result = self.update_processor.process_update(instruction)
                if enrichment_result and "instructions" in enrichment_result:
                    structured_enrichments.extend(enrichment_result["instructions"])
            
            if structured_enrichments:
                # Apply enrichment instructions
                enriched_json_path = os.path.join(output_dir, f"{base_name}_enriched.json")
                enriched_failed_path = os.path.join(output_dir, f"{base_name}_enrichment_failed.json") if save_intermediates else None
                json_data, _ = self.apply_instructions_to_json(
                    json_data, 
                    {"instructions": structured_enrichments}, 
                    enriched_json_path, 
                    enriched_failed_path
                )
        
        return json_data

# Convenience function for direct use
def process_property_document(document_path: str, 
                             template_path: Optional[str] = None,
                             output_dir: Optional[str] = None,
                             save_intermediates: bool = True) -> Dict[str, Any]:
    """Process a property document to create and enrich a JSON representation.
    
    Args:
        document_path: Path to the document file
        template_path: Optional path to a JSON template file
        output_dir: Directory to save output files (if None, uses document directory)
        save_intermediates: Whether to save intermediate results
        
    Returns:
        The final enriched JSON data
    """
    processor = PropertyProcessor(template_path)
    return processor.process_document(document_path, output_dir, save_intermediates) 