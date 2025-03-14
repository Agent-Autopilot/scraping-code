# Landlord Autopilot

A property management system that helps landlords manage properties, units, tenants, and leases through natural language processing and automated data enrichment.

## Features

- **Property Management**: Create and manage properties, units, tenants, and leases
- **Natural Language Processing**: Convert unstructured text into property management instructions
- **Data Enrichment**: Identify and fill in missing information in property data
- **Error Detection**: Find and correct inconsistencies and errors in property data
- **Flexible Data Models**: Handle partial information with optional fields
- **Document Conversion**: Convert various document formats (PDF, DOCX, etc.) to plaintext and extract relevant information

## Components

### Property Manager (`src/property_manager.py`)

The core component that manages properties, units, tenants, and leases. It provides methods to:
- Create and update properties
- Add and update units
- Add and update tenants
- Manage leases
- Process natural language updates

### Data Manager (`src/data_manager.py`)

Handles data persistence and updates, including:
- Loading and saving property schemas
- Updating property information
- Managing units, tenants, and leases
- Creating entities if they don't exist

### NLP Processor (`src/nlp_processor.py`)

Processes natural language updates using OpenAI's language models to convert them into structured property management instructions.

### Text to Instructions (`src/text_to_instructions.py`)

Converts unstructured text about properties into structured property management instructions using OpenAI's language models.

### Data Enricher (`src/data_enricher.py`)

Analyzes existing property data and original text data to identify and fill in missing information, such as:
- Missing address components (e.g., zip codes)
- Missing contact information (e.g., phone numbers, emails)
- Missing lease details (e.g., due dates)
- Inconsistencies between text data and structured data
- Errors in the data that need correction

### Document Converter (`src/document_converter.py`)

Converts various document formats to plaintext and extracts relevant information based on data models:
- Supports PDF, DOCX, DOC, and other formats
- Extracts text from documents using appropriate libraries
- Uses AI to identify and extract only the information relevant to the data models
- Returns the extracted information as a string

### Utilities (`src/utils.py`)

Provides common utility functions and classes used throughout the system:
- `GPTClient`: A wrapper for OpenAI API with retry logic and error handling
- `FileManager`: Handles file operations for loading and saving data
- Helper functions for data conversion and entity creation

## Code Organization

### Source Code (`src/`)

1. `data_models.py`
   - Contains data classes for the property management system
   - Includes models for Address, ContactInfo, Document, Photo, etc.
   - Uses dataclasses and dataclasses_json for serialization
   - All fields except IDs are optional to handle partial information

2. `bulk_processor.py`
   - Handles bulk processing of text updates
   - Coordinates between NLP Processor and Data Manager
   - Provides functions for processing multiple instructions at once

3. `data_manager.py`
   - Manages data persistence and updates
   - Handles CRUD operations for properties, units, tenants, etc.
   - Maintains schema integrity
   - Creates entities if they don't exist

4. `nlp_processor.py`
   - Processes natural language updates using OpenAI's language models
   - Converts text input into structured instructions
   - Validates and formats updates

5. `property_manager.py`
   - High-level interface for property management operations
   - Combines functionality of data manager and NLP processor
   - Provides methods for managing properties, units, tenants, and leases

6. `text_to_instructions.py`
   - Converts unstructured text about properties into structured instructions
   - Uses OpenAI's language models to generate clear, line-by-line instructions
   - Formats dates, phone numbers, and currency values consistently

7. `data_enricher.py`
   - Analyzes existing property data and original text data
   - Identifies and fills in missing information
   - Generates instructions to correct inconsistencies and errors

8. `document_converter.py`
   - Converts various document formats to plaintext
   - Extracts relevant information based on data models
   - Uses AI to identify important information in documents
   - Handles errors gracefully with detailed logging

9. `utils.py`
   - Provides common utility functions and classes used throughout the system
   - `GPTClient`: A wrapper for OpenAI API with retry logic and error handling
   - `FileManager`: Handles file operations for loading and saving data
   - Helper functions for data conversion and entity creation

## Data Flow

1. User provides natural language updates
2. NLP Processor converts text to structured instructions
3. Property Manager processes instructions and routes updates
4. Data Manager applies changes to the database
5. Changes are persisted to schema.json

## Update Types

The system supports the following update types:
- Property updates (name, address, etc.)
- Owner updates (contact info, documents)
- Tenant updates (personal info, lease)
- Lease updates (dates, amounts, due dates)
- Document updates (new/modify documents)
- Unit updates (photos, current tenant)

## Usage

### Data Enrichment

To enrich property data:

```python
from src.data_enricher import DataEnricher

# Initialize the data enricher
enricher = DataEnricher()

# Enrich data
enricher.enrich_data('path/to/schema.json', 'path/to/text_data.txt')
```

