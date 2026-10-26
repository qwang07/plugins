#!/usr/bin/env python3
"""编目同步测试——三份 marketplace.json 与 README 之间的跨文档引用完整性。

为什么这里用文本逐字比对：本仓的契约本身就是**词法契约**。Claude Code 只读
.claude-plugin/marketplace.json；Codex 读 .agents/plugins/marketplace.json 且读到
就停，永远看不到前者——两份必须各自完整，且共享字段逐字一致。量具是文本，正确。

门客（retinue）只读 .retinue-plugin/marketplace.json，只认 git-subdir 来源，且只列
带门客清单（.retinue-plugin/plugin.json）的插件——所以它的插件集合可以与前两份不同。
同名插件在三份里共享字段逐字一致；只在门客编目里的插件不参与 C1–C4。

反过来划清边界：「编目文案是否如实描述 northstar 实际的技能集合」是**兑现类契约**，
跨仓且需联网，不在本文件——**勿在此处用 grep 关键词去代理它**，那会变成变更探测器。

运行：python3 tests/catalog_sync.py；全绿退出码 0，任一红非 0。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAUDE = ROOT / ".claude-plugin/marketplace.json"
CODEX = ROOT / ".agents/plugins/marketplace.json"
RETINUE = ROOT / ".retinue-plugin/marketplace.json"
README = ROOT / "README.md"

# 共享字段：两份编目必须逐字相同（手工同步漏改一份 = 这里红）
SHARED = ["description", "homepage", "repository", "license", "keywords", "source"]
# description 的**显式例外**，且例外范围就是这份枚举：
# 凭据获取方式确实按客户端不同（见 README「Credentials」），两份文案各自描述本客户端的机制。
# 例外不是豁免——枚举内仍须满足：除末句外逐句相同（功能描述共享，仅末句可分岔），
# 且必须**真的不同**（相同则例外已失效，应从枚举删除，防止例外清单沦为万能挡箭牌）。
DESC_MAY_DIFFER = {"wecom": "凭据获取方式按客户端不同（keychain 提示 vs 环境变量）"}
# 客户端专属字段：允许只出现在一侧
ONLY_CLAUDE = {"displayName"}
ONLY_CODEX = {"policy"}
# 两侧都须有、但取值域各自不同，故不比对内容
DIVERGENT = {"category"}
# 门客编目条目允许的字段：共享字段 + 名字与显示名（门客读 displayName）
RETINUE_FIELDS = set(SHARED) | {"name", "displayName"}

failures = []


def check(name, ok, reason=""):
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f" —— {reason}"))
    if not ok:
        failures.append(name)


def load(p):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        check(f"C0 {p.relative_to(ROOT)} 可解析", False, str(e))
        return None


c, x, r = load(CLAUDE), load(CODEX), load(RETINUE)
if c is None or x is None or r is None:
    print("\n编目不可解析，后续断言无从谈起")
    sys.exit(1)

cp = {p["name"]: p for p in c.get("plugins", [])}
xp = {p["name"]: p for p in x.get("plugins", [])}
rp = {p["name"]: p for p in r.get("plugins", [])}
both = sorted(set(cp) & set(xp))

# C1 插件名集合相同——一份加了插件另一份忘加，该客户端就永远看不到它
check("C1 两份编目插件名集合相同", set(cp) == set(xp),
      f"仅 Claude 侧有 {sorted(set(cp) - set(xp))}；仅 Codex 侧有 {sorted(set(xp) - set(cp))}")

def sentences(s):
    return [t.strip() for t in re.split(r"(?<=[.。])\s+", (s or "").strip()) if t.strip()]


# C2 共享字段逐字一致（description 的例外单独判，见 C2b）
for n in both:
    fields = [f for f in SHARED if not (f == "description" and n in DESC_MAY_DIFFER)]
    diff = [f for f in fields if cp[n].get(f) != xp[n].get(f)]
    check(f"C2 {n} 共享字段逐字一致", not diff, f"不一致字段 {diff}——手工同步漏改一份")

# C2b description 例外的双向约束：枚举内必须真的不同，且只许末句分岔
for n in sorted(set(DESC_MAY_DIFFER) & set(both)):
    dc, dx = cp[n].get("description"), xp[n].get("description")
    check(f"C2b {n} description 例外仍在使用", dc != dx,
          "两侧已相同——例外失效，请从 DESC_MAY_DIFFER 删除，别让例外清单成为万能挡箭牌")
    sc, sx = sentences(dc), sentences(dx)
    check(f"C2b {n} description 仅末句分岔", sc[:-1] == sx[:-1],
          f"末句之外也不同：Claude 侧 {sc[:-1]} / Codex 侧 {sx[:-1]}——功能描述必须共享")

# C2c 例外枚举不得越界：枚举里不存在的插件名 = 陈旧条目
check("C2c description 例外枚举无陈旧条目", set(DESC_MAY_DIFFER) <= set(both),
      f"枚举中的 {sorted(set(DESC_MAY_DIFFER) - set(both))} 已不在编目里")

# C3 两侧各自的客户端专属字段与取值域字段齐备
for n in both:
    miss_c = sorted((ONLY_CLAUDE | DIVERGENT) - set(cp[n]))
    miss_x = sorted((ONLY_CODEX | DIVERGENT) - set(xp[n]))
    check(f"C3 {n} 客户端专属字段齐备", not miss_c and not miss_x,
          f"Claude 侧缺 {miss_c}；Codex 侧缺 {miss_x}")

# C4 字段差异不得越出允许清单——单侧独有的字段必须是已声明的客户端专属字段
for n in both:
    stray = sorted((set(cp[n]) ^ set(xp[n])) - ONLY_CLAUDE - ONLY_CODEX)
    check(f"C4 {n} 字段差异在允许清单内", not stray, f"越界差异字段 {stray}")

# C4b 专属字段不得串侧。C4 只查对称差集，专属字段被复制到**两侧**时它反而看不见
# ——实测由变异检查抓出，故补此正向断言。
for n in both:
    misplaced = sorted((ONLY_CLAUDE & set(xp[n])) | (ONLY_CODEX & set(cp[n])))
    check(f"C4b {n} 专属字段未串侧", not misplaced,
          f"{misplaced} 出现在了不属于它的那一侧——两侧都有时 C4 的对称差集为空，只能靠这条")

# R1 门客只认 git-subdir 来源（相对路径只用于应用内置的编目）
for n in sorted(rp):
    src = rp[n].get("source")
    ok = isinstance(src, dict) and src.get("source") == "git-subdir" and bool(src.get("url"))
    check(f"R1 {n} 门客编目来源是 git-subdir", ok, f"source 为 {src!r}")

# R2 与另两份同名的插件：共享字段逐字一致（description 例外同 C2）
for n in sorted(set(rp) & set(cp)):
    fields = [f for f in SHARED if not (f == "description" and n in DESC_MAY_DIFFER)]
    diff = [f for f in fields if rp[n].get(f) != cp[n].get(f)]
    check(f"R2 {n} 门客编目与 Claude 编目共享字段逐字一致", not diff, f"不一致字段 {diff}")

# R3 门客编目不带别的客户端的专属字段（policy、category 之类）
for n in sorted(rp):
    stray = sorted(set(rp[n]) - RETINUE_FIELDS)
    check(f"R3 {n} 门客编目字段在允许清单内", not stray, f"越界字段 {stray}")

# C5 README 的 Plugins 表格是又一处同步点：覆盖须与三份编目的并集双向相等
rd = README.read_text(encoding="utf-8") if README.exists() else ""
listed = set(re.findall(r"^\|\s*`([a-z0-9_-]+)`\s*\|", rd, re.M))
every = set(cp) | set(xp) | set(rp)
check("C5 README 表格覆盖全部插件", every <= listed, f"README 未列出 {sorted(every - listed)}")
check("C5 README 无编目外的插件", listed <= every, f"README 多出 {sorted(listed - every)}")

print(f"\n{'全绿' if not failures else f'{len(failures)} 红'}：共 {len(failures)} 失败")
sys.exit(1 if failures else 0)
