#!/usr/bin/env python3
"""Sync CodeGraph plugin version from npm and verify upstream catalog entries.

Uses only the Python standard library so it runs identically locally and in
GitHub Actions with zero extra dependencies.

Usage:
  python3 scripts/sync_plugins.py --sync-codegraph
  python3 scripts/sync_plugins.py --check-upstream
  python3 scripts/sync_plugins.py --sync-codegraph --check-upstream
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CODEGRAPH_PKG = "@colbymchenry/codegraph"
CODEGRAPH_MANIFESTS = [
    ROOT / "plugins/codegraph/.codex-plugin/plugin.json",
    ROOT / "plugins/codegraph/.claude-plugin/plugin.json",
    ROOT / "plugins/codegraph/plugin.json",
    ROOT / "plugins/codegraph/gemini-extension.json",
]
CATALOGS = [
    ROOT / ".claude-plugin/marketplace.json",
    ROOT / ".agents/plugins/marketplace.json",
    ROOT / ".retinue-plugin/marketplace.json",
]
MANIFEST_CANDIDATES = [
    ".codex-plugin/plugin.json",
    ".claude-plugin/plugin.json",
    "plugin.json",
    ".retinue-plugin/plugin.json",
]
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
GITHUB_URL_RE = re.compile(r"^https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$")


def http_get_json(url: str, *, github: bool = False) -> tuple[int, dict | None]:
    headers = {"User-Agent": "qwang07-plugins-sync"}
    if github:
        headers["Accept"] = "application/vnd.github+json"
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, None


def sync_codegraph() -> bool:
    """Fetch latest @colbymchenry/codegraph version from npm and update manifests."""
    url = f"https://registry.npmjs.org/{urllib.parse.quote(CODEGRAPH_PKG, safe='')}/latest"
    status, data = http_get_json(url)
    if status != 200 or not data or "version" not in data:
        raise RuntimeError(f"Failed to query npm registry ({url}): HTTP {status}")

    latest = str(data["version"]).strip()
    if not SEMVER_RE.match(latest):
        raise RuntimeError(f"Unexpected non-SemVer version from npm: {latest!r}")

    changed = False
    for path in CODEGRAPH_MANIFESTS:
        obj = json.loads(path.read_text(encoding="utf-8"))
        current = obj.get("version")
        if current != latest:
            obj["version"] = latest
            path.write_text(
                json.dumps(obj, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            print(f"UPDATED {path.relative_to(ROOT)}: {current} -> {latest}")
            changed = True
        else:
            print(f"OK      {path.relative_to(ROOT)}: already {latest}")

    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as f:
            f.write(f"codegraph_version={latest}\n")
            f.write(f"codegraph_changed={'true' if changed else 'false'}\n")

    return changed


def collect_catalog_sources() -> dict[str, dict]:
    """Return deduplicated plugin name -> git-subdir source across all catalogs."""
    sources: dict[str, dict] = {}
    for cat_path in CATALOGS:
        data = json.loads(cat_path.read_text(encoding="utf-8"))
        for entry in data.get("plugins", []):
            name = entry["name"]
            src = entry.get("source")
            if isinstance(src, dict) and src.get("source") == "git-subdir":
                sources.setdefault(name, src)
    return dict(sorted(sources.items()))


def check_upstream() -> int:
    """Check every catalog entry's upstream manifest and report live versions."""
    sources = collect_catalog_sources()
    rows: list[tuple[str, str, str, str, str]] = []
    failures = 0

    for name, src in sources.items():
        url = src["url"]
        subpath = src.get("path", "").strip("/")
        ref = src.get("ref") or "HEAD"

        m = GITHUB_URL_RE.match(url)
        if not m:
            rows.append((name, url, ref, "—", "FAIL (unsupported URL)"))
            failures += 1
            continue

        owner, repo = m.group(1), m.group(2)
        repo_slug = f"{owner}/{repo}"

        # Self-hosted plugins in this repository are read directly from disk.
        if repo_slug == "qwang07/plugins":
            version = None
            for cand in MANIFEST_CANDIDATES:
                p = ROOT / subpath / cand
                if p.exists():
                    version = json.loads(p.read_text(encoding="utf-8")).get("version")
                    break
            if version:
                rows.append((name, repo_slug, ref, str(version), "OK (local)"))
            else:
                rows.append((name, repo_slug, ref, "—", f"FAIL (missing manifest in {subpath})"))
                failures += 1
            continue

        # Check repository reachability first to distinguish private repos from broken paths.
        repo_status, repo_meta = http_get_json(
            f"https://api.github.com/repos/{owner}/{repo}", github=True
        )
        if repo_status == 404:
            rows.append((name, repo_slug, ref, "—", "SKIP (private repo)"))
            continue
        if repo_status != 200 or not repo_meta:
            rows.append((name, repo_slug, ref, "—", f"FAIL (repo HTTP {repo_status})"))
            failures += 1
            continue

        resolved_ref = src.get("ref") or repo_meta.get("default_branch") or "main"
        version = None
        last_status = 404
        for cand in MANIFEST_CANDIDATES:
            file_path = f"{subpath}/{cand}" if subpath else cand
            api_url = (
                f"https://api.github.com/repos/{owner}/{repo}/contents/"
                f"{urllib.parse.quote(file_path, safe='/')}?ref={urllib.parse.quote(resolved_ref)}"
            )
            st, body = http_get_json(api_url, github=True)
            last_status = st
            if st == 200 and body and body.get("content"):
                raw = base64.b64decode(body["content"]).decode("utf-8")
                manifest = json.loads(raw)
                version = manifest.get("version") or "(unversioned)"
                break

        if version is not None:
            rows.append((name, repo_slug, resolved_ref, str(version), "OK"))
        else:
            rows.append((name, repo_slug, resolved_ref, "—", f"FAIL (manifest HTTP {last_status})"))
            failures += 1

    lines = [
        "### Upstream Plugin Version Check",
        "",
        "| Plugin | Repo | Ref | Upstream Version | Status |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]
    for name, repo_slug, ref, version, status in rows:
        lines.append(f"| `{name}` | `{repo_slug}` | `{ref}` | `{version}` | {status} |")
    report = "\n".join(lines) + "\n"
    print("\n" + report)

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write(report)

    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sync-codegraph", action="store_true")
    parser.add_argument("--check-upstream", action="store_true")
    args = parser.parse_args()

    if not args.sync_codegraph and not args.check_upstream:
        parser.error("Specify --sync-codegraph and/or --check-upstream")

    if args.sync_codegraph:
        sync_codegraph()
    if args.check_upstream:
        return check_upstream()
    return 0


if __name__ == "__main__":
    sys.exit(main())
