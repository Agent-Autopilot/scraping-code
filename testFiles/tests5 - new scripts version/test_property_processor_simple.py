#!/usr/bin/env python3
"""Simplified Test script for PropertyProcessor

This script tests only the basic functionality of the PropertyProcessor class
by processing just the PDF document without enrichment or text file processing.
Limited to the first 10 instructions.
"""

import os
import sys
import json
import logging
import traceback
from pathlib import Path

# Add parent directory to Python path
parent_dir = str(Path(__file__).parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import PropertyProcessor
from src.property_processor import PropertyProcessor
from src.scripts.apply_instructions import JSONUpdater

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def print_json(json_data):
    """Print JSON data in a readable format."""
    print(json.dumps(json_data, indent=2))

def test_property_processor_simple():
    """Simplified test for the PropertyProcessor that only processes the PDF document."""
    # Get the current directory
    current_dir = Path(__file__).parent
    
    # Create output directory - using output4 folder
    output_dir = os.path.join(current_dir, "output4")
    os.makedirs(output_dir, exist_ok=True)
    
    # Define path to the PDF document
    pdf_document_path = os.path.join(current_dir, "APT A Lease.pdf")
    
    # Check if the document exists
    if not os.path.exists(pdf_document_path):
        logger.error(f"The sample document was not found: APT A Lease.pdf")
        logger.error("Please add the missing file to the tests5 directory")
        return
    
    # Define path to the default JSON template
    default_template_path = os.path.join(parent_dir, "src", "default.json")
    
    # Check if the default template exists
    if not os.path.exists(default_template_path):
        logger.error(f"The default template was not found: {default_template_path}")
        logger.error("Please make sure the default.json file exists in the src directory")
        return
    
    # Initialize the PropertyProcessor with the default template
    processor = PropertyProcessor(template_path=default_template_path)
    
    # Step 1: Extract text from the PDF
    logger.info(f"Step 1: Extracting text from PDF: {pdf_document_path}")
    text = processor.extract_text_from_document(
        pdf_document_path, 
        os.path.join(output_dir, "lease_extracted_text.txt")
    )
    
    # Step 2: Generate instructions from the text
    logger.info(f"Step 2: Generating instructions from extracted text")
    instructions = processor.generate_instructions_from_text(
        text, 
        os.path.join(output_dir, "lease_instructions.json")
    )
    
    # Step 3: Use the template from processor.template
    logger.info(f"Step 3: Using template from processor")
    template = processor.template
    
    # Limit instructions to first 10
    if instructions and isinstance(instructions, dict) and "instructions" in instructions:
        original_count = len(instructions["instructions"])
        logger.info(f"Limiting instructions from {original_count} to maximum of 10")
        limited_instructions = instructions.copy()
        limited_instructions["instructions"] = instructions["instructions"][:10]
        
        # Save the limited instructions
        with open(os.path.join(output_dir, "lease_limited_instructions.json"), "w") as f:
            json.dump(limited_instructions, f, indent=2)
            
        logger.info(f"Saved limited instructions set with {len(limited_instructions['instructions'])} instructions")
        instructions = limited_instructions
    
    # Log the instructions that will be processed
    if instructions and isinstance(instructions, dict) and "instructions" in instructions:
        logger.info(f"Processing {len(instructions['instructions'])} instructions:")
        for i, instruction in enumerate(instructions["instructions"]):
            logger.info(f"  {i+1}. {instruction}")
    
    # Step 4: Apply instructions to the template
    logger.info(f"Step 4: Applying instructions to template (using batched processing)")
    try:
        result, apply_results = processor.apply_instructions_to_json(
            template,
            instructions,
            os.path.join(output_dir, "lease_result.json"),
            os.path.join(output_dir, "lease_failed_instructions.json"),
            batch_size=10  # Process in batches of 10 instructions for better performance
        )
        
        # Print the result
        logger.info("Processing complete. Result:")
        print_json(result)
        
        # Print failed instructions if any
        failed_instructions = apply_results.get("failed_instructions", [])
        if failed_instructions:
            logger.info(f"Number of failed instructions: {len(failed_instructions)}")
            for i, failed in enumerate(failed_instructions):
                logger.info(f"Failed instruction {i+1}: {failed.get('instruction')}")
                logger.info(f"Error: {failed.get('error')}")
        else:
            logger.info("All instructions were applied successfully!")
    except Exception as e:
        logger.error(f"Error applying instructions: {str(e)}")
        logger.error(traceback.format_exc())
        return None
    
    # List all generated files
    logger.info("\nGenerated files:")
    for file in os.listdir(output_dir):
        file_path = os.path.join(output_dir, file)
        file_size = os.path.getsize(file_path)
        logger.info(f"- {file} ({file_size} bytes)")
    
    return result

if __name__ == "__main__":
    logger.info("Starting simplified PropertyProcessor test (limited to 10 instructions)")
    try:
        result = test_property_processor_simple()
        if result:
            logger.info("Test completed successfully")
        else:
            logger.error("Test failed - no result returned")
    except Exception as e:
        logger.exception(f"Error during test: {str(e)}")
    logger.info("Test finished") 