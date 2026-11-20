# CodeGraph Plugin

Thin multi-client plugin wrapper for [`@colbymchenry/codegraph`](https://github.com/colbymchenry/codegraph).

- Runs `npx -y @colbymchenry/codegraph@latest serve --mcp` so the MCP server tracks the latest upstream npm release without pinning a version.
- Ships an on-demand `codegraph` skill covering the official CLI workflows (`init`, `status`, `affected`, `codegraph.json`, troubleshooting, and non-MCP CLI queries) without duplicating the MCP `initialize` playbook.
- Ships `rules/AGENTS.md` (matching CodeGraph's official conditional instructions block) for Antigravity and Gemini CLI.

## Supported Clients

- **Claude Code**: `.claude-plugin/plugin.json` + `skills/`
- **Codex**: `.codex-plugin/plugin.json` + `skills/`
- **Antigravity**: `plugin.json` + `mcp_config.json` + `rules/AGENTS.md` + `skills/`
- **Gemini CLI**: `gemini-extension.json` + `rules/AGENTS.md` + `skills/`

## Requirements

- Node.js (`npx` on `PATH`)
- Network access on first run or when a newer `@colbymchenry/codegraph` release is published (downloads the self-contained per-platform runtime bundle)
- Run `npx -y @colbymchenry/codegraph@latest init` inside each repository you want indexed
