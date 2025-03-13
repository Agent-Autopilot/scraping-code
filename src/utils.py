"""Utility functions and classes for the property management system."""

import os
import json
from typing import Dict, Any, Optional, List, Tuple, Callable
from pathlib import Path
import ast
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GPTClient:
    """Wrapper for OpenAI API client with common functionality."""
    
    def __init__(self, model: Optional[str] = None):
        """Initialize the GPT client.
        
        Args:
            model: Optional model name to use. If None, uses the GPT_MODEL env var or a default.
        """
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = model or os.getenv('GPT_MODEL', 'gpt-4o-mini')
    
    def query(self, 
              prompt: str, 
              system_message: str = "You are a helpful assistant.", 
              temperature: float = 0.1,
              max_retries: int = 3) -> Optional[str]:
        """Query the GPT model with retry logic.
        
        Args:
            prompt: The user prompt to send
            system_message: The system message to set context
            temperature: Temperature setting for response randomness
            max_retries: Maximum number of retry attempts
            
        Returns:
            The model's response text or None if processing fails
        """
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature
                )
                
                result = response.choices[0].message.content.strip()
                return result
                
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"GPT processing failed after {max_retries} attempts: {str(e)}")
                    return None
                continue
        
        return None
    
    def query_and_parse(self, 
                        prompt: str, 
                        system_message: str = "You are a helpful assistant.",
                        temperature: float = 0.1,
                        max_retries: int = 3,
                        parser: Callable[[str], Any] = None) -> Optional[Any]:
        """Query the GPT model and parse the response with retry logic.
        
        Args:
            prompt: The user prompt to send
            system_message: The system message to set context
            temperature: Temperature setting for response randomness
            max_retries: Maximum number of retry attempts
            parser: Optional function to parse the response
            
        Returns:
            The parsed response or None if processing fails
        """
        for attempt in range(max_retries):
            try:
                response = self.query(prompt, system_message, temperature)
                
                if response is None or response.lower() == 'none':
                    return None
                
                # Clean up the response to ensure valid Python syntax
                # Remove code blocks if present
                if response.startswith('```'):
                    response = response.split('```')[1]
                    if response.startswith('python'):
                        response = response[6:]
                response = response.strip()
                
                # Use custom parser if provided, otherwise try to use ast.literal_eval
                if parser:
                    return parser(response)
                else:
                    try:
                        return ast.literal_eval(response)
                    except (ValueError, SyntaxError) as e:
                        print(f"Error parsing response on attempt {attempt + 1}: {str(e)}")
                        print(f"Raw response: {response}")
                        if attempt == max_retries - 1:
                            raise
                        continue
                
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"GPT processing failed after {max_retries} attempts: {str(e)}")
                    return None
                continue
        
        return None


class FileManager:
    """Utility class for file operations."""
    
    @staticmethod
    def load_json(file_path: str) -> Dict[str, Any]:
        """Load JSON data from file.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Dictionary containing the JSON data or empty dict if loading fails
        """
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading JSON data: {str(e)}")
            return {}
    
    @staticmethod
    def save_json(file_path: str, data: Dict[str, Any], indent: int = 2) -> bool:
        """Save JSON data to file.
        
        Args:
            file_path: Path to save the JSON file
            data: Dictionary to save as JSON
            indent: Indentation level for the JSON file
            
        Returns:
            True if saving was successful, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=indent)
            return True
        except Exception as e:
            print(f"Error saving JSON data: {str(e)}")
            return False
    
    @staticmethod
    def load_text(file_path: str) -> str:
        """Load text data from file.
        
        Args:
            file_path: Path to the text file
            
        Returns:
            String containing the text data or empty string if loading fails
        """
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except Exception as e:
            print(f"Error loading text data: {str(e)}")
            return ""
    
    @staticmethod
    def save_text(file_path: str, text: str) -> bool:
        """Save text data to file.
        
        Args:
            file_path: Path to save the text file
            text: String to save
            
        Returns:
            True if saving was successful, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            with open(file_path, 'w') as f:
                f.write(text)
            return True
        except Exception as e:
            print(f"Error saving text data: {str(e)}")
            return False
    
    @staticmethod
    def get_base_path(file_path: str) -> Tuple[str, str]:
        """Get the base directory and base name from a file path.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (base_dir, base_name)
        """
        base_dir = os.path.dirname(file_path)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        return base_dir, base_name


def convert_numeric_fields(data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
    """Convert specified fields to numeric values if possible.
    
    Args:
        data: Dictionary containing the data
        fields: List of field names to convert
        
    Returns:
        Updated dictionary with converted fields
    """
    result = data.copy()
    for field in fields:
        if field in result and result[field] is not None:
            try:
                result[field] = float(result[field])
            except ValueError:
                print(f"Warning: Could not convert {field} value '{result[field]}' to float. Keeping as string.")
    return result


def create_entity_if_missing(entity, entity_class, default_name: str = None, **kwargs):
    """Create an entity if it doesn't exist.
    
    Args:
        entity: The entity to check
        entity_class: The class to instantiate if entity is missing
        default_name: Default name for the entity if needed
        **kwargs: Additional arguments to pass to the entity constructor
        
    Returns:
        The existing entity or a new instance
    """
    if entity is None:
        if default_name is not None:
            kwargs['name'] = default_name
        return entity_class(**kwargs)
    return entity 