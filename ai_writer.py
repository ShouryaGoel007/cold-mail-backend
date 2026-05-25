
from groq import Groq
import os

def generate_email_and_subject(post_text, hr_name, user_profile, groq_api_key, email_examples=""):
    client = Groq(api_key=groq_api_key)

    email_prompt = f"""
    You are helping someone write a cold email to an HR professional.

    {"Study these example emails and copy their exact tone and style:" if email_examples else ""}
    {email_examples if email_examples else ""}

    The HR posted this on LinkedIn:
    ---
    {post_text[:2000]}
    ---

    HR name: {hr_name if hr_name else "HR Manager"}

    About the sender:
    {user_profile}

    Write a short cold email (max 120 words).
    - Reference something specific from their post
    - Sound human, not like a bot
    - No "I hope this email finds you well"
    - End with one simple call to action
    - Attach mention of resume

    Only output the email body.
    """

    email_response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": email_prompt}],
        max_tokens=400
    )

    subject_response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": f"Write ONE email subject line under 10 words for this LinkedIn post: {post_text[:300]}. Only output the subject line."}],
        max_tokens=50
    )

    return {
        "body": email_response.choices[0].message.content,
        "subject": subject_response.choices[0].message.content.strip()
    }
