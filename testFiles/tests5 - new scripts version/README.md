# PropertyProcessor Test

This directory contains a test script for the `PropertyProcessor` class, which provides a unified interface for processing property documents, creating structured JSON data, and enriching it with missing information.

## How to Run the Test

1. Add a PDF file named `sample_property.pdf` to this directory. This should be a document containing property information (e.g., a lease agreement, property description, etc.).

2. Run the test script:
   ```
   python test_property_processor.py
   ```

3. Check the `output` directory for the generated files:
   - `sample_property_extracted_text.txt`: The extracted text from the PDF
   - `sample_property_instructions.json`: The structured instructions generated from the text
   - `sample_property.json`: The JSON data created from the instructions
   - `sample_property_failed_instructions.json`: Any instructions that failed to apply
   - `sample_property_enrichment_instructions.txt`: Suggestions for enriching the JSON data
   - `sample_property_enriched.json`: The final enriched JSON data

## What the Test Does

The test script demonstrates two ways to use the `PropertyProcessor`:

1. Using the `PropertyProcessor` class directly:
   ```python
   processor = PropertyProcessor()
   result = processor.process_document(document_path, output_dir)
   ```

2. Using the convenience function:
   ```python
   result = process_property_document(document_path, output_dir=output_dir)
   ```

Both methods should produce the same result.

## Sample Document Requirements

For best results, the sample document should contain:
- Property details (address, name, etc.)
- Unit information (unit numbers, bedrooms, bathrooms, etc.)
- Tenant information (names, contact details, etc.)
- Lease information (start/end dates, rent amounts, etc.)

## Troubleshooting

If you encounter any issues:
1. Check the `test_log.txt` file for detailed logs
2. Ensure the PDF file is readable and contains relevant property information
3. Check that all required Python packages are installed 