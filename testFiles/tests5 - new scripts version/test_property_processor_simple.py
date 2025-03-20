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
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    """Test the simplified version of property processor."""
    # Set up paths
    base_dir = os.path.abspath(os.path.dirname(__file__))
    output_dir = os.path.join(base_dir, "output5")
    pdf_path = os.path.join(base_dir, "APT A Lease.pdf")
    template_path = os.path.join(parent_dir, "src", "default.json")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info("Starting simplified PropertyProcessor test (limited to 10 instructions)")
    
    # Initialize processor with template
    processor = PropertyProcessor(template_path)
    
    # Step 1: Extract text from PDF
    logger.info(f"Step 1: Extracting text from PDF: {pdf_path}")
    text = processor.extract_text_from_document(
        pdf_path, 
        save_path=os.path.join(output_dir, "lease_extracted_text.txt")
    )
    
    # Step 2: Generate instructions from text
    logger.info("Step 2: Generating instructions from extracted text")
    instructions = processor.generate_instructions_from_text(
        text, 
        save_path=os.path.join(output_dir, "lease_instructions.json")
    )
    
    # Step 3: Get template
    logger.info("Step 3: Using template from processor")
    template = processor.template
    
    # Check if instructions exist
    if not instructions or "instructions" not in instructions:
        logger.error("No instructions generated")
        return None
    
    # Limit instructions to 10 for simplified testing
    instruction_list = instructions.get("instructions", [])
    max_instructions = 10
    if len(instruction_list) > max_instructions:
        logger.info(f"Limiting instructions from {len(instruction_list)} to maximum of {max_instructions}")
        limited_instructions = {"instructions": instruction_list[:max_instructions]}
        
        # Save limited instructions for reference
        with open(os.path.join(output_dir, "lease_limited_instructions.json"), "w") as f:
            json.dump(limited_instructions, f, indent=2)
        logger.info(f"Saved limited instructions set with {len(limited_instructions['instructions'])} instructions")
        
        # Log the instructions we're processing
        logger.info(f"Processing {len(limited_instructions['instructions'])} instructions:")
        for i, instruction in enumerate(limited_instructions['instructions']):
            logger.info(f"  {i+1}. {instruction}")
    else:
        limited_instructions = instructions
    
    # Step 4: Apply instructions to create JSON
    logger.info("Step 4: Applying instructions to template (using batched processing)")
    json_data, results = processor.apply_instructions_to_json(
        template, 
        limited_instructions, 
        save_path=os.path.join(output_dir, "lease_result.json"),
        batch_size=10
    )
    
    # Check results
    if results and results["success"]:
        logger.info("Processing complete. Result:")
        print(json.dumps(json_data, indent=2))
        logger.info("All instructions were applied successfully!")
    else:
        logger.warning("Some instructions failed:")
        for failed in results.get("failed_instructions", []):
            logger.warning(f"  Failed: {failed}")
    
    # List all files in the output directory
    logger.info("\nGenerated files:")
    for root, _, files in os.walk(output_dir):
        for f in files:
            file_path = os.path.join(root, f)
            file_size = os.path.getsize(file_path)
            # Count lines in the file
            try:
                with open(file_path, 'r') as file:
                    line_count = sum(1 for _ in file)
            except:
                line_count = 0
            logger.info(f"- {f} ({file_size} bytes)")
    
    logger.info("Test completed successfully")
    return json_data

if __name__ == "__main__":
    result = test_property_processor_simple()
    logger.info("Test finished") 