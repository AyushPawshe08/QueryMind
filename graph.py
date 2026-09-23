import re
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from agent import (
    build_search_agent,
    build_reader_agent,
    writer_chain,
    critic_chain,
    generate_sub_queries,
    generate_gap_queries,
    extract_chart_data,
)


# ── Shared State ───────────────────────────────────────────────────────────────
class AgentState(TypedDict):
    topic: str
    sub_queries: list[str]
    search_results: str
    scraped_content: str
    sources: list[str]
    report: str
    critique: str
    score: int
    iterations: int
    chart_data: dict


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
def planner_node(state: AgentState) -> dict:
    """Generate orthogonal sub-queries initially, or targeted gap queries on retries."""
    topic = state["topic"]
    critique = state.get("critique", "")
    iterations = state.get("iterations", 0)

    if iterations > 0 and critique:
        sub_queries = generate_gap_queries(topic, critique)
    else:
        sub_queries = generate_sub_queries(topic)

    return {"sub_queries": sub_queries}


def search_node(state: AgentState) -> dict:
    """Search the web for all sub-queries in parallel and aggregate findings and sources."""
    from concurrent.futures import ThreadPoolExecutor

    queries = state.get("sub_queries") or [state["topic"]]

    def _search_single_query(q: str):
        agent = build_search_agent()
        result = agent.invoke({
            "messages": [{"role": "user", "content": f"Search for detailed information about: {q}"}]
        })
        chunks = []
        for msg in result.get("messages", []):
            chunks.append(_extract_text(getattr(msg, "content", "")))
        last_content = _extract_text(result["messages"][-1].content)
        summary = f"### Sub-topic: {q}\n{last_content}"
        return chunks, summary

    # Run sub-query searches concurrently rather than sequentially
    with ThreadPoolExecutor(max_workers=min(len(queries), 3)) as executor:
        search_results_pairs = list(executor.map(_search_single_query, queries))

    all_chunks = []
    all_summaries = []
    for chunks, summary in search_results_pairs:
        all_chunks.extend(chunks)
        all_summaries.append(summary)

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

    new_results = "\n\n".join(all_summaries)
    existing_results = state.get("search_results", "")
    if existing_results and state.get("iterations", 0) > 0:
        combined_results = f"{existing_results}\n\n## Targeted Gap Findings (Iteration {state.get('iterations', 0) + 1}):\n{new_results}"
    else:
        combined_results = new_results

    return {
        "search_results": combined_results,
        "sources": all_sources,
    }


def read_node(state: AgentState) -> dict:
    """Scrape full pages for top sources, chunk semantically, and retrieve top-10 dense excerpts."""
    from tools import scrape_page, extract_top_chunks

    sources = state.get("sources", [])[:5]
    pages = []
    for url in sources:
        page_data = scrape_page(url)
        if page_data.get("success") and len(page_data.get("text", "")) > 100:
            pages.append(page_data)

    if pages:
        top_chunks = extract_top_chunks(
            pages=pages,
            topic=state["topic"],
            sub_queries=state.get("sub_queries", []),
            top_k=10,
        )
    else:
        # Fallback if scraping gets blocked
        agent = build_reader_agent()
        result = agent.invoke({
            "messages": [{
                "role": "user",
                "content": f"Extract key information from these search results:\n\n{state['search_results'][:4000]}"
            }]
        })
        top_chunks = _extract_text(result["messages"][-1].content)

    return {"scraped_content": top_chunks}


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
    report_text = _extract_text(report)
    chart_data = extract_chart_data(state["topic"], report_text)

    return {"report": report_text, "chart_data": chart_data}




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
    """Loop back to planner if score is low; stop after 3 iterations max."""
    if state["score"] >= 7 or state.get("iterations", 0) >= 3:
        return "end"
    return "retry"


# ── Graph Assembly ─────────────────────────────────────────────────────────────
builder = StateGraph(AgentState)

builder.add_node("planner", planner_node)
builder.add_node("search",  search_node)
builder.add_node("read",    read_node)
builder.add_node("write",   write_node)
builder.add_node("critic",  critic_node)

builder.add_edge(START,     "planner")
builder.add_edge("planner", "search")
builder.add_edge("search",  "read")
builder.add_edge("read",    "write")
builder.add_edge("write",   "critic")

builder.add_conditional_edges(
    "critic",
    should_rewrite,
    {"end": END, "retry": "planner"},
)

research_graph = builder.compile()

