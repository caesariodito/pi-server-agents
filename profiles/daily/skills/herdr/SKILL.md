---
name: herdr
description: "Control Herdr, a terminal multiplexer for coding agents. Use only when the user explicitly mentions Herdr or asks to use Herdr to inspect or control panes, tabs, workspaces, commands, or another agent. Do not use merely because a task could benefit from a background terminal, delegation, or parallel work. Requires HERDR_ENV=1."
---

# Herdr

Herdr organizes terminals into workspaces, tabs, and panes, recognizes coding agents running inside panes, and exposes the current session through the `herdr` CLI.

Before issuing any control command, verify that this agent is running inside a Herdr-managed pane:

```bash
test "${HERDR_ENV:-}" = 1
```

If the check fails, say that you are not running inside Herdr and stop. Do not inspect or control the focused Herdr session from outside Herdr.

When the check passes, the `herdr` binary in `PATH` talks to the current session. Use it to inspect neighboring work, create terminal layout, start agents and commands, read output, and wait for state changes.

## Learn the current CLI

The installed binary is the authority for command syntax. Start with:

```bash
herdr --help
```

Then print the relevant command group by running the group without a subcommand:

```bash
herdr agent
herdr pane
herdr workspace
herdr tab
herdr worktree
herdr terminal
herdr notification
herdr integration
herdr session
herdr machine
```

Do not run bare `herdr` for discovery; it launches or attaches the TUI. Do not probe a mutating nested command by omitting arguments. Commands such as `herdr workspace create` are valid with defaults and will execute.

Most control commands return JSON. Read identifiers and state from those responses instead of predicting them.

## Understand layout, panes, and agents

Choose the primitive that matches the job:

- Workspace, tab, and pane topology organize terminal locations.
- Pane commands control raw terminals, shells, tests, servers, input, and output.
- Agent commands control the recognized coding agent currently occupying a pane.

A pane exists whether or not it contains an agent. `agent start` requires an existing available shell pane and never creates, splits, or moves layout. Use pane commands for ordinary processes. Use agent commands when Herdr must validate agent identity or interpret `idle`, `working`, `blocked`, `done`, and `unknown` lifecycle states.

Agent commands accept either a unique live agent name or the pane ID currently hosting that agent. They do not accept terminal IDs or bare agent-kind labels. Names must match `[a-z][a-z0-9_-]{0,31}` and be unique among live agents. A name follows the current pane occupant and is cleared when that agent exits, is released, or is replaced. Suspending an agent with Ctrl+Z and running a non-agent command preserves its identity while the exact process remains alive. This does not preserve the original identity across another recognized agent taking over. A retained identity does not mean the agent is in the foreground; inspect the pane before sending input.

`idle` and `done` normally indicate the agent is ready for input; neither guarantees that an unfamiliar approval dialog was recognized or that a retained agent is in the foreground. The CLI/API uses the server's seen state to distinguish them; explicit focus commands mark the target seen, while reads do not. Each TUI client tracks viewed completions independently, so its Done badge can differ from the CLI or another client's badge. Antigravity and Grok can be idle while background tasks or subagents keep running, so a settled-state wait is not proof those jobs have finished. `blocked` means Herdr recognized an approval or question UI. `unknown` means an agent is present but Herdr cannot classify it confidently; it does not prove completion.

## Use IDs and caller context

Public IDs are opaque stable handles:

- workspace: `w1`
- tab: `w1:t1`
- pane: `w1:p1`

Closed tab and pane IDs are not reused. A pane moved into another workspace receives a new workspace-qualified pane ID. After `pane move`, continue with `.result.move_result.pane.pane_id` or the live agent name. The old value is reported as `.result.move_result.previous_pane_id`; only the moved process's inherited caller context keeps resolving that old ID, so do not use it as a general agent target.

Herdr injects the caller's context into each managed pane:

```bash
printf '%s\n' "$HERDR_WORKSPACE_ID" "$HERDR_TAB_ID" "$HERDR_PANE_ID"
```

Prefer `--current` when a pane command should target the calling pane. An omitted `pane split` target uses the calling pane when `HERDR_PANE_ID` is available, otherwise the focused pane. Other commands may use the UI-focused pane, which can belong to the user or another client.

