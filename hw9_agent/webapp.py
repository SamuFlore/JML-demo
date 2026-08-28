from __future__ import annotations

import json
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .client import DeepSeekChatClient, ModelClientError
from .exercise import ExerciseBundle, build_review_prompt, deterministic_check


class ExerciseWebApp:
    def __init__(
        self,
        project_root: Path,
        source_root: str,
        exercise_dir: Path,
        model: str,
        base_url: str,
    ) -> None:
        self.project_root = project_root
        self.source_root = source_root
        self.bundle = ExerciseBundle.load(exercise_dir)
        self.model = model
        self.base_url = base_url
        self.static_dir = project_root / "web"

    def public_exercise(self) -> dict[str, Any]:
        samples = []
        for sample in self.bundle.config.get("samples", []):
            path = self.bundle.directory / sample["file"]
            samples.append({
                "id": sample["id"],
                "label": sample["label"],
                "content": path.read_text(encoding="utf-8"),
            })
        return {
            "id": self.bundle.config["id"],
            "title": self.bundle.config["title"],
            "method": self.bundle.config["method"],
            "default_mode": self.bundle.config["default_mode"],
            "allowed_modes": self.bundle.config["allowed_modes"],
            "placeholders": self.bundle.config["placeholders"],
            "requirement": self.bundle.requirement,
            "template": self.bundle.template,
            "samples": samples,
        }

    def review(self, data: dict[str, Any]) -> dict[str, Any]:
        submission = str(data.get("submission", ""))
        mode = str(data.get("mode", self.bundle.config["default_mode"]))
        history = data.get("history", [])
        if not isinstance(history, list):
            history = []
        checks = deterministic_check(self.bundle, submission)
        client = DeepSeekChatClient(model=self.model, base_url=self.base_url)
        prompt = build_review_prompt(
            self.project_root,
            self.source_root,
            self.bundle,
            submission,
            mode,
            history[-6:],
        )
        return {"checks": checks, "feedback": client.generate(prompt), "mode": mode}


def make_handler(app: ExerciseWebApp):
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(app.static_dir), **kwargs)

        def _json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/api/exercise":
                self._json(app.public_exercise())
                return
            if self.path == "/health":
                self._json({"status": "ok"})
                return
            if self.path == "/":
                self.path = "/index.html"
            super().do_GET()

        def do_POST(self):
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length > 1_000_000:
                    self._json({"error": "request too large"}, HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
                    return
                data = json.loads(self.rfile.read(length).decode("utf-8"))
                if self.path == "/api/check":
                    self._json({"checks": deterministic_check(app.bundle, str(data.get("submission", "")))})
                    return
                if self.path == "/api/review":
                    self._json(app.review(data))
                    return
                self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            except (ValueError, json.JSONDecodeError) as exc:
                self._json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            except ModelClientError as exc:
                self._json({"error": str(exc)}, HTTPStatus.SERVICE_UNAVAILABLE)
            except Exception as exc:
                self._json({"error": f"server error: {exc}"}, HTTPStatus.INTERNAL_SERVER_ERROR)

        def log_message(self, format, *args):
            print(f"[web] {self.address_string()} {format % args}")

    return Handler


def serve(app: ExerciseWebApp, host: str, port: int) -> None:
    server = ThreadingHTTPServer((host, port), make_handler(app))
    print(f"HW9 JML Learning Agent: http://{host}:{port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
