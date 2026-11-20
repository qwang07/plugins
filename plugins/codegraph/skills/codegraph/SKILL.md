---
name: codegraph
description: Manage local CodeGraph indexes (.codegraph/), check index status, run affected-test analysis, configure codegraph.json, troubleshoot syncing/locks, or query CodeGraph via CLI when MCP is unavailable.
---

# CodeGraph CLI & Index Operations

This skill covers the CLI workflows and configuration documented by [CodeGraph](https://colbymchenry.github.io/codegraph/) (`@colbymchenry/codegraph`).

For normal code questions on an indexed repository, prefer the `codegraph_explore` MCP tool directly — the MCP server delivers its own up-to-date usage instructions during `initialize`.

## Command Runner

Use `codegraph` directly if it is installed on `PATH`; otherwise run the latest release without global installation:

```bash
npx -y @colbymchenry/codegraph@latest <command>
```

The examples below write `codegraph` for brevity; substitute `npx -y @colbymchenry/codegraph@latest` when the global binary is absent.

## Project Indexing Lifecycle

Indexing is always the user's decision. **Do not run `init`, `index`, or `uninit` unless the user explicitly asks.**

- **Initialize and build the graph** (creates `.codegraph/` and indexes in one step):
  ```bash
  codegraph init [path]           # add --yes for non-interactive runs
  ```
- **Check index health and pending file syncs**:
  ```bash
  codegraph status [path]
  ```
- **Force a full re-index** (e.g., after editing `codegraph.json` or upgrading):
  ```bash
  codegraph index [path] --force  # --quiet reduces output
  ```
- **Manual incremental sync** (rarely needed — the MCP server auto-syncs via native file watching with a 2s debounce and catches up on reconnect; only needed when watching is disabled or scripting outside an agent session):
  ```bash
  codegraph sync [path]
  ```
- **Clear a stale lock** blocking indexing:
  ```bash
  codegraph unlock [path]
  ```
- **Manage background daemons**:
  ```bash
  codegraph daemon
  ```
- **Remove CodeGraph from a project**:
  ```bash
  codegraph uninit [path]         # --force skips confirmation
  ```

## CLI Query & Impact Commands

Use these when running in a non-MCP environment, inside a subagent without MCP access, or when you need structured CLI output (`--json`):

```bash
codegraph explore "<query>"       # verbatim source + call paths + blast radius (same as codegraph_explore)
codegraph node <symbol|file>      # one symbol's source + callers, or a line-numbered file read
codegraph query <search>          # FTS5 symbol search (--kind, --limit, --json)
codegraph callers <symbol>        # what calls a symbol (--limit, --json)
codegraph callees <symbol>        # what a symbol calls (--limit, --json)
codegraph impact <symbol>         # blast radius of changing a symbol (--depth, --json)
codegraph files [path]            # indexed file structure (--format, --filter, --max-depth, --json)
```

### Find Affected Tests (`codegraph affected`)

Traces transitive import dependencies from changed source files to identify test files to run:

```bash
codegraph affected src/utils.ts src/api.ts
git diff --name-only | codegraph affected --stdin
codegraph affected src/auth.ts --filter "e2e/*" --depth 5 --quiet
```

Flags: `--stdin`, `-d/--depth <n>` (default `5`), `-f/--filter <glob>`, `-j/--json`, `-q/--quiet`.

## Project Configuration (`codegraph.json`)

CodeGraph is zero-config by default — it automatically skips `.gitignore`d paths, files over 1 MB, and standard dependency/build directories (`node_modules`, `vendor`, `dist`, `build`, `target`, `.venv`, `Pods`, `.next`, etc.).

Create an optional `codegraph.json` at the repository root only when needed, then run `codegraph index`:

```json
{
  "exclude": ["static/", "**/vendor/**"],
  "include": ["Tools/"],
  "deprioritize": ["scripts/", "optional-skills/"],
  "extensions": {
    ".tpl": "php",
    ".dota_lua": "lua"
  }
}
```

- `exclude`: drop committed vendored/generated directories that `.gitignore` cannot hide.
- `include`: pull gitignored first-party source back into the index (`exclude` and built-in skips like `node_modules`/`.git` still win).
- `deprioritize`: keep paths indexed and searchable, but rank them below first-party product code.
- `extensions`: map non-standard file extensions to supported language IDs.

## Environment Variables & Troubleshooting

- **`CODEGRAPH_MCP_TOOLS`**: by default MCP exposes only `codegraph_explore`. Re-enable unlisted tools if needed, e.g. `CODEGRAPH_MCP_TOOLS=explore,node,search,callers,callees,impact,files,status`.
- **`CODEGRAPH_WATCH_DEBOUNCE_MS`**: auto-sync debounce window in ms (default `2000`, clamped to `100`–`60000`).
- **`CODEGRAPH_NO_DAEMON=1`**: run MCP in-process instead of sharing a background daemon (helpful on WSL2 `/mnt/` drives or restricted sandboxes; run only one writer per project in this mode).
- **`CODEGRAPH_DIR`**: override the index directory name (default `.codegraph`; e.g., `.codegraph-wsl` when sharing a checkout between Windows and WSL).
- **`CODEGRAPH_TELEMETRY=0`** or **`DO_NOT_TRACK=1`**: disable anonymous usage statistics (or run `codegraph telemetry off`).
- **Staleness banner (`⚠️`)**: if an MCP response flags recently edited files as pending re-index, read those specific files directly; unflagged files remain fresh.
