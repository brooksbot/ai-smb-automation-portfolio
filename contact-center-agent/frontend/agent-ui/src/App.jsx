import { useMemo, useState } from "react";

const API_URL = "http://localhost:8000/triage";
const SUMMARIZE_URL = "http://localhost:8000/summarize";

const GOLDEN_SET = [
  { id: "c1", transcript: "I need a refund for reservation ABC123", expected: "refund_request" },
  { id: "c2", transcript: "Why was I charged twice? My invoice says $50.", expected: "billing_question" },
  { id: "c3", transcript: "I forgot my password and can't log in.", expected: "password_reset" },
  { id: "c4", transcript: "Cancel my subscription immediately.", expected: "cancel_service" },
  { id: "c5", transcript: "Can we reschedule my appointment for Tuesday?", expected: "appointment_scheduling" },
  { id: "c6", transcript: "My package hasn't arrived yet, where is it?", expected: "shipment_status" },
  { id: "c7", transcript: "The app keeps crashing with Error 500.", expected: "technical_issue" },
  { id: "c8", transcript: "Your service is terrible, I want a manager.", expected: "complaint" },
  { id: "c9", transcript: "Someone hacked my account and changed the email.", expected: "fraud_account_takeover" },
  { id: "c10", transcript: "I am calling my lawyer to sue you for this.", expected: "legal_threat" }
];

