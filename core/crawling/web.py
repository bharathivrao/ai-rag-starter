
import requests
from bs4 import BeautifulSoup
from typing import Tuple

def fetch_url_text(url: str) -> Tuple[str, str]:
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        html = r.text
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        title = (soup.title.string or "").strip() if soup.title else ""
        elements = soup.find_all(["p","li","article","section","div","h1","h2","h3"])
        text = " ".join(s.get_text(separator=" ", strip=True) for s in elements)
        return text, title
    except Exception:
        return "", ""
