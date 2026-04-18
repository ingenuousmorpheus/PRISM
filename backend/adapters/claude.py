"""Anthropic Claude adapter — streams via messages API."""
import os, json, httpx
from .base import BaseAdapter


class ClaudeAdapter(BaseAdapter):
    name = "claude"
    price_in  = 3.0
    price_out = 15.0

    def __init__(self):
        self.api_key = os.getenv("CLAUDE_API_KEY", "")
        self.model   = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")
        self.base    = os.getenv("CLAUDE_BASE_URL", "https://api.anthropic.com/v1")

    async def stream(self, prompt: str, system: str = "", **kwargs):
        if not self.api_key:
            yield {"delta": "[Claude key missing — set CLAUDE_API_KEY in .env]",
                   "tokens_in": 0, "tokens_out": 0, "done": True}
            return

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        body = {
            "model": self.model,
            "max_tokens": kwargs.get("max_tokens", 2048),
            "system": system or "You are a helpful subagent inside PRISM.",
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
        }
        tin = tout = 0
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", f"{self.base}/messages",
                                     headers=headers, json=body) as r:
                async for line in r.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    try:
                        evt = json.loads(line[6:])
                    except Exception:
                        continue
                    t = evt.get("type")
                    if t == "message_start":
                        tin = evt["message"]["usage"].get("input_tokens", 0)
                    elif t == "content_block_delta":
                        d = evt["delta"].get("text", "")
                        if d:
                            tout += max(1, len(d) // 4)
                            yield {"delta": d, "tokens_in": tin,
                                   "tokens_out": tout, "done": False}
                    elif t == "message_delta":
                        tout = evt.get("usage", {}).get("output_tokens", tout)
        yield {"delta": "", "tokens_in": tin, "tokens_out": tout, "done": True}
