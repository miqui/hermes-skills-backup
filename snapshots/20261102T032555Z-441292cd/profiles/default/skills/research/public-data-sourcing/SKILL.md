---
name: public-data-sourcing
description: Use when sourcing public data with no documented API.
metadata:
  hermes:
    tags: [public-data, open-data, government-data, api-reverse-engineering, data-sourcing, research]
---

# Public data sourcing

Use when a project needs programmatic access to public or government data that has no documented API — locating the system of record, checking open-data portals first, reverse-engineering JS-portal backends, and verifying endpoints with live probes before building.

## Overview

Data projects that start from a government web page usually have no documented API. The page the user cites is often a link farm that delegates to a system-of-record portal run by a vendor (Tyler Technologies, Socrata, ArcGIS Hub, Granicus). Most such portals are JS SPAs whose bundles reveal the exact JSON endpoints they consume. The deliverable of a sourcing pass is verified endpoints with live-probe evidence plus an ingest design — never a scraping plan against HTML.

## Procedure

1. Fetch the cited landing page. If it holds no data, only links, follow the delegation link to the system of record — do not scrape the link farm.
2. Check official open data before reverse-engineering: Socrata (`/api/views`, `data.json`), ArcGIS Hub (`/api/download/v1/items/<id>/csv`), CKAN, data.gov harvest records. A county or city portal may publish a cleaner subset than the state portal — verify its jurisdictional coverage before relying on it.
3. If the portal is an SPA shell (2–3 KB HTML, `require.js`/Backbone/React bundles, no server-rendered data), fetch the bundle JS with curl and grep it for endpoint construction: `url`, `api`, `.cfm`, `getJSON`, `ajax`. Resource paths are typically assembled as `<base>/API/<resource>/<arg>` inside a helpers or router module; read that module to learn every resource name and argument.
4. Reconstruct request shapes from the client code, not from guesses: note the encoding chain (values base64-encoded inside a JSON object that is itself URL-encoded is a common pattern), pagination indexing and page size, and any `filters`-style resource that enumerates the valid filter values.
5. Verify with live probes before promising the user anything: one unfiltered list, one filtered query, one detail/children query, and two adjacent page numbers. Confirm page size and 0- vs 1-indexing empirically — do not assume either.
6. Deliver: verified endpoints with example live results, alternatives considered (commercial APIs, bulk datasets) and why rejected, and the ingest design — own normalized store plus a rate-limited incremental sync.

## Pitfalls

- Do not scrape the rendered HTML of an SPA — the DOM is a shell; grep the JS bundles for endpoint construction, or you will hand-build a fragile scraper around data the site already serves as JSON.
- Retry transient 5xx with a delay before concluding an endpoint is broken — undocumented endpoints fail sporadically, and recording a retry-failure as "endpoint broken" poisons the design.
- Treat undocumented endpoints as unguaranteed: build on your own DB with a polite rate limit (~1 req/s), so a vendor change degrades sync instead of taking the service down.
- Encode filter values exactly the way the client code does — decode the bundle's encoding chain first; most probe failures are an encoding-layer mistake, not a wrong endpoint.
- Confirm the geographic coverage of every candidate source — state portals cover all counties, county open-data portals cover only their own jurisdiction.

## Reference

`references/tyler-dhd-health-portal.md` — verified endpoint map for Tyler Technologies DHD health-inspection portals (Georgia restaurant inspection scores live there).
