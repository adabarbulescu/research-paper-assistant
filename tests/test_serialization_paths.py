from __future__ import annotations

from utils.serialization import decode_str_list, encode_str_list


def test_decode_str_list_json_format():
    raw = encode_str_list(["Doe, Jr.", "Alice Smith"])
    assert decode_str_list(raw) == ["Doe, Jr.", "Alice Smith"]


def test_decode_str_list_legacy_format():
    raw = "Alice Smith, Bob Stone"
    assert decode_str_list(raw) == ["Alice Smith", "Bob Stone"]
