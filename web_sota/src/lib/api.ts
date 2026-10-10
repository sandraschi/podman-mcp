// Same-origin by default (vite proxy in dev, backend-mounted dist in prod); absolute only inside Tauri.
const IN_TAURI =
  typeof window !== "undefined" && ("__TAURI__" in window || "__TAURI_INTERNALS__" in window);
export const API_BASE = IN_TAURI ? "http://127.0.0.1:11113" : "";
