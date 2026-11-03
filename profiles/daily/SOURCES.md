# Shared skill dependency

Canonical source: https://github.com/caesariodito/skills

Exact reviewed Git commit and resource selection: ../shared-skills.json. Pi installs this package natively; no vendored daily workflow, personal paths, node_modules, or generated catalogs belong here. Base includes server operations and shared gateway skills. Daily adds coding/review/security workflows.

Review shared source and tests before bumping commit. Preserve canonical licenses/provenance there. Herdr CLI remains installer-managed, while its optional agent skill remains separately reviewed upstream installation; no unversioned redistribution. Audit skill installation does not provision independent agents or OS sandbox controls.

Legacy daily-skills runtime directory is retained but removed from settings discovery. Exact unmodified former gateway skills move into runtime retired-skills backups; custom versions block migration for manual merge. Unknown files and private state remain untouched. Repository Git history retains former vendored snapshots/binaries/catalogs for recovery; new runtime does not install them.
