---
name: java-jvm-performance-debugging
description: "Use when debugging Java/JVM performance and memory issues."
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [java, jvm, performance, gc, jfr, jcmd, heap-dump, thread-dump, memory-leak, metaspace, native-memory, jmh, virtual-threads]
    related_skills: [code-performance-engineering, java-coding-standards, systematic-debugging, spring-boot-engineer]
---

# Java/JVM Performance Debugging

## Overview & Boundaries

Evidence-first diagnosis of JVM runtime problems: GC pressure, memory retention/leaks,
native/off-heap growth, CPU hotspots, tail latency, lock contention, virtual-thread
pinning. Assumes current-LTS-or-newer Java (17/21+); commands/behavior vary across JDK
builds/vendors (Temurin, Oracle, Corretto) — verify, don't assume.

**In scope:** JVM/process diagnosis (GC, heap, threads, classloading, native memory,
JIT/CPU); interpreting JFR/GC-log/thread-dump/heap-dump evidence; framing tuning as
testable hypotheses. **Hand off:** style/records → `java-coding-standards`; general
benchmark methodology/Big-O → `code-performance-engineering`; non-perf functional bugs
→ `systematic-debugging`; Spring Boot config → `spring-boot-engineer` (this only
inspects the JVM/DB-driver boundary).

**GraalVM caveat:** none of the HotSpot workflow below (jcmd subsystem, JFR event set,
GC-log format, heap/thread-dump tools) applies unqualified to a `native-image` binary —
much smaller surface, no classic `jcmd`/`jstack`/`jmap`. Confirm HotSpot before proceeding.

## Activation Triggers

"Slow / high latency / times out"; `OutOfMemoryError`, Metaspace growth, "GC overhead
limit exceeded", rising RSS; requests for heap/thread dump, JFR/jcmd/jstack/jmap, GC
logs; CPU pinned at 100%; JMH results implausible vs. prod; container OOM-kill or
cgroup mismatch; virtual-thread stalls/pinning. Not for compile/build errors or
functional bugs with no perf/memory dimension.

## Ground Truth First

Tool availability, flags, and JFR event sets vary across JDK 17/21/25 and vendors.
**Never hardcode a command list as universal.** Run `jcmd <pid> help` (and
`jcmd <pid> help <command>` for specifics) against the live target first; treat that as
ground truth for this exact build.

Diagnostics must run **inside the target's PID/container namespace** — `jps`, `jcmd`,
`jstack`, `jmap` can't see across boundaries; `exec` into the target's container (as its
OS user) first, or a bare host-side `jps -l` silently shows nothing/the wrong process.
Confirm detected heap/CPU ergonomics match actual container/cgroup limits
(`-XX:+UseContainerSupport` is default-on but can misdetect) — mismatch oversizes
heaps, causes OOM-kills.

## Stop-the-Line Severity/Safety Triage

Classify before running anything — gates which commands are permissible.

| Signal | Class | Action |
|---|---|---|
| Prod, live traffic | High-impact | JFR + low-impact `jcmd` sampling only first; avoid dumps/histograms/forced GC unless outage-level; state overhead/pause risk before running |
| Staging/repro | Low-impact | Full toolkit available — still baseline first |
| Corruption/security incident alongside perf symptom | Stop | Don't tune; hand off |
| Pause-inducing (heap dump, `GC.class_histogram`, forced GC) | High-impact | State expected pause/duration; get explicit go-ahead in prod |
| Dump/recording holds customer data | Data-sensitive | See Data/PII section before sharing |

Never run destructive/pause-inducing commands on live production without explicit
confirmation. Ask before going beyond read-only JFR/jcmd if environment class is unclear.

## Evidence-to-Change Workflow

1. State the symptom with numbers (p99 latency, growth rate), not adjectives.
2. Capture baseline before touching anything: `java -version`; `jcmd <pid>`
   `VM.flags`/`VM.command_line`; `jcmd <pid> help` (ground truth); GC config (`-Xlog:gc*`
   or `VM.info | grep -i heap`); container/cgroup limits; workload shape (rate, payload,
   concurrency, steady vs. bursty); numeric baseline (p50/p95/p99, throughput, GC pause
   time/frequency, heap trend).
