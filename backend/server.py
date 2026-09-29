"""PRISM server — FastAPI + WebSocket bridge.

Boot:
    python backend/server.py
"""
import os
import sys
import json
import time
import uuid
import asyncio
import pathlib
from contextlib import asynccontextmanager
from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from backend.adapters import get_adapter
from backend.router import plan, available_strategies, should_run, Step

FRONTEND = ROOT / "frontend"
RUN_LOG = ROOT / "prism_runs.jsonl"


def _load_history(limit: int = 200) -> list[dict]:
    """Reload durable local history after a PRISM restart."""
    if not RUN_LOG.exists():
        return []
    rows: list[dict] = []
    try:
        with RUN_LOG.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    return rows[-limit:]


RUN_HISTORY: list[dict] = _load_history()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "─" * 60)
    print("  PRISM · Parallel Reasoning & Intelligence System Mesh")
    print("  Local multi-model war room")
    print("─" * 60)
    print(
        f"  http://{os.getenv('PRISM_HOST','127.0.0.1')}:"
        f"{os.getenv('PRISM_PORT','7369')}"
    )
    print(f"  restored {len(RUN_HISTORY)} prior run(s)")
    print("─" * 60 + "\n")
    yield


app = FastAPI(title="PRISM", lifespan=lifespan)


@app.get("/")
async def root():
    return FileResponse(FRONTEND / "index.html")


app.mount("/static", StaticFiles(directory=FRONTEND), name="static")


@app.get("/api/config")
async def cfg():
    mythos_key = os.getenv("MYTHOS_API_KEY", "").strip()
    mythos_model = os.getenv("MYTHOS_MODEL", "").strip()
    return {
        "strategies": available_strategies(),
        "default": os.getenv("DEFAULT_STRATEGY", "cascade"),
        "agents": {
            "claude": {
                "model": os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5"),
                "configured": bool(os.getenv("CLAUDE_API_KEY")),
            },
            "openclaw": {
                "model": os.getenv("OPENCLAW_MODEL", "gpt-4o-mini"),
                "configured": bool(os.getenv("OPENCLAW_API_KEY")),
            },
            "mythos": {
                "model": mythos_model or "not configured",
                "configured": bool(mythos_key and mythos_model),
            },
        },
    }


@app.get("/api/history")
async def history():
    return RUN_HISTORY[-50:]


async def _run_step(
    step: Step,
    prev_output: str,
    ws: WebSocket,
    step_idx: int,
    total_steps: int,
    totals: dict,
):
    """Run one step, streaming deltas back over the websocket."""
    prompt = step.prompt.replace("{{prev}}", prev_output)
    agent = get_adapter(step.agent)

    await ws.send_json(
        {
            "type": "step_start",
            "idx": step_idx,
            "total": total_steps,
            "agent": step.agent,
            "role": step.role,
            "model": getattr(agent, "model", step.agent),
        }
    )
    t0 = time.perf_counter()
    collected, tin, tout = "", 0, 0
    first_token_t = None

    async for evt in agent.stream(prompt, step.system):
        if evt.get("delta"):
            if first_token_t is None:
                first_token_t = time.perf_counter()
            collected += evt["delta"]
            tin = evt.get("tokens_in", tin)
            tout = evt.get("tokens_out", tout)
            elapsed = max(0.001, time.perf_counter() - (first_token_t or t0))
            await ws.send_json(
                {
                    "type": "delta",
                    "agent": step.agent,
                    "role": step.role,
                    "idx": step_idx,
                    "delta": evt["delta"],
                    "tokens_in": tin,
                    "tokens_out": tout,
                    "tps": round(tout / elapsed, 1),
                    "elapsed_ms": int(elapsed * 1000),
                }
            )
        if evt.get("done"):
            tin = evt.get("tokens_in", tin)
            tout = evt.get("tokens_out", tout)

    total_elapsed = max(0.001, time.perf_counter() - t0)
    cost = agent.estimate_cost(tin, tout)
    totals.setdefault(
        step.agent,
        {"tokens_in": 0, "tokens_out": 0, "cost_usd": 0.0, "ms": 0},
    )
    totals[step.agent]["tokens_in"] += tin
    totals[step.agent]["tokens_out"] += tout
    totals[step.agent]["cost_usd"] += cost
    totals[step.agent]["ms"] += int(total_elapsed * 1000)

    await ws.send_json(
        {
            "type": "step_done",
            "idx": step_idx,
            "agent": step.agent,
            "role": step.role,
            "tokens_in": tin,
            "tokens_out": tout,
            "tps": round(tout / total_elapsed, 1),
            "elapsed_ms": int(total_elapsed * 1000),
            "cost_usd": round(cost, 5),
            "output_preview": collected[:280],
        }
    )
    return collected


