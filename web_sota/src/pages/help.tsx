import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Book, Shield, Zap, Info, AlertCircle, Wrench, Server, Cpu, GitBranch, MessageSquare, Package } from "lucide-react";

const TABS = [
  { id: "about", label: "About", icon: Info },
  { id: "architecture", label: "Architecture", icon: GitBranch },
  { id: "usage", label: "Usage", icon: Book },
  { id: "pods", label: "Pods Guide", icon: Package },
];

export function Help() {
    const [activeTab, setActiveTab] = useState("about");

    const tabBar = (
        <div className="flex gap-1 border-b border-slate-800 pb-0.5">
            {TABS.map((t) => (
                <button
                    key={t.id}
                    type="button"
                    onClick={() => setActiveTab(t.id)}
                    className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-t-lg transition-colors ${
                        activeTab === t.id
                            ? "bg-slate-800/60 text-white border border-b-0 border-slate-700"
                            : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/30"
                    }`}
                >
                    <t.icon className="h-4 w-4" />
                    {t.label}
                </button>
            ))}
        </div>
    );

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold tracking-tight text-white">Help & Documentation</h2>
                <p className="text-slate-400">Reference guide for Podman MCP Server with Daemon-less CLI management</p>
            </div>

            {tabBar}

            {activeTab === "about" && (
                <div className="grid gap-6 md:grid-cols-2">
                    <Card className="border-slate-800 bg-slate-950/50 md:col-span-2">
                        <CardHeader>
                            <div className="flex items-center gap-2">
                                <Info className="h-5 w-5 text-emerald-500" />
                                <CardTitle className="text-white">About Podman MCP</CardTitle>
                            </div>
                        </CardHeader>
                        <CardContent className="text-sm text-slate-400 space-y-3">
                            <p><strong>Podman MCP</strong> is an AI-powered Podman management server. It exposes Podman operations as MCP tools consumable by LLM agents (Claude Desktop, Cursor) and provides a React dashboard for manual management.</p>
                            <p>Unlike Podman Machine, which relies on a monolithic background service (podmand), Podman runs **daemon-less** using a fork-exec process model. This resolves common Windows hangs and cuts idle resource usage by up to 70%.</p>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3">
                                {[
                                    { label: "Version", value: "3.5.0", icon: Info },
                                    { label: "Backend", value: "127.0.0.1:11113", icon: Server },
                                    { label: "Frontend", value: "127.0.0.1:11112", icon: Zap },
                                    { label: "MCP endpoint", value: "/mcp (HTTP SSE)", icon: MessageSquare },
                                ].map((s) => (
                                    <div key={s.label} className="bg-slate-900/60 rounded-lg p-3 border border-slate-800">
                                        <div className="flex items-center gap-2 text-xs text-slate-500 mb-1">
                                            <s.icon className="h-3 w-3" />
                                            {s.label}
                                        </div>
                                        <div className="text-sm font-mono text-slate-200">{s.value}</div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>

                    <Card className="border-slate-800 bg-slate-950/50">
                        <CardHeader>
                            <div className="flex items-center gap-2">
                                <Shield className="h-5 w-5 text-purple-500" />
                                <CardTitle className="text-white">Security & Authentication</CardTitle>
                            </div>
                        </CardHeader>
                        <CardContent className="text-sm text-slate-400 space-y-2">
                            <p>Web app API requests require Basic Authentication. Default: <code className="text-blue-400">sandra / sandra123</code>.</p>
                            <p>The backend wraps the standard local command-line executable <code className="text-blue-400">podman</code>, meaning it inherits the current terminal context privileges and does not expose open TCP port sockets for container administration.</p>
                        </CardContent>
                    </Card>

                    <Card className="border-slate-800 bg-slate-950/50">
                        <CardHeader>
                            <div className="flex items-center gap-2">
                                <Zap className="h-5 w-5 text-yellow-500" />
                                <CardTitle className="text-white">Conforming Webapp Stack</CardTitle>
                            </div>
                        </CardHeader>
                        <CardContent className="text-sm text-slate-400 space-y-1">
                            <p>FastMCP 3.4+ · FastAPI · React 19 · Vite · TailwindCSS</p>
                            <p>Python 3.12+ · Podman CLI Wrapper · Pydantic v2</p>
                            <p className="text-xs text-slate-500 mt-2">Fleet standards compliance: SOTA v12.0</p>
                        </CardContent>
                    </Card>
                </div>
            )}

            {activeTab === "architecture" && (
                <div className="grid gap-6 md:grid-cols-2">
                    <Card className="border-slate-800 bg-slate-950/50 md:col-span-2">
                        <CardHeader>
                            <div className="flex items-center gap-2">
                                <GitBranch className="h-5 w-5 text-blue-500" />
                                <CardTitle className="text-white">System Architecture</CardTitle>
                            </div>
                        </CardHeader>
                        <CardContent className="text-sm text-slate-400 space-y-3">
                            <pre className="bg-slate-900/80 border border-slate-800 rounded-lg p-4 text-xs font-mono text-slate-300 overflow-x-auto">
{`LLM Client (Claude Desktop / Cursor)
      |
      +--- (STDIO JSON-RPC)
      |
      v
Podman MCP Server (FastMCP / Python) <--- HTTP SSE Bridge (:11113) <--- React Web App (:11112)
      |
      v  [Asynchronous Subprocess Executor]
      |
      +--> Windows PATH check for podman.exe
      |      OR
      +--> WSL2 fallback via: "wsl podman"
             |
             v
        Podman VM / Machine (WSL2 / Hyper-V)`}
                            </pre>
                            <p><strong>Lightweight Invocation:</strong> Instead of binding a TCP/SSH client socket to a background service, the server starts the local <code className="text-blue-400">podman</code> process dynamically on each tool call. It captures the stdout and parses the structured response via <code className="text-blue-400">--format json</code>.</p>
                            <p><strong>WSL2 Auto-detection:</strong> If native Windows Podman is missing, the backend automatically proxies requests through <code className="text-blue-400">wsl podman</code>, allowing seamless operation inside default WSL2 Linux distributions.</p>
                        </CardContent>
                    </Card>

                    <Card className="border-slate-800 bg-slate-950/50">
                        <CardHeader>
                            <div className="flex items-center gap-2">
                                <Cpu className="h-5 w-5 text-cyan-500" />
                                <CardTitle className="text-white">Directory Structure</CardTitle>
                            </div>
                        </CardHeader>
                        <CardContent className="text-sm text-slate-400 space-y-2">
                            <ul className="list-disc ml-4 space-y-1 text-xs">
                                <li><code className="text-blue-400">src/podmanmcp/</code> — The main MCP tools package (System, Containers, Pods, Images, Compose)</li>
                                <li><code className="text-blue-400">src/podman_mcp/</code> — FastAPI bridge substrate (chat routes, log routing, provider discovery)</li>
                                <li><code className="text-blue-400">web_sota/</code> — Vite + React SPA conforming dashboard</li>
                                <li><code className="text-blue-400">scripts/</code> — Port resolution, launch utilities, and start scripts</li>
                            </ul>
                        </CardContent>
                    </Card>

                    <Card className="border-slate-800 bg-slate-950/50">
                        <CardHeader>
                            <div className="flex items-center gap-2">
                                <Wrench className="h-5 w-5 text-orange-500" />
                                <CardTitle className="text-white">Machine Control & Recovery</CardTitle>
                            </div>
                        </CardHeader>
                        <CardContent className="text-sm text-slate-400 space-y-2">
                            <p>If the VM becomes unresponsive or WSL2 hits a memory lockup, the host can be rebooted safely. Clicking <strong>Restart Podman</strong> on the dashboard triggers: </p>
                            <ol className="list-decimal ml-4 space-y-1 text-xs">
                                <li><code className="text-blue-400">podman machine stop</code> (forces VM shutdown)</li>
                                <li><code className="text-blue-400">podman machine start</code> (re-allocates and boots VM)</li>
                            </ol>
                            <p className="text-xs mt-1">This avoids having to restart the entire WSL2 system service or computer.</p>
                        </CardContent>
                    </Card>
                </div>
            )}

            {activeTab === "usage" && (
                <div className="grid gap-6 md:grid-cols-2">
                    <Card className="border-slate-800 bg-slate-950/50">
                        <CardHeader>
                            <div className="flex items-center gap-2">
                                <Book className="h-5 w-5 text-blue-500" />
                                <CardTitle className="text-white">Quick Start</CardTitle>
                            </div>
                        </CardHeader>
                        <CardContent className="text-sm text-slate-400 space-y-3">
                            <p>1. Initialize and boot your local Podman VM machine if you haven't already:</p>
                            <pre className="bg-slate-900 border border-slate-800 rounded p-2 text-xs font-mono text-blue-300">
podman machine init
podman machine start
                            </pre>
                            <p>2. Double-click <code className="text-blue-400">start.bat</code> in the repository root. This boots the FastAPI backend and opens the Vite dashboard in your browser.</p>
                            <p>3. Ask the AI Agent natural queries on the **AI Command** page, such as <em>"List my containers"</em> or <em>"Start a Postgres pod"</em>.</p>
                        </CardContent>
                    </Card>

                    <Card className="border-slate-800 bg-slate-950/50">
                        <CardHeader>
                            <div className="flex items-center gap-2">
                                <MessageSquare className="h-5 w-5 text-emerald-500" />
                                <CardTitle className="text-white">AI Commands & Chat</CardTitle>
                            </div>
                        </CardHeader>
                        <CardContent className="text-sm text-slate-400 space-y-2">
                            <p>You can execute operations in natural language. Try typing:</p>
                            <ul className="space-y-1 ml-4 list-disc text-xs">
                                <li><em>"List running containers and show their stats"</em></li>
                                <li><em>"Pull image podman.io/library/node:20-alpine"</em></li>
                                <li><em>"Start a new pod called dev-pod forwarding port 80"</em></li>
                                <li><em>"Deploy my compose stack located at d:/Dev/projects/webapp"</em></li>
                                <li><em>"Clean up unused resources"</em></li>
                            </ul>
                        </CardContent>
                    </Card>

                    <Card className="border-slate-800 bg-slate-950/50">
                        <CardHeader>
                            <div className="flex items-center gap-2">
                                <Wrench className="h-5 w-5 text-orange-500" />
                                <CardTitle className="text-white">SOTA Portmanteau Tools</CardTitle>
                            </div>
                        </CardHeader>
                        <CardContent className="text-sm text-slate-400 space-y-2">
                            <p>To keep the context clean for LLM planners, we expose exactly **5 consolidated tools**:</p>
                            <ul className="space-y-1.5 ml-4 list-disc text-xs">
                                <li><code className="text-blue-400">manage_containers</code> — list, inspect, start, stop, restart, delete, create, logs, stats</li>
                                <li><code className="text-blue-400">manage_pods</code> — list, inspect, create, start, stop, delete</li>
                                <li><code className="text-blue-400">manage_images</code> — list, inspect, pull, delete, build, search</li>
                                <li><code className="text-blue-400">manage_system</code> — status, info, machine_list/init/start/stop, volume_*, network_*</li>
                                <li><code className="text-blue-400">manage_compose</code> — up, down, ps, logs</li>
                            </ul>
                        </CardContent>
                    </Card>

                    <Card className="border-slate-800 bg-slate-950/50">
                        <CardHeader>
                            <div className="flex items-center gap-2">
                                <AlertCircle className="h-5 w-5 text-red-500" />
                                <CardTitle className="text-white">Troubleshooting</CardTitle>
                            </div>
                        </CardHeader>
                        <CardContent className="text-sm text-slate-400 space-y-2 text-xs">
                            <p><strong>"Podman CLI not available":</strong> This means the server cannot execute <code className="text-blue-400">podman</code>. Check your PATH environment variable, or try running the command <code className="text-blue-400">podman machine start</code> manually in a terminal.</p>
                            <p><strong>WSL Connection hangs:</strong> If WSL2 locks up, click the red <strong>Restart Podman</strong> button on the dashboard to force a VM reboot.</p>
                        </CardContent>
                    </Card>
                </div>
            )}

            {activeTab === "pods" && (
                <div className="grid gap-6 md:grid-cols-2">
                    <Card className="border-slate-800 bg-slate-950/50 md:col-span-2">
                        <CardHeader>
                            <div className="flex items-center gap-2">
                                <Package className="h-5 w-5 text-blue-400" />
                                <CardTitle className="text-white">What is a Pod?</CardTitle>
                            </div>
                        </CardHeader>
                        <CardContent className="text-sm text-slate-400 space-y-3">
                            <p>A <strong>Pod</strong> is a concept native to Kubernetes and supported natively by Podman. It is a group of one or more containers that share the same network, IPC, and PID namespace.</p>
                            <p>This allows you to group related containers together. For instance, you can run a database container and a web application container inside the same pod. The web application can reference the database container directly via <code className="text-blue-400">localhost:5432</code>, eliminating the need to create complex bridge network setups.</p>
                        </CardContent>
                    </Card>

                    <Card className="border-slate-800 bg-slate-950/50">
                        <CardHeader>
                            <div className="flex items-center gap-2">
                                <Book className="h-5 w-5 text-blue-500" />
                                <CardTitle className="text-white">Basic Pod Commands</CardTitle>
                            </div>
                        </CardHeader>
                        <CardContent className="text-sm text-slate-400 space-y-2 text-xs">
                            <p>To run containers inside a pod via terminal:</p>
                            <pre className="bg-slate-900 border border-slate-800 rounded p-2 text-slate-300 font-mono">
# Create a pod forwarding port 8080
podman pod create --name my-pod -p 8080:80

# Run container inside that pod
podman run -d --pod my-pod --name web nginx:alpine
                            </pre>
                            <p>Both containers are now grouped, and the nginx server is accessible on your host machine at <code className="text-blue-400">http://localhost:8080</code>.</p>
                        </CardContent>
                    </Card>

                    <Card className="border-slate-800 bg-slate-950/50">
                        <CardHeader>
                            <div className="flex items-center gap-2">
                                <Wrench className="h-5 w-5 text-emerald-500" />
                                <CardTitle className="text-white">Dashboard Pods Page</CardTitle>
                            </div>
                        </CardHeader>
                        <CardContent className="text-sm text-slate-400 space-y-2">
                            <p>We've included a dedicated <strong>Pods</strong> tab in this web app. You can use it to inspect, view all active pod groupings, check how many containers reside in each pod namespace, and monitor their active state in real time.</p>
                        </CardContent>
                    </Card>
                </div>
            )}
        </div>
    );
}
