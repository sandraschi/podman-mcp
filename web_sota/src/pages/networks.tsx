import { useState, useEffect } from "react";
import { API_BASE } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, AlertCircle, Network, Plus, Trash2 } from "lucide-react";

interface NetworkItem {
  name: string;
  id: string;
  driver: string;
  subnets?: Array<{
    subnet: string;
    gateway?: string;
  }>;
}

export function Networks() {
  const [networks, setNetworks] = useState<NetworkItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newNetworkName, setNewNetworkName] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const fetchNetworks = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/networks`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      
      // Parse list of networks. Podman returns lowercase fields or capital fields in JSON
      const rawNets = data.networks || (data.data && data.data.networks) || [];
      const normalizedNets: NetworkItem[] = rawNets.map((n: any) => ({
        name: n.name || n.Name || "",
        id: n.id || n.Id || "",
        driver: n.driver || n.Driver || "",
        subnets: n.subnets || n.Subnets || (n.plugins ? n.plugins.map((p: any) => p.ipam) : []) || [],
      }));

      setNetworks(normalizedNets);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load networks");
      setNetworks([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateNetwork = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNetworkName.trim()) return;
    
    setSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/api/networks/create`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newNetworkName }),
      });
      const data = await res.json();
      if (!res.ok || !data.success) throw new Error(data.error || data.message || "Failed to create network");
      setNewNetworkName("");
      await fetchNetworks();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create network");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteNetwork = async (name: string) => {
    if (!confirm(`Are you sure you want to delete network "${name}"?`)) return;

    try {
      const res = await fetch(`${API_BASE}/api/networks/delete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      const data = await res.json();
      if (!res.ok || !data.success) throw new Error(data.error || data.message || "Failed to delete network");
      await fetchNetworks();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete network");
    }
  };

  useEffect(() => {
    fetchNetworks();
  }, []);

  if (loading && networks.length === 0) {
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
          <h2 className="text-2xl font-bold tracking-tight text-white">Networks</h2>
          <p className="text-slate-400">List and manage container bridge networks</p>
        </div>
        <button
          onClick={fetchNetworks}
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
          <CardTitle className="text-white text-base">Create Bridge Network</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCreateNetwork} className="flex gap-3 max-w-md">
            <input
              type="text"
              placeholder="e.g. dev_bridge"
              value={newNetworkName}
              onChange={(e) => setNewNetworkName(e.target.value)}
              disabled={submitting}
              className="flex-1 rounded-md border border-slate-850 bg-slate-900/50 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <button
              type="submit"
              disabled={submitting || !newNetworkName.trim()}
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
          <CardTitle className="text-white">Active Networks</CardTitle>
        </CardHeader>
        <CardContent>
          {networks.length === 0 && !error ? (
            <p className="text-slate-500 py-8 text-center">No networks found.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-800 text-left text-slate-400">
                    <th className="pb-2 pr-4 font-medium">Name</th>
                    <th className="pb-2 pr-4 font-medium">Network ID</th>
                    <th className="pb-2 pr-4 font-medium">Driver</th>
                    <th className="pb-2 pr-4 font-medium">Subnets</th>
                    <th className="pb-2 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {networks.map((n) => {
                    // Extract subnet string
                    const subnetStrs = n.subnets
                      ? n.subnets.map((s: any) => s.subnet || s.Subnet || JSON.stringify(s)).join(", ")
                      : "";
                      
                    return (
                      <tr key={n.id} className="border-b border-slate-800/80 text-slate-200 hover:bg-slate-900/20 transition-colors">
                        <td className="py-3 pr-4">
                          <span className="flex items-center gap-2">
                            <Network className="h-4 w-4 text-emerald-400 shrink-0" />
                            <span className="font-semibold">{n.name}</span>
                          </span>
                        </td>
                        <td className="py-3 pr-4 font-mono text-slate-400 text-xs">{n.id.slice(0, 12)}</td>
                        <td className="py-3 pr-4 font-mono text-slate-400 text-xs">{n.driver}</td>
                        <td className="py-3 pr-4 text-slate-400 font-mono text-xs">{subnetStrs || "—"}</td>
                        <td className="py-3 text-right">
                          <button
                            onClick={() => handleDeleteNetwork(n.name)}
                            disabled={n.name === "podman" || n.name === "default"}
                            className="p-1 rounded text-slate-400 hover:text-red-400 hover:bg-slate-800 disabled:opacity-30 disabled:hover:bg-transparent disabled:hover:text-slate-400 transition-all"
                            title={n.name === "podman" || n.name === "default" ? "Cannot delete default network" : "Delete Network"}
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </td>
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
