# Design It Twice

Use this reference when a chosen deepening candidate has multiple plausible **interfaces** or **seam** placements. The first plausible interface is rarely the strongest. Produce competing designs, then compare their **depth**, **locality**, and seam placement.

Use the parent skill’s vocabulary consistently: **module**, **interface**, **seam**, **port**, **adapter**, **leverage**, and **locality**.

## 1. Frame the Problem Space

Before delegation, prepare a concise user-facing frame containing:

- the candidate’s one-sentence responsibility;
- current callers and the complexity they coordinate;
- constraints a new interface must satisfy;
- dependencies and their categories from `deepening.md`;
- a rough illustrative code sketch that makes constraints concrete without proposing a solution.

By default, present the frame and immediately explore alternatives. If the choice commits the user to a substantial refactor, use a checkpoint: present the frame, ask for confirmation of the candidate and constraints, then continue.

Build a technical brief for each designer from actual source files and any available architecture records, ADRs, or domain vocabulary. Do not assume a project `CONTEXT.md` exists. When such a file exists and is useful, include it; otherwise state the relevant module names, terms, invariants, and constraints directly in each brief.

## 2. Produce Competing Designs

Use `delegate_task` in batch mode to dispatch at least three independent design briefs in parallel. Each brief must include:

- absolute paths or relevant source excerpts;
- caller and coupling details;
- dependency categories and what sits behind the proposed seam;
- project and domain vocabulary;
- a distinct design constraint from the list below;
- an instruction to avoid implementation changes and return a design only.

Use these distinct constraints:

1. **Minimum interface** — aim for one to three entry points. Maximise leverage per entry point, even if advanced use cases require a separate composition layer.
2. **Flexible but deep** — support meaningful variation through composition, typed options, or injected strategies while keeping the external interface small. Do not proliferate methods or mirror provider mechanics.
3. **Common caller and progressive disclosure** — make the normal caller trivial, then offer advanced control through a carefully bounded option or request object rather than separate entry points.
4. **Ports and adapters** — use when remote-but-owned or true-external dependencies dominate. Place a port around the deep module’s intention and compare transport adapters without exposing them to callers.

Each design must return:

1. **Interface:** types, operations, parameters, results, invariants, ordering constraints, error modes, required configuration, and performance characteristics.
2. **Caller example:** a compact example of the most important caller crossing the seam.
3. **What the implementation hides:** policy, coordination, edge cases, and dependency details behind the seam.
4. **Dependency strategy:** categories, ports if justified, and production/test adapters.
5. **Trade-offs:** high-leverage areas, thin areas, likely migration cost, and future constraints.

### Fallback: Single-Agent Mode

If delegation is unavailable, produce the three designs sequentially in one session under clearly separate headings. Preserve the separate constraints and output format; do not blend alternatives before comparison.

## 3. Present and Compare

Present each design separately, then compare them using a consistent table before making a recommendation:

| Criterion | Design A | Design B | Design C |
|---|---|---|---|
| Entry points and caller obligations | | | |
| Required configuration and performance facts | | | |
| Behaviour hidden behind the seam | | | |
| Dependency ports and adapters | | | |
| Seam placement | | | |
| Depth / leverage | | | |
| Change locality | | | |
| Test surface | | | |
| Caller and test migration cost | | | |
| Principal risk or thin area | | | |

Then make an opinionated recommendation. Prefer the design that keeps caller obligations smallest while preserving necessary behaviours, concentrates change locally, and puts the seam where policy changes together.

A hybrid is acceptable only when it preserves or reduces the best individual design’s interface burden. A hybrid that accumulates entry points or options from every alternative is a shallow module in disguise.

After the decision, hand the chosen interface to `writing-plans`; do not use the comparison as a pretext to begin an unapproved refactor.
