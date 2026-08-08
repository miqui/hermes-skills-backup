---
name: slack-communication
description: Use when formatting messages for Slack. Use mrkdwn.
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [slack, communication, formatting, mrkdwn, delivery]
    related_skills: [humanizer]
---

# Slack communication

## Overview

Slack is a conversational delivery surface, not a GitHub README renderer. Write messages for fast scanning in the client: lead with the result, keep context proportional, and use Slack-compatible `mrkdwn` primitives. Do not assume GitHub-Flavored Markdown (GFM) headings, tables, task lists, or Markdown-link rendering will be interpreted as intended.

For this user, concise and actionable Slack `mrkdwn` is the default. Use GFM only when the user explicitly requests it. If they ask to display a Markdown artifact in Slack, render it for reading in Slack rather than wrapping the complete document in a single opaque code block, unless they explicitly request raw source.

## When to use

Use this skill when:

- Responding in a Slack thread, channel, or DM.
- Posting a status, plan, decision, review, PR summary, or technical result in Slack.
- Translating a Markdown document, report, table, checklist, or skill into Slack-readable content.
- Reporting a long technical artifact where readability and copyability must be balanced.
- The user asks for "Slack-compatible Markdown," "mrkdwn," or to display a document in Slack.

Do not use this skill to alter a file just because it will later be shared in Slack. Preserve the source document's requested format; adapt the *message that delivers it*.

## Default message shape

Use the smallest structure that makes the result actionable:

1. **Result first.** State completion, blocker, decision, or answer in the first line.
2. **Evidence next.** Give the essential IDs, files, commands, measurements, or links.
3. **Action only if needed.** State the one next decision or user action; do not add generic offers to help.

For a short update, use one or two sentences. For a technical result, use a bold label followed by short bullets. Avoid prefatory phrases such as "Here is," "Certainly," or "I hope this helps."

## Slack `mrkdwn` primitives

Use these portable constructs:

| Intent | Prefer | Example |
| --- | --- | --- |
| Emphasis | `*bold*` | `*Validation passed*` |
| Light emphasis | `_italic_` | `_Optional_` |
| Deletion | `~strike~` | `~deprecated~` |
| Inline code | backticks | `` `./gradlew test` `` |
| Code sample | fenced block | triple-backtick block |
| Quote | `>` | `> quoted decision` |
| Bullet list | `•` or `-` | `• Run targeted tests` |
| Ordered steps | `1.`, `2.` | `1. Capture baseline` |
| Link | raw URL, or Slack link syntax when supported | `Docs: https://…` or `<https://…|Docs>` |

Use a raw URL when label syntax could make the message harder to copy, audit, or render across clients.

## GFM features to avoid by default

Do not rely on these in Slack output:

- `#` / `##` Markdown headings. Use a standalone `*bold label*` instead.
- Pipe tables. Convert them into labeled bullets or compact `key: value` lines.
- GitHub task lists such as `- [ ]` or `- [x]`. Use `☐`, `☑`, or plain status words instead.
- Footnotes, HTML, Mermaid, collapsible sections, and embedded HTML links.
- A language tag after a code fence when portable rendering matters. Plain fenced blocks are safest.
- Markdown images. Attach media through the platform when available, then describe it with alt text in the message.

## Presenting long Markdown artifacts

When the user wants a long document, skill, plan, or report displayed in Slack:

1. Start with a one-line outcome and any verification status.
2. Render prose sections with Slack-compatible bold labels, bullets, and numbered steps.
3. Preserve commands, config, source snippets, and literal frontmatter in focused fenced code blocks.
4. Replace tables with labeled lists; retain each row's meaning.
5. Keep links copyable and visible.
6. If the full artifact is too long for one message, split on natural section boundaries and number the parts. Never silently omit a section.
7. Offer or attach the raw source only when useful or explicitly requested.

For a `SKILL.md`, show the title and explanatory sections as Slack prose. Put YAML frontmatter and executable command examples in their own fenced blocks. Do not present the whole `SKILL.md` as one fenced block unless the user asked for the literal file contents.

## Technical status format

Use this shape for engineering work:

```text
*Completed: <outcome>*

• Changed: `<path>`
• Verified: `<command or check>` → <result>
• Review/PR: <URL or status>

*Next action:* <only when a decision is needed>
```

Omit empty categories. Do not claim completion, validation, publication, or CI success without actual evidence.

## Decision and blocker format

```text
*Decision needed: <subject>*

• Option A: <impact>
• Option B: <impact>

*Recommendation:* <one clear choice and reason>
```

```text
*Blocked: <specific blocker>*

• Observed: <actual error or missing prerequisite>
• Impact: <what cannot proceed>
• Needed: <smallest user action or decision>
```

## Common pitfalls

1. **Using GFM headings and tables.** Slack can show them as raw punctuation or hard-to-scan text. Use bold labels and lists.
2. **Posting raw source when the user asked to see the artifact.** Source-only delivery is difficult to read. Render prose and isolate only literal code/configuration.
3. **Putting every detail in a code block.** Code blocks prevent emphasis and reduce scanability. Reserve them for text that must be copied exactly.
4. **Treating a PR link as the result.** State what changed and what verification actually ran.
5. **Adding generic conversational filler.** Begin with the outcome and stop when the user has what they need.
6. **Using GFM by habit.** The user interacts primarily through Slack; use `mrkdwn` unless they request another format.
7. **Turning a soft quality target into a delivery blocker.** Keep safety, authorization, and correctness gates. But if the user relaxes a non-essential preference (such as an ideal document length), update the plan immediately and deliver once essential verification is satisfied. Do not repeatedly post progress-only updates while the user is waiting for a usable result.

## Verification checklist

- [ ] The first line communicates the outcome, blocker, or decision.
- [ ] Formatting uses Slack-compatible `mrkdwn` primitives.
- [ ] No GFM-only headings, tables, or task lists remain unless explicitly requested.
- [ ] Commands, paths, IDs, and URLs are copyable.
- [ ] Long artifacts are sectioned without omitted content.
- [ ] Claims of validation, publication, or completion have evidence.
- [ ] The message contains no generic filler or unnecessary invitation to continue.

## Reference

See `references/slack-mrkdwn.md` for a compact conversion guide and example delivery patterns.
