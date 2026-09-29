# PRISM — War Room Research & Efficiency Roadmap

_Last updated: 2026-09-29_

PRISM started as a lightweight local multi-model bridge. The stronger direction is a **human-supervised AI war room**: use several models only when they add information, keep disagreement visible, spend expensive tokens selectively, and require evidence before declaring consequential work complete.

This document records a GitHub landscape review and the design gaps PRISM should target without becoming another oversized orchestration framework.

## Public projects reviewed

### LangGraph
Repository: https://github.com/langchain-ai/langgraph

Strengths:
- durable/stateful workflows;
- long-running agents;
- explicit graph control;
- strong low-level orchestration primitives.

PRISM opportunity:
- keep a much smaller local runtime;
- make model disagreement and cost visible to a normal user;
- optimize whether another mind should be called at all.

### CrewAI
Repository: https://github.com/crewAIInc/crewAI

Strengths:
- crews + flows;
- role-based collaboration;
- guardrails, memory, knowledge and observability.

PRISM opportunity:
- dynamic councils instead of permanently configured crews;
- evidence-weighted arbitration;
- a single-screen "war room" showing why each seat was used and what it contributed.

### Microsoft Agent Framework
Repository: https://github.com/microsoft/agent-framework

Strengths:
- production-grade multi-agent workflows;
- Python/.NET/Go ecosystem;
- multiple providers and distributed/runtime patterns.

PRISM opportunity:
- be intentionally lightweight and local-first;
- make personal multi-model orchestration understandable without enterprise infrastructure.

### AutoGen
Repository: https://github.com/microsoft/autogen

AutoGen pioneered multi-agent chat/orchestration, but its own repository now directs new users toward Microsoft Agent Framework and states AutoGen is in maintenance mode.

PRISM lesson:
- do not anchor the architecture to one framework;
- keep adapters and routing policy separable.

### MagenticLite / Magentic-UI
Repository: https://github.com/microsoft/magentic-ui

Strengths:
- small-model efficiency;
- browser + local-file workflows;
- human steering/approval;
- sandboxing for risky browser actions.

PRISM opportunity:
- specialize in multi-model reasoning, disagreement, verification, and cost allocation rather than becoming another browser-automation app.

### MetaGPT
Repository: https://github.com/FoundationAgents/MetaGPT

Strengths:
- role-based "software company" organization;
- SOP-driven multi-agent collaboration;
- substantial automation around software tasks.

PRISM opportunity:
- assemble roles per mission instead of assuming one fixed organization;
- optimize for "minimum useful council" rather than maximum autonomous delegation.

### Langfuse
Repository: https://github.com/langfuse/langfuse

Strengths:
- traces;
- costs/latency;
- prompt management;
- evaluations/datasets;
- production observability.

PRISM opportunity:
- integrate the most important observability directly into the decision room;
- connect telemetry to routing decisions in real time rather than only inspecting traces afterward.

### RouteLLM / LLM routing projects
Examples:
- https://github.com/lm-sys/RouteLLM
- LiteLLM routing docs/repository ecosystem

Strengths:
- selecting cheaper models when quality is sufficient;
- model pools, fallback and routing;
- benchmarking cost/quality tradeoffs.

PRISM opportunity:
- optimize **cost per verified success**, not just cost per request/token;
- route additional models based on disagreement, evidence gaps, task risk and uncertainty.

### AgentRoom
Repository: https://github.com/CHPARK03/agentroom

Strengths:
- human approval gates;
- role/tool isolation;
- read-only QA;
- false-completion defense;
- resumable transcripts.

PRISM opportunity:
- generalize those reliability principles beyond coding;
- combine them with model/provider diversity, budget routing and a visual council.

---

# The gap PRISM should own

Most systems are strong in one of these areas:

1. orchestration,
2. routing,
3. observability,
4. multi-agent role play,
5. action automation.

PRISM should connect the missing layer:

> **When is another model worth calling, what did it add, what does it disagree with, what evidence supports the result, and did the extra call improve verified outcome enough to justify its cost?**

That is the PRISM war-room identity.

The design target is not "more agents."

It is:

> **the smallest council that produces a verified answer.**

---

# Efficiency features other systems often separate

## 1. Selective quorum

Do not run three expensive models by default.

Start with the cheapest capable seat.

Escalate only when:
- it explicitly reports uncertainty;
- a deterministic validator fails;
- the task is above a configured risk level;
- evidence is missing;
- a second opinion materially disagrees;
- or the user explicitly requests a council.

This is why PRISM's cascade must actually skip the expensive seat when no escalation is requested.

## 2. Evidence-weighted disagreement

Majority voting is weak when models share training data or repeat the same unsupported claim.

PRISM should eventually score:
- evidence supplied;
- independent source support;
- deterministic checks;
- model confidence calibration;
- contradiction with known facts;
- provenance.

**Evidence beats majority.**

## 3. Context broker

Sending the entire context to every seat wastes tokens.

Future PRISM should maintain:
- one canonical mission context;
- a compact shared digest;
- role-specific slices;
- source/provenance pointers;
- cache keys.

