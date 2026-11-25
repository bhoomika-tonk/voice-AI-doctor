"""FastAPI: REST for the dashboard, SSE for live events, WebRTC offer for the call."""
import asyncio, json
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import BackgroundTasks, FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pipecat.transports.network.webrtc_connection import IceServer, SmallWebRTCConnection

import store
from bot import run_bot
from events import subscribe, unsubscribe

app = FastAPI()
connections: dict[str, SmallWebRTCConnection] = {}
ICE = [IceServer(urls="stun:stun.l.google.com:19302")]


@app.get("/api/doctors")
def doctors():
    return store.list_doctors()


@app.get("/api/appointments")
def appointments():
    return store.APPOINTMENTS


@app.get("/api/events")
async def events():
    q = subscribe()

    async def stream():
        try:
            while True:
                try:
                    ev = await asyncio.wait_for(q.get(), timeout=15)
                    yield f"data: {json.dumps(ev)}\n\n"
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
        finally:
            unsubscribe(q)

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.post("/api/offer")
async def offer(body: dict, background: BackgroundTasks):
    pc_id = body.get("pc_id")
    if pc_id and pc_id in connections:
        conn = connections[pc_id]
        await conn.renegotiate(sdp=body["sdp"], type=body["type"], restart_pc=body.get("restart_pc", False))
    else:
        conn = SmallWebRTCConnection(ICE)
        await conn.initialize(sdp=body["sdp"], type=body["type"])

        @conn.event_handler("closed")
        async def _closed(c):
            connections.pop(c.pc_id, None)

        background.add_task(run_bot, conn)
    answer = conn.get_answer()
    connections[answer["pc_id"]] = conn
    return answer

DIST = Path(__file__).parent.parent / "frontend" / "dist"
if DIST.exists():  # after `npm run build`, FastAPI serves the React app on :7860
    app.mount("/", StaticFiles(directory=DIST, html=True), name="web")
