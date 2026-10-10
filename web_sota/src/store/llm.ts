import { create } from "zustand";
import { getLlmProviders, type LlmProvider } from "@/common/api";

export const DEFAULT_ENDPOINTS: Record<string, string> = {
  ollama: "http://127.0.0.1:11434",
  lmstudio: "http://127.0.0.1:1234",
};

function readKey(key: string, fallback: string): string {
  try {
    // Fleet-standard keys first (llm_provider/llm_model shared across fleet
    // webapps), then this app's legacy podman-chat-* keys (one-time migration).
    const legacy =
      key === "llm_provider"
        ? "podman-chat-provider"
        : key === "llm_model"
          ? "podman-chat-model"
          : null;
    return localStorage.getItem(key) ?? (legacy ? localStorage.getItem(legacy) : null) ?? fallback;
  } catch {
    return fallback;
  }
}

function writeKey(key: string, value: string): void {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* private mode: state still works for the session */
  }
}

interface LlmState {
  providers: LlmProvider[];
  provider: string;
  model: string;
  endpoint: string;
  personality: string;
  customPrompt: string;
  loadingProviders: boolean;
  gpuDetected: boolean;
  setProvider: (p: string) => void;
  setModel: (m: string) => void;
  setEndpoint: (e: string) => void;
  setPersonality: (p: string) => void;
  setCustomPrompt: (c: string) => void;
  ensureProviders: () => Promise<void>;
  refreshProviders: () => Promise<void>;
  detectGpu: () => void;
}

export const useLlmStore = create<LlmState>()((set, get) => ({
  providers: [],
  provider: readKey("llm_provider", "ollama"),
  model: readKey("llm_model", "llama3.2"),
  endpoint: readKey("podman-chat-endpoint", "http://127.0.0.1:11434"),
  personality: readKey("podman-chat-persona", "expert"),
  customPrompt: readKey("podman-chat-custom-prompt", ""),
  loadingProviders: false,
  gpuDetected: false,
  setProvider: (provider) => {
    set({ provider });
    writeKey("llm_provider", provider);
    const match = get().providers.find((p) => p.type === provider);
    if (match) {
      set({ endpoint: match.base_url });
      writeKey("podman-chat-endpoint", match.base_url);
      if (match.models[0]) {
        set({ model: match.models[0] });
        writeKey("llm_model", match.models[0]);
      }
    } else {
      const fallback = DEFAULT_ENDPOINTS[provider] ?? DEFAULT_ENDPOINTS.ollama;
      set({ endpoint: fallback });
      writeKey("podman-chat-endpoint", fallback);
    }
  },
  setModel: (model) => {
    set({ model });
    writeKey("llm_model", model);
  },
  setEndpoint: (endpoint) => {
    set({ endpoint });
    writeKey("podman-chat-endpoint", endpoint);
  },
  setPersonality: (personality) => {
    set({ personality });
    writeKey("podman-chat-persona", personality);
  },
  setCustomPrompt: (customPrompt) => {
    set({ customPrompt });
    writeKey("podman-chat-custom-prompt", customPrompt);
  },
  ensureProviders: async () => {
    set({ loadingProviders: true });
    try {
      const list = await getLlmProviders(false);
      set({ providers: list });
      if (list.length > 0) {
        const { provider, model } = get();
        const match = list.find((p) => p.type === provider);
        if (match) {
          set({ endpoint: match.base_url });
          writeKey("podman-chat-endpoint", match.base_url);
          if (!model || !match.models.includes(model)) {
            const next = match.models[0] ?? model;
            set({ model: next });
            writeKey("llm_model", next);
          }
        }
      }
    } catch {
      /* non-fatal: providers stay empty, manual endpoint still works */
    } finally {
      set({ loadingProviders: false });
    }
  },
  refreshProviders: async () => {
    set({ loadingProviders: true });
    try {
      const list = await getLlmProviders(true);
      set({ providers: list });
      if (list.length > 0) {
        const { provider } = get();
        const match = list.find((p) => p.type === provider);
        if (match) {
          set({ endpoint: match.base_url });
          writeKey("podman-chat-endpoint", match.base_url);
          if (match.models[0]) {
            set({ model: match.models[0] });
            writeKey("llm_model", match.models[0]);
          }
        }
      }
    } catch {
      /* non-fatal */
    } finally {
      set({ loadingProviders: false });
    }
  },
  detectGpu: () => {
    set({ gpuDetected: typeof navigator !== "undefined" && "gpu" in navigator });
  },
}));
