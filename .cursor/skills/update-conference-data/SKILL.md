---
name: update-conference-data
description: >-
  Add or update rows in data/conferences.csv for the Conference Tracker dashboard.
  Use when the user asks to add a conference, update deadlines/links/location,
  fix missing data, verify CFP/CfT/CfW, enrich notes, or edit conference catalog
  entries. Schema: docs/CATALOG.md. Requires web research from official sources before writing values.
  Keep one fact per column; never duplicate city/dates/deadlines/URLs into notes;
  use website + cfp_link (not a combined column); leave submission_tracks empty unless
  extras (CTF/Panels/Villages) remain after deadlines/links.
---

# Update conference data (`data/conferences.csv`)

**Schema, enums, UI mapping, notes format:** [`docs/CATALOG.md`](../../../docs/CATALOG.md) — do not invent parallel rules here.  
**PR workflow:** [CONTRIBUTING.md](../../../CONTRIBUTING.md).

## Scope

- **In scope:** `data/conferences.csv` only.
- **Out of scope:** `index.html` / `app.js` unless the user asks for UI changes.

## Before editing

1. Read the CSV **header** — never reorder columns ([`docs/CATALOG.md`](../../../docs/CATALOG.md)).
2. **Search** for an existing row (name, similar spelling, same domain).
3. **Research on the web** — not training data alone.

## Update vs add

| Situation | Action |
|-----------|--------|
| Already listed | **Update** changed fields only |
| New or distinct regional edition | **Add** one row |
| Duplicates | **Merge** per user intent |

**Never** two rows for the same edition.

## Research

Use **WebSearch** / **WebFetch** until you can cite official evidence.

**Source order:** (1) official site + CFP pages (2) Sessionize / PaperCall / Pretalx / vendor CFP (3) organizer posts if site stale (4) aggregators **as leads only** — verify before writing.

**Collect into columns first** (not notes):

| Fact | Column(s) |
|------|-----------|
| Start / end | `conference_start_date`, `conference_end_date` (`YYYY-MM-DD` or `TBD`) |
| Deadlines | `cfp_` / `cft_` / `cfw_` / `cfv_` `*_deadline_MM-DD` (`MM-DD` or `TBD`) |
| URLs | `website` (homepage), `cfp_link` (talk portal if distinct), `cft_link`, `cfw_link`, `cfv_link` |
| Place | `city`, `country` |
| Format / TZ | `conference_type`, `timezone` |
| Sponsorship enum | `travel_accommodation_sponsorship` |

Then write **`notes`** only for leftovers per [Notes format](../../../docs/CATALOG.md#notes-format): short blurb; optional `history:`, `cfp:`, `speakers:`, `src:` segments separated by `; `.

### `submission_tracks` (minify)

- Omit `Talks` / `Trainings` / `Workshops` / `Keynotes` — implied or not program extras.
- Allowlist only: `CTF`, `Villages`, `Panels`, `Briefings`, `Unconference`, `Exhibition`, `Mentorship` (pipe-separated).
- Map `Contests` → `CTF`. Never store topic tags (`AI`, `Tech`, …).
- Leave empty when there are no extras.
- Deadline cells: always `MM-DD` or `TBD` (never blank).

### Dates when the row is stale or empty

1. Official site (blog, FAQ, archives) + **CfP Watch** / submission portals.
2. Verified listings — confirm on organizer or official source.
3. **Write:** latest edition start/end for this row’s city; matching `cfp_deadline_MM-DD`; prior years in `history:` notes segment; `venue_pattern` `Rotating` if city/format changed; `last_verified_date` = today.

### Hard limits

- **Never invent** dates, deadlines, or URLs.
- **`TBD` / `Unknown`** when not verifiable.
- Prefer **last official edition** over `TBD` conference dates for recurring events.
- Open CfP, no close date → deadline `TBD`, URL in link column, `cfp: open close unlisted` in notes (not a prose dump).
- **Never** copy city, ISO dates, `MM-DD`, or primary portal URLs into `notes`.

## CSV editing

Quoted commas; empty optional links; bump `last_verified_date` on every touched row; no wide unrelated reformats.

## Checklist

```
- [ ] Row located or confirmed new
- [ ] Official site + CFP checked
- [ ] Structured fields filled; deadlines MM-DD or TBD (never blank)
- [ ] notes use blurb + optional history:/cfp:/speakers:/src: (no column dupes / bare URLs)
- [ ] submission_tracks allowlisted extras only (or empty)
- [ ] last_verified_date + notes/sources
- [ ] User summary ready
```

## Deliverable

1. Added / updated counts and names  
2. Key field changes  
3. High-priority gaps still `TBD`/`Unknown`  
4. Sources when non-obvious  

## Verify locally (optional)

`python3 scripts/validate_catalog.py`  
`python3 -m http.server 8000` → `index.html`

## Examples

| Case | Do |
|------|-----|
| CfP open, no close | `cfp_*=TBD`, portal URL in link column, notes `cfp: open close unlisted` |
| CfP closed | Keep `MM-DD`; keep conference dates; do not restate date in notes |
| Talks only | Empty `submission_tracks` |
| Talks + CTF | `submission_tracks=CTF` |
| Prior editions | `history: 2023 City; 2024 City` — not full date reprint if columns hold latest |
| New BSides | New row; pretalx/sessionize; `venue_pattern` when known |
| City moved | `history:` + note; separate row if user wants new city tracked |
