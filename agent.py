from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools import web_search, scrape_url
from dotenv import load_dotenv

load_dotenv()

# ── Model Setup ────────────────────────────────────────────────────────────────
llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", temperature=0)


# ── Agent 1: Search Agent ──────────────────────────────────────────────────────
def build_search_agent():
    return create_agent(
        model=llm,
        tools=[web_search],
        system_prompt=(
            "You are a web research specialist. "
            "Search the web thoroughly for information on the given topic. "
            "You MUST explicitly include all source Titles and their full URLs (https://...) in your final response. "
            "Never summarize away, omit, or invent URLs."
        ),
    )


# ── Agent 2: Reader Agent ──────────────────────────────────────────────────────
def build_reader_agent():
    return create_agent(
        model=llm,
        tools=[scrape_url],
        system_prompt=(
            "You are a content extraction specialist. "
            "Given URLs from search results, scrape the most relevant pages and extract "
            "the most informative details. "
            "Always state which source URL each piece of information was extracted from."
        ),
    )


# ── Writer Chain ───────────────────────────────────────────────────────────────
# ── Writer Chain ───────────────────────────────────────────────────────────────
writer_prompt = ChatPromptTemplate.from_messages([
    ("system", (
        "You are a principal research scientist and technical author. "
        "You synthesize rigorous, data-driven, and authoritative research reports "
        "backed by concrete numbers, architectural details, and verified citations."
    )),
    ("human", """Write an authoritative, publication-grade research report on the topic below.

Topic: {topic}

Verified Source URLs Found During Research:
{sources}

Information & Excerpts Gathered:
{research}

### REQUIRED REPORT STRUCTURE:

# Research Report: {topic}

## Executive Summary
A comprehensive briefing of the paradigm, core significance, and current landscape.

## Architecture & Foundational Principles
Deep explanation of the core technical mechanisms, design patterns, and workflows.

## Real-World Implementations & Empirical Benchmarks
Concrete real-world deployments, enterprise systems, and empirical results.
- You MUST include at least one structured **Markdown comparison table** summarizing key metrics (e.g. latency, throughput, benchmark accuracy, cost, or parameter efficiency).

## Challenges, Trade-Offs & Future Outlook
Objective technical analysis of bottlenecks, scalability constraints, and the 2026+ evolutionary roadmap.

## Conclusion & Strategic Takeaways
Final synthesis and actionable summary for engineers and researchers.

## Verified Sources
- List every relevant source URL provided above as a clean Markdown link with its Title (e.g., `- [Source Title or Website](URL)`).
- Never write that the report was synthesized or that no URLs were found. You MUST cite the actual URLs provided.

### STRICT WRITING RULES:
- Use **inline citations** next to specific technical facts or numbers (e.g., "...demonstrated by [Organization Name](URL)...").
- Be detailed, factual, and deeply technical. Avoid superficial generalities."""),
])

writer_chain = writer_prompt | llm | StrOutputParser()


# ── Chart Data Extractor Chain ─────────────────────────────────────────────────
chart_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a quantitative research data analyst.
Your job is to extract quantifiable, numerical benchmark comparisons from technical research reports into structured JSON for Plotly visualization.

If real comparative numbers (e.g., benchmark accuracy %, throughput tokens/s, latency ms, parameter counts, cost metrics) are present in the text, extract them into a chart.
If the research does NOT contain comparative numbers, output exactly: {{"has_chart": false}}

When numerical data is found, output valid JSON in this exact structure:
{{
  "has_chart": true,
  "title": "Short descriptive chart title",
  "chart_type": "bar",
  "x_axis_title": "Systems / Models / Categories",
  "y_axis_title": "Metric Name (e.g. Accuracy %, Latency ms)",
  "categories": ["System A", "System B", "System C"],
  "values": [78.4, 86.2, 92.0]
}}
Do NOT output markdown backticks or commentary. Output raw JSON only."""),
    ("human", """Extract benchmark chart data from this research report:

Topic: {topic}

Report:
{report}"""),
])

chart_data_chain = chart_prompt | llm | StrOutputParser()


def extract_chart_data(topic: str, report: str) -> dict:
    """Extract structured numerical benchmark data for Plotly charts."""
    import json
    import re

    try:
        raw = chart_data_chain.invoke({"topic": topic, "report": report})
        cleaned = re.sub(r"^```json\s*", "", raw.strip(), flags=re.IGNORECASE)
        cleaned = re.sub(r"```$", "", cleaned.strip()).strip()
        data = json.loads(cleaned)

        if data.get("has_chart"):
            cats = data.get("categories", [])
            vals = data.get("values", [])
            if cats and vals and len(cats) == len(vals) and len(cats) >= 2:
                # Ensure values are floats/ints
                data["values"] = [float(v) for v in vals]
                return data
    except Exception as e:
        print(f"[Chart Notice] No valid chart data extracted: {e}")

    return {"has_chart": False}



# ── Critic Chain ───────────────────────────────────────────────────────────────
critic_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a sharp and constructive research critic. Be honest and specific."),
    ("human", """Review the research report below and evaluate it strictly.

