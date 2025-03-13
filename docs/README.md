# Landlord Autopilot Documentation

This directory contains documentation and notes for the Landlord Autopilot project.

## Project Structure

```
landlord-autopilot/
├── src/                    # Source code directory
│   ├── data_models.py     # Data classes and models
│   ├── bulk_processor.py  # Bulk update processing
│   ├── data_manager.py    # Data persistence and CRUD
│   └── nlp_processor.py   # Natural language processing
├── docs/                  # Documentation directory
│   └── README.md         # This file
└── schema.json           # Property management schema
```

## Code Organization

### Source Code (`src/`)

1. `data_models.py`
   - Contains data classes for the property management system
   - Includes models for Address, ContactInfo, Document, Photo, etc.
   - Uses dataclasses and dataclasses_json for serialization

2. `bulk_processor.py`
   - Handles bulk processing of text updates
   - Coordinates between NLP Processor and Data Manager
   - Provides command-line interface for batch updates

3. `data_manager.py`
   - Manages data persistence and updates
   - Handles CRUD operations for properties, units, tenants, etc.
   - Maintains schema integrity

4. `nlp_processor.py`
   - Processes natural language updates using GPT-4
   - Converts text input into structured instructions
   - Validates and formats updates

## Data Flow

1. User provides natural language updates
2. NLP Processor converts text to structured data
3. Bulk Processor validates and routes updates
4. Data Manager applies changes to the database
5. Changes are persisted to schema.json

## Update Types

The system supports the following update types:
- Property updates (name, address, etc.)
- Owner updates (contact info, documents)
- Tenant updates (personal info, lease)
- Lease updates (dates, amounts)
- Document updates (new/modify documents)
- Unit updates (photos, current tenant) 