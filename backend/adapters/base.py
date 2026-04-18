"""Base adapter — every subagent implements `stream()`."""
from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, Any


class BaseAdapter(ABC):
    name: str = "base"
    # Approximate $/1M tokens for cost estimation. Override per adapter.
    price_in:  float = 3.0
    price_out: float = 15.0

    @abstractmethod
    async def stream(self, prompt: str, system: str = "", **kwargs) -> AsyncIterator[Dict[str, Any]]:
        """Yield dicts of form:
            {"delta": str, "tokens_in": int, "tokens_out": int, "done": bool}
        """
        raise NotImplementedError
        yield  # pragma: no cover

    def estimate_cost(self, tin: int, tout: int) -> float:
        return (tin / 1_000_000) * self.price_in + (tout / 1_000_000) * self.price_out