The data enricher will:
1. Analyze the JSON schema and text data
2. Identify missing or incomplete information
3. Generate instructions to fill in the missing data
4. Apply the instructions to update the JSON schema
5. Save the results for review

### Text to Instructions

To convert unstructured text into property management instructions:

```python
from src.text_to_instructions import TextToInstructions

# Initialize the converter
converter = TextToInstructions()

# Convert text to instructions
text = "Property at 123 Main St with tenant John Smith paying $1200 rent due on the 15th"
instructions = converter.convert_text(text)

# Process each instruction
for instruction in instructions:
    print(instruction)
```

### Document Conversion

To convert documents and extract relevant information:

```python
from src.document_converter import convert_document_to_relevant_text

# Convert a document and extract relevant information
try:
    result = convert_document_to_relevant_text("path/to/your/document.pdf")
    print(result)
except ValueError as e:
    print(f"Error: {str(e)}")
```

You can also use the included test script:

```bash
python "testFiles/tests4 - document conversion/test_document_converter.py" "path/to/your/document.pdf"
```

Or with output to a file:

```bash
python "testFiles/tests4 - document conversion/test_document_converter.py" "path/to/your/document.pdf" --output "result.txt"
```

### Best Practices and Limitations

When using the data enricher, be aware of the following:

1. **Review Suggestions**: Always review the generated suggestions before applying them, as the AI might make incorrect inferences.

2. **Check for Hallucinations**: The AI might generate information not present in the source data (e.g., assigning "last day of each month" as due dates without evidence).

3. **Verify Cross-Entity Inferences**: Be cautious of suggestions that apply information from one entity to another (e.g., using owner's zip code for property address).

4. **Examine Failed Instructions**: Review the failed instructions file to understand what couldn't be processed.

5. **Backup Data**: Always keep a backup of your data before enrichment, which the system automatically creates.

## Environment Variables

The system uses the following environment variables:
- `OPENAI_API_KEY`: Required for API access to OpenAI
- `GPT_MODEL`: The model to use for NLP processing (defaults to gpt-4o-mini)

## Test Scripts

- `testFiles/tests1 - basics/test_schema.py`: Tests loading and creating objects from JSON schema
- `testFiles/tests1 - basics/test_updates.py`: Tests various update scenarios
- `testFiles/tests2 - text instructions/test_property_setup.py`: Sets up a property management system with a duplex property
- `testFiles/tests3 - txt input and enrichment/test_text_to_instructions.py`: Tests converting unstructured text to property management instructions
- `testFiles/tests3 - txt input and enrichment/test_data_enricher.py`: Tests the data enrichment functionality
- `testFiles/tests4 - document conversion/test_document_converter.py`: Tests converting documents to plaintext and extracting relevant information

## Requirements

- Python 3.8+
- OpenAI API key (set in `.env` file)
- Required packages (see `requirements.txt`)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/landlord-autopilot.git
cd landlord-autopilot
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## Project Structure

```
landlord-autopilot/
├── src/                    # Source code directory
│   ├── data_models.py     # Data classes and models
│   ├── bulk_processor.py  # Bulk update processing
│   ├── data_manager.py    # Data persistence and CRUD
│   ├── nlp_processor.py   # Natural language processing
│   ├── property_manager.py # High-level property management interface
│   ├── text_to_instructions.py # Text to instructions conversion
│   ├── data_enricher.py   # Data enrichment functionality
│   ├── document_converter.py # Document conversion functionality
│   ├── utils.py           # Utility functions and classes
│   └── templates/         # Template files for new schemas
├── testFiles/             # Test files and scripts
│   ├── tests1 - basics/   # Basic functionality tests
│   ├── tests2 - text instructions/ # Text instruction tests
│   ├── tests3 - txt input and enrichment/ # Data enrichment tests
│   ├── tests4 - document conversion/ # Document conversion tests
│   └── oldTests/          # Archive of previous test versions
├── docs/                  # Documentation directory
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (not in version control)
└── schema.json           # Property management schema
```

## Future Improvements

Potential improvements for the system include:

1. **Enhanced Validation**: Add more robust validation to prevent incorrect inferences
2. **Confidence Scoring**: Implement confidence scores for enrichment suggestions
3. **User Interface**: Create a web interface for reviewing and approving suggestions
4. **Scheduled Enrichment**: Set up periodic data enrichment to keep information up-to-date
5. **Multi-Source Enrichment**: Incorporate external data sources for validation
6. **Improved Error Handling**: Enhance error handling and recovery mechanisms
7. **Testing Framework**: Develop comprehensive unit and integration tests
8. **Documentation**: Create detailed API documentation and usage examples

## License

MIT License