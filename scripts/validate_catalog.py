#!/usr/bin/env python3
"""Validate conferences.csv against docs/CATALOG.md (used by CI)."""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CSV_PATH = REPO / "data" / "conferences.csv"
CATALOG_PATH = REPO / "docs" / "CATALOG.md"

MM_DD = re.compile(r"^(TBD|\d{2}-\d{2})$")
ISO_DATE = re.compile(r"^(TBD|\d{4}-\d{2}-\d{2})$")
ISO_IN_TEXT = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b")
URL_IN_TEXT = re.compile(r"https?://[^\s;|,]+", re.I)

IMPLIED_TRACKS = frozenset(
    {"talks", "trainings", "workshops", "training", "workshop", "talk", "keynotes", "keynote"}
)
ALLOWED_TRACKS = frozenset(
    {
        "CTF",
        "Villages",
        "Panels",
        "Briefings",
        "Unconference",
        "Exhibition",
        "Mentorship",
    }
)
LINK_FIELDS = (
    "website",
    "cfp_link",
    "cft_link",
    "cfw_link",
    "cfv_link",
)
DEADLINE_FIELDS = (
    "cfp_deadline_MM-DD",
    "cft_deadline_MM-DD",
    "cfw_deadline_MM-DD",
    "cfv_deadline_MM-DD",
)


def load_expected_header() -> list[str]:
    text = CATALOG_PATH.read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("conference_name,"):
            return stripped.split(",")
    raise SystemExit(f"Could not find CSV header in {CATALOG_PATH}")


def validate_mm_dd(value: str, field: str, row_num: int, errors: list[str]) -> None:
    clean = value.strip()
    if not clean:
        errors.append(
            f"row {row_num}: empty {field} (use TBD or MM-DD; empty not allowed)"
        )
        return
    if not MM_DD.match(clean):
        errors.append(f"row {row_num}: invalid {field} {value!r} (expected MM-DD or TBD)")


def validate_iso_date(value: str, field: str, row_num: int, errors: list[str]) -> None:
    if not ISO_DATE.match(value):
        errors.append(
            f"row {row_num}: invalid {field} {value!r} (expected YYYY-MM-DD or TBD)"
        )


def urls_allowed_in_notes(notes: str) -> set[str]:
    """URLs that appear in src: segments are allowed."""
    allowed: set[str] = set()
    for m in re.finditer(r"(?i)\bsrc:\s*([^;]+)", notes):
        for u in URL_IN_TEXT.findall(m.group(1)):
            allowed.add(u.rstrip(").,]"))
            allowed.add(u.rstrip(").,]").rstrip("/"))
    return allowed


def main() -> int:
    if not CSV_PATH.is_file():
        print(f"::error file={CSV_PATH}::Missing conferences.csv", file=sys.stderr)
        return 1

    expected = load_expected_header()
    errors: list[str] = []
    names: dict[str, int] = {}

    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration:
            print("::error::conferences.csv is empty", file=sys.stderr)
            return 1

        if header != expected:
            errors.append(
                "CSV header does not match docs/CATALOG.md "
                f"(expected {len(expected)} columns, got {len(header)})"
            )

        for row_num, row in enumerate(reader, start=2):
            if not any(cell.strip() for cell in row):
                continue
            if len(row) != len(expected):
                errors.append(
                    f"row {row_num}: expected {len(expected)} columns, got {len(row)}"
                )
                continue

            record = dict(zip(expected, row))
            name = record["conference_name"].strip()
            if not name:
                errors.append(f"row {row_num}: missing conference_name")
                continue

            key = name.casefold()
            if key in names:
                errors.append(
                    f"row {row_num}: duplicate conference_name {name!r} "
                    f"(first seen row {names[key]})"
                )
            else:
                names[key] = row_num

            for field in DEADLINE_FIELDS:
                validate_mm_dd(record[field], field, row_num, errors)

            for field in (
                "conference_start_date",
                "conference_end_date",
                "last_verified_date",
            ):
                validate_iso_date(record[field].strip(), field, row_num, errors)

            tracks_raw = record.get("submission_tracks", "").strip()
            if tracks_raw:
                for tok in re.split(r"[|,]", tracks_raw):
                    t = tok.strip()
                    if not t:
                        continue
                    if t.casefold() in IMPLIED_TRACKS:
                        errors.append(
                            f"row {row_num}: submission_tracks must not include "
                            f"{t!r} (implied by deadline/link columns; extras only)"
                        )
                    elif t not in ALLOWED_TRACKS:
                        allowed = "|".join(sorted(ALLOWED_TRACKS))
                        errors.append(
                            f"row {row_num}: submission_tracks token {t!r} not in "
                            f"allowlist ({allowed})"
                        )

            notes = record.get("notes", "")
            note_urls = {
                u.rstrip(").,]") for u in URL_IN_TEXT.findall(notes)
            }
            note_urls |= {u.rstrip("/") for u in note_urls}
            for field in LINK_FIELDS:
                url = record.get(field, "").strip()
                if not url:
                    continue
                # Exact URL token only (same-host deeper paths in src: are OK)
                if url in note_urls or url.rstrip("/") in note_urls:
                    errors.append(
                        f"row {row_num}: notes repeats {field} URL "
                        f"(keep URL only in {field})"
                    )

            if ISO_IN_TEXT.search(notes):
                errors.append(
                    f"row {row_num}: notes contain ISO date "
                    f"(use conference_*_date columns or history: YYYY City)"
                )

            allowed_urls = urls_allowed_in_notes(notes)
            for u in URL_IN_TEXT.findall(notes):
                clean = u.rstrip(").,]")
                if clean not in allowed_urls and clean.rstrip("/") not in allowed_urls:
                    errors.append(
                        f"row {row_num}: notes URL must be in a src: segment "
                        f"(found {clean!r})"
                    )

    if errors:
        for msg in errors:
            print(f"::error file={CSV_PATH}::{msg}", file=sys.stderr)
        print(f"::error::Found {len(errors)} catalog validation error(s)", file=sys.stderr)
        return 1

    print(f"Validated {len(names)} conference row(s) in {CSV_PATH.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
