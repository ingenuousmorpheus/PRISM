"""Claude Mythos adapter — identical wire format to Claude, separate keys/model.
Graceful fallback: if MYTHOS_API_KEY is unset, we transparently borrow the
Claude key so users can test the code path today. Flip it to its own key on
Mythos release day and nothing else changes.
"""
import os
from .claude import ClaudeAdapter


class MythosAdapter(ClaudeAdapter):
    name = "mythos"
    price_in  = 6.0    # placeholder — update when Anthropic publishes pricing
    price_out = 30.0

    def __init__(self):
        super().__init__()
        mk = os.getenv("MYTHOS_API_KEY", "").strip()
        self.api_key = mk or self.api_key
        self.model   = os.getenv("MYTHOS_MODEL", "claude-mythos-1")
        self.base    = os.getenv("MYTHOS_BASE_URL", self.base)
        self._placeholder = not mk
