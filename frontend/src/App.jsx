import { useEffect, useState } from "react";
import Logo from "./components/Logo";
import Auth from "./pages/Auth";
import { Link, navigate, usePath } from "./router";
import { authApi, getToken, getUser } from "./api";
import Research from "./pages/Research";

const STEPS = [
  "Checking your topic",
  "Planning 3 research angles",
  "Searching the web",
  "Reading the best sources",
  "Writing the report",
  "Reviewing for quality",
];

const HOW = [
  {
    n: "01",
    title: "Ask anything",
    text: "Type a topic or a question. QueryMind first checks that it's something that can actually be researched.",
  },
  {
    n: "02",
    title: "It breaks it down",
    text: "Your question is split into three different angles so the research covers the topic from every side.",
  },
  {
    n: "03",
    title: "It searches and reads",
    text: "Sources are found across the web, then read in full, not just skimmed from snippets.",
  },
  {
    n: "04",
    title: "It writes and self-reviews",
    text: "A report is drafted and scored out of 10. If it isn't good enough, it goes back and fills the gaps.",
  },
];

const FEATURES = [
  {
    title: "Real sources, real links",
    text: "Every report lists the pages it was built from, so you can check the work yourself.",
  },
  {
    title: "Charts and diagrams",
    text: "Reports include visuals where they help: flow diagrams and data charts, not just walls of text.",
  },
  {
    title: "Self-critiquing",
    text: "A built-in reviewer scores each draft and sends it back for improvement when it falls short.",
  },
  {
    title: "Live progress",
    text: "Watch each stage happen in real time instead of staring at a spinner.",
  },
  {
    title: "Your research library",
    text: "Every report is saved to your account. Revisit, search, or delete them any time.",
  },
  {
    title: "Export as Markdown",
    text: "Download any report as a clean .md file and drop it into your notes or docs.",
  },
];



function Navbar() {
  return (
    <header className="">
      <div className="container nav-inner">
        <Logo />
        <nav className="nav-links">
          <a href="#how">How it works</a>
          <a href="#features">Features</a>
          <a href="#report">Sample report</a>
        </nav>
        <div className="nav-actions">
          <Link to="/signin" className="link-quiet">Sign in</Link>
          <Link to="/signup" className="btn btn-sm">Get started</Link>
        </div>
      </div>
    </header>
  );
}