Report:
{report}

Evaluation Criteria:
1. Are there minimum 3 concrete, deep key findings?
2. Are real, clickable external source URLs listed under Sources? (Heavily penalize if URLs are missing or if the author claims sources are synthesized without URLs)
3. Is the writing clear, professional, and insightful?

Respond in this exact format:

Score: X/10

Strengths:
- ...
- ...

Areas to Improve:
- ...
- ...

One line verdict:
..."""),
])

critic_chain = critic_prompt | llm | StrOutputParser()


# ── Topic Validator ────────────────────────────────────────────────────────────
def validate_topic(topic: str) -> dict:
    """Quick LLM check: is this topic suitable for factual web research?"""
    from langchain_core.messages import HumanMessage, SystemMessage

    messages = [
        SystemMessage(content="""You are a research topic validator.
Decide if the given topic is suitable for factual web research.

A topic is INVALID if it:
- Asks for a personal opinion ("what do you think about X")
- Is purely subjective (best color, favorite food)
- Is too vague (single word like "life", "stuff")
- Is about a private individual with no public information

A topic is VALID if it:
- Has factual, researchable information on the web
- Is about a concept, technology, public figure, event, science, etc.

Reply in EXACTLY one of these two formats — nothing else:
VALID
INVALID: <one short reason>"""),
        HumanMessage(content=f"Topic: {topic}"),
    ]

    parser = StrOutputParser()
    raw_text = parser.invoke(llm.invoke(messages))
    if isinstance(raw_text, list):
        text = " ".join(str(x) for x in raw_text).strip()
    else:
        text = str(raw_text).strip()

    if text.upper().startswith("VALID"):
        return {"valid": True, "reason": ""}
    else:
        reason = text.replace("INVALID:", "").replace("INVALID", "").strip()
        return {"valid": False, "reason": reason or "Topic is not suitable for research."}


# ── Planner Chain (Sub-Query Decomposition) ───────────────────────────────────
planner_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a research planning strategist. Your job is to break down a research topic into targeted, distinct web search queries."),
    ("human", """Given the research topic below, generate exactly 3 orthogonal, high-signal search queries that cover:
1. Core technical architecture, mechanisms, or foundational principles
2. Current real-world implementations, benchmarks, or modern trends
3. Key challenges, trade-offs, and future developments

Topic: {topic}

Provide EXACTLY 3 queries, one per line, without numbering, bullets, or commentary:"""),
])

planner_chain = planner_prompt | llm | StrOutputParser()


def parse_queries(raw_output: str, fallback_topic: str) -> list[str]:
    """Parse newline-delimited queries and remove bullets/numbers."""
    lines = [line.strip() for line in raw_output.strip().splitlines() if line.strip()]
    cleaned = []
    for line in lines:
        # Strip leading numbers/bullets like "1. ", "- ", etc.
        import re
        c = re.sub(r"^(\d+[\.\)]|[-*•])\s*", "", line).strip().strip('"\'')
        if c:
            cleaned.append(c)
    return cleaned[:3] if cleaned else [fallback_topic]


def generate_sub_queries(topic: str) -> list[str]:
    """Generate 3 orthogonal sub-queries for a topic."""
    raw = planner_chain.invoke({"topic": topic})
    return parse_queries(raw, topic)


# ── Gap Query Chain (Critique-Aware Retries) ───────────────────────────────────
gap_query_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a research gap analyst. You analyze critic feedback and generate targeted search queries to resolve missing evidence or weaknesses."),
    ("human", """The research report on '{topic}' was reviewed by a critic:

{critique}

Identify the key missing facts, depth gaps, or weaknesses noted in the critique.
Generate exactly 2 to 3 targeted web search queries specifically designed to locate the missing information and fix those gaps.

Provide EXACTLY 2 to 3 queries, one per line, without numbering, bullets, or commentary:"""),
])

gap_query_chain = gap_query_prompt | llm | StrOutputParser()


def generate_gap_queries(topic: str, critique: str) -> list[str]:
    """Generate 2-3 targeted search queries to address critic feedback."""
    raw = gap_query_chain.invoke({"topic": topic, "critique": critique})
    return parse_queries(raw, topic)


