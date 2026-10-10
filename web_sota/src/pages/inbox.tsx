import { AlertCircle, Inbox as InboxIcon, Loader2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { API_BASE } from "@/lib/api";

interface PodmanEvent {
  action: string;
  type: string;
  name: string;
  image: string;
  time: number;
}

const SINCE_OPTIONS = ["1h", "24h", "7d"];

function formatTime(epoch: number): string {
  if (!epoch) return "—";
  return new Date(epoch * 1000).toLocaleString();
}

export function Inbox() {
  const [events, setEvents] = useState<PodmanEvent[]>([]);
  const [engine, setEngine] = useState<string>("unknown");
  const [engineMsg, setEngineMsg] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [since, setSince] = useState("24h");

  const fetchEvents = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(
        `${API_BASE}/api/events?since=${encodeURIComponent(since)}&limit=200`,
      );
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      setEvents(data.events ?? []);
      setEngine(data.engine ?? "unknown");
      setEngineMsg(data.message ?? "");
      setError(data.success ? null : (data.message ?? "Engine unreachable"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load events");
      setEvents([]);
      setEngine("down");
    } finally {
      setLoading(false);
    }
  }, [since]);

  useEffect(() => {
    fetchEvents();
    const t = setInterval(fetchEvents, 15000);
    return () => clearInterval(t);
  }, [fetchEvents]);

  const types = Array.from(new Set(events.map((e) => e.type))).sort();
  const visible = events.filter(
    (e) =>
      (typeFilter === "all" || e.type === typeFilter) &&
      (!filter || `${e.action} ${e.name} ${e.image}`.toLowerCase().includes(filter.toLowerCase())),
  );

  return (
    <div className="space-y-6" data-testid="inbox-page">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">Inbox</h2>
          <p className="text-slate-400">Recent Podman engine events, auto-refreshed</p>
        </div>
        <div className="flex items-center gap-2">
          <select
            data-testid="inbox-since"
            value={since}
            onChange={(e) => setSince(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-md px-2 py-1.5 text-sm text-slate-200"
          >
            {SINCE_OPTIONS.map((s) => (
              <option key={s} value={s}>
                last {s}
              </option>
            ))}
          </select>
          <select
            data-testid="inbox-type"
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="bg-slate-900 border border-slate-800 rounded-md px-2 py-1.5 text-sm text-slate-200"
          >
            <option value="all">all types</option>
            {types.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
          <input
            data-testid="inbox-filter"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Filter action, name, image…"
            className="bg-slate-900 border border-slate-800 rounded-md px-3 py-1.5 text-sm text-slate-200 w-56"
          />
          <button
            type="button"
            data-testid="inbox-refresh"
            onClick={fetchEvents}
            disabled={loading}
            className="rounded-md bg-slate-800 px-3 py-1.5 text-sm font-medium text-slate-200 hover:bg-slate-700 disabled:opacity-50 transition-colors"
          >
            {loading ? "Refreshing…" : "Refresh"}
          </button>
        </div>
      </div>

      {engine === "down" && (
        <Card className="border-amber-900/50 bg-amber-950/20" data-testid="inbox-engine-down">
          <CardContent className="flex items-center gap-3 pt-6">
            <AlertCircle className="h-8 w-8 text-amber-500 shrink-0" />
            <p className="text-amber-200">
              Podman engine unreachable
              {engineMsg ? `: ${engineMsg}` : ". Start the machine to see live events."}
            </p>
          </CardContent>
        </Card>
      )}

      {error && engine !== "down" && (
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
            <InboxIcon className="h-5 w-5 text-blue-400" />
            Events
            <span className="text-xs font-normal text-slate-400" data-testid="inbox-count">
              {visible.length} of {events.length}
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading && events.length === 0 ? (
            <div className="flex items-center justify-center min-h-[200px]">
              <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
            </div>
          ) : visible.length === 0 ? (
            <p className="text-slate-500 py-8 text-center">No events in scope.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-800 text-left text-slate-400">
                    <th className="pb-2 pr-4 font-medium">Time</th>
                    <th className="pb-2 pr-4 font-medium">Type</th>
                    <th className="pb-2 pr-4 font-medium">Action</th>
                    <th className="pb-2 pr-4 font-medium">Name</th>
                    <th className="pb-2 font-medium">Image</th>
                  </tr>
                </thead>
                <tbody>
                  {visible.map((e) => (
                    <tr
                      key={`${e.time}-${e.type}-${e.action}-${e.name}-${e.image}`}
                      className="border-b border-slate-800/80 text-slate-200 hover:bg-slate-900/20 transition-colors"
                    >
                      <td className="py-2 pr-4 font-mono text-xs text-slate-400 whitespace-nowrap">
                        {formatTime(e.time)}
                      </td>
                      <td className="py-2 pr-4">
                        <span className="rounded bg-slate-800 px-1.5 py-0.5 text-xs text-slate-300">
                          {e.type}
                        </span>
                      </td>
                      <td className="py-2 pr-4 font-medium">{e.action}</td>
                      <td className="py-2 pr-4 font-mono text-xs">{e.name || "—"}</td>
                      <td className="py-2 font-mono text-xs text-slate-400">{e.image || "—"}</td>
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
