import os
from dotenv import load_dotenv
from langchain.tools import tool
import requests
from bs4 import BeautifulSoup

load_dotenv()


def _scrape_with_firecrawl(url: str, api_key: str) -> dict | None:
    """Attempt scraping via Firecrawl API to bypass Cloudflare and render JavaScript into Markdown."""
    try:
        from firecrawl import FirecrawlApp

        app = FirecrawlApp(api_key=api_key)
        res = app.scrape_url(url, formats=["markdown"])

        markdown_content = ""
        if isinstance(res, dict):
            markdown_content = res.get("markdown") or res.get("data", {}).get("markdown") or ""
        elif hasattr(res, "markdown"):
            markdown_content = getattr(res, "markdown") or ""
        elif hasattr(res, "data") and hasattr(res.data, "markdown"):
            markdown_content = getattr(res.data, "markdown") or ""

        if markdown_content and len(markdown_content.strip()) > 50:
            return {
                "url": url,
                "text": markdown_content[:35000],
                "success": True,
                "engine": "firecrawl",
            }
    except Exception as e:
        print(f"[Scraper Notice] Firecrawl error for {url}: {e}. Falling back to standard engine.")
    return None


def scrape_page(url: str) -> dict:
    """
    Scrapes full readable web content:
    1. Uses Firecrawl API if FIRECRAWL_API_KEY is available (renders JS, handles Cloudflare).
    2. Gracefully falls back to BeautifulSoup + Requests.
    """
    firecrawl_key = os.getenv("FIRECRAWL_API_KEY", "").strip()
    if firecrawl_key:
        fc_res = _scrape_with_firecrawl(url, firecrawl_key)
        if fc_res and fc_res.get("success"):
            return fc_res

    # Fallback Engine: Requests + BeautifulSoup
    try:
        resp = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                )
            },
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "aside"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        return {
            "url": url,
            "text": text[:35000],
            "success": True,
            "engine": "requests",
        }
    except Exception as e:
        return {
            "url": url,
            "text": f"Could not scrape URL: {str(e)}",
            "success": False,
            "engine": "error",
        }


@tool
def scrape_url(url: str) -> str:
    """Scrape and return deep text content from a given URL for comprehensive reading."""
    res = scrape_page(url)
    return res["text"]


if __name__ == "__main__":
    test = scrape_page("https://www.python.org/about/")
    print(f"Scraped {len(test['text'])} chars. Engine: {test['engine']}. Success: {test['success']}")