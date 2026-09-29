"""Quick import + plan smoke test. Run: python scripts/smoke_test.py"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from backend.router import plan, available_strategies, should_run
from backend.adapters import REGISTRY, get_adapter

print("Strategies available:", available_strategies())
print("Adapters registered :", list(REGISTRY))

for s in available_strategies():
    p = plan("Refactor this repo to use async handlers", s)
    print(f"\n[{p.strategy}] {len(p.steps)} step(s):")
    for i, st in enumerate(p.steps):
        mark = "||" if st.parallel else "->"
        suffix = "" if st.when == "always" else f" when={st.when}"
        print(
            f"   {mark} step {i}: {st.agent:9s} "
            f"role={st.role:12s} weight={st.weight}{suffix}"
        )

cascade = plan("test", "cascade")
assert should_run(cascade.steps[1], "[ESCALATE] needs deeper reasoning")
assert not should_run(cascade.steps[1], "confident answer")
assert "war-room" in available_strategies()

print("\nConditional routing checks passed.")
print("Adapters instantiate:")
for name in REGISTRY:
    a = get_adapter(name)
    print(f"   OK {name:9s}  model={getattr(a, 'model', '?') or '(unset)'}")
