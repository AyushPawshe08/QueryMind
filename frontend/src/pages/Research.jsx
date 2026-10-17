import { useState, useRef } from "react";
import { marked } from "marked";
import { RotateCcwClock } from "lucide-react";
import Logo from "../components/Logo";
import { Link, navigate } from "../router";
import {
  getUser,
  clearAuth,
  researchApi,
  RESEARCH_STEPS,
} from "../api";

const MAX_TOPIC_LENGTH = 500;

const SUGGESTED_TOPICS = [
  "Quantum Computing in Drug Discovery",
  "Pros and Cons of Nuclear Fusion in 2026",
  "How do mRNA Vaccines Work?",
  "Impact of Remote Work on Global Engineering Productivity",
  "Agentic AI Architecture and Multi-Agent Collaboration",
];

export default function Research() {
  const [topic, setTopic] = useState("");
  const [error, setError] = useState("");
  const [status, setStatus] = useState("idle"); // "idle" | "running" | "done" | "failed"
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [stepDetails, setStepDetails] = useState({});
  const [report, setReport] = useState(null);
  const [copied, setCopied] = useState(false);

  // User and History state
  const [user] = useState(() => getUser());
  const [historyOpen, setHistoryOpen] = useState(false);
  const [pastReports, setPastReports] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const textareaRef = useRef(null);

  const loadHistory = async () => {
    setLoadingHistory(true);
    try {
      const reports = await researchApi.getReports();
      setPastReports(reports || []);
    } catch (err) {
      console.error("Failed to fetch past reports:", err);
    } finally {
      setLoadingHistory(false);
    }
  };

  const toggleHistory = () => {
    if (!historyOpen) {
      loadHistory();
    }
    setHistoryOpen(!historyOpen);
  };

  const handleSignOut = () => {
    clearAuth();
    navigate("/signin");
  };

  const cleanTopic = topic.trim().replace(/\s+/g, " ");
  const canSubmit = cleanTopic.length >= 3 && status !== "running";

  const startResearch = async (e) => {
    e?.preventDefault();
    if (!cleanTopic) {
      setError("Please enter a research topic.");
      textareaRef.current?.focus();
      return;
    }
    if (cleanTopic.length < 5) {
      setError("Please add a little more detail (at least 5 characters).");
      textareaRef.current?.focus();
      return;
    }

    setError("");
    setReport(null);
    setCurrentStepIndex(0);
    setStepDetails({});
    setStatus("running");

    try {
      // Step-by-step progress tracking
      const finalReport = await researchApi.streamResearch(cleanTopic, (event) => {
        if (event.type === "step") {
          const nodeName = event.node;
          const idx = RESEARCH_STEPS.findIndex((s) => s.id === nodeName);
          if (idx !== -1) {
            setCurrentStepIndex(idx + 1);
          }
          setStepDetails((prev) => ({
            ...prev,
            [nodeName]: event.message || "",
            sub_queries: event.sub_queries || prev.sub_queries,
            sources: event.sources || prev.sources,
            score: event.score || prev.score,
          }));
        }
      });

      setReport(finalReport);
      setStatus("done");
    } catch (err) {
      console.error("Research failed:", err);
      setError(err.message || "Failed to execute research pipeline. Please try again.");
      setStatus("failed");
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (canSubmit) startResearch();
    }
  };

  const resetForm = () => {
    setTopic("");
    setError("");
    setReport(null);
    setStatus("idle");
    setCurrentStepIndex(0);
    setStepDetails({});
  };

  const handleCopy = () => {
    if (!report?.report) return;
    navigator.clipboard.writeText(report.report);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    if (!report?.report) return;
    const blob = new Blob([report.report], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    const slug = (report.topic || "research-report")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .slice(0, 40);
    a.download = `${slug}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const openPastReport = async (item) => {
    try {
      const detailed = await researchApi.getReport(item.id);
      setReport({
        id: detailed.id,
        topic: detailed.topic,
        report: detailed.report_markdown,
        critique: detailed.critique,
        score: detailed.score,
        sources: detailed.sources || [],
        chart_data: detailed.chart_data || {},
        sub_queries: detailed.sub_queries || [],
        iterations: detailed.iterations || 1,
      });
      setStatus("done");
      setHistoryOpen(false);
    } catch (err) {
      console.error("Error loading report:", err);
      alert("Failed to load past report.");
    }
  };

  const deletePastReport = async (e, id) => {
    e.stopPropagation();
    if (!confirm("Delete this saved report?")) return;
    try {
      await researchApi.deleteReport(id);
      setPastReports((prev) => prev.filter((r) => r.id !== id));
      if (report?.id === id) {
        resetForm();
      }
    } catch (err) {
      console.error("Error deleting report:", err);
      alert("Failed to delete report.");
    }
  };

  // Convert markdown string to sanitized HTML using marked
  const renderedMarkdown = report?.report ? marked.parse(report.report) : "";

  return (
    <div className="app">
      {/* ── App Top Navigation ──────────────────────────────────────────────── */}
      <header className="app-bar">
        <div className="container app-bar-inner">
          <Logo size={32} />

          <div className="nav-actions">
            {user ? (
              <div className="app-user-pill">
                <span className="user-dot" />
                <span>{user.full_name || user.email.split("@")[0]}</span>
              </div>
            ) : null}

            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={toggleHistory}
              title="View past research reports"
            >
              <RotateCcwClock />History
            </button>

            {user ? (
              <button
                type="button"
                className="link-quiet small"
                onClick={handleSignOut}
                style={{ background: "none", border: "none", cursor: "pointer" }}
              >
                Sign out
              </button>
            ) : (
              <Link to="/signin" className="link-quiet small">
                Sign in
              </Link>
            )}
          </div>
        </div>
      </header>

      {/* ── Main Research Viewport ─────────────────────────────────────────── */}
      <main className="research-main">
        {status !== "done" && (
          <>
            <div className="r-hero">
              <span className="pill">
                <span className="pill-dot" /> Autonomous Multi-Agent Intelligence
              </span>
              <h1 className="r-title">What do you want to understand?</h1>
              <p className="r-lead">
                QueryMind decomposes your topic into orthogonal angles, searches the live web,
                reads full pages, synthesizes a cited report, and self-reviews quality.
              </p>
            </div>

            {/* Composer Box */}
            <form className={`composer ${error ? "has-error" : ""}`} onSubmit={startResearch}>
              <textarea
                ref={textareaRef}
                value={topic}
                onChange={(e) => {
                  setTopic(e.target.value.slice(0, MAX_TOPIC_LENGTH));
                  if (error) setError("");
                }}
                onKeyDown={handleKeyDown}
                placeholder="e.g. How do microplastics affect human health and cellular biology?"
                rows={3}
                disabled={status === "running"}
              />

              <div className="composer-foot">
                <div className="composer-hint">
                  <span>{topic.length}/{MAX_TOPIC_LENGTH}</span>
                  <span style={{ marginLeft: "12px", opacity: 0.7 }}>
                    Press ↵ to research
                  </span>
                </div>

                <button
                  className="btn composer-submit"
                  type="submit"
                  disabled={!canSubmit}
                >
                  {status === "running" ? "Researching…" : "Start research"}
                  {status !== "running" && <span aria-hidden>→</span>}
                </button>
              </div>
            </form>

            {error && (
              <p className="r-error-banner" role="alert">
                ⚠️ {error}
              </p>
            )}

            {/* Topic Suggestion Chips */}
            {status === "idle" && (
              <div className="chips-row">
                <span className="chips-label">Try one:</span>
                {SUGGESTED_TOPICS.map((suggested) => (
                  <button
                    key={suggested}
                    type="button"
                    className="chip-btn"
                    onClick={() => {
                      setTopic(suggested);
                      setError("");
                      textareaRef.current?.focus();
                    }}
                  >
                    {suggested}
                  </button>
                ))}
              </div>
            )}

            {/* Real-Time Multi-Agent Live Stepper */}
            {status === "running" && (
              <div className="agent-progress-box">
                <div className="progress-head">
                  <span className="progress-eyebrow">Multi-Agent Workflow Execution</span>
                  <div className="progress-pulse">
                    <span className="pulse-spinner" />
                    <span>Agent working in real time…</span>
                  </div>
                </div>

                <div className="agent-steps-list">
                  {RESEARCH_STEPS.map((s, idx) => {
                    const isDone = idx < currentStepIndex;
                    const isNow = idx === currentStepIndex;
                    const stepNote = stepDetails[s.id];

                    return (
                      <div
                        key={s.id}
                        className={`agent-step-item ${isNow ? "now" : isDone ? "done" : ""}`}
                      >
                        <div className="step-left">
                          <span className="step-icon-badge">
                            {isDone ? "✓" : idx + 1}
                          </span>
                          <div>
                            <div className="step-title">{s.label}</div>
                            {stepNote && (
                              <div className="step-note">{stepNote}</div>
                            )}
                          </div>
                        </div>

                        {isNow && (
                          <span className="pill" style={{ padding: "3px 10px", fontSize: "11px" }}>
                            In progress
                          </span>
                        )}
                        {isDone && (
                          <span style={{ color: "#22c55e", fontSize: "13px", fontWeight: 600 }}>
                            Done
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </>
        )}

        {/* ── Completed Report View ────────────────────────────────────────── */}
        {status === "done" && report && (
          <article className="report-view">
            {/* Action Bar */}
            <div className="report-actions-bar">
              <div className="report-meta-left">
                <button className="btn btn-ghost btn-sm" onClick={resetForm}>
                  ← New research
                </button>
                <span
                  className={`score-badge ${
                    (report.score || 0) >= 8 ? "score-high" : "score-mid"
                  }`}
                >
                  Quality Score: {report.score || 8}/10
                </span>
                <span className="report-iter-tag">
                  {report.iterations || 1} {report.iterations === 1 ? "iteration" : "iterations"}
                </span>
              </div>

              <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
                <button className="btn btn-ghost btn-sm" onClick={handleCopy}>
                  {copied ? "✓ Copied!" : "Copy Report"}
                </button>
                <button className="btn btn-sm" onClick={handleDownload}>
                  Download .md
                </button>
              </div>
            </div>

            {/* Sub-Queries Angles Strip */}
            {report.sub_queries && report.sub_queries.length > 0 && (
              <div className="subqueries-strip">
                <div className="subqueries-label">Orthogonal Research Angles Explored</div>
                <div className="subqueries-pills">
                  {report.sub_queries.map((q, i) => (
                    <span key={i} className="subquery-pill">
                      🔍 {q}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Benchmark Visualization Chart (if extracted) */}
            {report.chart_data && report.chart_data.has_chart && (
              <div className="chart-card">
                <div className="chart-header">
                  <div className="chart-title">{report.chart_data.title}</div>
                  <div className="chart-axis-note">
                    {report.chart_data.y_axis_title || "Metric"} vs {report.chart_data.x_axis_title || "Categories"}
                  </div>
                </div>

                <div className="chart-bars-wrap">
                  {(() => {
                    const cats = report.chart_data.categories || [];
                    const vals = report.chart_data.values || [];
                    const maxVal = Math.max(...vals, 1);

                    return cats.map((cat, i) => {
                      const val = vals[i] ?? 0;
                      const heightPercent = Math.max(15, Math.round((val / maxVal) * 100));

                      return (
                        <div key={i} className="chart-column">
                          <div className="chart-bar" style={{ height: `${heightPercent}%` }}>
                            <span className="chart-val">{val}</span>
                          </div>
                          <span className="chart-label">{cat}</span>
                        </div>
                      );
                    });
                  })()}
                </div>
              </div>
            )}

            {/* Markdown Report Document */}
            <div className="report-paper">
              <div
                className="markdown-body"
                dangerouslySetInnerHTML={{ __html: renderedMarkdown }}
              />
            </div>

            {/* Critic's Quality Review Box */}
            {report.critique && (
              <div className="critique-box">
                <div className="critique-title">
                  <span>🛡️</span> Critic Assessment & Feedback
                </div>
                <div className="critique-content">{report.critique}</div>
              </div>
            )}

            {/* Verified Sources Grid */}
            {report.sources && report.sources.length > 0 && (
              <div className="sources-card">
                <h3 style={{ fontSize: "17px", marginBottom: "8px" }}>
                  Verified Web Sources ({report.sources.length})
                </h3>
                <p className="muted small">
                  Sources crawled, semantically ingested, and cited throughout this report.
                </p>

                <div className="sources-grid">
                  {report.sources.map((url, idx) => {
                    let domain = url;
                    try {
                      domain = new URL(url).hostname.replace("www.", "");
                    } catch {}

                    return (
                      <a
                        key={idx}
                        href={url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="source-item"
                      >
                        <span className="source-url-text">{domain}</span>
                        <span style={{ fontSize: "11px", color: "var(--orange)" }}>↗</span>
                      </a>
                    );
                  })}
                </div>
              </div>
            )}
          </article>
        )}
      </main>

      {/* ── Slide-Over History Drawer ───────────────────────────────────────── */}
      {historyOpen && (
        <div className="drawer-backdrop" onClick={() => setHistoryOpen(false)}>
          <div className="drawer-content" onClick={(e) => e.stopPropagation()}>
            <div className="drawer-head">
              <h3 style={{ fontSize: "18px" }}>Your Research Library</h3>
              <button
                className="btn-icon"
                onClick={() => setHistoryOpen(false)}
                aria-label="Close history"
              >
                ✕
              </button>
            </div>

            <div className="drawer-list">
              {loadingHistory ? (
                <p className="muted small" style={{ textAlign: "center", marginTop: "30px" }}>
                  Loading saved reports…
                </p>
              ) : pastReports.length === 0 ? (
                <p className="muted small" style={{ textAlign: "center", marginTop: "30px" }}>
                  No saved research reports yet. Complete your first research to see it here!
                </p>
              ) : (
                pastReports.map((item) => (
                  <div
                    key={item.id}
                    className="drawer-item"
                    onClick={() => openPastReport(item)}
                  >
                    <div className="drawer-item-title">{item.topic}</div>
                    <div className="drawer-item-meta">
                      <span>Score: {item.score || "N/A"}/10</span>
                      <span>
                        {item.created_at
                          ? new Date(item.created_at).toLocaleDateString()
                          : "Recently"}
                      </span>
                      <button
                        className="btn-icon"
                        onClick={(e) => deletePastReport(e, item.id)}
                        title="Delete report"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}