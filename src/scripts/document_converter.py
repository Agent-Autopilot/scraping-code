"""Document Converter Script

This script provides functionality to convert various document formats (PDF, DOCX, etc.)
to plaintext and extract the most important text related to property management.
"""

import os
import sys
import logging
import traceback
from typing import Optional

# Add parent directory to Python path if needed
parent_dir = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import from scripts.utils
from src.scripts.utils import GPTClient, get_data_models_description

# Document conversion libraries
try:
    import PyPDF2
    from docx import Document as DocxDocument
    # Textract is optional
    try:
        import textract
        TEXTRACT_AVAILABLE = True
    except ImportError:
        TEXTRACT_AVAILABLE = False
except ImportError:
    logging.warning("Some document conversion libraries are missing. Run 'pip install PyPDF2 python-docx' to install them.")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    try:
        text = ""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text() + "\n\n"
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        logger.error(traceback.format_exc())
        return f"Error extracting text: {str(e)}"

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from a DOCX file."""
    try:
        doc = DocxDocument(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {str(e)}")
        logger.error(traceback.format_exc())
        return f"Error extracting text: {str(e)}"

def extract_text_using_textract(file_path: str) -> str:
    """Extract text using textract (fallback method)."""
    try:
        if not TEXTRACT_AVAILABLE:
            return "Textract not available. Install with 'pip install textract'."
        
        text = textract.process(file_path).decode('utf-8')
        return text
    except Exception as e:
        logger.error(f"Error extracting text with textract: {str(e)}")
        logger.error(traceback.format_exc())
        return f"Error extracting text: {str(e)}"

def extract_text_from_document(file_path: str) -> str:
    """Extract text from a document based on its file extension."""
    if not os.path.exists(file_path):
        return f"File not found: {file_path}"
    
    file_extension = os.path.splitext(file_path)[1].lower()
    
    # If it's a text file, just read it directly
    if file_extension == '.txt':
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading text file: {str(e)}")
            return f"Error reading text file: {str(e)}"
    
    # Try specific extractors based on file extension
    if file_extension == '.pdf':
        text = extract_text_from_pdf(file_path)
    elif file_extension == '.docx':
        text = extract_text_from_docx(file_path)
    else:
        # Try textract as a fallback for other file types
        if TEXTRACT_AVAILABLE:
            text = extract_text_using_textract(file_path)
        else:
            return f"Unsupported file type: {file_extension}. Install textract for broader support."
    
    # If the text is very short, it might indicate an extraction failure
    if len(text.strip()) < 10 and "Error extracting text" not in text:
        logger.warning(f"Extracted text is suspiciously short: '{text}'")
        
        # Try textract as a fallback if available
        if TEXTRACT_AVAILABLE and "Error extracting text" not in text:
            text = extract_text_using_textract(file_path)
    
    return text

def filter_relevant_text(text: str) -> str:
    """Filter the extracted text to keep only property-related information."""
    if not text or text.startswith("Error") or text.startswith("File not found") or text.startswith("Unsupported file type"):
        return text
    
    # Get data models description for context
    try:
        data_models_description = get_data_models_description()
    except Exception as e:
        logger.error(f"Error getting data models description: {str(e)}")
        logger.error(traceback.format_exc())
        # Provide a generic description if data models can't be loaded
        data_models_description = "Property management data including properties, units, tenants, leases, and related information."
    
    # Create the system prompt
    system_prompt = f"""You are an AI assistant that extracts relevant information from documents for a property management system.
Your task is to analyze the provided document text and extract ONLY the information that is relevant to property management.

The property management system uses the following data models:
{data_models_description}

IMPORTANT GUIDELINES:
1. Extract ALL text that might be relevant to property management.
2. Do not summarize or interpret the information - keep the original wording.
3. Remove irrelevant boilerplate text, legal jargon, or information not related to property management.
4. Preserve the original formatting of important information like dates, amounts, and contact details.
5. If the document doesn't contain any relevant information, return "No relevant property information found in document."

Your response should be ONLY the extracted relevant text, with no additional explanations or notes."""

    # Create the user prompt
    user_prompt = f"""Document text:

{text}

Extract the relevant property management information from this document text according to the guidelines."""

    # Call the GPT API
    gpt_client = GPTClient()
    result = gpt_client.query(user_prompt, system_prompt, temperature=0.1)
    
    if not result:
        logger.error("Failed to get a response from GPT")
        return "Error: Failed to filter relevant text using GPT"
    
    return result

def extract_relevant_text(file_path: str) -> str:
    """Extract relevant property-related text from a document.
    
    This is the main function that should be called by other modules.
    
    Args:
        file_path: Path to the document file
        
    Returns:
        Extracted relevant text as a string
    """
    try:
        # Extract raw text from the document
        raw_text = extract_text_from_document(file_path)
        
        # If text extraction failed, return the error
        if raw_text.startswith("Error") or raw_text.startswith("File not found") or raw_text.startswith("Unsupported file type"):
            return raw_text
        
        # Filter the text to keep only relevant information
        relevant_text = filter_relevant_text(raw_text)
        
        return relevant_text
        
    except Exception as e:
        logger.error(f"Error extracting relevant text: {str(e)}")
        logger.error(traceback.format_exc())
        return f"Error extracting relevant text: {str(e)}" 