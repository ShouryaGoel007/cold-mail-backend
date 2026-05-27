import os
import json
import base64
import pickle
import re
from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from ai_writer import generate_email_and_subject
from mailer import send_email_with_token
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import requests as http_requests
from bs4 import BeautifulSoup

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

app = Flask(__name__)
CORS(app, supports_credentials=True, origins="*")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
CREDENTIALS_INFO = json.loads(os.environ.get("CREDENTIALS_JSON", "{}"))
REDIRECT_URI = os.environ.get("REDIRECT_URI", "http://localhost:5000/oauth2callback")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "shourya123")

CLIENT_ID = CREDENTIALS_INFO.get("web", {}).get("client_id", "")
CLIENT_SECRET = CREDENTIALS_INFO.get("web", {}).get("client_secret", "")
TOKEN_URI = "https://oauth2.googleapis.com/token"
AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
SCOPES = "https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.readonly"

# LinkedIn cookies stored in memory
linkedin_cookies = {}
raw_cookies = os.environ.get("LINKEDIN_COOKIES", "{}")
try:
    linkedin_cookies = json.loads(raw_cookies)
except:
    linkedin_cookies = {}


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Cold Mail Bot is running!"})


@app.route("/update-cookies", methods=["POST"])
def update_cookies():
    # Secret admin route to update LinkedIn cookies without touching Render
    try:
        data = request.json
        password = data.get("password", "")
        if password != ADMIN_PASSWORD:
            return jsonify({"success": False, "error": "Wrong password"}), 403

        new_li_at = data.get("li_at", "")
        new_jsessionid = data.get("jsessionid", "")

        if not new_li_at:
            return jsonify({"success": False, "error": "li_at is required"}), 400

        global linkedin_cookies
        linkedin_cookies = {
            "li_at": new_li_at,
            "JSESSIONID": new_jsessionid
        }

        # Test if cookies work
        test_result = test_cookies(linkedin_cookies)
        if test_result:
            return jsonify({"success": True, "message": "Cookies updated and working!"})
        else:
            return jsonify({"success": True, "message": "Cookies updated but could not verify. Try scraping a post to check."})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def test_cookies(cookies):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        session = http_requests.Session()
        session.cookies.update(cookies)
        r = session.get("https://www.linkedin.com/feed/", headers=headers, timeout=10)
        return "feed" in r.url or r.status_code == 200
    except:
        return False


def scrape_linkedin_post(url, cookies):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    session = http_requests.Session()
    session.cookies.update(cookies)
    response = session.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    full_text = soup.get_text(separator=" ", strip=True)
    emails_found = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", full_text)
    return {
        "full_text": full_text[:3000],
        "email_in_post": emails_found[0] if emails_found else None
    }


@app.route("/auth/login", methods=["GET"])
def auth_login():
    from urllib.parse import urlencode
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "offline",
        "prompt": "consent"
    }
    auth_url = AUTH_URI + "?" + urlencode(params)
    return jsonify({"auth_url": auth_url})


@app.route("/oauth2callback", methods=["GET"])
def oauth2callback():
    try:
        code = request.args.get("code")
        if not code:
            return redirect(f"{FRONTEND_URL}?error=no_code_received")
        token_response = http_requests.post(TOKEN_URI, data={
            "code": code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code"
        })
        token_data = token_response.json()
        if "error" in token_data:
            return redirect(f"{FRONTEND_URL}?error={token_data['error']}")
        creds = Credentials(
            token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            token_uri=TOKEN_URI,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            scopes=SCOPES.split()
        )
        token_b64 = base64.b64encode(pickle.dumps(creds)).decode("utf-8")
        service = build("gmail", "v1", credentials=creds)
        profile = service.users().getProfile(userId="me").execute()
        user_email = profile["emailAddress"]
        return redirect(f"{FRONTEND_URL}?token={token_b64}&email={user_email}")
    except Exception as e:
        print("OAuth error:", str(e))
        return redirect(f"{FRONTEND_URL}?error={str(e)}")


@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.json
        linkedin_url = data.get("linkedin_url")
        user_profile = data.get("user_profile")
        hr_name = data.get("hr_name", "")

        post_data = scrape_linkedin_post(linkedin_url, linkedin_cookies)

        result = generate_email_and_subject(
            post_text=post_data["full_text"],
            hr_name=hr_name,
            user_profile=user_profile,
            groq_api_key=GROQ_API_KEY
        )
        return jsonify({
            "success": True,
            "email_body": result["body"],
            "subject": result["subject"],
            "hr_email": post_data["email_in_post"],
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/send", methods=["POST"])
def send():
    try:
        hr_email = request.form.get("hr_email")
        subject = request.form.get("subject")
        body = request.form.get("body")
        resume = request.files.get("resume")
        token_b64 = request.form.get("token")
        if not resume:
            return jsonify({"success": False, "error": "No resume uploaded"}), 400
        if not token_b64:
            return jsonify({"success": False, "error": "Please connect Gmail first"}), 401
        resume_bytes = resume.read()
        resume_filename = resume.filename
        creds = pickle.loads(base64.b64decode(token_b64))
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        send_email_with_token(hr_email, subject, body, resume_bytes, resume_filename, creds)
        return jsonify({"success": True, "message": f"Email sent to {hr_email}!"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
