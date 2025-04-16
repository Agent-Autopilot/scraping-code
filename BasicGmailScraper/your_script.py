from __future__ import print_function
import os.path
import base64
import re
import html2text
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.message import EmailMessage

# If modifying scopes, delete token.json
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def save_attachment(part_data, filename):
    """Save attachment data to a file"""
    if not os.path.isdir('attachments'):
        os.mkdir('attachments')
    
    filepath = os.path.join('attachments', filename)
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

def read_first_email():
    service = get_gmail_service()
    results = service.users().messages().list(userId='me', maxResults=1).execute()
    messages = results.get('messages', [])

    if not messages:
        print("No messages found.")
    else:
        msg = service.users().messages().get(userId='me', id=messages[0]['id'], format='full').execute()
        headers = msg['payload']['headers']
        subject = next(h['value'] for h in headers if h['name'] == 'Subject')
        sender = next(h['value'] for h in headers if h['name'] == 'From')

        print(f"📩 From: {sender}")
        print(f"📌 Subject: {subject}")

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
                    saved_path = save_attachment(attachment_data, filename)
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
                            saved_path = save_attachment(attachment_data, filename)
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

        print("📜 Body:\n")
        print(body)
        
        if attachments:
            print("\n📎 Attachments:")
            for idx, attachment in enumerate(attachments, 1):
                print(f"  {idx}. {os.path.basename(attachment)}")
        else:
            print("\nNo attachments found.")

if __name__ == '__main__':
    read_first_email()

