import { AlertCircle, Loader2, Play, Wrench } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { API_BASE } from "@/lib/api";

const DEFAULT_OPS: Record<string, string> = {
  manage_containers: "list",
  manage_pods: "list",
  manage_images: "list",
  manage_system: "status",
  manage_compose: "ps",
  manage_backup: "list_backups",
  manage_migrate: "compatibility_check",
  manage_agentic: "health_sweep",
  manage_health: "system_overview",
};

interface RunResult {
  ok: boolean;
  text: string;
}

export function Tools() {
  const [tools, setTools] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [params, setParams] = useState<Record<string, string>>({});
  const [running, setRunning] = useState<Record<string, boolean>>({});
  const [outputs, setOutputs] = useState<Record<string, RunResult | null>>({});
  const [pageError, setPageError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTools = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/tools`);
        const data = await response.json();
        const runnable = ((data.tools as string[]) || []).filter((t) => t.startsWith("manage_"));
        setTools(runnable);
        const initial: Record<string, string> = {};
        for (const t of runnable) {
          initial[t] = JSON.stringify({ operation: DEFAULT_OPS[t] ?? "list" });
        }
        setParams(initial);
      } catch (error) {
        setPageError(error instanceof Error ? error.message : "Failed to fetch tools");
      } finally {
        setLoading(false);
      }
    };
    fetchTools();
  }, []);

  const runTool = async (tool: string) => {
    let parsed: Record<string, unknown> = {};
    try {
      parsed = JSON.parse(params[tool] || "{}");
    } catch {
      setOutputs((o) => ({ ...o, [tool]: { ok: false, text: "params is not valid JSON" } }));
      return;
    }
    setRunning((r) => ({ ...r, [tool]: true }));
    try {
      const res = await fetch(`${API_BASE}/api/tools/call`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tool, params: parsed }),
      });
      const data = await res.json();
      const ok = res.ok && data.success !== false;
      setOutputs((o) => ({ ...o, [tool]: { ok, text: JSON.stringify(data, null, 2) } }));
    } catch (e) {
      setOutputs((o) => ({
        ...o,
        [tool]: { ok: false, text: e instanceof Error ? e.message : "request failed" },
      }));
    } finally {
      setRunning((r) => ({ ...r, [tool]: false }));
    }
  };

  return (
    <div className="space-y-6" data-testid="tools-page">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">Podman MCP Tools</h2>
        <p className="text-slate-400">Directly execute container and engine operations</p>
      </div>

      {pageError && (
        <Card className="border-red-900/50 bg-red-950/20">
          <CardContent className="flex items-center gap-3 pt-6">
            <AlertCircle className="h-8 w-8 text-red-500 shrink-0" />
            <p className="text-red-200">{pageError}</p>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3" data-testid="tools-grid">
        {loading ? (
          <div className="col-span-full flex items-center justify-center p-12">
            <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
          </div>
        ) : (
          tools.map((tool) => {
            const out = outputs[tool];
            return (
              <Card
                key={tool}
                className="border-slate-800 bg-slate-950/50 hover:bg-slate-900/50 transition-colors"
              >
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-semibold text-white">{tool}</CardTitle>
                    <Wrench className="h-4 w-4 text-blue-500" />
                  </div>
                  <CardDescription className="text-xs text-slate-400">
                    Container orchestration tool
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-2">
                  <input
                    data-testid={`tool-params-${tool}`}
                    value={params[tool] ?? ""}
                    onChange={(e) => setParams((p) => ({ ...p, [tool]: e.target.value }))}
                    spellCheck={false}
                    placeholder='{"operation": "list"}'
                    className="w-full bg-slate-900 border border-slate-800 rounded-md px-2 py-1.5 text-xs font-mono text-slate-200"
                  />
                  <Button
                    size="sm"
                    data-testid={`tool-run-${tool}`}
                    disabled={running[tool]}
                    onClick={() => runTool(tool)}
                    className="w-full bg-slate-800 hover:bg-slate-700 text-slate-200 disabled:opacity-50"
                  >
                    {running[tool] ? (
                      <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                    ) : (
                      <Play className="mr-2 h-3 w-3" />
                    )}
                    Execute
                  </Button>
                  {out && (
                    <pre
                      data-testid={`tool-output-${tool}`}
                      className={`max-h-48 overflow-auto rounded-md border p-2 text-[11px] font-mono whitespace-pre-wrap ${
                        out.ok
                          ? "border-slate-800 bg-slate-900/60 text-slate-300"
                          : "border-red-900/60 bg-red-950/20 text-red-200"
                      }`}
                    >
                      {out.text}
                    </pre>
                  )}
                </CardContent>
              </Card>
            );
          })
        )}
      </div>

      {!loading && tools.length === 0 && !pageError && (
        <div className="flex flex-col items-center justify-center p-12 border border-dashed border-slate-800 rounded-lg">
          <AlertCircle className="h-8 w-8 text-slate-600 mb-2" />
          <p className="text-slate-500">No tools detected from backend</p>
        </div>
      )}
    </div>
  );
}
