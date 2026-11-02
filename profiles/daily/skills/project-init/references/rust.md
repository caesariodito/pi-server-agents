# Rust

Apply only rules supported by workspace configuration and code.

## Evidence

Inspect `Cargo.toml`, `Cargo.lock`, workspace layout, toolchain files, feature flags, lint config, tests, unsafe code, generated code, and CI.

## Guidance candidates

- Name exact Cargo commands, workspace/package scope, features, and required toolchain.
- Preserve crate boundaries and public API visibility; avoid widening `pub` without need.
- Use repository error types and conversion patterns; keep error context and avoid `unwrap` or `expect` in production paths without proven invariant.
- Prefer borrowing over cloning where clear, but do not trade readability for speculative micro-optimization.
- Keep unsafe code isolated, documented with invariants, and covered by focused checks.
- Preserve async runtime and blocking boundaries; do not block executor threads.
- Follow current unit, integration, fixture, and property-test layout.
- Run formatting, clippy policy, and relevant tests with required features.
- Do not edit generated files, target output, or vendored dependencies by hand.

Include only specific rules that change likely agent behavior in this repository.
