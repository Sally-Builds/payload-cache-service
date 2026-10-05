"""CLI tests: arg parsing/sanitizing plus input/output helpers.

main()'s HTTP calls are exercised manually against a live server (see README);
these tests cover everything around them.
"""

import json

import pytest
from pydantic_settings import CliApp

from cli import CacheCli, load_request, write_result


def _parse(args):
    return CliApp.run(CacheCli, cli_args=args)


def test_defaults():
    cli = _parse(["--json", "{}"])
    assert cli.host == "http://localhost:8000"
    assert cli.repeat == 1
    assert cli.input is None
    assert cli.output is None


def test_long_flags():
    cli = _parse(
        [
            "--host",
            "http://example:9",
            "--repeat",
            "4",
            "--input",
            "in.json",
            "--output",
            "out.json",
        ]
    )
    assert cli.host == "http://example:9"
    assert cli.repeat == 4
    assert cli.input == "in.json"
    assert cli.output == "out.json"


def test_repeat_must_be_positive():
    with pytest.raises(Exception):
        _parse(["--repeat", "0", "--json", "{}"])


def test_load_request_from_json_flag():
    cli = _parse(["--json", '{"list_1": ["a"], "list_2": ["b"]}'])
    assert load_request(cli) == {"list_1": ["a"], "list_2": ["b"]}


def test_load_request_from_file(tmp_path):
    payload = {"list_1": ["a"], "list_2": ["b"]}
    path = tmp_path / "in.json"
    path.write_text(json.dumps(payload))
    cli = _parse(["--input", str(path)])
    assert load_request(cli) == payload


def test_load_request_from_stdin(monkeypatch, capsys):
    import sys

    monkeypatch.setattr(sys, "stdin", _Stdin('{"list_1": ["a"], "list_2": ["b"]}'))
    cli = _parse(["--input", "-"])
    assert load_request(cli) == {"list_1": ["a"], "list_2": ["b"]}


class _Stdin:
    def __init__(self, text):
        self._text = text

    def read(self):
        return self._text


def test_load_request_requires_exactly_one_source():
    with pytest.raises(ValueError):
        load_request(_parse(["--json", "{}", "--input", "x"]))
    with pytest.raises(ValueError):
        load_request(_parse([]))


def test_load_request_rejects_bad_shape():
    with pytest.raises(ValueError):
        load_request(_parse(["--json", '{"nope": 1}']))
    with pytest.raises(ValueError):
        load_request(_parse(["--json", "[1, 2]"]))


def test_write_result_to_stdout(capsys):
    write_result({"output": "A, B"}, "-")
    out, _ = capsys.readouterr()
    assert json.loads(out) == {"output": "A, B"}


def test_write_result_to_file(tmp_path):
    path = tmp_path / "out.json"
    write_result({"output": "A, B"}, str(path))
    assert json.loads(path.read_text()) == {"output": "A, B"}
