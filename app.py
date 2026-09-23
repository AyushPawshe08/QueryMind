import io
import markdown
import streamlit as st
from graph import research_graph

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Research Agent",
    page_icon="🔬",
    layout="wide",
)

# ── Styling ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    .report-box {
        background: #131722;
        color: #e2e8f0;
        border-radius: 10px;
        padding: 2rem;
        border-left: 5px solid #3b82f6;
        border: 1px solid #2d3748;
        border-left-width: 5px;
        margin-top: 1rem;
        line-height: 1.75;
    }
    .report-box h1, .report-box h2, .report-box h3, .report-box h4 {
        color: #60a5fa !important;
        margin-top: 1.2rem;
        margin-bottom: 0.6rem;
    }
    .report-box p, .report-box li {
        color: #e2e8f0 !important;
        font-size: 1.02rem;
    }
    .report-box a {
        color: #93c5fd !important;
        text-decoration: underline;
    }
    .report-box code {
        background: #1e293b !important;
        color: #f8fafc !important;
        padding: 2px 6px;
        border-radius: 4px;
    }
    .metric-card {
        background: #1e293b;
        color: #f8fafc;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("🔬 Research Agent")
st.caption("Powered by **LangGraph** · **Gemini** · **Tavily** — Search → Read → Write → Critique")
st.divider()

# ── Suggested Topics ───────────────────────────────────────────────────────────
st.markdown("##### 💡 2026 Trending Research Topics:")
suggested_topics = [
    "Agentic AI Workflows & Multi-Agent Systems in 2026",
    "Post-Quantum Cryptography Migration & NIST Standards",
    "Humanoid Robotics & Embodied AI Breakthroughs",
    "Small Language Models (SLMs) & On-Device Edge AI",
]

if "topic_input" not in st.session_state:
    st.session_state["topic_input"] = ""

sug_cols = st.columns(len(suggested_topics))
for idx, sug in enumerate(suggested_topics):
    if sug_cols[idx].button(sug, key=f"sug_{idx}", use_container_width=True):
        st.session_state["topic_input"] = sug
        st.rerun()

# ── Input ──────────────────────────────────────────────────────────────────────
topic = st.text_input(
    "Research Topic",
    value=st.session_state.get("topic_input", ""),
    placeholder="e.g. How do LLMs work?",
    label_visibility="visible",
)
run_btn = st.button("🚀 Run Research", type="primary", disabled=not topic.strip())



# ── PDF Generator ──────────────────────────────────────────────────────────────
def generate_pdf(report_md: str, topic: str) -> bytes:
    from io import BytesIO
    from xhtml2pdf import pisa

    html_body = markdown.markdown(report_md, extensions=["extra", "toc"])
    styled = f"""
    <html>
    <head>
    <meta charset="utf-8"/>
    <style>
        @page {{ margin: 2cm; }}
        body {{
            font-family: Helvetica, Arial, sans-serif;
            font-size: 11pt;
            color: #222;
            line-height: 1.7;
        }}
        .cover-title {{
            font-size: 20pt;
            font-weight: bold;
            color: #1a1a2e;
            margin-bottom: 6px;
        }}
        .cover-sub {{
            font-size: 11pt;
            color: #555;
            margin-bottom: 30px;
            border-bottom: 2px solid #4a90d9;
            padding-bottom: 12px;
        }}
        h1 {{ font-size: 16pt; color: #1a1a2e; margin-top: 24px; }}
        h2 {{ font-size: 13pt; color: #16213e; margin-top: 18px; }}
        h3 {{ font-size: 11pt; color: #333; }}
        a  {{ color: #1a73e8; text-decoration: underline; word-wrap: break-word; }}
        ul, ol {{ padding-left: 1.5em; }}
        blockquote {{
            border-left: 4px solid #4a90d9;
            padding-left: 14px;
            color: #555;
            margin-left: 0;
        }}
    </style>
    </head>
    <body>
        <div class="cover-title">Research Report</div>
        <div class="cover-sub">Topic: {topic}</div>
        {html_body}
    </body>
    </html>
    """
    buf = BytesIO()
    pisa.CreatePDF(styled, dest=buf)
    return buf.getvalue()


# ── Main Flow ──────────────────────────────────────────────────────────────────
if run_btn and topic.strip():

    # ── Topic Validation Gate ──────────────────────────────────────────────────
    from agent import validate_topic
    with st.spinner("🔎 Validating topic..."):
        validation = validate_topic(topic.strip())

    if not validation["valid"]:
        st.error(f"⛔ **Topic not suitable for research**\n\n{validation['reason']}")
        st.info("💡 **Try a factual topic** — e.g. *'How do transformers work?'*, *'History of quantum computing'*, *'Impact of AI on healthcare'*")
        st.stop()

    # Status row
    st.markdown("#### ⚙️ Pipeline Status")
    col1, col2, col3, col4 = st.columns(4)
    p_search = col1.empty()
    p_read   = col2.empty()
    p_write  = col3.empty()
    p_critic = col4.empty()

    p_search.info("🔍 Searching...")
    p_read.info("📖 Reading...")
    p_write.info("✍️ Writing...")
    p_critic.info("🧐 Critiquing...")


    # Accumulated state
    state: dict = {
        "topic":           topic.strip(),
        "search_results":  "",
        "scraped_content": "",
        "sources":         [],
        "report":          "",
        "critique":        "",
        "score":           0,
        "iterations":      0,
    }

    # Stream graph updates node-by-node
    for chunk in research_graph.stream(state, stream_mode="updates"):
        if "search" in chunk:
            state.update(chunk["search"])
            p_search.success(f"✅ Searched (iter {state['iterations'] + 1})")
        if "read" in chunk:
            state.update(chunk["read"])
            p_read.success("✅ Read")
        if "write" in chunk:
            state.update(chunk["write"])
            p_write.success("✅ Written")
        if "critic" in chunk:
            state.update(chunk["critic"])
            p_critic.success(f"✅ Critiqued · Score {state['score']}/10")

    st.divider()

    # ── Report Preview ─────────────────────────────────────────────────────────
    st.markdown("#### 📄 Final Report")

    # Low-score warning banner
    if state["score"] < 7:
        st.warning(
            f"⚠️ **Report quality is below threshold** ({state['score']}/10 after {state['iterations']} iteration(s)). "
            "The topic may be too subjective or lack sufficient web sources. "
            "Consider rephrasing with a more specific, factual angle."
        )

    with st.container():
        st.markdown(
            f'<div class="report-box">{markdown.markdown(state["report"], extensions=["extra"])}</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Critique & Metrics ─────────────────────────────────────────────────────
    left, right = st.columns([2, 1])

    with left:
        with st.expander("🧐 Critic Review", expanded=False):
            st.text(state["critique"])

    with right:
        m1, m2 = st.columns(2)
        m1.metric("Score", f"{state['score']}/10")
        m2.metric("Iterations", state["iterations"])

    st.divider()

    # ── PDF Download ───────────────────────────────────────────────────────────
    with st.spinner("Generating PDF..."):
        pdf_bytes = generate_pdf(state["report"], topic.strip())

    safe_name = topic.strip().replace(" ", "_")[:40]
    st.download_button(
        label="📥 Download Report as PDF",
        data=pdf_bytes,
        file_name=f"{safe_name}_report.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True,
    )