function Mockup() {
  const [active, setActive] = useState(0);

  useEffect(() => {
    const t = setInterval(() => {
      setActive((a) => (a + 1) % (STEPS.length + 2));
    }, 1300);
    return () => clearInterval(t);
  }, []);

  const done = active >= STEPS.length;

  return (
    <div className="mock">
      <div className="mock-bar">
        <i /><i /><i />
        <span className="mock-url">querymind.app/research</span>
      </div>

      <div className="mock-body">
        <div className="mock-query">
          <span className="mock-label">TOPIC</span>
          <p>How do microplastics affect human health?</p>
        </div>

        <div className="mock-grid">
          <ul className="mock-steps">
            {STEPS.map((s, i) => {
              const state = i < active ? "done" : i === active && !done ? "now" : "todo";
              return (
                <li key={s} className={state}>
                  <span className="dot">{state === "done" ? "✓" : ""}</span>
                  {s}
                </li>
              );
            })}
          </ul>

          <div className="mock-report">
            <div className="mock-report-head">
              <span className="mock-label">REPORT</span>
              <span className={`score ${done ? "show" : ""}`}>Quality 8/10</span>
            </div>
            <div className="sk w60" />
            <div className="sk w100" />
            <div className="sk w90" />
            <div className="sk w75" />
            <div className="mock-chart">
              <span style={{ height: "40%" }} />
              <span style={{ height: "65%" }} />
              <span style={{ height: "50%" }} />
              <span style={{ height: "85%" }} />
              <span style={{ height: "70%" }} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Hero() {
  return (
    <section className="hero container" id="top">
      <div className="pill">
        <span className="pill-dot" /> Autonomous research assistant
      </div>
      <h1>
        Ask a question.
        <br />
        <em>Get the full picture.</em>
      </h1>
      <p className="lead">
        QueryMind searches the web, reads the sources, and writes a cited research
        report for you, then checks its own work before handing it over.
      </p>
      <div className="hero-cta">
        <Link to="/signup" className="btn">
  Start researching <span aria-hidden>→</span>
</Link>
        <a href="#how" className="btn btn-ghost">See how it works</a>
      </div>
      <ul className="hero-points">
        <li>Cited sources</li>
        <li>Charts & diagrams</li>
        <li>Self-reviewed</li>
      </ul>
      <Mockup />
    </section>
  );
}

function How() {
  return (
    <section className="section container" id="how">
      <p className="eyebrow">How it works</p>
      <h2>From question to report in four steps.</h2>
      <div className="how-grid">
        {HOW.map((h) => (
          <div className="how-card" key={h.n}>
            <span className="how-n">{h.n}</span>
            <h3>{h.title}</h3>
            <p>{h.text}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function Features() {
  return (
    <section className="section container" id="features">
      <p className="eyebrow">Features</p>
      <h2>Built for people who need answers, not tabs.</h2>
      <div className="feat-grid">
        {FEATURES.map((f) => (
          <div className="feat" key={f.title}>
            <span className="feat-bullet" />
            <h3>{f.title}</h3>
            <p>{f.text}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function ReportPreview() {
  return (
    <section className="section container" id="report">
      <div className="report-wrap">
        <div className="report-copy">
          <p className="eyebrow">Sample report</p>
          <h2>Structured, sourced, and ready to read.</h2>
          <p className="muted">
            Each report comes with a clear summary, organised sections, visuals,
            a quality critique, and a full list of sources.
          </p>
          <ul className="checks">
            <li>Executive summary up front</li>
            <li>Diagrams and charts inline</li>
            <li>Critic's feedback included</li>
            <li>Every source linked</li>
          </ul>
        </div>

        <div className="doc">
          <div className="doc-top">
            <span className="mock-label">REPORT.MD</span>
            <span className="score show">Quality 8/10</span>
          </div>
          <h4>Microplastics and Human Health</h4>
          <div className="sk w100" />
          <div className="sk w95" />
          <div className="sk w80" />
          <h5>Key findings</h5>
          <div className="sk w100" />
          <div className="sk w70" />
          <h5>Sources</h5>
          <div className="src"><span>[1]</span><div className="sk w60" /></div>
          <div className="src"><span>[2]</span><div className="sk w75" /></div>
          <div className="src"><span>[3]</span><div className="sk w50" /></div>
        </div>
      </div>
    </section>
  );
}

function CTA() {
  return (
    <section className="container" id="cta">
      <div className="cta">
        <h2>Stop opening twenty tabs.</h2>
        <p>Give QueryMind a topic and get a cited report back.</p>
        <Link to="/signup" className="btn btn-dark">
  Create your free account <span aria-hidden>→</span>
</Link>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="footer">
      <div className="container footer-inner">
        <Logo />
        <span className="muted small">© 2026 QueryMind. All rights reserved.</span>
      </div>
    </footer>
  );
}

function ProtectedRoute({ children }) {
  const [status, setStatus] = useState(() =>
    getToken() && getUser() ? "authorized" : "checking"
  );

  useEffect(() => {
    let active = true;

    authApi.getMe().then((user) => {
      if (!active) return;
      if (user) {
        setStatus("authorized");
      } else {
        setStatus("unauthorized");
        navigate("/signin", { replace: true });
      }
    });

    return () => {
      active = false;
    };
  }, []);

  if (status !== "authorized") return null;
  return children;
}

function Landing() {
  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <How />
        <Features />
        <ReportPreview />
        <CTA />
      </main>
      <Footer />
    </>
  );
}

export default function App() {
  const path = usePath();
  if (path === "/signin") return <Auth mode="signin" />;
  if (path === "/signup") return <Auth mode="signup" />;
  if (path === "/research") {
    return (
      <ProtectedRoute>
        <Research />
      </ProtectedRoute>
    );
  }
  return <Landing />;
}