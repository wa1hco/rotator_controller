# Copyright (C) 2026 Jeff Millar, WA1HCO
# SPDX-License-Identifier: GPL-3.0-only
"""Loopback HTTP server for the browser UI.

The process binds ``127.0.0.1`` on a free port. Every page and API route
lives under ``/s/<token>/``. The token is the session key: it is in the
URL the app opens, and it is different each launch. A request without
that prefix is a 404.

Firmware that later serves the same static files implements ``/api/...``
at the site root, with no session prefix. The browser uses relative URLs,
so both layouts work.
"""

from __future__ import annotations

import asyncio
import json
import mimetypes
import socket
import threading
from pathlib import Path

from aiohttp import WSMsgType, web

from rotatorctl.document import SettingsError
from rotatorctl.protocol import CommandError
from rotatorctl.transport import TransportError
from rotatorctl_gui.state import IDLE_SECONDS, ApiError, AppState

STATE_KEY: web.AppKey[AppState] = web.AppKey("state")
STOP_KEY: web.AppKey[asyncio.Event] = web.AppKey("stop")

STATIC_TYPES = {
    ".css": "text/css",
    ".html": "text/html",
    ".js": "text/javascript",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
}


def static_dir() -> Path:
    import sys

    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", "")
        return Path(meipass) / "rotatorctl_gui" / "static"
    return Path(__file__).resolve().parent / "static"


def build_app(state: AppState) -> web.Application:
    app = web.Application(middlewares=[local_only, errors])
    app[STATE_KEY] = state
    prefix = f"/s/{state.token}"
    app.router.add_get(prefix, _slash)
    app.router.add_get(prefix + "/", index)
    app.router.add_get(prefix + "/static/{name}", static_file)
    routes = {
        ("GET", "/api/boot"): boot,
        ("GET", "/api/schema"): schema,
        ("GET", "/api/pages"): pages,
        ("GET", "/api/catalog"): catalog,
        ("GET", "/api/document"): document,
        ("POST", "/api/document/new"): new_document,
        ("POST", "/api/document/edit"): edit_document,
        ("POST", "/api/document/preview"): preview_document,
        ("POST", "/api/document/save"): save_document,
        ("POST", "/api/document/upload"): upload_document,
        ("GET", "/api/document/download"): download_document,
        ("POST", "/api/document/push"): push_document,
        ("POST", "/api/preset/apply"): apply_preset,
        ("POST", "/api/override"): override,
        ("GET", "/api/files"): files,
        ("POST", "/api/files/open"): open_file,
        ("GET", "/api/controllers"): controllers,
        ("POST", "/api/controllers/scan"): scan,
        ("POST", "/api/controllers/add"): add_controller,
        ("POST", "/api/controllers/connect"): connect,
        ("POST", "/api/controllers/disconnect"): disconnect,
        ("GET", "/api/device"): device,
        ("POST", "/api/device/edit"): edit_device,
        ("POST", "/api/device/preview"): preview_device,
        ("POST", "/api/device/save"): save_device,
        ("POST", "/api/device/backup"): backup_device,
        ("POST", "/api/device/restore"): restore_device,
        ("POST", "/api/device/compare"): compare_device,
        ("POST", "/api/device/copy"): copy_device,
        ("POST", "/api/heartbeat"): heartbeat,
        ("POST", "/api/shutdown"): shutdown,
    }
    for (method, path), handler in routes.items():
        app.router.add_route(method, prefix + path, handler)
    app.router.add_get(prefix + "/api/ws", websocket)
    return app


def _state(request: web.Request) -> AppState:
    request.app[STATE_KEY].touch()
    return request.app[STATE_KEY]


async def _json(request: web.Request) -> dict:
    if not request.body_exists:
        return {}
    try:
        data = await request.json()
    except json.JSONDecodeError as exc:
        raise ApiError(400, "invalid", "body is not JSON") from exc
    if not isinstance(data, dict):
        raise ApiError(400, "invalid", "body is not a JSON object")
    return data


def _ok(payload: dict) -> web.Response:
    return web.json_response(payload)


@web.middleware
async def local_only(request: web.Request, handler):  # type: ignore[no-untyped-def]
    peer = request.remote or ""
    if peer not in ("127.0.0.1", "::1"):
        raise web.HTTPForbidden(text="loopback only")
    return await handler(request)


@web.middleware
async def errors(request: web.Request, handler):  # type: ignore[no-untyped-def]
    try:
        return await handler(request)
    except ApiError as exc:
        return web.json_response(exc.payload, status=exc.status)
    except SettingsError as exc:
        return web.json_response({"error": exc.code, "message": exc.message}, status=400)
    except (CommandError, TransportError, OSError) as exc:
        return web.json_response({"error": "controller", "message": str(exc)}, status=502)


async def _slash(request: web.Request) -> web.StreamResponse:
    raise web.HTTPFound(f"/s/{request.app[STATE_KEY].token}/")


