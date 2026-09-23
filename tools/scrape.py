from dotenv import load_dotenv
from langchain.tools import tool
import requests
from bs4 import BeautifulSoup

load_dotenv()

@tool
def scrape_url(url: str) -> str:
    """Scrape and return clean text content from a given URL for deeper reading."""
    try:
        resp = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        return text[:3000]
    except Exception as e:
        return f"Could not scrape URL: {str(e)}"


if __name__ == "__main__":
    print(scrape_url.invoke("https://www.python.org/about/"))