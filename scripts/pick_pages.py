#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pick_pages.py — 由内容判据确定性推荐「页面粒度 + 页内导航」（Phase 1.7）。

为什么需要它：IA 四选一（portfolio / narrative / directory / conversion）只回答了
「这一页由哪些区块组成」，没回答「内容该分成几页」。缺了后半句，模型会不假思索地
输出同一个形状 —— 单个 index，条目再多也全塞进去，页面再长也只能一翻到底。

本脚本把这两个判断变成可复核的计算：读 `architectures/pagination.json` 的阈值，
按内容判据（条目数 / 深度 / 可否独立引用 / 并列主题数 / 区块数 / 查阅型区块数…）
推出结论，并给出逐条理由、被排除的档位与可观测的证伪条件。

与 pick_stack.py 同类：确定性、零依赖、可接 CI。阈值只改注册表，不改本脚本。

用法：
    python scripts/pick_pages.py --entries 3 --depth shallow --ia directory --blocks 2
    python scripts/pick_pages.py --entries 17 --depth deep --shareable --ia portfolio --blocks 3
    python scripts/pick_pages.py --entries 6 --depth medium --indexable \\
        --ia conversion --blocks 5 --lookup 1
    python scripts/pick_pages.py --host system-only
    python scripts/pick_pages.py --entries 40 --depth deep --shareable --json
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REG_PATH = os.path.join(os.path.dirname(HERE), "architectures", "pagination.json")

LEVELS = ["single", "master-detail", "multi-page"]
NAV_LEVELS = ["none", "anchor-jump", "sticky-toc", "section-rail"]
DEPTH_RANK = {"shallow": 0, "medium": 1, "deep": 2}


def load_registry(path=REG_PATH):
    """读阈值注册表 —— 判据的唯一真源。缺了就直说，不要用硬编码兜底。"""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:  # pragma: no cover - 只在仓库被改坏时触发
        print(f"读不到判据注册表 {path}：{e}", file=sys.stderr)
        print("阈值必须来自注册表；请先修好 architectures/pagination.json", file=sys.stderr)
        sys.exit(2)


# ------------------------------------------------------------------ 轴一：页面粒度
def decide_granularity(o, reg):
    """返回 (level, [理由…], {被排除档位: 理由})。"""
    th = reg["granularity"]["thresholds"]
    depth_ok = o.depth in th["depth_qualifying"]
    why, excl = [], {}

    if o.host == "system-only":
        return "n/a", ["交付形态 system-only：只出 token，不搭站"], {
            k: "system-only 不产出页面" for k in LEVELS}

    if o.themes >= th["themes_multi_page"]:
        level = "multi-page"
        why.append(f"themes={o.themes} ≥{th['themes_multi_page']}：除集合外还有并列的独立主题，"
                   f"塞进一页会互相打断，且各自需要能被单独链接")
        excl["single"] = "并列的独立主题无法在一页内互不打断"
        excl["master-detail"] = "只解决「条目」的拆分，没解决「并列主题」的拆分"
    elif (o.entries >= th["entries_master_detail"] and depth_ok
          and (o.shareable or o.indexable)):
        level = "master-detail"
        trig = "可独立分享" if o.shareable else "需被搜索引擎单独收录"
        why.append(f"entries={o.entries} ≥{th['entries_master_detail']} 且 depth={o.depth} "
                   f"且{trig}：用户会「只要那一条」，需要一个能落到单条的 URL")
        excl["single"] = f"条目多且有独立深度内容，单页会把每条压成缩略"
        excl["multi-page"] = "除该集合外没有并列的独立主题"
    elif o.entries >= th["entries_master_detail_forced"] and depth_ok:
        level = "master-detail"
        why.append(f"entries={o.entries} ≥{th['entries_master_detail_forced']}：条目数已多到"
                   f"单页扫读失效，索引页本身要能被筛、能定位到某一条")
        excl["single"] = f"条目数 {o.entries} 已超出单页可扫读的范围"
        excl["multi-page"] = "除该集合外没有并列的独立主题"
    else:
        level = "single"
        if o.entries == 0:
            why.append("没有条目集合：内容是一个整体（一段叙事 / 一个转化动作），本来就是一页")
        else:
            why.append(f"entries={o.entries} / depth={o.depth}：条目少或浅，拆页只会得到几个空洞的页面")
        excl["master-detail"] = (f"entries={o.entries} <{th['entries_master_detail']} "
                                 f"或 depth={o.depth} 不够，详情页撑不起来")
        excl["multi-page"] = "没有并列的独立主题"

    # 否决：非技术维护者 + 不能静态生成
    for v in reg["granularity"]["veto"]:
        if o.maintainer == "nontech" and not o.static_gen and level != "single":
            why.append(f"⚠ 否决 {v['id']}：{v['why']} —— 本次由 {level} 降级为 single")
            excl[level] = f"{v['id']}：{o.maintainer} 维护者 + 不能静态生成"
            level = "single"
        break

    if level == "single" and o.maintainer == "nontech" and not o.static_gen:
        why.append("（本就是 single，否决条件未触发额外降级）")

    return level, why, excl