async def index(_request: web.Request) -> web.Response:
    page = static_dir() / "index.html"
    if not page.is_file():
        raise web.HTTPNotFound(text="index.html is missing from the bundle")
    return web.Response(
        text=page.read_text(encoding="utf-8"),
        content_type="text/html",
        charset="utf-8",
        headers={"Content-Security-Policy": "default-src 'self'; style-src 'self'; img-src 'self'; script-src 'self'"},
    )


async def static_file(request: web.Request) -> web.Response:
    name = request.match_info["name"]
    if "/" in name or "\\" in name or name.startswith("."):
        raise web.HTTPNotFound()
    path = static_dir() / name
    if not path.is_file():
        raise web.HTTPNotFound()
    kind = STATIC_TYPES.get(path.suffix.lower()) or mimetypes.guess_type(name)[0] or "application/octet-stream"
    if kind.startswith("text/") or kind == "image/svg+xml":
        return web.Response(body=path.read_bytes(), content_type=kind, charset="utf-8")
    return web.Response(body=path.read_bytes(), content_type=kind)


async def boot(request: web.Request) -> web.Response:
    return _ok(_state(request).boot_payload())


async def schema(request: web.Request) -> web.Response:
    return _ok(_state(request).schema_payload())


async def pages(request: web.Request) -> web.Response:
    return _ok(_state(request).pages_payload())


async def catalog(request: web.Request) -> web.Response:
    return _ok(_state(request).catalog_payload())


async def document(request: web.Request) -> web.Response:
    return _ok(_state(request).document_payload())


async def new_document(request: web.Request) -> web.Response:
    return _ok(_state(request).new_document())


async def edit_document(request: web.Request) -> web.Response:
    body = await _json(request)
    return _ok(_state(request).edit_offline(str(body.get("name") or ""), str(body.get("value") or "")))


async def preview_document(request: web.Request) -> web.Response:
    return _ok(_state(request).preview_offline())


async def save_document(request: web.Request) -> web.Response:
    body = await _json(request)
    return _ok(_state(request).save_offline(str(body.get("name") or "")))


async def upload_document(request: web.Request) -> web.Response:
    body = await _json(request)
    return _ok(_state(request).load_text(str(body.get("text") or "")))


async def download_document(request: web.Request) -> web.Response:
    name, text = _state(request).download_text()
    return web.Response(
        text=text,
        content_type="application/yaml",
        charset="utf-8",
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )


async def push_document(request: web.Request) -> web.Response:
    return _ok(await asyncio.to_thread(_state(request).push_offline))


async def apply_preset(request: web.Request) -> web.Response:
    body = await _json(request)
    return _ok(_state(request).apply_preset(str(body.get("id") or "")))


async def override(request: web.Request) -> web.Response:
    body = await _json(request)
    raw = body.get("value")
    return _ok(_state(request).set_override(str(body.get("name") or ""), None if raw is None else str(raw)))


async def files(request: web.Request) -> web.Response:
    return _ok(_state(request).list_files())


async def open_file(request: web.Request) -> web.Response:
    body = await _json(request)
    return _ok(_state(request).open_named(str(body.get("name") or "")))


async def controllers(request: web.Request) -> web.Response:
    return _ok(_state(request).controllers_payload())


async def scan(request: web.Request) -> web.Response:
    body = await _json(request)
    timeout = float(body.get("timeout") or 0.8)
    state = _state(request)
    return _ok(await asyncio.to_thread(state.scan, timeout))


async def add_controller(request: web.Request) -> web.Response:
    body = await _json(request)
    port = int(body.get("port") or 0)
    return _ok(
        _state(request).add_controller(
            str(body.get("kind") or ""),
            host=str(body.get("host") or ""),
            port=port,
            path=str(body.get("path") or ""),
        )
    )


async def connect(request: web.Request) -> web.Response:
    body = await _json(request)
    state = _state(request)
    target = str(body.get("target") or "")
    discard = bool(body.get("discard"))
    return _ok(await asyncio.to_thread(lambda: state.connect(target, discard=discard)))


async def disconnect(request: web.Request) -> web.Response:
    return _ok(_state(request).disconnect())


async def device(request: web.Request) -> web.Response:
    return _ok(_state(request).device_payload())


async def edit_device(request: web.Request) -> web.Response:
    body = await _json(request)
    return _ok(_state(request).edit_device(str(body.get("name") or ""), str(body.get("value") if body.get("value") is not None else "")))


async def preview_device(request: web.Request) -> web.Response:
    return _ok(_state(request).preview_device())


async def save_device(request: web.Request) -> web.Response:
    return _ok(await asyncio.to_thread(_state(request).save_device))


async def backup_device(request: web.Request) -> web.Response:
    text = _state(request).backup_text()
    return web.Response(text=text, content_type="text/plain", charset="utf-8")


