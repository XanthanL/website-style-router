#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ledger.py — 批次风格账本：让 skill 记住它做过什么。

## 为什么需要它

v0.7 之后发现的核心问题：**单站内的「约束排除」无法解决跨站的「同向收敛」。**

排除法的工作方式是「给一个需求，砍掉不适用的选项」。但当一批站的需求画像相似
（小型 / 单页 / 无后端 / 中文 / 低频更新）时，排除法砍掉的是同一批选项，剩下的
必然落在同一个区域。5 个测试站独立选型，全都滑向 swiss-utility 和 provisions-label。

每个站单看都合格（audit F 级 0），五个摆一起就塌 —— 因为**没有任何一个脚本知道
「上一次用的是什么」**。本文件补上这个维度。

## 用法

    # 查重：本次选型是否与同批次已交付的站撞车（开工前必跑）
    python scripts/ledger.py --check --dir <工作区> \\
        --anchor swiss-utility --surface white --variant a --pair 0 \\
        --axis left-rail --family grid --layout utility-board

    # 记录一次交付
    python scripts/ledger.py --commit --dir <工作区> --name 12sqm-coffee \\
        --anchor warm-hospitality --surface paper --variant a --pair 0 \\
        --axis center-axis --family craft --layout editorial-hero \\
        --font-display Gloock --ia conversion

    # 批次多样性报告
    python scripts/ledger.py --report --dir <工作区>

    # 机器可消费
    python scripts/ledger.py --check ... --json

账本落在 `<工作区>/.style-ledger.json`，**不进 skill 仓库** —— 它是项目侧状态，
跟着具体的一批站走。换一批站就换一个工作区。

退出码：0 = 通过 / 1 = 有高冲突或报告不达标 / 2 = 用法错误。
无第三方依赖。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)

LEDGER_NAME = ".style-ledger.json"

# 字段 → 「已出现多少次才算冲突」
# 1 表示「只要出现过就冲突」（必须唯一）；2 表示「出现 2 次以上才冲突」（允许一对）
UNIQUE_AT = {
    "anchor": 1,
    "font_display": 1,
    "surface": 2,
    "axis": 2,
    "family": 2,
    "layout": 2,
    "ia": 2,
}

LABEL = {
    "anchor": "锚点",
    "font_display": "display 字体",
    "surface": "底色档",
    "axis": "中轴",
    "family": "族",
    "layout": "布局原型",
    "ia": "信息架构",
}

# 批次报告阈值
MIN_ANCHOR_UNIQUE = 0.80
MIN_FONT_UNIQUE = 1.00
MIN_SURFACE_KINDS = 3
MIN_FAMILY_RATIO = 0.60
# 中轴只有 3 档。要求「3 种全部出现」= 覆盖率 100% = **配额**，不是多样性 ——
# 那会强制每个批次都含一个 `split` 站，而 split 只有 5 个锚点（还全在 editorial/expressive 附近），
# 结果把布局原型与族的自由度一起锁死（v0.9 实测：5 站凑不齐 3 种中轴就是这个原因）。
# 改成「≥2 种 + 单档占比 ≤60%」：仍然抓得住「5 站全 left-rail」这种真塌缩，但不再制造必经点。
MIN_AXIS_KINDS = 2
MAX_AXIS_SHARE = 0.60


def ledger_path(d):
    return os.path.join(os.path.abspath(d), LEDGER_NAME)