# ------------------------------------------------------------------ 轴二：页内导航
def decide_nav(o, reg, gran):
    """返回 (level, [理由…], {被排除档位: 理由})。"""
    th = reg["inPageNav"]["thresholds"]
    why, excl = [], {}

    if gran == "n/a":
        return "n/a", ["system-only 不产出页面"], {k: "无页面" for k in NAV_LEVELS}

    # 否决优先于规则：转化页不给整页目录
    for v in reg["inPageNav"]["veto"]:
        if v["id"] == "V1" and o.ia == "conversion" and o.lookup == 0 and o.blocks < 7:
            return "none", [
                f"否决 {v['id']}：{v['why']}",
                f"（ia=conversion, lookup={o.lookup}, blocks={o.blocks} <7）"
            ], {"anchor-jump": "转化页无查阅型区块时，目录会打断说服链",
                "sticky-toc": "同上，且区块数不足以支撑目录",
                "section-rail": "同上，且区块数不足以支撑章节轨"}

    if o.blocks <= th["blocks_none_max"]:
        return "none", [f"blocks={o.blocks} ≤{th['blocks_none_max']}：页面真的短，加导航只会是噪音"], \
            {k: "页面区块数不足以支撑导航" for k in NAV_LEVELS[1:]}

    if o.screens >= th["screens_rail_min"] or o.blocks >= th["blocks_rail_min"]:
        level = "section-rail"
        why.append(f"blocks={o.blocks} / screens={o.screens}：超长页，需要常驻章节轨 + 进度指示")
    elif o.blocks >= th["blocks_sticky_min"]:
        level = "sticky-toc"
        why.append(f"blocks={o.blocks} ≥{th['blocks_sticky_min']}：需要跟随滚动、带当前位置高亮的目录")
    elif o.blocks >= th["blocks_anchor_min"] and (o.lookup >= 1 or o.linear):
        level = "anchor-jump"
        if o.lookup >= 1:
            why.append(f"blocks={o.blocks} 且 lookup={o.lookup}：页面里有查阅型区块"
                       f"（FAQ / 规格 / 合规），用户是「来查」的 —— 给一条直达捷径")
        else:
            why.append(f"blocks={o.blocks} 且为线性叙事：章节锚点既是导航也是阅读节奏")
    else:
        level = "none"
        why.append(f"blocks={o.blocks}：区块不多且无查阅型区块、非线性长页，导航收益低于噪音")

    order = NAV_LEVELS.index(level)
    for k in NAV_LEVELS:
        if k == level:
            continue
        excl[k] = "档位过重（会挤占内容）" if NAV_LEVELS.index(k) > order else "档位过轻（解决不了定位问题）"
    return level, why, excl


# ------------------------------------------------------------------ 输出
def falsify(reg, gran, nav):
    out = []
    if gran in reg["falsify"]:
        out += reg["falsify"][gran]
    if nav != "n/a":
        out += reg["falsify"]["nav"]
    return out