async def restore_device(request: web.Request) -> web.Response:
    body = await _json(request)
    text = str(body.get("text") or "")
    state = _state(request)
    if body.get("apply"):
        return _ok(await asyncio.to_thread(state.apply_restore, text))
    return _ok(state.preview_restore(text))


async def compare_device(request: web.Request) -> web.Response:
    body = await _json(request)
    return _ok(_state(request).compare_text(str(body.get("text") or "")))


async def copy_device(request: web.Request) -> web.Response:
    body = await _json(request)
    state = _state(request)
    target = str(body.get("target") or "")
    return _ok(await asyncio.to_thread(state.copy_from, target))


async def heartbeat(request: web.Request) -> web.Response:
    _state(request)
    return _ok({"ok": True})


async def shutdown(request: web.Request) -> web.Response:
    state = _state(request)
    stopper = request.app.get(STOP_KEY)
    if stopper is not None:
        stopper.set()
    return _ok({"ok": True, "idle_seconds": state.idle_seconds})


async def websocket(request: web.Request) -> web.WebSocketResponse:
    state = _state(request)
    socket = web.WebSocketResponse(heartbeat=20)
    await socket.prepare(request)
    state.socket_count += 1
    try:
        async for message in socket:
            state.touch()
            if message.type == WSMsgType.TEXT and message.data == "quit":
                stopper = request.app.get(STOP_KEY)
                if stopper is not None:
                    stopper.set()
                await socket.close()
                break
            if message.type in (WSMsgType.CLOSE, WSMsgType.ERROR):
                break
    finally:
        state.socket_count = max(0, state.socket_count - 1)
    return socket


def loopback_socket() -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 0))
    sock.listen(128)
    return sock


class Running:
    def __init__(self, state: AppState, url: str, loop: asyncio.AbstractEventLoop, thread: threading.Thread) -> None:
        self.state = state
        self.url = url
        self.loop = loop
        self.thread = thread

    def stop(self) -> None:
        stopper = getattr(self, "_stop", None)
        if stopper is not None:
            self.loop.call_soon_threadsafe(stopper.set)
        self.thread.join(timeout=5)
        self.state.close()


def start_server(state: AppState, *, idle_seconds: int | None = None) -> Running:
    """Start the loopback server on a background thread and return its URL."""

    if idle_seconds is not None:
        state.idle_seconds = idle_seconds
    sock = loopback_socket()
    host, port = sock.getsockname()[:2]
    sock.setblocking(False)
    ready = threading.Event()
    holder: dict[str, object] = {}

    def target() -> None:
        async def _main() -> None:
            stop = asyncio.Event()
            app = build_app(state)
            app[STOP_KEY] = stop
            runner = web.AppRunner(app)
            await runner.setup()
            await web.SockSite(runner, sock).start()
            holder["loop"] = asyncio.get_running_loop()
            holder["stop"] = stop
            ready.set()

            async def idle() -> None:
                if state.idle_seconds <= 0:
                    return
                while not stop.is_set():
                    await asyncio.sleep(1)
                    quiet = state.socket_count == 0 and (time_since(state) > state.idle_seconds)
                    if quiet:
                        stop.set()

            idle_task = asyncio.create_task(idle())
            await stop.wait()
            idle_task.cancel()
            await runner.cleanup()

        asyncio.run(_main())

    thread = threading.Thread(target=target, name="rotatorctl-http", daemon=True)
    thread.start()
    if not ready.wait(10):
        raise RuntimeError("the local server did not start")
    url = f"http://{host}:{port}/s/{state.token}/"
    running = Running(state, url, holder["loop"], thread)  # type: ignore[arg-type]
    running._stop = holder["stop"]  # type: ignore[attr-defined]
    return running


def time_since(state: AppState) -> float:
    import time

    return time.monotonic() - state.last_seen


def serve_until_stop(state: AppState, *, open_browser: bool) -> int:
    """Run in the foreground. Used by the double-click app."""

    import webbrowser

    running = start_server(state, idle_seconds=state.idle_seconds)
    if state.idle_seconds > 0:
        idle_line = f"The helper quits {state.idle_seconds} seconds after the last browser tab closes.\n"
    else:
        idle_line = "Idle quit is off.\n"
    message = (
        "Rotator Controller\n"
        f"{running.url}\n"
        + idle_line
        + "Use Quit in the page, or press Ctrl+C, to stop it now.\n"
    )
    print(message, flush=True)
    if open_browser:
        webbrowser.open(running.url)
    try:
        while running.thread.is_alive():
            running.thread.join(timeout=0.5)
    except KeyboardInterrupt:
        running.stop()
    state.close()
    return 0


# Re-export for callers that want the documented idle default.
__all__ = ["IDLE_SECONDS", "AppState", "Running", "build_app", "serve_until_stop", "start_server", "static_dir"]
