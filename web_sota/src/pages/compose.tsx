import { useCallback, useEffect, useRef, useState } from "react";
import { API_BASE } from "@/lib/api";
import { analyzeComposeFile } from "@/common/api";
import { Layers, Play, Square, Eye, EyeOff, RefreshCw, Terminal, FileText, Upload, Server, Container, Network, ListOrdered, Database } from "lucide-react";

interface ComposeProject {
  Name?: string;
  name?: string;
  Status?: string;
  status?: string;
  ConfigFiles?: string;
  configFiles?: string;
}

interface ComposeContainer {
  Name?: string;
  name?: string;
  Service?: string;
  service?: string;
  State?: string;
  state?: string;
  Status?: string;
  status?: string;
  Ports?: string;
  ports?: string;
}

interface ComposeAnalysis {
  success: boolean;
  file_path?: string;
  file_size?: number;
  compose_version?: string;
  service_count?: number;
  volume_count?: number;
  network_count?: number;
  services?: Array<{
    name: string; image: string; build: string; ports: Array<{host: string; container: string}>;
    volumes: string[]; depends_on: string[]; environment_keys: string[];
    restart: string; healthcheck: boolean; container_name: string;
  }>;
  volumes?: Array<{name: string; driver: string}>;
  networks?: Array<{name: string; driver: string}>;
  all_images?: string[];
  all_ports?: string[];
  has_build_contexts?: boolean;
  has_healthchecks?: boolean;
  has_depends_on?: boolean;
  unreferenced_volumes?: string[];
  error?: string;
}

const API = `${API_BASE}/api`;

