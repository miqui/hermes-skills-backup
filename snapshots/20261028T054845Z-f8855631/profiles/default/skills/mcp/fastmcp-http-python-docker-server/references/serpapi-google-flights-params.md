# SerpAPI Google Flights parameters used in `mcp-flights`

Validated from the SerpAPI Google Flights docs during a FastMCP server scaffold.

## Core fields

- `departure_id`
- `arrival_id`
- `outbound_date`
- `return_date`
- `currency`
- `hl`
- `adults`
- `children`
- `infants_in_seat`
- `infants_on_lap`
- `travel_class`
- `type`

## Advanced filters

- `stops`
  - `0` any number of stops
  - `1` nonstop only
  - `2` 1 stop or fewer
  - `3` 2 stops or fewer
- `bags`
- `max_price`
- `sort_by`
  - `1` top flights
  - `2` price
  - `3` departure time
  - `4` arrival time
  - `5` duration
  - `6` emissions
- `outbound_times`
- `return_times`
  - examples: `4,18`, `19,23`, `4,18,3,19`
- `include_airlines`
- `exclude_airlines`
  - documented as mutually exclusive with `include_airlines`
- `layover_duration`
- `exclude_basic`
- `deep_search`

## Useful validation rules

- `type=1` (round trip) should require `return_date`
- `type=2` (one way) should omit `return_date`
- `return_times` should require `return_date`
- normalize airline lists to uppercase comma-separated IATA codes
- convert booleans like `deep_search` / `exclude_basic` to lowercase strings if the upstream API expects query-string booleans
