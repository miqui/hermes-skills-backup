---
name: code-performance-engineering
description: "Use when diagnosing, benchmarking, profiling, or improving code performance across languages and runtimes. Guides evidence-first performance work: define performance goals, reason about Big-O complexity where applicable, reproduce workloads, measure baselines, identify bottlenecks, optimize safely, and verify regressions without premature or cosmetic tuning."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [performance, profiling, benchmarking, optimization, complexity, big-o, latency, throughput, memory, cpu, tail-latency]
    related_skills: [systematic-debugging, test-driven-development, requesting-code-review, python-performance-optimization, golang-troubleshooting, node-backend, spring-boot-engineer, grpc-api, graphql-api]
---

# Code Performance Engineering

## Overview

Use this skill for evidence-first performance work across languages, runtimes, and application styles. Performance engineering is not just "make it faster"; it is a disciplined loop: define the performance question, reproduce a representative workload, capture a baseline, identify the actual bottleneck, choose the smallest high-leverage change, and verify the result without breaking correctness or maintainability.

Big-O complexity belongs in this workflow whenever runtime or memory growth depends on input size, collection size, graph size, query fan-out, batching, recursion depth, or data-structure choice. Complexity analysis explains how work scales; profiling and benchmarks prove what matters in the real workload.

For Python-specific profiler commands and idioms, also load `python-performance-optimization`. For Go slowdowns, crashes, deadlocks, race conditions, or profiling inside a broader debugging task, also load `golang-troubleshooting`. For backend/API performance, pair with the implementation skill for the runtime or protocol, such as `node-backend`, `spring-boot-engineer`, `grpc-api`, or `graphql-api`.

## When to Use

Use this skill when the task involves:

- Diagnosing slow code, high latency, low throughput, or high resource use.
- Reviewing or implementing a change that claims to improve performance.
- Designing a benchmark or interpreting benchmark output.
- Choosing between algorithmic, data-structure, caching, batching, database, I/O, concurrency, or memory optimizations.
- Investigating performance regressions in a pull request or release.
- Adding performance guardrails such as benchmarks, regression tests, dashboards, or SLO checks.
- Explaining time or space complexity with Big-O notation.

Do not use this skill as the only guide when:

- The issue is general correctness debugging with no performance symptom; use `systematic-debugging` first.
- The task is purely Python implementation-level profiling; also load `python-performance-optimization`.
- The task is cloud cost governance rather than code-level performance.
- The user asks for infrastructure load-testing design only; this skill can help with workload realism, but a dedicated load-testing plan may be needed.

## Performance Workflow

### 1. Define the performance question

Turn vague complaints into measurable questions:

- What is slow: endpoint, job, CLI command, render path, query, startup, build, test, or loop?
- What metric matters most: latency, throughput, CPU, memory, allocations, I/O, tail latency, cost, or energy?
- What is the acceptable target: p95 under 200 ms, 2x throughput, 50% less memory, no regression over baseline?
- What workload represents reality: input sizes, concurrency, data distribution, cache state, warm/cold start, network location?

Avoid optimizing until the target and workload are explicit.

### 2. Preserve correctness first

Before changing performance-sensitive code:

- Run or add correctness tests around the behavior being optimized.
- Capture edge cases for empty, small, large, skewed, duplicate, missing, and malformed inputs.
- For concurrency changes, include cancellation, timeout, race, ordering, and shutdown scenarios.
- For cache changes, define invalidation, freshness, capacity, and error behavior.

A faster wrong answer is a regression.

### 3. Establish a baseline

Capture enough data to compare before and after:

- Current metric values and variance across repeated runs.
- Input sizes and workload parameters.
- Machine/runtime versions and relevant flags.
- Cache state, warmup strategy, and data fixtures.
- Profiling traces, flamegraphs, query plans, allocation summaries, or logs.

If the baseline cannot be reproduced, treat the optimization claim as weak evidence.

### 4. Analyze Big-O where applicable

Use complexity analysis when performance depends on scale. Identify dominant variables and likely growth rates before reaching for micro-optimizations.

Ask:

- What grows: number of items, records, queries, graph nodes, edges, files, tokens, bytes, requests, or users?
- Are there nested loops, repeated scans, repeated sorts, hidden copies, recursive traversals, or N+1 calls?
- Can a data-structure or algorithm change reduce the growth rate?
- Does the asymptotic improvement matter for realistic input sizes?

