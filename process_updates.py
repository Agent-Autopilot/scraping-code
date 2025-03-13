import json
from update_database import DataManager
from update_processor import UpdateProcessor
from openai import OpenAI
import os
from dotenv import load_dotenv

def parse_text_input(text_input: str) -> list[str]:
    """Split the input text into individual tasks by newlines and clean up"""
    # Split by newlines and remove empty lines
    tasks = [line.strip() for line in text_input.split('\n') if line.strip()]
    
    # Group related lines together (e.g., unit creation with multiple properties)
    grouped_tasks = []
    current_task = []
    
    for task in tasks:
        # If the line starts with a common action word, it's a new task
        action_words = ['add', 'create', 'update', 'change', 'modify', 'remove', 'delete']
        if any(task.lower().startswith(word) for word in action_words) and current_task:
            grouped_tasks.append('\n'.join(current_task))
            current_task = [task]
        else:
            current_task.append(task)
    
    # Add the last task if exists
    if current_task:
        grouped_tasks.append('\n'.join(current_task))
    
    return grouped_tasks

def preprocess_updates(text_input: str, schema: dict) -> list[str]:
    """Convert a bulk text input into well-formatted individual instructions using GPT-4"""
    load_dotenv()
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    prompt = f"""Given the following property management schema and bulk text input, break down the input into individual, well-formatted instructions.

Schema:
{json.dumps(schema, indent=2)}

Text Input:
{text_input}

Break down the input into separate instructions, where each instruction:
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
8. For new entities:
   - Include all required fields
   - Generate appropriate IDs where needed
   - Set up proper relationships with existing entities

Respond with a JSON array of strings containing the converted instructions.
Each instruction should be self-contained and unambiguous."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
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
        # If GPT fails, return the manually parsed tasks
        return parse_text_input(text_input)

def process_bulk_updates(text_input: str):
    """Process a bulk text input containing multiple property management updates"""
    try:
        # Initialize manager and processor
        manager = DataManager()
        processor = UpdateProcessor()

        # Load current schema for preprocessing
        with open('schema.json', 'r') as f:
            schema = json.load(f)
        
        print("\nPreprocessing updates...")
        instructions = preprocess_updates(text_input, schema)
        
        print("\nProcessed instructions:")
        for i, instruction in enumerate(instructions, 1):
            print(f"\n{i}. {instruction}")

        print("\nApplying updates...")
        for instruction in instructions:
            print(f"\nProcessing: {instruction}")
            success = processor.process_update(instruction, manager)
            print(f"Result: {'Success' if success else 'Failed'}")

            if success:
                print("Changes saved to schema.json")

    except Exception as e:
        print(f"Processing failed with error: {str(e)}")

def main():
    print("Enter your updates (press Ctrl+D or Ctrl+Z when finished):")
    try:
        # Read all input until EOF
        text_input = ""
        while True:
            try:
                line = input()
                text_input += line + "\n"
            except EOFError:
                break
        
        if text_input.strip():
            process_bulk_updates(text_input.strip())
        else:
            print("No input provided.")
            
    except KeyboardInterrupt:
        print("\nOperation cancelled.")

if __name__ == "__main__":
    main() 