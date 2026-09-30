# PRISMSESSION.md

## Project
PRISM — Parallel Reasoning & Intelligence System Mesh

Repository:
https://github.com/ingenuousmorpheus/PRISM

## Owner direction — 2026-09-29

PRISM was one of the owner's early apps. Reframe and extend it as a **local multi-model AI war room** rather than a simple three-model bridge.

Do not throw away the lightweight FastAPI + WebSocket + vanilla frontend foundation.

The desired direction is:
- multiple AI seats/models;
- efficient selective routing;
- visible disagreement;
- evidence/provenance;
- persistent mission history;
- human oversight;
- eventually specialist nodes on other home PCs;
- measure cost/latency but optimize for verified usefulness, not cheap tokens alone.

Research reference:
`docs/WAR_ROOM_RESEARCH.md`

## Audit findings before enhancement

The original README overstated several capabilities relative to the code:
- cascade described conditional escalation but always executed Claude;
- vote-of-three described a majority result but the runtime only concatenated outputs;
- history was written to JSONL but the UI/server history reset after restart;
- Mythos silently borrowed Claude credentials when not configured;
- README claimed replay/fork/share and shared memory that were not implemented;
- UI said Esc abort even though cancel handling was absent;
- savings percentages were presented too confidently for a counterfactual estimate.

Treat truthfulness of runtime state as a design requirement.

## Work completed 2026-09-29

### Conditional cascade
`backend/router.py` now has deterministic step conditions.

The Claude escalation seat in `cascade` runs only when the cheap first-pass output begins with:

`[ESCALATE]`

### War-room strategy
New strategy:

`war-room`

Flow:
- Claude = skeptical/senior independent analyst;
- OpenClaw = practical/operator independent analyst;
- OpenClaw = low-cost chair that reconciles the reports.

The chair must preserve disagreement and return:
- CONSENSUS
- DISAGREEMENT
- DECISION/OUTPUT
- VERIFY NEXT

Rule:
**Evidence beats majority.**

### Persistent run ledger foundation
`backend/server.py` now:
- assigns a stable `run_id`;
- reloads `prism_runs.jsonl` on startup;
- keeps recent durable run history;
- records executed/skipped steps;
- surfaces conditional skips through WebSocket events.

### No silent Mythos substitution
`backend/adapters/mythos.py` no longer borrows Claude credentials.

If the optional third seat is not explicitly configured, it says it is unavailable.

### UI integrity
- war-room strategy is surfaced;
- skipped conditional calls are visible;
- savings language is labeled as an estimate;
- false "Esc to abort" hint was removed.

## Current next phase

**Planning update 2026-09-29:** the owner selected personal AI councils and small-team decision rooms from launch. The documentation-only enhancement below refines the future sequence; no additional implementation phase was started in this pass.

Continue with **PR-01 Mission Ledger**, then **PR-02 Capability Registry**.

Recommended immediate implementation:
1. make History rows fork/re-run tasks cleanly;
2. add a run details endpoint or structured record view;
3. persist exact provider/model per executed step;
4. add step outcome status (success/error/skipped);
5. add provider health/availability metadata;
6. replace hard-coded three-seat UI assumptions with a capability-driven renderer.

Then implement PR-03 adaptive routing.

## Architectural rule

PRISM should not become a huge framework by copying CrewAI, LangGraph, Agent Framework, MetaGPT, Langfuse or LiteLLM.

Borrow the important lessons:
- durable state;
- explainable routing;
- observability;
- human gates;
- validation;
- model health;
- structured roles.

PRISM's unique product identity is the decision layer:

> **the smallest council that produces a verified answer.**

## Continuation instruction

When the owner says:
**"Continue PRISM from the last phase"**

1. read this file;
2. inspect the live repo before editing;
3. read `docs/WAR_ROOM_RESEARCH.md`;
4. preserve existing work;
5. start at the first incomplete PR phase;
6. do not silently substitute providers/models;
7. do not claim completion without a concrete code/test/receipt basis.

## Decision-room research and plan saved - 2026-09-29

Codex reviewed source at `660856d62bacf318d21c7870f1bbc71c8451bee1` and primary product documentation for Council, Synode, TeamAI, Loomio and Polis. The codebase-memory project list contained no PRISM index, so repository source was inspected directly. This was a documentation assignment, not a feature build.

Updated `docs/WAR_ROOM_RESEARCH.md` with the owner's dual audience choice, verified current gaps, dated competitive sources, proposed differentiation, release gates and evaluation criteria. Updated `docs/ARCHITECTURE.md` to distinguish implemented behavior from proposed room/event/decision interfaces and correct the stale consensus and strategy descriptions.

Future priorities: reliable persistence and reconnect; personal/team room isolation; explicit human decision contracts; evidence and dissent; budget-aware councils; sensitivity analysis and outcome review. Competitive differentiation is a research hypothesis, not a claim that all other products lack these abilities. Existing features such as blind review and decision journals are explicitly credited to comparable products.

Known prerequisites remain unimplemented: unsafe HTML metadata/error insertion, stale consensus UI copy, swallowed journal-write errors, socket-owned execution, hard-coded seats, and incomplete run history. No production files, dependencies, credentials, model configuration or other project were changed. Do not mark any new capability shipped on the strength of this plan.