### 5. Profile before changing code

Use the profiler that matches the suspected bottleneck:

- CPU sampling or tracing for compute-bound hot paths.
- Allocation and heap profiling for memory pressure or GC overhead.
- Lock/contention profiling for concurrency stalls.
- Query plans and database metrics for database-bound paths.
- Distributed traces for service-to-service latency and fan-out.
- System metrics for I/O wait, disk, network, CPU saturation, and memory limits.

Prefer sampling profilers for production-like systems because they reduce observer effect. Use instrumentation when you need exact timings around known boundaries.

### 6. Optimize the highest-leverage bottleneck

Choose the smallest change likely to move the target metric:

- Fix algorithmic complexity before constant-factor tuning when scale is the issue.
- Batch, join, or preload when repeated remote/database calls dominate.
- Reduce allocations, copies, serialization, or materialization when memory/GC dominates.
- Bound concurrency and remove contention when queues, locks, or resource pools dominate.
- Cache only when the value is reused, invalidation is understood, and memory trade-offs are acceptable.
- Use lower-level/runtime-specific optimizations only after clearer structural fixes are exhausted.

### 7. Verify improvement and trade-offs

After the change:

- Re-run correctness tests.
- Re-run the same benchmark or workload as the baseline.
- Compare target metrics, variance, p95/p99, and resource side effects.
- Check memory, readability, operational risk, and failure modes.
- Add a benchmark or regression guard if the path is important and stable enough.

## Metric Taxonomy

| Metric | What it tells you | Typical evidence |
|---|---|---|
| Latency | Time for one operation/request | p50/p95/p99 timings, traces |
| Throughput | Work completed per time unit | requests/sec, jobs/min, rows/sec |
| CPU time | Compute consumed | profiler samples, CPU utilization |
| Wall time | User-observed elapsed time | timers, traces, benchmark output |
| Memory footprint | Resident or heap usage | heap profile, RSS, peak memory |
| Allocation rate | Object churn and GC pressure | allocation profile, GC logs |
| I/O wait | Time blocked on disk/network | system metrics, traces |
| Database time | Query or transaction cost | query plans, DB metrics, slow query logs |
| Contention | Waiting for locks/resources | mutex profile, queue depth, pool wait |
| Tail latency | Worst user-visible delays | p95/p99/p999, timeout counts |
| Cold start | First-run or startup delay | startup trace, import/init timings |

Choose metrics that match the user-visible or system-visible symptom.

## Big-O and Algorithmic Complexity

Big-O describes how time or space grows as input size grows. Use it to find scalability risks and to compare algorithmic choices. Do not use it as proof that code is faster in the real workload; constants, memory layout, cache locality, runtime overhead, database indexes, network latency, and contention can dominate.

### Define variables explicitly

Name the variables before writing complexity claims:

| Symbol | Meaning example |
|---|---|
| `n` | number of input items |
| `m` | number of related records or secondary collection size |
| `k` | batch size, page size, top-K count, or selected item count |
| `d` | depth of tree or recursive traversal |
| `V` | graph vertices/nodes |
| `E` | graph edges |
| `q` | number of queries, remote calls, or fan-out requests |
| `b` | bytes processed |

Use separate variables for independent dimensions. A nested loop over `users` and `orders` is `O(n*m)`, not automatically `O(n^2)` unless both collections scale together.

### Complexity checklist

- Identify the hot path and the input-size variables.
- Estimate time complexity and space complexity.
- Look for nested loops, repeated scans, hidden copies, sorting, recursion, and fan-out.
- Inspect library calls used inside loops; they may hide scans, allocations, serialization, or remote work.
- Check whether a data-structure change improves complexity.
- Confirm the asymptotic improvement matters for expected and worst-case input sizes.
- Validate the complexity claim with representative benchmark or profiling evidence.

### Common complexity patterns

