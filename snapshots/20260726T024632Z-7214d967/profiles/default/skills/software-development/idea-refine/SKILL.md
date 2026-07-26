---
name: idea-refine
description: Use when refining an early idea, feature concept, workflow change, or product direction through structured divergent and convergent thinking. Helps turn a vague concept into a sharper recommendation, explicit assumptions, and a concrete one-pager.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [ideation, strategy, product, planning, refinement]
    related_skills: [writing-plans, spike]
---

# Idea Refine

## Overview

Use this skill to turn a rough idea into a sharper, more actionable direction worth building, testing, or rejecting. The goal is not to produce a large brainstorm dump. The goal is to help the user think clearly, surface the real problem, explore a handful of strong alternatives, pressure-test them honestly, and end with a concrete artifact that moves work forward.

This skill works best when the input is still fuzzy: a startup idea, a feature request, a workflow change, a process improvement, or a strategic direction that sounds promising but has not yet been framed well. It can also be used inside an existing codebase, where current architecture and constraints should shape the ideation rather than being ignored.

The core rhythm is:
1. **Understand & Expand** — clarify the problem and generate strong variations.
2. **Evaluate & Converge** — stress-test the best directions for value, feasibility, and differentiation.
3. **Sharpen & Ship** — produce a short, practical one-pager with a recommendation, assumptions, MVP scope, and a clear "not doing" list.

## When to Use

Use this skill when:
- The user has a vague idea and wants help refining it.
- The user wants to explore multiple directions before committing to implementation.
- The user needs a sharper product, feature, or workflow concept.
- The user wants honest pushback, not just brainstorming support.
- The user needs a concrete output such as a recommendation memo, MVP scope, or next-step plan.
- The idea should be grounded in an existing codebase, product context, or operational constraint.

Do not use this skill when:
- The user already has a clear implementation plan and wants coding help right now.
- The task is pure execution, bug-fixing, or code review with no strategic ambiguity.
- The user only wants a long list of random ideas without evaluation.
- The problem is already fully specified and the next step should be `writing-plans` or implementation.

## Working Style

This skill is conversational, but it should not wander.

- Ask a brief batch of **3-5 sharpening questions** when key context is missing.
- Restate the problem as a crisp **"How might we..."** framing early.
- Generate **5-8 idea variations**, not 20 shallow ones.
- Label the lens behind each variation when useful: inversion, simplification, audience shift, combination, first principles, constraint removal, analogous inspiration.
- Push back on weak ideas. This skill should be honest, not flattering.
- When operating inside a project, inspect the codebase with Hermes-native file tools so the ideation reflects real architecture, constraints, and prior art.
- End with a concrete artifact, not just a conversation transcript.

### Experienced-collaborator mode

When the user wants a **human-in-the-loop**, experienced-collaborator interaction, do not run the whole refine loop as one monologue. Use **explicit checkpoints** and pause for validation before converging.

Recommended checkpoint rhythm:
1. **After problem framing** — restate the problem, target user/use case, assumptions, and early risks; then pause for correction.
2. **After option comparison** — compare 2-4 plausible directions with honest tradeoffs; then pause for preference/steer.
3. **Before locking the recommendation** — present the recommended direction, MVP scope, not-doing list, and key open decisions; then pause for sign-off before moving into planning.

At these checkpoints:
- treat the user as a peer, not a novice
- prefer crisp tradeoff language over tutorial explanation
- recommend a direction, but do **not** lock it in until the user validates it
- surface edge cases, failure modes, and risks early rather than as an appendix

## Phase 1 — Understand & Expand

### Goal
Take the raw idea and open it up without losing the actual problem.

### Method

1. **Restate the idea** as a concise "How might we..." problem statement.
   - Good: outcome-focused, user-specific, not solution-embedded.
   - Bad: already commits to a specific implementation.

2. **Ask 3-5 sharpening questions** when needed.
   Focus on:
   - Who is this for, specifically?
   - What does success look like?
   - What constraints actually matter?
   - What is being used today instead?
   - Why now?

   Do not proceed blindly if the user, success criteria, and major constraints are still unclear.

3. **Generate 5-8 variations** using strong ideation lenses.
   Useful lenses include:
   - **Inversion** — what if we did the opposite?
   - **Constraint removal** — what if time, budget, or tooling were not the limit?
   - **Audience shift** — what if this were for a different user?
   - **Combination** — what if this merged with an adjacent idea?
   - **Simplification** — what is the 10x simpler version?
   - **10x version** — what would this look like at extreme scale or ambition?
   - **Expert lens** — what would domain insiders find obvious that outsiders miss?

4. **Ground ideas in reality when context exists.**
   If the idea lives inside an existing codebase or workflow, inspect current files and patterns with Hermes tools like `search_files` and `read_file`. Reference specific constraints instead of ideating in a vacuum.