3. Pick the least-invasive diagnostic that can confirm/rule out a hypothesis.
4. Form a hypothesis from evidence, not intuition.
5. Make the smallest change that tests it.
6. Re-measure under the same workload/environment; compare to baseline.
7. Roll back if it doesn't help or regresses something else — never leave an unverified
   change "because it seemed fine."

## JVM and Container Discovery

```
jps -l ; jcmd <pid> help ; jcmd <pid> VM.version ; jcmd <pid> VM.flags
cat /sys/fs/cgroup/memory.max   # cgroup v2 memory limit
nproc                           # CPUs as seen by the container
```
If tools can't see the target, exec into its container/namespace (as the JVM's OS user)
and retry, or use `ps` to find the PID from inside.

## Symptom → Evidence Matrix

| Symptom | First evidence | Tool |
|---|---|---|
| High/rising latency | CPU flame graph + GC log overlay | JFR, `-Xlog:gc*` |
| Long/frequent GC pauses | Pause times/cause | GC logging, `jstat -gcutil` |
| Heap unbounded growth | Old-gen occupancy trend | GC log, JFR `GCHeapSummary` |
| Suspected retention leak | Histogram trend, then dump | `GC.class_histogram` (high-impact), heap dump |
| RSS rises, heap flat | Native/off-heap breakdown | NMT (needs launch-time flag) |
| Metaspace OOM / class growth | Loaded-class trend | `VM.classloader_stats`, histogram |
| Hangs/throughput drop | Thread BLOCKED/WAITING | `jcmd <pid> Thread.print` |
| CPU pinned at 100% | Method-level sampling | JFR execution samples |
| Virtual-thread stalls | Carrier pinning | JFR `jdk.VirtualThreadPinned` |
| JMH mismatches prod | Methodology audit | See JMH section |

## Safe-First Diagnostic Commands

`jcmd` is the primary, maintained tool — prefer over `jstack`/`jmap`, which Oracle marks
**"experimental and unsupported... might not be available in future releases,"** used
only as legacy fallbacks when no `jcmd` equivalent exists. Order below is increasing
invasiveness; confirm syntax with `jcmd <pid> help <command>` first — flags vary by build.

**1. JFR** (JDK 11+, low-impact): overhead on `default.jfc` is generally low but not
fixed/guaranteed — Oracle documents it rising if event settings are modified; never
promise a specific fixed percentage.
```
jcmd <pid> JFR.check
jcmd <pid> JFR.start name=diag duration=120s filename=/tmp/diag.jfr settings=default
jcmd <pid> JFR.dump name=diag filename=/tmp/diag-snapshot.jfr   # dump without stopping
jcmd <pid> JFR.stop name=diag
jfr print --events jdk.GCHeapSummary,jdk.ExecutionSample /tmp/diag.jfr | less
```
`profile.jfc` captures more detail at meaningfully higher cost — short targeted windows
in prod, not continuous; custom event config can push overhead beyond either preset.

**2. jstat / VM.flags / VM.log (low-impact):**
```
jstat -gcutil <pid> 1000 10
jcmd <pid> VM.flags
jcmd <pid> VM.log list               # discover current runtime logging config
```
Prefer enabling GC logs (`-Xlog:gc*`) at **startup** so history predates incidents;
treat `VM.log` changes as deliberate, not routine.

**3. Thread dumps (medium impact, low frequency):**
```
jcmd <pid> Thread.print -l           # -l adds lock info
```
Prefer over `jstack`/`kill -3`. Take 3-5 dumps seconds apart to distinguish a stall from
a deadlock; avoid tight-loop use in prod.

**4. Class histograms (high-impact, not routine, potentially disruptive):**
```
jcmd <pid> GC.class_histogram
```
Full heap scan, **can pause the app** (Oracle: "Impact: High"). Check
`jcmd <pid> help GC.class_histogram` for actual options rather than inventing flags.
Only after cheaper evidence points at retention; explicit confirmation required in prod.

