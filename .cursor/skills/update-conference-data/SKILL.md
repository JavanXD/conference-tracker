---
name: update-conference-data
description: >-
  Add or update rows in data/conferences.csv for the Conference Tracker dashboard.
  Use when the user asks to add a conference, update deadlines/links/location,
  fix missing data, verify CFP/CfT/CfW, enrich notes, or edit conference catalog
  entries. Schema: docs/CATALOG.md. Requires web research from official sources
  before writing values. Follow CATALOG one-fact-per-column and notes rules.
---

# Update conference data (`data/conferences.csv`)

**Canonical schema (columns, enums, deadlines, notes, UI mapping):** [`docs/CATALOG.md`](../../../docs/CATALOG.md) — follow it; do not invent parallel rules here.  
**PR workflow:** [CONTRIBUTING.md](../../../CONTRIBUTING.md).

## Scope

- **In scope:** `data/conferences.csv` only.
- **Out of scope:** `index.html` / `app.js` unless the user asks for UI changes.

## Before editing

1. Confirm column order and field rules in [`docs/CATALOG.md`](../../../docs/CATALOG.md) (never reorder the header).
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

**Collect structured facts into the correct columns first** (see CATALOG “One fact, one column”). Write **`notes`** only for leftovers per [Notes format](../../../docs/CATALOG.md#notes-format).

### Dates when the row is stale or empty

1. Official site (blog, FAQ, archives) + **CfP Watch** / submission portals.
2. Verified listings — confirm on organizer or official source.
3. **Write:** latest edition start/end for this row’s city; matching deadlines; prior years in a `history:` notes segment; set `venue_pattern` / `last_verified_date` per CATALOG.

### Hard limits

- **Never invent** dates, deadlines, or URLs.
- **`TBD` / `Unknown`** when not verifiable.
- Prefer **last official edition** over `TBD` conference dates for recurring events.
- Open CfP, no close date → deadline `TBD`, portal URL in the link column, `cfp: open close unlisted` in notes (not a prose dump).
- **Never** duplicate city, dates, deadlines, or primary portal URLs into `notes`.

## CSV editing

Quoted commas; empty optional links; bump `last_verified_date` on every touched row; no wide unrelated reformats. Full field rules: [`docs/CATALOG.md`](../../../docs/CATALOG.md).

## Checklist

```
- [ ] Row located or confirmed new
- [ ] Official site + CFP checked
- [ ] Fields follow docs/CATALOG.md (deadlines, tracks, notes, last_verified_date)
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
| CfP open, no close | Deadline `TBD`, portal in link column, notes `cfp: open close unlisted` |
| CfP closed | Keep deadline MM-DD; do not restate it in notes |
| Talks only | Empty `submission_tracks` (implied by deadline/link) |
| Talks + CTF | `submission_tracks=CTF` |
| Prior editions | `history: 2023 City; 2024 City` — columns hold latest |
| New BSides | New row; pretalx/sessionize; `venue_pattern` when known |
| City moved | `history:` + note; separate row if user wants new city tracked |
