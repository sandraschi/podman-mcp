import { useState, useEffect } from "react";
import { API_BASE } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, AlertCircle, Box } from "lucide-react";

interface ContainerItem {
  id: string;
  name: string;
  status: string;
  image: string;
  state: string;
  created?: string;
}

export function Containers() {
  const [containers, setContainers] = useState<ContainerItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchContainers = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/containers`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      setContainers(data.containers ?? []);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load containers");
      setContainers([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchContainers();
  }, []);

  if (loading && containers.length === 0) {
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
          <h2 className="text-2xl font-bold tracking-tight text-white">Containers</h2>
          <p className="text-slate-400">List and manage Podman containers</p>
        </div>
        <button
          onClick={fetchContainers}
          disabled={loading}
          className="rounded-md bg-slate-800 px-3 py-2 text-sm font-medium text-slate-200 hover:bg-slate-700 disabled:opacity-50"
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

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-white">All containers</CardTitle>
        </CardHeader>
        <CardContent>
          {containers.length === 0 && !error ? (
            <p className="text-slate-500 py-8 text-center">No containers found.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-800 text-left text-slate-400">
                    <th className="pb-2 pr-4 font-medium">Name</th>
                    <th className="pb-2 pr-4 font-medium">ID</th>
                    <th className="pb-2 pr-4 font-medium">Image</th>
                    <th className="pb-2 pr-4 font-medium">State</th>
                    <th className="pb-2 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {containers.map((c) => (
                    <tr key={c.id} className="border-b border-slate-800/80 text-slate-200">
                      <td className="py-3 pr-4">
                        <span className="flex items-center gap-2">
                          <Box className="h-4 w-4 text-blue-500 shrink-0" />
                          {c.name}
                        </span>
                      </td>
                      <td className="py-3 pr-4 font-mono text-slate-400">{c.id.slice(0, 12)}</td>
                      <td className="py-3 pr-4">{c.image}</td>
                      <td className="py-3 pr-4">
                        <span
                          className={
                            c.state === "running"
                              ? "text-emerald-400"
                              : "text-slate-500"
                          }
                        >
                          {c.state}
                        </span>
                      </td>
                      <td className="py-3">{c.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
