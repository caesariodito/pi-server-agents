# .NET and C#

Apply only rules supported by solution, project, configuration, and code evidence.

## Evidence

Inspect solution files, `*.csproj`, `Directory.Build.*`, `Directory.Packages.props`, `global.json`, `.editorconfig`, test projects, analyzers, nullable settings, target frameworks, and CI.

## Guidance candidates

- Name exact `dotnet` commands and required SDK from repository configuration.
- Preserve nullable-reference and analyzer policy; fix warnings in changed code rather than suppressing them without reason.
- Keep domain, application, infrastructure, and presentation dependencies aligned with existing project references.
- Use dependency injection and configuration patterns already present; avoid service locators and global mutable state.
- Keep async paths async, pass cancellation tokens where established, and avoid sync-over-async.
- Preserve public API compatibility unless breakage is approved.
- Use existing test framework, assertion style, fixtures, and project placement.
- Handle disposal and transaction ownership explicitly where resources or data integrity are involved.
- Do not edit generated files, build output, or generated migrations by hand unless repository workflow requires it.

Include only specific rules that change likely agent behavior in this repository.
