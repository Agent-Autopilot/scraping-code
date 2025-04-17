#!/usr/bin/env python3
"""
Email Processor Script

This script:
1. Gets the most recent email's body and attachments
2. Converts attachments to text
3. Combines all into a single string
4. Processes the combined text with the property processor
"""

import os
import base64
import re
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import html2text

# Use absolute import path when running as a script
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.property_processor import PropertyProcessor, process_property_document

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# If modifying scopes, delete token.json
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# Paths to credentials and token files in GmailCredentials directory
CREDENTIALS_PATH = os.path.join(SCRIPT_DIR, 'GmailCredentials', 'credentials.json')
TOKEN_PATH = os.path.join(SCRIPT_DIR, 'GmailCredentials', 'token.json')

# Base directory for email-specific folders
EMAILS_BASE_DIR = os.path.join(SCRIPT_DIR, 'Emails')

def sanitize_filename(text):
    """Convert text to a valid filename by removing invalid characters"""
    # Replace invalid filename characters with underscores
    return re.sub(r'[\\/*?:"<>|]', "_", text)

def create_email_directory(sender, subject, date_time):
    """Create a directory for this specific email based on metadata"""
    # Sanitize sender and subject for use in directory name
    safe_sender = sanitize_filename(sender.split('<')[0].strip())[:30]  # Limit length
    safe_subject = sanitize_filename(subject)[:50]  # Limit length
    
    # Format date_time for directory name
    date_str = date_time.strftime("%Y%m%d_%H%M%S")
    
    # Create directory name
    dir_name = f"{date_str}_{safe_sender}_{safe_subject}"
    
    # Create full path
    full_path = os.path.join(EMAILS_BASE_DIR, dir_name)
    
    # Create directory if it doesn't exist
    if not os.path.exists(full_path):
        os.makedirs(full_path)
    
    return full_path

def get_gmail_service():
    """Authenticate and get Gmail API service"""
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def save_attachment(part_data, filename, email_dir):
    """Save attachment data to a file in the email-specific directory"""
    # Create attachments subdirectory within the email directory
    attachments_dir = os.path.join(email_dir, 'attachments')
    if not os.path.exists(attachments_dir):
        os.makedirs(attachments_dir)
    
    filepath = os.path.join(attachments_dir, filename)
    with open(filepath, 'wb') as f:
        f.write(base64.urlsafe_b64decode(part_data))
    
    print(f"✅ Attachment saved: {filepath}")
    return filepath

def extract_text(content, is_html=False):
    """Extract readable text content from email body"""
    if is_html:
        # Convert HTML to plain text
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = True
        return h.handle(content).strip()
    return content.strip()

