#!/usr/bin/env python3
"""cache-cli: exercise the payload caching service from the command line.

Flags are parsed and sanitized with Pydantic Settings (CliApp).

Two deliberate deviations from the task spec, documented here rather than
hidden:
  1. The spec gives "-h" to both --host and --help. "-h" is the universal
     help flag, so it means help; --host is long-form only.
  2. pydantic-settings' CLI parser supports long flags only, so there are no
     -r/-i/-j/-o short forms. The long forms (--repeat, --input, --json,
     --output) behave exactly as specified, including "-" for stdin/stdout.

Example:
    ./cache-cli --json '{"list_1": ["a"], "list_2": ["b"]}' --repeat 3
"""

import json
import sys
import time

import httpx
from pydantic import Field
from pydantic_settings import BaseSettings, CliApp, SettingsConfigDict


class CacheCli(BaseSettings):
    model_config = SettingsConfigDict(cli_parse_args=True)

    host: str = "http://localhost:8000"
    repeat: int = Field(default=1, ge=1)
    input: str | None = None
    json_input: str | None = Field(default=None, alias="json")
    output: str | None = None


def load_request(cli: CacheCli) -> dict:
    """Load and validate the request body from --json, --input, or stdin."""
    if (cli.input is None) == (cli.json_input is None):
        raise ValueError("provide exactly one of --input or --json")
    raw = cli.json_input
    if raw is None:
        if cli.input == "-":
            raw = sys.stdin.read()
        else:
            with open(cli.input, encoding="utf-8") as f:
                raw = f.read()
    data = json.loads(raw)
    if not isinstance(data, dict) or "list_1" not in data or "list_2" not in data:
        raise ValueError('input JSON must be an object with "list_1" and "list_2"')
    return data


def write_result(result: dict, output: str | None) -> None:
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if output in (None, "-"):
        sys.stdout.write(text)
    else:
        with open(output, "w", encoding="utf-8") as f:
            f.write(text)


def main() -> int:
    cli = CliApp.run(CacheCli)
    try:
        request = load_request(cli)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    try:
        # trust_env=False: never route localhost dev traffic through a proxy,
        # and never crash on malformed proxy env vars (seen in sandboxes).
        with httpx.Client(base_url=cli.host, timeout=30, trust_env=False) as client:
            ids: list[str] = []
            for i in range(cli.repeat):
                started = time.perf_counter()
                resp = client.post("/payload", json=request)
                elapsed_ms = (time.perf_counter() - started) * 1000
                if resp.status_code not in (200, 201):
                    print(
                        f"error: POST /payload failed "
                        f"({resp.status_code}): {resp.text}",
                        file=sys.stderr,
                    )
                    return 1
                data = resp.json()
                ids.append(data["id"])
                print(
                    f"iteration {i + 1}/{cli.repeat}: "
                    f"id={ids[-1]} ({elapsed_ms:.0f} ms) - {data['message']}",
                    file=sys.stderr,
                )

            resp = client.get(f"/payload/{ids[0]}")
            if resp.status_code != 200:
                print(
                    f"error: GET /payload failed ({resp.status_code}): {resp.text}",
                    file=sys.stderr,
                )
                return 1
            result = resp.json()
    except httpx.ConnectError:
        print(f"error: cannot reach {cli.host} (is the service running?)", file=sys.stderr)
        return 1

    if cli.repeat > 1 and len(set(ids)) == 1:
        print(
            f"cache check: all {cli.repeat} POSTs returned the same id "
            "(payload reused, no duplicate generation)",
            file=sys.stderr,
        )

    write_result(result, cli.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