export default function App() {
  const [activeTab, setActiveTab] = useState("console");
  const [transcript, setTranscript] = useState(GOLDEN_SET[0].transcript);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  
  // Eval & Summary State
  const [evalResults, setEvalResults] = useState([]);
  const [isEvalRunning, setIsEvalRunning] = useState(false);
  const [summary, setSummary] = useState("");
  const [isSummarizing, setIsSummarizing] = useState(false);

  async function runTriage(text) {
    setLoading(true);
    try {
      const resp = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transcript: text, metadata: { channel: "ui-test" } })
      });
      const json = await resp.json();
      setResult(json);
      return json;
    } catch (e) {
      console.error("Triage Error:", e);
    } finally {
      setLoading(false);
    }
  }

  async function runFullEval() {
    setIsEvalRunning(true);
    setSummary(""); // Clear old summary
    const results = [];
    for (const item of GOLDEN_SET) {
      const start = Date.now();
      const pred = await runTriage(item.transcript);
      results.push({
        ...item,
        predicted: pred?.intent || "error",
        isCorrect: pred?.intent === item.expected,
        latency: Date.now() - start
      });
      setEvalResults([...results]);
    }
    setIsEvalRunning(false);
  }

  async function generateSummary() {
    setIsSummarizing(true);
    try {
      const resp = await fetch(SUMMARIZE_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ results: evalResults })
      });
      const json = await resp.json();
      setSummary(json.summary);
    } catch (e) {
      console.error("Summary Error:", e);
    } finally {
      setIsSummarizing(false);
    }
  }

  const accuracy = (evalResults.filter(r => r.isCorrect).length / evalResults.length * 100) || 0;

  
  
  return (
    <div style={{ maxWidth: 1000, margin: "40px auto", padding: 20, fontFamily: "sans-serif", color: "var(--fg)" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1>Agent Intelligence Dashboard</h1>
        <div style={{ display: "flex", gap: 10 }}>
          <button
            onClick={() => setActiveTab("console")}
            style={{
              padding: "8px 16px",
              background: activeTab === "console" ? "var(--primary)" : "var(--btn-bg)",
              color: activeTab === "console" ? "var(--primary-fg)" : "var(--fg)",
              border: "1px solid var(--btn-border)",
              cursor: "pointer",
              borderRadius: 6,
              fontWeight: "600"
            }}
          >
            Console
          </button>
          <button
            onClick={() => setActiveTab("eval")}
            style={{
              padding: "8px 16px",
              background: activeTab === "eval" ? "var(--primary)" : "var(--btn-bg)",
              color: activeTab === "eval" ? "var(--primary-fg)" : "var(--fg)",
              border: "1px solid var(--btn-border)",
              cursor: "pointer",
              borderRadius: 6,
              fontWeight: "600"
            }}
          >
            Evaluation
          </button>
        </div>
      </div>

      {activeTab === "console" ? (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginTop: 20 }}>
          <div style={{ border: "1px solid var(--border)", padding: 20, borderRadius: 10, background: "var(--card)" }}>
            <h3>Input</h3>
            <textarea
              value={transcript}
              onChange={(e) => setTranscript(e.target.value)}
              style={{ width: "100%", height: 150, padding: 10, borderRadius: 8, border: "1px solid var(--border)", background: "var(--card)", color: "var(--fg)" }}
            />
            <button
              onClick={() => runTriage(transcript)}
              disabled={loading}
              style={{ marginTop: 10, padding: "10px 20px", cursor: "pointer", background: "var(--primary)", color: "var(--primary-fg)", border: "none", borderRadius: 6, fontWeight: "600" }}
            >
              {loading ? "Processing..." : "Run Triage"}
            </button>
          </div>
          <div style={{ border: "1px solid var(--border)", padding: 20, borderRadius: 10, background: "var(--card)" }}>
            <h3>Output</h3>
            {result ? (
              <pre style={{ fontSize: 12, whiteSpace: "pre-wrap", color: "var(--fg)" }}>{JSON.stringify(result, null, 2)}</pre>
            ) : <p style={{ color: "var(--fg)" }}>No results yet.</p>}
          </div>
        </div>
      ) : (
        <div style={{ marginTop: 20 }}>
          <div style={{ display: "flex", justifyContent: "space-between", background: "var(--card)", padding: 20, borderRadius: 10, border: "1px solid var(--border)" }}>
            <div>
              <h2 style={{ margin: 0 }}>Accuracy: {accuracy.toFixed(1)}%</h2>
              <p style={{ margin: 0, color: "var(--fg)", opacity: 0.6 }}>Tested on {evalResults.length} / {GOLDEN_SET.length} samples</p>
            </div>
            <button
              onClick={runFullEval}
              disabled={isEvalRunning}
              style={{ padding: "10px 30px", background: "var(--primary)", color: "var(--primary-fg)", border: "none", borderRadius: 6, cursor: "pointer", fontWeight: "600" }}
            >
              {isEvalRunning ? "Running Eval..." : "Start Batch Evaluation"}
            </button>
          </div>

          {evalResults.length === 10 && (
            <div style={{ marginTop: 20, padding: 20, background: "var(--info-bg)", borderRadius: 10, border: "1px solid var(--info-border)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <h3 style={{ margin: 0, color: "var(--info-fg)" }}>📊 Executive Insight Brief</h3>
                <button
                  onClick={generateSummary}
                  disabled={isSummarizing}
                  style={{ padding: "8px 16px", cursor: "pointer", borderRadius: 6, border: "1px solid var(--info-border)", background: "var(--card)", color: "var(--info-fg)", fontWeight: "600", boxShadow: "0 1px 2px rgba(0,0,0,0.05)" }}
                >
                  {isSummarizing ? "Analyzing..." : "Generate Summary"}
                </button>
              </div>
              {summary && (
                <div style={{ marginTop: 15, whiteSpace: "pre-wrap", fontSize: 14, lineHeight: "1.6", color: "var(--fg)" }}>
                  {summary}
                </div>
              )}
            </div>
          )}

          <table style={{ width: "100%", marginTop: 20, borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ textAlign: "left", borderBottom: "2px solid var(--border)" }}>
                <th style={{ padding: 10 }}>Transcript</th>
                <th>Expected</th>
                <th>Predicted</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {evalResults.map((res, i) => (
                <tr key={i} style={{ borderBottom: "1px solid var(--border)" }}>
                  <td style={{ padding: 10, fontSize: 12 }}>{res.transcript}</td>
                  <td style={{ fontSize: 12, fontWeight: "bold" }}>{res.expected}</td>
                  <td style={{ fontSize: 12, color: res.isCorrect ? "#22c55e" : "#ef4444" }}>{res.predicted}</td>
                  <td>{res.isCorrect ? "✅" : "❌"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}