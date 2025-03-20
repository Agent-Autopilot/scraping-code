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
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(parent_dir)

# Import property processor
from src.property_processor import PropertyProcessor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def print_json(data):
    """Print JSON data in a readable format."""
    print(json.dumps(data, indent=2))

def test_property_processor():
    """Test the PropertyProcessor with multiple documents."""
    # Set up paths
    base_dir = os.path.abspath(os.path.dirname(__file__))
    output_dir = os.path.join(base_dir, "output5")
    pdf_path = os.path.join(base_dir, "APT A Lease.pdf")
    text_path = os.path.join(base_dir, "woodbridge_test_input.txt")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info("Starting PropertyProcessor test with multiple documents")
    
    # Initialize processor with empty template
    processor = PropertyProcessor()
    
    # Process first document (PDF)
    logger.info(f"Processing first document: {pdf_path}")
    first_result = processor.process_document(
        pdf_path, 
        output_dir=output_dir,
        save_intermediates=True
    )
    
    # Log the result
    logger.info("Processing of first document complete. Result:")
    print_json(first_result)
    
    # Save intermediate result for next document
    intermediate_path = os.path.join(output_dir, "intermediate_result.json")
    with open(intermediate_path, "w") as f:
        json.dump(first_result, f, indent=2)
    logger.info(f"Saved intermediate result to {intermediate_path}")
    
    # Process second document (Text file) with the result from the first document as template
    logger.info(f"\nProcessing second document: {text_path}")
    processor = PropertyProcessor(template_path=intermediate_path)
    final_result = processor.process_document(
        text_path, 
        output_dir=output_dir,
        save_intermediates=True
    )
    
    # Save the final result
    final_path = os.path.join(output_dir, "final_result.json")
    with open(final_path, "w") as f:
        json.dump(final_result, f, indent=2)
    
    # Log the final result
    logger.info("Processing of both documents complete. Final result:")
    print_json(final_result)
    
    # List all generated files
    logger.info("\nGenerated files:")
    for file in os.listdir(output_dir):
        file_path = os.path.join(output_dir, file)
        file_size = os.path.getsize(file_path)
        logger.info(f"- {file} ({file_size} bytes)")
    
    logger.info("Test completed successfully")
    return final_result

if __name__ == "__main__":
    try:
        result = test_property_processor()
        if result:
            logger.info("Test finished")
        else:
            logger.error("Test failed - no result returned")
    except Exception as e:
        logger.exception(f"Error during test: {e}") 