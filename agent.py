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
writer_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert research writer. You write accurate, factual, and strictly sourced research reports."),
    ("human", """Write a detailed research report on the topic below.

Topic: {topic}

Verified Source URLs Found During Research:
{sources}

Research Gathered:
{research}

Structure the report as:
- Introduction
- Key Findings (minimum 3 well-explained points with concrete technical depth)
- Conclusion
- Sources

STRICT INSTRUCTIONS FOR SOURCES:
- Under 'Sources', list every relevant source URL provided above as a Markdown link with its Title (e.g., `- [Source Title or Website](URL)`).
- Never write that the report was synthesized or that no URLs were found. You MUST cite the actual URLs provided in 'Verified Source URLs Found During Research'.
- Be detailed, factual, and professional."""),
])

writer_chain = writer_prompt | llm | StrOutputParser()


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

