"""Optional third Anthropic-wire-compatible PRISM seat.

PRISM does not silently borrow Claude credentials or substitute another model
when this seat is unavailable. Configure both MYTHOS_API_KEY and MYTHOS_MODEL
if you intentionally want to use it.
"""
import os
from .claude import ClaudeAdapter


class MythosAdapter(ClaudeAdapter):
    name = "mythos"
    price_in = 6.0
    price_out = 30.0

    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("MYTHOS_API_KEY", "").strip()
        self.model = os.getenv("MYTHOS_MODEL", "").strip()
        self.base = os.getenv("MYTHOS_BASE_URL", self.base).strip()

    async def stream(self, prompt: str, system: str = "", **kwargs):
        if not self.api_key or not self.model:
            yield {
                "delta": (
                    "[Mythos seat unavailable — configure both MYTHOS_API_KEY "
                    "and MYTHOS_MODEL. PRISM did not substitute another model.]"
                ),
                "tokens_in": 0,
                "tokens_out": 0,
                "done": True,
            }
            return
        async for evt in super().stream(prompt, system, **kwargs):
            yield evt
