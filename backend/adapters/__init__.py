"""Adapter registry. Add new models by importing them here."""
from .base import BaseAdapter
from .claude import ClaudeAdapter
from .openclaw import OpenClawAdapter
from .mythos import MythosAdapter

REGISTRY = {
    "claude":   ClaudeAdapter,
    "openclaw": OpenClawAdapter,
    "mythos":   MythosAdapter,
}

def get_adapter(name: str) -> BaseAdapter:
    cls = REGISTRY.get(name.lower())
    if not cls:
        raise ValueError(f"Unknown adapter: {name}. Available: {list(REGISTRY)}")
    return cls()
