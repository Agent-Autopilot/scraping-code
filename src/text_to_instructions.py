"""Convert unstructured text into property management instructions.

This module takes unstructured text about properties and converts it into
a series of natural language instructions that can be processed by the
property management system.
"""

import os
from typing import List
from openai import OpenAI
from dotenv import load_dotenv

class TextToInstructions:
    """Convert unstructured text into property management instructions."""
    
    def __init__(self):
        """Initialize the converter with OpenAI client."""
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = os.getenv('GPT_MODEL', 'gpt-4o-mini')

    def convert_text(self, text: str) -> List[str]:
        """Convert unstructured text into a list of property management instructions.
        
        Args:
            text: Unstructured text containing property information
            
        Returns:
            List of natural language instructions for the property management system
        """
        prompt = f"""Convert the following unstructured text about a property into a series of clear, line-by-line property management instructions.

For example, given:
```
name: Sample Property
address: 123 Main St, Boston MA 02108
owner: ABC LLC (contact: john@abc.com, 555-0123)
unit 101: tenant Bob Smith, rent $1000, security $2000
```

Convert to instructions like:
1. Create a new property called Sample Property at 123 Main St, Boston, MA 02108
2. Set the owner to ABC LLC
3. Update the owner's email to john@abc.com and phone to 5550123
4. Create unit 101
5. Add tenant Bob Smith to unit 101
6. Set lease for unit 101 with rent $1000 and security deposit $2000

Rules:
1. Each instruction should be a complete, natural language command
2. Include all available information (property details, owner info, units, tenants, etc.)
3. Break down complex information into simple, atomic updates
4. Use standard formats for:
   - Addresses (include street, city, state, zip if available)
   - Phone numbers (just digits)
   - Dates (YYYY-MM-DD format)
   - Currency (no commas, just digits)
5. Skip any information that's marked as uncertain with "?" or similar
6. For missing or incomplete information, skip those fields rather than making assumptions
7. For move-in and move-out dates, convert them to proper YYYY-MM-DD format
8. For payment dates, include them as lease due dates
9. For phone/email combinations, split them into separate contact updates
10. For unit numbers, include the bed count in the unit name if provided

Now, convert this text into property management instructions:

{text}"""

        try:
            print("\nSending text to OpenAI for conversion...")
            print(f"Model: {self.model.split('#')[0].strip()}")
            print(f"API Key: {self.client.api_key[:8]}...")
            messages = [
                {"role": "system", "content": "You are a property management system that converts unstructured text into clear instructions."},
                {"role": "user", "content": prompt}
            ]
            print(f"Messages: {messages}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1
            )
            
            # Split the response into individual instructions
            instructions = []
            print("\nGenerated instructions:")
            for line in response.choices[0].message.content.strip().split('\n'):
                line = line.strip()
                # Remove numbered prefixes like "1. ", "2. ", etc.
                if line and not line.startswith('#'):
                    line = line.split('. ', 1)[-1] if '. ' in line else line
                    instructions.append(line)
                    print(f"- {line}")
            
            return instructions
            
        except Exception as e:
            print(f"Error converting text to instructions: {str(e)}")
            return []

def main():
    """Example usage of the text to instructions converter."""
    converter = TextToInstructions()
    
    # Example text
    text = """
    name: Sample Property
    address: 123 Main St, Boston MA 02108
    owner: ABC LLC (contact: john@abc.com, 555-0123)
    unit 101: tenant Bob Smith, rent $1000, security $2000
    """
    
    instructions = converter.convert_text(text)
    print("\nConverted Instructions:")
    for i, instruction in enumerate(instructions, 1):
        print(f"{i}. {instruction}")

if __name__ == "__main__":
    main() 