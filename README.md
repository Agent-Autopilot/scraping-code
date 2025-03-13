# Landlord Autopilot

A property management system that uses natural language processing to automate property updates and management tasks.

## Features

- Natural language processing of property management updates
- Support for properties, units, tenants, leases, and documents
- Automated address validation and zip code lookup
- Structured data persistence with JSON
- GPT-4 powered text analysis

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

## Usage

1. Process bulk updates from a file:
```bash
python src/bulk_processor.py
```

2. Interactive mode:
```bash
python src/data_manager.py
```

## Project Structure

- `src/`: Source code
  - `data_models.py`: Data classes and models
  - `bulk_processor.py`: Bulk update processing
  - `data_manager.py`: Data persistence and CRUD
  - `nlp_processor.py`: Natural language processing
- `docs/`: Documentation and notes
- `schema.json`: Property management data
- `requirements.txt`: Python dependencies
- `.env`: Environment variables

For detailed documentation, see [docs/README.md](docs/README.md)

## License

MIT License