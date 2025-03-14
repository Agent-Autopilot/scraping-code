"""Test script for document_converter.py

This script demonstrates how to use the document_converter module to convert
various document formats to plaintext and extract relevant information.
"""

import os
import sys
import argparse

# Add the src directory to the Python path so we can import the document_converter module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))
from document_converter import convert_document_to_relevant_text

def main():
    """
    Main function to test the document converter.
    """
    parser = argparse.ArgumentParser(description='Convert a document to plaintext and extract relevant information.')
    parser.add_argument('file_path', help='Path to the document file')
    parser.add_argument('--output', '-o', help='Path to save the output text (optional)')
    
    args = parser.parse_args()
    
    try:
        print(f"Processing document: {args.file_path}")
        result = convert_document_to_relevant_text(args.file_path)
        
        print("\nExtracted Relevant Information:")
        print("-" * 50)
        print(result)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result)
            print(f"\nOutput saved to: {args.output}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 