Discover live state with:

```bash
herdr workspace list
herdr tab list --workspace "$HERDR_WORKSPACE_ID"
herdr pane current --current
herdr pane list --workspace "$HERDR_WORKSPACE_ID"
herdr agent list
```

Creation responses expose the IDs to use next. `workspace create` returns `.result.workspace`, `.result.tab`, and `.result.root_pane`. `tab create` returns `.result.tab` and `.result.root_pane`. `pane split` returns the new pane as `.result.pane`.

IDs and live agent names are scoped to one server. Two saved SSH machines can both have `w1:p1` or an agent named `reviewer`. Selecting a machine in the TUI does not retarget commands running in your pane: without `--machine`, they still use the inherited session and socket context.

To control a saved SSH machine, use the same global prefix for discovery and every later command:

```bash
herdr --machine <label-or-id> agent list
herdr --machine <label-or-id> pane list
herdr --machine <label-or-id> agent prompt <remote-agent-name> "Reply with your current status." --wait --timeout 120000
```

The selector must be an enabled saved profile ID or a unique, case-sensitive label, not an arbitrary SSH hostname. Commands use that profile's remote session without an open TUI. Do not combine `--machine` with `--session` or `--remote`. Discover IDs on that machine; inherited local IDs and `--current` do not identify remote panes.

Both installations must support machine API forwarding, and the remote server must already be running and API-compatible. Forwarding never installs, starts, or restarts a server and never falls back to Local. Local configuration, session management, installation commands, and interactive attachment are not forwarded. Remote worktree paths must be absolute, `~`, or start with `~/`; plugin link paths must be absolute. A connection failure does not prove a mutation was not applied: inspect remote state before retrying.

`herdr machine list` lists saved connection profiles, not a cross-machine pane inventory; add `--json` for scripts. Only add, remove, enable, or disable profiles when the user asks. Removing a profile disconnects the client but does not stop remote sessions. Interactive `machine add` discovers running remote sessions and may ask the user to pick one; non-interactive setup uses the remote default session unless `--remote-session` is explicitly supplied. Use `herdr machine status [<label-or-id>] --json` to diagnose a failing machine. `herdr machine reconnect` needs the user to complete SSH authentication in their terminal; do not run it for them. Setup asks before stopping an incompatible server and defaults to No; do not approve replacement without the user's consent. Experimental handoff is not part of `machine add`.

## Start and coordinate an agent

Use this workflow only when the user requests separate-agent work. Naming/topology rules alone do not authorize delegation. Work directly otherwise; never substitute hidden subagents or child Pi sessions for Herdr.

### Name the family

Inspect `herdr agent list`. Choose an unused short lowercase alphanumeric family ID starting with a letter, such as `k7p`. Rename the spawning agent `<char-id>-super-<context>` and name each spawned agent `<char-id>-child-<context>` with the same family ID and unique short context:

```text
k7p-super-auth
k7p-child-tests
k7p-child-review
```

Validate each full name against `[a-z][a-z0-9_-]{0,31}`: at most 32 characters and unique among live agents. Shorten context before use; inspect collisions rather than silently reusing a name. Preserve an existing matching family. Rename the caller explicitly:

```bash
herdr agent rename "$HERDR_PANE_ID" k7p-super-auth
```

### Create a linked worktree workspace

Every spawned agent gets a separate Herdr-linked worktree workspace grouped under the spawning workspace's repository, not a sibling pane or tab. Here, nested means Herdr's linked worktree grouping; do not invent arbitrary recursive workspace hierarchy or filesystem nesting. Reserve pane splits for ordinary shell commands.

For a new checkout:

```bash
herdr worktree create --workspace "$HERDR_WORKSPACE_ID" \
  --branch k7p-child-tests --label k7p-child-tests --no-focus
```

For an existing worktree, use `herdr worktree open --workspace <parent-workspace-id> --path <absolute-worktree-path> --label <child-name> --no-focus`. If the spawning workspace is not attached to the intended Git repository, use verified repository `--cwd <absolute-repo-path>` instead of `--workspace`. Plain `workspace create --cwd <worktree>` does not create this grouping. For non-Git work, stop and ask before using a standalone workspace; do not fall back to pane delegation.

