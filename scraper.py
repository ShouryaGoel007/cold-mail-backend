
import requests
import re
from bs4 import BeautifulSoup

def scrape_linkedin_post(url, cookies):
    """
    Scrapes LinkedIn post using saved cookies.
    No browser needed — works on server.
    cookies = dict of your LinkedIn cookies
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    session = requests.Session()
    session.cookies.update(cookies)

    response = session.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    full_text = soup.get_text(separator=" ", strip=True)

    emails_found = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", full_text)

    return {
        "full_text": full_text[:3000],
        "email_in_post": emails_found[0] if emails_found else None
    }
