"""Quick import + plan smoke test. Run: python scripts/smoke_test.py"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from backend.router import plan, available_strategies
from backend.adapters import REGISTRY, get_adapter

print("Strategies available:", available_strategies())
print("Adapters registered :", list(REGISTRY))

for s in available_strategies():
    p = plan("Refactor this repo to use async handlers", s)
    print(f"\n[{p.strategy}] {len(p.steps)} step(s):")
    for i, st in enumerate(p.steps):
        mark = "||" if st.parallel else "->"
        print(f"   {mark} step {i}: {st.agent:9s} role={st.role:12s} weight={st.weight}")

print("\nAll strategies plan cleanly. Adapters instantiate:")
for name in REGISTRY:
    a = get_adapter(name)
    print(f"   OK {name:9s}  model={getattr(a, 'model', '?')}")
