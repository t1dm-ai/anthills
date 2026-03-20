"""
CoolFlow HVAC — FastAPI backend.

Run from the project root:
    uvicorn backend.server:app --reload --port 8000
"""

import asyncio
import json
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from anthills import Colony, Worker, WorkerContext
from anthills.board import Pheromone, BoardEvent

from .agents import (
    LeadQualifier,
    Dispatcher,
    TechSimulator,
    JobCompleter,
    InvoiceProcessor,
)
from .ledger import Ledger, current_entry as _current_entry


ledger = Ledger()


# ─── Serialization ────────────────────────────────────────────────────────────

def serialize_pheromone(p: Pheromone) -> dict:
    return {
        "id": p.id,
        "type": p.type,
        "payload": p.payload,
        "intensity": p.intensity,
        "deposited_by": p.deposited_by,
        "deposited_at": p.deposited_at.isoformat(),
        "ttl_seconds": p.ttl_seconds,
        "trail_id": p.trail_id,
        "metadata": p.metadata,
    }


def serialize_event(e: BoardEvent) -> dict:
    return {
        "id": e.id,
        "event_type": e.event_type,
        "pheromone_id": e.pheromone_id,
        "pheromone": serialize_pheromone(e.pheromone) if e.pheromone else None,
        "timestamp": e.timestamp.isoformat(),
    }


def serialize_worker(w: Worker, stats: dict | None = None) -> dict:
    s = stats or {}
    reacts = w.reacts_to
    return {
        "id": w.id,
        "name": w.name,
        "reacts_to": reacts[0] if len(reacts) == 1 else ", ".join(reacts),
        "status": s.get("status", "idle"),
        "processed_count": s.get("processed", 0),
        "error_count": s.get("errors", 0),
        "last_active": s.get("last_active"),
    }


# ─── Connection manager ───────────────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self._connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._connections.append(ws)

    def disconnect(self, ws: WebSocket):
        self._connections.discard(ws) if hasattr(self._connections, "discard") else None
        if ws in self._connections:
            self._connections.remove(ws)

    async def broadcast(self, message: dict):
        dead = []
        for ws in list(self._connections):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


# ─── Colony with broadcast hooks ──────────────────────────────────────────────