5. **Use support files selectively.**
   Read `frameworks.md` for extra ideation lenses when the obvious ones are not enough.

### Output of Phase 1
- A strong "How might we..." framing
- A clearer definition of user, goal, and constraints
- 5-8 meaningful idea variations with reasons, not just labels

## Phase 2 — Evaluate & Converge

### Goal
Reduce the space of possibilities honestly instead of carrying every idea forward.

### Method

1. **Cluster the strongest ideas** into 2-3 distinct directions.
   Each direction should represent a real strategic choice, not cosmetic variants.

2. **Stress-test each direction** using three core dimensions:
   - **User value** — who benefits, how strongly, and how often?
   - **Feasibility** — what is hard technically, operationally, legally, or organizationally?
   - **Differentiation** — what makes this meaningfully different, not just slightly better?

3. **Surface hidden assumptions** explicitly.
   For each direction, name:
   - What must be true for this to work
   - What could kill the idea
   - What is intentionally being ignored for now

4. **Be honest about trade-offs.**
   If an idea is weak, say so. If one direction is compelling but risky, say that too. This skill is useful precisely because it narrows and judges, not because it preserves optionality forever.

5. **Use the deeper rubric when needed.**
   Read `refinement-criteria.md` for the full evaluation framework, including assumption tiers and MVP scoping principles.

### Output of Phase 2
- 2-3 clustered directions
- A reasoned comparison across value, feasibility, and differentiation
- Explicit assumptions and dealbreakers
- A recommended direction with a clear rationale

## Phase 3 — Sharpen & Ship

### Goal
Turn the thinking into a compact artifact someone can act on.

### Default artifact
Produce a markdown one-pager in this shape:

```markdown
# [Idea Name]

## Problem Statement
[One-sentence "How might we..." framing]

## Recommended Direction
[Chosen direction and why]

## Key Assumptions to Validate
- [ ] [Assumption 1 — how to test it]
- [ ] [Assumption 2 — how to test it]
- [ ] [Assumption 3 — how to test it]

## MVP Scope
[What the smallest useful version includes]

## Not Doing (and Why)
- [Thing 1] — [reason]
- [Thing 2] — [reason]
- [Thing 3] — [reason]

## Open Questions
- [Question that needs resolution before build]
```

### Guidance
- The **"Not Doing"** section is mandatory. It forces focus.
- The final artifact should help someone decide what to test, build, or reject next.
- If the user wants the artifact saved to a repo or note file, confirm the destination before writing it.
- If the direction is mature enough to implement, suggest `writing-plans` as the next skill.

## Codebase-Aware Ideation

When the idea is attached to an existing product or repository:
- Inspect actual project structure before proposing directions.
- Use current architecture as both a constraint and a source of leverage.
- Reference concrete files, modules, data models, or APIs when they materially shape the recommendation.
- Avoid proposing an elegant concept that collides with the codebase's actual reality.

This skill should sound different inside a live codebase than it does in a greenfield product brainstorm.

## Tone

Direct, thoughtful, and slightly provocative. Be a sharp thinking partner, not a workshop facilitator reading a template. Push one level deeper than the user's first framing without becoming performative or exhausting.

## Support Files

Use these support files when needed:
- `frameworks.md` — additional ideation lenses and reframing tools
- `refinement-criteria.md` — evaluation rubric for Phase 2 and MVP scoping
- `examples.md` — examples of strong ideation sessions across product, feature, and process ideas

Do not dump these frameworks mechanically. Pick the lens that actually helps the current idea.

## Common Pitfalls

1. **Asking too many questions before generating value.**
   Ask enough to get clear, then move. Long intake interviews kill momentum.

2. **Generating too many weak variations.**
   5-8 considered options beat 20 shallow ones.

3. **Being a yes-machine.**
   Weak ideas need honest pressure-testing, not encouragement theater.

4. **Skipping the user and success criteria.**
   If you cannot say who this is for and what success looks like, the idea is not ready.

5. **Jumping to implementation too early.**
   This skill is for shaping direction first. Move to planning only after convergence.

6. **Ignoring existing constraints.**
   In a real codebase or business context, architecture and operational limits are part of the idea.

7. **Forgetting the "Not Doing" list.**
   Without explicit exclusions, the output becomes a wish list instead of a strategy.

## Verification Checklist

- [ ] A clear "How might we..." problem statement exists
- [ ] The target user and success criteria are defined
- [ ] Multiple directions were explored, not just the first idea
- [ ] The strongest directions were compared on value, feasibility, and differentiation
- [ ] Hidden assumptions were made explicit
- [ ] A recommended direction was chosen with rationale
- [ ] The final output includes MVP scope and a "Not Doing" list
- [ ] Any codebase-aware recommendations were grounded in actual project context
- [ ] If the idea is now implementation-ready, the handoff to `writing-plans` is obvious
