# Python

Apply only rules supported by repository configuration and code.

## Evidence

Inspect `pyproject.toml`, lockfiles, supported Python versions, package layout, type-checker and linter config, test config, migration tools, entry points, and CI.

## Guidance candidates

- Name exact environment, package-manager, test, lint, format, and type-check commands.
- Preserve package boundaries and import style; do not mutate `sys.path` to bypass structure.
- Add type annotations at established boundaries and satisfy configured type checker.
- Validate external mappings, environment values, request data, and persistence data at runtime.
- Use context managers for owned resources and explicit transaction boundaries for data changes.
- Avoid mutable default arguments, broad exception catches, and silent error suppression.
- Use existing async model consistently; avoid blocking I/O in async paths.
- Follow current test fixtures, markers, naming, and layout.
- Do not edit generated files, virtual environments, lockfiles by hand, or migration history outside repository workflow.

Include only specific rules that change likely agent behavior in this repository.
