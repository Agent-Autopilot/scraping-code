# Landlord Autopilot

Landlord Autopilot streamlines property management by automatically extracting and organizing information from your property documents. It eliminates manual data entry by processing leases, agreements, and records to create a comprehensive, centralized database of all your properties, units, tenants, and leases.

## Features

- **Centralized Information Storage**: Consolidate data from all your property documents into a single, organized file
- **Effortless Document Processing**: Upload leases, agreements, and property records without manual data entry
- **Automatic Information Extraction**: System identifies and extracts key details from your documents
- **Smart Data Enrichment**: Automatically fills in missing information based on context
- **Multi-Document Support**: Process information from various sources to build a complete property profile

## Code Structure

### Source Files (`src/`)

- **`property_processor.py`**: Main interface that orchestrates the entire document processing pipeline
  - Handles document intake from various formats (PDF, DOCX, TXT)
  - Coordinates text extraction, instruction generation, and JSON updates
  - Manages the enrichment process to fill information gaps
  - Provides both object-oriented and functional interfaces for flexibility
  - Maintains state between multiple document processing operations

- **`data_models.py`**: Comprehensive data structures for property management entities
  - Defines hierarchical relationships between properties, units, tenants, and leases
  - Implements JSON serialization/deserialization for persistent storage
  - Provides optional fields throughout to handle partial information
  - Uses type hints for better code reliability and IDE support
  - Structures data to mirror real-world property management relationships

### Scripts (`src/scripts/`)

- **`data_manager.py`**: Core data manipulation engine
  - Processes structured instructions to update JSON data
  - Handles entity creation, updates, and relationship management
  - Maintains data integrity during updates
  - Tracks failed instructions for debugging
  - Implements intelligent merging of new and existing data

- **`nlp_processor.py`**: Natural language understanding component
  - Analyzes document text to determine intent and extract entities
  - Transforms unstructured text into actionable instructions
  - Uses OpenAI's language models with specialized prompts
  - Handles ambiguity in natural language descriptions
  - Normalizes dates, currency values, and contact information

- **`text_to_instructions.py`**: Specialized text processing module
  - Converts property-specific language into structured instructions
  - Breaks complex updates into atomic operations
  - Standardizes formatting for consistency
  - Prioritizes instructions based on dependencies
  - Handles edge cases in property descriptions

- **`data_enricher.py`**: Intelligent data completion system
  - Analyzes existing data to identify information gaps
  - Generates suggestions for missing fields based on context
  - Cross-references information across entities
  - Provides confidence levels for suggested enrichments
  - Returns enrichment instructions without modifying data directly

- **`document_converter.py`**: Multi-format document processing
  - Extracts text from PDF, DOCX, and plain text files
  - Filters irrelevant content to focus on property information
  - Preserves important structural elements from documents
  - Handles document encoding and formatting issues
  - Uses AI to identify the most relevant sections of documents

- **`utils.py`**: Shared utility functions and helper classes
  - `GPTClient`: Robust OpenAI API wrapper with error handling and retries
  - `FileManager`: Comprehensive file operations for JSON and text
  - Data conversion utilities for various property management formats
  - Logging configuration and standardized error handling
  - Helper functions for data model descriptions and validation