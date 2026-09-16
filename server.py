import asyncio
import json
import secrets
import socket
from pathlib import Path
from aiohttp import web, WSMsgType

ROOT = Path(__file__).parent
PUBLIC = ROOT / "public"
PORT = 8080

# room_code -> {"html": str, "clients": set[WebSocketResponse]}
rooms = {}


def get_local_ip():
    """Best-effort LAN IP discovery."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def new_room_code():
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    while True:
        code = "".join(secrets.choice(alphabet) for _ in range(6))
        if code not in rooms:
            return code


def ensure_room(code):
    code = code.upper()
    if code not in rooms:
        rooms[code] = {
            "html": """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Mi sitio local</title>
</head>
<body style="font-family:system-ui;display:grid;place-items:center;min-height:100vh">
  <main>
    <h1>🚀 Hola desde Local Web Builder</h1>
    <p>Este sitio está siendo servido por un servidor HTTP local.</p>
  </main>
</body>
</html>""",
            "clients": set(),
        }
    return rooms[code]


async def broadcast(code, html, sender=None):
    room = rooms.get(code)
    if not room:
        return

    room["html"] = html
    message = json.dumps({"type": "html", "html": html})

    dead = []
    for ws in list(room["clients"]):
        if ws is sender:
            continue
        try:
            await ws.send_str(message)
        except Exception:
            dead.append(ws)

    for ws in dead:
        room["clients"].discard(ws)


async def index(request):
    return web.FileResponse(PUBLIC / "index.html")


async def create_room(request):
    code = new_room_code()
    ensure_room(code)
    return web.json_response({
        "code": code,
        "builder_url": f"/?room={code}",
        "site_url": f"/site/{code}",
    })


async def room_state(request):
    code = request.match_info["code"].upper()
    if code not in rooms:
        return web.json_response({"error": "Sala no encontrada"}, status=404)

    return web.json_response({"code": code, "html": rooms[code]["html"]})


async def room_socket(request):
    code = request.match_info["code"].upper()
    if code not in rooms:
        raise web.HTTPNotFound(text="Sala no encontrada")

    ws = web.WebSocketResponse(heartbeat=30)
    await ws.prepare(request)

    room = rooms[code]
    room["clients"].add(ws)

    # Mandamos el estado actual al nuevo visitante/editor.
    await ws.send_str(json.dumps({"type": "html", "html": room["html"]}))

    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                except json.JSONDecodeError:
                    continue

                if data.get("type") == "set_html":
                    html = data.get("html")
                    if isinstance(html, str):
                        # Limitación razonable para el prototipo.
                        if len(html.encode("utf-8")) <= 2_000_000:
                            await broadcast(code, html, sender=ws)

                elif data.get("type") == "ping":
                    await ws.send_str(json.dumps({"type": "pong"}))

            elif msg.type == WSMsgType.ERROR:
                break
    finally:
        room["clients"].discard(ws)

    return ws


async def local_ip(request):
    return web.json_response({
        "ip": get_local_ip(),
        "port": PORT,
        "url": f"http://{get_local_ip()}:{PORT}/",
    })


async def site(request):
    """Serve a room as a real HTTP page: /site/ABC123"""
    code = request.match_info["code"].upper()
    if code not in rooms:
        raise web.HTTPNotFound(text="Sala no encontrada")

    return web.Response(
        text=rooms[code]["html"],
        content_type="text/html",
        charset="utf-8",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
        },
    )


app = web.Application()
app.router.add_get("/", index)
app.router.add_get("/api/local-ip", local_ip)
app.router.add_post("/api/rooms", create_room)
app.router.add_get("/api/rooms/{code}", room_state)
app.router.add_get("/ws/{code}", room_socket)
app.router.add_get("/site/{code}", site)
app.router.add_static("/assets/", PUBLIC / "assets", show_index=True)


if __name__ == "__main__":
    ip = get_local_ip()
    print()
    print("==============================================")
    print(" Local Web Builder")
    print("==============================================")
    print(f" Builder:  http://127.0.0.1:{PORT}/")
    print(f" Red local: http://{ip}:{PORT}/")
    print(" Ctrl+C para detener el servidor.")
    print("==============================================")
    print()
    web.run_app(app, host="0.0.0.0", port=PORT)