| Pattern | Typical complexity | Watch for |
|---|---:|---|
| Single pass over a collection | `O(n)` | Usually fine unless repeated often |
| Nested loop over the same collection | `O(n^2)` | Candidate for map/set/index |
| Nested loop over two collections | `O(n*m)` | Candidate for precomputed lookup |
| Hash lookup per item | `O(n)` average total | Memory growth and hash behavior |
| Membership check in list inside loop | `O(n*m)` or `O(n^2)` | Convert membership side to set |
| Sorting | `O(n log n)` | Avoid repeated sorts inside loops |
| Top-K with heap | `O(n log k)` | Often better than full sort for small `k` |
| Binary search | `O(log n)` | Requires sorted/indexed data |
| Tree traversal | `O(n)` | Space can be `O(d)` recursion depth |
| Graph BFS/DFS | `O(V + E)` | Track visited set and memory |
| Dynamic programming table | often `O(n*m)` | Space may be reducible |
| N+1 database calls | `O(n)` remote calls | Latency impact can dwarf CPU cost |
| Cartesian product | `O(n*m)` | Often accidental and dangerous |
| Full copy per iteration | often `O(n^2)` total | Hidden in append/concat/slice patterns |

### Big-O vs real-world performance

Use Big-O to answer:

- Will this get worse as input grows?
- Is this algorithm structurally inefficient?
- Can a better data structure reduce the growth rate?
- Is the current benchmark too small to expose the real issue?

Use profiling and benchmarking to answer:

- Is this actually the bottleneck?
- How much faster did it get?
- Did p95 or p99 latency improve?
- Did memory, readability, or correctness regress?

## Benchmark Design

A benchmark is only useful if it predicts the real workload or isolates a specific question.

### Benchmark checklist

- Use representative input sizes, shapes, and distributions.
- Include both typical and worst-case-ish data where relevant.
- Warm up runtimes with JITs, caches, connection pools, imports, or lazy initialization.
- Run enough iterations to estimate variance.
- Report median and tail metrics, not only best result.
- Isolate external noise when possible: network, disk, background jobs, debug logging.
- Avoid measuring setup/teardown unless setup cost is the target.
- Keep correctness assertions in or near the benchmark so optimized code cannot cheat.
- Compare against the baseline using the same environment and workload.

### Microbenchmarks vs macrobenchmarks

Use microbenchmarks for isolated algorithm or function questions. Use macrobenchmarks for user-visible behavior such as endpoint latency, job throughput, startup time, or end-to-end processing.

Microbenchmarks can mislead when they ignore I/O, serialization, database plans, allocation behavior, concurrency, or cache state. Macrobenchmarks can mislead when they are too noisy to identify a bottleneck. Prefer both when the change is important: microbenchmark the local improvement, then macrobenchmark the real outcome.

## Profiling Strategy

Start broad, then narrow:

1. Confirm the symptom with metrics or timings.
2. Identify whether the path is CPU-bound, memory-bound, I/O-bound, DB-bound, lock-bound, or fan-out-bound.
3. Capture the matching profile or trace.
4. Optimize the largest relevant contributor.
5. Re-profile to confirm the bottleneck moved or shrank.

### Profiler selection

| Suspected bottleneck | Evidence to collect |
|---|---|
| CPU-bound hot code | CPU profile, flamegraph, sampled stacks |
| Memory or GC pressure | heap profile, allocation profile, GC logs |
| Database latency | query plan, slow query log, index stats, DB timings |
| Network/service fan-out | distributed trace, per-call timings, retry counts |
| Lock contention | mutex/block profile, queue depths, wait time |
| Disk/file I/O | system metrics, file operation timings, buffering behavior |
| Startup/cold path | import/init trace, dependency load timings |

## Optimization Decision Tree

1. **If complexity is worse than necessary, fix algorithm or data structure first.**
   - `O(n^2)` repeated scans -> `O(n)` with a lookup table.
   - `O(n*m)` joins in application code -> indexed lookup, database join, or batched query.
   - `O(n log n)` full sort for top results -> `O(n log k)` heap/top-K when `k` is small.
   - Repeated `O(n)` membership checks -> average `O(1)` set/dict lookup.
   - N+1 remote calls -> batch, join, preload, or cache.

2. **If complexity is appropriate, profile constant factors and runtime behavior.**
   - Reduce allocations and copies.
   - Avoid unnecessary serialization/deserialization.
   - Move invariant work out of loops.
   - Stream large data instead of materializing it.
   - Use efficient library/runtime primitives where readability remains acceptable.

