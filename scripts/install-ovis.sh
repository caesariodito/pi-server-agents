#!/usr/bin/env bash
# Compatibility tombstone: never install retired legacy runtime or plugin.
set -Eeuo pipefail
printf 'Ovis installation retired. Use Heeler with herdr-core over SSH. Existing runtime state was not changed.\n' >&2
exit 1
