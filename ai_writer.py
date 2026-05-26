from groq import Groq

def generate_email_and_subject(post_text, hr_name, user_profile, groq_api_key):
    client = Groq(api_key=groq_api_key)

    email_prompt = (
        "You are helping someone write a cold email to an HR professional.\n\n"
        "The HR posted this on LinkedIn:\n---\n"
        + post_text[:2000] +
        "\n---\n\n"
        "HR name: " + (hr_name if hr_name else "HR Manager") + "\n\n"
        "About the sender:\n"
        + user_profile +
        "\n\nWrite a short cold email (max 120 words).\n"
        "- Reference something specific from their post\n"
        "- Sound human, not like a bot\n"
        "- No I hope this email finds you well\n"
        "- End with one simple call to action\n"
        "- Mention resume is attached\n\n"
        "Only output the email body. Nothing else."
    )

    subject_prompt = (
        "You are writing an email subject line for a cold job application email.\n\n"
        "Based on this LinkedIn post by an HR:\n"
        + post_text[:500] +
        "\n\nAbout the applicant:\n"
        + user_profile +
        "\n\nWrite ONE subject line following these rules:\n"
        "- Must mention the specific role or company name from the post\n"
        "- Keep it under 8 words\n"
        "- Be direct and professional\n"
        "- Format like one of these examples:\n"
        "  * Application for Data Analyst Role at Blinkit\n"
        "  * IIT BHU Student Applying for Product Intern Role\n"
        "  * Interested in the Growth Manager Position at Rapido\n"
        "  * Final Year IIT BHU - Applying for Operations Intern\n"
        "- Do NOT use vague words like Opportunity, Excited, Passionate\n"
        "- Do NOT use punctuation like ! or ?\n"
        "- Only output the subject line, nothing else."
    )

    email_res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": email_prompt}],
        max_tokens=400
    )
    subject_res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": subject_prompt}],
        max_tokens=50
    )
    return {
        "body": email_res.choices[0].message.content,
        "subject": subject_res.choices[0].message.content.strip()
    }