def load(d):
    p = ledger_path(d)
    if not os.path.exists(p):
        return {"version": 1, "entries": []}
    try:
        doc = json.load(open(p, encoding="utf-8"))
    except Exception as e:
        print(f"账本损坏，无法读取：{p}\n  {e}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(doc.get("entries"), list):
        print(f"账本格式不对（缺 entries 数组）：{p}", file=sys.stderr)
        sys.exit(2)
    return doc


def save(d, doc):
    p = ledger_path(d)
    open(p, "w", encoding="utf-8").write(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
    )
    return p


def registry_options():
    """从 skill 注册表读可选值，用于给出「换成什么」的建议。"""
    out = {"anchor": [], "family": [], "surface": [], "axis": [], "layout": []}
    try:
        idx = json.load(open(os.path.join(SKILL, "styles", "index.json"), encoding="utf-8"))
        for x in idx.get("anchors", []):
            out["anchor"].append(x["slug"])
            if x.get("family"):
                out["family"].append(x["family"])
            if x.get("axis"):
                out["axis"].append(x["axis"])
            if x.get("layout"):
                out["layout"].append(x["layout"])
    except Exception:
        pass
    try:
        sig = json.load(open(os.path.join(SKILL, "styles", "signatures.json"), encoding="utf-8"))
        out["surface"] = sorted((sig.get("_surfacePresets") or {}).keys())
    except Exception:
        pass
    for k in out:
        out[k] = sorted(set(out[k]))
    return out


def collect(a):
    """从命令行参数收集本次选型的指纹。"""
    keys = ["anchor", "family", "surface", "variant", "pair", "axis",
            "layout", "ia", "font_display"]
    return {k: getattr(a, k.replace("-", "_"), None) for k in keys}


def cmd_check(a):
    doc = load(a.dir)
    entries = doc["entries"]
    mine = collect(a)

    conflicts = []
    for field, need in UNIQUE_AT.items():
        val = mine.get(field)
        if val is None:
            continue
        hits = [e for e in entries if str(e.get(field)) == str(val)]
        if len(hits) >= need:
            who = "、".join(e.get("name") or "?" for e in hits[:4])
            sev = "高" if need == 1 else "中"
            conflicts.append({
                "field": field, "value": val, "count": len(hits),
                "who": who, "severity": sev,
            })

    opts = registry_options()
    used = {
        "anchor": {e.get("anchor") for e in entries},
        "surface": {e.get("surface") for e in entries},
        "axis": {e.get("axis") for e in entries},
        "family": {e.get("family") for e in entries},
    }
    suggestions = []
    fam = mine.get("family")
    if any(c["field"] == "anchor" for c in conflicts):
        alt = [x for x in opts["anchor"] if x not in used["anchor"]]
        if fam:
            same_fam = [x for x in alt if x in _anchors_of_family(fam)]
            if same_fam:
                suggestions.append(
                    f"锚点改选（同族未用）：{'、'.join(same_fam[:4])}"
                )
        if alt:
            suggestions.append(f"或跨族换锚点（未用）：{'、'.join(alt[:5])}")
        suggestions.append(
            "若必须保留该锚点：换组合 —— "
            f"surface ∈ {{{', '.join(x for x in opts['surface'] if x not in used['surface']) or '无可用'}}}，"
            "variant ∈ {b,c,d}，pair ∈ {1,2,3}"
        )
    if any(c["field"] == "surface" for c in conflicts):
        free = [x for x in opts["surface"] if x not in used["surface"]]
        suggestions.append(f"底色档改选（未用）：{'、'.join(free) or '全部已用，优先挑出现次数最少的'}")
    if any(c["field"] == "axis" for c in conflicts):
        free = [x for x in opts["axis"] if x not in used["axis"]]
        if free:
            suggestions.append(f"中轴改选（未用）：{'、'.join(free)}")
    if any(c["field"] == "font_display" for c in conflicts):
        suggestions.append("display 字体已撞车：把 --pair 换成 1/2/3 取族备用池")

    high = [c for c in conflicts if c["severity"] == "高"]
    result = {
        "ledger": ledger_path(a.dir),
        "history_count": len(entries),
        "selection": mine,
        "conflicts": conflicts,
        "suggestions": suggestions,
        "pass": not high,
    }

    if a.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"批次账本：{ledger_path(a.dir)}（已有 {len(entries)} 条记录）")
        print()
        print("本次选型指纹：")
        for k in ["anchor", "family", "surface", "variant", "pair", "axis", "layout", "ia", "font_display"]:
            if mine.get(k) is not None:
                print(f"  {LABEL.get(k, k):<14} {mine[k]}")
        print()
        if not entries:
            print("账本为空 —— 这是本批次第一个站，选型自由。")
        elif not conflicts:
            print("无冲突：本次指纹与同批次已交付的站全部错开。")
        else:
            print("冲突：")
            for c in conflicts:
                mark = "✗" if c["severity"] == "高" else "△"
                print(f"  {mark} {LABEL.get(c['field'], c['field'])}「{c['value']}」"
                      f"已被 {c['who']} 使用（{c['count']} 次）—— {c['severity']}冲突")
            print()
            print("建议：")
            for s in suggestions:
                print(f"  · {s}")
        print()
        print("结论：" + ("通过" if result["pass"] else "不通过 —— 存在高冲突，换掉再开工"))
    return 0 if result["pass"] else 1