Each agent receives only what it needs.

## 4. Semantic + exact caching

Before paying for a model call:
- exact fingerprint cache;
- semantic similarity cache;
- reusable context summaries;
- stable tool results.

Cache entries must include model/version/prompt-policy provenance so stale results are not mistaken for current truth.

## 5. Cost per verified success

Token savings alone can reward cheap but wrong answers.

The meaningful metric is:

**total model/tool cost / verified successful missions**

Track:
- attempts;
- retries;
- escalation;
- validation pass/fail;
- human correction;
- final accepted result.

## 6. Model health and capability registry

Every seat should expose:
- provider;
- exact model;
- context limit;
- modalities;
- tool support;
- measured latency;
- recent failure rate;
- estimated prices;
- local/cloud/privacy class;
- current availability.

Do not silently substitute one model for another.

## 7. Persistent mission ledger

Every run should have:
- run_id;
- task;
- plan;
- exact agents/models;
- executed/skipped steps;
- prompts or hashes;
- outputs;
- costs;
- latency;
- evidence;
- validators;
- human decisions;
- final status.

The mission ledger is how PRISM becomes resumable and auditable.

## 8. Verification receipts

PRISM should distinguish:

PROPOSED -> EXECUTED -> VERIFIED

For coding, a receipt might be:
- tests passed;
- file hash;
- build output;
- git commit.

For research:
- source list;
- retrieval timestamps;
- contradictions.

For external actions:
- provider acknowledgement/receipt.

No receipt means no verified-complete claim.

## 9. Budget envelope

A run may have:
- maximum dollars;
- maximum model calls;
- maximum latency;
- local-only mode;
- allowed providers;
- minimum verification level.

The router should optimize inside that envelope.

## 10. War Room UI

The GUI should eventually show:
- mission;
- task graph;
- seats currently active;
- model/provider health;
- evidence cards;
- disagreements;
- budget remaining;
- calls skipped because they were unnecessary;
- validators/receipts;
- final decision packet.

The point is not a prettier chat window.

The point is to let the user **see the reasoning organization without exposing private chain-of-thought**: claims, evidence, decisions, status and provenance.

---

# Implementation phases

## PR-00 — Integrity pass
Status: STARTED 2026-09-29.

Goals:
- stop silent provider/model substitution;
- make cascade truly conditional;
- stop claiming fake majority synthesis;
- make cost claims clearly estimates;
- remove UI claims for features that do not exist.

## PR-01 — Mission ledger
Status: STARTED 2026-09-29.

Goals:
- durable history across restart;
- stable run_id;
- executed/skipped step counts;
- replay/fork UX.

## PR-02 — Capability registry
Planned.

Move model/provider metadata out of hard-coded UI assumptions.

Support:
- Claude;
- OpenAI-compatible endpoints;
- LM Studio;
- Ollama;
- future providers through clean adapters.

## PR-03 — Adaptive router
Planned.

Inputs:
- task type;
- difficulty;
- risk;
- budget;
- latency goal;
- privacy requirement;
- model health;
- cached prior evidence.

Output:
- explainable route;
- fallback chain;
- reason each rejected seat was not selected.

## PR-04 — Evidence & verifier layer
Planned.

Add deterministic validators before spending on another judge model.

Examples:
- JSON/schema validation;
- tests;
- lint/build;
- source-presence checks;
- file existence/hash checks;
- policy gates.

## PR-05 — Disagreement engine
Planned.

Only convene extra seats when material disagreement remains.

Persist:
- claim;
- supporting evidence;
- opposing evidence;
- unresolved uncertainty;
- chair decision;
- verification requirement.

## PR-06 — Context broker + cache
Planned.

Add:
- canonical mission digest;
- role-specific context slices;
- exact cache;
- optional semantic cache;
- provenance and TTL.

## PR-07 — Human gates + action receipts
Planned.

Any consequential external action should require explicit authorization unless the user has configured a narrow pre-approval policy.

State:
PROPOSED -> APPROVED -> SUBMITTED -> CONFIRMED / FAILED / UNKNOWN_VERIFYING

## PR-08 — Distributed specialist nodes
Planned.

Allow remote/local home machines to register specialties and health without giving them unrestricted system access.

A node should advertise capabilities rather than receiving arbitrary shell authority.

## PR-09 — Benchmark lab
Planned.

Benchmark PRISM against:
- always-strong-model;
- always-cheap-model;
- simple cascade;
- war room;
- cache + adaptive route.

Measure:
- verified success;
- cost;
- latency;
- retries;
- human correction rate.

---

# Current owner direction

PRISM should feel like a **war room**, not merely a model switcher.

The visual metaphor is:
- specialists take seats;
- only necessary seats light up;
- the chair summarizes consensus and disagreement;
- evidence is pinned to the board;
- expensive seats stay dark unless they are needed;
- the user remains the final authority for consequential actions.

The defining efficiency principle is:

> **Do not pay for another mind unless PRISM can explain why that mind is likely to add value.**
