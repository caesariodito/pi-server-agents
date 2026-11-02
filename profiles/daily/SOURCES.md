# Daily skill provenance

Curated source snapshot, not installed dependencies. No node_modules, caches, credentials, or generated output included.

- engineering-lifecycle, implementation-review, technical-spec, emil-design-eng: local https://github.com/caesariodito/skills snapshot based on `fdc06a2b889cc627d9da020d09507828dea02fc1`, with approved local lifecycle trigger cleanup. Existing emil-design-eng license retained.
- project-init: local dotfiles `pi/agent/skills/project-init`, based on dotfiles revision `444a91a3fa2c1c39d4533fc9b2ac91cde0e7f6f3`.
- herdr: user-installed `~/.agents/skills/herdr/SKILL.md` snapshot; no upstream revision recorded by original installation. CLI schema remains runtime authority. Review source before publishing/distributing beyond personal setup.
- security-audit: Cloudflare https://github.com/cloudflare/security-audit-skill at `c1c8a8c1471069fb0e188eeaff69b8e8db6564a8`, including MIT license, companions, schema, validators and tests. Upstream skill files unchanged; local UPSTREAM.md routing note adapted to portable installed locations.

Portable adaptations: replace personal dotfiles paths with installed daily-skills paths. Shared preview resolves marked from managed Pi or nvm/npm global Pi; Mermaid remains optional and separately installed only when requested. No Mac environment or browser automation profile imported.

Updates must review source diffs, preserve licenses, run validators and installer tests, and refresh this provenance. Dependencies declared by optional review tools are not installed by base setup.
