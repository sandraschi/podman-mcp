import { useCallback, useEffect, useRef, useState } from "react";
import { API_BASE } from "@/lib/api";
import { getLlmProviders, type LlmProvider } from "@/common/api";
import { Bot, User, Send, StopCircle, Download, Sparkles, Settings2, RefreshCw, Cpu, ChevronDown, ChevronRight, CheckCircle2, XCircle } from "lucide-react";

type Role = "user" | "assistant";
type Personality = { id: string; name: string; prompt: string };
interface ToolResultEvent { tool: string; result: { success: boolean; tool: string; params: Record<string, unknown>; result?: string; error?: string; timing_ms: number } }
interface Message { role: Role; content: string; timestamp: number; toolCalls?: ToolCallCard[] }
interface ToolCallCard { nl_name: string; tool: string; result: ToolResultEvent["result"] | null }

const PERSONALITIES: Personality[] = [
  { id: "expert", name: "Podman Expert", prompt: "You are a senior Podman/SRE engineer. Answer concisely with practical commands and best practices." },
  { id: "sre", name: "SRE", prompt: "You are an SRE focused on reliability. Frame answers around monitoring, resource limits, and failure modes." },
  { id: "beginner", name: "Beginner", prompt: "You are a friendly Podman tutor. Explain concepts simply, no jargon." },
];

const DEFAULT_ENDPOINTS: Record<string, string> = {
  ollama: "http://127.0.0.1:11434",
  lmstudio: "http://127.0.0.1:1234",
};

function fmt(ts: number) { return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }); }

