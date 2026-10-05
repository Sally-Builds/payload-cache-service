"""Pure payload logic: cache keys, interleaving, output formatting.

Kept free of I/O so it is trivially unit-testable. The service layer
(app/service.py) is the only place that touches the database and the
transformer.
"""

import hashlib
import json


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def string_key(text: str) -> str:
    """Cache key for one transformer input: the exact raw string.

    Keyed on the raw string (not the transformed value) because the raw
    string is what the transformer receives.
    """
    return sha256_hex(text)


def payload_key(list_1: list[str], list_2: list[str]) -> str:
    """Cache key for a whole payload request.

    Canonical JSON (fixed key order, compact separators) so identical
    requests always hash identically, while any change in content or order
    produces a different key.
    """
    canonical = json.dumps(
        {"list_1": list_1, "list_2": list_2},
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return sha256_hex(canonical)


def interleave(list_1: list[str], list_2: list[str]) -> list[str]:
    """Interleave two equal-length lists: a1, b1, a2, b2, ..."""
    if len(list_1) != len(list_2):
        raise ValueError("list_1 and list_2 must contain the same number of strings")
    interleaved: list[str] = []
    for a, b in zip(list_1, list_2):
        interleaved.append(a)
        interleaved.append(b)
    return interleaved


def format_output(items: list[str]) -> str:
    return ", ".join(items)
