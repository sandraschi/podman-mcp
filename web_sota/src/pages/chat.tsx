import {
  Bot,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Cpu,
  Download,
  RefreshCw,
  Send,
  Settings2,
  Sparkles,
  StopCircle,
  User,
  XCircle,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { API_BASE } from "@/lib/api";
import { useLlmStore } from "@/store/llm";

type Role = "user" | "assistant";
type Personality = { id: string; name: string; prompt: string };
interface ToolResultEvent {
  tool: string;
  result: {
    success: boolean;
    tool: string;
    params: Record<string, unknown>;
    result?: string;
    error?: string;
    timing_ms: number;
  };
}
interface Message {
  role: Role;
  content: string;
  timestamp: number;
  toolCalls?: ToolCallCard[];
}
interface ToolCallCard {
  nl_name: string;
  tool: string;
  result: ToolResultEvent["result"] | null;
}

const PERSONALITIES: Personality[] = [
  {
    id: "expert",
    name: "Podman Expert",
    prompt:
      "You are a senior Podman/SRE engineer. Answer concisely with practical commands and best practices.",
  },
  {
    id: "sre",
    name: "SRE",
    prompt:
      "You are an SRE focused on reliability. Frame answers around monitoring, resource limits, and failure modes.",
  },
  {
    id: "beginner",
    name: "Beginner",
    prompt: "You are a friendly Podman tutor. Explain concepts simply, no jargon.",
  },
  {
    id: "operator",
    name: "Operator",
    prompt:
      "You are a Podman operator focused on compose stacks, backups, and migrations. Prefer exact CLI steps in order.",
  },
  { id: "custom", name: "Custom", prompt: "" },
];

function fmt(ts: number) {
  return new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function Chat() {
  const [messages, setMessages] = useState<Message[]>(() => {
    try {
      return JSON.parse(localStorage.getItem("podman-chat") || "[]");
    } catch {
      return [];
    }
  });
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [abort, setAbort] = useState<AbortController | null>(null);
  const [personality, setPersonality] = [
    useLlmStore((s) => s.personality),
    useLlmStore((s) => s.setPersonality),
  ];
  const [provider] = [useLlmStore((s) => s.provider)];
  const [model] = [useLlmStore((s) => s.model)];
  const [customPrompt, setCustomPrompt] = [
    useLlmStore((s) => s.customPrompt),
    useLlmStore((s) => s.setCustomPrompt),
  ];
  const [endpoint, setEndpoint] = [
    useLlmStore((s) => s.endpoint),
    useLlmStore((s) => s.setEndpoint),
  ];
  const [showSettings, setShowSettings] = useState(false);
  const [providers] = [useLlmStore((s) => s.providers)];
  const [loadingProviders] = [useLlmStore((s) => s.loadingProviders)];
  const [gpuDetected] = [useLlmStore((s) => s.gpuDetected)];
  const [toolMode, setToolMode] = useState(
    () => localStorage.getItem("podman-chat-tool-mode") === "true",
  );
  const [expandedCards, setExpandedCards] = useState<Set<number>>(new Set());
  const [chatSkills, setChatSkills] = useState<string[]>([]);
  const [skillPreprompt, setSkillPreprompt] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const personaBase =
    personality === "custom"
      ? {
          id: "custom",
          name: "Custom",
          prompt: customPrompt || "You are a helpful Podman assistant.",
        }
      : (PERSONALITIES.find((p) => p.id === personality) ?? PERSONALITIES[0]);
  // Skill-first composition: server skill preprompt + selected personality.
  const persona = {
    ...personaBase,
    prompt: [skillPreprompt, personaBase.prompt].filter(Boolean).join("\n\n"),
  };

  useEffect(() => {
    localStorage.setItem("podman-chat", JSON.stringify(messages.slice(-100)));
  }, [messages]);
  // biome-ignore lint/correctness/useExhaustiveDependencies: messages dep intentionally re-runs scroll on new chat lines
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (!showSettings) return;
    useLlmStore.getState().ensureProviders();
  }, [showSettings]);

  useEffect(() => {
    useLlmStore.getState().detectGpu();
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/api/skills`);
        if (!res.ok || cancelled) return;
        const data = await res.json();
        if (!cancelled) {
          setChatSkills(data.skills ?? []);
          setSkillPreprompt(data.system_preprompt ?? "");
        }
      } catch {
        /* skills stay empty: chat works without them */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const refreshProviders = useCallback(async () => {
    await useLlmStore.getState().refreshProviders();
  }, []);

  const onProviderChange = useCallback((next: string) => {
    useLlmStore.getState().setProvider(next);
  }, []);

  const onModelChange = useCallback((next: string) => {
    useLlmStore.getState().setModel(next);
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
      if (next.has(idx)) next.delete(idx);
      else next.add(idx);
      return next;
    });
  }, []);

  const send = useCallback(async () => {
    const q = input.trim();
    if (!q || streaming) return;
    setInput("");
    const userMsg: Message = { role: "user", content: q, timestamp: Date.now() };
    const botMsg: Message = {
      role: "assistant",
      content: "",
      timestamp: Date.now(),
      toolCalls: [],
    };
    setMessages((prev) => [...prev, userMsg, botMsg]);
    setStreaming(true);
    const history = messages.slice(-20).map((m) => ({ role: m.role, content: m.content }));
    const ctrl = new AbortController();
    setAbort(ctrl);
    const body: Record<string, unknown> = {
      query: q,
      provider,
      model,
      endpoint,
      stream: true,
      system_prompt: persona.prompt,
      history,
    };
    if (toolMode) body.mode = "agentic";
    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
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
          if (!trimmed?.startsWith("data: ")) continue;
          const raw = trimmed.slice(6);
          try {
            const event = JSON.parse(raw);
            if (event.type === "text") {
              setMessages((prev) => {
                const c = [...prev];
                const l = c[c.length - 1];
                if (l?.role === "assistant")
                  c[c.length - 1] = { ...l, content: l.content + event.content };
                return c;
              });
            } else if (event.type === "tool_call") {
              setMessages((prev) => {
                const c = [...prev];
                const l = c[c.length - 1];
                if (l?.role === "assistant" && l.toolCalls)
                  l.toolCalls = [
                    ...l.toolCalls,
                    { nl_name: event.nl_name, tool: event.tool, result: null },
                  ];
                return c;
              });
            } else if (event.type === "tool_result") {
              setMessages((prev) => {
                const c = [...prev];
                const l = c[c.length - 1];
                if (l?.role === "assistant" && l.toolCalls) {
                  const i = l.toolCalls.findIndex(
                    (tc) => tc.tool === event.tool && tc.result === null,
                  );
                  if (i >= 0) l.toolCalls[i] = { ...l.toolCalls[i], result: event.result };
                }
                return c;
              });
            } else if (event.type === "done") {
              break;
            }
          } catch {
            /* skip malformed */
          }
        }
      }
    } catch (e: unknown) {
      const errName = e instanceof Error ? e.name : "unknown";
      const errMsg = e instanceof Error ? e.message : String(e);
      if (errName !== "AbortError")
        setMessages((prev) => {
          const c = [...prev];
          const l = c[c.length - 1];
          if (l?.role === "assistant")
            c[c.length - 1] = { ...l, content: l.content || `Error: ${errMsg}` };
          return c;
        });
    } finally {
      setStreaming(false);
      setAbort(null);
    }
  }, [input, streaming, messages, provider, model, endpoint, persona.prompt, toolMode]);

  const stop = () => {
    abort?.abort();
    setStreaming(false);
  };

  const exportChat = (fmt: "md" | "json" | "txt") => {
    const c =
      fmt === "json"
        ? JSON.stringify(messages, null, 2)
        : fmt === "txt"
          ? messages
              .map((m) => `${m.role === "user" ? "User" : persona.name}: ${m.content}`)
              .join("\n")
          : messages
              .map((m) => `### ${m.role === "user" ? "User" : persona.name}\n${m.content}\n`)
              .join("\n");
    const b = new Blob([c], { type: "text/plain" });
    const u = URL.createObjectURL(b);
    const a = document.createElement("a");
    a.href = u;
    a.download = `podman-chat.${fmt}`;
    a.click();
    URL.revokeObjectURL(u);
  };

  const suggested = [
    "List all running containers",
    "Show me container logs for nginx",
    "Check Podman CLI health",
    "Clean up unused images and volumes",
    "Back up the pgdata volume before upgrading",
    "Is my compose file Podman-compatible?",
  ];

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col space-y-3" data-testid="chat-page">
      <div
        className="flex items-center justify-between flex-wrap gap-2"
        data-testid="chat-controls"
      >
        <div className="flex items-center gap-3">
          <h2 className="text-2xl font-bold tracking-tight text-white">AI Command</h2>
          <div
            className="flex gap-1 bg-slate-900 rounded-lg p-1 border border-slate-800"
            data-testid="personality-select"
          >
            {PERSONALITIES.map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => {
                  setPersonality(p.id);
                  localStorage.setItem("podman-chat-persona", p.id);
                }}
                className={`px-3 py-1 text-xs rounded-md transition-colors ${personality === p.id ? "bg-blue-600 text-white" : "text-slate-400 hover:text-white"}`}
              >
                {p.name}
              </button>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span data-testid="chat-llm-status" className="text-xs text-slate-500 font-mono">
            {provider}/{model}
            {gpuDetected ? " · GPU" : ""}
          </span>
          <button
            type="button"
            onClick={toggleToolMode}
            className={`p-1.5 rounded-md ${toolMode ? "bg-blue-600/30 text-blue-400 border border-blue-500/30" : "text-slate-400 hover:text-white hover:bg-slate-800"}`}
            title={
              toolMode
                ? "Tool execution mode ON — queries run Podman tools"
                : "Tool execution mode OFF"
            }
          >
            <Cpu className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={() => setShowSettings(!showSettings)}
            className="p-1.5 rounded-md text-slate-400 hover:text-white hover:bg-slate-800"
            title="Settings"
          >
            <Settings2 className="h-4 w-4" />
          </button>
          <button
            type="button"
            data-testid="chat-export"
            onClick={() => exportChat("txt")}
            disabled={messages.length === 0}
            className="p-1.5 rounded-md text-slate-400 hover:text-white hover:bg-slate-800 disabled:opacity-40"
            title="Export TXT"
          >
            <Download className="h-4 w-4" />
          </button>
          <button
            type="button"
            data-testid="chat-clear"
            onClick={() => {
              setMessages([]);
              localStorage.removeItem("podman-chat");
            }}
            disabled={messages.length === 0}
            className="text-xs text-slate-400 hover:text-white px-2 py-1 rounded-md hover:bg-slate-800 disabled:opacity-40"
          >
            Clear
          </button>
        </div>
      </div>
      {personality === "custom" && (
        <input
          value={customPrompt}
          onChange={(e) => {
            setCustomPrompt(e.target.value);
            localStorage.setItem("podman-chat-custom-prompt", e.target.value);
          }}
          placeholder="Custom system prompt..."
          data-testid="chat-custom-prompt"
          className="bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 w-full"
        />
      )}

      {showSettings && (
        <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-3 flex flex-wrap gap-3 items-center text-sm">
          <div>
            <label htmlFor="chat-provider" className="text-xs text-slate-500 block">
              Provider
            </label>
            <div className="relative">
              <select
                id="chat-provider"
                data-testid="llm-provider-select"
                value={provider}
                onChange={(e) => onProviderChange(e.target.value)}
                className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-200 text-xs min-w-[9rem] appearance-none pr-6"
              >
                {providers.length === 0 ? (
                  <option value="ollama">Ollama</option>
                ) : (
                  providers.map((p) => (
                    <option key={p.type} value={p.type}>
                      {p.type}
                    </option>
                  ))
                )}
              </select>
              {activeProvider && (
                <span
                  className={`absolute right-1.5 top-1/2 -translate-y-1/2 h-2 w-2 rounded-full ${activeProvider.reachable ? "bg-green-500" : "bg-red-500"}`}
                />
              )}
            </div>
          </div>
          {modelOptions.length > 0 && (
            <div>
              <label htmlFor="chat-model" className="text-xs text-slate-500 block">
                Model
              </label>
              <select
                id="chat-model"
                data-testid="llm-model-select"
                value={model}
                onChange={(e) => onModelChange(e.target.value)}
                className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-200 text-xs min-w-[9rem]"
              >
                {modelOptions.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </div>
          )}
          {modelOptions.length === 0 && (
            <div>
              <label htmlFor="chat-model-text" className="text-xs text-slate-500 block">
                Model
              </label>
              <input
                id="chat-model-text"
                value={model}
                onChange={(e) => onModelChange(e.target.value)}
                className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-200 text-xs w-28 font-mono"
              />
            </div>
          )}
          <div>
            <label htmlFor="chat-endpoint" className="text-xs text-slate-500 block">
              Endpoint
            </label>
            <input
              id="chat-endpoint"
              value={endpoint}
              onChange={(e) => {
                setEndpoint(e.target.value);
                localStorage.setItem("podman-chat-endpoint", e.target.value);
              }}
              className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-slate-200 text-xs w-44 font-mono"
            />
          </div>
          {gpuDetected && providers.length === 0 && (
            <p className="text-xs text-amber-300/80 w-full">
              GPU detected but no local LLM is running — start Ollama (`ollama serve`) or LM Studio
              to enable AI chat.
            </p>
          )}
          <button
            type="button"
            onClick={refreshProviders}
            disabled={loadingProviders}
            className="mt-4 p-1.5 rounded-md text-slate-400 hover:text-white hover:bg-slate-800 self-end"
          >
            <RefreshCw className={`h-4 w-4 ${loadingProviders ? "animate-spin" : ""}`} />
          </button>
        </div>
      )}

      <div className="flex-1 overflow-y-auto space-y-3 pr-1" data-testid="chat-messages">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
            <Bot className="h-12 w-12 text-slate-700" />
            <p className="text-slate-500 text-sm max-w-md">
              Ask me about Podman — containers, images, volumes, compose, or daemon issues.
            </p>
            {chatSkills.length > 0 && (
              <div className="flex flex-wrap gap-2 justify-center" data-testid="skill-chips">
                {chatSkills.map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => setInput(`Use the ${s} skill: `)}
                    title={`Prompt template: ${s}`}
                    className="px-3 py-1.5 text-xs bg-purple-900/30 hover:bg-purple-800/40 text-purple-200 rounded-lg border border-purple-700/40"
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}
            <div className="flex flex-wrap gap-2 justify-center" data-testid="example-prompts">
              {suggested.map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => setInput(p)}
                  className="px-3 py-1.5 text-xs bg-slate-800/60 hover:bg-slate-700/60 text-slate-300 rounded-lg border border-slate-700/50"
                >
                  <Sparkles className="h-3 w-3 inline mr-1 text-blue-400" />
                  {p}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={`${msg.timestamp}-${msg.role}`}
              className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}
            >
              {msg.role !== "user" && (
                <div className="h-8 w-8 rounded-full bg-blue-900/50 flex items-center justify-center border border-blue-800/50 shrink-0">
                  <Bot className="h-4 w-4 text-blue-400" />
                </div>
              )}
              <div className={`max-w-[80%] space-y-1 ${msg.role === "user" ? "items-end" : ""}`}>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-500">
                    {msg.role === "user" ? "You" : persona.name}
                  </span>
                  <span className="text-xs text-slate-600">{fmt(msg.timestamp)}</span>
                </div>
                {msg.toolCalls && msg.toolCalls.length > 0 && (
                  <div className="space-y-2 mb-2">
                    {msg.toolCalls.map((tc, j) => (
                      <div
                        key={`${tc.tool}-${tc.nl_name}`}
                        className="bg-slate-900/80 border border-slate-700/60 rounded-lg overflow-hidden text-xs"
                      >
                        <button
                          type="button"
                          onClick={() => toggleCard(msg.timestamp + j)}
                          className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-slate-800/50"
                        >
                          {expandedCards.has(msg.timestamp + j) ? (
                            <ChevronDown className="h-3.5 w-3.5 shrink-0 text-slate-400" />
                          ) : (
                            <ChevronRight className="h-3.5 w-3.5 shrink-0 text-slate-400" />
                          )}
                          {tc.result ? (
                            tc.result.success ? (
                              <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-green-500" />
                            ) : (
                              <XCircle className="h-3.5 w-3.5 shrink-0 text-red-500" />
                            )
                          ) : (
                            <span className="h-3.5 w-3.5 shrink-0 rounded-full bg-blue-500/50 animate-pulse" />
                          )}
                          <span className="text-slate-200 font-medium">{tc.nl_name}</span>
                          {tc.result && (
                            <span className="text-slate-500 ml-auto">{tc.result.timing_ms}ms</span>
                          )}
                        </button>
                        {expandedCards.has(msg.timestamp + j) && tc.result && (
                          <div className="px-3 pb-2 space-y-1.5 text-slate-400 font-mono border-t border-slate-800 pt-1.5">
                            <div>
                              <span className="text-slate-500">tool: </span>
                              {tc.result.tool}
                            </div>
                            <div>
                              <span className="text-slate-500">params: </span>
                              {JSON.stringify(tc.result.params)}
                            </div>
                            <div>
                              <span className="text-slate-500">timing: </span>
                              {tc.result.timing_ms}ms
                            </div>
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
                <div
                  className={`text-sm rounded-xl px-4 py-2.5 ${msg.role === "user" ? "bg-blue-600/20 text-blue-100 border border-blue-700/30" : "bg-slate-800/60 text-slate-200 border border-slate-700/50"}`}
                >
                  <div className="whitespace-pre-wrap break-words">
                    {msg.content ||
                      (msg === messages[messages.length - 1] && streaming ? (
                        <span className="animate-pulse">...</span>
                      ) : (
                        ""
                      ))}
                  </div>
                </div>
              </div>
              {msg.role === "user" && (
                <div className="h-8 w-8 rounded-full bg-slate-800 flex items-center justify-center border border-slate-700 shrink-0">
                  <User className="h-4 w-4 text-slate-400" />
                </div>
              )}
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>

      <div className="flex gap-2 items-end bg-slate-900/80 border border-slate-800 rounded-xl p-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
          placeholder="Ask about Podman..."
          rows={1}
          data-testid="chat-input"
          className="flex-1 bg-transparent border-0 outline-none text-sm text-slate-200 placeholder-slate-500 resize-none max-h-32 py-1.5 px-2"
        />
        {streaming ? (
          <button
            type="button"
            onClick={stop}
            className="p-2 rounded-lg bg-red-600/20 hover:bg-red-600/40 text-red-400"
          >
            <StopCircle className="h-5 w-5" />
          </button>
        ) : (
          <button
            type="button"
            data-testid="chat-send"
            onClick={send}
            disabled={!input.trim()}
            className="p-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-30 text-white"
          >
            <Send className="h-5 w-5" />
          </button>
        )}
      </div>
    </div>
  );
}
