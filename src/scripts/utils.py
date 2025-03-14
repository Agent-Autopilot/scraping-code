"""Utility functions and classes for the property management system."""

import os
import json
from typing import Dict, Any, Optional, List, Tuple, Callable
from pathlib import Path
import ast
import openai
from dotenv import load_dotenv
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class GPTClient:
    """Wrapper for OpenAI API client with common functionality."""
    
    def __init__(self, model: Optional[str] = None):
        """Initialize the GPT client.
        
        Args:
            model: Optional model name to use. If None, uses the GPT_MODEL env var or a default.
        """
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = model or os.getenv('GPT_MODEL', 'gpt-4o-mini')
        logger.info(f"Initialized GPTClient with model: {self.model}")
    
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
                logger.debug(f"Querying GPT model (attempt {attempt+1}/{max_retries})")
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature
                )
                
                return response.choices[0].message.content
                
            except Exception as e:
                logger.error(f"Error on attempt {attempt + 1}/{max_retries}: {str(e)}")
                if attempt == max_retries - 1:
                    logger.error(f"Failed after {max_retries} attempts")
                    return None
        
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
                logger.debug(f"Querying GPT model for parsing (attempt {attempt+1}/{max_retries})")
                response = self.query(prompt, system_message, temperature)
                
                if response is None or response.lower() == 'none':
                    logger.warning("Received None or 'none' response from GPT")
                    return None
                
                # Clean up the response to ensure valid Python syntax
                # Remove code blocks if present
                if response.startswith('```'):
                    logger.debug("Removing code block markers from response")
                    response = response.split('```')[1]
                    if response.startswith('python'):
                        response = response[6:]
                response = response.strip()
                
                # Use custom parser if provided, otherwise try to use ast.literal_eval
                if parser:
                    logger.debug("Using custom parser function")
                    return parser(response)
                else:
                    try:
                        logger.debug("Attempting to parse response with ast.literal_eval")
                        return ast.literal_eval(response)
                    except (ValueError, SyntaxError) as e:
                        logger.error(f"Error parsing response on attempt {attempt + 1}: {str(e)}")
                        logger.error(f"Raw response: {response}")
                        if attempt == max_retries - 1:
                            raise
                        continue
                
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"GPT processing failed after {max_retries} attempts: {str(e)}")
                    logger.error(traceback.format_exc())
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
        except FileNotFoundError:
            logger.warning(f"File not found: {file_path}")
            return {}
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in file: {file_path}")
            return {}
        except Exception as e:
            logger.error(f"Error loading JSON data: {str(e)}")
            logger.error(traceback.format_exc())
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
            logger.error(f"Error saving JSON data: {str(e)}")
            logger.error(traceback.format_exc())
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
        except FileNotFoundError:
            logger.warning(f"File not found: {file_path}")
            return ""
        except Exception as e:
            logger.error(f"Error loading text data: {str(e)}")
            logger.error(traceback.format_exc())
            return ""
    
    @staticmethod
    def save_text(file_path: str, text: str) -> bool:
        """Save text data to file.
        
        Args:
            file_path: Path to save the text file
            text: String to save to the file
            
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
            logger.error(f"Error saving text data: {str(e)}")
            logger.error(traceback.format_exc())
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
                logger.warning(f"Warning: Could not convert {field} value '{result[field]}' to float. Keeping as string.")
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

def parse_python_value(value_str: str) -> Any:
    """Parse a Python value from a string.
    
    Args:
        value_str: String representation of a Python value
        
    Returns:
        Parsed Python value
    """
    try:
        return ast.literal_eval(value_str)
    except (SyntaxError, ValueError):
        # If it can't be parsed as a Python literal, return it as a string
        return value_str

def find_template_path(template_name: str) -> Optional[str]:
    """Find the path to a template file.
    
    Args:
        template_name: Name of the template file (without extension)
        
    Returns:
        Path to the template file or None if not found
    """
    # Check in the current directory
    if os.path.exists(f"{template_name}.json"):
        return f"{template_name}.json"
    
    # Check in the scripts directory
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(scripts_dir, f"{template_name}.json")
    
    if os.path.exists(template_path):
        return template_path
    
    return None

def generate_id(prefix: str = "", length: int = 8) -> str:
    """Generate a random ID.
    
    Args:
        prefix: Optional prefix for the ID
        length: Length of the random part of the ID
        
    Returns:
        Generated ID
    """
    import random
    import string
    
    random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return f"{prefix}{random_part}"

def get_data_models_description() -> str:
    """Get a detailed description of all data models for GPT input.
    
    This function dynamically discovers and returns a string description of all data models 
    defined in data_models.py, including their fields, types, and descriptions. This is useful 
    for providing context to GPT when processing property-related information.
    
    Returns:
        A string description of all data models
    """
    import dataclasses
    import sys
    import os
    import inspect
    
    # Ensure parent directory is in path
    parent_dir = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
    
    # Dynamically import data_models module
    try:
        import src.data_models as data_models_module
    except ImportError:
        # Try relative import if the above fails
        try:
            from .. import data_models as data_models_module
        except ImportError:
            return "Error: Unable to import data_models module"
    
    # Discover all dataclass models in the module
    data_models = []
    for name, obj in inspect.getmembers(data_models_module):
        # Check if it's a dataclass and not imported from another module
        if dataclasses.is_dataclass(obj) and obj.__module__ == data_models_module.__name__:
            data_models.append(obj)
    
    if not data_models:
        return "No data models found in the data_models module."
    
    # Build description
    description = "# Property Management Data Models\n\n"
    
    for model in data_models:
        # Get class name and docstring
        class_name = model.__name__
        class_doc = model.__doc__ or f"{class_name} data model"
        
        description += f"## {class_name}\n{class_doc}\n\n### Fields:\n"
        
        # Get fields from dataclass
        for field in dataclasses.fields(model):
            field_name = field.name
            field_type = field.type
            
            # Convert type to string representation
            if hasattr(field_type, "__name__"):
                type_name = field_type.__name__
            else:
                type_name = str(field_type).replace("typing.", "")
            
            # Get field docstring if available (from comments in the class)
            field_doc = ""
            if hasattr(model, f"__{field_name}_doc__"):
                field_doc = f" - {getattr(model, f'__{field_name}_doc__')}"
            
            description += f"- {field_name} ({type_name}){field_doc}\n"
        
        description += "\n"
    
    return description 