Read actual workspace and root-pane IDs from creation/open JSON; response schema is authoritative. Verify returned checkout path, branch/base, and shared repository using `herdr workspace get <returned-workspace-id>` and Git inspection before starting a writer. Worktrees start from a Git base, not the parent's uncommitted changes; explicitly arrange any needed snapshot or patch without committing or discarding user work implicitly. Reviewers must receive the exact intended diff, including relevant untracked files, rather than reviewing a clean base accidentally.

Keep one writer per checkout. Starting another agent never authorizes commits, integration, publication, cleanup, or recursive spawning. Do not move existing agents/workspaces unless requested.

An available root pane must be at its interactive shell prompt with no foreground task. Start the requested kind there; otherwise use `pi`:

```bash
herdr agent start k7p-child-tests --kind pi --pane <returned-root-pane-id>
```

### Supply bounded context

Before prompting, record supervisor name/pane/workspace, child name/workspace/worktree, approved goal, canonical spec path/version, and exact baseline. Give the child only relevant instructions, files, settled decisions, acceptance criteria, ownership/read-write limits, verification commands, stop conditions, and required return format. Canonical specs or evidence missing from the new worktree need an explicit readable path or snapshot. No secrets or unrelated transcript dumps. Keep architecture/scope decisions and final acceptance with the supervisor.

Use the kind requested by the user. Run `herdr agent` to inspect the installed kind list and options. Pass native agent arguments only after `--`:

```bash
herdr agent start k7p-child-tests --kind pi --pane <returned-root-pane-id> -- <agent-args...>
```

A successful `agent start` returns only after Herdr detects the expected agent in the same pane and considers it ready for interactive input. If the agent is blocked during startup, the command returns `agent_not_ready` immediately but keeps the name available for `agent read` and `agent send-keys`. Wait until the agent becomes idle before prompting it. Startup defaults to a 30-second timeout.

Submit work through the agent surface:

```bash
herdr agent prompt k7p-child-tests "<bounded context, task, validation, and return contract>" --wait --timeout 120000
```

`agent prompt` honors the pane's live bracketed-paste mode and sends text followed by encoded Enter as one ordered submission. It reports successful submission only after both have been written; that alone does not prove the agent started a turn. For Codex on Windows, Herdr sends a paste boundary before Enter so submission does not depend on prompt size. It rejects an agent already waiting at an approval or question dialog with `agent_blocked` before sending any input. Inspect the blocked UI and ask the user before answering it. For normal agent work, `--wait` is enough: it waits for the first settled `idle`, `done`, or `blocked` state. Do not repeat those defaults with `--until`.

With `--wait`, a prompt sent from a non-working state must produce observed `working` or `blocked` activity. After submission, Herdr waits up to five seconds for that activity; unrelated `idle`, `done`, or session changes do not satisfy this gate. It returns `agent_prompt_stalled` if no activity is observed, or `timeout` if the caller's timeout expires first. The caller timeout includes submission time. Without a timeout, the settled-state wait is indefinite after activity is observed. This wait tracks lifecycle state, not an individual turn; if the agent is already working, completion of the active turn may satisfy it.

Use `--until` only for a state-specific workflow, such as waiting for an already-running agent to request input:

```bash
herdr agent wait k7p-child-tests --until blocked --timeout 120000
```

Without `--until`, standalone `agent wait` uses the same settled-state defaults as `agent prompt --wait`.

Use logical keys for interactive agent UI controls:

```bash
herdr agent send-keys k7p-child-tests esc
herdr agent send-keys k7p-child-tests ctrl+c
```

Herdr validates all keys before writing any bytes. Read the result through the resolved agent:

```bash
herdr agent get k7p-child-tests
herdr agent read k7p-child-tests --source recent-unwrapped --lines 120
```

If a wait fails or returns `blocked`, inspect `agent get` and `agent read` before deciding what input to send. A timeout or stalled response does not prove the prompt was never delivered; do not blindly submit it again. Use the pane surface only when raw terminal control is intentional.

### Return results to the spawner

The child must finish with a concise handoff addressed to its recorded supervisor:

