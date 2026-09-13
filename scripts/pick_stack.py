#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pick_stack.py — 由「网页需求」确定性推荐技术栈（Phase 1.5）。

为什么需要它：用 AI 生成网页时，模型会不假思索地输出同一套骨架
（Astro + src/pages/index.astro + src/styles/tokens.css + src/data/*.json），
于是不同内容产出的是**同一个形状换文案**——本质上只是「不同的 Markdown 组织器」。
本脚本把「需求 → 技术栈」变成可复核的判断：先按硬约束**排除**，再对剩下的评分定序，
输出排序 + 逐条理由 + 被排除项 + 一段可直接落进 tech-stack.md 的结论。

与 emit_tokens.py 同类：确定性、零依赖、可接 CI。

用法：
    python scripts/pick_stack.py --pages single --interaction light --maintainer nontech \\
        --data single-json --budget lean
    python scripts/pick_stack.py --host embedded --host-stack next
    python scripts/pick_stack.py --render ssr --i18n multi --json

参数与 techstack.md 的 D1–D8 一一对应。无第三方依赖。
"""
from __future__ import annotations

import argparse
import json
import re
import sys

# ------------------------------------------------------------------ 候选栈
CANDIDATES = ["plain-html", "astro", "eleventy", "vite-vanilla", "next", "nuxt", "hugo"]

STACK_META = {
    "plain-html":   {"name": "纯静态 HTML + CSS", "dir": "index.html + style.css + app.js（可选）"},
    "astro":        {"name": "Astro",             "dir": "src/pages/ + src/components/ + src/styles/"},
    "eleventy":     {"name": "11ty",              "dir": "src/ + _includes/ + .eleventy.js"},
    "vite-vanilla": {"name": "Vite + 原生 TS",    "dir": "index.html + src/main.ts + vite.config.ts"},
    "next":         {"name": "Next.js",           "dir": "app/ + components/ + next.config.js"},
    "nuxt":         {"name": "Nuxt",              "dir": "pages/ + components/ + nuxt.config.ts"},
    "hugo":         {"name": "Hugo",              "dir": "content/ + layouts/ + hugo.toml"},
}

# 宿主栈名 → 候选栈 id（embedded 时使用）
HOST_STACK_MAP = {
    "plain": "plain-html", "plain-html": "plain-html", "html": "plain-html",
    "astro": "astro", "eleventy": "eleventy", "11ty": "eleventy",
    "vite": "vite-vanilla", "vite-vanilla": "vite-vanilla", "vanilla": "vite-vanilla",
    "next": "next", "nextjs": "next", "nuxt": "nuxt",
    "hugo": "hugo",
}


def h_exclude(opts):
    """硬约束排除（顺序与 techstack.md §3 一致）。返回 {candidate: reason}。"""
    out = {}

    def ban(cands, reason):
        for c in cands:
            out.setdefault(c, reason)

    if opts.host == "embedded":
        keep = HOST_STACK_MAP.get(opts.host_stack or "astro")
        ban([c for c in CANDIDATES if c != keep],
            f"embedded：服从宿主栈（{keep}），不另起一套")
        return out, keep

    if opts.host == "system-only":
        return {c: "system-only：只出 token，不搭站" for c in CANDIDATES}, None

    if opts.render == "ssr":
        ban(["plain-html", "astro", "eleventy", "hugo", "vite-vanilla"],
            "render=ssr：纯静态方案无服务端渲染")
    if opts.maintainer == "nontech":
        ban(["astro", "eleventy", "next", "nuxt", "hugo", "vite-vanilla"],
            "maintainer=nontech：维护者不能碰命令行 / Node 构建链")
    if opts.interaction == "heavy":
        ban(["plain-html", "eleventy", "hugo"],
            "interaction=heavy：重交互需要模块系统与状态管理")
    if opts.pages == "many":
        ban(["plain-html", "vite-vanilla"],
            "pages=many：无模板复用 → 维护成本指数上升")
    if opts.i18n == "multi":
        ban(["plain-html", "hugo"],
            "i18n=multi：路由级 i18n 需框架原生支持")
    if opts.budget == "lean" and opts.pages == "single":
        ban(["next", "nuxt"],
            "budget=lean + pages=single：框架运行时与首屏预算冲突")
    return out, None


def score(opts):
    """对未被排除的候选评分。返回 {candidate: (score, [理由…])}。"""
    S, R = {}, {}

    def add(c, pts, why):
        if pts == 0:
            return
        S[c] = S.get(c, 0) + pts
        R.setdefault(c, []).append(("+" if pts > 0 else "") + f"{pts:g} {why}")

    # plain-html
    add("plain-html", 3 if opts.pages == "single" else 0, "单页，无需路由")
    add("plain-html", 2 if opts.interaction in ("none", "light") else 0, "交互轻，原生 JS 够用")
    add("plain-html", 2 if opts.maintainer == "nontech" else 0, "非技术维护者，零构建")
    add("plain-html", 1 if opts.data in ("inline", "single-json") else 0, "数据简单，运行期读取即可")
    add("plain-html", 2 if opts.budget == "lean" else 0, "首屏预算紧，无运行时")
    add("plain-html", -2 if opts.pages == "few" else 0, "多页无模板复用，改一处要改 N 处")

    # astro
    add("astro", 3 if opts.pages in ("few", "many") else 0, "多页内容站，组件 + 模板复用")
    add("astro", 2 if opts.data in ("single-json", "cms") else 0, "构建期数据层天然适配")
    add("astro", 2 if opts.i18n == "multi" else 0, "原生 i18n 路由")
    add("astro", 1 if opts.interaction == "light" else 0, "islands：只给需要的组件注水")
    add("astro", 1 if opts.budget == "normal" else 0, "默认零 JS，性能可控")
    add("astro", -1 if opts.pages == "single" else 0, "单页用 SSG 偏重")

    # eleventy
    add("eleventy", 2 if opts.pages == "many" else 0, "大量页面，产物干净")
    add("eleventy", 2 if opts.data == "single-json" else 0, "JSON/Markdown 驱动的静态生成")
    add("eleventy", 1 if opts.interaction == "none" else 0, "几乎无交互")

    # vite-vanilla
    add("vite-vanilla", 3 if opts.interaction == "heavy" else 0, "重交互：图表 / Canvas / 滚动动画")
    add("vite-vanilla", 2 if opts.budget == "lean" else 0, "无框架运行时，产物小")
    add("vite-vanilla", 1 if opts.pages == "single" else 0, "单页 + 重交互的最优解")
    add("vite-vanilla", -1 if opts.pages == "many" else 0, "多页需自搭路由")

    # next
    add("next", 3 if opts.render == "ssr" else 0, "SSR / 鉴权 / 个性化")
    add("next", 2 if opts.interaction == "heavy" else 0, "重交互 + 多页")
    add("next", 2 if opts.data == "api" else 0, "运行时数据源")
    add("next", 2 if opts.i18n == "multi" else 0, "i18n 路由成熟")
    add("next", 1 if opts.pages == "many" else 0, "多页应用结构清晰")
    add("next", 1 if opts.maintainer == "team" else 0, "团队协作生态完整")

    # nuxt（与 next 对等，团队已用 Vue 时优先）
    add("nuxt", 3 if opts.render == "ssr" else 0, "SSR / 鉴权 / 个性化")
    add("nuxt", 2 if opts.interaction == "heavy" else 0, "重交互 + 多页")
    add("nuxt", 2 if opts.data == "api" else 0, "运行时数据源")
    add("nuxt", 2 if opts.i18n == "multi" else 0, "i18n 路由成熟")
    add("nuxt", 1 if opts.pages == "many" else 0, "多页应用结构清晰")

    # hugo
    add("hugo", 3 if opts.pages == "many" else 0, "数百上千页，构建极快")
    add("hugo", 2 if opts.interaction == "none" else 0, "纯静态内容")
    add("hugo", 1 if opts.data == "single-json" else 0, "数据文件驱动")

    return S, R


def recommend(opts):
    excl, forced = h_exclude(opts)

    if opts.host == "system-only":
        return {"mode": "system-only", "ranked": [], "excluded": excl,
                "conclusion": "system-only：不搭站，跳过技术栈选型，直接进 G3 出 token。"}

    if opts.host == "embedded":
        c = forced
        return {"mode": "embedded", "ranked": [{"stack": c, "score": None, "reasons":
                [f"服从宿主栈 {c}（host-align.md）"]}], "excluded": excl,
                "conclusion": f"embedded：服从宿主栈 `{c}`，本页在其内部落地，不引入第二套构建链。"}

    survivors = [c for c in CANDIDATES if c not in excl]
    if not survivors:
        return {"mode": "contradiction", "ranked": [], "excluded": excl,
                "conclusion": "输入自相矛盾：所有候选栈都被排除。请回 G0 复核需求"
                              "（常见冲突：非技术维护者 + 重交互 / 大量页面 + 需要 SSR）。"}

    S, R = score(opts)
    ranked = sorted(survivors, key=lambda c: (-S.get(c, 0), CANDIDATES.index(c)))
    out = [{"stack": c, "score": S.get(c, 0), "reasons": R.get(c, [])} for c in ranked]
    top = ranked[0]
    why = "；".join(re.sub(r"^[+-]?\d+(?:\.\d+)?\s*", "", r) for r in R.get(top, [])) or "无强偏好，取默认"
    return {"mode": "ranked", "ranked": out, "excluded": excl,
            "conclusion": f"选定 `{top}`。依据：{why}。"}


def fmt(opts, res):
    L = []
    A = L.append
    A("pick_stack — 技术栈选型（Phase 1.5）")
    A("=" * 68)
    A("输入判定（D1–D8）")
    A(f"  D1 页面规模 {opts.pages} ｜ D2 交互 {opts.interaction} ｜ D3 维护者 {opts.maintainer}")
    A(f"  D4 数据源 {opts.data} ｜ D5 形态 {opts.host} ｜ D6 多语言 {opts.i18n}")
    A(f"  D7 渲染 {opts.render} ｜ D8 性能预算 {opts.budget}")
    A("")
    if res["ranked"]:
        A("候选排序")
        for i, r in enumerate(res["ranked"], 1):
            sc = "—" if r["score"] is None else f"{r['score']:g}"
            meta = STACK_META.get(r["stack"], {})
            A(f"  {i}. {r['stack']:<13} {meta.get('name',''):<18} 得分 {sc}")
            A(f"     目录形状：{meta.get('dir','')}")
            for why in r["reasons"]:
                A(f"       {why}")
        A("")
    if res["excluded"]:
        A("被排除")
        for c, why in res["excluded"].items():
            A(f"  × {c:<13} {why}")
        A("")
    A("结论")
    A(f"  {res['conclusion']}")
    A("")
    A("→ 把上面的判定与结论写进 tech-stack.md，并补 3 条可观测的证伪条件（techstack.md §5）。")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description="由网页需求确定性推荐技术栈")
    ap.add_argument("--pages", choices=["single", "few", "many"], default="few")
    ap.add_argument("--interaction", choices=["none", "light", "heavy"], default="light")
    ap.add_argument("--maintainer", choices=["nontech", "tech", "team"], default="tech")
    ap.add_argument("--data", choices=["inline", "single-json", "cms", "api"], default="inline")
    ap.add_argument("--host", choices=["standalone", "embedded", "system-only"], default="standalone")
    ap.add_argument("--host-stack", default="astro",
                    help="embedded 时的宿主栈（astro/next/nuxt/plain/eleventy/hugo）")
    ap.add_argument("--i18n", choices=["none", "multi"], default="none")
    ap.add_argument("--render", choices=["static", "ssr"], default="static")
    ap.add_argument("--budget", choices=["lean", "normal"], default="normal")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    res = recommend(a)
    if a.json:
        print(json.dumps({"input": vars(a), **res}, ensure_ascii=False, indent=2))
    else:
        print(fmt(a, res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
