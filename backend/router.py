"""PRISM routing plans.

A plan says which seat should run, in what order, and under what condition.
The server owns execution and telemetry.
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class Step:
    agent: str
    prompt: str
    system: str = ""
    role: str = ""
    parallel: bool = False
    weight: float = 1.0
    when: str = "always"


@dataclass
class Plan:
    strategy: str
    steps: List[Step] = field(default_factory=list)
    summary_template: str = ""


BASE_SYS = (
    "You are a subagent inside PRISM, a local multi-agent war room. "
    "Be concise, state uncertainty, and do not claim work was completed unless "
    "the evidence in your context supports it."
)


def should_run(step: Step, prev_output: str) -> bool:
    if step.when == "always":
        return True
    if step.when == "on_escalate":
        return prev_output.lstrip().upper().startswith("[ESCALATE]")
    raise ValueError(f"Unknown step condition: {step.when}")


def _draft_polish(task: str) -> Plan:
    return Plan(
        strategy="draft-polish",
        steps=[
            Step(
                "openclaw",
                f"Draft a first-pass solution to this task. Be thorough but rough — "
                f"a stronger reviewer will polish it after you.\n\nTASK:\n{task}",
                system=BASE_SYS + " You are the DRAFTER.",
                role="drafter",
                weight=0.45,
            ),
            Step(
                "claude",
                "Here is a rough draft from another agent. Polish it: fix errors, "
                "tighten logic, improve clarity, and preserve unresolved uncertainty. "
                "Output the final answer only.\n\n"
                "DRAFT:\n{{prev}}\n\nORIGINAL TASK:\n" + task,
                system=BASE_SYS + " You are the POLISHER.",
                role="polisher",
                weight=0.55,
            ),
        ],
        summary_template="OpenClaw drafted; Claude polished the result.",
    )


def _parallel_specialist(task: str) -> Plan:
    return Plan(
        strategy="parallel-specialist",
        steps=[
            Step(
                "claude",
                f"Handle the REASONING + ARCHITECTURE aspects of this task.\n\n{task}",
                system=BASE_SYS + " Specialty: reasoning.",
                role="reasoner",
                parallel=True,
                weight=0.4,
            ),
            Step(
                "openclaw",
                f"Handle the BOILERPLATE + STRUCTURE aspects of this task.\n\n{task}",
                system=BASE_SYS + " Specialty: code structure & boilerplate.",
                role="structurer",
                parallel=True,
                weight=0.3,
            ),
            Step(
                "mythos",
                f"Handle the CREATIVE + NAMING + UX aspects of this task.\n\n{task}",
                system=BASE_SYS + " Specialty: creative/UX.",
                role="creative",
                parallel=True,
                weight=0.3,
            ),
        ],
        summary_template=(
            "Specialists ran independently. Their outputs are kept separate so "
            "provenance remains visible instead of pretending an automatic merge occurred."
        ),
    )


def _cascade(task: str) -> Plan:
    return Plan(
        strategy="cascade",
        steps=[
            Step(
                "openclaw",
                "Attempt the task using the cheapest reasonable path. "
                "If you are not confident the answer is correct, important facts are "
                "missing, or deeper reasoning is needed, begin your reply with exactly "
                "[ESCALATE]. Otherwise do not use that marker.\n\n"
                f"TASK:\n{task}",
                system=BASE_SYS + " You are the FIRST-PASS seat.",
                role="first-pass",
                weight=0.35,
            ),
            Step(
                "claude",
                "The first-pass seat explicitly requested escalation. Independently "
                "check its reasoning, correct errors, and produce the final answer.\n\n"
                "FIRST PASS:\n{{prev}}\n\nORIGINAL TASK:\n" + task,
                system=BASE_SYS + " You are the ESCALATION seat.",
                role="escalation",
                weight=0.65,
                when="on_escalate",
            ),
        ],
        summary_template=(
            "Cheap-first cascade. Claude is called only when the first-pass output "
            "starts with the explicit [ESCALATE] marker."
        ),
    )


def _vote(task: str) -> Plan:
    return Plan(
        strategy="vote-of-three",
        steps=[
            Step("claude", task, BASE_SYS, "voter-A", parallel=True, weight=0.33),
            Step("openclaw", task, BASE_SYS, "voter-B", parallel=True, weight=0.33),
            Step("mythos", task, BASE_SYS, "voter-C", parallel=True, weight=0.34),
        ],
        summary_template=(
            "Three independent answers are shown together. PRISM does not hide "
            "disagreement behind a fake majority calculation."
        ),
    )


def _context_share(task: str) -> Plan:
    return Plan(
        strategy="context-share",
        steps=[
            Step(
                "openclaw",
                f"Distill the following into a compact brief (target <=400 tokens) "
                f"that another agent can act on without seeing the original. Preserve "
                f"requirements, constraints, uncertainties, and evidence.\n\n{task}",
                system=BASE_SYS + " You are the CONTEXT COMPRESSOR.",
                role="compressor",
                weight=0.25,
            ),
            Step(
                "claude",
                "Act on this distilled brief. Do not invent details omitted from it.\n\n"
                "BRIEF:\n{{prev}}",
                system=BASE_SYS + " You act on compressed context.",
                role="executor",
                weight=0.75,
            ),
        ],
        summary_template="OpenClaw compressed context; Claude acted on the brief.",
    )


def _war_room(task: str) -> Plan:
    return Plan(
        strategy="war-room",
        steps=[
            Step(
                "claude",
                f"Analyze this task independently. Focus on correctness, hidden risks, "
                f"and the strongest solution. Do not defer to another agent.\n\n{task}",
                system=BASE_SYS + " You are the SKEPTIC / senior analyst.",
                role="skeptic",
                parallel=True,
                weight=0.38,
            ),
            Step(
                "openclaw",
                f"Analyze this task independently. Focus on the most practical, "
                f"efficient implementation and concrete next actions.\n\n{task}",
                system=BASE_SYS + " You are the OPERATOR / practical analyst.",
                role="operator",
                parallel=True,
                weight=0.32,
            ),
            Step(
                "openclaw",
                "You are the PRISM CHAIR. Below are independent war-room reports. "
                "Synthesize them without erasing disagreement. Return four short "
                "sections: CONSENSUS, DISAGREEMENT, DECISION/OUTPUT, VERIFY NEXT. "
                "If a claim cannot be verified from the reports, say so.\n\n"
                "WAR ROOM REPORTS:\n{{prev}}\n\nORIGINAL TASK:\n" + task,
                system=BASE_SYS + " You are the CHAIR. Evidence beats majority.",
                role="chair",
                weight=0.30,
            ),
        ],
        summary_template=(
            "Independent skeptic and operator reports were reconciled by a low-cost "
            "chair. Disagreement is preserved instead of silently averaged away."
        ),
    )


_STRATEGIES = {
    "draft-polish": _draft_polish,
    "parallel-specialist": _parallel_specialist,
    "cascade": _cascade,
    "vote-of-three": _vote,
    "context-share": _context_share,
    "war-room": _war_room,
}


def plan(task: str, strategy: str = "draft-polish") -> Plan:
    fn = _STRATEGIES.get(strategy, _draft_polish)
    return fn(task)


def available_strategies():
    return list(_STRATEGIES.keys())