export function Chat() {
  const [messages, setMessages] = useState<Message[]>(() => { try { return JSON.parse(localStorage.getItem("podman-chat") || "[]"); } catch { return []; } });
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [abort, setAbort] = useState<AbortController | null>(null);
  const [personality, setPersonality] = useState(() => localStorage.getItem("podman-chat-persona") || "expert");
  const [provider, setProvider] = useState(() => localStorage.getItem("podman-chat-provider") || "ollama");
  const [model, setModel] = useState(() => localStorage.getItem("podman-chat-model") || "llama3.2");
  const [endpoint, setEndpoint] = useState(() => localStorage.getItem("podman-chat-endpoint") || "http://127.0.0.1:11434");
  const [showSettings, setShowSettings] = useState(false);
  const [providers, setProviders] = useState<LlmProvider[]>([]);
  const [loadingProviders, setLoadingProviders] = useState(false);
  const [toolMode, setToolMode] = useState(() => localStorage.getItem("podman-chat-tool-mode") === "true");
  const [expandedCards, setExpandedCards] = useState<Set<number>>(new Set());
  const bottomRef = useRef<HTMLDivElement>(null);
  const persona = PERSONALITIES.find((p) => p.id === personality) ?? PERSONALITIES[0];

  useEffect(() => { localStorage.setItem("podman-chat", JSON.stringify(messages.slice(-100))); }, [messages]);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  useEffect(() => {
    if (!showSettings) return;
    let cancelled = false;
    (async () => {
      setLoadingProviders(true);
      try {
        const list = await getLlmProviders(false);
        if (cancelled) return;
        setProviders(list);
        if (list.length > 0) {
          const match = list.find((p) => p.type === provider);
          if (match) {
            if (!model || !match.models.includes(model)) {
              if (match.models[0]) setModel(match.models[0]);
            }
            setEndpoint(match.base_url);
          }
        }
      } catch { /* non-fatal */ }
      finally { if (!cancelled) setLoadingProviders(false); }
    })();
    return () => { cancelled = true; };
  }, [showSettings]);

  const refreshProviders = useCallback(async () => {
    setLoadingProviders(true);
    try {
      const list = await getLlmProviders(true);
      setProviders(list);
      if (list.length > 0) {
        const match = list.find((p) => p.type === provider);
        if (match) {
          setEndpoint(match.base_url);
          if (match.models[0]) setModel(match.models[0]);
        }
      }
    } catch { /* non-fatal */ }
    finally { setLoadingProviders(false); }
  }, [provider]);

  const onProviderChange = useCallback((next: string) => {
    setProvider(next);
    localStorage.setItem("podman-chat-provider", next);
    const match = providers.find((p) => p.type === next);
    if (match) {
      setEndpoint(match.base_url);
      localStorage.setItem("podman-chat-endpoint", match.base_url);
      if (match.models[0]) {
        setModel(match.models[0]);
        localStorage.setItem("podman-chat-model", match.models[0]);
      }
    } else {
      const fallback = DEFAULT_ENDPOINTS[next] ?? DEFAULT_ENDPOINTS.ollama;
      setEndpoint(fallback);
      localStorage.setItem("podman-chat-endpoint", fallback);
    }
  }, [providers]);

  const onModelChange = useCallback((next: string) => {
    setModel(next);
    localStorage.setItem("podman-chat-model", next);
  }, []);

  const activeProvider = providers.find((p) => p.type === provider);
  const modelOptions = activeProvider?.models ?? [];

  const toggleToolMode = useCallback(() => {
    setToolMode((prev) => {
      const next = !prev;
      localStorage.setItem("podman-chat-tool-mode", String(next));
      return next;
    });
  }, []);

  const toggleCard = useCallback((idx: number) => {
    setExpandedCards((prev) => {
      const next = new Set(prev);
      if (next.has(idx)) next.delete(idx); else next.add(idx);
      return next;
    });
  }, []);

  const send = useCallback(async () => {
    const q = input.trim();
    if (!q || streaming) return;
    setInput("");
    const userMsg: Message = { role: "user", content: q, timestamp: Date.now() };
    const botMsg: Message = { role: "assistant", content: "", timestamp: Date.now(), toolCalls: [] };
    setMessages((prev) => [...prev, userMsg, botMsg]);
    setStreaming(true);
    const history = messages.slice(-20).map((m) => ({ role: m.role, content: m.content }));
    const ctrl = new AbortController();
    setAbort(ctrl);
    const body: Record<string, unknown> = { query: q, provider, model, endpoint, stream: true, system_prompt: persona.prompt, history };
    if (toolMode) body.mode = "agentic";
    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: ctrl.signal,
      });
      const reader = res.body?.getReader();
      if (!reader) throw new Error("No response body");
      const dec = new TextDecoder();
      let buf = "";
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += dec.decode(value, { stream: !done });
        const lines = buf.split("\n\n");
        buf = lines.pop() ?? "";
        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || !trimmed.startsWith("data: ")) continue;
          const raw = trimmed.slice(6);
          try {
            const event = JSON.parse(raw);
            if (event.type === "text") {
              setMessages((prev) => { const c = [...prev]; const l = c[c.length - 1]; if (l?.role === "assistant") c[c.length - 1] = { ...l, content: l.content + event.content }; return c; });
            } else if (event.type === "tool_call") {
              setMessages((prev) => { const c = [...prev]; const l = c[c.length - 1]; if (l?.role === "assistant" && l.toolCalls) l.toolCalls = [...l.toolCalls, { nl_name: event.nl_name, tool: event.tool, result: null }]; return c; });
            } else if (event.type === "tool_result") {
              setMessages((prev) => { const c = [...prev]; const l = c[c.length - 1]; if (l?.role === "assistant" && l.toolCalls) { const i = l.toolCalls.findIndex((tc) => tc.tool === event.tool && tc.result === null); if (i >= 0) l.toolCalls[i] = { ...l.toolCalls[i], result: event.result }; } return c; });
            } else if (event.type === "done") {
              break;
            }
          } catch { /* skip malformed */ }
        }
      }
    } catch (e: any) {
      if (e.name !== "AbortError") setMessages((prev) => { const c = [...prev]; const l = c[c.length - 1]; if (l?.role === "assistant") c[c.length - 1] = { ...l, content: l.content || `Error: ${e.message}` }; return c; });
    } finally { setStreaming(false); setAbort(null); }
  }, [input, streaming, messages, provider, model, endpoint, personality, persona, toolMode]);

  const stop = () => { abort?.abort(); setStreaming(false); };

  const exportChat = (fmt: "md" | "json") => {
    let c = fmt === "json" ? JSON.stringify(messages, null, 2) : messages.map((m) => `### ${m.role === "user" ? "User" : persona.name}\n${m.content}\n`).join("\n");
    const b = new Blob([c], { type: "text/plain" }); const u = URL.createObjectURL(b);
    const a = document.createElement("a"); a.href = u; a.download = `podman-chat.${fmt}`; a.click(); URL.revokeObjectURL(u);
  };

  const suggested = ["List all running containers", "Show me container logs for nginx", "Check Podman CLI health", "Clean up unused images and volumes"];

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col space-y-3" data-testid="chat-page">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-3">
          <h2 className="text-2xl font-bold tracking-tight text-white">AI Command</h2>
            <div className="flex gap-1 bg-slate-900 rounded-lg p-1 border border-slate-800" data-testid="personality-select">
              {PERSONALITIES.map((p) => (
              <button key={p.id} type="button" onClick={() => { setPersonality(p.id); localStorage.setItem("podman-chat-persona", p.id); }}
                className={`px-3 py-1 text-xs rounded-md transition-colors ${personality === p.id ? "bg-blue-600 text-white" : "text-slate-400 hover:text-white"}`}>{p.name}</button>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button type="button" onClick={toggleToolMode}
            className={`p-1.5 rounded-md ${toolMode ? "bg-blue-600/30 text-blue-400 border border-blue-500/30" : "text-slate-400 hover:text-white hover:bg-slate-800"}`}
            title={toolMode ? "Tool execution mode ON — queries run Podman tools" : "Tool execution mode OFF"}>
            <Cpu className="h-4 w-4" />
          </button>
          <button type="button" onClick={() => setShowSettings(!showSettings)} className="p-1.5 rounded-md text-slate-400 hover:text-white hover:bg-slate-800" title="Settings"><Settings2 className="h-4 w-4" /></button>
          <button type="button" data-testid="chat-export" onClick={() => exportChat("md")} className="p-1.5 rounded-md text-slate-400 hover:text-white hover:bg-slate-800" title="Export MD"><Download className="h-4 w-4" /></button>
          <button type="button" data-testid="chat-clear" onClick={() => { setMessages([]); localStorage.removeItem("podman-chat"); }} className="text-xs text-slate-400 hover:text-white px-2 py-1 rounded-md hover:bg-slate-800">Clear</button>
        </div>
      </div>

      {showSettings && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-3 flex flex-wrap gap-3 items-center text-sm">
          <div>
            <label className="text-xs text-slate-500 block">Provider</label>
            <div className="relative">
              <select value={provider} onChange={(e) => onProviderChange(e.target.value)}
                className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-200 text-xs min-w-[9rem] appearance-none pr-6">
                {providers.length === 0 ? (
                  <option value="ollama">Ollama</option>
                ) : providers.map((p) => (
                  <option key={p.type} value={p.type}>{p.type}</option>
                ))}
              </select>
              {activeProvider && (
                <span className={`absolute right-1.5 top-1/2 -translate-y-1/2 h-2 w-2 rounded-full ${activeProvider.reachable ? "bg-green-500" : "bg-red-500"}`} />
              )}
            </div>
          </div>
          {modelOptions.length > 0 && (
            <div>
              <label className="text-xs text-slate-500 block">Model</label>
              <select value={model} onChange={(e) => onModelChange(e.target.value)}
                className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-200 text-xs min-w-[9rem]">
                {modelOptions.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>
          )}
          {modelOptions.length === 0 && (
            <div>
              <label className="text-xs text-slate-500 block">Model</label>
              <input value={model} onChange={(e) => onModelChange(e.target.value)}
                className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-200 text-xs w-28 font-mono" />
            </div>
          )}
          <div>
            <label className="text-xs text-slate-500 block">Endpoint</label>
            <input value={endpoint} onChange={(e) => { setEndpoint(e.target.value); localStorage.setItem("podman-chat-endpoint", e.target.value); }}
              className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-200 text-xs w-44 font-mono" />
          </div>
          <button type="button" onClick={refreshProviders} disabled={loadingProviders}
            className="mt-4 p-1.5 rounded-md text-slate-400 hover:text-white hover:bg-slate-800 self-end">
            <RefreshCw className={`h-4 w-4 ${loadingProviders ? "animate-spin" : ""}`} />
          </button>
        </div>
      )}

      <div className="flex-1 overflow-y-auto space-y-3 pr-1">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
            <Bot className="h-12 w-12 text-slate-700" />
            <p className="text-slate-500 text-sm max-w-md">Ask me about Podman — containers, images, volumes, compose, or daemon issues.</p>
            <div className="flex flex-wrap gap-2 justify-center">
              {suggested.map((p) => (
                <button key={p} type="button" onClick={() => setInput(p)}
                  className="px-3 py-1.5 text-xs bg-slate-800/60 hover:bg-slate-700/60 text-slate-300 rounded-lg border border-slate-700/50">
                  <Sparkles className="h-3 w-3 inline mr-1 text-blue-400" />{p}
                </button>
              ))}
            </div>
          </div>
        ) : messages.map((msg, i) => (
          <div key={i} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}>
            {msg.role !== "user" && <div className="h-8 w-8 rounded-full bg-blue-900/50 flex items-center justify-center border border-blue-800/50 shrink-0"><Bot className="h-4 w-4 text-blue-400" /></div>}
            <div className={`max-w-[80%] space-y-1 ${msg.role === "user" ? "items-end" : ""}`}>
              <div className="flex items-center gap-2"><span className="text-xs text-slate-500">{msg.role === "user" ? "You" : persona.name}</span><span className="text-xs text-slate-600">{fmt(msg.timestamp)}</span></div>
              {msg.toolCalls && msg.toolCalls.length > 0 && (
                <div className="space-y-2 mb-2">
                  {msg.toolCalls.map((tc, j) => (
                    <div key={j} className="bg-slate-900/80 border border-slate-700/60 rounded-lg overflow-hidden text-xs">
                      <button type="button" onClick={() => toggleCard(i * 100 + j)} className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-slate-800/50">
                        {expandedCards.has(i * 100 + j) ? <ChevronDown className="h-3.5 w-3.5 shrink-0 text-slate-400" /> : <ChevronRight className="h-3.5 w-3.5 shrink-0 text-slate-400" />}
                        {tc.result ? (
                          tc.result.success ? <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-green-500" /> : <XCircle className="h-3.5 w-3.5 shrink-0 text-red-500" />
                        ) : <span className="h-3.5 w-3.5 shrink-0 rounded-full bg-blue-500/50 animate-pulse" />}
                        <span className="text-slate-200 font-medium">{tc.nl_name}</span>
                        {tc.result && <span className="text-slate-500 ml-auto">{tc.result.timing_ms}ms</span>}
                      </button>
                      {expandedCards.has(i * 100 + j) && tc.result && (
                        <div className="px-3 pb-2 space-y-1.5 text-slate-400 font-mono border-t border-slate-800 pt-1.5">
                          <div><span className="text-slate-500">tool: </span>{tc.result.tool}</div>
                          <div><span className="text-slate-500">params: </span>{JSON.stringify(tc.result.params)}</div>
                          <div><span className="text-slate-500">timing: </span>{tc.result.timing_ms}ms</div>
                          {tc.result.success ? (
                            <div className="text-emerald-400/80 break-all max-h-32 overflow-y-auto bg-slate-950/50 rounded p-1.5">
                              {tc.result.result?.slice(0, 1000)}
                            </div>
                          ) : (
                            <div className="text-red-400/80">{tc.result.error}</div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
              <div className={`text-sm rounded-xl px-4 py-2.5 ${msg.role === "user" ? "bg-blue-600/20 text-blue-100 border border-blue-700/30" : "bg-slate-800/60 text-slate-200 border border-slate-700/50"}`}>
                <div className="whitespace-pre-wrap break-words">{msg.content || (i === messages.length - 1 && streaming ? <span className="animate-pulse">...</span> : "")}</div>
              </div>
            </div>
            {msg.role === "user" && <div className="h-8 w-8 rounded-full bg-slate-800 flex items-center justify-center border border-slate-700 shrink-0"><User className="h-4 w-4 text-slate-400" /></div>}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="flex gap-2 items-end bg-slate-900/80 border border-slate-800 rounded-xl p-2">
        <textarea value={input} onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }}
          placeholder="Ask about Podman..." rows={1} data-testid="chat-input"
          className="flex-1 bg-transparent border-0 outline-none text-sm text-slate-200 placeholder-slate-500 resize-none max-h-32 py-1.5 px-2" />
        {streaming ? (
          <button type="button" onClick={stop} className="p-2 rounded-lg bg-red-600/20 hover:bg-red-600/40 text-red-400"><StopCircle className="h-5 w-5" /></button>
        ) : (
          <button type="button" data-testid="chat-send" onClick={send} disabled={!input.trim()} className="p-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-30 text-white"><Send className="h-5 w-5" /></button>
        )}
      </div>
    </div>
  );
}
