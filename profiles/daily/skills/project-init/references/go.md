# Go

Apply only rules supported by repository configuration and code.

## Evidence

Inspect `go.mod`, `go.work`, package layout, `cmd/`, `internal/`, generated-code directives, linter config, tests, build tags, and CI.

## Guidance candidates

- Name exact `go` commands and any repository wrapper scripts.
- Preserve package boundaries; keep internal packages internal and avoid import cycles.
- Return errors with useful context while preserving inspectable causes through `%w` where appropriate.
- Pass `context.Context` through request-scoped operations according to existing APIs; do not store it in structs without established reason.
- Define interfaces at consumer boundaries only when substitution is needed; prefer concrete types otherwise.
- Protect goroutine lifecycle, channel ownership, cancellation, and shared state.
- Use table-driven tests only where cases benefit; follow current package and external-test style.
- Run formatting and relevant tests; include race checks when concurrency behavior changes and repository supports them.
- Do not edit generated files or vendored dependencies by hand.

Include only specific rules that change likely agent behavior in this repository.
