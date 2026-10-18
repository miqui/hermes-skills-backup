# Secret Scanner Choice for Corpus Imports

## Default preference

This user prefers **betterleaks** over gitleaks for secret scanning during skill
imports. Check for it first (`which betterleaks`); use it when present. Only fall
back to gitleaks if betterleaks is unavailable and the user hasn't specified a
scanner, and note the substitution when you report results.

## Invocation

```bash
cd <path-to-cloned-skill-dir>   # scan the specific skill directory, not the whole repo
betterleaks dir . --no-banner --report-format json --report-path <tmp>/betterleaks_report.json
```

Read the console summary (`... leaks found` / `no leaks found`) and the JSON report
for the pass/fail signal. `dir` scans a working tree (not git history); use
`betterleaks git` if you need history-aware scanning of the upstream repo itself.

Note: on a clean scan, the JSON report file can be literally the 4-byte body
`null` (not `{}` or `[]`) — this is a valid "no leaks" result, not a malformed
report. Don't treat a `null`/empty-looking report as a scan failure; trust the
console summary line alongside it.

## Reporting rule (do not leak matched values)

Report only **path, category/rule-id, and line number** for any finding. Never
print or quote the matched secret value in the audit report, even redacted/partial
— this mirrors the CI secret-scan hygiene rule in `secure-agent-skills`. A clean
scan should be reported as "no leaks found" plus the byte/line count scanned, not
a dump of the raw JSON report.

### Safe inspection of a non-trivial report

If the report is non-null and you need to check finding counts or structure
before writing up results, do not `cat`/print the raw JSON (it may contain
matched secret fragments). Inspect it with `jq` for structure only, never for
values:

```bash
jq 'keys' report.json                       # top-level shape
jq '[.leaks // .findings // []] | length' report.json   # finding count only
jq '.leaks[]? | {path, rule, line}' report.json         # path/rule/line only — omit any "match"/"secret" field
```

This keeps the whole inspection in the terminal/jq layer — no need to load the
report into a general-purpose script interpreter just to count or filter it.
