import base64
import email
import imaplib
import os
import pickle
from datetime import datetime, timedelta
from email.header import decode_header

import markdown
from dotenv import load_dotenv
from fastapi import FastAPI

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

app = FastAPI()

connection = imaplib.IMAP4_SSL(os.environ['IMAP_SERVER'])  # this is done to make SSL connection with gmail
connection.login(os.environ['EMAIL'], os.environ['PASSWORD'])  # login to the gmail account
connection.select('Inbox')  # this is to check for emails under this label


@app.get("/list-strathmore-communications")
def list_strathmore_communications():
    """
    List all emails with the title 'Strathmore Communications' from the past month.

    Returns:
        list: A list of email data for matching emails.
    """
    # Calculate the date one month ago from the current date
    five_days_ago = (datetime.now() - timedelta(days=5)).date().strftime('%d-%b-%Y')

    search_criteria = f'FROM "Strathmore Communications" SINCE {five_days_ago}'
    result, email_data = connection.search(None, search_criteria)
    email_ids = email_data[0].split()
    # Sort the email IDs in reverse order to get the most recent first
    email_ids = email_ids[::-1]
    emails = []

    for email_id in email_ids:
        # Fetch the email data
        email_data = connection.fetch(email_id, "(RFC822)")[1][0][1]
        email_message = email.message_from_bytes(email_data)

        # Extract subject
        subject = email_message.get("Subject")

        # Extract body and convert to Markdown
        # Initialize body as an empty string
        body = ""
        for part in email_message.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode('utf-8')
                body = markdown.markdown(body)

        # Extract attachments (including non-text attachments as Base64)
        attachments = []
        for part in email_message.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition'):
                attachment = {
                    "filename": part.get_filename(),
                    "content": base64.b64encode(part.get_payload(decode=True)).decode('utf-8')
                }
                attachments.append(attachment)

        emails.append({
            "Subject": subject,
            "Body": body,
            "Attachments": attachments
        })
    return emails


# Dictionary to store image file names and their associated email subjects
subject_image_mapping = {}

# Define the filename for the mapping file
mapping_file = 'subject_image_mapping.pkl'


# Function to save the mapping to a .pkl file
def save_mapping():
    with open('subject_image_mapping.pkl', 'wb') as file:
        pickle.dump(subject_image_mapping, file)


# Function to load the mapping from a .pkl file
def load_mapping():
    try:
        with open('subject_image_mapping.pkl', 'rb') as file:
            return pickle.load(file)
    except FileNotFoundError:
        return {}  # Return an empty dictionary if the file doesn't exist


# Create a dictionary for the reversed mapping
reversed_mapping = {}


# Download and process emails as you described
def download_images(email_id, connection, download_dir):
    email_data = connection.fetch(email_id, "(RFC822)")[1][0][1]
    email_message = email.message_from_bytes(email_data)

    # Extract subject
    subject, _ = decode_header(email_message.get("Subject"))[0]

    for part in email_message.walk():
        if part.get('Content-Disposition'):
            if part.get_content_maintype() == 'image':
                file_name, charset = decode_header(part.get_filename())[0]
                if charset:
                    file_name = file_name.decode(charset)
                if file_name:
                    file_path = os.path.join(download_dir, file_name)
                    if not os.path.isfile(file_path):
                        with open(file_path, 'wb') as fp:
                            fp.write(part.get_payload(decode=True))
                        print(f'Downloaded "{file_name}" from email titled "{subject}".')
                        # Store the mapping of image file name and email subject
                        subject_image_mapping[file_name] = subject
                        # Store the reversed mapping
                        reversed_mapping[subject] = file_name
                        # Save the mapping after downloading each image
                        save_mapping()


# Save the final mapping (both original and reversed) at the end of your script
save_mapping()


@app.get("/download-strathmore-communications-emails")
def download_strathmore_communications_emails():
    """
    Download all the emails with the title 'Strathmore Communications' from the past month.

    Returns:
        str: A message indicating the download is completed.
    """
    # Calculate the date one month ago from the current date
    five_days_ago = (datetime.now() - timedelta(days=5)).date().strftime('%d-%b-%Y')

    search_criteria = f'FROM "Strathmore Communications" SINCE {five_days_ago}'
    result, email_data = connection.search(None, search_criteria)
    email_ids = email_data[0].split()
    # Sort the email IDs in reverse order to get the most recent first
    email_ids = email_ids[::-1]

    download_dir = f'C:/Users/Jerome/PycharmProjects/emailExtractor/images/'

    for email_id in email_ids:
        download_images(email_id, connection, download_dir)

    return {"message": "Download completed."}
