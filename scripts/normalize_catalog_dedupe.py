#!/usr/bin/env python3
"""Normalize conferences.csv: one-fact columns, track allowlist, notes segments.

Migrates legacy `website_or_cfp_link` → `website` + `cfp_link`.
See docs/CATALOG.md. Safe to re-run. Does not bump last_verified_date.
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

REPO = Path(__file__).resolve().parents[1]
CSV_PATH = REPO / "data" / "conferences.csv"
PUBLIC_CSV = REPO / "public" / "data" / "conferences.csv"
CATALOG_PATH = REPO / "docs" / "CATALOG.md"

DEADLINE_FIELDS = (
    "cfp_deadline_MM-DD",
    "cft_deadline_MM-DD",
    "cfw_deadline_MM-DD",
    "cfv_deadline_MM-DD",
)
LINK_FIELDS = (
    "website",
    "cfp_link",
    "cft_link",
    "cfw_link",
    "cfv_link",
)

IMPLIED_TRACKS = frozenset(
    {"talks", "trainings", "workshops", "training", "workshop", "talk", "keynotes", "keynote"}
)
TRACK_ALIASES = {
    "contests": "CTF",
    "contest": "CTF",
    "ctf": "CTF",
    "villages": "Villages",
    "village": "Villages",
    "panels": "Panels",
    "panel": "Panels",
    "briefings": "Briefings",
    "briefing": "Briefings",
    "unconference": "Unconference",
    "exhibition": "Exhibition",
    "mentorship": "Mentorship",
}
ALLOWED_TRACKS = frozenset(TRACK_ALIASES.values())

URL_RE = re.compile(r"https?://[^\s;|,]+", re.I)
ISO_RE = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b")
MMDD_RE = re.compile(r"\b(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])\b")
MONTH_DATE_RE = re.compile(
    r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|"
    r"Dec(?:ember)?)\.?\s+\d{1,2}"
    r"(?:\s*[-–]\s*\d{1,2})?"
    r"(?:\s*,?\s*20\d{2})?\b",
    re.I,
)
HISTORY_PAIR_RE = re.compile(
    r"\b(20\d{2})\s+([A-Z][A-Za-z][A-Za-z .'-]{1,40}?)(?=(?:\s*;|\s*,|\s+20\d{2}\b|$))"
)
SPEAKERS_RE = re.compile(
    r"(?i)(?:flight|hotel|travel\s*grant|speakers?|sponsorship)[^;]{0,80}"
    r"(?:EUR|USD|GBP|CHF|\$|€|£|\d+\s*(?:eur|usd))[^;]{0,40}"
)
PORTAL_HINT_RE = re.compile(
    r"(?i)papercall|sessionize|pretalx|/cfp\b|call[_-]?for|callfor|cfp\.|"
    r"/papers\b|/submit\b|/abstract"
)
AGGREGATOR_HOSTS = frozenset(
    {
        "papercall.io",
        "sessionize.com",
        "pretalx.com",
        "cfp.directory",
        "eventbrite.com",
        "events.humanitix.com",
        "humanitix.com",
        "welcu.com",
        "whova.com",
        "lu.ma",
        "meetup.com",
        "hopin.com",
        "airtable.com",
        "forms.gle",
        "docs.google.com",
        "linkedin.com",
    }
)


def load_expected_header() -> list[str]:
    text = CATALOG_PATH.read_text(encoding="utf-8")
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("conference_name,"):
            return stripped.split(",")
    raise SystemExit(f"Could not find CSV header in {CATALOG_PATH}")


def normalize_deadline(value: str) -> str:
    clean = (value or "").strip()
    return clean if clean else "TBD"


def normalize_tracks(raw: str) -> str:
    if not (raw or "").strip():
        return ""
    parts: list[str] = []
    seen: set[str] = set()
    for tok in re.split(r"[|,]", raw):
        t = tok.strip()
        if not t:
            continue
        key = t.casefold()
        if key in IMPLIED_TRACKS:
            continue
        mapped = TRACK_ALIASES.get(key)
        if mapped is None:
            continue
        if mapped.casefold() in seen:
            continue
        seen.add(mapped.casefold())
        parts.append(mapped)
    return "|".join(parts)


def host_of(url: str) -> str:
    try:
        host = (urlparse(url).hostname or "").lower()
        return host.removeprefix("www.")
    except Exception:
        return ""


def looks_like_portal(url: str) -> bool:
    return bool(PORTAL_HINT_RE.search(url or ""))


def is_aggregator(url: str) -> bool:
    host = host_of(url)
    if not host:
        return False
    if host in AGGREGATOR_HOSTS:
        return True
    return any(host == h or host.endswith("." + h) for h in AGGREGATOR_HOSTS)


def split_website_cfp(url: str) -> tuple[str, str]:
    """Return (website, cfp_link) from a legacy combined URL."""
    url = (url or "").strip()
    if not url:
        return "", ""
    if not looks_like_portal(url):
        return url, ""

    if is_aggregator(url):
        return "", url

    try:
        parsed = urlparse(url)
        path = (parsed.path or "").rstrip("/")
        if path and path != "":
            origin = f"{parsed.scheme}://{parsed.netloc}"
            if origin.rstrip("/") != url.rstrip("/"):
                return origin, url
    except Exception:
        pass
    return "", url


def origin_of(url: str) -> str:
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return ""
        return f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        return ""


def migrate_legacy_website_column(row: dict[str, str]) -> None:
    """Ensure row has website + cfp_link; migrate website_or_cfp_link if present."""
    website = (row.get("website") or "").strip()
    cfp_link = (row.get("cfp_link") or "").strip()
    legacy = (row.get("website_or_cfp_link") or "").strip()

    if legacy and not website and not cfp_link:
        website, cfp_link = split_website_cfp(legacy)
    elif legacy and website and not cfp_link and looks_like_portal(legacy) and legacy != website:
        cfp_link = legacy
    elif legacy and cfp_link and not website and not looks_like_portal(legacy):
        website = legacy

    # Portal/aggregator wrongly stored as homepage
    if website and (looks_like_portal(website) or is_aggregator(website)):
        derived = (
            origin_of(cfp_link) if cfp_link and not is_aggregator(cfp_link) else ""
        )
        if is_aggregator(website):
            if not cfp_link:
                cfp_link = website
                website = ""
            else:
                website = derived
        elif not cfp_link:
            website, cfp_link = split_website_cfp(website)
        else:
            # Own-domain submission path in website while cfp_link already set
            website = origin_of(website) or derived

    # If website empty but cfp is own-domain portal, recover homepage origin
    if not website and cfp_link and looks_like_portal(cfp_link) and not is_aggregator(cfp_link):
        website = origin_of(cfp_link)

    # Aggregator origins are not useful homepages
    if website and is_aggregator(website):
        website = ""

    row["website"] = website
    row["cfp_link"] = cfp_link
    if "website_or_cfp_link" in row:
        del row["website_or_cfp_link"]


def promote_cfp_from_src(row: dict[str, str]) -> None:
    """If cfp_link empty, lift first portal URL out of notes src: into cfp_link."""
    if (row.get("cfp_link") or "").strip():
        return
    notes = row.get("notes") or ""
    m = re.search(r"(?i)\bsrc:\s*([^;]+)", notes)
    if not m:
        return
    src_body = m.group(1)
    portals = [u.rstrip(").,]") for u in URL_RE.findall(src_body) if looks_like_portal(u)]
    if not portals:
        return
    chosen = portals[0]
    # Don't promote aggregator calendars/tickets that aren't submission portals
    if not PORTAL_HINT_RE.search(chosen):
        return
    row["cfp_link"] = chosen
    remaining = []
    for u in URL_RE.findall(src_body):
        clean = u.rstrip(").,]")
        if clean == chosen or clean.rstrip("/") == chosen.rstrip("/"):
            continue
        remaining.append(clean)
    before = m.group(0)
    after = ("src: " + " ".join(remaining)).strip() if remaining else ""
    notes2 = notes.replace(before, after, 1)
    notes2 = re.sub(r"\s*;\s*;+", "; ", notes2)
    row["notes"] = notes2.strip(" \t\n\r;,.|-")


def primary_urls(row: dict[str, str]) -> set[str]:
    urls: set[str] = set()
    for field in LINK_FIELDS:
        url = (row.get(field) or "").strip()
        if not url:
            continue
        urls.add(url)
        urls.add(url.rstrip("/"))
    return urls


def extract_labeled_segments(notes: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for key in ("history", "cfp", "speakers", "src"):
        m = re.search(rf"(?i)\b{key}:\s*([^;]+)", notes)
        if m:
            found[key] = m.group(1).strip()
    return found


def strip_labeled_segments(notes: str) -> str:
    return re.sub(
        r"(?i)\b(?:history|cfp|speakers|src):\s*[^;]*",
        "",
        notes,
    )


def tidy_text(text: str) -> str:
    text = re.sub(r"\s*;\s*;+", "; ", text)
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\s+([,;])", r"\1", text)
    text = re.sub(r"([,;])\s*", r"\1 ", text)
    text = re.sub(r"\(\s*\)", "", text)
    return text.strip(" \t\n\r;,.|-")


def shorten_blurb(blurb: str, limit: int = 220) -> str:
    blurb = tidy_text(blurb)
    if len(blurb) <= limit:
        return blurb
    cut = blurb[: limit + 1]
    for sep in ("; ", ". ", ", "):
        idx = cut.rfind(sep)
        if idx >= 80:
            return tidy_text(cut[:idx])
    return tidy_text(cut[:limit].rsplit(" ", 1)[0])


def rewrite_notes(row: dict[str, str]) -> str:
    notes = (row.get("notes") or "").strip()
    if not notes:
        return ""

    labeled = extract_labeled_segments(notes)
    work = strip_labeled_segments(notes)

    primaries = primary_urls(row)
    secondary_urls: list[str] = []
    if labeled.get("src"):
        for u in URL_RE.findall(labeled["src"]):
            u = u.rstrip(").,]")
            if u not in primaries and u.rstrip("/") not in primaries and u not in secondary_urls:
                secondary_urls.append(u)

    for match in URL_RE.finditer(work):
        u = match.group(0).rstrip(").,]")
        if u in primaries or u.rstrip("/") in primaries:
            continue
        if u not in secondary_urls:
            secondary_urls.append(u)

    for url in list(primaries):
        work = work.replace(url, "")

    work = URL_RE.sub("", work)
    work = ISO_RE.sub("", work)
    work = MMDD_RE.sub("", work)

    name = (row.get("conference_name") or "").strip()
    city = (row.get("city") or "").strip()
    country = (row.get("country") or "").strip()
    start = (row.get("conference_start_date") or "").strip()
    end = (row.get("conference_end_date") or "").strip()

    if start and start != "TBD" and end and end != "TBD":
        work = MONTH_DATE_RE.sub("", work)

    if city and city != "TBD":
        work = re.sub(rf"\b{re.escape(city)}\b", "", work, flags=re.IGNORECASE)
    if country and country != "TBD":
        work = re.sub(rf"\b{re.escape(country)}\b", "", work, flags=re.IGNORECASE)
    if name and work.lower().startswith(name.lower()):
        work = work[len(name) :].lstrip(" :,-;")

    history_bits: list[str] = []
    if labeled.get("history"):
        history_bits.append(labeled["history"])
    for year, place in HISTORY_PAIR_RE.findall(work):
        place = place.strip(" ,;")
        if len(place) < 2:
            continue
        bit = f"{year} {place}"
        if bit not in history_bits:
            history_bits.append(bit)
    since = re.search(r"(?i)\bsince\s+(20\d{2})\b", work)
    if since and not history_bits:
        history_bits.append(f"since {since.group(1)}")

    speakers = labeled.get("speakers", "")
    if not speakers:
        sm = SPEAKERS_RE.search(notes)
        if sm:
            speakers = tidy_text(sm.group(0))
            work = work.replace(sm.group(0), "")

    cfp_seg = labeled.get("cfp", "")
    cfp_deadline = normalize_deadline(row.get("cfp_deadline_MM-DD", ""))
    cfp_link = (row.get("cfp_link") or "").strip()
    if not cfp_seg and cfp_deadline == "TBD":
        if looks_like_portal(cfp_link) or re.search(
            r"(?i)\b(cfp|call for)\b.{0,40}\b(open|no (?:close|deadline)|close unlisted)\b",
            notes,
        ):
            cfp_seg = "open close unlisted"

    for bit in history_bits:
        work = re.sub(re.escape(bit), "", work, flags=re.IGNORECASE)
    work = re.sub(r"(?i)\bsince\s+20\d{2}\b", "", work)

    blurb = shorten_blurb(work)

    parts: list[str] = []
    if blurb:
        parts.append(blurb)
    if history_bits:
        uniq: list[str] = []
        for b in history_bits:
            b = tidy_text(b)
            if b and b not in uniq:
                uniq.append(b)
        parts.append("history: " + "; ".join(uniq[:8]))
    if cfp_seg:
        parts.append("cfp: " + tidy_text(cfp_seg))
    if speakers:
        parts.append("speakers: " + tidy_text(speakers)[:160])
    if secondary_urls:
        parts.append("src: " + " ".join(secondary_urls[:3]))

    return "; ".join(parts)


def main() -> int:
    expected = load_expected_header()

    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            print("empty CSV", file=sys.stderr)
            return 1
        rows = list(reader)

    track_cleared = track_trimmed = notes_changed = deadlines_filled = 0
    split_portal = split_home = both = 0

    for row in rows:
        migrate_legacy_website_column(row)
        promote_cfp_from_src(row)

        website = (row.get("website") or "").strip()
        cfp_link = (row.get("cfp_link") or "").strip()
        if website and cfp_link:
            both += 1
        elif cfp_link and not website:
            split_portal += 1
        elif website and not cfp_link:
            split_home += 1

        for field in DEADLINE_FIELDS:
            before = row.get(field, "")
            after = normalize_deadline(before)
            if after != before:
                deadlines_filled += 1
                row[field] = after

        before_t = (row.get("submission_tracks") or "").strip()
        after_t = normalize_tracks(before_t)
        if after_t != before_t:
            if before_t and not after_t:
                track_cleared += 1
            else:
                track_trimmed += 1
            row["submission_tracks"] = after_t

        before_n = (row.get("notes") or "").strip()
        after_n = rewrite_notes(row)
        if after_n != before_n:
            notes_changed += 1
            row["notes"] = after_n

        # Drop any leftover legacy key
        row.pop("website_or_cfp_link", None)

    rows.sort(key=lambda r: (r.get("conference_name") or "").casefold())

    for path in (CSV_PATH, PUBLIC_CSV):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=expected, lineterminator="\n", extrasaction="ignore"
            )
            writer.writeheader()
            writer.writerows(rows)

    print(
        f"rows={len(rows)} website_only={split_home} cfp_only={split_portal} "
        f"website+cfp={both} deadlines_filled={deadlines_filled} "
        f"tracks_cleared={track_cleared} tracks_trimmed={track_trimmed} "
        f"notes_changed={notes_changed}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
