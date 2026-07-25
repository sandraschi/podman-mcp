import { defineConfig } from '@playwright/test';
export default defineConfig({
    testDir: './e2e', timeout: 60000, retries: 1,
    use: { baseURL: 'http://localhost:11112', headless: true, screenshot: 'only-on-failure' },
    webServer: {
        command: 'uv run python -m podman_mcp.server --port 11113',
        port: 11113, timeout: 30000, reuseExistingServer: false
    }
});
