import os
import base64
import pickle
import json
import tempfile
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def get_gmail_service():
    creds = None

    # Load token from environment variable
    token_b64 = os.environ.get("TOKEN_PICKLE", "")
    if token_b64:
        token_bytes = base64.b64decode(token_b64)
        creds = pickle.loads(token_bytes)

    # Refresh if expired
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

        # Save refreshed token back — update env on render manually if needed
        refreshed = base64.b64encode(pickle.dumps(creds)).decode("utf-8")
        print("TOKEN REFRESHED — update TOKEN_PICKLE env var with this:")
        print(refreshed)

    if not creds or not creds.valid:
        raise Exception("Gmail token is invalid or missing. Please re-authenticate locally and update TOKEN_PICKLE.")

    return build("gmail", "v1", credentials=creds)


def send_email(to_email, subject, body, resume_bytes, resume_filename):
    service = get_gmail_service()

    msg = MIMEMultipart()
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    attachment = MIMEBase("application", "octet-stream")
    attachment.set_payload(resume_bytes)
    encoders.encode_base64(attachment)
    attachment.add_header("Content-Disposition", f'attachment; filename="{resume_filename}"')
    msg.attach(attachment)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()
    return True
