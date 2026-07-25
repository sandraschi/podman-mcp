import { Cpu, RefreshCw, Save } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  getHealth,
  getLlmProviders,
  getLlmSettings,
  setLlmSettings,
  type LlmProvider,
} from "@/common/api";

const DEFAULT_ENDPOINTS: Record<string, string> = {
  ollama: "http://127.0.0.1:11434",
  lmstudio: "http://127.0.0.1:1234",
};

export function Settings() {
  const [provider, setProvider] = useState(() => getLlmSettings().provider);
  const [model, setModel] = useState(() => getLlmSettings().model);
  const [endpoint, setEndpoint] = useState(() => getLlmSettings().endpoint);
  const [providers, setProviders] = useState<LlmProvider[]>([]);
  const [apiStatus, setApiStatus] = useState<string | null>(null);
  const [loadingModels, setLoadingModels] = useState(false);

  const activeProvider = useMemo(
    () => providers.find((p) => p.type === provider),
    [providers, provider],
  );

  const modelOptions = useMemo(() => {
    const fromGlom = activeProvider?.models ?? [];
    if (fromGlom.length > 0) return fromGlom;
    return model ? [model] : [];
  }, [activeProvider, model]);

  const applyProvider = useCallback((next: string, list: LlmProvider[]) => {
    setProvider(next);
    const match = list.find((p) => p.type === next);
    if (match) {
      setEndpoint(match.base_url);
      if (match.models[0]) setModel(match.models[0]);
      return;
    }
    setEndpoint(DEFAULT_ENDPOINTS[next] ?? DEFAULT_ENDPOINTS.ollama);
  }, []);

  const refreshGlom = useCallback(
    async (force = false) => {
      setLoadingModels(true);
      setApiStatus("Querying Ollama and LM Studio…");
      try {
        const list = await getLlmProviders(force);
        setProviders(list);
        if (list.length === 0) {
          setApiStatus("No local LLM found (Ollama :11434, LM Studio :1234)");
          return;
        }
        const saved = getLlmSettings();
        const current =
          list.find((p) => p.type === (force ? provider : saved.provider)) ??
          list[0];
        applyProvider(current.type, list);
        setApiStatus(
          `Discovered: ${list.map((p) => `${p.type} (${p.models.length} models)`).join(", ")}`,
        );
      } catch (err) {
        setApiStatus(err instanceof Error ? err.message : "Model discovery failed");
      } finally {
        setLoadingModels(false);
      }
    },
    [applyProvider, provider],
  );

  useEffect(() => {
    void (async () => {
      setLoadingModels(true);
      try {
        const list = await getLlmProviders(false);
        setProviders(list);
        if (list.length > 0) {
          const saved = getLlmSettings();
          const current =
            list.find((p) => p.type === saved.provider) ?? list[0];
          applyProvider(current.type, list);
          if (saved.model) setModel(saved.model);
        }
      } catch {
        /* non-fatal on mount */
      } finally {
        setLoadingModels(false);
      }
    })();
  }, [applyProvider]);

  const onProviderChange = (next: string) => {
    applyProvider(next, providers);
  };

  const testApi = async () => {
    setApiStatus("Testing API…");
    try {
      await getHealth();
      setApiStatus("Backend reachable on port 11113");
    } catch (err) {
      setApiStatus(err instanceof Error ? err.message : "API test failed");
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">Settings</h2>
        <p className="text-slate-400">
          Local LLM glom-on (Ollama / LM Studio) and Podman MCP preferences
        </p>
      </div>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Cpu className="h-5 w-5 text-blue-500" />
            <CardTitle className="text-white">Local LLM (Glom On)</CardTitle>
          </div>
          <CardDescription className="text-slate-400">
            Backend probes Ollama and LM Studio; models populate the dropdown below.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {providers.length > 0 ? (
            <ul className="space-y-1 text-sm text-emerald-300/90">
              {providers.map((p) => (
                <li key={p.type}>
                  {p.type} at {p.base_url}
                  {p.models.length > 0
                    ? ` — ${p.models.slice(0, 4).join(", ")}${p.models.length > 4 ? "…" : ""}`
                    : " — no models listed"}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-500">
              No providers discovered yet. Start Ollama or LM Studio, then refresh.
            </p>
          )}

          <div className="grid gap-4 md:grid-cols-3">
            <div className="grid gap-2">
              <Label className="text-slate-300">Provider</Label>
              <Select value={provider} onValueChange={onProviderChange}>
                <SelectTrigger className="bg-slate-900 border-slate-800 text-slate-100">
                  <SelectValue placeholder="Select provider" />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-800 text-slate-100">
                  <SelectItem value="ollama">Ollama</SelectItem>
                  <SelectItem value="lmstudio">LM Studio</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <Label className="text-slate-300">API endpoint</Label>
              <Input
                value={endpoint}
                onChange={(e) => setEndpoint(e.target.value)}
                className="bg-slate-900 border-slate-800 text-slate-100"
              />
            </div>
            <div className="grid gap-2">
              <Label className="text-slate-300">Model</Label>
              <Select
                value={model || undefined}
                onValueChange={setModel}
                disabled={modelOptions.length === 0}
              >
                <SelectTrigger className="bg-slate-900 border-slate-800 text-slate-100">
                  <SelectValue
                    placeholder={
                      loadingModels ? "Loading models…" : "Select a model"
                    }
                  />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-800 text-slate-100 max-h-64">
                  {modelOptions.map((m) => (
                    <SelectItem key={m} value={m}>
                      {m}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            <Button
              className="bg-blue-600 hover:bg-blue-700 text-white"
              onClick={() => {
                setLlmSettings({ provider, model, endpoint });
                setApiStatus("LLM settings saved locally");
              }}
            >
              <Save className="mr-2 h-4 w-4" /> Save LLM settings
            </Button>
            <Button
              variant="outline"
              className="border-slate-800 text-slate-300 hover:bg-slate-800"
              disabled={loadingModels}
              onClick={() => void refreshGlom(true)}
            >
              <RefreshCw
                className={`mr-2 h-4 w-4 ${loadingModels ? "animate-spin" : ""}`}
              />
              Refresh models
            </Button>
            <Button
              variant="outline"
              className="border-slate-800 text-slate-300 hover:bg-slate-800"
              onClick={() => void testApi()}
            >
              Test API
            </Button>
          </div>
          {apiStatus && <p className="text-sm text-slate-400">{apiStatus}</p>}
        </CardContent>
      </Card>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-white">App information</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-slate-400 space-y-1">
          <p>Podman MCP webapp (SOTA)</p>
          <p>Frontend: 11112 · Backend: 11113</p>
          <p>Event logs: /logs · Fleet glom-on via GET /api/llm/providers</p>
        </CardContent>
      </Card>
    </div>
  );
}
