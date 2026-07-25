import { useState, useEffect, useCallback } from 'react';
import { Sidebar } from './sidebar';
import { Topbar } from './topbar';
import { useConnection } from '@/store/connection';
import { useZoom } from '@/lib/useZoom';
// import { Toaster } from '@/components/ui/toaster';

const BACKEND_PORT = 11113;
const BACKOFF = [1, 2, 4, 8, 16, 30];

interface AppLayoutProps {
    children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
    useZoom();
    const [collapsed, setCollapsed] = useState(false);

    const tick = useCallback(async () => {
        let attempt = 0;
        const poll = async () => {
            try {
                const r = await fetch(`http://127.0.0.1:${BACKEND_PORT}/api/health`, { signal: AbortSignal.timeout(5000) });
                if (r.ok) { useConnection.setState({ state: "connected" }); attempt = 0; }
                else useConnection.setState({ state: "offline", lastError: `HTTP ${r.status}` });
            } catch (e) {
                useConnection.setState({ state: "offline", lastError: e instanceof Error ? e.message : "Network error" });
            }
            attempt = Math.min(++attempt, BACKOFF.length - 1);
            setTimeout(poll, BACKOFF[attempt] * 1000);
        };
        poll();
    }, []);

    useEffect(() => {
        tick();
    }, [tick]);

    // Tauri event bridge
    useEffect(() => {
        let unlisten: (() => void) | undefined;
        (async () => {
            try {
                const { listen } = await import("@tauri-apps/api/event");
                unlisten = await listen<string>("backend-status", (event) => {
                    if (event.payload === "ready") useConnection.setState({ state: "connected" });
                    else if (event.payload?.startsWith("error:")) useConnection.setState({ state: "error", lastError: event.payload });
                });
            } catch {
                // Not inside Tauri — HTTP polling handles it
            }
        })();
        return () => { if (unlisten) unlisten(); };
    }, []);

    // Persist sidebar state
    useEffect(() => {
        const stored = localStorage.getItem('sidebar-collapsed');
        if (stored !== null) setCollapsed(stored === 'true');
    }, []);

    const handleToggle = () => {
        const newState = !collapsed;
        setCollapsed(newState);
        localStorage.setItem('sidebar-collapsed', String(newState));
    };

    return (
        <div className="flex min-h-screen flex-col bg-slate-950 text-slate-50 font-sans selection:bg-emerald-500/30">
            <div className="flex flex-1 overflow-hidden">
                <Sidebar collapsed={collapsed} onToggle={handleToggle} />
                <div className="flex flex-1 flex-col overflow-hidden">
                    <Topbar />
                    <main className="flex-1 overflow-y-auto p-6 scroll-smooth">
                        <div className="mx-auto max-w-7xl animate-in fade-in duration-500">
                            {children}
                        </div>
                    </main>
                </div>
            </div>
            {/* <Toaster /> */}
        </div>
    );
}