- child/supervisor names, worktree path, branch, and exact baseline;
- status: completed, blocked, or failed; goal and acceptance coverage;
- changed paths and where the actual diff/patch or authorized commits live;
- commands run and results, including failures and unrun checks;
- findings, decisions, assumptions, residual risks, and next action.

A settled Herdr state is not task acceptance. After waiting, the supervisor must read the child's output, verify its checkout/diff and relevant checks, then bring the result/context into its own session and canonical spec before continuing. This supervisor pull is the default delivery channel: a child need not inject a prompt into a busy parent. If asynchronous notification is explicitly needed, target the recorded supervisor name/pane and inspect its state before sending; never answer a parent approval UI.

If terminal history cannot recover the handoff, have the child write a secret-free handoff under ignored `.scratch/<task>/` in its worktree and report its absolute path. The supervisor must read and acknowledge it. Missing handoff or unavailable verification remains blocked; do not infer success from `idle`/`done`.

Retain child workspace/worktree and unintegrated changes until accepted and safely preserved. Integration or destructive cleanup requires appropriate approval; never remove the only copy of work. No automatic closing on child completion.

## Run an ordinary command in another pane

For shell commands only, inspect caller layout (`herdr pane layout --pane "$HERDR_PANE_ID"`); split wide panes right and tall/narrow panes down. Preserve caller working directory and user focus:

```bash
herdr pane split --current --direction right --cwd "$PWD" --no-focus
```

Read the new pane ID from `.result.pane.pane_id`, then run and inspect the command:

```bash
herdr pane run <returned-pane-id> "just test"
herdr pane wait-output <returned-pane-id> --match "test result" --timeout 120000
herdr pane read <returned-pane-id> --source recent-unwrapped --lines 120
```

`pane run` queues command text and Enter together; success acknowledges admission, not command execution. On macOS, `pane run` and `agent start` reject a command that exceeds the terminal's current canonical line-input limit before queuing it. Wait for the interactive shell prompt before retrying. The check covers this submission, not an earlier incomplete line or a later terminal-mode change. `pane wait-output` searches the selected snapshot immediately, so output that already exists can match. Use `--match <text>` for a literal substring or `--regex <pattern>` for a Rust regular expression. Omitting `--timeout` allows an indefinite wait.

Use the read source that matches the task:

- `visible`: the currently rendered viewport.
- `recent`: recent rendered output, including soft wraps.
- `recent-unwrapped`: recent output with soft wraps joined; prefer it for logs and transcripts.
- `detection`: the plain-text bottom-buffer snapshot used for agent detection.

Use `--format ansi` when colors and terminal styling are evidence. Otherwise use text.

`--lines` asks Herdr for more rows from the pane's available screen and host scrollback. Alternate-screen rows do not enter ordinary host scrollback. For supported idle agents, Herdr can collect application-owned history and restore the viewport afterward, but not every application or response can be recovered this way.

If a larger recent read still does not reveal the completed response, ask the agent to write it as Markdown in a temporary directory and reply only with the file path, then read that file on the same machine. Use this only as a fallback; do not request file output in the initial prompt.

## Safety and coordination rules

- Use `--no-focus` for background work unless the user asked to switch context.
- Use `--current`, an explicit pane ID, or a unique agent name. Do not rely on another client's focused pane.
- Parse IDs from JSON responses. Do not derive them from sidebar order or examples.
- Do not close workspaces, tabs, panes, or sessions you did not create unless the user explicitly asked. Ordinary CLI/API closes do not inherit the TUI's last-pane confirmation. `workspace close --group` closes the primary workspace and its linked worktree workspaces; never add it merely to bypass `workspace_group_close_required`.
- Use `--trust-repository` only after the user has verified the repository. It grants per-request Git trust; it is not a routine retry for a failed worktree command.
- Client and server versions can differ after an update. Check `herdr status` before relying on new server features. A missing method is not permission to stop or upgrade a server.
- Never run `herdr server stop` from an active session unless the user explicitly intends to stop the server and its pane processes.
- Never kill the main Herdr process. Use named test sessions for experiments that need an isolated server.
- CLI server errors are JSON on stderr with exit status 1. CLI syntax errors exit with status 2.
