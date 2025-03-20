#!/usr/bin/env python3
"""Test script for PropertyProcessor

This script demonstrates the functionality of the PropertyProcessor class
by processing multiple sample documents and applying changes to the same JSON.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add parent directory to Python path
parent_dir = str(Path(__file__).parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import PropertyProcessor
from src.property_processor import PropertyProcessor, process_property_document

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(Path(__file__).parent, "test_log.txt"))
    ]
)
logger = logging.getLogger(__name__)

def print_json(json_data):
    """Print JSON data in a readable format."""
    print(json.dumps(json_data, indent=2))

def test_property_processor():
    """Test the PropertyProcessor with multiple documents."""
    # Get the current directory
    current_dir = Path(__file__).parent
    
    # Create output directory
    output_dir = os.path.join(current_dir, "output4")
    os.makedirs(output_dir, exist_ok=True)
    
    # Define paths to the sample documents
    pdf_document_path = os.path.join(current_dir, "APT A Lease.pdf")
    txt_document_path = os.path.join(current_dir, "woodbridge_test_input.txt")
    
    # Check if the documents exist
    missing_files = []
    if not os.path.exists(pdf_document_path):
        missing_files.append("APT A Lease.pdf")
    if not os.path.exists(txt_document_path):
        missing_files.append("woodbridge_test_input.txt")
    
    if missing_files:
        logger.error(f"The following sample documents were not found: {', '.join(missing_files)}")
        logger.error("Please add the missing files to the tests5 directory")
        return
    
    # Initialize a single PropertyProcessor instance to maintain state between documents
    processor = PropertyProcessor()
    
    # Process the first document (PDF)
    logger.info(f"Processing first document: {pdf_document_path}")
    result = processor.process_document(pdf_document_path, output_dir)
    
    # Print the result after first document
    logger.info("Processing of first document complete. Result:")
    print_json(result)
    
    # Save intermediate result
    intermediate_json_path = os.path.join(output_dir, "intermediate_result.json")
    with open(intermediate_json_path, 'w') as f:
        json.dump(result, f, indent=2)
    logger.info(f"Saved intermediate result to {intermediate_json_path}")
    
    # Process the second document (TXT) and update the same JSON
    logger.info(f"\nProcessing second document: {txt_document_path}")
    
    # Extract text from the second document
    text = processor.extract_text_from_document(
        txt_document_path, 
        os.path.join(output_dir, "woodbridge_extracted_text.txt")
    )
    
    # Generate instructions from the text
    instructions = processor.generate_instructions_from_text(
        text, 
        os.path.join(output_dir, "woodbridge_instructions.json")
    )
    
    # Apply instructions to the existing JSON
    final_result, apply_results = processor.apply_instructions_to_json(
        result,  # Use the result from the first document
        instructions,
        os.path.join(output_dir, "final_result.json"),
        os.path.join(output_dir, "woodbridge_failed_instructions.json"),
        batch_size=10  # Process in batches of 10 instructions for better performance
    )
    
    # Enrich the final JSON with text from the second document
    enrichment_instructions = processor.enrich_json_with_text(
        final_result,
        text,
        os.path.join(output_dir, "woodbridge_enrichment_instructions.txt")
    )
    
    # Print the final result
    logger.info("Processing of both documents complete. Final result:")
    print_json(final_result)
    
    # List all generated files
    logger.info("\nGenerated files:")
    for file in os.listdir(output_dir):
        file_path = os.path.join(output_dir, file)
        file_size = os.path.getsize(file_path)
        logger.info(f"- {file} ({file_size} bytes)")
    
    return final_result

if __name__ == "__main__":
    logger.info("Starting PropertyProcessor test with multiple documents")
    try:
        result = test_property_processor()
        if result:
            logger.info("Test completed successfully")
        else:
            logger.error("Test failed - no result returned")
    except Exception as e:
        logger.exception(f"Error during test: {str(e)}")
    logger.info("Test finished") 