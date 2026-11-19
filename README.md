# qwang07's plugins

A plugin marketplace for [Claude Code](https://claude.com/claude-code), [Codex](https://developers.openai.com/codex), and [门客 (retinue)](https://github.com/qwang07/retinue). The catalog links to the plugin repositories. Milestone publishes both installable bundles on its [`plugin` branch](https://github.com/qwang07/milestone-mod/tree/plugin/plugins/milestone).

## Install

### Claude Code

```
/plugin marketplace add qwang07/plugins
/plugin install wecom@qwang07
/plugin install archify@qwang07
```

### Codex

```
codex plugin marketplace add qwang07/plugins
codex plugin add wecom@qwang07
codex plugin add archify@qwang07
codex plugin add milestone@qwang07
```

Or run `/plugins` in the Codex CLI and install from the browser.

To refresh an existing Milestone installation, run:

```sh
codex plugin marketplace upgrade qwang07
codex plugin add milestone@qwang07
```

### Antigravity

Clone the Milestone release branch.

```sh
git clone --branch plugin --single-branch https://github.com/qwang07/milestone-mod.git milestone-release
```

Copy `milestone-release/plugins/milestone/antigravity` to `~/.gemini/config/plugins/milestone`.
Follow the [Milestone setup guide](https://github.com/qwang07/milestone-mod/blob/plugin/plugins/milestone/antigravity/README.md) to enable the panel.
Run `git -C milestone-release pull --ff-only` to fetch updates, then replace the installed plugin directory with the updated bundle.

### 门客 (retinue)

In 门客, open 设置 · 插件 · 市场, add the catalog `https://github.com/qwang07/plugins`, then install `todo` from it. 门客 also ships `todo` in its built-in catalog, so this entry is only needed to install it from source.

## Plugins

| Plugin | What it does | Source |
|---|---|---|
| `wecom` | 79 WeCom (企业微信) tools, 8 resources, 3 prompts — Contact, Approval, Drive, Doc/Smartsheet/Form over MCP | [qwang07/wecom-mcp](https://github.com/qwang07/wecom-mcp) |
| `todo` | 门客的待办清单：门客做多步的活时列出清单，侧边面板画清单，名录状态位显示进度（门客 only） | [qwang07/retinue](https://github.com/qwang07/retinue/tree/main/plugins/todo) |
| `archify` | Interactive architecture and workflow diagrams, sequence diagrams and source-backed explainers; upstream skill synced daily | [qwang07/archify](https://github.com/qwang07/archify/tree/plugin/plugins/archify) |
| `milestone` | Project goals, deliverables, and live progress for Codex and Antigravity | [Milestone packages](https://github.com/qwang07/milestone-mod/tree/plugin/plugins/milestone) |

### Credentials

`wecom` needs a self-built WeCom app's corp ID and secret. The two clients collect them differently:

- **Claude Code** prompts you when the plugin is enabled; the secret is stored in the system keychain, not in `settings.json`.
- **Codex** forwards `WECOM_CORP_ID`, `WECOM_CORP_SECRET`, and `WECOM_ADMIN_USERID` from your shell environment — export them before starting Codex.

`archify` needs no credentials; its CLI requires Node.js 18+. The generated `plugin` branch tracks upstream daily at 04:23 Asia/Shanghai (GitHub schedules may be delayed). The catalog uses `git-subdir` with `path: plugins/archify` so clients can use blob-filtered sparse checkout rather than clone the fork with all file history. Each package records its upstream commit in `plugins/archify/upstream.json`. Refresh / update the installed plugin to receive changes; [packaging details](https://github.com/qwang07/archify/tree/packaging/.github/plugin).

## Why three catalog files

Each client discovers a marketplace by scanning fixed paths, and their lists differ:

| Client | Path | Notes |
|---|---|---|
| Claude Code | `.claude-plugin/marketplace.json` | the only path it reads |
| Codex | `.agents/plugins/marketplace.json` | ranks above `.claude-plugin/`, so Codex reads this one and never sees the other |
| 门客 | `.retinue-plugin/marketplace.json` | the only path it reads; lists only plugins that carry a 门客 manifest (`.retinue-plugin/plugin.json`), and only `git-subdir` sources |

Because Codex stops at the first match, its catalog has to carry the full plugin list on its own. Keep fields shared by Claude Code and Codex in sync. The Codex catalog also lists Milestone. The 门客 file may list a different set of plugins; a plugin it shares with the other two must carry the same shared fields. `tests/catalog_sync.py` checks all three against each other and against the table above.

Each plugin's own `plugin.json` declares its version. Publish both Milestone packages to the `plugin` branch of `qwang07/milestone-mod` when releasing a new version.

## License

MIT
