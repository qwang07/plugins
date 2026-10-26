# qwang07's plugins

A plugin marketplace for [Claude Code](https://claude.com/claude-code), [Codex](https://developers.openai.com/codex), and [门客 (retinue)](https://github.com/qwang07/retinue). This repo is only the catalog — each plugin lives in its own repository and is pulled in by `git-subdir`.

## Install

### Claude Code

```
/plugin marketplace add qwang07/plugins
/plugin install wecom@qwang07
/plugin install northstar@qwang07
```

### Codex

```
codex plugin marketplace add qwang07/plugins
codex plugin add wecom@qwang07
codex plugin add northstar@qwang07
```

Or run `/plugins` in the Codex CLI and install from the browser.

### 门客 (retinue)

In 门客, open 设置 · 插件 · 市场, add the catalog `https://github.com/qwang07/plugins`, then install `todo` from it. 门客 also ships `todo` in its built-in catalog, so this entry is only needed to install it from source.

## Plugins

| Plugin | What it does | Source |
|---|---|---|
| `wecom` | 79 WeCom (企业微信) tools, 8 resources, 3 prompts — Contact, Approval, Drive, Doc/Smartsheet/Form over MCP | [qwang07/wecom-mcp](https://github.com/qwang07/wecom-mcp) |
| `todo` | 门客的待办清单：门客做多步的活时列出清单，侧边面板画清单，名录状态位显示进度（门客 only） | [qwang07/retinue](https://github.com/qwang07/retinue/tree/main/plugins/todo) |
| `northstar` | 契约驱动的开发回路，六技能：contract → write-test → audit → 实施（裸代理）→ simplify → code-review，外加 diagnose 缺陷归因独立入口 | [qwang07/northstar](https://github.com/qwang07/northstar) |

### Credentials

`wecom` needs a self-built WeCom app's corp ID and secret. The two clients collect them differently:

- **Claude Code** prompts you when the plugin is enabled; the secret is stored in the system keychain, not in `settings.json`.
- **Codex** forwards `WECOM_CORP_ID`, `WECOM_CORP_SECRET`, and `WECOM_ADMIN_USERID` from your shell environment — export them before starting Codex.

`northstar` needs no credentials.

## Why three catalog files

Each client discovers a marketplace by scanning fixed paths, and their lists differ:

| Client | Path | Notes |
|---|---|---|
| Claude Code | `.claude-plugin/marketplace.json` | the only path it reads |
| Codex | `.agents/plugins/marketplace.json` | ranks above `.claude-plugin/`, so Codex reads this one and never sees the other |
| 门客 | `.retinue-plugin/marketplace.json` | the only path it reads; lists only plugins that carry a 门客 manifest (`.retinue-plugin/plugin.json`), and only `git-subdir` sources |

Because Codex stops at the first match, its catalog has to carry the full plugin list on its own. The Claude Code and Codex files are kept in sync by hand; they differ only in client-specific fields (`owner` for Claude Code, `interface` / `policy` for Codex). The 门客 file may list a different set of plugins; a plugin it shares with the other two must carry the same shared fields. `tests/catalog_sync.py` checks all three against each other and against the table above.

Plugin versions are **not** pinned here — each plugin's own `plugin.json` is the authority, so releasing a plugin never requires a commit to this repo.

## License

MIT
