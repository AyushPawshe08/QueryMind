from langchain.tools import tool
import requests
from tavily import TavilyClient
import os
from dotenv import load_dotenv
import json

load_dotenv()
tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


@tool
def web_search(query : str) -> str:
    """Search the web and find the recent and reliable information on the topic. Return Titles, URLs and snippets."""

    results = tavily.search(query=query, max_results=5).get("results", [])

    out = []

    for r in results:
        out.append(
            f"Title: {r['title']}\nURL: {r['url']}\nSnippet: {r['content'] [:300]}\n"
        )

    return "\n----\n".join(out)

# response = web_search.invoke("What are the AI Trends in 2026")

# print(json.dumps(response, indent=2, ensure_ascii=False))