export function Compose() {
  const [projects, setProjects] = useState<ComposeProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedProject, setSelectedProject] = useState<string | null>(null);
  const [containers, setContainers] = useState<ComposeContainer[]>([]);
  const [logs, setLogs] = useState("");
  const [config, setConfig] = useState("");
  const [showConfig, setShowConfig] = useState(false);
  const [actionMsg, setActionMsg] = useState("");
  const [analysis, setAnalysis] = useState<ComposeAnalysis | null>(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [analysisPath, setAnalysisPath] = useState("");
  const [analysisError, setAnalysisError] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchProjects = useCallback(async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/compose/projects?all=true`);
      const data = await r.json();
      setProjects(data.projects ?? []);
    } catch { setProjects([]); }
    finally { setLoading(false); }
  }, []);

  const fetchContainers = useCallback(async (project: string) => {
    try {
      const r = await fetch(`${API}/compose/ps?project=${encodeURIComponent(project)}`);
      const data = await r.json();
      setContainers(data.containers ?? []);
    } catch { setContainers([]); }
  }, []);

  const fetchLogs = useCallback(async (project: string) => {
    try {
      const r = await fetch(`${API}/compose/logs?project=${encodeURIComponent(project)}&tail=50`);
      const data = await r.json();
      setLogs(data.output ?? data.logs ?? "");
    } catch { setLogs("(failed to fetch logs)"); }
  }, []);

  const fetchConfig = useCallback(async (project: string) => {
    try {
      const r = await fetch(`${API}/compose/config?project=${encodeURIComponent(project)}`);
      const data = await r.json();
      setConfig(data.config ?? "(no config)");
    } catch { setConfig("(failed to fetch config)"); }
  }, []);

  const selectProject = useCallback((name: string) => {
    setSelectedProject(name);
    setShowConfig(false);
    setLogs("");
    fetchContainers(name);
    fetchLogs(name);
  }, [fetchContainers, fetchLogs]);

  const doAction = useCallback(async (action: "up" | "down", project: string) => {
    setActionMsg(`${action === "up" ? "Starting" : "Stopping"} ${project}...`);
    try {
      const r = await fetch(`${API}/compose/${action}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ project }),
      });
      const data = await r.json();
      setActionMsg(data.message ?? `${action} completed`);
      setTimeout(() => setActionMsg(""), 3000);
      fetchContainers(project);
      fetchProjects();
    } catch (e: any) {
      setActionMsg(`Error: ${e.message}`);
    }
  }, [fetchContainers, fetchProjects]);

  const pickFile = useCallback(async () => {
    setAnalysisError("");
    try {
      const { open } = await import("@tauri-apps/plugin-dialog");
      const selected = await open({ multiple: false, filters: [{ name: "Compose", extensions: ["yml", "yaml"] }] });
      if (selected) {
        setAnalysisPath(selected);
        setAnalysisLoading(true);
        const r = await analyzeComposeFile(selected);
        setAnalysis(r);
        if (!r.success) setAnalysisError(r.error ?? "Analysis failed");
        setAnalysisLoading(false);
      }
    } catch {
      // Not in Tauri — fall back to manual input
      if (fileInputRef.current) fileInputRef.current.click();
    }
  }, []);

  const handleFileInput = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setAnalysisPath(file.name);
    setAnalysisLoading(true);
    setAnalysisError("");
    const reader = new FileReader();
    reader.onload = async () => {
      // Send file content to backend for parsing
      try {
        const r = await fetch(`${API}/compose/analyze`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ file_path: `upload:${file.name}`, content: reader.result }),
        });
        const data = await r.json();
        setAnalysis(data);
        if (!data.success) setAnalysisError(data.error ?? "Analysis failed");
      } catch (err: any) {
        setAnalysisError(err.message);
      }
      setAnalysisLoading(false);
    };
    reader.readAsText(file);
  }, []);

  const analyzePath = useCallback(async () => {
    if (!analysisPath.trim()) return;
    setAnalysisLoading(true);
    setAnalysisError("");
    try {
      const r = await analyzeComposeFile(analysisPath.trim());
      setAnalysis(r);
      if (!r.success) setAnalysisError(r.error ?? "Analysis failed");
    } catch (err: any) {
      setAnalysisError(err.message);
    }
    setAnalysisLoading(false);
  }, [analysisPath]);

  useEffect(() => { fetchProjects(); }, [fetchProjects]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Layers className="h-6 w-6 text-blue-400" />
          <h2 className="text-2xl font-bold tracking-tight text-white">Compose</h2>
        </div>
        <div className="flex items-center gap-2">
          <button type="button" onClick={() => fetchProjects()}
            className="p-1.5 rounded-md text-slate-400 hover:text-white hover:bg-slate-800">
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </button>
          {actionMsg && <span className="text-xs text-blue-400">{actionMsg}</span>}
        </div>
      </div>

      <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-slate-400" />
            <span className="text-sm font-medium text-slate-300">Analyze Compose File</span>
          </div>
          <button type="button" onClick={pickFile}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-md bg-blue-600/20 text-blue-400 hover:bg-blue-600/40 border border-blue-700/30">
            <Upload className="h-3.5 w-3.5" /> Pick File
          </button>
        </div>
        <div className="flex gap-2">
          <input
            ref={fileInputRef} type="file" accept=".yml,.yaml" className="hidden"
            onChange={handleFileInput}
          />
          <input value={analysisPath} onChange={(e) => setAnalysisPath(e.target.value)}
            placeholder="Path to podman-compose.yml (or pick above)"
            className="flex-1 bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-xs text-slate-200 font-mono placeholder-slate-600" />
          <button type="button" onClick={analyzePath} disabled={analysisLoading || !analysisPath.trim()}
            className="px-3 py-1.5 text-xs rounded-md bg-slate-800 text-slate-300 hover:bg-slate-700 disabled:opacity-40 border border-slate-700">
            {analysisLoading ? "..." : "Analyze"}
          </button>
        </div>
        {analysisError && <p className="text-xs text-red-400">{analysisError}</p>}
        {analysis && analysis.success && (
          <div className="border-t border-slate-800 pt-3 space-y-3">
            <div className="flex flex-wrap gap-2 text-xs">
              <span className="bg-slate-800 px-2 py-0.5 rounded text-slate-300"><Server className="h-3 w-3 inline mr-1" />{analysis.service_count} services</span>
              <span className="bg-slate-800 px-2 py-0.5 rounded text-slate-300"><Container className="h-3 w-3 inline mr-1" />{analysis.all_images?.length} images</span>
              <span className="bg-slate-800 px-2 py-0.5 rounded text-slate-300"><Database className="h-3 w-3 inline mr-1" />{analysis.volume_count} volumes</span>
              <span className="bg-slate-800 px-2 py-0.5 rounded text-slate-300"><Network className="h-3 w-3 inline mr-1" />{analysis.network_count} networks</span>
              <span className="bg-slate-800 px-2 py-0.5 rounded text-slate-300"><ListOrdered className="h-3 w-3 inline mr-1" />{analysis.all_ports?.length} ports</span>
              {analysis.has_healthchecks && <span className="bg-emerald-900/40 px-2 py-0.5 rounded text-emerald-400">healthchecks</span>}
              {analysis.has_depends_on && <span className="bg-amber-900/40 px-2 py-0.5 rounded text-amber-400">depends-on</span>}
              {analysis.has_build_contexts && <span className="bg-amber-900/40 px-2 py-0.5 rounded text-amber-400">build contexts</span>}
            </div>
            {analysis.services && (
              <div className="space-y-1">
                {analysis.services.map((svc) => (
                  <div key={svc.name} className="bg-slate-800/50 rounded px-3 py-2 text-xs">
                    <div className="flex items-center justify-between text-slate-200 font-medium">
                      <span>{svc.name}</span>
                      {svc.image && <span className="text-slate-400 font-mono">{svc.image}</span>}
                      {svc.build && <span className="text-slate-400 font-mono">build: {svc.build}</span>}
                    </div>
                    <div className="flex flex-wrap gap-2 mt-1 text-slate-500">
                      {svc.ports.length > 0 && <span>ports: {svc.ports.map((p) => `${p.host}:${p.container}`).join(", ")}</span>}
                      {svc.volumes.length > 0 && <span>volumes: {svc.volumes.join(", ")}</span>}
                      {svc.depends_on.length > 0 && <span>depends: {svc.depends_on.join(", ")}</span>}
                      {svc.restart && <span>restart: {svc.restart}</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-1 space-y-2">
          <h3 className="text-sm font-medium text-slate-400 uppercase tracking-wider">Projects</h3>
          {projects.length === 0 ? (
            <p className="text-sm text-slate-500">No compose projects found.</p>
          ) : (
            <div className="space-y-1">
              {projects.map((p) => {
                const name = p.Name ?? p.name ?? "?";
                const status = (p.Status ?? p.status ?? "").toLowerCase();
                const running = status.includes("running") || status.includes("up");
                return (
                  <button key={name} type="button" onClick={() => selectProject(name)}
                    className={`w-full text-left flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${selectedProject === name ? "bg-blue-600/20 border border-blue-500/30" : "bg-slate-900/60 border border-slate-800 hover:bg-slate-800/80"}`}>
                    <span className={`h-2 w-2 rounded-full shrink-0 ${running ? "bg-green-500" : "bg-slate-500"}`} />
                    <span className="text-slate-200 font-medium">{name}</span>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        <div className="xl:col-span-2 space-y-4">
          {selectedProject ? (
            <>
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-slate-400 uppercase tracking-wider">{selectedProject}</h3>
                <div className="flex items-center gap-2">
                  <button type="button" onClick={() => doAction("up", selectedProject)}
                    className="flex items-center gap-1 px-3 py-1.5 text-xs rounded-md bg-emerald-600/20 text-emerald-400 hover:bg-emerald-600/40 border border-emerald-700/30">
                    <Play className="h-3.5 w-3.5" /> Up
                  </button>
                  <button type="button" onClick={() => doAction("down", selectedProject)}
                    className="flex items-center gap-1 px-3 py-1.5 text-xs rounded-md bg-red-600/20 text-red-400 hover:bg-red-600/40 border border-red-700/30">
                    <Square className="h-3.5 w-3.5" /> Down
                  </button>
                  <button type="button" onClick={() => { setShowConfig(!showConfig); if (!showConfig) fetchConfig(selectedProject); }}
                    className={`p-1.5 rounded-md ${showConfig ? "bg-blue-600/30 text-blue-400" : "text-slate-400 hover:text-white hover:bg-slate-800"}`}>
                    {showConfig ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              {showConfig && (
                <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-3">
                  <pre className="text-xs text-slate-300 font-mono whitespace-pre-wrap max-h-96 overflow-y-auto">{config}</pre>
                </div>
              )}

              <div className="bg-slate-900/60 border border-slate-800 rounded-lg overflow-hidden">
                <div className="px-3 py-2 border-b border-slate-800 text-xs text-slate-500 font-medium">Containers</div>
                {containers.length === 0 ? (
                  <div className="px-3 py-4 text-sm text-slate-500">No containers in this project.</div>
                ) : (
                  <div className="divide-y divide-slate-800/50">
                    {containers.map((c, i) => {
                      const name = c.Name ?? c.name ?? "?";
                      const svc = c.Service ?? c.service ?? "?";
                      const state = (c.State ?? c.state ?? "").toLowerCase();
                      const status = c.Status ?? c.status ?? "";
                      const running = state === "running";
                      return (
                        <div key={i} className="flex items-center gap-3 px-3 py-2 text-sm">
                          <span className={`h-2 w-2 rounded-full shrink-0 ${running ? "bg-green-500" : "bg-red-500"}`} />
                          <span className="text-slate-200 font-mono text-xs truncate max-w-[200px]">{name}</span>
                          <span className="text-slate-500 text-xs ml-auto">{svc}</span>
                          <span className={`text-xs ${running ? "text-emerald-400" : "text-slate-500"}`}>{status}</span>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {logs && (
                <div className="bg-slate-900/60 border border-slate-800 rounded-lg">
                  <div className="flex items-center gap-2 px-3 py-2 border-b border-slate-800 text-xs text-slate-500 font-medium">
                    <Terminal className="h-3.5 w-3.5" /> Logs (last 50 lines)
                  </div>
                  <pre className="text-xs text-slate-400 font-mono whitespace-pre-wrap max-h-48 overflow-y-auto p-3">{logs}</pre>
                </div>
              )}
            </>
          ) : (
            <div className="flex items-center justify-center h-48 text-sm text-slate-500">Select a compose project to inspect</div>
          )}
        </div>
      </div>
    </div>
  );
}
