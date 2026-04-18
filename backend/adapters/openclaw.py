"""OpenClaw adapter — works with any OpenAI-compatible endpoint.
Point OPENCLAW_BASE_URL at OpenAI, Groq, Ollama, LM Studio, etc.
"""
import os, json, httpx
from .base import BaseAdapter


class OpenClawAdapter(BaseAdapter):
    name = "openclaw"
    price_in  = 0.15
    price_out = 0.60

    def __init__(self):
        self.api_key = os.getenv("OPENCLAW_API_KEY", "")
        self.model   = os.getenv("OPENCLAW_MODEL", "gpt-4o-mini")
        self.base    = os.getenv("OPENCLAW_BASE_URL", "https://api.openai.com/v1")

    async def stream(self, prompt: str, system: str = "", **kwargs):
        if not self.api_key:
            yield {"delta": "[OpenClaw key missing — set OPENCLAW_API_KEY in .env]",
                   "tokens_in": 0, "tokens_out": 0, "done": True}
            return

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system or "You are an OpenClaw subagent inside PRISM."},
                {"role": "user",   "content": prompt},
            ],
            "stream": True,
            "max_tokens": kwargs.get("max_tokens", 2048),
        }
        tin = max(1, len(prompt) // 4)
        tout = 0
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream("POST", f"{self.base}/chat/completions",
                                     headers=headers, json=body) as r:
                async for line in r.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    payload = line[6:].strip()
                    if payload == "[DONE]":
                        break
                    try:
                        evt = json.loads(payload)
                    except Exception:
                        continue
                    delta = (evt.get("choices", [{}])[0]
                                .get("delta", {}).get("content", ""))
                    if delta:
                        tout += max(1, len(delta) // 4)
                        yield {"delta": delta, "tokens_in": tin,
                               "tokens_out": tout, "done": False}
                    usage = evt.get("usage")
                    if usage:
                        tin  = usage.get("prompt_tokens", tin)
                        tout = usage.get("completion_tokens", tout)
        yield {"delta": "", "tokens_in": tin, "tokens_out": tout, "done": True}