3. **If I/O or remote calls dominate, reduce round trips and wait time.**
   - Batch requests.
   - Use connection pooling.
   - Parallelize only up to downstream capacity.
   - Add timeouts, cancellation, and backpressure.
   - Cache only when invalidation and capacity are clear.

4. **If concurrency dominates, remove contention before adding workers.**
   - Bound queues and goroutines/threads/tasks.
   - Avoid shared locks in hot paths.
   - Separate CPU-bound and I/O-bound pools.
   - Measure queue time and resource-pool wait.

5. **If database work dominates, inspect query shape.**
   - Use query plans rather than guessing.
   - Fix missing indexes, bad predicates, over-fetching, and N+1 access patterns.
   - Prefer set-based operations when appropriate.
   - Validate that indexes improve the real query and do not create unacceptable write overhead.

## Safe Performance Change Patterns

- Keep the simple implementation as a reference in tests when possible.
- Add benchmarks next to the code if the project supports stable benchmarking.
- Document why the optimization exists and what trade-off it makes.
- Prefer structural improvements over clever micro-optimizations.
- Make caching explicit: key, value, invalidation, TTL, capacity, and failure behavior.
- Feature-flag risky algorithm rewrites or rollout-sensitive changes.
- Preserve observability so future regressions can be diagnosed.
- Avoid changing multiple performance dimensions at once unless necessary; otherwise attribution becomes hard.

## Code Review Checklist

When reviewing performance-sensitive code, check:

- [ ] The performance problem and target metric are stated.
- [ ] Baseline numbers or profiler evidence exist.
- [ ] The workload is representative of real use.
- [ ] Time and space complexity are estimated where input growth matters.
- [ ] Complexity variables are named clearly: `n`, `m`, `k`, `V`, `E`, `q`, etc.
- [ ] The code avoids accidental `O(n^2)` or `O(n*m)` behavior.
- [ ] Sorting, copying, serialization, database calls, and remote calls inside loops are justified.
- [ ] Any claimed complexity improvement is backed by representative benchmarks or profiling.
- [ ] Correctness tests cover the optimized path and edge cases.
- [ ] Tail latency, memory use, and operational risk are considered, not only average speed.
- [ ] The optimized code remains readable enough for future maintenance.

## Common Pitfalls

1. **Optimizing without a baseline.** You cannot prove improvement without before/after evidence.

2. **Using Big-O as proof of speed.** Better asymptotic complexity may still be slower for small inputs or worse memory locality. Measure the real workload.

3. **Ignoring algorithmic complexity.** Micro-optimizing an `O(n^2)` hot path rarely beats changing it to `O(n)` or `O(n log n)`.

4. **Benchmarking unrealistic inputs.** Tiny, uniform, warm-cache inputs often hide the real bottleneck.

5. **Reporting best-case timings.** Use repeated runs and include variance or distribution; p95/p99 often matter more than fastest run.

6. **Improving mean latency while worsening tail latency.** Queues, locks, retries, and GC can make p99 worse even when averages improve.

7. **Adding caches without an invalidation strategy.** Cache bugs can become correctness bugs, memory leaks, or stale-data incidents.

8. **Treating database or network calls as cheap loop operations.** N+1 calls are often worse than their apparent CPU complexity.

9. **Parallelizing into a bottleneck.** More workers can increase contention, saturate downstream services, and worsen tail latency.

10. **Trading clarity for tiny gains.** Clever code needs strong evidence and tests; otherwise it becomes future performance debt.

11. **Missing hidden copies and allocations.** Slicing, concatenation, serialization, ORM accessors, and library helpers can hide expensive work.

12. **Changing too many things at once.** If performance improves or regresses, attribution becomes unclear.

## Verification Checklist

Before calling a performance task complete:

- [ ] The target metric and workload are defined.
- [ ] Correctness tests pass before and after the change.
- [ ] Baseline performance was captured.
- [ ] Big-O time/space complexity was analyzed where scale matters.
- [ ] A profiler, trace, query plan, or benchmark identified the bottleneck.
- [ ] The optimization targets the measured bottleneck.
- [ ] Before/after results show improvement on the representative workload.
- [ ] Memory, CPU, tail latency, I/O, and operational trade-offs were checked.
- [ ] Regression guardrails were added or explicitly deferred with rationale.
- [ ] The final explanation includes evidence, trade-offs, and any remaining risks.
