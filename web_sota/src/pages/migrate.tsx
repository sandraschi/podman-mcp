import { ArrowLeftRight, FileCode, Container, Search, ShieldCheck, Download, Upload, Terminal } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const ACTIONS = [
  {
    icon: FileCode, label: "Convert Compose", desc: "docker-compose.yml → podman-compose.yml",
    tool: 'manage_migrate(operation="docker_compose_to_podman", source_path="<path>/docker-compose.yml")',
  },
  {
    icon: ArrowLeftRight, label: "Convert to Docker", desc: "podman-compose.yml → docker-compose.yml",
    tool: 'manage_migrate(operation="podman_compose_to_docker", source_path="<path>/podman-compose.yml")',
  },
  {
    icon: Container, label: "Migrate Image", desc: "Pull Docker Hub image for Podman",
    tool: 'manage_migrate(operation="migrate_image", image_name="nginx:latest", new_name="nginx:podman")',
  },
  {
    icon: Search, label: "Scan Artifacts", desc: "Find Docker artifacts to migrate",
    tool: 'manage_migrate(operation="scan_docker_artifacts")',
  },
  {
    icon: ShieldCheck, label: "Compatibility Check", desc: "Check if compose file works with Podman",
    tool: 'manage_migrate(operation="compatibility_check", source_path="<path>/docker-compose.yml")',
  },
  {
    icon: Upload, label: "Export for Docker", desc: "Export Podman image as Docker archive",
    tool: 'manage_migrate(operation="export_for_docker", image_name="<image>")',
  },
  {
    icon: FileCode, label: "Dockerfile → Containerfile", desc: "Copy Dockerfile to Containerfile",
    tool: 'manage_migrate(operation="dockerfile_to_containerfile", source_path="<path>/Dockerfile")',
  },
];

export function MigratePage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">Docker ↔ Podman Migration</h2>
        <p className="text-slate-400">Port between Docker Desktop and Podman seamlessly</p>
      </div>

      <div className="mb-6 bg-gradient-to-br from-purple-900/20 via-slate-900/50 to-transparent border border-purple-900/30 rounded-xl px-6 py-5">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-lg font-semibold text-white">Why migrate?</h3>
            <p className="text-sm text-slate-300 mt-1">
              Podman is a drop-in replacement for Docker with no background daemon, no root requirement,
              and native Kubernetes pod support. Compose files, Dockerfiles, and OCI images are compatible.
              Use the tools below or ask the AI on the Chat page to run any migration automatically.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2 mt-3">
          <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full bg-emerald-900/40 text-emerald-300 border border-emerald-700/40">
            Daemonless
          </span>
          <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full bg-blue-900/40 text-blue-300 border border-blue-700/40">
            OCI Compatible
          </span>
          <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs rounded-full bg-amber-900/40 text-amber-300 border border-amber-700/40">
            Docker CLI compatible
          </span>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {ACTIONS.map((a) => (
          <Card key={a.label} className="border-slate-800 bg-slate-950/50 hover:border-purple-800/50 transition-colors">
            <CardHeader className="pb-2">
              <div className="flex items-center gap-2">
                <a.icon className="h-5 w-5 text-purple-400" />
                <CardTitle className="text-white text-sm">{a.label}</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="text-sm text-slate-400 space-y-2">
              <p>{a.desc}</p>
              <code className="block bg-slate-900 border border-slate-800 rounded p-2 text-xs font-mono text-purple-300 overflow-x-auto whitespace-pre-wrap">
                {a.tool}
              </code>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Terminal className="h-5 w-5 text-amber-400" />
            <CardTitle className="text-white">Manual CLI Migration</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="text-sm text-slate-400 space-y-3">
          <p>You can also migrate manually using the CLI. Podman mirrors the Docker CLI 1:1:</p>
          <div className="grid gap-3 md:grid-cols-2">
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-3">
              <p className="text-xs font-medium text-slate-300 mb-2">Docker → Podman</p>
              <pre className="text-xs text-blue-300 font-mono whitespace-pre-wrap">
{`# Same compose file works
podman compose up -d

# Pull Docker Hub images
podman pull docker.io/nginx:latest

# Run containers the same way
podman run -d -p 8080:80 nginx

# Create Kubernetes-style pods
podman pod create --name my-pod`}
              </pre>
            </div>
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-3">
              <p className="text-xs font-medium text-slate-300 mb-2">Podman → Docker</p>
              <pre className="text-xs text-blue-300 font-mono whitespace-pre-wrap">
{`# Export image for Docker
podman save --format docker-archive \\
  -o myimage.tar myimage:latest

# Load into Docker
docker load -i myimage.tar

# Compose files are compatible
# Just use docker compose instead`}
              </pre>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
