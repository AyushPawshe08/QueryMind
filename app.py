import re
import markdown
import streamlit as st
from pydantic import ValidationError

from graph import research_graph
from database import (
    init_db,
    save_report,
    get_past_reports,
    get_report_by_id,
    create_user,
    get_user_by_email,
    get_user_by_id,
)
from auth import (
    UserRegisterSchema,
    UserLoginSchema,
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)

# Initialize Neon DB tables and columns on startup
init_db()

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="QueryMind - Deep Research Agent",
    page_icon="🔬",
    layout="wide",
)

# ── Global Styling ─────────────────────────────────────────────────────────────
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
    .report-box table { width: 100%; border-collapse: collapse; margin: 12px 0; }
    .report-box th { background: #1e3a5f; color: #bfdbfe; border: 1px solid #334155; padding: 6px 10px; }
    .report-box td { border: 1px solid #334155; padding: 6px 10px; color: #e2e8f0; }
    .metric-card {
        background: #1e293b;
        color: #f8fafc;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    .auth-card {
        background: #131722;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 2rem;
        max-width: 480px;
        margin: 2rem auto;
    }
</style>
""", unsafe_allow_html=True)


# ── Authentication Gate (PyJWT + pwdlib[argon2] + pydantic[email]) ─────────────
current_user = None
token = st.session_state.get("auth_token")

if token:
    payload = decode_access_token(token)
    if payload:
        current_user = get_user_by_id(payload["user_id"])
        if not current_user:
            st.session_state["auth_token"] = None
    else:
        st.session_state["auth_token"] = None

# If not authenticated, render login/registration portal
if not current_user:
    st.markdown("<h2 style='text-align: center; color: #60a5fa;'>🔬 QueryMind</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8;'>AI Deep Research Platform — Please sign in to access your personal research workspace.</p>", unsafe_allow_html=True)

    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        tab_login, tab_register = st.tabs(["🔑 Log In", "✨ Create Account"])

        with tab_login:
            st.markdown("#### Welcome Back")
            with st.form("login_form", clear_on_submit=False):
                login_email = st.text_input("Email", placeholder="name@company.com")
                login_password = st.text_input("Password", type="password", placeholder="••••••••")
                login_submitted = st.form_submit_button("Sign In", width="stretch", type="primary")

                if login_submitted:
                    try:
                        validated = UserLoginSchema(email=login_email.strip(), password=login_password)
                        user_record = get_user_by_email(validated.email)
                        if user_record and verify_password(validated.password, user_record["hashed_password"]):
                            new_token = create_access_token(user_id=user_record["id"], email=user_record["email"])
                            st.session_state["auth_token"] = new_token
                            st.toast(f"Welcome back, {user_record['full_name'] or user_record['email']}!", icon="👋")
                            st.rerun()
                        else:
                            st.error("Invalid email or password.")
                    except ValidationError as ve:
                        st.error(f"Validation error: {ve.errors()[0]['msg']}")

        with tab_register:
            st.markdown("#### New Researcher Account")
            with st.form("register_form", clear_on_submit=False):
                reg_name = st.text_input("Full Name (Optional)", placeholder="Jane Doe")
                reg_email = st.text_input("Email Address", placeholder="name@company.com")
                reg_password = st.text_input("Password (min. 8 characters)", type="password", placeholder="••••••••")
                reg_submitted = st.form_submit_button("Register & Get Started", width="stretch", type="primary")

                if reg_submitted:
                    try:
                        validated = UserRegisterSchema(
                            email=reg_email.strip(),
                            password=reg_password,
                            full_name=reg_name.strip() if reg_name else None,
                        )
                        # Check existing user
                        existing = get_user_by_email(validated.email)
                        if existing:
                            st.error("An account with this email already exists.")
                        else:
                            hashed = hash_password(validated.password)
                            new_user = create_user(
                                email=validated.email,
                                hashed_password=hashed,
                                full_name=validated.full_name,
                            )
                            if new_user:
                                new_token = create_access_token(user_id=new_user["id"], email=new_user["email"])
                                st.session_state["auth_token"] = new_token
                                st.success("Account created successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to create account. Please try again.")
                    except ValidationError as ve:
                        st.error(f"Validation error: {ve.errors()[0]['msg']}")

    st.stop()


# ── Authenticated User Workspace ───────────────────────────────────────────────

# ── Sidebar: User Profile & Personal Research History ──────────────────────────
with st.sidebar:
    user_display = current_user.get("full_name") or current_user.get("email").split("@")[0]
    st.markdown(f"### 👤 {user_display}")
    st.caption(f"Signed in as `{current_user['email']}`")

    if st.button("🚪 Log Out", width="stretch", type="secondary"):
        st.session_state["auth_token"] = None
        st.session_state["loaded_report"] = None
        st.session_state["active_result"] = None
        st.session_state["topic_input"] = ""
        st.session_state["is_running"] = False
        st.rerun()

    st.divider()
    st.markdown("### 📚 Your Research History")

    if st.button("➕ New Research", width="stretch", type="primary"):
        st.session_state["loaded_report"] = None
        st.session_state["active_result"] = None
        st.session_state["topic_input"] = ""
        st.session_state["is_running"] = False
        st.rerun()

    st.markdown("---")
    # Fetch past reports belonging strictly to the authenticated user
    past_reports = get_past_reports(user_id=current_user["id"], limit=30)
    if past_reports:
        for pr in past_reports:
            score_str = f"⭐ {pr['score']}/10" if pr.get("score") is not None else "📝"
            title_clean = pr["topic"][:26] + ("..." if len(pr["topic"]) > 26 else "")
            date_str = pr["created_at"].strftime("%b %d, %H:%M") if pr.get("created_at") else ""

            if st.button(
                f"{score_str} · {title_clean}",
                key=f"hist_{pr['id']}",
                width="stretch",
                help=f"{pr['topic']}\nSaved: {date_str}",
            ):
                st.session_state["active_result"] = None
                st.session_state["loaded_report"] = get_report_by_id(pr["id"], user_id=current_user["id"])
                st.rerun()
    else:
        st.caption("No past research saved yet in your account.")


# ── Header ─────────────────────────────────────────────────────────────────────
st.title("🔬 Research Agent")
st.caption("Powered by **LangGraph** · **Gemini** · **Tavily** — Plan → Search → Read → Write → Critique")
st.divider()

# ── Session State Init ─────────────────────────────────────────────────────────
if "topic_input" not in st.session_state:
    st.session_state["topic_input"] = ""
if "is_running" not in st.session_state:
    st.session_state["is_running"] = False
if "topic_to_run" not in st.session_state:
    st.session_state["topic_to_run"] = None
if "active_result" not in st.session_state:
    st.session_state["active_result"] = None


def trigger_research():
    """Callback fired immediately before rerun, locking the button and input."""
    val = st.session_state.get("topic_input", "").strip()
    if val and not st.session_state.get("is_running", False):
        st.session_state["is_running"] = True
        st.session_state["topic_to_run"] = val
        st.session_state["loaded_report"] = None
        st.session_state["active_result"] = None


# ── Suggested Topics ───────────────────────────────────────────────────────────
st.markdown("##### 💡 2026 Trending Research Topics:")
suggested_topics = [
    "Agentic AI Workflows & Multi-Agent Systems in 2026",
    "Post-Quantum Cryptography Migration & NIST Standards",
    "Humanoid Robotics & Embodied AI Breakthroughs",
    "Small Language Models (SLMs) & On-Device Edge AI",
]

sug_cols = st.columns(len(suggested_topics))
for idx, sug in enumerate(suggested_topics):
    if sug_cols[idx].button(
        sug, key=f"sug_{idx}", width="stretch",
        disabled=st.session_state.get("is_running", False),
    ):
        st.session_state["topic_input"] = sug
        st.rerun()

# ── Input ──────────────────────────────────────────────────────────────────────
topic = st.text_input(
    "Research Topic",
    value=st.session_state.get("topic_input", ""),
    placeholder="e.g. How do LLMs work?",
    label_visibility="visible",
    disabled=st.session_state.get("is_running", False),
    key="topic_input_field",
)
# Sync text_input to topic_input in state if not running
if not st.session_state.get("is_running", False):
    st.session_state["topic_input"] = topic

run_btn = st.button(
    "⏳ Research in Progress..." if st.session_state.get("is_running", False) else "🚀 Run Research",
    type="primary",
    disabled=not topic.strip() or st.session_state.get("is_running", False),
    on_click=trigger_research,
)


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
        a  {{ color: #1a73e8; text-decoration: underline; }}
        ul, ol {{ padding-left: 1.5em; }}
        blockquote {{
            border-left: 4px solid #4a90d9;
            padding-left: 14px;
            color: #555;
            margin-left: 0;
        }}
        table {{ width: 100%; margin: 12px 0; }}
        th {{ background: #e8f0fe; font-weight: bold; border: 1px solid #94a3b8; padding: 5px 8px; }}
        td {{ border: 1px solid #cbd5e1; padding: 5px 8px; color: #1e293b; }}
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


# ── Plotly Chart Renderer ──────────────────────────────────────────────────────
def render_plotly_chart(chart_data: dict | None):
    """Render interactive Plotly bar chart from extracted benchmark data."""
    if not chart_data or not chart_data.get("has_chart"):
        return

    import plotly.graph_objects as go

    title  = chart_data.get("title", "Empirical Benchmark Comparison")
    cats   = chart_data.get("categories", [])
    vals   = chart_data.get("values", [])
    x_lbl  = chart_data.get("x_axis_title", "System / Model")
    y_lbl  = chart_data.get("y_axis_title", "Value")

    fig = go.Figure(data=[go.Bar(
        x=cats, y=vals,
        marker=dict(color=vals, colorscale="Blues", line=dict(color="#38bdf8", width=1.5)),
        text=vals, textposition="auto",
    )])
    fig.update_layout(
        title=dict(text=f"📊 {title}", font=dict(color="#60a5fa", size=16)),
        xaxis=dict(title=x_lbl, color="#94a3b8", gridcolor="#334155"),
        yaxis=dict(title=y_lbl, color="#94a3b8", gridcolor="#334155"),
        plot_bgcolor="#131722", paper_bgcolor="#131722",
        font=dict(color="#e2e8f0"),
        margin=dict(l=40, r=40, t=50, b=40), height=380,
    )
    st.plotly_chart(fig, width="stretch")


# ── Report Renderer ────────────────────────────────────────────────────────────
def render_report_content(report_md: str):
    """Render the full Markdown report inside the styled dark box."""
    st.markdown(
        f'<div class="report-box">'
        f'{markdown.markdown(report_md, extensions=["extra", "tables", "toc"])}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Main Flow: Running Research ────────────────────────────────────────────────
if st.session_state.get("is_running") and st.session_state.get("topic_to_run"):
    run_topic = st.session_state["topic_to_run"]

    # ── Topic Validation Gate ──────────────────────────────────────────────────
    from agent import validate_topic
    with st.spinner("🔎 Validating topic..."):
        validation = validate_topic(run_topic)

    if not validation["valid"]:
        st.session_state["is_running"] = False
        st.session_state["topic_to_run"] = None
        st.error(f"⛔ **Topic not suitable for research**\n\n{validation['reason']}")
        st.info("💡 Try a factual topic — e.g. *'How do transformers work?'*")
        st.stop()

    # ── Pipeline Status Row ────────────────────────────────────────────────────
    st.markdown("#### ⚙️ Pipeline Status")
    col1, col2, col3, col4, col5 = st.columns(5)
    p_plan   = col1.empty()
    p_search = col2.empty()
    p_read   = col3.empty()
    p_write  = col4.empty()
    p_critic = col5.empty()

    p_plan.info("🎯 Planning...")
    p_search.info("🔍 Searching...")
    p_read.info("📖 Reading...")
    p_write.info("✍️ Writing...")
    p_critic.info("🧐 Critiquing...")

    sub_q_container = st.empty()

    # ── Initial State ──────────────────────────────────────────────────────────
    state: dict = {
        "topic":           run_topic,
        "sub_queries":     [],
        "search_results":  "",
        "scraped_content": "",
        "sources":         [],
        "report":          "",
        "critique":        "",
        "score":           0,
        "iterations":      0,
        "chart_data":      {},
    }

    # ── Stream LangGraph Updates ───────────────────────────────────────────────
    for chunk in research_graph.stream(state, stream_mode="updates"):
        if "planner" in chunk:
            state.update(chunk["planner"])
            if state["iterations"] == 0:
                p_plan.success(f"✅ Planned ({len(state['sub_queries'])} angles)")
                badges = "".join(
                    f"<span style='background:#1e293b;color:#93c5fd;padding:4px 8px;"
                    f"margin-right:6px;margin-bottom:4px;display:inline-block;"
                    f"border-radius:4px;font-size:0.85rem;border:1px solid #334155;'>📌 {q}</span>"
                    for q in state["sub_queries"]
                )
                sub_q_container.markdown(
                    f"<div style='margin-top:0.3rem;'><b>Targeted Angles:</b><br/>{badges}</div>",
                    unsafe_allow_html=True,
                )
            else:
                p_plan.warning(f"🔄 Gap Queries ({len(state['sub_queries'])})")
                badges = "".join(
                    f"<span style='background:#3b1e2b;color:#fca5a5;padding:4px 8px;"
                    f"margin-right:6px;margin-bottom:4px;display:inline-block;"
                    f"border-radius:4px;font-size:0.85rem;border:1px solid #7f1d1d;'>🎯 {q}</span>"
                    for q in state["sub_queries"]
                )
                sub_q_container.markdown(
                    f"<div style='margin-top:0.3rem;'><b>Refining Gaps:</b><br/>{badges}</div>",
                    unsafe_allow_html=True,
                )
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

    # ── Auto-Save to Neon DB (Scoped to Current User) ──────────────────────────
    report_id = save_report(
        topic=run_topic,
        sub_queries=state["sub_queries"],
        report=state["report"],
        critique=state["critique"],
        score=state["score"],
        iterations=state["iterations"],
        sources=state["sources"],
        chart_data=state.get("chart_data"),
        user_id=current_user["id"],
    )
    if report_id:
        st.toast(f"💾 Research saved to your account in Neon DB (ID #{report_id})", icon="✅")

    # Save to active_result and release lock
    st.session_state["active_result"] = state
    st.session_state["is_running"] = False
    st.session_state["topic_to_run"] = None
    st.rerun()


# ── Render Latest Research Result ──────────────────────────────────────────────
elif st.session_state.get("active_result"):
    res = st.session_state["active_result"]

    st.markdown("#### 📄 Final Research Report")

    if res.get("score", 0) < 7:
        st.warning(
            f"⚠️ **Report quality below threshold** ({res['score']}/10 after "
            f"{res.get('iterations', 1)} iteration(s)). Consider a more specific, factual topic."
        )

    render_plotly_chart(res.get("chart_data"))
    render_report_content(res["report"])

    st.divider()

    # ── Critique & Metrics ─────────────────────────────────────────────────────
    left, right = st.columns([2, 1])
    with left:
        with st.expander("🧐 Critic Review", expanded=False):
            st.text(res.get("critique", "No critique available."))
    with right:
        m1, m2 = st.columns(2)
        m1.metric("Score", f"{res.get('score', 'N/A')}/10")
        m2.metric("Iterations", res.get("iterations", 1))

    st.divider()

    # ── PDF Download ───────────────────────────────────────────────────────────
    with st.spinner("Generating PDF..."):
        pdf_bytes = generate_pdf(res["report"], res["topic"])

    safe_name = res["topic"].strip().replace(" ", "_")[:40]
    st.download_button(
        label="📥 Download Report as PDF",
        data=pdf_bytes,
        file_name=f"{safe_name}_report.pdf",
        mime="application/pdf",
        type="primary",
        width="stretch",
    )


# ── Render Archived Report from Neon DB ────────────────────────────────────────
elif st.session_state.get("loaded_report"):
    loaded = st.session_state["loaded_report"]
    created_at_str = (
        loaded["created_at"].strftime("%B %d, %Y at %H:%M")
        if loaded.get("created_at") else ""
    )

    st.info(f"📂 **Viewing Archived Research Report** · Saved on {created_at_str}")

    col_title, col_close = st.columns([4, 1])
    with col_title:
        st.subheader(f"📑 {loaded['topic']}")
    with col_close:
        if st.button("✖️ Close View", width="stretch"):
            st.session_state["loaded_report"] = None
            st.rerun()

    if loaded.get("sub_queries"):
        badges = "".join(
            f"<span style='background:#1e293b;color:#93c5fd;padding:4px 8px;"
            f"margin-right:6px;margin-bottom:4px;display:inline-block;"
            f"border-radius:4px;font-size:0.85rem;border:1px solid #334155;'>📌 {q}</span>"
            for q in loaded["sub_queries"]
        )
        st.markdown(
            f"<div style='margin-bottom:1rem;'><b>Research Angles:</b><br/>{badges}</div>",
            unsafe_allow_html=True,
        )

    render_plotly_chart(loaded.get("chart_data"))
    render_report_content(loaded["report"])

    st.divider()

    left, right = st.columns([2, 1])
    with left:
        with st.expander("🧐 Critic Review", expanded=True):
            st.text(loaded.get("critique", "No critique available."))
    with right:
        m1, m2 = st.columns(2)
        m1.metric("Score", f"{loaded.get('score', 'N/A')}/10")
        m2.metric("Iterations", loaded.get("iterations", 1))

    st.divider()

    with st.spinner("Preparing PDF..."):
        pdf_bytes = generate_pdf(loaded["report"], loaded["topic"])

    safe_name = loaded["topic"].strip().replace(" ", "_")[:40]
    st.download_button(
        label="📥 Download Archived Report as PDF",
        data=pdf_bytes,
        file_name=f"{safe_name}_archived.pdf",
        mime="application/pdf",
        type="primary",
        width="stretch",
    )