def fmt(o, reg, gran, gwhy, gexcl, nav, nwhy, nexcl):
    L = []
    A = L.append
    A("pick_pages — 页面粒度与页内导航（Phase 1.7）")
    A("=" * 68)
    A("输入判定")
    A(f"  P1 条目数 {o.entries} ｜ P2 深度 {o.depth} ｜ P3 可分享 {'是' if o.shareable else '否'}"
      f" ｜ P4 可收录 {'是' if o.indexable else '否'}")
    A(f"  P5 并列主题 {o.themes} ｜ P6 维护者 {o.maintainer} ｜ P7 可静态生成 {'是' if o.static_gen else '否'}")
    A(f"  N1 区块数 {o.blocks} ｜ N2 查阅型区块 {o.lookup} ｜ N3 线性 {'是' if o.linear else '否'}"
      f" ｜ N4 预估屏数 {o.screens or '—'}")
    A(f"  IA {o.ia} ｜ 交付形态 {o.host}")
    A("")
    A("轴一 · 页面粒度")
    meta = reg["granularity"]["levels"].get(gran, {})
    A(f"  → {gran}（{meta.get('name','')}）")
    if meta.get("pages") not in (None, ""):
        A(f"     页面清单：{meta.get('pages')}")
    if meta.get("shape"):
        A(f"     产物形状：{meta.get('shape')}")
    for w in gwhy:
        A(f"     · {w}")
    if gexcl:
        A("     被排除：")
        for k, w in gexcl.items():
            A(f"       × {k:<14} {w}")
    A("")
    A("轴二 · 页内导航")
    nmeta = reg["inPageNav"]["levels"].get(nav, {})
    A(f"  → {nav}（{nmeta.get('name','')}）")
    if nmeta.get("note"):
        A(f"     {nmeta.get('note')}")
    for w in nwhy:
        A(f"     · {w}")
    if nexcl:
        A("     被排除：")
        for k, w in nexcl.items():
            A(f"       × {k:<14} {w}")
    A("")
    A("证伪条件（交付后拿事实检验；任一成立就回头改判）")
    for f in falsify(reg, gran, nav):
        A(f"  · {f}")
    A("")
    A("→ 把两行结论写进 content-profile.md 的「页面粒度与页内导航」段（格式见 architectures/granularity.md §4.2），")
    A("  交付前跑 python scripts/audit_tokens.py --site <站点目录> 校验声明与产物一致。")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description="由内容判据确定性推荐页面粒度与页内导航")
    ap.add_argument("--entries", type=int, default=0, help="同一集合的条目数（无集合记 0）")
    ap.add_argument("--depth", choices=["shallow", "medium", "deep"], default="shallow",
                    help="条目平均内容深度")
    ap.add_argument("--shareable", action="store_true", help="条目需要独立 URL（能被单独分享）")
    ap.add_argument("--indexable", action="store_true", help="条目需要被搜索引擎单独收录")
    ap.add_argument("--themes", type=int, default=0,
                    help="除集合外内容量足以独占一页的并列独立主题数")
    ap.add_argument("--maintainer", choices=["nontech", "tech"], default="tech")
    ap.add_argument("--static-gen", dest="static_gen", action="store_true", default=True,
                    help="能用单一数据源静态生成多页（默认）")
    ap.add_argument("--no-static-gen", dest="static_gen", action="store_false",
                    help="不能静态生成多页")
    ap.add_argument("--ia", choices=["portfolio", "narrative", "directory", "conversion", "none"],
                    default="none", help="已定的 IA 原型（仅用于兜底与提示）")
    ap.add_argument("--blocks", type=int, default=0, help="首页区块 / 章节数")
    ap.add_argument("--lookup", type=int, default=0, help="查阅型区块数（FAQ / 规格 / 合规 / 索引 / 附录）")
    ap.add_argument("--linear", action="store_true", help="线性阅读（叙事长页）")
    ap.add_argument("--screens", type=int, default=0, help="预估屏数（可选）")
    ap.add_argument("--host", choices=["standalone", "embedded", "system-only"], default="standalone")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    reg = load_registry()
    gran, gwhy, gexcl = decide_granularity(a, reg)
    nav, nwhy, nexcl = decide_nav(a, reg, gran)

    if a.json:
        print(json.dumps({
            "input": vars(a),
            "granularity": {"level": gran, "reasons": gwhy, "excluded": gexcl,
                            "meta": reg["granularity"]["levels"].get(gran, {})},
            "inPageNav": {"level": nav, "reasons": nwhy, "excluded": nexcl,
                          "meta": reg["inPageNav"]["levels"].get(nav, {})},
            "falsify": falsify(reg, gran, nav),
        }, ensure_ascii=False, indent=2))
    else:
        print(fmt(a, reg, gran, gwhy, gexcl, nav, nwhy, nexcl))
    return 0


if __name__ == "__main__":
    sys.exit(main())
