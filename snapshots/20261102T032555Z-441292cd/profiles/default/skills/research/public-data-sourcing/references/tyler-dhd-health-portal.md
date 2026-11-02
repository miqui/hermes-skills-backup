# Tyler Technologies DHD health-inspection portals

Tyler Technologies' "Digital Health Department" platform publishes public inspection portals at `https://<jurisdiction>.healthinspections.us/<portal>/` (e.g. `stateofgeorgia` for Georgia DPH's statewide restaurant/pool/hotel scores). The portal HTML is a 2–3 KB shell — a Backbone + require.js SPA loads everything from `/publicportals/` bundles. `publicportals/libs/helpers.js` builds every request as `API/index.cfm/<resource>` relative to the portal path.

## Resources (GET, JSON responses)

- `API/index.cfm/facilities/<page>` — 5 records per page; page is a 0-indexed integer that can be advanced indefinitely. Record shape: `name`, `id` (base64 of the internal facility ID — use as-is in other resources), `mapAddress`, and `columns` — a dict of display strings (address, phone, permit type, permit number, last inspection score, last inspection date).
- `API/index.cfm/search/<urlencoded JSON>/<page>` — JSON keys: `keyword`, `county`, `city`, `dropdown`, `parish`; every VALUE is base64-encoded inside the JSON (e.g. `{"keyword":"c3VzaGk="}`), then the whole JSON is URL-encoded into the path. Same 5-per-page record shape.
- `API/index.cfm/inspectionsData/<base64 facilityId>` — full inspection history per facility: date, inspection purpose, score, inspector, a `violations` array (violation code, rule citation, points, corrected-during-inspection, repeat flag, inspector notes), and `printablePath` (relative URL of the full printable report; embeds the backend `dsn`/`domainid`).
- `API/index.cfm/filters` — enumerations for the search UI: cities (566), counties (159), permit types (Food Service, Tourist Accommodation, Swimming Pool). The UI also shows Score, Permit Number, and Last Inspection Date filters, but their values arrays are empty — no server-side filter values are published for them.

## Coverage and caveats

- Statewide jurisdiction data (Georgia: all participating counties; DPH notes Gwinnett/Newton/Rockdale are excluded from the statewide search). Per-county open-data portals exist separately but only cover their own county.
- No documented API and no published ToS — treat as public-record but unguaranteed; design ingestion as a rate-limited sync into an owned store.
- The ColdFusion backend occasionally returns transient HTTP 500 on valid requests — retry with a short delay before diagnosing.
- Scores and dates live inside `columns` display strings ("Last Inspection Score: 87") — parse them out before serving; do not treat `columns` keys as a stable schema.