**5. Heap dumps (high-impact, production-impacting, confirm before running):**
```
jcmd <pid> GC.heap_dump /tmp/heap.hprof
```
Can pause/safepoint the JVM (duration scales with live heap, not fixed — do not claim
zero pause); file may hold sensitive data. By default the command **requests a full GC**
before dumping (Oracle: "Impact: High ... Request a full GC unless the -all option is
specified"); pass `-all` to suppress that GC request and include unreachable objects
instead. Verify against `jcmd <pid> help GC.heap_dump` for the exact build, since flag
names/availability differ by version. Only after cheaper evidence points at retention,
only with explicit prod confirmation.
`jmap -dump:live,...` is a legacy fallback only (Oracle's "experimental/unsupported");
prefer `jcmd`. State the pause estimate, get explicit go-ahead, prefer a canary/replica.

## JFR Event Interpretation

`jdk.GCHeapSummary`/`GCPhasePause`: occupancy *after old-gen collections* vs. sawtooth.
`jdk.ExecutionSample`/`NativeMethodSample`: CPU stacks → flame graph.
`jdk.ObjectAllocationSample` (17+): allocation-site sampling for churn.
`jdk.ThreadPark`/lock events: contention/parking vs. latency spikes.
`jdk.VirtualThreadPinned`: carrier pinned by `synchronized`/native calls. Cross-reference
JFR timestamps against GC logs/dashboards; one source rarely suffices.

## Memory Investigation Flows

**Allocation churn**: `-Xlog:gc*` at startup; check young-GC frequency/promotion rate;
JFR allocation sampling finds hot sites; pool only after confirming the site.

**Heap retention/leak**: histogram at two points separated by real workload (each run
high-impact); diff live-object counts per class. Unbounded growth → heap dump, then
dominator/retained-size tree (Eclipse MAT, JDK Mission Control) for the GC root.

**Classloader/Metaspace**: `jcmd <pid> VM.classloader_stats` (9+) or histogram trend;
common causes: proxy/bytecode-gen libs, hot-reload, classloaders never released after
redeploy. A *stable* class count with Metaspace OOM usually means `-XX:MaxMetaspaceSize`
too low, not a leak.

**Direct/native memory**: RSS rising, heap flat (`GC.heap_info`) → off-heap
(DirectByteBuffers, JNI, mmap). **NMT requires `-XX:NativeMemoryTracking=summary`
(or `detail`) at JVM startup — cannot be enabled retroactively**; `jcmd` reports
tracking disabled otherwise; restarting to add it is a real intervention.
```
jcmd <pid> VM.native_memory baseline        # required before any diff
jcmd <pid> VM.native_memory summary.diff    # compare current state to the baseline
jcmd <pid> VM.native_memory summary         # point-in-time, no baseline needed
```
`summary.diff` is meaningless without a prior `baseline` in the same session. `detail`
has materially higher overhead than `summary` — reserve for short windows.

## CPU, Latency, Lock, Virtual-Thread Diagnostics

CPU hotspot: JFR `ExecutionSample` → flame graph; distinguish hot path from allocation
driving GC CPU. Lock contention: JFR monitor events or thread dumps with many `BLOCKED`
on one monitor — find the owner, not just waiters. Virtual threads (21+): pinning from
`synchronized`/native frames blocks unmounting — check `VirtualThreadPinned`; fix is
usually `ReentrantLock`, not disabling virtual threads. Tail latency: correlate GC
pauses/thread dumps with the spike; don't assert a generic threshold without the app's
own SLO.

## JMH Benchmark Correctness

Recommend running JMH as an **isolated executable artifact** — e.g. via
`jmh-java-benchmark-archetype`, or a build-plugin-supported benchmark artifact (shade,
assembly, or similar) — rather than `jmh-core` bolted loosely onto an existing module.
Any controlled JMH runner is acceptable as long as it preserves the full harness
lifecycle (fork isolation, warmup, iteration, measurement, teardown) unmodified; what's
rejected is an IDE run or a hand-timed loop (JMH README calls IDE execution unreliable
due to JIT/inlining variance). Confirm: sufficient `@Warmup` for JIT steady state;
`@Fork` > 1; dead-code elimination prevented (`Blackhole`-consumed results); constant
folding avoided (realistic varying inputs); noisy CI/thermal throttling noted. A "20%
improvement" from one fork/iteration without a proper controlled JMH harness run is not
evidence.

## Spring/JPA/Database Boundary

JVM-level only: confirm GC/CPU-bound vs. I/O/query-bound first (JFR socket/file-I/O
events or query-timing logs). Pool exhaustion shows as threads `WAITING` on acquisition
— sizing/config, hand to `spring-boot-engineer`. N+1/Hibernate session tuning aren't
JVM-memory problems though they can resemble churn — use this skill only to rule
GC/heap in or out.

## Decision Framework for Tuning and Rollback

State the evidence-backed problem (not "try G1 tuning") → state the mechanism → define
success metric/threshold before applying → canary/staging first when possible →
re-measure the same workload vs. baseline → roll back if no improvement or a regression
elsewhere (e.g. lower pause, higher CPU) — never keep a change on "feels faster" →
document before/after numbers and exact flags changed.

## Data/PII Protection and Production Safety

Heap dumps (and, less, thread dumps/JFR) can hold live app data — PII, credentials,
session tokens, local variables. Restrict file permissions, don't paste raw contents
into shared channels, delete after analysis unless retention required. Never upload a
dump externally without explicit permission — analyze locally (Eclipse MAT, JDK Mission
Control). Share summaries, not raw artifacts. Every high-impact command requires
disclosed pause/overhead **and** explicit human confirmation before running against
anything production-adjacent — an approval gate, not a courtesy notice.

## Common Pitfalls

1. Running class histogram/heap dump before a cheap GC-log/JFR trend, or as routine
   rather than a stated, confirmed, high-impact action.
2. Reading heap-used at a random moment instead of after old-gen GCs — inflates growth.
3. Treating one JMH run, ad hoc timing, or an IDE run as proof instead of a proper
   controlled JMH harness run with warmup/forks.
4. Assuming NMT can be enabled live without the startup flag, or skipping `baseline`
   before `summary.diff`.
5. Blaming GC for latency without checking CPU hotspots/I/O first; disabling virtual
   threads wholesale instead of fixing the pinning `synchronized`.
6. Presenting `jstack`/`jmap` as stable primaries instead of the documented
   experimental/unsupported legacy fallbacks.
7. Hardcoding a fixed "jcmd command list" instead of running `jcmd <pid> help` live, or
   running tools from outside the target's namespace and concluding "no JVM found."
8. Declaring victory after tuning without re-measuring against the baseline, or
   treating a container OOM-kill as an in-JVM leak without checking limit detection.
9. Sharing/persisting a dump without weighing sensitive-data exposure, or applying
   this HotSpot workflow unmodified to a GraalVM native-image binary.
10. Asserting a fixed JFR overhead percentage instead of noting it varies with event
    settings and load.

## Verification Checklist

- [ ] Symptom stated with concrete numbers, not adjectives; HotSpot (not native-image) confirmed
- [ ] Environment classified (high/low-impact) before any command
- [ ] `jcmd <pid> help` run against the live target as ground truth for available commands
- [ ] Diagnostic tools run inside the target's PID/container namespace
- [ ] Baseline captured (version/flags, container limits, workload, metrics) before changes
- [ ] Least-invasive diagnostic tried first (`jcmd`/JFR before dumps); `GC.class_histogram`/
      heap dumps justified by prior cheaper evidence, not routine
- [ ] High-impact/data-sensitive commands had impact stated and were explicitly confirmed
- [ ] NMT startup flag confirmed enabled, and a `baseline` established before `summary.diff`
- [ ] Hypothesis is evidence-backed; change is the smallest one that tests it
- [ ] Re-measurement used the same workload/environment as the baseline
- [ ] Non-improvement or regression triggers rollback, not persistence "just in case"
- [ ] Dumps/recordings treated as sensitive; not shared/persisted beyond necessity
- [ ] JMH claims verified via a controlled JMH harness run with warmup, `@Fork` > 1,
      and `Blackhole`-consumed results — not an IDE run or ad hoc timing
