#!/usr/bin/env python3
"""Regenerate self-contained index.html from the jurisdiction folder tree."""

from __future__ import annotations

import json
from pathlib import Path

DATA_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = Path(__file__).resolve().parent
TEMPLATE = OUT_DIR / "index.template.html"
OUT_HTML = OUT_DIR / "index.html"
TRAINED_FILE = OUT_DIR / "trained_progress.json"
SKIP = {"_Coverage", "_Priority", "_Refresh", "_archive", "Country_Index"}


def normalize_progress(raw: dict) -> dict:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, dict[str, bool]] = {}
    for key, value in raw.items():
        if not isinstance(key, str):
            continue
        if value is True:
            out[key] = {"jsonl": True, "ongoing": False}
        elif value is False:
            out[key] = {"jsonl": False, "ongoing": False}
        elif isinstance(value, dict):
            out[key] = {
                "jsonl": value.get("jsonl") is True,
                "ongoing": value.get("ongoing") is True,
            }
    return out


def load_trained_progress() -> dict:
    if not TRAINED_FILE.exists():
        return {}
    try:
        data = json.loads(TRAINED_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return normalize_progress(data if isinstance(data, dict) else {})


def scan() -> dict:
    continents = []
    for continent_path in sorted(DATA_ROOT.iterdir()):
        if not continent_path.is_dir() or continent_path.name.startswith("."):
            continue
        if continent_path.name in SKIP:
            continue

        countries = []
        for country_path in sorted(continent_path.iterdir()):
            if not country_path.is_dir():
                continue

            states = [
                {"id": state_path.name, "name": state_path.name.replace("_", " ")}
                for state_path in sorted(country_path.iterdir())
                if state_path.is_dir()
            ]
            countries.append(
                {
                    "id": country_path.name,
                    "name": country_path.name.replace("_", " "),
                    "states": states,
                }
            )

        continents.append(
            {
                "id": continent_path.name,
                "name": continent_path.name.replace("_", " "),
                "countries": countries,
            }
        )

    return {"continents": continents}


def main() -> None:
    data = scan()
    trained = load_trained_progress()
    template = TEMPLATE.read_text(encoding="utf-8")
    html = template.replace("__JURISDICTION_DATA__", json.dumps(data, ensure_ascii=False))
    html = html.replace("__TRAINED_PROGRESS__", json.dumps(trained, ensure_ascii=False))
    OUT_HTML.write_text(html, encoding="utf-8")

    countries = sum(len(c["countries"]) for c in data["continents"])
    states = sum(len(co["states"]) for c in data["continents"] for co in c["countries"])
    jsonl_count = sum(1 for v in trained.values() if v.get("jsonl"))
    ongoing_count = sum(1 for v in trained.values() if v.get("ongoing"))
    print(f"Wrote {OUT_HTML}")
    print(f"  {len(data['continents'])} continents, {countries} countries, {states} states")
    if jsonl_count or ongoing_count:
        print(
            f"  {jsonl_count} JSONL · {ongoing_count} ongoing toggles embedded from trained_progress.json"
        )
    print("  Open index.html in your editor HTML preview — toggles persist automatically.")


if __name__ == "__main__":
    main()
