"""Document Converter Module

This module provides functionality to convert various document formats (PDF, DOCX, etc.)
to plaintext and then extract the most important information based on the data models.

The main function is `convert_document_to_relevant_text` which takes a file path,
converts it to plaintext, and then uses AI to extract only the information relevant
to the data models.
"""

import os
import tempfile
import logging
from typing import Optional, Dict, Any, List
import traceback
import inspect
import dataclasses

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

# OpenAI for text extraction
import openai
from dotenv import load_dotenv

# Import data models
from data_models import (
    Address, ContactInfo, Document, Photo, Lease, 
    Tenant, Unit, Entity, Property
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Extracted text as a string
    """
    try:
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise

def extract_text_from_docx(file_path: str) -> str:
    """
    Extract text from a DOCX file.
    
    Args:
        file_path: Path to the DOCX file
        
    Returns:
        Extracted text as a string
    """
    try:
        doc = DocxDocument(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {str(e)}")
        raise

def extract_text_using_textract(file_path: str) -> str:
    """
    Extract text from a file using textract (fallback method).
    
    Args:
        file_path: Path to the file
        
    Returns:
        Extracted text as a string
    """
    if not TEXTRACT_AVAILABLE:
        raise ImportError("Textract is not available. Install it with 'pip install textract'.")
    
    try:
        text = textract.process(file_path).decode('utf-8')
        return text
    except Exception as e:
        logger.error(f"Error extracting text using textract: {str(e)}")
        raise

def extract_text_from_document(file_path: str) -> str:
    """
    Extract text from a document file based on its extension.
    
    Args:
        file_path: Path to the document file
        
    Returns:
        Extracted text as a string
    """
    _, file_extension = os.path.splitext(file_path.lower())
    
    try:
        if file_extension == '.pdf':
            return extract_text_from_pdf(file_path)
        elif file_extension in ['.docx', '.doc']:
            try:
                return extract_text_from_docx(file_path)
            except:
                # Fallback to textract for .doc files or if python-docx fails
                if TEXTRACT_AVAILABLE:
                    return extract_text_using_textract(file_path)
                else:
                    raise ValueError(f"Could not extract text from {file_path}. For .doc files, please install textract.")
        else:
            # Try using textract for other file types
            if TEXTRACT_AVAILABLE:
                return extract_text_using_textract(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}. Please install textract for additional format support.")
    except Exception as e:
        logger.error(f"Failed to extract text from {file_path}: {str(e)}")
        raise ValueError(f"Could not extract text from {file_path}: {str(e)}")

def chunk_text(text: str, max_chunk_size: int = 4000) -> List[str]:
    """
    Split text into chunks of maximum size.
    
    Args:
        text: The text to split
        max_chunk_size: Maximum size of each chunk in characters
        
    Returns:
        List of text chunks
    """
    # Split by paragraphs first
    paragraphs = text.split('\n')
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        # If adding this paragraph would exceed the max chunk size, start a new chunk
        if len(current_chunk) + len(paragraph) + 1 > max_chunk_size and current_chunk:
            chunks.append(current_chunk)
            current_chunk = paragraph + '\n'
        else:
            current_chunk += paragraph + '\n'
    
    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

def get_data_model_info() -> str:
    """
    Get information about the data models by inspecting the actual classes.
    
    Returns:
        A string containing information about the data models
    """
    data_models = [Address, ContactInfo, Document, Photo, Lease, Tenant, Unit, Entity, Property]
    model_info = []
    
    for model in data_models:
        # Get the class name
        class_name = model.__name__
        
        # Get the fields from the dataclass
        fields = []
        for field in dataclasses.fields(model):
            fields.append(field.name)
        
        # Add the model info to the list
        model_info.append(f"{class_name}: {', '.join(fields)}")
    
    return "\n".join(model_info)

def extract_relevant_information(text: str) -> str:
    """
    Use AI to extract only the information relevant to the data models.
    
    Args:
        text: The full plaintext extracted from the document
        
    Returns:
        A string containing only the relevant information
    """
    try:
        # Get the data model definitions from the actual classes
        data_model_info = get_data_model_info()
        
        # Split the text into chunks if it's too large
        chunks = chunk_text(text)
        logger.info(f"Split text into {len(chunks)} chunks")
        
        all_relevant_text = []
        
        # Process each chunk separately
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}")
            
            # Create a prompt for the AI
            prompt = f"""
            I have a document that has been converted to plaintext. I need to extract only the information 
            that is relevant to my data models. Please analyze the text and extract only the parts that 
            contain information that could be used to populate these data models.
            
            The system has the following data models with their fields:
            
            {data_model_info}
            
            Please focus ONLY on extracting information that directly relates to these specific fields.
            Do not include information that cannot be mapped to these fields.
            
            Please output the information in a clear, readable plaintext format (NOT JSON).
            Format it as key-value pairs, for example:
            
            Property Name: Example Property
            Address: 123 Main St, City, State, ZIP
            Tenant Name: John Doe
            Lease Start Date: 2023-01-01
            
            Please remove any irrelevant information, formatting, headers, footers, page numbers, 
            and other content that doesn't directly relate to these data models.
            
            This is chunk {i+1} of {len(chunks)} from the document.
            
            Here is the plaintext:
            
            {chunk}
            """
            
            # Call the OpenAI API
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",  # Using a model with larger context window
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts relevant information from documents. You only extract information that directly maps to the specified data model fields and output it in plaintext format."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            # Extract and add the relevant text from this chunk
            chunk_result = response.choices[0].message.content.strip()
            if chunk_result and not chunk_result.lower().startswith(("i don't see any relevant information", "there is no relevant information")):
                all_relevant_text.append(chunk_result)
        
        # Combine all the relevant text
        combined_text = "\n\n".join(all_relevant_text)
        
        # If we have multiple chunks, do a final pass to consolidate and remove duplicates
        if len(chunks) > 1 and combined_text:
            logger.info("Performing final consolidation pass")
            
            final_prompt = f"""
            I have extracted relevant information from different parts of a document. 
            Please consolidate this information, remove any duplicates, and organize it 
            according to the data models:
            
            {data_model_info}
            
            Please focus ONLY on information that directly relates to these specific fields.
            Do not include information that cannot be mapped to these fields.
            
            Please output the information in a clear, readable plaintext format (NOT JSON).
            Format it as key-value pairs, for example:
            
            Property Name: Example Property
            Address: 123 Main St, City, State, ZIP
            Tenant Name: John Doe
            Lease Start Date: 2023-01-01
            
            Here is the extracted information:
            
            {combined_text}
            """
            
            final_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that consolidates and organizes information according to specific data models. You only include information that directly maps to the specified data model fields and output it in plaintext format."},
                    {"role": "user", "content": final_prompt}
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            return final_response.choices[0].message.content.strip()
        
        return combined_text
    
    except Exception as e:
        logger.error(f"Error extracting relevant information: {str(e)}")
        logger.error(traceback.format_exc())
        raise ValueError(f"Failed to extract relevant information: {str(e)}")

def convert_document_to_relevant_text(file_path: str) -> str:
    """
    Convert a document to plaintext and extract only the information relevant to the data models.
    
    Args:
        file_path: Path to the document file
        
    Returns:
        A string containing only the relevant information from the document
    """
    try:
        # Step 1: Convert document to plaintext
        logger.info(f"Converting document to plaintext: {file_path}")
        plaintext = extract_text_from_document(file_path)
        
        # Step 2: Extract relevant information using AI
        logger.info("Extracting relevant information using AI")
        relevant_text = extract_relevant_information(plaintext)
        
        return relevant_text
    
    except Exception as e:
        logger.error(f"Error in convert_document_to_relevant_text: {str(e)}")
        logger.error(traceback.format_exc())
        raise ValueError(f"Failed to process document {file_path}: {str(e)}")

if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python document_converter.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    try:
        result = convert_document_to_relevant_text(file_path)
        print("\nExtracted Relevant Information:")
        print("-" * 50)
        print(result)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1) 