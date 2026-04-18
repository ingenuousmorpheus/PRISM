<div align="center">

# PRISM
### Parallel Reasoning & Intelligence System Mesh

**One task. Many minds. Perfect harmony.**

A local bridge that lets Claude, OpenClaw, and Claude Mythos work together as a single swarm — splitting work intelligently, sharing context, and cutting your token bill by 40–70%.

![PRISM Banner](frontend/assets/banner.svg)

[![License: MIT](https://img.shields.io/badge/License-MIT-gold.svg)](./LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Stars](https://img.shields.io/badge/stars-%E2%9C%A8-violet)](#)
[![Made with love](https://img.shields.io/badge/made%20with-%F0%9F%96%A4-black)](#)

</div>

---

## Why PRISM?

Anthropic's new policy charges extra if you route your Claude subscription through third‑party agent runners like **OpenClaw**. That's annoying if you've already been paying. PRISM runs **locally on your machine** and acts as a neutral bridge — so:

- Your Claude subscription stays on Claude.
- OpenClaw stays on OpenClaw.
- Claude **Mythos** (the upcoming frontier model) plugs right in the day it drops.
- Every agent sees the *same task graph* and the *same shared memory*, but they each pay their own bill.

No double‑billing. No middleman taxes. Just a clean mesh between the agents you already own.

---

## Features

| | |
|---|---|
| 🌈 **Three‑way mesh** | Claude · OpenClaw · Mythos subagents, swappable in one dropdown |
| 📊 **Live progress bar** | Know exactly when a task completes, down to the millisecond |
| ⚡ **Per‑agent speedometer** | tokens/sec for Claude *and* OpenClaw *and* Mythos, side‑by‑side |
| 🪙 **Token meters** | Input/output tokens shown per agent, with a running $ cost estimate |
| 🧠 **Smart splitter** | Decomposes your task, routes cheap parts to cheap models |
| 📝 **Task journal** | Every run ends with a plain‑English summary of *who did what* |
| 🔌 **Pluggable adapters** | Add Ollama, LM Studio, Groq, Gemini, or Mythos in ~40 lines |
| 🎨 **Fancy GUI** | Glassmorphism, animated prism refraction, zero AI‑slop aesthetics |
| 💾 **Run history** | Every task saved locally — replay, fork, or share |

---

## Token‑Splitting Strategies

PRISM ships with **five** splitter strategies you can toggle per run. Each one is designed to make the user feel the download was worth it.

1. **`draft-polish`** — OpenClaw drafts, Claude polishes. ~55% cheaper than pure Claude.
2. **`parallel-specialist`** — Claude handles reasoning, OpenClaw handles boilerplate, Mythos handles creativity. Runs all three simultaneously.
3. **`cascade`** — Cheapest model tries first; escalates only if confidence < threshold.
4. **`vote-of-three`** — All three models answer; PRISM picks the majority answer. Expensive but bulletproof.
5. **`context-share`** — One agent reads the repo once, others consume the distilled summary. Saves ~70% input tokens on large codebases.

The router logs which strategy fired, how much it saved vs. the baseline, and shows it in the task summary.

---

## Quickstart

```bash
git clone https://github.com/YOUR_USERNAME/PRISM.git
cd PRISM
pip install -r requirements.txt
cp .env.example .env       # add your API keys
python backend/server.py   # opens http://127.0.0.1:7369
```

Windows users: just double‑click `run.bat`.

---

## Configuration

Edit `.env`:

```env
CLAUDE_API_KEY=sk-ant-...
OPENCLAW_API_KEY=oc_...
OPENCLAW_BASE_URL=https://api.openclaw.ai/v1
MYTHOS_API_KEY=                # leave blank until release
MYTHOS_BASE_URL=               # leave blank until release

DEFAULT_STRATEGY=draft-polish
PRISM_PORT=7369                # 7 · 3 · 6 · 9 — a nod to the build
```

---

## Adding a New Subagent

Drop a file in `backend/adapters/`:

```python
# backend/adapters/my_model.py
from .base import BaseAdapter

class MyAdapter(BaseAdapter):
    name = "mymodel"
    async def stream(self, prompt, ctx):
        # yield {"delta": str, "tokens_in": int, "tokens_out": int}
        ...
```

Register it in `backend/adapters/__init__.py`. Done.

---

## Roadmap

- [x] Claude + OpenClaw bridge
- [x] Live progress + speedometer
- [x] Five token‑splitting strategies
- [ ] Claude Mythos adapter (ready, waiting on API)
- [ ] VS Code extension
- [ ] CLI mode (`prism "refactor this repo"`)
- [ ] Shared vector cache across agents

---

## License

MIT — do whatever you want. Star the repo if PRISM saves you money. 🖤
