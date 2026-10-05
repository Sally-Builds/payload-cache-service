"""Unit tests for the pure payload logic (no I/O)."""

import pytest

from app import logic


def test_interleave_alternates_lists():
    assert logic.interleave(["a1", "a2"], ["b1", "b2"]) == ["a1", "b1", "a2", "b2"]


def test_interleave_rejects_unequal_lengths():
    with pytest.raises(ValueError):
        logic.interleave(["a1", "a2"], ["b1"])


def test_interleave_empty_lists():
    assert logic.interleave([], []) == []


def test_format_output_matches_spec_sample():
    items = ["FIRST STRING", "OTHER STRING", "SECOND STRING"]
    assert logic.format_output(items) == "FIRST STRING, OTHER STRING, SECOND STRING"


def test_payload_key_is_deterministic():
    k1 = logic.payload_key(["a"], ["b"])
    k2 = logic.payload_key(["a"], ["b"])
    assert k1 == k2


def test_payload_key_is_order_sensitive():
    assert logic.payload_key(["a"], ["b"]) != logic.payload_key(["b"], ["a"])


def test_payload_key_distinguishes_inputs():
    assert logic.payload_key(["a"], ["b"]) != logic.payload_key(["a"], ["c"])


def test_string_key_distinguishes_raw_strings():
    # Keyed on the raw string, which is what the transformer receives.
    assert logic.string_key("a") != logic.string_key(" a ")
