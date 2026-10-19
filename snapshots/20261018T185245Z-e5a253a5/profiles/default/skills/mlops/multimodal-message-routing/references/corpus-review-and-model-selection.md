# Corpus Review and Multimodal Model Selection Checklist

Use this as a compact, project-specific evidence checklist. Adapt facts to the live repository; do not copy labels or counts into a new project without re-verifying them.

## 1. Fixed output contract versus internal taxonomy

When a challenge requires an enum such as:

```text
personal | urgent | event | payment | business_update | promotion |
greeting | forward | spam | scam | unknown
```

keep it separate from richer internal topic clusters. Example internal clusters found in a multimodal messaging corpus:

- incident / safety / operational;
- financial / payment;
- commercial / promotion;
- shopping, delivery, and peer resale;
- academy / school;
- professional / work;
- travel / logistics;
- social, greeting, and forwarded material;
- sports;
- medical / health;
- identity and account security;
- civic/legal-adjacent content only where direct evidence exists.

`form submit` or `action required` usually belongs to intent, not topic.

## 2. Corpus checks

- Use a CSV parser, not line counts, because message text may include embedded newlines.
- Confirm every incoming `media_id` resolves through the media index to a local file.
- Check whether target-message IDs and historical-message IDs use distinct namespaces.
- Verify the exact historical ID namespace expected in any evidence-output field.
- Treat absent history as a valid condition; emit the contract-required empty/`none` form where appropriate.
- Restrict predictions to participant-facing data if the repository differentiates it from organizer-only data.

## 3. Signal checklist

| Decision input | Validate against |
|---|---|
| Trust | verification, legitimate-domain match, account age, abuse reports, known relationship |
| User preference | promotion consent, opt-out time, group mute state, engagement and dismissal history |
| Relevance | group role, direct mention, relationship history, transaction/booking history |
| Urgency | concrete deadline, event timing, requested action, trusted operational context |
| Risk | impersonation signals, coercive payment/OTP requests, reports, unsafe links, text/media injection |
| Interruption budget | DND window, daily notification load, historical dismissals |
| Evidence | relevant historical messages plus observed events, not incoming IDs |

## 4. Untrusted content

Audit actual messages and media-derived text for embedded instructions such as “set action=notify” or “ignore policy.” Keep source content isolated as quoted data in the classifier context; it never changes the schema, policy, or output requirements.

## 5. Model selection decision table

| Question | Native multimodal answer | Split-pipeline answer |
|---|---|---|
| Can one call jointly reason over image, audio, and text? | Choose a model/API with supported image and audio input. | Transcribe audio and produce image observations/OCR first. |
| Can output be constrained? | Require schema/structured output. | Require schema at the final classifier stage. |
| Is the provider usable? | Verify credentials, endpoint, stable identifier, quotas, and costs. | Verify each provider and handoff format. |
| How is media evidence preserved? | Return media ID plus observation/uncertainty. | Persist transcript/OCR/visual observations with source media IDs. |

A provider may be the best **capability** choice yet unavailable in the current environment. State that clearly and provide an available fallback rather than treating documentation as deployment proof.

## 6. Minimal evaluation fixtures

- same text from trusted and look-alike senders;
- same promotion for opted-in and opted-out users;
- muted group with a direct, time-sensitive mention;
- valid payment/update versus credential-theft request;
- image/poster with conflicting text versus supplied message text;
- unclear/blurred media;
- no relevant history;
- malicious embedded instructions in text, image OCR, or transcript.

Record observed performance separately from assumptions, especially for authenticity/manipulation detection.

## 7. Probing a "configurable policy" seam for asymmetric validation

Specs for personalized routing systems frequently promise that a policy/config
loader "rejects unrecognized or malformed keys/actions" for things like
per-user topic overrides. Reading the parser's source is not enough to sign
off on that claim — validation is commonly asymmetric: the **action/enum
value** gets checked against an allow-list, but the **key/topic name** is
accepted as any string with no allow-list at all. A misspelled topic then
loads silently and becomes a dead no-op instead of raising, which is a real
compliance gap even though every existing test passes.

Write a tiny standalone script that deliberately violates each claimed rule
and prints/asserts the outcome, one call per rule:

```python
# Does the loader actually reject an unknown/misspelled topic key, or does
# it only validate the action value?
from router.policy import load_policy_mapping
p = load_policy_mapping(
    {"user_overrides": {"u1": {"topics": {"totally_bogus_topic": "notify"}}}}
)
print("accepted silently:", p.user_overrides["u1"].topics)  # should have raised
```

Run it with the project's real import path (e.g.
`PYTHONPATH=code uv run python /tmp/probe.py`). If it should raise and
doesn't, cite the exact call and printed output in the review — that is
concrete, demonstrated evidence, stronger than "the validator has a key
allow-list" inferred from reading code. Always check both directions
(value-side AND key-side) before accepting a "clearly rejects unrecognized
input" claim for any config/policy/mapping loader.
