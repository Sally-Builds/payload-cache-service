"""Simulated external "transformer" service.

This stands in for the real external service the task describes: it is slow
(artificial latency, like a network round trip) and deterministic, so caching
behavior can be reasoned about and tested without network access.

TransformerClient.calls is observable on purpose: tests and the CLI's repeat
mode use it to prove that caching actually minimizes external calls.
"""

import asyncio


class TransformerClient:
    def __init__(self, latency_seconds: float = 0.05) -> None:
        self.latency_seconds = latency_seconds
        self.calls = 0

    async def transform(self, text: str) -> str:
        await asyncio.sleep(self.latency_seconds)
        self.calls += 1
        return text.strip().upper()
