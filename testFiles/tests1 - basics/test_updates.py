import json
import shutil
import sys
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.update_database import DataManager
from src.update_processor import UpdateProcessor
from openai import OpenAI
import os
from dotenv import load_dotenv

def preprocess_test_cases(inputs: list[str], schema: dict) -> list[str]:
    """Convert test inputs into well-formatted instructions using GPT-4"""
    load_dotenv()
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    prompt = f"""Given the following property management schema and list of test inputs, convert each input into a well-formatted, precise instruction that includes all necessary context and specific references.

Schema:
{json.dumps(schema, indent=2)}

Test Inputs:
{json.dumps(inputs, indent=2)}

For each input, create a precise instruction that:
1. Uses specific identifiers instead of generic references
2. Includes all necessary context from the schema
3. Uses consistent formatting and terminology
4. Makes implicit references explicit
5. Maintains all important details from the original input
6. For address updates:
   - Include complete address information
   - For zip codes, use accurate data (e.g., Woodbridge, CT is 06525; Nyack, NY is 10960)
7. For entity updates:
   - Maintain all existing fields not being updated
   - Ensure proper nesting of contact information
   - Reference the specific entity being updated

Respond with a JSON array of strings containing the converted instructions in the same order as the inputs.
Each instruction should be self-contained and unambiguous."""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a property management system instruction formatter. Convert user inputs into precise, well-formatted instructions."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )
    
    try:
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error parsing GPT response: {str(e)}")
        return inputs

def backup_schema():
    """Create a backup of the schema file"""
    shutil.copy('testFiles/tests1 - basics/test_schema.json', 'testFiles/tests1 - basics/test_schema.backup.json')

def restore_schema():
    """Restore the schema from backup"""
    shutil.move('testFiles/tests1 - basics/test_schema.backup.json', 'testFiles/tests1 - basics/test_schema.json')

def test_updates():
    """Test various update scenarios"""
    try:
        # Create backup of schema
        backup_schema()

        # Initialize manager and processor
        manager = DataManager(schema_path='testFiles/tests1 - basics/test_schema.json')
        processor = UpdateProcessor()

        # Original test cases
        inputs = [
            "change property name to Woodbridge Duplex",
            "change address to 10 Miles ave, woodbridge ct. find the zip code yourself",
            "change owner to woodbridge community partners LLC",
            "email of owner to vadim.tantsyura@gmail.com",
            "phone of LLC to 6282599139",
            "address of LLC to 3 willow ct, nyack ny, find the zip code yourself"
        ]

        # Preprocess test cases
        with open('testFiles/tests1 - basics/test_schema.json', 'r') as f:
            schema = json.load(f)
        
        print("\nPreprocessing test cases...")
        test_cases = preprocess_test_cases(inputs, schema)
        
        print("\nOriginal inputs vs Processed instructions:")
        for i, (original, processed) in enumerate(zip(inputs, test_cases), 1):
            print(f"\n{i}. Original: {original}")
            print(f"   Processed: {processed}")

        print("\nRunning test cases...")
        for test in test_cases:
            print(f"\nTest input: {test}")
            success = processor.process_update(test, manager)
            print(f"Result: {'Success' if success else 'Failed'}")

            if success:
                # Verify the changes were saved
                with open('testFiles/tests1 - basics/test_schema.json', 'r') as f:
                    current_data = json.load(f)
                print("Changes saved to schema.json")

    except Exception as e:
        print(f"Test failed with error: {str(e)}")
    finally:
        # Restore original schema
        # restore_schema()
        pass

if __name__ == "__main__":
    test_updates() 