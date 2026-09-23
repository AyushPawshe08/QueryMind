import re
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from agent import build_search_agent, build_reader_agent, writer_chain, critic_chain


# ── Shared State ───────────────────────────────────────────────────────────────
class AgentState(TypedDict):
    topic: str
    search_results: str
    scraped_content: str
    sources: list[str]
    report: str
    critique: str
    score: int
    iterations: int


def _extract_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
            elif hasattr(item, "text"):
                parts.append(getattr(item, "text"))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content) if content is not None else ""


# ── Nodes ──────────────────────────────────────────────────────────────────────
def search_node(state: AgentState) -> dict:
    agent = build_search_agent()
    result = agent.invoke({
        "messages": [{"role": "user", "content": f"Search for information about: {state['topic']}"}]
    })

    # Collect all messages and raw tool outputs to extract authentic URLs
    all_chunks = []
    for msg in result.get("messages", []):
        all_chunks.append(_extract_text(getattr(msg, "content", "")))

    combined_text = "\n".join(all_chunks)
    found_urls = re.findall(r'https?://[^\s)\]"\'>]+', combined_text)

    # Clean and deduplicate URLs
    clean_urls = []
    seen = set()
    for url in found_urls:
        u = url.rstrip(".,;:")
        if u not in seen:
            seen.add(u)
            clean_urls.append(u)

    existing_sources = state.get("sources") or []
    all_sources = list(dict.fromkeys(existing_sources + clean_urls))

    return {
        "search_results": _extract_text(result["messages"][-1].content),
        "sources": all_sources,
    }


def read_node(state: AgentState) -> dict:
    agent = build_reader_agent()
    result = agent.invoke({
        "messages": [{
            "role": "user",
            "content": (
                f"Based on these search results, scrape the most relevant URLs "
                f"and extract detailed information:\n\n{state['search_results']}"
            ),
        }]
    })
    return {"scraped_content": _extract_text(result["messages"][-1].content)}


def write_node(state: AgentState) -> dict:
    research = f"{state['search_results']}\n\n{state['scraped_content']}"
    sources = state.get("sources", [])
    if sources:
        sources_formatted = "\n".join(f"- {url}" for url in sources)
    else:
        sources_formatted = "None identified."

    report = writer_chain.invoke({
        "topic": state["topic"],
        "research": research,
        "sources": sources_formatted,
    })
    return {"report": _extract_text(report)}




def critic_node(state: AgentState) -> dict:
    critique = critic_chain.invoke({"report": state["report"]})

    # Parse the numeric score from "Score: X/10"
    score = 6  # conservative default so we retry if parsing fails
    match = re.search(r"Score:\s*(\d+)", critique)
    if match:
        score = int(match.group(1))

    return {
        "critique": critique,
        "score": score,
        "iterations": state.get("iterations", 0) + 1,
    }


# ── Conditional Edge ───────────────────────────────────────────────────────────
def should_rewrite(state: AgentState) -> str:
    """Loop back to search if score is low; stop after 3 iterations max."""
    if state["score"] >= 7 or state.get("iterations", 0) >= 3:
        return "end"
    return "search"


# ── Graph Assembly ─────────────────────────────────────────────────────────────
builder = StateGraph(AgentState)

builder.add_node("search", search_node)
builder.add_node("read",   read_node)
builder.add_node("write",  write_node)
builder.add_node("critic", critic_node)

builder.add_edge(START,    "search")
builder.add_edge("search", "read")
builder.add_edge("read",   "write")
builder.add_edge("write",  "critic")

builder.add_conditional_edges(
    "critic",
    should_rewrite,
    {"end": END, "search": "search"},
)

research_graph = builder.compile()
