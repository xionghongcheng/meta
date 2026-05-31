#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Minimal workflow-driven local web UI server."""

from __future__ import annotations

import argparse
import json
import logging
import mimetypes
import threading
import traceback
import uuid
import webbrowser
from dataclasses import asdict, is_dataclass
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from infra import Config, create_project_logger
from workflows import WorkflowService
from shared_base.paths import CANON_DIR, default_memory_path


WEBUI_DIR = Path(__file__).resolve().parent
STATIC_DIR = WEBUI_DIR / "static"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
MEDIA_WORKFLOWS = {"material_first", "roughcut"}


def to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return {key: to_jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")
    if hasattr(value, "item") and callable(getattr(value, "item")):
        try:
            return value.item()
        except Exception:
            pass
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


class JobLogHandler(logging.Handler):
    def __init__(self, store: "JobStore", job_id: str):
        super().__init__(level=logging.INFO)
        self.store = store
        self.job_id = job_id
        self.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = self.format(record)
        except Exception:
            message = record.getMessage()
        self.store.append_log(self.job_id, message)


class JobStore:
    def __init__(self):
        self._jobs: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def create(self, workflow_id: str, payload: dict[str, Any]) -> str:
        job_id = uuid.uuid4().hex[:12]
        now = datetime.now().isoformat(timespec="seconds")
        with self._lock:
            self._jobs[job_id] = {
                "id": job_id,
                "workflow_id": workflow_id,
                "status": "queued",
                "message": "等待执行",
                "created_at": now,
                "updated_at": now,
                "payload": to_jsonable(payload),
                "logs": [],
                "result": None,
                "error": None,
            }
        return job_id

    def update(self, job_id: str, **fields: Any) -> None:
        with self._lock:
            job = self._jobs[job_id]
            job.update({key: to_jsonable(value) for key, value in fields.items()})
            job["updated_at"] = datetime.now().isoformat(timespec="seconds")

    def append_log(self, job_id: str, message: str) -> None:
        with self._lock:
            job = self._jobs[job_id]
            job["logs"].append(message)
            job["updated_at"] = datetime.now().isoformat(timespec="seconds")

    def get(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return json.loads(json.dumps(job, ensure_ascii=False)) if job else None

    def list(self) -> list[dict[str, Any]]:
        with self._lock:
            jobs = list(self._jobs.values())
            jobs.sort(key=lambda item: item["created_at"], reverse=True)
            return json.loads(json.dumps(jobs, ensure_ascii=False))


class WebUIService:
    def __init__(self):
        self.jobs = JobStore()
        self.default_memory_path = default_memory_path()
        self.default_memory_path.parent.mkdir(parents=True, exist_ok=True)
        self.media_lock = threading.Lock()

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "canon_dir": str(CANON_DIR),
            "memory_path": str(self.default_memory_path),
            "output_dir": Config.OUTPUT_DIR,
            "ui_mode": "creator-desk",
        }

    def list_workflows(self) -> list[dict]:
        return WorkflowService(memory_path=str(self.default_memory_path)).workflows()

    def advise_workflow(self, message: str) -> dict:
        service = WorkflowService(memory_path=str(self.default_memory_path))
        return service.advise(message)

    def profile(self, memory_path: str | None = None) -> dict:
        service = WorkflowService(memory_path=str(self.default_memory_path))
        return service.profile(memory_path=memory_path or str(self.default_memory_path))

    def ingest(self, files: list[str], out: str | None = None) -> dict:
        service = WorkflowService(memory_path=str(self.default_memory_path))
        result = service.ingest(files=files, out=out)
        return result

    def start_workflow(self, workflow_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        service = WorkflowService(memory_path=str(self.default_memory_path))
        known = {item["id"] for item in service.workflows()}
        if workflow_id not in known:
            raise ValueError(f"未知 workflow: {workflow_id}")

        job_id = self.jobs.create(workflow_id, payload)
        thread = threading.Thread(target=self._run_workflow, args=(job_id, workflow_id, payload), daemon=True)
        thread.start()
        return {"job_id": job_id}

    def _run_workflow(self, job_id: str, workflow_id: str, payload: dict[str, Any]) -> None:
        if workflow_id in MEDIA_WORKFLOWS and not self.media_lock.acquire(blocking=False):
            self.jobs.update(job_id, status="blocked", message="当前已有一个重型媒体任务在运行，请稍后重试")
            return

        logger_name = f"webui.workflow.{workflow_id}.{job_id}"
        logger = create_project_logger(Config.OUTPUT_DIR, logger_name)
        memory_handler = JobLogHandler(self.jobs, job_id)
        logger.addHandler(memory_handler)

        try:
            self.jobs.update(job_id, status="running", message=f"正在执行工作流：{workflow_id}")
            service = WorkflowService(config=Config, logger=logger, memory_path=str(self.default_memory_path))
            result = service.run(workflow_id, payload)
            self.jobs.update(job_id, status="success", message="工作流执行完成", result=result)
        except Exception as exc:
            logger.error("工作流执行异常: %s", exc, exc_info=True)
            self.jobs.update(
                job_id,
                status="error",
                message=str(exc),
                error={"message": str(exc), "traceback": traceback.format_exc()},
            )
        finally:
            logger.removeHandler(memory_handler)
            memory_handler.close()
            if workflow_id in MEDIA_WORKFLOWS and self.media_lock.locked():
                self.media_lock.release()


def make_handler(service: WebUIService):
    class Handler(BaseHTTPRequestHandler):
        server_version = "JianyingWorkflowUI/1.0"

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path in {"/", "/index.html", "/workbench", "/workbench/", "/workbench/index.html"}:
                return self._send_static("index.html")
            if parsed.path.startswith("/static/"):
                return self._send_static(parsed.path.removeprefix("/static/"))
            if parsed.path == "/api/health":
                return self._send_json(service.health())
            if parsed.path == "/api/workflows":
                return self._send_json({"workflows": service.list_workflows()})
            if parsed.path == "/api/jobs":
                return self._send_json({"jobs": service.jobs.list()})
            if parsed.path.startswith("/api/jobs/"):
                job_id = parsed.path.rsplit("/", 1)[-1]
                job = service.jobs.get(job_id)
                if not job:
                    return self._send_json({"error": "job not found"}, status=404)
                return self._send_json(job)
            if parsed.path == "/api/profile":
                query = parse_qs(parsed.query)
                memory = query.get("memory", [""])[0] or None
                try:
                    return self._send_json(service.profile(memory_path=memory))
                except Exception as exc:
                    return self._send_json({"error": str(exc)}, status=400)
            return self._send_json({"error": "not found"}, status=404)

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            try:
                payload = self._read_json()
            except Exception as exc:
                return self._send_json({"error": f"invalid json: {exc}"}, status=400)

            try:
                if parsed.path == "/api/workflows/advise":
                    return self._send_json(service.advise_workflow(str(payload.get("message", ""))))

                if parsed.path == "/api/workflows/run":
                    return self._send_json(
                        service.start_workflow(
                            workflow_id=str(payload.get("workflow_id", "")),
                            payload=dict(payload.get("payload", {})),
                        ),
                        status=202,
                    )

                if parsed.path == "/api/ingest":
                    files = payload.get("files", [])
                    if isinstance(files, str):
                        files = [line.strip() for line in files.splitlines()]
                    return self._send_json(service.ingest(files=files, out=payload.get("out")))

                # compatibility endpoints
                if parsed.path == "/api/suggest":
                    result = service.start_workflow(
                        workflow_id="script_first",
                        payload={"idea": str(payload.get("idea", ""))},
                    )
                    return self._send_json(result, status=202)

                if parsed.path == "/api/roughcut":
                    result = service.start_workflow(
                        workflow_id="roughcut",
                        payload=payload,
                    )
                    return self._send_json(result, status=202)
            except Exception as exc:
                return self._send_json({"error": str(exc)}, status=400)

            return self._send_json({"error": "not found"}, status=404)

        def log_message(self, fmt: str, *args: Any) -> None:
            return

        def _read_json(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length else b"{}"
            return json.loads(raw.decode("utf-8"))

        def _send_json(self, payload: Any, status: int = 200) -> None:
            body = json.dumps(to_jsonable(payload), ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_static(self, filename: str) -> None:
            file_path = STATIC_DIR / filename
            if not file_path.exists() or not file_path.is_file():
                return self._send_json({"error": "static file not found"}, status=404)
            data = file_path.read_bytes()
            content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", f"{content_type}; charset=utf-8")
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    return Handler


def run_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, open_browser: bool = False) -> None:
    service = WebUIService()
    httpd = ThreadingHTTPServer((host, port), make_handler(service))
    url = f"http://{host}:{port}"
    print(f"JianyingAgent workflow UI running at {url}")
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="JianyingAgent 本地网页工作台")
    parser.add_argument("--host", default=DEFAULT_HOST, help="监听地址，默认 127.0.0.1")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="监听端口，默认 8765")
    parser.add_argument("--open", action="store_true", help="启动后自动打开浏览器")
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    run_server(host=args.host, port=args.port, open_browser=args.open)