_FAMILY_CACHE = {}


def _anchors_of_family(fam):
    if not _FAMILY_CACHE:
        try:
            idx = json.load(open(os.path.join(SKILL, "styles", "index.json"), encoding="utf-8"))
            for x in idx.get("anchors", []):
                _FAMILY_CACHE.setdefault(x.get("family"), []).append(x["slug"])
        except Exception:
            pass
    return set(_FAMILY_CACHE.get(fam, []))


def cmd_commit(a):
    doc = load(a.dir)
    if not a.name:
        print("--commit 需要 --name <站名>", file=sys.stderr)
        return 2
    if not a.anchor:
        print("--commit 需要 --anchor <slug>", file=sys.stderr)
        return 2
    entry = collect(a)
    entry["name"] = a.name
    entry["committed"] = datetime.now().isoformat(timespec="seconds")
    doc["entries"] = [e for e in doc["entries"] if e.get("name") != a.name] + [entry]
    p = save(a.dir, doc)
    print(f"已记录 {a.name} → {p}（共 {len(doc['entries'])} 条）")
    if not a.font_display:
        print("  注意：未带 --font-display —— R3 要求 display 字体全库唯一，"
              "不记录这一项，批次报告会判「未记录」不通过。", file=sys.stderr)
    return 0


def cmd_report(a):
    doc = load(a.dir)
    entries = doc["entries"]
    n = len(entries)
    if n == 0:
        print(f"账本为空：{ledger_path(a.dir)}")
        return 0

    def stat(field):
        vals = [e.get(field) for e in entries]
        return Counter(str(v) for v in vals if v is not None)

    rows = []
    anchor_c = stat("anchor")
    font_c = stat("font_display")
    surface_c = stat("surface")
    axis_c = stat("axis")
    family_c = stat("family")

    anchor_uniq = len(anchor_c) / n
    rows.append(("锚点唯一率", f"{len(anchor_c)}/{n} = {anchor_uniq:.0%}",
                 anchor_uniq >= MIN_ANCHOR_UNIQUE, f"阈值 ≥{MIN_ANCHOR_UNIQUE:.0%}"))
    rows.append(("底色档种类", f"{len(surface_c)} 种（{'、'.join(surface_c)}）",
                 len(surface_c) >= MIN_SURFACE_KINDS, f"阈值 ≥{MIN_SURFACE_KINDS} 种"))
    rows.append(("中轴种类", f"{len(axis_c)} 种（{'、'.join(axis_c)}）",
                 len(axis_c) >= MIN_AXIS_KINDS, f"阈值 ≥{MIN_AXIS_KINDS} 种"))
    # 种类数只能证明「不是全都一样」，挡不住「5 站里 4 站 left-rail」。
    # 占比上限才是「不塌缩」的直接表达。
    if axis_c:
        top_axis, top_n = axis_c.most_common(1)[0]
        axis_share = top_n / n
        rows.append(("中轴最大占比", f"{top_axis} {top_n}/{n} = {axis_share:.0%}",
                     axis_share <= MAX_AXIS_SHARE, f"阈值 ≤{MAX_AXIS_SHARE:.0%}"))
    else:
        rows.append(("中轴最大占比", f"未记录（0/{n}）", False, "--commit 时须带 --axis"))
    # display 字体没记录 = 这一项**没被校验**。不能显示成 100% —— 那等于
    # 「没有判据的必填项」，正是 v0.7 视觉签名失效的同一个坑。
    if font_c:
        font_uniq = len(font_c) / n
        rows.append(("display 唯一率", f"{len(font_c)}/{n} = {font_uniq:.0%}",
                     font_uniq >= MIN_FONT_UNIQUE, "阈值 100%"))
    else:
        rows.append(("display 唯一率", f"未记录（0/{n}）", False,
                     "--commit 时须带 --font-display"))
    fam_ratio = len(family_c) / n
    rows.append(("族覆盖", f"{len(family_c)} 族 / {n} 站 = {fam_ratio:.0%}",
                 fam_ratio >= MIN_FAMILY_RATIO, f"阈值 ≥{MIN_FAMILY_RATIO:.0%}"))

    fails = [r for r in rows if not r[2]]

    if a.json:
        print(json.dumps({
            "ledger": ledger_path(a.dir), "count": n,
            "anchor": dict(anchor_c), "font_display": dict(font_c),
            "surface": dict(surface_c), "axis": dict(axis_c), "family": dict(family_c),
            "checks": [{"name": r[0], "value": r[1], "pass": r[2], "rule": r[3]} for r in rows],
            "pass": not fails,
        }, ensure_ascii=False, indent=2))
    else:
        print(f"批次多样性报告 · {n} 个站 · {ledger_path(a.dir)}")
        print("─" * 62)
        for name, val, ok, rule in rows:
            print(f"  {'✓' if ok else '✗'} {name:<16} {val:<34} {rule}")
        print("─" * 62)
        print("  族分布   " + " / ".join(f"{k} {v}" for k, v in family_c.most_common()))
        print("  底色分布 " + " / ".join(f"{k} {v}" for k, v in surface_c.most_common()))
        print("  中轴分布 " + " / ".join(f"{k} {v}" for k, v in axis_c.most_common()))
        if font_c:
            print("  字体分布 " + " / ".join(f"{k} {v}" for k, v in font_c.most_common()))
        print("─" * 62)
        if fails:
            print(f"综合：不通过（{len(fails)} 项不达标）—— "
                  + "；".join(f"{r[0]} {r[1]}" for r in fails))
        else:
            print("综合：通过 —— 本批次风格差异度达标。")
    return 0 if not fails else 1


