"use client";

import { useState } from "react";

const apiPublic = process.env.NEXT_PUBLIC_API_ORIGIN || "http://127.0.0.1:8000";

function jsonHeaders(token: string): Record<string, string> {
  const h: Record<string, string> = { "Content-Type": "application/json" };
  if (token) h.Authorization = `Bearer ${token}`;
  return h;
}

function authHeaders(token: string): Record<string, string> {
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}

export default function Home() {
  const [slug, setSlug] = useState("demo-co");
  const [email, setEmail] = useState("you@company.com");
  const [password, setPassword] = useState("longpassword123");
  const [token, setToken] = useState("");
  const [msg, setMsg] = useState("");
  const [jobId, setJobId] = useState<string>("");

  async function register() {
    setMsg("Registering…");
    const r = await fetch("/api/v1/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        tenant_slug: slug,
        tenant_name: "Demo tenant",
        email,
        password,
      }),
    });
    const j = await r.json();
    if (!r.ok) {
      setMsg(JSON.stringify(j, null, 2));
      return;
    }
    setToken(j.access_token);
    setMsg("Registered. Run “Sample forecast” next.");
  }

  async function login() {
    setMsg("Logging in…");
    const r = await fetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tenant_slug: slug, email, password }),
    });
    const j = await r.json();
    if (!r.ok) {
      setMsg(JSON.stringify(j, null, 2));
      return;
    }
    setToken(j.access_token);
    setMsg("Logged in.");
  }

  async function sampleForecast() {
    if (!token) {
      setMsg("Register or login first.");
      return;
    }
    setMsg("Running sample forecast…");
    const r = await fetch("/api/v1/forecast/sample", {
      method: "POST",
      headers: jsonHeaders(token),
      body: JSON.stringify({ days_ahead: 14, history_days: 120 }),
    });
    const j = await r.json();
    setMsg(JSON.stringify(j, null, 2));
    if (j.job_id) setJobId(String(j.job_id));
  }

  async function fetchJob() {
    if (!token || !jobId) {
      setMsg("Need token and job id.");
      return;
    }
    const r = await fetch(`/api/v1/forecast/jobs/${jobId}`, { headers: authHeaders(token) });
    const j = await r.json();
    setMsg(JSON.stringify(j, null, 2));
  }

  async function listJobs() {
    if (!token) {
      setMsg("Register or login first.");
      return;
    }
    const r = await fetch("/api/v1/forecast/jobs?limit=5", { headers: authHeaders(token) });
    const j = await r.json();
    setMsg(JSON.stringify(j, null, 2));
  }

  return (
    <main style={{ fontFamily: "system-ui", maxWidth: 720, margin: "2rem auto", padding: 16 }}>
      <h1 style={{ marginTop: 0 }}>ChainMind — API smoke</h1>
      <p>
        Requests use Next rewrites to the API (see <code>web/next.config.mjs</code>, <code>API_ORIGIN</code>). OpenAPI
        lives on the API host:{" "}
        <a href={`${apiPublic}/docs`} target="_blank" rel="noreferrer">
          {apiPublic}/docs
        </a>
        .
      </p>

      <section style={{ display: "grid", gap: 10, marginBottom: 20 }}>
        <label>
          Tenant slug
          <input value={slug} onChange={(e) => setSlug(e.target.value)} style={{ width: "100%" }} />
        </label>
        <label>
          Email
          <input value={email} onChange={(e) => setEmail(e.target.value)} style={{ width: "100%" }} />
        </label>
        <label>
          Password (10+ chars)
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} style={{ width: "100%" }} />
        </label>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button type="button" onClick={register}>
            Register
          </button>
          <button type="button" onClick={login}>
            Login
          </button>
        </div>
      </section>

      <section style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 16 }}>
        <button type="button" onClick={sampleForecast}>
          Sample forecast
        </button>
        <button type="button" onClick={listJobs}>
          List jobs
        </button>
        <label style={{ display: "flex", gap: 6, alignItems: "center" }}>
          Job id
          <input value={jobId} onChange={(e) => setJobId(e.target.value)} style={{ width: 120 }} />
        </label>
        <button type="button" onClick={fetchJob}>
          Fetch job
        </button>
      </section>

      {token ? (
        <p style={{ wordBreak: "break-all" }}>
          <strong>Bearer (dev only):</strong> <code>{token.slice(0, 28)}…</code>
        </p>
      ) : null}

      <pre style={{ background: "#0f172a", color: "#e2e8f0", padding: 12, overflow: "auto", fontSize: 13 }}>{msg}</pre>
    </main>
  );
}
