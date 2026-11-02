---
name: ga-restaurant-inspections
description: Use when building/syncing the GA restaurant-scores API.
metadata:
  version: '1.0'
  tags: [georgia, restaurant-inspections, hono, data-sourcing]
---

# Georgia Restaurant Inspection Scores — Data Source & Project Spec

## Source
- coastalhealthdistrict.org/home/restaurant_inspections has no data of its own; it delegates to the statewide portal https://ga.healthinspections.us/stateofgeorgia/ (Tyler Technologies DHD platform, Georgia DPH). Covers all 159 GA counties.
- No official API or statewide bulk download exists (only county exceptions like Fulton's Socrata portal). The portal is a Backbone SPA backed by an undocumented JSON API — endpoints below verified live 2026-10-08.

## JSON API (base: https://ga.healthinspections.us/stateofgeorgia/API/index.cfm)
- `GET /facilities/<page>` — paged facility list, 5 records/page: name, mapAddress, phone, permit type/number, last inspection score + date, base64 `id`.
- `GET /search/<urlencoded JSON>/<page>` — JSON body whose `keyword`, `county`, `city` values are base64-encoded, e.g. `{"county":"Q0hBVEhBTQ=="}` for CHATHAM; 5/page.
- `GET /inspectionsData/<base64 facilityId>` — full inspection history: date, purpose, score, inspector, violations[] (code, rule citation, points, corrected-on-site, repeat, notes) plus printablePath to the full report.
- `GET /filters` — dropdown values: 566 cities, 159 counties, permit types (Food Service / Tourist Accommodation / Swimming Pool).

## Quirks
- Results sorted by last-inspection date desc (newest first) → incremental sync walks pages until dates ≤ last watermark.
- Transient HTTP 500s observed on the portal → retry with backoff.
- ColdFusion portal, no auth needed; be polite: ~1 req/sec rate limit.
- Facility/search ids are base64 strings — URL-encode the `=` when used in paths.

## Scale (measured by binary-searching last page per county)
~4,390 facilities in the 8 Coastal Health District counties: Chatham 2,385; Glynn 865; Camden 350; Liberty 250; Bryan 215; Effingham 175; McIntosh 105; Long 45.
Full score backfill ≈ 880 page requests (~15 min at 1 req/s); violation detail adds ~1 req/facility (~1.5 hr one-time).

## Agreed project spec (Miguel's decisions)
- Read-only Hono REST API: Node + @hono/node-server, TypeScript, SQLite + Drizzle.
- Auth: hono/jwt + zod (self-rolled — better-auth was offered and rejected).
- Endpoints: GET /counties, /facilities?county=&city=&min_score=, /facilities/:id, /facilities/:id/inspections, /inspections/:id.
- Ingest: Node worker, county-scoped to the 8 coastal counties, rate-limited, nightly incremental sync (node-cron in-app or Hermes cronjob hitting a JWT-guarded /admin/sync).
- Tables: facilities, inspections, violations.
- CI: single keyless ci.yml (eslint + tsc, tests via Hono app.request(), npm ci, npm audit gate on high/critical, build), CodeQL via default setup, dependabot, secret scanning + push protection. Protect main at repo creation (PR + approval; required checks = workflow job names).
- Tests use recorded portal fixtures — CI never hits the live endpoint.
- Repo created via git-workflow.sh; README needs a Run manually section.
