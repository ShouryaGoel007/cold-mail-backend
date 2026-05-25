
from flask import Flask, request, jsonify
from flask_cors import CORS
from scraper import scrape_linkedin_post
from ai_writer import generate_email_and_subject
from mailer import send_email
import os
import json

app = Flask(__name__)
CORS(app)

# Load config from environment variables (set these on Railway)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
HUNTER_API_KEY = os.environ.get("HUNTER_API_KEY")
LINKEDIN_COOKIES = json.loads(os.environ.get("LINKEDIN_COOKIES", "{}"))

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Cold Mail Bot is running!"})

@app.route("/generate", methods=["POST"])
def generate():
    """
    Takes LinkedIn URL + user profile
    Returns AI-written email preview
    """
    try:
        data = request.json
        linkedin_url = data.get("linkedin_url")
        user_profile = data.get("user_profile")
        hr_name = data.get("hr_name", "")

        # Scrape LinkedIn post
        post_data = scrape_linkedin_post(linkedin_url, LINKEDIN_COOKIES)

        # Generate email with AI
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
            "post_preview": post_data["full_text"][:200]
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/send", methods=["POST"])
def send():
    """
    Takes email content + resume file
    Actually sends the email
    """
    try:
        hr_email = request.form.get("hr_email")
        subject = request.form.get("subject")
        body = request.form.get("body")
        resume = request.files.get("resume")

        if not resume:
            return jsonify({"success": False, "error": "No resume uploaded"}), 400

        resume_bytes = resume.read()
        resume_filename = resume.filename

        send_email(hr_email, subject, body, resume_bytes, resume_filename)

        return jsonify({"success": True, "message": f"Email sent to {hr_email}!"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
