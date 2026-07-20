import { useState, useEffect } from "react";
import { API_BASE } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, AlertCircle, Database, Plus, Trash2 } from "lucide-react";

interface VolumeItem {
  Name: string;
  Driver: string;
  Mountpoint: string;
  Scope?: string;
}

export function Volumes() {
  const [volumes, setVolumes] = useState<VolumeItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newVolumeName, setNewVolumeName] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const fetchVolumes = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/volumes`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      
      // Parse list of volumes
      const vols = data.volumes || (data.data && data.data.volumes) || [];
      setVolumes(vols);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load volumes");
      setVolumes([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateVolume = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newVolumeName.trim()) return;
    
    setSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/api/volumes/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newVolumeName }),
      });
      const data = await res.json();
      if (!res.ok || !data.success) throw new Error(data.error || data.message || "Failed to create volume");
      setNewVolumeName("");
      await fetchVolumes();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create volume");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteVolume = async (name: string) => {
    if (!confirm(`Are you sure you want to delete volume "${name}"?`)) return;

    try {
      const res = await fetch(`${API_BASE}/api/volumes/delete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      const data = await res.json();
      if (!res.ok || !data.success) throw new Error(data.error || data.message || "Failed to delete volume");
      await fetchVolumes();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete volume");
    }
  };

  useEffect(() => {
    fetchVolumes();
  }, []);

  if (loading && volumes.length === 0) {
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
          <h2 className="text-2xl font-bold tracking-tight text-white">Volumes</h2>
          <p className="text-slate-400">List and manage persistent storage volumes</p>
        </div>
        <button
          onClick={fetchVolumes}
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

      {/* Creation form */}
      <Card className="border-slate-800 bg-slate-950/50 backdrop-blur-xl">
        <CardHeader>
          <CardTitle className="text-white text-base">Create Storage Volume</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCreateVolume} className="flex gap-3 max-w-md">
            <input
              type="text"
              placeholder="e.g. pg_data"
              value={newVolumeName}
              onChange={(e) => setNewVolumeName(e.target.value)}
              disabled={submitting}
              className="flex-1 rounded-md border border-slate-850 bg-slate-900/50 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <button
              type="submit"
              disabled={submitting || !newVolumeName.trim()}
              className="flex items-center gap-1 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-50 transition-colors"
            >
              {submitting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  <Plus className="h-4 w-4" />
                  Create
                </>
              )}
            </button>
          </form>
        </CardContent>
      </Card>

      <Card className="border-slate-800 bg-slate-950/50 backdrop-blur-xl">
        <CardHeader>
          <CardTitle className="text-white">Active Volumes</CardTitle>
        </CardHeader>
        <CardContent>
          {volumes.length === 0 && !error ? (
            <p className="text-slate-500 py-8 text-center">No volumes found.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-800 text-left text-slate-400">
                    <th className="pb-2 pr-4 font-medium">Name</th>
                    <th className="pb-2 pr-4 font-medium">Driver</th>
                    <th className="pb-2 pr-4 font-medium">Mountpoint</th>
                    <th className="pb-2 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {volumes.map((v) => (
                    <tr key={v.Name} className="border-b border-slate-800/80 text-slate-200 hover:bg-slate-900/20 transition-colors">
                      <td className="py-3 pr-4">
                        <span className="flex items-center gap-2">
                          <Database className="h-4 w-4 text-blue-400 shrink-0" />
                          <span className="font-semibold">{v.Name}</span>
                        </span>
                      </td>
                      <td className="py-3 pr-4 font-mono text-slate-400 text-xs">{v.Driver}</td>
                      <td className="py-3 pr-4 text-slate-400 font-mono text-xs max-w-xs truncate" title={v.Mountpoint}>
                        {v.Mountpoint}
                      </td>
                      <td className="py-3 text-right">
                        <button
                          onClick={() => handleDeleteVolume(v.Name)}
                          className="p-1 rounded text-slate-400 hover:text-red-400 hover:bg-slate-800 transition-all"
                          title="Delete Volume"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
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
