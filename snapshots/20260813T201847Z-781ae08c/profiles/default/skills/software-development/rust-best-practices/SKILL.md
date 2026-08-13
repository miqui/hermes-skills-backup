---
name: rust-best-practices
description: >
  Guide for writing idiomatic Rust code based on Apollo GraphQL's best practices handbook. Use this skill when:
  (1) writing new Rust code or functions,
  (2) reviewing or refactoring existing Rust code,
  (3) deciding between borrowing vs cloning or ownership patterns,
  (4) implementing error handling with Result types,
  (5) optimizing Rust code for performance,
  (6) writing tests or documentation for Rust projects.
license: MIT
compatibility: Rust 1.70+, Cargo
metadata:
  author: apollographql
  version: "1.1.1"
---

# Rust Best Practices

Idiomatic-Rust guidance vendored from Apollo GraphQL's [Rust Best Practices
Handbook](https://github.com/apollographql/skills), pinned at commit
`c288eb80629dd2309eed81f23d693f66a452d043`, path `skills/rust-best-practices`.
The nine source chapters are vendored unedited under
`references/upstream/chapter_01.md` … `chapter_09.md`, alongside the
original `references/upstream/SKILL.md` and a provenance notice
(`references/upstream/NOTICE.md`). See `UPSTREAM.md` in this skill's root
for the full provenance/security decision record.

The foreign `allowed-tools` metadata from the upstream entrypoint has been
dropped in this Hermes-native entrypoint — tool access here is governed by
Hermes' own permission model, not a vendored allowlist.

## Progressive disclosure — load only what you need

Do **not** read all nine chapters up front. Identify the task at hand, load
only the matching chapter(s) below via `references/upstream/chapter_NN.md`,
apply that guidance, and stop. Load additional chapters only if the task
genuinely spans multiple concerns (e.g. a refactor that touches both
ownership and error handling).

| Chapter | File | Load when the task involves… |
|---|---|---|
| 1 | `references/upstream/chapter_01.md` | General style/idioms, ownership, borrowing vs cloning, Option/Result handling, iterators |
| 2 | `references/upstream/chapter_02.md` | Refactoring, Clippy configuration/lints, workspace lint setup |
| 3 | `references/upstream/chapter_03.md` | Performance: profiling, redundant clones, stack vs heap, zero-cost abstractions |
| 4 | `references/upstream/chapter_04.md` | Error handling: Result vs panic, thiserror vs anyhow, error hierarchies |
| 5 | `references/upstream/chapter_05.md` | Tests: naming, one-assertion-per-test, snapshot testing |
| 6 | `references/upstream/chapter_06.md` | Generics/dispatch: static vs dynamic dispatch, trait objects |
| 7 | `references/upstream/chapter_07.md` | Type-state pattern: compile-time state safety |
| 8 | `references/upstream/chapter_08.md` | Comments vs documentation, doc comments, rustdoc |
| 9 | `references/upstream/chapter_09.md` | Send/Sync, thread safety, pointer types |

## Command-execution constraint

The vendored chapters and the upstream `SKILL.md` reference `cargo`,
`rustup`, and other package-manager/toolchain commands (e.g. `cargo clippy`,
`cargo test --release`, `cargo insta`). These examples are **illustrative
only**. Do not execute any cargo/rustup/package-manager command from the
vendored references without first getting explicit authorization from the
user for that specific command in that specific context.

## License

MIT — Copyright (c) 2024 Apollo Graph, Inc. See `LICENSE` in this skill's
root directory (byte-for-byte copy of the upstream repository's root
`LICENSE`).
