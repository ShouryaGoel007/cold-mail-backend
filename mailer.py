import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from googleapiclient.discovery import build

def send_email_with_token(to_email, subject, body, resume_bytes, resume_filename, creds):
    service = build("gmail", "v1", credentials=creds)
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
