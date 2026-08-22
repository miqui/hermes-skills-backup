# Slack mrkdwn conversion guide

Use this reference when turning a Markdown artifact into a Slack message.

## Convert, do not copy blindly

| Source form | Slack delivery form |
| --- | --- |
| `# Heading` | Standalone `*Heading*` line |
| Markdown table | Short labeled bullets: `• Key: value` |
| `- [ ] Task` | `☐ Task` or `Pending: Task` |
| `- [x] Done` | `☑ Done` or `Complete: Done` |
| `[label](https://example.com)` | `label: https://example.com` or `<https://example.com|label>` |
| Full document in one fence | Render prose; fence only source/config/commands |
| Mermaid/HTML/footnotes | Explain the content in prose; attach or link the source if needed |

## Delivery patterns

### Short completion update

```text
*Completed: dependency audit*

• Changed: `docs/dependencies.md`
• Verified: `npm test` → 42 passing
• PR: https://github.com/org/repo/pull/123
```

### Long artifact introduction

```text
*Completed: JVM diagnostics skill*

Validated frontmatter and related-skill references. The rendered skill follows in two parts; command and YAML blocks are preserved exactly.
```

Then divide at meaningful section boundaries and label each continuation:

```text
*JVM diagnostics skill (1/2)*
```

Do not split a code fence across messages. Repeat only the minimum context needed for a later part to stand alone.

### Blocker

```text
*Blocked: production heap dump requires approval*

• Observed: dump would trigger a full GC and may contain customer data.
• Impact: retention analysis cannot proceed safely.
• Needed: approval for a sanitized off-peak capture, or a lower-impact JFR recording.
```

## Final pre-send check

- Does the first line say what happened?
- Are any GFM tables, headings, or task-list markers still present?
- Are literal commands and paths fenced or backticked?
- Is every URL usable without relying on custom rendering?
- Could a reader skim the message in under 15 seconds and find the outcome?
