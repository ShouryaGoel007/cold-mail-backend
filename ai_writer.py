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
        "Write ONE email subject line under 10 words for this LinkedIn post: "
        + post_text[:300] +
        ". Only output the subject line."
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
