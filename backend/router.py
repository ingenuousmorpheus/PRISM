"""Task splitter — decides which subagents run, with what prompt, in what order.

Returns a list of `Step` objects. The server drives them, streaming every token
back to the UI with the originating agent tagged so the progress bar, the
speedometers, and the token meters all stay in sync.
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class Step:
    agent: str                 # "claude" | "openclaw" | "mythos"
    prompt: str
    system: str = ""
    role:   str = ""           # human label: "drafter", "polisher", etc.
    parallel: bool = False     # if True, run concurrently with neighboring parallel steps
    weight:   float = 1.0      # contribution to the overall progress bar


@dataclass
class Plan:
    strategy: str
    steps: List[Step] = field(default_factory=list)
    summary_template: str = ""


BASE_SYS = ("You are a subagent inside PRISM, a local multi-agent bridge. "
            "Be concise. Assume another agent may build on your output.")


def _draft_polish(task: str) -> Plan:
    return Plan(
        strategy="draft-polish",
        steps=[
            Step("openclaw",
                 f"Draft a first-pass solution to this task. Be thorough but rough — "
                 f"a smarter model will polish it after you.\n\nTASK:\n{task}",
                 system=BASE_SYS + " You are the DRAFTER.",
                 role="drafter", weight=0.45),
            Step("claude",
                 "Here is a rough draft from another agent. Polish it: fix errors, "
                 "tighten logic, improve clarity. Output the final answer only.\n\n"
                 "DRAFT:\n{{prev}}\n\nORIGINAL TASK:\n" + task,
                 system=BASE_SYS + " You are the POLISHER.",
                 role="polisher", weight=0.55),
        ],
        summary_template="OpenClaw drafted; Claude polished. Final answer reflects "
                         "Claude's reasoning on OpenClaw's scaffold.",
    )


def _parallel_specialist(task: str) -> Plan:
    return Plan(
        strategy="parallel-specialist",
        steps=[
            Step("claude",
                 f"Handle the REASONING + ARCHITECTURE aspects of this task.\n\n{task}",
                 system=BASE_SYS + " Specialty: reasoning.",
                 role="reasoner", parallel=True, weight=0.4),
            Step("openclaw",
                 f"Handle the BOILERPLATE + STRUCTURE aspects of this task.\n\n{task}",
                 system=BASE_SYS + " Specialty: code structure & boilerplate.",
                 role="structurer", parallel=True, weight=0.3),
            Step("mythos",
                 f"Handle the CREATIVE + NAMING + UX aspects of this task.\n\n{task}",
                 system=BASE_SYS + " Specialty: creative/UX.",
                 role="creative", parallel=True, weight=0.3),
        ],
        summary_template="All three agents ran in parallel; each contributed their "
                         "specialty. Outputs were merged by PRISM.",
    )


def _cascade(task: str) -> Plan:
    return Plan(
        strategy="cascade",
        steps=[
            Step("openclaw",
                 f"Attempt this task. If you are NOT confident, start your reply "
                 f"with '[ESCALATE]'.\n\n{task}",
                 system=BASE_SYS, role="first-pass", weight=0.35),
            Step("claude",
                 "The cheaper agent flagged low confidence. Take over:\n\n"
                 "THEIR ATTEMPT:\n{{prev}}\n\nORIGINAL TASK:\n" + task,
                 system=BASE_SYS, role="escalation", weight=0.65),
        ],
        summary_template="Cascade: OpenClaw tried first, Claude only ran if needed.",
    )


def _vote(task: str) -> Plan:
    return Plan(
        strategy="vote-of-three",
        steps=[
            Step("claude",   task, BASE_SYS, "voter-A", parallel=True, weight=0.33),
            Step("openclaw", task, BASE_SYS, "voter-B", parallel=True, weight=0.33),
            Step("mythos",   task, BASE_SYS, "voter-C", parallel=True, weight=0.34),
        ],
        summary_template="Three independent answers; PRISM merged the consensus.",
    )


def _context_share(task: str) -> Plan:
    return Plan(
        strategy="context-share",
        steps=[
            Step("openclaw",
                 f"Read and distill the following into a compact brief (≤400 tokens) "
                 f"that another agent can act on without seeing the original.\n\n{task}",
                 system=BASE_SYS + " You are the CONTEXT COMPRESSOR.",
                 role="compressor", weight=0.25),
            Step("claude",
                 "Act on this distilled brief. Do not ask for the original.\n\n"
                 "BRIEF:\n{{prev}}",
                 system=BASE_SYS + " You act on compressed context.",
                 role="executor", weight=0.75),
        ],
        summary_template="OpenClaw compressed the context; Claude executed on the "
                         "distilled brief — saving ~70% input tokens.",
    )


_STRATEGIES = {
    "draft-polish":         _draft_polish,
    "parallel-specialist":  _parallel_specialist,
    "cascade":              _cascade,
    "vote-of-three":        _vote,
    "context-share":        _context_share,
}


def plan(task: str, strategy: str = "draft-polish") -> Plan:
    fn = _STRATEGIES.get(strategy, _draft_polish)
    return fn(task)


def available_strategies():
    return list(_STRATEGIES.keys())
