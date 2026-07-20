import { useState, useEffect } from "react";
import { API_BASE } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, AlertCircle, Package } from "lucide-react";

interface PodItem {
  Id: string;
  Name: string;
  Status: string;
  Created: string;
  NumberOfContainers: number;
  Containers?: Array<{
    Id: string;
    Names: string;
    Status: string;
  }>;
}

export function Pods() {
  const [pods, setPods] = useState<PodItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPods = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/pods`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      // Podman pods might be inside data.pods or data.data.pods
      const podsList = data.pods || (data.data && data.data.pods) || [];
      setPods(podsList);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load pods");
      setPods([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPods();
  }, []);

  if (loading && pods.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[320px]">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Pods</h2>
          <p className="text-slate-400">List and manage Podman pods (shared container groups)</p>
        </div>
        <button
          onClick={fetchPods}
          disabled={loading}
          className="rounded-md bg-slate-800 px-3 py-2 text-sm font-medium text-slate-200 hover:bg-slate-700 disabled:opacity-50 transition-colors"
        >
          {loading ? "Refreshing…" : "Refresh"}
        </button>
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
          <CardTitle className="text-white">Active Pods</CardTitle>
        </CardHeader>
        <CardContent>
          {pods.length === 0 && !error ? (
            <p className="text-slate-500 py-8 text-center">No pods found. Create a pod using 'podman pod create' or chat.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-800 text-left text-slate-400">
                    <th className="pb-2 pr-4 font-medium">Name</th>
                    <th className="pb-2 pr-4 font-medium">Pod ID</th>
                    <th className="pb-2 pr-4 font-medium">Containers</th>
                    <th className="pb-2 pr-4 font-medium">State</th>
                    <th className="pb-2 font-medium">Created</th>
                  </tr>
                </thead>
                <tbody>
                  {pods.map((p) => {
                    const statusLower = String(p.Status).toLowerCase();
                    const stateColor = 
                      statusLower === "running" ? "text-emerald-400" :
                      statusLower === "degraded" ? "text-amber-400" :
                      "text-slate-500";
                    return (
                      <tr key={p.Id} className="border-b border-slate-800/80 text-slate-200 hover:bg-slate-900/20 transition-colors">
                        <td className="py-3 pr-4">
                          <span className="flex items-center gap-2">
                            <Package className="h-4 w-4 text-blue-400 shrink-0" />
                            <span className="font-semibold">{p.Name}</span>
                          </span>
                        </td>
                        <td className="py-3 pr-4 font-mono text-slate-400">{p.Id.slice(0, 12)}</td>
                        <td className="py-3 pr-4">{p.NumberOfContainers || (p.Containers ? p.Containers.length : 0)}</td>
                        <td className="py-3 pr-4">
                          <span className={stateColor}>
                            {p.Status}
                          </span>
                        </td>
                        <td className="py-3 text-slate-400">{new Date(p.Created).toLocaleString() || "—"}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
