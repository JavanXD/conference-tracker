# Conference catalog (`data/conferences.csv`)

Canonical reference for the static catalog in `data/`. The dashboard loads it with Papa Parse; invalid values may coerce to `TBD`/`Unknown` (`normalizeAndValidateRows` in `app.js`).

**How to edit rows:** [`.cursor/skills/update-conference-data/SKILL.md`](../.cursor/skills/update-conference-data/SKILL.md) (research workflow). **PRs:** [`CONTRIBUTING.md`](../CONTRIBUTING.md).

**Not stored in CSV:** `accepts_cfp` … `accepts_cfv`, `cfp_deadline_month` — derived on load from `*_deadline_MM-DD`.

## Header (do not reorder)

```
conference_name,priority_level,attendees_500_plus,academic_acceptance_level,submission_tracks,travel_accommodation_sponsorship,cfp_deadline_MM-DD,cft_deadline_MM-DD,cfw_deadline_MM-DD,cfv_deadline_MM-DD,conference_start_date,conference_end_date,city,country,website,cfp_link,cft_link,cfw_link,cfv_link,conference_type,timezone,notes,last_verified_date,venue_pattern
```

## Columns

| # | Column | Values / notes |
|---|--------|----------------|
| 1 | `conference_name` | Official name (required) |
| 2 | `priority_level` | `High` \| `Medium` \| `Low` — see [priority](#priority) |
| 3 | `attendees_500_plus` | `Yes` \| `No` \| `Unknown` |
| 4 | `academic_acceptance_level` | `Academic` \| `Industry` \| `Mixed` \| `Unknown` |
| 5 | `submission_tracks` | Optional **extras only** — allowlist: `CTF` \| `Villages` \| `Panels` \| `Briefings` \| `Unconference` \| `Exhibition` \| `Mentorship` (pipe-separated). See [Name badges](#name-badges) |
| 6 | `travel_accommodation_sponsorship` | `Yes` \| `No` \| `Unknown` \| `Partial` |
| 7–10 | `*_deadline_MM-DD` | `MM-DD` or `TBD` — **source of truth** per submission type; keep **past** close dates |
| 11–12 | `conference_start_date`, `conference_end_date` | `YYYY-MM-DD` or `TBD` — fill **last official edition** when next year unknown; edition history / relocation in `notes` |
| 13–14 | `city`, `country` | Plain text; `TBD` city ok; normalize country names — see [countries](#country-names) |
| 15 | `website` | Conference homepage |
| 16 | `cfp_link` | Dedicated talk CfP portal when distinct from homepage — see [links and UI](#links-and-ui) |
| 17–19 | `cft_link`, `cfw_link`, `cfv_link` | Dedicated portal only — see [links and UI](#links-and-ui) |
| 20 | `conference_type` | `In-Person` \| `Hybrid` \| `Virtual` |
| 21 | `timezone` | IANA id |
| 22 | `notes` | Extra evidence only — see [Notes format](#notes-format) (do **not** repeat other columns) |
| 23 | `last_verified_date` | `YYYY-MM-DD` — set to **today** on every row you touch |
| 24 | `venue_pattern` | `Rotating` \| `Mostly Fixed` \| `Fixed` \| `Unknown` |

### One fact, one column

| Fact | Store in | Never also put in `notes` / `submission_tracks` |
|------|----------|-----------------------------------------------|
| Name | `conference_name` | — |
| City / country | `city`, `country` | — |
| Edition dates | `conference_start_date`, `conference_end_date` | — |
| Deadline closes | `cfp_` / `cft_` / `cfw_` / `cfv_` `*_deadline_MM-DD` | — |
| Homepage / type URLs | `website`, `cfp_link`, `cft_link`, `cfw_link`, `cfv_link` | — |
| Format / TZ | `conference_type`, `timezone` | — |
| Travel support enum | `travel_accommodation_sponsorship` | Only **nuance** in notes (amounts, caps) |
| Talks / trainings / workshops | Deadlines and/or type links | Not in `submission_tracks` |

### Notes format

`notes` is for **non-column** facts. Use short semicolon-separated segments agents can parse:

```
unique blurb; history: YYYY[ City]; …; cfp: open close unlisted; speakers: <nuance>; src: <secondary URL>
```

| Segment | When | Example |
|---------|------|---------|
| Leading blurb | Always if useful (≤ ~220 chars) | `WarCon-inspired invite-only Czech IT security` |
| `history:` | Prior editions / relocation | `history: 2023 Prague; 2024 Prague; 2025 Prague` |
| `cfp:` | Close date unlisted or multi-portal ambiguity | `cfp: open close unlisted` |
| `speakers:` | Detail beyond Yes/Partial/No | `speakers: flight<=500EUR + 1 hotel night` |
| `src:` | Secondary source only (not the primary link columns) | `src: https://cfp.directory/events/…` |

**Forbidden in `notes`:** restating the conference name, city, country, start/end ISO dates, `MM-DD` deadlines, or any URL already in link columns. Any secondary URL must live in a `src:` segment. Do not paste the whole CFP page.

**Maintainers:** `python3 scripts/normalize_catalog_dedupe.py` rewrites tracks/notes/deadlines toward this shape; `python3 scripts/validate_catalog.py` enforces it in CI.

### Deadlines (`MM-DD`)

| Record | Column |
|--------|--------|
| Talk / training / workshop / volunteer close | `cfp_` / `cft_` / `cfw_` / `cfv_` |
| No public or unknown close | `TBD` + explain in `notes` |

Do **not** clear deadlines or conference dates when CfP is closed. Open on PaperCall/Sessionize with no close date → `TBD` + portal URL + note. **Never leave deadline cells empty** — use `TBD`.

`MM-DD` is resolved against **conference edition year** from `conference_start_date` (CfP month-day before event start → prior calendar year). Actionable vs past is computed in `app.js`.

### Conference dates (`YYYY-MM-DD`)

| Situation | Action |
|-----------|--------|
| Next edition announced | Official start/end |
| Not announced | Latest **verifiable** edition (even years ago); older runs in `notes` |
| Series relocated | Regional row keeps last **local** dates; note new city or add a row |
| Nothing verifiable | `TBD` only then |

Single-day: same date in start and end. Stale CSV years still matter: missing conference dates → **TBD** / empty **Next Due** even though the UI can project occurrences once dates exist.

## Links and UI

| Curator sets | Speaker table |
|--------------|----------------|
| `MM-DD` + type link | Linked date |
| `MM-DD`, link empty | Date only |
| `TBD` + URL for that type | Platform emoji (Sessionize 📅, PaperCall 📣, …) |
| `TBD`, no URL | Empty cell |

| Field | Rule |
|-------|------|
| `website` | Conference homepage |
| `cfp_link` | Distinct talk CfP portal (PaperCall/Sessionize/…); UI falls back to `website` if empty |
| `cft_link` | Distinct training portal; implies **Trainings** (no need to repeat in `submission_tracks`) |
| `cfw_link` | Distinct workshop portal; implies **Workshops** |
| `cfv_link` | Volunteer / staff call |

**Filters:** *Has deadline* = valid `MM-DD`; *No deadline* = `TBD`/empty (includes link-only). **Open CfPs** = CfP still in the future. **Sponsorship** `Unknown` → **—**; filter **Unset**. Detail panel lists deadlines + links. Export omits derived `accepts_*`.

### Name badges

Small letters beside the conference name (e.g. **C** = CTF) are **not** separate CSV columns.

| Source | Effect |
|--------|--------|
| `cfp_deadline_MM-DD` (valid) | **Talks** implied — no **P** badge (CfP column covers talks) |
| `cft_deadline_MM-DD` or `cft_link` | **Trainings** implied — no **T** badge |
| `cfw_deadline_MM-DD` or `cfw_link` | **Workshops** implied — no **W** badge |
| `submission_tracks` | Only tokens **not** implied above become badges (typically `CTF`, `Panels`, `Villages`) |

**Minify CSV:** leave `submission_tracks` empty when the row only has talks/trainings/workshops via deadline/link columns; add allowlisted extras only (`CTF|Villages|Panels|…`). Map `Contests` → `CTF`. Do not store topic tags (`AI`, `Keynotes`, …). Detail **Tracks** merges implied + listed tokens.

**Next Due / Start / End (display):** projects next calendar occurrence from stored dates (`est.`, italic dates); ICS and “open CfP” filters use **stored** values only. Pipeline/trip default year = projected occurrence.

## CSV quoting

Quote fields that contain commas; escape `"` as `""`.

```csv
ExampleCon,High,Yes,Industry,,Unknown,03-15,TBD,TBD,TBD,2026-06-01,2026-06-03,Berlin,Germany,https://example.com,https://example.com/cfp,,,,In-Person,Europe/Berlin,"history: 2024 Berlin; 2025 Berlin",2026-06-01,Rotating
```

(`submission_tracks` empty — talks implied by `cfp_deadline_MM-DD`. Homepage and CfP portal are separate columns; deadline and city live in columns, not notes.)

## Priority

| Level | Typical |
|-------|---------|
| `High` | Major industry cons, flagship camps |
| `Medium` | Regional cons, AppSec days, mid BSides |
| `Low` | Small/local BSides, unconfirmed |

## Country names

`United States`, `United Kingdom`, `United Arab Emirates`, `Netherlands`, `Czech Republic`, `South Korea`; city spelling per official site when stable.

## App validation (on load)

Invalid `MM-DD` / `YYYY-MM-DD` → `TBD` + console warning; bad `venue_pattern` → `Unknown`; mistaken `cft_`/`cfw_` homepage links may be stripped when tracks don’t match. Fix CSV rather than relying on coercion.