def main():
    ap = argparse.ArgumentParser(
        description="批次风格账本 —— 打破跨站同向收敛",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="退出码：0 通过 / 1 有冲突或不达标 / 2 用法错误",
    )
    ap.add_argument("--dir", default=".", help="工作区目录（账本落在此处的 .style-ledger.json）")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true", help="查重：本次选型是否与历史撞车")
    g.add_argument("--commit", action="store_true", help="记录一次交付")
    g.add_argument("--report", action="store_true", help="批次多样性报告")

    ap.add_argument("--name", help="站名（--commit 必填）")
    ap.add_argument("--anchor", help="锚点 slug")
    ap.add_argument("--family", help="族")
    ap.add_argument("--surface", help="底色档")
    ap.add_argument("--variant", help="变体轴 a/b/c/d")
    ap.add_argument("--pair", type=int, help="字体搭配序号 0-3")
    ap.add_argument("--axis", help="中轴")
    ap.add_argument("--layout", help="布局原型")
    ap.add_argument("--ia", help="信息架构原型")
    ap.add_argument("--font-display", dest="font_display", help="display 字体首族名")
    ap.add_argument("--json", action="store_true", help="机器可读输出")

    a = ap.parse_args()
    if a.check:
        return cmd_check(a)
    if a.commit:
        return cmd_commit(a)
    return cmd_report(a)


if __name__ == "__main__":
    sys.exit(main())
