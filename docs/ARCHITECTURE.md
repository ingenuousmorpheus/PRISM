# PRISM — Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                       FRONTEND (SPA)                         │
│  index.html · style.css · app.js                             │
│  ─ TASK input · strategy picker · RUN button                 │
│  ─ Progress bar · per-agent speedometers · token meters      │
│  ─ Live stream · summary · history tabs                      │
└───────────────────┬──────────────────────────────────────────┘
                    │  WebSocket /ws   (JSON events)
                    ▼
┌──────────────────────────────────────────────────────────────┐
│                 SERVER (FastAPI + uvicorn)                   │
│  backend/server.py                                           │
│  ─ /api/config   ─ /api/history   ─ /ws                      │
│                                                              │
│   _execute_plan(task, strategy)                              │
│     └─▶ router.plan() → [Step, Step, …]                      │
│     └─▶ for each step:                                       │
│          adapter.stream(prompt) → yields deltas              │
│          ↳ websocket push: delta · step_done                 │
│     └─▶ aggregate → "complete" event with summary            │
└──────┬──────────┬──────────┬────────────────────────────────┘
       │          │          │
       ▼          ▼          ▼
   ┌───────┐  ┌───────┐  ┌────────┐
   │Claude │  │OpenClaw│ │ Mythos │     ← adapters/*.py
   │ API   │  │  API   │ │  API   │        (each a BaseAdapter)
   └───────┘  └───────┘  └────────┘
```

## Agent adapter contract

```python
class BaseAdapter:
    name: str
    price_in: float        # $ / 1M input tokens
    price_out: float       # $ / 1M output tokens
    async def stream(prompt, system) -> AsyncIterator[dict]:
        # yields {"delta": str, "tokens_in": int, "tokens_out": int, "done": bool}
```

Every adapter is stateless and streams. The server is the only component
aware of multi-agent orchestration — adapters don't know about each other.

## Router strategies

| Strategy             | Steps | Pattern                               |
|----------------------|:-----:|---------------------------------------|
| draft-polish         | 2     | sequential: cheap → smart             |
| parallel-specialist  | 3     | parallel: reason ∥ structure ∥ create |
| cascade              | 2     | conditional escalation                |
| vote-of-three        | 3     | parallel consensus                    |
| context-share        | 2     | compress → act                        |

The router returns a `Plan` of `Step` objects; the server respects
`step.parallel` to group adjacent steps into an `asyncio.gather`.

## WebSocket events

```
→ {type:"run", task, strategy}

← {type:"plan", strategy, steps[]}
← {type:"step_start", idx, agent, role, model}
← {type:"delta", idx, agent, delta, tokens_in, tokens_out, tps, elapsed_ms}
← {type:"step_done", idx, agent, tokens_in, tokens_out, cost_usd, elapsed_ms}
← {type:"complete", totals, spent_usd, baseline_usd, saved_usd, saved_pct, summary, final_output}
← {type:"error", error}
```

## Why PRISM is cheap to add to

- Add an adapter: one file, one class, ~40 lines.
- Add a strategy: one function in `router.py`, returns `Plan(steps=[…])`.
- No DB required. No queue required. Just Python + websockets.
- The frontend auto-renders whatever strategies the server advertises.
