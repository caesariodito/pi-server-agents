# TypeScript and JavaScript

Apply only rules supported by repository configuration and code.

## Evidence

Inspect `package.json`, active lockfile, `tsconfig*.json`, lint and formatter config, test config, package-manager workspace files, module type, build config, and CI.

## Guidance candidates

- Name package manager and exact repository scripts; use scripts instead of invoking hidden tool internals.
- Preserve ESM/CommonJS boundary and configured module resolution.
- Keep TypeScript strictness; avoid `any`, unchecked casts, and non-null assertions unless repository convention and local proof justify them.
- Validate external JSON, environment values, request data, and persistence data at runtime; TypeScript types do not validate runtime input.
- Preserve public export boundaries and avoid deep imports across packages.
- Use existing async and error-handling conventions; do not leave floating promises or swallow actionable errors.
- Place tests according to current layout and use current runner, fixtures, and naming.
- Do not edit generated output, lockfiles through hand changes, or files owned by code generation.

Include only specific rules that change likely agent behavior in this repository.