class HVACColony(Colony):
    """Colony that broadcasts worker lifecycle events to WebSocket clients."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # worker_id → {status, processed, errors, last_active}
        self._stats: dict[str, dict] = {}

    def get_stats(self, worker_id: str) -> dict:
        return self._stats.setdefault(worker_id, {
            "status": "idle",
            "processed": 0,
            "errors": 0,
            "last_active": None,
        })

    async def _invoke_worker_with_connectors(self, worker: Worker, pheromone: Pheromone) -> None:
        stats = self.get_stats(worker.id)
        stats["status"] = "busy"

        # ── Ledger: open entry ──────────────────────────────────────────────
        import uuid as _uuid
        invocation_id = str(_uuid.uuid4())
        entry = ledger.start(worker, pheromone, invocation_id)
        token = _current_entry.set(entry)

        await manager.broadcast({
            "type": "worker_started",
            "data": {"worker_id": worker.id, "pheromone_id": pheromone.id},
        })
        # Broadcast the "running" entry immediately so the UI can show it
        await manager.broadcast({"type": "ledger_entry", "data": ledger.serialize(entry)})

        # ── Build context with deposit spy ──────────────────────────────────
        required = getattr(worker, "connectors", [])
        resolved = (
            await self._connector_registry.resolve_many(required) if required else {}
        )
        ctx = WorkerContext(
            pheromone=pheromone,
            board=self._board,
            colony=self,
            worker_id=worker.id,
            connectors=resolved,
        )
        # Spy on ctx.deposit to capture first output pheromone
        _captured: list[dict] = []
        _orig_deposit = ctx.deposit

        def _spy_deposit(type, payload, intensity=1.0, **kwargs):
            if not _captured:
                _captured.append({"type": type, "payload": dict(payload)})
            return _orig_deposit(type=type, payload=payload, intensity=intensity, **kwargs)

        ctx.deposit = _spy_deposit  # type: ignore[method-assign]

        try:
            await worker.invoke(ctx)

            output = _captured[0] if _captured else {}
            ledger.complete(entry, output.get("type"), output.get("payload"))

            stats["status"] = "idle"
            stats["processed"] += 1
            stats["last_active"] = datetime.now(timezone.utc).isoformat()
            await manager.broadcast({
                "type": "worker_completed",
                "data": {
                    "worker_id": worker.id,
                    "pheromone_id": pheromone.id,
                    "processed_count": stats["processed"],
                },
            })
        except Exception as e:
            ledger.fail(entry, str(e))
            stats["status"] = "error"
            stats["errors"] += 1
            stats["last_active"] = datetime.now(timezone.utc).isoformat()
            await manager.broadcast({
                "type": "worker_error",
                "data": {"worker_id": worker.id, "error": str(e)},
            })
            raise
        finally:
            _current_entry.reset(token)
            # Broadcast the sealed entry
            await manager.broadcast({"type": "ledger_entry", "data": ledger.serialize(entry)})


# ─── Module-level state ───────────────────────────────────────────────────────

colony: HVACColony | None = None
registered_workers: list[Worker] = []
colony_started_at: str = ""


def build_colony() -> tuple[HVACColony, list[Worker]]:
    col = HVACColony(
        name="CoolFlow HVAC",
        auto_halt=False,
        evaporation_interval=120,
    )

    workers = [
        LeadQualifier(name="LeadQualifier"),
        Dispatcher(name="Dispatcher"),
        TechSimulator(name="TechSimulator"),
        JobCompleter(name="JobCompleter"),
        InvoiceProcessor(name="InvoiceProcessor"),
    ]

    for w in workers:
        col.register_worker(w)

    # Broadcast every pheromone deposit to all UI clients
    async def on_deposit(p: Pheromone):
        await manager.broadcast({
            "type": "pheromone_deposited",
            "data": serialize_pheromone(p),
        })

    col.board.subscribe("*", on_deposit)

    return col, workers


def get_colony_state() -> dict:
    return {
        "id": colony.id,
        "name": colony.name,
        "status": "running" if colony._running else "stopped",
        "workers": [
            serialize_worker(w, colony.get_stats(w.id))
            for w in registered_workers
        ],
        "pheromone_count": len(colony.board.snapshot()),
        "event_count": len(colony.events()),
        "started_at": colony_started_at,
    }


# ─── App lifecycle ────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    global colony, registered_workers, colony_started_at

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("⚠️  ANTHROPIC_API_KEY not set — Claude agents will fail.")
        print("   Export it before starting: export ANTHROPIC_API_KEY=sk-...")

    colony, registered_workers = build_colony()
    colony_started_at = datetime.now(timezone.utc).isoformat()

    asyncio.create_task(colony.run_async())
    print(f"✅ {colony.name} colony running — {len(registered_workers)} agents registered")
    print("   Workers:", ", ".join(w.name for w in registered_workers))

    yield

    if colony:
        colony.stop()
        print("🛑 Colony stopped")


app = FastAPI(title="CoolFlow HVAC API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── WebSocket ────────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send current state immediately on connect
        await websocket.send_json({
            "type": "colony_state",
            "data": get_colony_state(),
        })
        await websocket.send_json({
            "type": "board_snapshot",
            "data": {
                "pheromones": [serialize_pheromone(p) for p in colony.board.snapshot()],
                "events": [serialize_event(e) for e in colony.events()],
            },
        })
        await websocket.send_json({
            "type": "ledger_snapshot",
            "data": {
                "entries": [ledger.serialize(e) for e in ledger.all()],
                "chain_valid": ledger.verify_chain(),
            },
        })

        # Keep alive — handle any messages from the client
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
                if msg.get("type") == "deposit":
                    colony.deposit(type=msg["pheromone_type"], payload=msg["payload"])
            except Exception:
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ─── REST endpoints ───────────────────────────────────────────────────────────

@app.post("/api/deposit")
async def deposit(body: dict):
    """Deposit a pheromone onto the colony board."""
    p = colony.deposit(type=body["type"], payload=body["payload"])
    return {"id": p.id, "type": p.type, "trail_id": p.trail_id}


@app.get("/api/state")
async def get_state():
    """Full colony + board snapshot."""
    return {
        "colony": get_colony_state(),
        "pheromones": [serialize_pheromone(p) for p in colony.board.snapshot()],
        "events": [serialize_event(e) for e in colony.events()],
    }


@app.get("/api/health")
async def health():
    return {"status": "ok", "colony": colony.name if colony else None}


@app.get("/api/ledger")
async def get_ledger():
    """Full agent action ledger."""
    return {
        "entries": [ledger.serialize(e) for e in ledger.all()],
        "chain_valid": ledger.verify_chain(),
        "total": len(ledger.all()),
    }


@app.get("/api/ledger/verify")
async def verify_ledger():
    """Verify the chain integrity of the ledger."""
    entries = ledger.all()
    return {
        "chain_valid": ledger.verify_chain(),
        "total_entries": len(entries),
        "sealed_entries": sum(1 for e in entries if e.hash is not None),
    }


@app.post("/api/reset")
async def reset():
    """Clear the board and ledger, broadcast a fresh snapshot to all clients."""
    colony.board.clear()
    ledger._entries.clear()
    await manager.broadcast({
        "type": "board_snapshot",
        "data": {"pheromones": [], "events": []},
    })
    await manager.broadcast({
        "type": "ledger_snapshot",
        "data": {"entries": [], "chain_valid": True},
    })
    await manager.broadcast({
        "type": "colony_state",
        "data": get_colony_state(),
    })
    return {"ok": True}
