"""Opt-in online check: every remote Action pin must resolve via GitHub's Git commit API.

Run before release with: uv run --locked python tools/verify_action_pins.py
This reads public metadata only; it does not upload code or configuration.
"""

import json
import re
from pathlib import Path
from urllib.request import Request, urlopen

import yaml

ROOT = Path(__file__).resolve().parents[1]
PIN = re.compile(r"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@([0-9a-f]{40})")


def action_pins() -> set[tuple[str, str]]:
    pins: set[tuple[str, str]] = set()

    def visit(value: object) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key == "uses" and isinstance(item, str) and not item.startswith("./"):
                    match = PIN.fullmatch(item)
                    if match is None:
                        raise ValueError("Remote Actions must use full commit SHAs.")
                    pins.add((match[1], match[2]))
                else:
                    visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    for path in [ROOT / "action.yml", *sorted((ROOT / ".github/workflows").glob("*.yml"))]:
        visit(yaml.safe_load(path.read_text(encoding="utf-8")))
    return pins


def verify() -> None:
    for repository, sha in sorted(action_pins()):
        url = f"https://api.github.com/repos/{repository}/git/commits/{sha}"
        request = Request(url, headers={"Accept": "application/vnd.github+json"})
        with urlopen(request, timeout=30) as response:
            commit = json.load(response)
        if commit.get("sha") != sha or "tree" not in commit or "parents" not in commit:
            raise ValueError("GitHub did not return the requested Git commit.")
        print(f"Verified commit: {repository}@{sha}")


if __name__ == "__main__":
    verify()