async def _execute_plan(task: str, strategy: str, ws: WebSocket):
    p = plan(task, strategy)
    run_id = uuid.uuid4().hex[:12]
    await ws.send_json(
        {
            "type": "plan",
            "run_id": run_id,
            "strategy": p.strategy,
            "steps": [
                {
                    "agent": s.agent,
                    "role": s.role,
                    "parallel": s.parallel,
                    "weight": s.weight,
                    "when": s.when,
                }
                for s in p.steps
            ],
        }
    )

    totals: dict = {}
    outputs: list[str] = []
    prev = ""
    total = len(p.steps)
    executed_steps = 0
    skipped_steps = 0

    i = 0
    step_idx = 0
    while i < total:
        if p.steps[i].parallel:
            cluster = []
            while i < total and p.steps[i].parallel:
                cluster.append(p.steps[i])
                i += 1
            results = await asyncio.gather(
                *[
                    _run_step(s, prev, ws, step_idx + k, total, totals)
                    for k, s in enumerate(cluster)
                ]
            )
            executed_steps += len(cluster)
            outputs.extend(results)
            prev = "\n\n---\n\n".join(results)
            step_idx += len(cluster)
            continue

        step = p.steps[i]
        if not should_run(step, prev):
            skipped_steps += 1
            await ws.send_json(
                {
                    "type": "step_skipped",
                    "idx": step_idx,
                    "agent": step.agent,
                    "role": step.role,
                    "reason": f"condition '{step.when}' was not met",
                }
            )
            i += 1
            step_idx += 1
            continue

        out = await _run_step(step, prev, ws, step_idx, total, totals)
        executed_steps += 1
        outputs.append(out)
        prev = out
        i += 1
        step_idx += 1

    claude = get_adapter("claude")
    tin_total = sum(v["tokens_in"] for v in totals.values())
    tout_total = sum(v["tokens_out"] for v in totals.values())
    cost_total = sum(v["cost_usd"] for v in totals.values())
    baseline = claude.estimate_cost(tin_total, tout_total)
    savings = max(0.0, baseline - cost_total)
    savings_pct = (savings / baseline * 100) if baseline else 0.0

    summary = (
        f"Strategy '{p.strategy}' — {p.summary_template} "
        f"Executed {executed_steps} step(s), skipped {skipped_steps}. "
        f"Estimated savings vs. the configured Claude price baseline: "
        f"~${savings:.4f} ({savings_pct:.0f}%)."
    )

    record = {
        "run_id": run_id,
        "task": task[:500],
        "strategy": p.strategy,
        "totals": totals,
        "executed_steps": executed_steps,
        "skipped_steps": skipped_steps,
        "baseline_usd": round(baseline, 5),
        "spent_usd": round(cost_total, 5),
        "saved_usd": round(savings, 5),
        "saved_pct": round(savings_pct, 1),
        "final_output": prev,
        "summary": summary,
        "ts": time.time(),
    }
    RUN_HISTORY.append(record)
    del RUN_HISTORY[:-200]

    try:
        with RUN_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass

    await ws.send_json({"type": "complete", **record})


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except Exception:
                await ws.send_json({"type": "error", "error": "bad json"})
                continue
            if msg.get("type") == "run":
                task = msg.get("task", "").strip()
                strategy = msg.get(
                    "strategy", os.getenv("DEFAULT_STRATEGY", "cascade")
                )
                if not task:
                    await ws.send_json({"type": "error", "error": "empty task"})
                    continue
                try:
                    await _execute_plan(task, strategy, ws)
                except Exception as e:
                    await ws.send_json({"type": "error", "error": str(e)})
    except WebSocketDisconnect:
        return


if __name__ == "__main__":
    uvicorn.run(
        "backend.server:app",
        host=os.getenv("PRISM_HOST", "127.0.0.1"),
        port=int(os.getenv("PRISM_PORT", "7369")),
        reload=False,
    )
