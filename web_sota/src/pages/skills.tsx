import { AlertCircle, Brain, Check, Copy, Loader2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { API_BASE } from "@/lib/api";

async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    try {
      const ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      return true;
    } catch {
      return false;
    }
  }
}

export function Skills() {
  const [skills, setSkills] = useState<string[]>([]);
  const [tools, setTools] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState("");
  const [copied, setCopied] = useState<string | null>(null);

  const fetchSkills = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/skills`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      setSkills(data.skills ?? []);
      setTools(data.tools ?? []);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load skills");
      setSkills([]);
      setTools([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSkills();
  }, [fetchSkills]);

  const onCopy = async (name: string) => {
    if (await copyText(name)) {
      setCopied(name);
      setTimeout(() => setCopied((c) => (c === name ? null : c)), 1500);
    }
  };

  const q = filter.toLowerCase();
  const visibleSkills = skills.filter((s) => !q || s.toLowerCase().includes(q));
  const visibleTools = tools.filter((t) => !q || t.toLowerCase().includes(q));

  const renderRow = (name: string, kind: string) => (
    <div
      key={`${kind}-${name}`}
      data-testid={`skill-${name}`}
      className="flex items-center gap-3 px-3 py-2 text-sm border-b border-slate-800/60 last:border-0"
    >
      <span className="font-mono text-slate-200">{name}</span>
      <span className="text-xs text-slate-500">{kind}</span>
      <button
        type="button"
        onClick={() => onCopy(name)}
        title={`Copy ${kind} name`}
        className="ml-auto p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
      >
        {copied === name ? (
          <Check className="h-4 w-4 text-green-400" />
        ) : (
          <Copy className="h-4 w-4" />
        )}
      </button>
    </div>
  );

  return (
    <div className="space-y-6" data-testid="skills-page">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Skills</h2>
          <p className="text-slate-400">Prompts and tools the AI Command page can use</p>
        </div>
        <div className="flex items-center gap-2">
          <input
            data-testid="skills-filter"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Filter skills and tools…"
            className="bg-slate-900 border border-slate-800 rounded-md px-3 py-1.5 text-sm text-slate-200 w-56"
          />
          <button
            type="button"
            data-testid="skills-refresh"
            onClick={fetchSkills}
            disabled={loading}
            className="rounded-md bg-slate-800 px-3 py-1.5 text-sm font-medium text-slate-200 hover:bg-slate-700 disabled:opacity-50 transition-colors"
          >
            {loading ? "Refreshing…" : "Refresh"}
          </button>
        </div>
      </div>

      {error && (
        <Card className="border-red-900/50 bg-red-950/20">
          <CardContent className="flex items-center gap-3 pt-6">
            <AlertCircle className="h-8 w-8 text-red-500 shrink-0" />
            <p className="text-red-200">{error}</p>
          </CardContent>
        </Card>
      )}

      <Card className="border-slate-800 bg-slate-950/50 backdrop-blur-xl">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Brain className="h-5 w-5 text-purple-400" />
            Prompts
            <span className="text-xs font-normal text-slate-400" data-testid="skills-count">
              {visibleSkills.length} of {skills.length}
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading && skills.length === 0 ? (
            <div className="flex items-center justify-center min-h-[120px]">
              <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
            </div>
          ) : visibleSkills.length === 0 ? (
            <p className="text-slate-500 py-6 text-center">No prompts match.</p>
          ) : (
            <div>{visibleSkills.map((s) => renderRow(s, "prompt"))}</div>
          )}
        </CardContent>
      </Card>

      <Card className="border-slate-800 bg-slate-950/50 backdrop-blur-xl">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Brain className="h-5 w-5 text-blue-400" />
            Tools
            <span className="text-xs font-normal text-slate-400" data-testid="tools-count">
              {visibleTools.length} of {tools.length}
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading && tools.length === 0 ? (
            <div className="flex items-center justify-center min-h-[120px]">
              <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
            </div>
          ) : visibleTools.length === 0 ? (
            <p className="text-slate-500 py-6 text-center">No tools match.</p>
          ) : (
            <div>{visibleTools.map((t) => renderRow(t, "tool"))}</div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