def get_most_recent_email():
    """Get the most recent email's body and attachments"""
    service = get_gmail_service()
    results = service.users().messages().list(userId='me', maxResults=1).execute()
    messages = results.get('messages', [])

    if not messages:
        print("No messages found.")
        return None, [], None, None, None
    
    msg = service.users().messages().get(userId='me', id=messages[0]['id'], format='full').execute()
    headers = msg['payload']['headers']
    subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), "No Subject")
    sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), "Unknown Sender")
    
    # Get date from email headers or from the message internal date
    date_str = next((h['value'] for h in headers if h['name'].lower() == 'date'), None)
    if date_str:
        try:
            # Try to parse the email date header
            # Email date format can be complex, this is a simplified attempt
            date_obj = datetime.datetime.strptime(date_str[:25], "%a, %d %b %Y %H:%M:%S")
        except:
            # If parsing fails, use the internal date
            date_obj = datetime.datetime.fromtimestamp(int(msg['internalDate'])/1000)
    else:
        # Use the internal date if no date header
        date_obj = datetime.datetime.fromtimestamp(int(msg['internalDate'])/1000)

    print(f"📩 From: {sender}")
    print(f"📌 Subject: {subject}")
    print(f"📅 Date: {date_obj}")

    # Create directory for this email
    email_dir = create_email_directory(sender, subject, date_obj)
    print(f"📁 Email directory created: {email_dir}")

    # Process body and attachments
    parts = msg['payload'].get('parts', [])
    plain_text_body = ""
    html_body = ""
    attachments = []
    
    if parts:
        # Process all parts
        for part in parts:
            mime_type = part.get('mimeType', '')
            
            if mime_type == 'text/plain' and 'data' in part['body']:
                # Plain text body
                body_data = part['body']['data']
                plain_text_body = base64.urlsafe_b64decode(body_data).decode()
            elif mime_type == 'text/html' and 'data' in part['body']:
                # HTML body (backup if no plain text is found)
                body_data = part['body']['data']
                html_body = base64.urlsafe_b64decode(body_data).decode()
            elif 'filename' in part and part['filename']:
                # This is an attachment
                if 'data' in part['body']:
                    attachment_data = part['body']['data']
                else:
                    # If attachment data is in a separate part
                    attachment_id = part['body']['attachmentId']
                    attachment = service.users().messages().attachments().get(
                        userId='me', messageId=messages[0]['id'], id=attachment_id
                    ).execute()
                    attachment_data = attachment['data']
                
                filename = part['filename']
                saved_path = save_attachment(attachment_data, filename, email_dir)
                attachments.append(saved_path)
            elif 'parts' in part:
                # Handle nested parts (like multipart/alternative)
                for subpart in part['parts']:
                    sub_mime_type = subpart.get('mimeType', '')
                    
                    if sub_mime_type == 'text/plain' and 'data' in subpart['body']:
                        body_data = subpart['body']['data']
                        plain_text_body = base64.urlsafe_b64decode(body_data).decode()
                    elif sub_mime_type == 'text/html' and 'data' in subpart['body']:
                        body_data = subpart['body']['data']
                        html_body = base64.urlsafe_b64decode(body_data).decode()
                    elif 'filename' in subpart and subpart['filename']:
                        # This is an attachment in a nested part
                        if 'data' in subpart['body']:
                            attachment_data = subpart['body']['data']
                        else:
                            attachment_id = subpart['body']['attachmentId']
                            attachment = service.users().messages().attachments().get(
                                userId='me', messageId=messages[0]['id'], id=attachment_id
                            ).execute()
                            attachment_data = attachment['data']
                        
                        filename = subpart['filename']
                        saved_path = save_attachment(attachment_data, filename, email_dir)
                        attachments.append(saved_path)
    else:
        # Handle messages with no parts structure
        mime_type = msg['payload'].get('mimeType', '')
        body_data = msg['payload']['body']['data']
        decoded_data = base64.urlsafe_b64decode(body_data).decode()
        
        if mime_type == 'text/plain':
            plain_text_body = decoded_data
        elif mime_type == 'text/html':
            html_body = decoded_data
    
    # Determine the body to display (prefer plain text)
    if plain_text_body:
        body = extract_text(plain_text_body)
    elif html_body:
        body = extract_text(html_body, is_html=True)
    else:
        body = "No readable content found in this email."

    # Save the email metadata and body to a file in the email directory
    email_info_path = os.path.join(email_dir, "email_metadata_and_content.txt")
    with open(email_info_path, "w") as f:
        f.write(f"FROM: {sender}\n")
        f.write(f"SUBJECT: {subject}\n")
        f.write(f"DATE: {date_obj}\n")
        f.write("\n--- EMAIL CONTENT ---\n\n")
        f.write(body)
    
    return body, attachments, email_dir, sender, subject

def main():
    """Main function to process email"""
    print("Processing most recent email...")
    
    # Step 1: Get the most recent email's body and attachments
    body, attachments, email_dir, sender, subject = get_most_recent_email()
    if not body and not attachments:
        print("No email data found.")
        return

    # Initialize property processor
    processor = PropertyProcessor()
    
    # Step 2: Convert attachments to text
    attachment_texts = []
    for i, attachment_path in enumerate(attachments, 1):
        print(f"Processing attachment {i}: {os.path.basename(attachment_path)}")
        # Only process document files that can be converted to text
        if attachment_path.lower().endswith(('.pdf', '.docx', '.doc', '.txt', '.rtf')):
            text = processor.extract_text_from_document(attachment_path)
            attachment_texts.append((os.path.basename(attachment_path), text))
            
            # Save the extracted text to a file
            text_filename = f"{os.path.splitext(os.path.basename(attachment_path))[0]}_text.txt"
            text_path = os.path.join(email_dir, text_filename)
            with open(text_path, "w") as f:
                f.write(text)
    
    # Step 3: Combine all content into a single string
    combined_text = f"body: {body}\n\n"
    
    for i, (filename, text) in enumerate(attachment_texts, 1):
        combined_text += f"attachment {i} ({filename}): {text}\n\n"
    
    # Step 4: Feed the combined text to the property processor
    print("Processing combined text with property processor...")
    
    # Save the combined text for processing
    combined_text_path = os.path.join(email_dir, "combined_email_content.txt")
    with open(combined_text_path, "w") as f:
        f.write(combined_text)
    
    # Create output directory inside email directory
    output_dir = os.path.join(email_dir, "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Process the combined text
    result = process_property_document(
        document_path=combined_text_path,
        output_dir=output_dir,
        save_intermediates=True
    )
    
    print(f"Processing complete. Results saved to '{output_dir}' directory.")
    
    return result

if __name__ == "__main__":
    main() 