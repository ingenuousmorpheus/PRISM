# PRISM — Architecture

Current-source baseline: `660856d62bacf318d21c7870f1bbc71c8451bee1` (reviewed 2026-09-29). The first sections describe implemented behavior; the final section is a proposed design only.

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
| vote-of-three        | 3     | independent answers, no computed vote |
| context-share        | 2     | compress → act                        |
| war-room             | 3     | skeptic + operator, then chair        |

The router returns a `Plan` of `Step` objects; the server respects
`step.parallel` to group adjacent steps into an `asyncio.gather`.

## WebSocket events

```
→ {type:"run", task, strategy}

← {type:"plan", run_id, strategy, steps[]}
← {type:"step_start", idx, agent, role, model}
← {type:"delta", idx, agent, delta, tokens_in, tokens_out, tps, elapsed_ms}
← {type:"step_done", idx, agent, tokens_in, tokens_out, cost_usd, elapsed_ms}
← {type:"step_skipped", idx, agent, role, reason}
← {type:"complete", totals, spent_usd, baseline_usd, saved_usd, saved_pct, summary, final_output}
← {type:"error", error}
```

## Why PRISM is cheap to add to

- Add an adapter: one file, one class, ~40 lines.
- Add a strategy: one function in `router.py`, returns `Plan(steps=[…])`.
- Current persistence is completed-run JSONL, reloaded at startup. It is not an event journal or resumable queue; write failures are currently swallowed.
- The frontend renders advertised strategies dynamically, but its agent meters still assume three named seats.

## Proposed decision-room architecture (not implemented)

The [decision-room plan](WAR_ROOM_RESEARCH.md#decision-room-enhancement-plan---2026-09-29) extends the existing runtime rather than replacing it with an orchestration framework. Personal and small-team rooms ship together on one self-hosted server; SQLite is the initial store. Multi-server deployment is deferred.

### Boundaries and data

- **Rooms:** `Room`, `Membership`, `Message` and attachment metadata. Owner/member/viewer checks apply to all API operations and subscriptions. AI seats have separate identities and no human voting authority.
- **Execution:** `Run`, step records, model configuration snapshots and usage records. A server-owned task supervises calls independently of socket connections. Provider keys remain server-side and are excluded from events and exports.
- **Evidence:** `Claim` and `Evidence` link source identity, retrieval date, excerpt, verification status and message/step provenance. Source presence is distinct from factual verification; retrieved content is untrusted input, not executable instructions.
- **Decisions:** `DecisionVersion` records the contract, options, criteria, dissent, frozen voting rules and human approval. `Outcome` records follow-up observations without mutating the accepted version.
- **Storage:** append-only domain events plus transactional read projections in SQLite. Event fields: `event_id`, `room_id`, optional `run_id`, room sequence, timestamp, type, schema version and payload. Minimize personal data; deletion/retention must cover projections, attachments, events and exports without promising permanent immutable content storage.

### Proposed API and lifecycle

- Version new endpoints under `/api/v1`: rooms/members/messages, runs/cancel, claims/evidence, decision versions/votes/finalize, outcomes and exports. Mutations take an idempotency key scoped to room and actor; optimistic version checks reject concurrent conflicting finalizations.
- New `/ws/v1` subscriptions specify room and last received sequence. Authorize first, replay persisted events, then stream live events. Persist before broadcast; a failed write produces a visible error rather than a success acknowledgement. Reconnect never creates a duplicate run.
- Run states: queued, running, awaiting_human, completed, failed, cancelled, interrupted. A browser disconnect leaves a server-owned run running within its budget; explicit cancellation stops new dispatch and cancels in-flight tasks where supported. Server restart marks unfinished runs interrupted; paid calls require explicit retry to avoid duplicate charges.
- Preserve legacy `/ws` run and existing config/history endpoints during migration through the new execution service. Import legacy JSONL once using content fingerprints; retain originals and mark incomplete provenance as unknown. Do not infer lost prompts from truncated task fields.
- Bound provider concurrency, input sizes, attachment sizes and model-call budgets. Reserve estimated maximum call cost before dispatch; reconcile reported usage afterward. Unknown pricing cannot support a guaranteed dollar cap, so block capped dispatch until configured or use an explicitly selected call/token limit.
- Private mode binds loopback by default. Team mode requires authenticated invitations, HTTPS, room authorization and WebSocket origin validation before remote exposure. Keep local-only room policy enforceable at provider selection; no silent cloud fallback.

### Verification and release

Deterministic tests must cover event ordering/replay, idempotency, room isolation, migration repeatability, persistence failure, cancellation, restart interruption, budget reservation, partial provider failure, rendering injection and decision conflicts. Live-provider checks are opt-in. Room usability and recommendation usefulness require human evaluation; runtime success does not certify decision correctness. External action execution and distributed workers remain deferred.
