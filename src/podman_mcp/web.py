import json
import logging
import os
from collections.abc import AsyncGenerator
from typing import Literal

import httpx
from fastapi import Body, Depends, FastAPI, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from fastmcp import FastMCP

from podmanmcp.tools.containers import manage_containers
from podmanmcp.tools.images import manage_images
from podmanmcp.tools.system import manage_system
from podmanmcp.tools.pods import manage_pods
from podmanmcp.tools.compose import manage_compose

from .activity_log import (
    SortOrder,
    clear_logs,
    export_logs,
    log_activity,
    log_stats,
    query_logs,
)
from .ai import AIRouter
from .auth import authenticate
from .llm.manager import get_llm_manager

SortParam = Literal["asc", "desc"]
logger = logging.getLogger("podmanmcp")


def setup_webapp(app: FastAPI, mcp_app: FastMCP):
    """Setup standard SOTA web endpoints for Podman-MCP."""
    import time

    _start_time = time.time()
    ai_router = AIRouter(mcp_app)

    @app.get("/api/health")
    async def health():
        return {"status": "healthy", "service": "podman-mcp"}

    @app.get("/api/capabilities")
    async def capabilities():
        tools = await mcp_app.list_tools()
        return {
            "service": "podman-mcp",
            "pages": {
                "dashboard": True,
                "containers": True,
                "pods": True,
                "images": True,
                "volumes": True,   # New SOTA page
                "networks": True,  # New SOTA page
                "tools": True,
                "logs": True,
                "settings": True,
                "chat": True,
            },
            "tool_count": len(tools),
            "llm_glom": True,
        }

    @app.get("/api/tools")
    async def list_tools():
        tools = await mcp_app.list_tools()
        return {"tools": [t.name for t in tools]}

    @app.get("/api/llm/providers")
    async def llm_providers(refresh: bool = Query(False)):
        manager = get_llm_manager()
        if refresh:
            await manager.glom_local_providers_if_up(force=True)
        return {"success": True, "providers": manager.list_providers()}

    @app.get("/api/logs")
    async def logs_query(
        limit: int = Query(50, ge=1, le=500),
        offset: int = Query(0, ge=0),
        level: str | None = Query(None),
        kind: str | None = Query(None),
        search: str | None = Query(None),
        sort: str = Query("desc"),
        after_id: str | None = Query(None),
    ):
        order: SortOrder = "asc" if sort == "asc" else "desc"
        return query_logs(
            limit=limit,
            offset=offset,
            level=level,
            kind=kind,
            search=search,
            sort=order,
            after_id=after_id,
        )

    @app.get("/api/logs/stats")
    async def logs_stats():
        return log_stats()

    @app.get("/api/logs/export")
    async def logs_export(
        format: str = Query("json"),
        level: str | None = Query(None),
        kind: str | None = Query(None),
        search: str | None = Query(None),
        sort: str = Query("desc"),
    ):
        order: SortOrder = "asc" if sort == "asc" else "desc"
        if format not in ("json", "csv"):
            format = "json"
        body, media_type, filename = export_logs(
            format=format,
            level=level,
            kind=kind,
            search=search,
            sort=order,
        )
        log_activity("export", f"Logs exported as {format}", meta={"filename": filename})
        return Response(
            content=body,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @app.delete("/api/logs")
    async def logs_clear():
        clear_logs()
        log_activity("system", "Log buffer cleared", level="WARNING")
        return {"success": True}

    @app.get("/api/containers")
    async def api_containers():
        log_activity("tool_call", "manage_containers list (web API)")
        result = await manage_containers(operation="list")
        return result

    @app.get("/api/pods")
    async def api_pods():
        log_activity("tool_call", "manage_pods list (web API)")
        result = await manage_pods(operation="list")
        return result

    @app.get("/api/volumes")
    async def api_volumes():
        log_activity("tool_call", "manage_system volume_list (web API)")
        result = await manage_system(operation="volume_list")
        return result

    @app.post("/api/volumes/create")
    async def api_volume_create(payload: dict = Body(...)):
        name = payload.get("name")
        log_activity("tool_call", f"manage_system volume_create (web API): {name}")
        result = await manage_system(operation="volume_create", name=name)
        return result

    @app.post("/api/volumes/delete")
    async def api_volume_delete(payload: dict = Body(...)):
        name = payload.get("name")
        log_activity("tool_call", f"manage_system volume_delete (web API): {name}")
        result = await manage_system(operation="volume_delete", name=name)
        return result

    @app.get("/api/networks")
    async def api_networks():
        log_activity("tool_call", "manage_system network_list (web API)")
        result = await manage_system(operation="network_list")
        return result

    @app.post("/api/networks/create")
    async def api_network_create(payload: dict = Body(...)):
        name = payload.get("name")
        log_activity("tool_call", f"manage_system network_create (web API): {name}")
        result = await manage_system(operation="network_create", name=name)
        return result

    @app.post("/api/networks/delete")
    async def api_network_delete(payload: dict = Body(...)):
        name = payload.get("name")
        log_activity("tool_call", f"manage_system network_delete (web API): {name}")
        result = await manage_system(operation="network_delete", name=name)
        return result

    @app.get("/api/system")
    async def api_system():
        log_activity("tool_call", "manage_system status + info (web API)")
        status_res = await manage_system(operation="status")
        info_res = await manage_system(operation="info")
        
        # Format disk summary mock / placeholder for API structure compatibility
        disk_summary = {
            "total_containers_size": 0,
            "total_images_size": 0,
            "total_volumes_size": 0,
            "total_size": 0,
        }
        
        return {
            "status": status_res,
            "info": info_res.get("data") or info_res,
            "disk": {"disk_usage": {"summary": disk_summary}},
        }

    @app.get("/api/images")
    async def api_images():
        log_activity("tool_call", "manage_images list (web API)")
        return await manage_images(operation="list")

    @app.get("/api/compose/projects")
    async def api_compose_projects(all_: bool = Query(False, alias="all")):
        log_activity("tool_call", "list compose projects (web API)")
        
        # Scan repositories for folders containing podman-compose.yml or compose.yaml
        projects = []
        try:
            repos_dir = "d:\\Dev\\repos"
            if os.path.exists(repos_dir):
                for folder in os.listdir(repos_dir):
                    folder_path = os.path.join(repos_dir, folder)
                    if os.path.isdir(folder_path):
                        if (os.path.exists(os.path.join(folder_path, "podman-compose.yml")) or 
                            os.path.exists(os.path.join(folder_path, "compose.yaml")) or
                            os.path.exists(os.path.join(folder_path, "compose.yml"))):
                            projects.append({
                                "name": folder,
                                "path": folder_path.replace("\\", "/"),
                                "status": "stopped",  # Default state
                            })
        except Exception as e:
            logger.warning("Failed to auto-scan compose projects: %s", e)
            
        # Add local template projects
        if not projects:
            projects = [
                {
                    "name": "podman-mcp-compose",
                    "path": "d:/Dev/repos/podman-mcp",
                    "status": "stopped",
                }
            ]
            
        return {"success": True, "projects": projects}

    @app.get("/api/compose/ps")
    async def api_compose_ps(project: str = Query(...)):
        log_activity("tool_call", f"compose ps (web API): {project}")
        return await manage_compose(operation="ps", project_path=project)

    @app.post("/api/compose/up")
    async def api_compose_up(payload: dict = Body(...)):
        project = payload["project"]
        log_activity("tool_call", f"compose up (web API): {project}")
        return await manage_compose(
            operation="up",
            project_path=project,
            file_name=payload.get("file_name")
        )

    @app.post("/api/compose/down")
    async def api_compose_down(payload: dict = Body(...)):
        project = payload["project"]
        log_activity("tool_call", f"compose down (web API): {project}")
        return await manage_compose(
            operation="down",
            project_path=project,
            volumes=payload.get("volumes", False)
        )

    @app.get("/api/compose/logs")
    async def api_compose_logs(project: str = Query(...)):
        log_activity("tool_call", f"compose logs (web API): {project}")
        return await manage_compose(operation="logs", project_path=project)

    @app.get("/api/dashboard")
    async def api_dashboard():
        try:
            containers_res = await manage_containers(operation="list")
            images_res = await manage_images(operation="list")
            status_res = await manage_system(operation="status")
            pods_res = await manage_pods(operation="list")

            containers_list = containers_res.get("containers") or []
            images_list = images_res.get("images") or []
            pods_list = pods_res.get("pods") or []

            status_data = status_res.get("data") or {}
            
            # Map standard system info block for UI dashboard compatibility
            sys_info = {
                "podman_version": status_data.get("version", "Unknown"),
                "rootless": status_data.get("rootless", False),
                "containers": {
                    "total": len(containers_list),
                    "running": sum(1 for c in containers_list if c.get("state") == "running"),
                    "stopped": sum(1 for c in containers_list if c.get("state") != "running"),
                },
                "images": {
                    "total": len(images_list)
                },
                "memory": {
                    "total_formatted": "Allocated via VM"
                },
                "cpu": {
                    "cores": 0
                }
            }

            log_activity("tool_call", "dashboard aggregate (web API)")
            return {
                "containers": containers_list,
                "containers_status": "success" if containers_res.get("success") else "error",
                "containers_message": containers_res.get("message", ""),
                
                "pods": pods_list,
                "pods_status": "success" if pods_res.get("success") else "error",
                
                "system_info": sys_info,
                "system_status": "success" if status_res.get("success") else "error",
                
                "disk_summary": {
                    "total_containers_size": 0,
                    "total_images_size": sum(img.get("size", 0) for img in images_list),
                    "total_volumes_size": 0,
                    "total_size": sum(img.get("size", 0) for img in images_list),
                },
                "images": images_list,
                "images_count": len(images_list),
                "images_status": "success" if images_res.get("success") else "error",
            }
        except Exception as exc:
            log_activity("server", f"dashboard error: {exc}", level="ERROR")
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/api/chat")
    async def chat(payload: dict = Body(...), user: str = Depends(authenticate)):
        query = payload.get("query", "")
        provider = str(payload.get("provider") or "ollama")
        model = str(payload.get("model") or "llama3.2")
        endpoint = str(payload.get("endpoint") or "http://127.0.0.1:11434").rstrip("/")
        system_prompt = payload.get("system_prompt", "")
        stream = payload.get("stream", False)
        mode = payload.get("mode", "llm")
        history = payload.get("history", [])
        agentic_tools = payload.get("agentic_tools", False)

        log_activity("tool_call", f"chat via {provider}", meta={"model": model, "stream": stream, "mode": mode})

        if mode == "agentic" and stream:
            return StreamingResponse(
                _agentic_chat_stream(query, provider, model, endpoint, system_prompt, history),
                media_type="text/event-stream",
            )

        try:
            if provider == "ollama":
                async with httpx.AsyncClient(timeout=120.0) as client:
                    ollama_messages = []
                    if system_prompt:
                        ollama_messages.append({"role": "system", "content": system_prompt})
                    for h in history:
                        ollama_messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
                    ollama_messages.append({"role": "user", "content": query})
                    if stream:
                        return StreamingResponse(
                            _stream_ollama(client, endpoint, model, ollama_messages),
                            media_type="text/event-stream",
                        )
                    response = await client.post(
                        f"{endpoint}/api/chat",
                        json={"model": model, "messages": ollama_messages, "stream": False},
                    )
                    response.raise_for_status()
                    text = response.json().get("message", {}).get("content", "No response")
            elif provider == "lmstudio":
                async with httpx.AsyncClient(timeout=120.0) as client:
                    lm_messages = []
                    if system_prompt:
                        lm_messages.append({"role": "system", "content": system_prompt})
                    for h in history:
                        lm_messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
                    lm_messages.append({"role": "user", "content": query})
                    if stream:
                        return StreamingResponse(
                            _stream_lmstudio(client, endpoint, model, lm_messages),
                            media_type="text/event-stream",
                        )
                    response = await client.post(
                        f"{endpoint}/v1/chat/completions",
                        json={"messages": lm_messages, "model": model, "temperature": 0.7},
                    )
                    response.raise_for_status()
                    text = response.json()["choices"][0]["message"]["content"]
            else:
                return await ai_router.process_command(query)

            if agentic_tools:
                from .tool_orchestrator import _match_query, execute_tool

                tool_name = _match_query(query)
                if tool_name:
                    tool_result = await execute_tool(tool_name, query)
                    return {"response": text, "status": "success", "tool_calls": [tool_result]}
            return {"response": text, "status": "success"}
        except Exception as exc:
            log_activity("server", f"chat error: {exc}", level="ERROR")
            return {"response": f"AI Bridge Error: {exc}", "status": "error"}

    class _AgenticEvent:
        """SSE event types for agentic chat."""
        TEXT = "text"
        TOOL_CALL = "tool_call"
        TOOL_RESULT = "tool_result"
        DONE = "done"

    async def _agentic_chat_stream(
        query: str, provider: str, model: str, endpoint: str, system_prompt: str, history: list
    ) -> AsyncGenerator[str, None]:
        """Stream agentic chat with interleaved tool execution."""
        from .tool_orchestrator import _match_query, execute_tool, tool_to_nl_name

        tool_name = _match_query(query)
        tool_result = None

        if tool_name:
            yield f"data: {json.dumps({'type': _AgenticEvent.TEXT, 'content': f'Running {tool_to_nl_name(tool_name)}...'})}\n\n"
            yield f"data: {json.dumps({'type': _AgenticEvent.TOOL_CALL, 'tool': tool_name, 'nl_name': tool_to_nl_name(tool_name)})}\n\n"
            tool_result = await execute_tool(tool_name, query)
            yield f"data: {json.dumps({'type': _AgenticEvent.TOOL_RESULT, 'tool': tool_name, 'result': tool_result})}\n\n"

        async with httpx.AsyncClient(timeout=120.0) as client:
            msgs = []
            if system_prompt:
                msgs.append({"role": "system", "content": system_prompt})
            tool_summary = ""
            if tool_result and tool_result.get("success"):
                if isinstance(tool_result.get("result"), str):
                    tool_summary = f"\n\nTool result: {tool_result['result'][:1000]}"
                else:
                    tool_summary = "\n\nTool executed successfully."
            elif tool_result:
                tool_summary = f"\n\nTool returned: {tool_result.get('error', 'unknown error')}"

            user_content = f"{query}{tool_summary}" if tool_summary else query
            for h in history:
                msgs.append({"role": h.get("role", "user"), "content": h.get("content", "")})
            msgs.append({"role": "user", "content": user_content})

            if provider == "ollama":
                async for chunk in _stream_ollama_raw(client, endpoint, model, msgs):
                    yield f"data: {json.dumps({'type': _AgenticEvent.TEXT, 'content': chunk})}\n\n"
            elif provider == "lmstudio":
                async for chunk in _stream_lmstudio_raw(client, endpoint, model, msgs):
                    yield f"data: {json.dumps({'type': _AgenticEvent.TEXT, 'content': chunk})}\n\n"

        yield f"data: {json.dumps({'type': _AgenticEvent.DONE})}\n\n"

    async def _stream_ollama_raw(client, endpoint, model, messages) -> AsyncGenerator[str, None]:
        async with client.stream(
            "POST", f"{endpoint}/api/chat", json={"model": model, "messages": messages, "stream": True}, timeout=120
        ) as r:
            async for line in r.aiter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        yield data.get("message", {}).get("content", "")
                    except json.JSONDecodeError:
                        pass

    async def _stream_lmstudio_raw(client, endpoint, model, messages) -> AsyncGenerator[str, None]:
        async with client.stream(
            "POST",
            f"{endpoint}/v1/chat/completions",
            json={"messages": messages, "model": model, "temperature": 0.7, "stream": True},
            timeout=120,
        ) as r:
            async for line in r.aiter_lines():
                if line.startswith("data: "):
                    chunk = line[6:]
                    if chunk == "[DONE]":
                        break
                    try:
                        data = json.loads(chunk)
                        yield data["choices"][0].get("delta", {}).get("content", "")
                    except json.JSONDecodeError:
                        pass

    async def _stream_ollama(client, endpoint, model, messages):
        async with client.stream(
            "POST", f"{endpoint}/api/chat", json={"model": model, "messages": messages, "stream": True}, timeout=120
        ) as r:
            async for line in r.aiter_lines():
                if line:
                    import json as _json
                    try:
                        data = _json.loads(line)
                        yield data.get("message", {}).get("content", "")
                    except:
                        pass

    async def _stream_lmstudio(client, endpoint, model, messages):
        async with client.stream(
            "POST",
            f"{endpoint}/v1/chat/completions",
            json={"messages": messages, "model": model, "temperature": 0.7, "stream": True},
            timeout=120,
        ) as r:
            async for line in r.aiter_lines():
                if line.startswith("data: "):
                    chunk = line[6:]
                    if chunk == "[DONE]":
                        break
                    import json as _json
                    try:
                        data = _json.loads(chunk)
                        yield data["choices"][0].get("delta", {}).get("content", "")
                    except:
                        pass

    @app.get("/api/v1/diagnostics")
    async def diagnostics():
        import time
        try:
            import psutil
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            try:
                disk = psutil.disk_usage("/").percent
            except:
                disk = 0
        except ImportError:
            cpu = mem = disk = 0
        return {
            "success": True,
            "backend": {"port": 11113, "status": "running", "uptime": time.time() - _start_time},
            "system": {"cpu_percent": cpu, "memory_percent": mem, "disk_percent": disk},
            "tools": {"total": 9},
            "cua_status": {"tesseract_available": False, "window_found": False},
        }

    @app.post("/api/podman/recover")
    async def recover_podman():
        log_activity("system", "Attempting Podman Machine recovery via VM stop and start", level="WARNING")
        from podmanmcp.podman_context import run_podman_command
        
        # Halt and restart the local virtual machine runner
        stop_res = await run_podman_command(["machine", "stop"])
        start_res = await run_podman_command(["machine", "start"])
        
        success = stop_res["success"] and start_res["success"]
        msg = f"Podman Machine recovery complete. VM stop: {'success' if stop_res['success'] else 'failed'}. VM start: {'success' if start_res['success'] else 'failed'}."
        
        log_activity("system", msg, level="INFO" if success else "ERROR")
        return {"success": success, "message": msg}
