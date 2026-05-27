import requests
import json
import re

def extract_post_text(data):
    for item in data.get("included", []):
        # Method 1 - commentary field
        if "commentary" in item:
            commentary = item["commentary"]
            if isinstance(commentary, dict):
                text = commentary.get("text", {})
                if isinstance(text, dict):
                    t = text.get("text", "")
                    if t and len(t) > 20:
                        return t
                elif isinstance(text, str) and len(text) > 20:
                    return text
            elif isinstance(commentary, str) and len(commentary) > 20:
                return commentary

        # Method 2 - text field directly
        if "text" in item and isinstance(item["text"], dict):
            t = item["text"].get("text", "")
            if t and len(t) > 50:
                return t

        # Method 3 - nested dicts
        for key, val in item.items():
            if isinstance(val, dict):
                if "text" in val and isinstance(val["text"], str) and len(val["text"]) > 50:
                    return val["text"]
                if "commentary" in val:
                    c = val["commentary"]
                    if isinstance(c, dict) and "text" in c:
                        t = c["text"]
                        if isinstance(t, dict):
                            return t.get("text", "")
                        return t
    return None


def scrape_linkedin_post(url, cookies):
    post_id = url.split("activity:")[-1].split("/")[0]
    jsessionid = cookies.get("JSESSIONID", "")
    csrf = jsessionid.replace('"', '').replace('ajax:', '')

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/vnd.linkedin.normalized+json+2.1",
        "x-li-lang": "en_US",
        "x-restli-protocol-version": "2.0.0",
        "csrf-token": f"ajax:{csrf}",
        "Cookie": f"li_at={cookies.get('li_at', '')}; JSESSIONID={jsessionid}"
    }

    api_url = f"https://www.linkedin.com/voyager/api/feed/updates/urn:li:activity:{post_id}?moduleKey=feed-full-update&count=1"
    r = requests.get(api_url, headers=headers)
    data = r.json()

    post_text = extract_post_text(data)

    if not post_text:
        post_text = "Could not extract post text. Please check the URL."

    emails_found = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", post_text)

    print(f"✅ Scraped post text ({len(post_text)} chars)")
    print(f"📧 Emails found: {emails_found}")

    return {
        "full_text": post_text[:3000],
        "email_in_post": emails_found[0] if emails_found else None
    }
