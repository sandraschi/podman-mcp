import { useCallback, useEffect, useState, useRef } from "react";
import { API_BASE } from "@/lib/api";
import { useConnection } from "@/store/connection";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, AlertTriangle, Box, Cpu, ExternalLink, HardDrive, Loader2, AlertCircle, RefreshCw, Package, Terminal, Download, Wrench } from "lucide-react";
import { Link } from "react-router-dom";

interface ContainerItem {
  id: string;
  name: string;
  status: string;
  image: string;
  state: string;
}

interface SystemInfo {
  podman_version?: string;
  rootless?: boolean;
  containers?: { total?: number; running?: number; paused?: number; stopped?: number };
  images?: { total?: number };
  memory?: { total?: number; total_formatted?: string };
  cpu?: { cores?: number };
}

interface ImageItem {
  id?: string;
  repo_tags?: string[];
  size?: number;
  created?: string;
}

interface DashboardData {
  containers: ContainerItem[];
  containers_status?: string;
  containers_message?: string;
  system_info: SystemInfo | null;
  system_status?: string;
  disk_summary?: {
    total_containers_size?: number;
    total_images_size?: number;
    total_volumes_size?: number;
    total_size?: number;
  };
  images: ImageItem[];
  images_count?: number;
  images_status?: string;
  pods?: any[];
  pods_status?: string;
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorType, setErrorType] = useState<"backend_down" | "podman_missing" | "podman_not_started" | "podman_error" | null>(null);
  const connState = useConnection((s) => s.state);
  const prevConn = useRef(connState);

  const fetchDashboard = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/dashboard`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setData(json);
      if (json.containers_status === "error" || json.system_status === "error") {
        const msg = json.containers_message || "Podman CLI/Machine not available";
        setError(msg);
        const lower = msg.toLowerCase();
        if (lower.includes("not available") || lower.includes("not found") || lower.includes("executable")) {
          setErrorType("podman_missing");
        } else if (lower.includes("machine") && (lower.includes("not running") || lower.includes("stopped"))) {
          setErrorType("podman_not_started");
        } else {
          setErrorType("podman_error");
        }
      } else {
        setError(null);
        setErrorType(null);
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Failed to load dashboard";
      setError(msg);
      setErrorType("backend_down");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial fetch on mount
  useEffect(() => { fetchDashboard(); }, [fetchDashboard]);

  // Re-fetch when backend transitions to connected (e.g. after startup delay)
  useEffect(() => {
    if (prevConn.current !== "connected" && connState === "connected") {
      setLoading(true);
      fetchDashboard();
    }
    prevConn.current = connState;
  }, [connState, fetchDashboard]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[320px]">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="space-y-6">
        <div className="mb-6 bg-gradient-to-br from-blue-900/20 via-slate-900/50 to-transparent border border-blue-900/30 rounded-xl px-6 py-5">
          <h3 className="text-lg font-semibold text-white">Podman MCP</h3>
          <p className="text-sm text-slate-300 mt-1">
            AI-powered Podman management via natural language.
            Control containers, pods, images, volumes, and networks through chat or the dashboard.
          </p>
          <p className="text-xs text-slate-500 mt-1">
            Backend port 11113 · MCP endpoint /mcp · Fleet: mcp-central-docs/projects/podman-mcp
          </p>
        </div>

        {errorType === "backend_down" && (
          <div className="space-y-4">
            <Card className="border-red-900/50 bg-red-950/20">
              <CardContent className="flex items-start gap-3 pt-6">
                <AlertCircle className="h-8 w-8 text-red-500 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-red-200 font-medium">Backend is not running</p>
                  <p className="text-red-300/70 text-sm mt-1">{error}</p>
                </div>
                <RestartPodmanButton />
              </CardContent>
            </Card>
            <Card className="border-amber-900/30 bg-amber-950/10">
              <CardContent className="pt-5 pb-4">
                <h4 className="text-amber-200 font-medium flex items-center gap-2 text-sm">
                  <Terminal className="h-4 w-4" /> Start the backend server
                </h4>
                <ol className="mt-3 space-y-2 text-sm text-slate-300 list-decimal ml-5">
                  <li>Open a terminal in the project directory</li>
                  <li>
                    Run:{' '}
                    <code className="bg-slate-800 px-2 py-0.5 rounded text-blue-300 text-xs">
                      .\web_sota\start.ps1
                    </code>
                  </li>
                  <li>Wait for the health check to pass, then refresh this page</li>
                </ol>
                <p className="text-xs text-slate-500 mt-3">
                  Frontend: <code className="text-blue-400">http://127.0.0.1:11112</code> · Backend: <code className="text-blue-400">http://127.0.0.1:11113</code>
                </p>
              </CardContent>
            </Card>
          </div>
        )}

        {errorType === "podman_missing" && (
          <div className="space-y-4">
            <Card className="border-red-900/50 bg-red-950/20">
              <CardContent className="flex items-start gap-3 pt-6">
                <AlertCircle className="h-8 w-8 text-red-500 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-red-200 font-medium">Podman is not installed</p>
                  <p className="text-red-300/70 text-sm mt-1">{error}</p>
                </div>
              </CardContent>
            </Card>
            <Card className="border-blue-900/30 bg-blue-950/10">
              <CardContent className="pt-5 pb-4">
                <h4 className="text-blue-200 font-medium flex items-center gap-2 text-sm">
                  <Download className="h-4 w-4" /> Install Podman
                </h4>
                <ol className="mt-3 space-y-2 text-sm text-slate-300 list-decimal ml-5">
                  <li>
                    Install via winget:{' '}
                    <code className="bg-slate-800 px-2 py-0.5 rounded text-emerald-300 text-xs">
                      winget install RedHat.Podman
                    </code>
                  </li>
                  <li>
                    Or download from:{' '}
                    <a href="https://podman.io/docs/installation" target="_blank" rel="noopener noreferrer"
                       className="text-blue-400 hover:underline inline-flex items-center gap-1">
                      podman.io <ExternalLink className="h-3 w-3" />
                    </a>
                  </li>
                  <li>
                    Initialize the machine:{' '}
                    <code className="bg-slate-800 px-2 py-0.5 rounded text-blue-300 text-xs">podman machine init</code>
                  </li>
                  <li>
                    Start the machine:{' '}
                    <code className="bg-slate-800 px-2 py-0.5 rounded text-blue-300 text-xs">podman machine start</code>
                  </li>
                </ol>
                <p className="text-xs text-slate-500 mt-3">
                  Restart the backend after installation, then refresh this page.
                </p>
              </CardContent>
            </Card>
          </div>
        )}

        {errorType === "podman_not_started" && (
          <div className="space-y-4">
            <Card className="border-red-900/50 bg-red-950/20">
              <CardContent className="flex items-start gap-3 pt-6">
                <AlertCircle className="h-8 w-8 text-red-500 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-red-200 font-medium">Podman machine is not running</p>
                  <p className="text-red-300/70 text-sm mt-1">{error}</p>
                </div>
                <RestartPodmanButton />
              </CardContent>
            </Card>
            <Card className="border-amber-900/30 bg-amber-950/10">
              <CardContent className="pt-5 pb-4">
                <h4 className="text-amber-200 font-medium flex items-center gap-2 text-sm">
                  <Terminal className="h-4 w-4" /> Start the Podman machine
                </h4>
                <ol className="mt-3 space-y-2 text-sm text-slate-300 list-decimal ml-5">
                  <li>Open a terminal (PowerShell or Command Prompt)</li>
                  <li>
                    Run:{' '}
                    <code className="bg-slate-800 px-2 py-0.5 rounded text-blue-300 text-xs">
                      podman machine start
                    </code>
                  </li>
                  <li>Wait for the VM to boot (usually 10-30 seconds)</li>
                  <li>Click "Restart Podman" above, or refresh this page</li>
                </ol>
                <p className="text-xs text-slate-500 mt-3">
                  If the machine fails to start, try:{' '}
                  <code className="bg-slate-800 px-2 py-0.5 rounded text-blue-300 text-xs">
                    podman machine stop && podman machine start
                  </code>
                </p>
              </CardContent>
            </Card>
          </div>
        )}

        {(errorType === "podman_error" || !errorType) && (
          <div className="space-y-4">
            <Card className="border-red-900/50 bg-red-950/20">
              <CardContent className="flex items-start gap-3 pt-6">
                <AlertCircle className="h-8 w-8 text-red-500 shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-red-200 font-medium">Podman error</p>
                  <p className="text-red-300/70 text-sm mt-1">{error ?? "Unknown error"}</p>
                </div>
                <RestartPodmanButton />
              </CardContent>
            </Card>
            <Card className="border-slate-800 bg-slate-950/50">
              <CardContent className="pt-5 pb-4">
                <h4 className="text-slate-300 font-medium flex items-center gap-2 text-sm">
                  <Wrench className="h-4 w-4" /> Troubleshooting
                </h4>
                <ul className="mt-3 space-y-2 text-sm text-slate-400 list-disc ml-5">
                  <li>Verify Podman is running: run <code className="text-blue-400 bg-slate-800 px-1.5 py-0.5 rounded text-xs">podman --version</code> in a terminal</li>
                  <li>Check machine status: <code className="text-blue-400 bg-slate-800 px-1.5 py-0.5 rounded text-xs">podman machine list</code></li>
                  <li>Try restarting the machine: <code className="text-blue-400 bg-slate-800 px-1.5 py-0.5 rounded text-xs">podman machine stop && podman machine start</code></li>
                  <li>If using WSL2, ensure your default distro has Podman installed</li>
                  <li>Check the logs page for detailed error output</li>
                </ul>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    );
  }

  const containers = data.containers ?? [];
  const running = containers.filter((c) => c.state === "running").length;
  const stopped = containers.length - running;
  const sys = data.system_info ?? {};
  const mem = sys.memory ?? {};
  const disk = data.disk_summary ?? {};
  const totalSize = disk.total_size ?? 0;
  const images = data.images ?? [];
  const pods = data.pods ?? [];
  const runningPods = pods.filter((p) => String(p.Status).toLowerCase() === "running").length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Podman Dashboard</h2>
          <p className="text-slate-400">Container overview and engine status</p>
        </div>
      </div>

      <div className="mb-6 bg-gradient-to-br from-blue-900/20 via-slate-900/50 to-transparent border border-blue-900/30 rounded-xl px-6 py-5">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-lg font-semibold text-white">Podman MCP</h3>
            <p className="text-sm text-slate-300 mt-1">
              Daemonless container engine &mdash; no background service, no root required.
              Control containers, pods, images, volumes, and networks through chat or the dashboard.
            </p>
            <div className="flex flex-wrap gap-2 mt-2">
              <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full bg-emerald-900/40 text-emerald-300 border border-emerald-700/40">
                Daemonless
              </span>
              {sys.rootless ? (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full bg-emerald-900/40 text-emerald-300 border border-emerald-700/40">
                  Rootless
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full bg-amber-900/40 text-amber-300 border border-amber-700/40">
                  Rootful
                </span>
              )}
              <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full bg-blue-900/40 text-blue-300 border border-blue-700/40">
                Pods native
              </span>
            </div>
          </div>
        </div>
        <p className="text-xs text-slate-500 mt-1">
          v{sys.podman_version ?? "—"} · Backend port 11113 · MCP endpoint /mcp
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">Containers</CardTitle>
            <Box className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{containers.length}</div>
            <p className="text-xs text-slate-400">
              {running} Running | {stopped} Stopped
            </p>
            <Link to="/containers" className="text-xs text-blue-400 hover:underline mt-1 inline-block">
              View all
            </Link>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">Pods</CardTitle>
            <Package className="h-4 w-4 text-blue-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{pods.length}</div>
            <p className="text-xs text-slate-400">
              {runningPods} Running | {pods.length - runningPods} Other
            </p>
            <Link to="/pods" className="text-xs text-blue-400 hover:underline mt-1 inline-block">
              View all
            </Link>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">CPU</CardTitle>
            <Cpu className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">{sys.cpu?.cores ?? "—"} cores</div>
            <p className="text-xs text-slate-400">Host allocation</p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">Memory</CardTitle>
            <Activity className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {mem.total_formatted ?? (mem.total != null ? formatBytes(mem.total) : "—")}
            </div>
            <p className="text-xs text-slate-400">Total VM limit</p>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-200">Storage</CardTitle>
            <HardDrive className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white">
              {totalSize > 0 ? formatBytes(totalSize) : "—"}
            </div>
            <p className="text-xs text-slate-400">Images cache size</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4 border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="text-white">Status Log</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[200px] font-mono text-xs p-4 overflow-y-auto border border-slate-800 rounded-md bg-slate-900/50 text-slate-400 space-y-1">
              <p className="text-blue-400">[info] Podman {sys.podman_version ?? "—"}</p>
              <p>[info] {data.containers_message ?? `Containers: ${containers.length}`}</p>
              <p>[info] Pods: {pods.length} total ({runningPods} running)</p>
              <p className="text-emerald-400">
                [success] System: {data.system_status === "success" ? "OK" : data.system_status ?? "—"}
              </p>
              {data.containers_status === "error" && (
                <p className="text-amber-400">[warn] Containers list error</p>
              )}
            </div>
          </CardContent>
        </Card>
        <Card className="col-span-3 border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="text-white">Images ({images.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 max-h-[200px] overflow-y-auto">
              {images.length === 0 ? (
                <p className="text-slate-500 text-sm">No images</p>
              ) : (
                images.slice(0, 8).map((img, i) => {
                  const tag = (img.repo_tags && img.repo_tags[0]) || img.id || "—";
                  const sz = img.size != null ? formatBytes(img.size) : "";
                  return (
                    <div key={i} className="flex items-center">
                      <Box className="h-4 w-4 text-blue-400 mr-2 shrink-0" />
                      <div className="min-w-0 space-y-0.5">
                        <p className="text-sm font-medium leading-none text-white truncate">
                          {tag}
                        </p>
                        {sz && <p className="text-xs text-slate-400">{sz}</p>}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function RestartPodmanButton() {
  const [restarting, setRestarting] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const handleRestart = useCallback(async () => {
    setRestarting(true); setResult(null);
    try {
      const r = await fetch(`${API_BASE}/api/podman/recover`, { method: "POST" });
      const d = await r.json();
      setResult(d.success ? "Podman machine restarted" : d.message);
    } catch { setResult("Failed to trigger restart"); }
    finally { setRestarting(false); }
  }, []);
  return (
    <div className="flex flex-col items-end gap-1">
      <button type="button" onClick={handleRestart} disabled={restarting}
        className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium bg-red-700 hover:bg-red-600 disabled:opacity-50 text-white rounded-md transition-colors">
        <RefreshCw className={`h-4 w-4 ${restarting ? "animate-spin" : ""}`} />
        {restarting ? "Restarting..." : "Restart Podman"}
      </button>
      {result && <span className="text-xs text-slate-400">{result}</span>}
    </div>
  );
}
