

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";


export function getToken() {
  return localStorage.getItem("qm_token") || "";
}

export function setToken(token) {
  if (token) {
    localStorage.setItem("qm_token", token);
  } else {
    localStorage.removeItem("qm_token");
  }
}

export function getUser() {
  try {
    const raw = localStorage.getItem("qm_user");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function setUser(user) {
  if (user) {
    localStorage.setItem("qm_user", JSON.stringify(user));
  } else {
    localStorage.removeItem("qm_user");
  }
}

export function clearAuth() {
  localStorage.removeItem("qm_token");
  localStorage.removeItem("qm_user");
}

function authHeaders() {
  const token = getToken();
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

// ── Auth Endpoints ─────────────────────────────────────────────────────────────
export const authApi = {
  async register(email, password, fullName) {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email,
        password,
        full_name: fullName || null,
      }),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Registration failed.");
    }
    setToken(data.access_token);
    setUser(data.user);
    return data;
  },

  async login(email, password) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Invalid email or password.");
    }
    setToken(data.access_token);
    setUser(data.user);
    return data;
  },

  async getMe() {
    const token = getToken();
    if (!token) return null;
    try {
      const res = await fetch(`${API_BASE}/auth/me`, {
        headers: authHeaders(),
      });
      if (!res.ok) {
        clearAuth();
        return null;
      }
      const user = await res.json();
      setUser(user);
      return user;
    } catch {
      return null;
    }
  },
};

// ── Research Steps ─────────────────────────────────────────────────────────────
export const RESEARCH_STEPS = [
  { id: "planner", label: "Decomposing query into 3 orthogonal angles" },
  { id: "search", label: "Searching web and aggregating verified sources" },
  { id: "read", label: "Scraping full pages & semantic vector RAG retrieval" },
  { id: "write", label: "Synthesizing report, architecture diagrams & charts" },
  { id: "critic", label: "Reviewing quality, scoring, and verifying citations" },
];

// ── Research Endpoints ─────────────────────────────────────────────────────────
export const researchApi = {
  async validate(topic) {
    const res = await fetch(`${API_BASE}/research/validate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic }),
    });
    if (!res.ok) return { valid: true };
    return await res.json();
  },

  /**
   * Run research with real-time SSE streaming updates.
   * Calls onEvent callback whenever an agent finishes a step.
   */
  async streamResearch(topic, onEvent) {
    const token = getToken();
    const url = new URL(`${API_BASE}/research/stream`);
    url.searchParams.set("topic", topic);
    url.searchParams.set("save", "true");
    if (token) url.searchParams.set("token", token);

    const response = await fetch(url.toString(), {
      headers: { Accept: "text/event-stream" },
    });

    if (!response.ok) {
      if (response.status === 404 || response.status === 405) {
        return await this.runDirect(topic);
      }
      let data = {};
      try {
        data = await response.json();
      } catch {
        // Use the status-based message when the server did not return JSON.
      }
      throw new Error(data.detail || `Research request failed (${response.status}).`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";
    let finalResult = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop() || "";

      for (const block of lines) {
        if (!block.trim()) continue;
        let eventType = "message";
        let dataStr = "";

        for (const line of block.split("\n")) {
          if (line.startsWith("event:")) {
            eventType = line.replace("event:", "").trim();
          } else if (line.startsWith("data:")) {
            dataStr = line.replace("data:", "").trim();
          }
        }

        if (dataStr) {
          let data;
          try {
            data = JSON.parse(dataStr);
          } catch (e) {
            console.error("Failed to parse SSE line:", e);
            continue;
          }

          if (eventType === "step") {
            onEvent?.({ type: "step", ...data });
          } else if (eventType === "complete") {
            finalResult = data;
            onEvent?.({ type: "complete", ...data });
          } else if (eventType === "error") {
            throw new Error(data.error || "Streaming error");
          }
        }
      }
    }

    if (!finalResult) {
      throw new Error("Research finished without returning final report.");
    }

    return finalResult;
  },

  async runDirect(topic) {
    const res = await fetch(`${API_BASE}/research`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ topic, save_to_history: true }),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Research pipeline failed.");
    }
    return data;
  },

  async getReports() {
    const res = await fetch(`${API_BASE}/reports`, {
      headers: authHeaders(),
    });
    if (!res.ok) return [];
    return await res.json();
  },

  async getReport(id) {
    const res = await fetch(`${API_BASE}/reports/${id}`, {
      headers: authHeaders(),
    });
    if (!res.ok) {
      throw new Error("Report not found.");
    }
    return await res.json();
  },

  async deleteReport(id) {
    const res = await fetch(`${API_BASE}/reports/${id}`, {
      method: "DELETE",
      headers: authHeaders(),
    });
    return res.ok;
  },
};
