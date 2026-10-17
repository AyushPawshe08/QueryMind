try:
    from backend.tools.web_search import web_search
    from backend.tools.scrape import scrape_url, scrape_page
    from backend.tools.rag import extract_top_chunks
except ImportError:
    from .web_search import web_search
    from .scrape import scrape_url, scrape_page
    from .rag import extract_top_chunks

__all__ = ["web_search", "scrape_url", "scrape_page", "extract_top_chunks"]
