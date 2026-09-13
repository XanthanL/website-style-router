#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""audit_tokens.py — 对 MASTER.md / tokens.css 做「审美数值」审计。

与 validate_skill.py 的分工：
  validate_skill.py  → 这个 skill 仓库自己是否规范（frontmatter / 引用 / 卫生）
  audit_tokens.py    → 产出的设计系统是否「站得住」（字阶等比、行长、对比度…）

checklist.md 查的是流程与形状合规；本脚本查的是**数值**——页面好不好看里
能被量化的那部分。判据分级 F 致命 / I 重要 / S 建议，含义见 design-qa.md。

F6（v0.7 新增）是**反同质化**判据：检查 `--font-display` / `--font-body` 是否
真的做了搭配（首族具名、二者不同），而不是默认继承一个通用栈。只查数值不查字体
时，40 个锚点会产出观感雷同的页面 —— 数值全过、风格全同。

F14 / F15（v0.9 新增）是**结构**判据，走 `--site <站点目录>`：
  F14 页面粒度 —— 声明的 single / master-detail / multi-page 与实际页面文件数是否一致；
      未声明即失败（没有判据的「必填」等于不必填）。
  F15 页内导航 —— 声明的 none / anchor-jump / sticky-toc / section-rail 与实际锚点是否一致；
      声明了导航却没有可达锚点、或长页声明 none，都算失败。
  编号从 F11 跳到 F14，是为了**避开 validate_skill.py 的 F12/F13** —— 两个脚本各自
  维护独立的 F 编号，重号会让引用产生歧义（见 CONCEPTS.md 的编号歧义一节）。

用法：
    python scripts/audit_tokens.py examples/vivian-peng-portfolio/design-system/MASTER.md
    python scripts/audit_tokens.py path/to/tokens.css --json
    python scripts/audit_tokens.py --site examples/vivian-peng-portfolio     # F14/F15
    python scripts/audit_tokens.py --batch <批次目录>                        # F11

退出码：有 F 级不通过 → 1；否则 0。
无第三方依赖。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter

# ------------------------------------------------------------------ 颜色
HEX_RE = re.compile(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b")
RGB_RE = re.compile(r"rgba?\(\s*([\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)")


def parse_color(v: str):
    """返回 ((r,g,b), alpha) 0..1；无法解析返回 (None, None)。

    alpha 必须一起返回 —— 半透明文字色要**合成到底色上**再算对比度，
    否则 rgba(23,23,15,.6) 会被误判成 16:1 的纯黑。
    """
    v = (v or "").strip()
    m = HEX_RE.search(v)
    if m:
        h = m.group(1)
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        rgb = tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
        a = int(h[6:8], 16) / 255 if len(h) == 8 else 1.0
        return rgb, a
    m = RGB_RE.search(v)
    if m:
        rgb = tuple(min(1.0, max(0.0, float(x) / 255)) for x in m.groups()[:3])
        am = re.search(r"rgba\([^)]*[,/]\s*([\d.]+)\s*\)", v)
        a = min(1.0, max(0.0, float(am.group(1)))) if am else 1.0
        return rgb, a
    return None, None


def over(fg, a, bg):
    """把半透明前景合成到不透明底色上，返回实心色。"""
    if a is None or a >= 1.0 or bg is None:
        return fg
    return tuple(a * f + (1 - a) * b for f, b in zip(fg, bg))


def rel_lum(rgb) -> float:
    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b) -> float:
    la, lb = rel_lum(a), rel_lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


VAR_RE = re.compile(r"--([a-zA-Z0-9\-_]+)\s*:\s*([^;{}]+)[;}]")
# MASTER.md 常见的表格写法： | `--bg` | `#FFFFFF` | 纸白 | 依据 |
TABLE_RE = re.compile(r"\|\s*`--([a-zA-Z0-9\-_]+)`\s*\|\s*`?([^|`]+?)`?\s*\|")

# ------------------------------------------------------------------ 报告
class Report:
    def __init__(self, path):
        self.path = path
        self.items = []

    def add(self, level, code, msg, hint=""):
        self.items.append(dict(level=level, code=code, msg=msg, hint=hint))

    def err(self, code, msg, hint=""):
        self.add("F", code, msg, hint)

    def warn(self, code, msg, hint=""):
        self.add("I", code, msg, hint)

    def info(self, code, msg, hint=""):
        self.add("S", code, msg, hint)

    @property
    def fails(self):
        return [x for x in self.items if x["level"] == "F"]


def collect(text: str):
    """两种写法都认：CSS 块 `--x: v;` 与 markdown 表格 `| `--x` | `v` |`。"""
    v = {}
    for m in VAR_RE.finditer(text):
        v.setdefault(m.group(1), m.group(2).strip())
    for m in TABLE_RE.finditer(text):
        val = m.group(2).strip()
        if val and not val.startswith("--") and "<" not in val:
            v.setdefault(m.group(1), val)
    return v


# 角色 → 常见同义词。规范名（design-qa.md 的词汇表）优先，同义词兜底 ——
# 目的是「自有命名也能被审计」，同时让偏离规范这件事可见（会出 S 级提示）。
ROLES = {
    "bg":           ("paper", "background", "canvas", "base"),
    "bg-soft":      ("paper-2", "surface-2", "bg-alt", "paper-1"),
    "fg":           ("ink", "text", "foreground", "body-color"),
    "muted":        ("ink-60", "text-muted", "muted-1", "grey", "gray"),
    "line":         ("ink-12", "rule", "border", "hairline", "divider"),
    "accent-ink":   ("accent-text", "link", "link-color"),
    "measure":      ("container", "max-width", "wrap", "page-width"),
    "prose-width":  ("measure-text", "line-length", "reading-width"),
}
CANONICAL = {
    "bg", "bg-soft", "fg", "muted", "line", "accent", "accent-ink", "accent-soft",
    "measure", "prose-width", "gutter", "axis", "radius", "shadow", "ease", "dur-fast", "dur-normal",
    "surface", "variant",
}


def make_role(V):
    nonce = []

    def role(name):
        if name in V:
            return V[name]
        for alt in ROLES.get(name, ()):
            if alt in V:
                nonce.append((name, alt))
                return V[alt]
        return None

    role.aliases_used = nonce
    return role


def px(v):
    m = re.match(r"^\s*(-?[\d.]+)\s*px\s*$", v or "")
    return float(m.group(1)) if m else None


def main():
    ap = argparse.ArgumentParser(description="设计系统 token 的审美数值审计")
    ap.add_argument("file", nargs="?", help="MASTER.md 或 tokens.css")
    ap.add_argument("--anchor", help="同时校验「产出的 token 是否与锚点签名一致」")
    ap.add_argument("--batch", help="批次模式：扫描该目录下所有站，检查跨站差异度（F11）")
    ap.add_argument("--site", help="站点目录：校验页面粒度与页内导航的声明与产物是否一致（F14/F15）")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.batch:
        return cmd_batch(a.batch, a.json)
    if a.site:
        return cmd_site(a.site, a.json)
    if not a.file:
        ap.error("需要给出 file，或使用 --batch <目录> / --site <站点目录>")

    if not os.path.exists(a.file):
        print(f"文件不存在：{a.file}", file=sys.stderr)
        return 2
    text = open(a.file, encoding="utf-8", errors="replace").read()
    V = collect(text)
    R = Report(a.file)

    if not V:
        R.err("F0", "没有解析到任何 CSS 自定义属性", "确认是 MASTER.md 的 token 段或 tokens.css")
        return emit(R, a.json)

    get = make_role(V)

    # ---------------- F1 中轴
    axis = get("axis")
    if axis is None:
        R.err("F1", "缺 `--axis`（中轴未定）", "取值 left-rail / center-axis / split，见 layouts.md")
    else:
        ok = any(k in axis for k in ("left-rail", "center-axis", "split"))
        if not ok:
            R.err("F1", f"`--axis: {axis}` 取值非法", "只能 left-rail / center-axis / split")

    # ---------------- F2 对比度
    c_bg, _a_bg = parse_color(get("bg") or "")
    pairs = [
        ("fg", "fg", 7.0, "正文主色"),
        ("muted", "muted", 4.5, "次要文字"),
        ("accent-ink", "accent-ink", 4.5, "链接 / 强调文字"),
        ("accent", "accent", 3.0, "大字号 / 装饰用强调色"),
    ]
    if c_bg is None:
        R.info("F2", "`--bg` 无法解析（非 hex/rgb），对比度未校验", "若用 oklch() 请同时给出 hex 值")
    else:
        for key, label, need, why in pairs:
            raw = get(key)
            if raw is None:
                R.info("F2", f"未定义 `--{key}`，跳过对比度检查", "")
                continue
            rgb, al = parse_color(raw)
            if rgb is None:
                R.info("F2", f"`--{key}` 无法解析（{raw[:24]}），未校验", "")
                continue
            solid = over(rgb, al, c_bg)
            c = contrast(solid, c_bg)
            note = f"（原值带 {al:.0%} 透明度，已合成到底色上计算）" if (al is not None and al < 1) else ""
            if c < need:
                R.err("F2", f"`--{key}`（{why}）对 `--bg` 仅 {c:.2f}:1，低于 {need}:1{note}",
                      "调亮/调暗该色，或让 emit_tokens.py 按 solve_contrast 重新求解")
            elif c > need * 3.2 and key == "muted":
                R.warn("F2", f"`--muted` 对 `--bg` 达 {c:.1f}:1 —— 过黑，不像次要文字{note}",
                       "次要文本取「刚好过 4.5:1」的最亮档更自然")

    # ---------------- F3 字阶
    med_ratio = None
    fs_all = {k: v for k, v in V.items() if k.startswith("fs-")}
    fs = {k: px(v) for k, v in fs_all.items()}
    fs = {k: v for k, v in fs.items() if v}
    fluid = sorted(k for k in fs_all if k not in fs)
    if not fs_all:
        R.warn("F3", "没有 `--fs-*` 字阶变量", "用 emit_tokens.py 生成，别手编")
    else:
        if len(fs_all) > 6:
            R.err("F3", f"字阶 {len(fs_all)} 级，超过 6 级上限", f"现有：{sorted(fs_all)}")
        base_k = "fs-base" if "fs-base" in fs else ("fs-body" if "fs-body" in fs else None)
        disp_k = "fs-display" if "fs-display" in fs else ("fs-mega" if "fs-mega" in fs else None)
        if len(fs) >= 4:
            ordered = sorted(fs.items(), key=lambda kv: kv[1])
            body = [(k, v) for k, v in ordered if k != disp_k]
            ratios = [round(b[1] / a_[1], 4) for a_, b in zip(body, body[1:])]
            if ratios:
                med_ratio = sorted(ratios)[len(ratios) // 2]
                bad = [f"{r:.3f}" for r in ratios if not (0.9 * med_ratio <= r <= 1.1 * med_ratio)]
                R.add("S", "F3", f"字阶公比 ≈ {med_ratio:.3f}"
                                f"（{len(fs_all)} 级：{', '.join(f'{v:g}' for _, v in ordered)}"
                                + (f"；弹性值 {', '.join(fluid)} 未计入" if fluid else "") + "）")
                if bad:
                    R.err("F3", f"字阶不是等比：偏离的相邻比值 {', '.join(bad)}",
                          "模块化字阶才能形成秩序感；见 typography.md §1")
                if med_ratio < 1.15:
                    R.err("F3", f"字阶公比 {med_ratio:.3f} 过小，层级会塌陷", "低于 1.15 用户分不出标题与正文")
                if med_ratio > 1.7:
                    R.warn("F3", f"字阶公比 {med_ratio:.3f} 过大，小字会碎", "中文小字低于 12px 不可读")
        elif fluid:
            R.info("F3", f"字阶多为弹性值（{', '.join(fluid)}），等比性未校验",
                   "clamp() 字号无法静态比较公比；确认中间档仍按同一公比取值")
        d = fs.get(disp_k) if disp_k else None
        others = [v for k, v in fs.items() if k != disp_k]
        if d and others and d <= max(others):
            R.err("F3", "最大字号未明显拉开", "display 必须显著大于次大字号（typography.md §1）")
        b = fs.get(base_k) if base_k else None
        if b and b < 14:
            R.err("F3", f"正文基准 {b:g}px 偏小", "中文正文 ≥ 15px，西文 ≥ 14px")
        tiny = [(k, v) for k, v in fs.items() if v < 11]
        if tiny:
            R.warn("F3", f"存在 <11px 的字号：{tiny}", "仅可用于装饰性微标签")

    # ---------------- F4 间距栅格
    sp = {k: px(v) for k, v in V.items() if k.startswith("space-") or k.startswith("sp-")}
    sp = {k: v for k, v in sp.items() if v}
    if len(sp) >= 2:
        base = min(sp.values())
        off = {k: v for k, v in sp.items() if base and abs(v / base - round(v / base)) > 1e-6}
        if off:
            R.err("F4", f"间距未全部落在 {base:g}px 栅格上：{off}",
                  "所有纵向/横向间距取栅格整数倍，混入栅格外数值会显得不整齐")
        else:
            R.add("S", "F4", f"间距栅格 {base:g}px，{len(sp)} 级全部对齐")
    else:
        R.info("F4", "间距未 token 化为 `--space-*`，栅格未校验",
               "把间距写成变量（规范化更强，也便于跨区块复用）")
    g = px(get("gutter") or "")
    if g is not None and g < 16:
        R.warn("F4", f"页面边距 `--gutter: {g:g}px` 偏窄",
               "移动端页面边距 ≥16px；--gutter 独立于节奏栅格，不参与上面的整数倍检查")

    # ---------------- I1 行长
    m = None
    prose = get("prose-width")
    if prose:
        m = re.match(r"^\s*([\d.]+)\s*ch\s*$", prose)
        if m:
            c = float(m.group(1))
            if not (44 <= c <= 80):
                R.warn("I1", f"`--prose-width: {c:g}ch` 超出 44–80ch",
                       f"约合 {c/2:.0f} 汉字/行；过窄换行频繁，过宽回行失焦")
            else:
                R.add("S", "I1", f"行长 {c:g}ch ≈ {c/2:.0f} 汉字/行（在带内）")
        else:
            R.info("I1", f"`--prose-width: {prose}` 非 ch 单位", "正文列宽用 ch 或 em，不要用 px")
    else:
        R.warn("I1", "未定义 `--prose-width`（正文列宽目标）", "见 typography.md §4")

    # ---------------- I2 行高
    lh = {k: v for k, v in V.items() if k.startswith("lh-") or k.startswith("leading-")}
    def num(x):
        try:
            return float(str(x).strip())
        except (ValueError, TypeError):
            return None
    def lh_pick(*names):
        for n in names:
            if n in lh:
                return num(lh[n])
        return None
    lhb = lh_pick("lh-base", "lh-body", "leading-base", "leading-body")
    lhd = lh_pick("lh-display", "lh-mega", "leading-display")
    if lhb is not None and not (1.4 <= lhb <= 2.0):
        R.warn("I2", f"正文行高 {lhb:g} 超出 1.4–2.0",
               "中文主站建议 1.7–1.95；低于 1.4 会挤，高于 2.0 段落会散")
    if lhd is not None and lhd > 1.3:
        R.warn("I2", f"标题行高 {lhd:g} 偏大（应 ≤1.3）", "大字行高倍数必须小于正文")
    if lhb is not None and lhd is not None and lhd >= lhb:
        R.err("I2", f"标题行高 {lhd:g} ≥ 正文行高 {lhb:g}", "行高必须随字号增大而收紧")
    for k, v in lh.items():
        if v and re.match(r"^\s*[\d.]+px\s*$", str(v)):
            R.warn("I2", f"`--{k}` 用了 px 单位（{v}）", "行高必须无单位，否则子元素继承固定像素")

    # ---------------- I3 强调色数量
    accents = [k for k in V if re.match(r"^accent(-\w+)?$", k)]
    if len(accents) > 4:
        R.warn("I3", f"强调色相关变量 {len(accents)} 个（{sorted(accents)}）",
               "全站高饱和强调色 ≤2 个；accent/soft/ink 三档同色系属正常")

    # ---------------- I4 字重
    w = {k: v for k, v in V.items() if "weight" in k}
    vals = {str(x).strip() for x in w.values()}
    if len(vals) > 2:
        R.warn("I4", f"字重用了 {len(vals)} 档：{sorted(vals)}", "超过两档就失去克制；建议 400 + 1 个重端")

    # ---------------- I5 圆角
    rad = {k: px(v) for k, v in V.items() if "radius" in k}
    rad = {k: v for k, v in rad.items() if v is not None}
    if len(rad) > 3:
        R.warn("I5", f"圆角档 {len(rad)} 个：{rad}", "圆角 ≤3 档；直角流派应全部为 0")
    if rad and 0 < max(rad.values()) <= 2 and len(rad) > 1:
        R.info("I5", "圆角近乎直角但设了多档", "近乎直角取单档 0 或 2 即可")

    # ---------------- I6 容器宽
    if get("measure") is None:
        R.warn("I6", "未定义 `--measure`", "主容器宽必须统一，禁止各区块自定 max-width")

    # ---------------- I7 字距方向
    td = get("trk-display") or V.get("tracking-display") or V.get("ls-display")
    tl = get("trk-label") or V.get("tracking-label") or V.get("ls-label")
    def em(x):
        m = re.match(r"^\s*(-?[\d.]+)\s*em\s*$", str(x or ""))
        return float(m.group(1)) if m else None
    tdv, tlv = em(td), em(tl)
    if tdv is not None and tdv > 0.06:
        R.warn("I7", f"大标题字距明显为正（{tdv:g}em）", "大字号要负字距，否则字间像被撑开。"
               "唯一例外：东方留白/书法流派的疏朗大字可微正（≤0.04em），须是有意为之")
    if tlv is not None and tlv <= 0:
        R.warn("I7", f"微标签字距非正（{tlv:g}em）", "全大写/微标签需正字距 +0.06~0.12em")

    # ---------------- F5 与锚点签名一致（--anchor 时启用）
    if a.anchor:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sp_path = os.path.join(root, "styles", "signatures.json")
        ix_path = os.path.join(root, "styles", "index.json")
        if not (os.path.exists(sp_path) and os.path.exists(ix_path)):
            R.info("F5", f"找不到签名字典，跳过一致性校验", "确认本脚本在 skill 的 scripts/ 下")
        else:
            siginfo = json.load(open(sp_path, encoding="utf-8"))["anchors"]
            if a.anchor not in siginfo:
                R.err("F5", f"未知锚点 `{a.anchor}`", "用 emit_tokens.py --list 查看")
            else:
                sig = siginfo[a.anchor]
                idx = json.load(open(ix_path, encoding="utf-8"))
                anc = next(x for x in idx["anchors"] if x["slug"] == a.anchor)
                tag = f"与签名 `{a.anchor}` 不一致"

                fsv = {k: px(v) for k, v in V.items() if k.startswith("fs-")}
                fsv = {k: v for k, v in fsv.items() if v}
                b = fsv.get("fs-base") or fsv.get("fs-body")
                if b and abs(b - sig["base"]) > 1:
                    R.err("F5", f"正文基准 {b:g}px ≠ 签名 {sig['base']}px（{tag}）", "有意偏离请在 MASTER.md 注明理由")
                if med_ratio is not None and abs(med_ratio - sig["r"]) / sig["r"] > 0.05:
                    R.err("F5", f"字阶公比实测 {med_ratio:.3f} ≠ 签名 {sig['r']}（{tag}）", "改公比等于重做整套字号关系")
                if lhb is not None and abs(lhb - sig["lh"]) > 0.05:
                    R.err("F5", f"正文行高 {lhb:g} ≠ 签名 {sig['lh']}（{tag}）", "")
                if m:  # prose-width 已在 I1 解析
                    c = float(m.group(1))
                    if abs(c - sig["ch"]) > 3:
                        R.err("F5", f"行长 {c:g}ch ≠ 签名 {sig['ch']}ch（{tag}）", "")
                if sp and min(sp.values()) != sig["unit"]:
                    R.err("F5", f"间距基数 {min(sp.values()):g}px ≠ 签名 {sig['unit']}px（{tag}）", "")
                if rad:
                    r_ = rad.get("radius")
                    if r_ is not None and abs(r_ - sig["rad"]) > 0.5:
                        R.err("F5", f"圆角 {r_:g}px ≠ 签名 {sig['rad']}px（{tag}）", "")
                if axis and anc["axis"] not in axis:
                    R.err("F5", f"中轴 `{axis.strip()}` ≠ 注册表 `{anc['axis']}`", "axis 决定对齐策略，不能随意改")
                if not any(x["code"] == "F5" for x in R.items):
                    R.add("S", "F5", f"token 与锚点签名 `{a.anchor}` 一致（字阶/行高/行长/栅格/圆角/中轴）")

    # ---------------- F6 字体搭配（反同质化）
    # 这一节是 v0.7 新增的。旧版只查数值不查字体，于是 40 个锚点产出的
    # --font-display 几乎都是 "Inter, -apple-system…" —— 数值全过、观感全同。
    # 判据的核心：**标题字体必须是被选出来的，不是被默认继承的**。
    GENERIC = {"system-ui", "-apple-system", "blinkmacsystemfont", "sans-serif",
               "serif", "monospace", "ui-sans-serif", "ui-serif", "ui-monospace",
               "segoe ui", "arial", "helvetica", "helvetica neue"}

    def first_family(stack):
        s = (stack or "").strip()
        m = re.search(r'"([^"]+)"|\'([^\']+)\'|([A-Za-z][\w\s\-]*)', s)
        return (m.group(1) or m.group(2) or m.group(3) or "").strip() if m else ""

    fdisp = get("font-display") or V.get("font-display") or V.get("display-font") or V.get("heading-font")
    fbody = get("font-body") or V.get("font-body") or V.get("body-font")
    if fdisp is None and fbody is None:
        R.err("F6", "未定义 `--font-display` / `--font-body`（字体未做搭配）",
              "字体必须是选型的一等公民：见 styles/fonts.json；用 emit_tokens.py 生成")
    else:
        fd, fb = first_family(fdisp), first_family(fbody)
        if fdisp is None:
            R.err("F6", "缺 `--font-display`（标题字体未指定）", "标题字体必须显式声明，不能用正文字体顶替")
        elif fd.lower() in GENERIC:
            R.err("F6", f"`--font-display` 首族是通用关键字 `{fd}`（未做搭配）",
                  "通用栈只能出现在回退位置；首族必须是具名字体（fonts.json 的 R1）")
        if fbody is None:
            R.err("F6", "缺 `--font-body`（正文字体未指定）", "")
        elif fb.lower() in GENERIC:
            R.err("F6", f"`--font-body` 首族是通用关键字 `{fb}`（未做搭配）", "")
        if fd and fb and fd.lower() == fb.lower():
            R.err("F6", f"标题与正文同用 `{fd}`（= 没做搭配）",
                  "同一字体当标题与正文是 AI 均值味的来源；见 fonts.json 的 R2")
        if fd and fb and fd.lower() != fb.lower() and fd.lower() not in GENERIC and fb.lower() not in GENERIC:
            R.add("S", "F6", f"字体搭配：`{fd}`（标题）× `{fb}`（正文）")
        # 与 fonts.json 的锚点搭配比对（--anchor 时给出更具体的提示）
        if a.anchor:
            fp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              "styles", "fonts.json")
            if os.path.exists(fp) and fd:
                try:
                    F = json.load(open(fp, encoding="utf-8"))
                    want = first_family((F.get("anchors", {}).get(a.anchor) or {}).get("display", ""))
                    if want and want.lower() != fd.lower():
                        R.info("F6", f"`--font-display` 为 `{fd}`，而 fonts.json 为锚点 `{a.anchor}` 指定的是 `{want}`",
                               "有意替换请同步更新 fonts.json（R3 要求 display 全库唯一）")
                except Exception:
                    pass

    # ---------------- F10 视觉签名（反同质化 · 交付前必过）
    # 视觉签名是**结构级**的差异化手法 —— 去掉颜色、去掉字体，依然能看出这是哪个站。
    # layouts.md 要求每站 ≥3 条并过「灰度测试」，但 v0.7 只写了「必填」却没配机器判据，
    # 结果 5 个测试站 5/5 全部缺失。**没有判据的「必填」等于不必填。**
    if a.file.lower().endswith(".css"):
        R.info("F10", "tokens.css 不含视觉签名段（它属于 MASTER.md）",
               "对 MASTER.md 跑一次以校验签名")
    else:
        m = re.search(r"^#{1,4}[^\n]*视觉签名[^\n]*$", text, re.M)
        if not m:
            R.err("F10", "MASTER.md 缺「视觉签名」段（交付前必填）",
                  "见 layouts.md 的签名菜单；每站至少 3 条结构级手法，且必须过灰度测试")
        else:
            rest = text[m.end():]
            nxt = re.search(r"^#{1,4}\s", rest, re.M)
            seg = rest[:nxt.start()] if nxt else rest
            items = re.findall(r"^\s*(?:[-*+]|\d+[.)])\s+\S", seg, re.M)
            if len(items) < 3:
                R.err("F10", f"「视觉签名」只有 {len(items)} 条，要求 ≥3 条",
                      "签名是结构级手法（栅格断裂 / 尺度越级 / 材质叠印 / 轴向偏置…），"
                      "不是配色或字体 —— 那些属于锚点，不属于签名")
            else:
                R.add("S", "F10", f"视觉签名 {len(items)} 条（过灰度测试即可交付）")

    # ---------------- N1 命名规范
    if get.aliases_used:
        pairs = sorted(set(get.aliases_used))
        noncanon = sorted(k for k in V if k not in CANONICAL and not re.match(
            r"^(fs|space|sp|lh|leading|trk|tracking|ls|radius|font|weight|dur)-", k)
            and k not in {"accent", "accent-ink", "accent-soft"})
        R.info("N1", "非规范 token 名：" + "、".join(f"`--{a}` 充当 `--{c}`" for c, a in pairs),
               "规范词汇表见 design-qa.md。自有命名能被审计，但跨项目复用与交接会变难")
        if noncanon:
            R.info("N1", f"其余自由命名：{', '.join('--' + k for k in noncanon[:8])}"
                         + ("…" if len(noncanon) > 8 else ""), "")

    # ---------------- S 级
    sh = get("shadow")
    if sh and "none" not in sh and "var(" not in sh:
        R.info("S1", f"声明了阴影（{sh[:30]}）", "零装饰流派用 --line 分区替代阴影")
    ease = get("ease")
    d1 = get("dur-fast") or ""
    if ease and "linear" in ease and "0ms" not in d1:
        R.info("S2", f"缓动为 linear", "除非零动效，linear 会显得机械")
    if get("line") is None and not any("border" in k for k in V):
        R.info("S3", "无 `--line` 也无边框变量", "分区若靠阴影，检查是否与流派冲突")
    if not any("tabular" in k or "mono" in k for k in V):
        R.info("S4", "未见等宽/表格数字相关 token", "价格、规格、时间列需 tabular-nums 对齐")
    if "never" not in text.lower():
        R.info("S5", "未见 `never` 清单", "MASTER.md 应显式写出禁止项，且可被机器/人检查")

    return emit(R, a.json)


# ---------------------------------------------------------------- F11 批次差异度
# 单站自洽 ≠ 批次多样。v0.7 的教训：5 个测试站每一个单独跑 audit 都是 F 级 0，
# 但摆在一起 --bg 5/5 全是 #FFFFFF、锚点只用 3 个、字体 4/5 没做搭配。
# 判据只有「单站内自洽」这一条腿，就必然漏掉跨站收敛。这一节补上另一条腿。
# 与 ledger.py 的分工：ledger 在**开工前**查重（事前），本判据在**交付前**审计（事后）。

SKIP_DIRS = {"node_modules", ".git", "_source", "source", "_extracted",
             "assets", "art", "thumb", "tools", "inbox", "dist", "build"}


def _first_family(stack):
    m = re.search(r'"([^"]+)"|\'([^\']+)\'|([A-Za-z][\w\s\-]*)', (stack or "").strip())
    return (m.group(1) or m.group(2) or m.group(3) or "").strip() if m else ""


AXES = ("left-rail", "center-axis", "split")
SURFACES = ("white", "paper", "tint", "stone", "slate", "ink", "deep")


def _norm(v, allowed):
    """把取到的值归一化到白名单 —— markdown 表格与 never 清单会把说明文字混进来。"""
    s = (v or "").strip().strip("*`\"' ")
    for k in allowed:
        if k in s:
            return k
    return s[:24] or None


def fingerprint(text):
    """从一个站的产出里抽出可比对的指纹。

    必须走 `make_role()` 而不是直接 `V.get()` —— 与单站审计用同一套别名解析。
    否则用自有命名（如 `--paper` 充当 `--bg`、`--ink` 充当 `--fg`）的站会：
    单站审计 F 0 通过，而 `--batch` 读出的指纹全是空值，
    表现为「每个站单看都合格，摆一起却因为读不到值而判不达标」——
    这是假失败，会掩盖真正的同质化，也会让人误以为反同质化门没做。
    """
    V = collect(text)
    role = make_role(V)
    return {
        "surface": _norm(role("surface"), SURFACES),
        "axis": _norm(role("axis"), AXES),
        "bg": (role("bg") or "").strip().upper() or None,
        "font_display": _first_family(role("font-display")) or None,
        "font_body": _first_family(role("font-body")) or None,
        "fs_base": (role("fs-base") or "").strip() or None,
        "space_1": (role("space-1") or "").strip() or None,
        "radius": (role("radius") or "").strip() or None,
    }


def scan_sites(root):
    """扫出 root 下每个站的一份 token 文本（优先 tokens.css，其次 MASTER.md）。"""
    out = []
    for name in sorted(os.listdir(root)):
        p = os.path.join(root, name)
        if not os.path.isdir(p) or name.startswith(".") or name in SKIP_DIRS:
            continue
        cand = []
        for base, dirs, files in os.walk(p):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
            for f in files:
                if f in ("tokens.css", "MASTER.md"):
                    cand.append(os.path.join(base, f))
        if not cand:
            continue
        cand.sort(key=lambda x: (0 if x.endswith("tokens.css") else 1, len(x)))
        fp = fingerprint(open(cand[0], encoding="utf-8", errors="replace").read())
        fp["site"] = name
        fp["file"] = os.path.relpath(cand[0], root).replace("\\", "/")
        out.append(fp)
    return out


def cmd_batch(root, as_json):
    root = os.path.abspath(root)
    if not os.path.isdir(root):
        print(f"目录不存在：{root}", file=sys.stderr)
        return 2
    sites = scan_sites(root)
    if not sites:
        print(f"在 {root} 下没找到任何站（子目录需含 tokens.css 或 MASTER.md）", file=sys.stderr)
        return 2

    n = len(sites)

    def kinds(key):
        return Counter(str(s[key]) for s in sites if s.get(key))

    surf, ax, bg = kinds("surface"), kinds("axis"), kinds("bg")
    fdisp, fbody = kinds("font_display"), kinds("font_body")
    fsb, sp1, rad = kinds("fs_base"), kinds("space_1"), kinds("radius")
    # 中轴只有 3 档。要求「3 种全部出现」= 覆盖率 100% = **配额**：那会强制每个批次
    # 都含一个 `split` 站，而 split 只有 5 个锚点，等于把布局与族的自由度一起锁死。
    # 改成「≥2 种 + 单档占比 ≤60%」：仍然抓得住「5 站全 left-rail」，但不再制造必经点。
    # 与 scripts/ledger.py 的 MIN_AXIS_KINDS / MAX_AXIS_SHARE 保持同一套语义。
    MIN_AXIS_KINDS = 2
    MAX_AXIS_SHARE = 0.60

    checks = []

    def add(name, val, ok, rule, detail=""):
        checks.append({"name": name, "value": val, "pass": ok, "rule": rule, "detail": detail})

    def dups(c):
        return "；".join(f"{k}×{v}" for k, v in c.most_common() if v > 1)

    if surf:
        add("底色档种类", f"{len(surf)} 种（{'、'.join(surf)}）", len(surf) >= 3, "阈值 ≥3 种")
    add("底色值唯一率", f"{len(bg)}/{n} = {len(bg)/n:.0%}", len(bg) / n >= 0.8,
        "阈值 ≥80%", dups(bg))
    add("中轴种类", f"{len(ax)} 种（{'、'.join(ax) or '缺'}）", len(ax) >= MIN_AXIS_KINDS,
        f"阈值 ≥{MIN_AXIS_KINDS} 种")
    # 种类数只能证明「不是全都一样」，挡不住「5 站里 4 站 left-rail」—— 占比才是「不塌缩」。
    if ax:
        top_ax, top_n = ax.most_common(1)[0]
        add("中轴最大占比", f"{top_ax} {top_n}/{n} = {top_n/n:.0%}", top_n / n <= MAX_AXIS_SHARE,
            f"阈值 ≤{MAX_AXIS_SHARE:.0%}")
    else:
        add("中轴最大占比", f"未记录（0/{n}）", False, "tokens 须写 `--axis`")
    add("display 唯一率", f"{len(fdisp)}/{n} = {len(fdisp)/n:.0%}", len(fdisp) / n >= 1.0,
        "阈值 100%", dups(fdisp))
    add("基准字号种类", f"{len(fsb)} 种（{'、'.join(fsb)}）", len(fsb) >= 3, "阈值 ≥3 种")
    add("间距基数种类", f"{len(sp1)} 种（{'、'.join(sp1)}）", len(sp1) >= 3, "阈值 ≥3 种")
    add("圆角档种类", f"{len(rad)} 种（{'、'.join(rad)}）", len(rad) >= 2, "阈值 ≥2 种")

    fails = [c for c in checks if not c["pass"]]
    result = {"root": root, "count": n, "sites": sites, "checks": checks, "pass": not fails}

    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"批次差异度审计 · {n} 个站 · {root}")
        print("=" * 68)
        for c in checks:
            print(f"  {'✓' if c['pass'] else '✗'} {c['name']:<16} {c['value']:<32} {c['rule']}")
            if not c["pass"] and c.get("detail"):
                print(f"      撞车：{c['detail']}")
        print("=" * 68)
        print("  逐站指纹：")
        for s in sites:
            print(f"    {s['site']:<18} {str(s.get('surface') or '—'):<7} "
                  f"{str(s.get('axis') or '—'):<13} {str(s.get('font_display') or '—'):<20} "
                  f"{str(s.get('bg') or '—')}")
        print("=" * 68)
        if fails:
            print(f"综合：FAIL（{len(fails)} 项不达标）")
            for c in fails:
                print(f"  → {c['name']}：{c['value']}（{c['rule']}）")
            print("\n逐站单跑 audit 可能全是 PASS —— 那是「单站自洽」这条腿。")
            print("本判据补的是「跨站差异」：一批站服务的是各行各业，风格必须迥异。")
        else:
            print("综合：PASS —— 本批次风格差异度达标。")
    return 0 if not fails else 1


# ---------------------------------------------------------------- F14/F15 页面结构
# 与 --batch 的分工：--batch 比的是**跨站差异**（风格），--site 比的是**站内声明与产物**
# （结构）。两者都不看数值 —— 数值归单文件模式。
#
# 为什么必须有这一节：v0.8 及以前，IA 只决定「这一页由哪些区块组成」，不决定「内容分几页」。
# 于是所有站都只产出单个 index，条目再多也全塞进一页；长页也没有任何页内跳转。
# 而「页面粒度」与「页内导航」在文档里写着「必填」，却**没有任何机器判据** ——
# 与 v0.7 的「视觉签名」是一模一样的失效方式。这一节补上判据。
#
# 判据阈值来自 architectures/pagination.json（唯一真源），本脚本不硬编码。

PAGE_EXT = (".astro", ".html", ".htm", ".mdx", ".md", ".jsx", ".tsx",
            ".vue", ".svelte", ".njk", ".liquid", ".ejs", ".hbs", ".php")
CODE_EXT = (".js", ".ts", ".mjs", ".cjs")
SITE_SKIP = {"node_modules", "dist", "build", "_site", ".astro", ".next", ".nuxt",
             ".git", ".cache", "public", "static", "assets", "vendor"}
PROFILE_FILES = ("content-profile.md", "intent-summary.md")

HREF_HASH_RE = re.compile(r'href\s*=\s*["\']#([A-Za-z][\w\-:.]*)["\']')
ID_RE = re.compile(r'\bid\s*=\s*["\']([^"\']+)["\']')
SECTION_RE = re.compile(r"<\s*section\b", re.I)
H2_RE = re.compile(r"<\s*h2\b", re.I)

GRAN_LEVELS = {"single": 1, "master-detail": 2, "multi-page": 3, "n/a": 0}
GRAN_ALIAS = {"单页": "single", "主从": "master-detail", "主从页": "master-detail",
              "多页": "multi-page", "多页并列": "multi-page", "不适用": "n/a"}
NAV_LEVELS = ("none", "anchor-jump", "sticky-toc", "section-rail")
NAV_ALIAS = {"无": "none", "锚点跳转": "anchor-jump", "粘性目录": "sticky-toc", "章节轨": "section-rail"}


def _decl_value(text, key, allowed, aliases):
    """从 content-profile.md 里取一行声明。返回 (值, None) / (原文, 'invalid') / (None, 'missing')。"""
    m = re.search(re.escape(key) + r"\s*[：:]\s*`?\s*([^\s`|，,。;；)）(（]+)", text)
    if not m:
        return None, "missing"
    raw = m.group(1).strip().strip("`*\"'")
    if raw in allowed:
        return raw, None
    if raw in aliases:
        return aliases[raw], None
    low = raw.lower()
    if low in allowed:
        return low, None
    for cand in allowed:
        if low.startswith(cand):
            return cand, None
    return raw, "invalid"


def _iter_site_files(site):
    for base, dirs, files in os.walk(site):
        dirs[:] = [d for d in dirs if d not in SITE_SKIP and not d.startswith(".")]
        rel = os.path.relpath(base, site).replace("\\", "/")
        segs = [] if rel == "." else rel.split("/")
        for f in files:
            yield os.path.join(base, f), "/".join(segs + [f]), segs


def find_page_files(site):
    """站点里的页面文件：`pages/` 目录下的页面，或根目录的 HTML。"""
    out = []
    for path, rel, segs in _iter_site_files(site):
        f = os.path.basename(rel)
        if f.startswith("_") or f.startswith("404"):
            continue
        ext = os.path.splitext(f)[1].lower()
        if ext not in PAGE_EXT:
            continue
        if "pages" in segs or (not segs and ext in (".html", ".htm")):
            out.append(rel)
    return sorted(set(out))


def site_ids(site):
    """全站 id 集合 —— 锚点目标可能落在 layout / 组件里，不能只扫页面文件。"""
    ids = set()
    for path, _rel, _segs in _iter_site_files(site):
        ext = os.path.splitext(path)[1].lower()
        if ext not in PAGE_EXT and ext not in CODE_EXT:
            continue
        try:
            ids |= set(ID_RE.findall(open(path, encoding="utf-8", errors="replace").read()))
        except OSError:
            continue
    return ids


def page_stats(site, rel):
    text = open(os.path.join(site, *rel.split("/")), encoding="utf-8", errors="replace").read()
    return {
        "hrefs": HREF_HASH_RE.findall(text),
        "blocks": max(len(SECTION_RE.findall(text)), len(H2_RE.findall(text))),
    }


# ---------------------------------------------------------------- 补判据的辅助
# 这几条是「本可机器化却一直没做」的铁律：19 字段必须渲染 / 18 可溯源 /
# 26 一份真源 / 14 嵌入服从宿主 / 29 产物形状反映技术栈。
# 来源：用项目第一条信条反过来审自己 —— 「没有判据的必填 = 不必填」。

SRC_ALL_EXT = PAGE_EXT + CODE_EXT          # 页面 + 组件源码
DATA_DIR_NAMES = ("data", "_data")
TOKEN_FILE_NAMES = ("tokens.css", "globals.css", "tokens.md")


def find_data_files(site):
    """站点的数据源文件（src/data/*.json 等）—— 字段定义的真源。"""
    out = []
    for base, dirs, files in os.walk(site):
        dirs[:] = [d for d in dirs if d not in SITE_SKIP and not d.startswith(".")]
        if os.path.basename(base) in DATA_DIR_NAMES:
            out += [os.path.join(base, f) for f in files if f.lower().endswith(".json")]
    return sorted(out)


def data_shape(obj, prefix=""):
    """从数据结构里抽出 {字段路径: 数组长度}；非数组不记录。

    只关心数组 —— 铁律 19 的原始失效场景就是「images: [...7 张] 却只渲染第一张」，
    标量字段漏渲染反而不容易出事（会直接看不见）。
    """
    fields = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{prefix}{k}"
            if isinstance(v, list):
                fields[p] = len(v)
                for item in v[:20]:
                    if isinstance(item, dict):
                        fields.update(data_shape(item, p + "[]."))
            elif isinstance(v, dict):
                fields.update(data_shape(v, p + "."))
    elif isinstance(obj, list):
        for item in obj[:50]:
            if isinstance(item, dict):
                fields.update(data_shape(item, prefix + "[]."))
    return fields


def site_source_text(site):
    """全站页面/组件源码拼成一份文本。

    必须看全站而不是首页：`[slug].astro` 这类详情页才是渲染数组字段的地方，
    只扫首页会把「详情页渲染了、首页没渲染」误判成漏渲染。
    """
    buf = []
    for path, _rel, _segs in _iter_site_files(site):
        if os.path.splitext(path)[1].lower() not in SRC_ALL_EXT:
            continue
        try:
            buf.append(open(path, encoding="utf-8", errors="replace").read())
        except OSError:
            continue
    return "\n".join(buf)


def iter_tokens(text):
    """抽出 `--x: v` 定义；跳过值是另一个变量引用的（无法静态比对）。"""
    out = {}
    for m in re.finditer(r"(--[\w-]+)\s*:\s*([^;}\n]+)", text):
        v = m.group(2).strip().strip('"`* ')
        if v and not v.startswith("--") and "<" not in v:
            out.setdefault(m.group(1), v)
    return out


def norm_val(v):
    """值归一化 —— 去空白后比较。

    字体栈在两份文件里常写成 `Inter","Helvetica` 与 `Inter", "Helvetica`，
    差别只有逗号后的空格，语义完全相同。不归一化会把这种写法差异误报成「真源漂移」，
    而误报比漏报更伤：下一次真的漂移会被当成噪声忽略掉。
    """
    return re.sub(r"\s+", "", (v or "")).lower()


def find_named_file(site, names):
    for base, dirs, files in os.walk(site):
        dirs[:] = [d for d in dirs if d not in SITE_SKIP and not d.startswith(".")]
        for n in names:
            if n in files:
                return os.path.join(base, n)
    return None


# 溯源标记：`p12` / `p. 12` / URL / `<url> #selector`
CITE_RE = re.compile(r"\bp\s?\.?\s?\d{1,4}\b|https?://|<url>")


def cmd_site(site, as_json):
    site = os.path.abspath(site)
    if not os.path.isdir(site):
        print(f"目录不存在：{site}", file=sys.stderr)
        return 2

    R = Report(site)
    th_none_max, th_min_targets = 5, 2
    reg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "architectures", "pagination.json")
    if os.path.exists(reg_path):
        try:
            t = (json.load(open(reg_path, encoding="utf-8"))
                 .get("inPageNav", {}).get("thresholds", {}))
            th_none_max = t.get("none_contradiction_blocks", th_none_max)
            th_min_targets = t.get("min_anchor_targets", th_min_targets)
        except Exception as e:
            R.info("F15", f"读不到判据注册表（{e}），用内置默认阈值",
                   "阈值应在 architectures/pagination.json")
    else:
        R.info("F15", "找不到 architectures/pagination.json，用内置默认阈值", "")

    decl_text, decl_file = "", None
    for name in PROFILE_FILES:
        p = os.path.join(site, name)
        if os.path.exists(p):
            decl_text += open(p, encoding="utf-8", errors="replace").read() + "\n"
            decl_file = decl_file or name
    if not decl_file:
        R.err("F14", f"站点目录下找不到 {' 或 '.join(PROFILE_FILES)}",
              "页面粒度与页内导航必须写进 content-profile.md"
              "（格式见 architectures/granularity.md §4.2）")

    gran, gerr = _decl_value(decl_text, "页面粒度", GRAN_LEVELS, GRAN_ALIAS)
    nav, nerr = _decl_value(decl_text, "页内导航", NAV_LEVELS, NAV_ALIAS)

    pages = find_page_files(site)
    ids = site_ids(site)
    idx = next((p for p in pages if os.path.basename(p).lower().startswith("index.")),
               pages[0] if pages else None)
    stats = page_stats(site, idx) if idx else None

    # ---------------- F14 页面粒度
    if gerr == "missing":
        R.err("F14", "未声明「页面粒度」",
              "在 content-profile.md 写 `页面粒度：single|master-detail|multi-page|n/a`；"
              "先跑 python scripts/pick_pages.py 算")
    elif gerr == "invalid":
        R.err("F14", f"「页面粒度」取值非法：{gran}",
              "只能 single / master-detail / multi-page / n/a")
    else:
        n, need = len(pages), GRAN_LEVELS[gran]
        if gran == "n/a":
            if n:
                R.warn("F14", f"声明 n/a（system-only 不搭站），却找到 {n} 个页面文件", "复核交付形态")
            else:
                R.add("S", "F14", "页面粒度 n/a ✓（system-only，无页面）")
        elif gran == "single":
            if n != 1:
                R.err("F14", f"声明 single，实际有 {n} 个页面文件：{pages[:5]}",
                      "single 必须恰好 1 个页面；要么改声明，要么把内容并回一页")
            else:
                R.add("S", "F14", f"页面粒度 single ✓（{pages[0]}）")
        elif n < need:
            R.err("F14", f"声明 {gran}（需 ≥{need} 个页面），实际只有 {n} 个：{pages or '无'}",
                  "多页 / 主从必须有真实存在的页面文件；只写声明不算数")
        else:
            R.add("S", "F14", f"页面粒度 {gran} ✓（{n} 个页面文件）")
            if gran == "master-detail" and not any("[" in p for p in pages):
                R.info("F14", "master-detail 未用动态路由模板（如 `[slug]`）",
                       "详情页由同一模板生成时用 `[slug]` 更省事，也不会漏掉新增条目")

    # ---------------- F15 页内导航
    if nerr == "missing":
        R.err("F15", "未声明「页内导航」",
              "写 `页内导航：none|anchor-jump|sticky-toc|section-rail`；"
              "先跑 python scripts/pick_pages.py 算")
    elif nerr == "invalid":
        R.err("F15", f"「页内导航」取值非法：{nav}",
              "只能 none / anchor-jump / sticky-toc / section-rail")
    elif not stats:
        R.warn("F15", "找不到任何页面文件，页内导航未校验", "")
    elif nav == "none":
        if stats["blocks"] >= th_none_max:
            R.err("F15", f"声明「页内导航：none」，但首页有 {stats['blocks']} 个区块"
                         f"（阈值 {th_none_max}）",
                  "长页声明无导航 = 用户只能一翻到底；要么加锚点，要么改声明并在"
                  "content-profile.md 写明为何不需要")
        else:
            R.add("S", "F15", f"页内导航 none ✓（首页 {stats['blocks']} 个区块，确实短）")
    else:
        reach = [h for h in stats["hrefs"] if h in ids]
        if len(reach) < th_min_targets:
            R.err("F15", f"声明「页内导航：{nav}」，但首页只有 {len(reach)} 个可达锚点"
                         f"（要求 ≥{th_min_targets}）",
                  '声明了导航就必须真的做出来：href="#x" 且页面上存在 id="x"')
        else:
            R.add("S", "F15", f"页内导航 {nav} ✓（{len(reach)} 个可达锚点）")

    # ---------------- 断链（所有页面）
    broken = []
    for p in pages:
        st = stats if (idx and p == idx) else page_stats(site, p)
        broken += [f"{p}#{h}" for h in st["hrefs"] if h not in ids]
    if broken:
        R.err("F15", f"页内锚点断链 {len(broken)} 处：{broken[:6]}",
              'href="#x" 必须能在站内找到 id="x"')

    # ---------------- F16 字段渲染完整性（铁律 19）
    data_files = find_data_files(site)
    if data_files:
        src_text = site_source_text(site)
        arrays = {}
        for df in data_files:
            try:
                arrays.update(data_shape(json.load(open(df, encoding="utf-8"))))
            except (OSError, ValueError):
                continue
        short_render, unused = [], []
        for path, n in sorted(arrays.items()):
            if n <= 1:
                continue
            leaf = path.split(".")[-1].replace("[]", "")
            if not leaf:
                continue
            if leaf not in src_text:
                unused.append(f"{path}({n})")
                continue
            hard0 = re.search(rf"{re.escape(leaf)}\s*\[\s*0\s*\]", src_text)
            # 只认 .map()/.flatMap()：它们**产出标记**，等于真的把每一项渲染出来了。
            # 不认 .forEach() —— 它通常只做副作用（注册灯箱数据、绑定事件），
            # 页面上一个元素都不会多。把它算作渲染，会让「脚本里遍历过」
            # 掩盖「模板里只渲染第一张」，正是铁律 19 的失效场景。
            loops = re.search(rf"{re.escape(leaf)}\s*\.\s*(map|flatMap)\s*\(", src_text)
            if hard0 and not loops:
                short_render.append(f"{path}（数据 {n} 条，代码只取 [0]）")
        if short_render:
            R.err("F16", f"数组字段疑似只渲染第一项：{short_render[:4]}",
                  "铁律 19：字段定义了就必须渲染 —— 用 .map() 遍历，不要写 [0]。"
                  "引用校验对这种情况仍然 PASS，所以必须有这条判据")
        elif unused:
            R.warn("F16", f"数据里定义了但全站未引用的数组字段：{unused[:4]}",
                   "要么渲染出来，要么从数据里删掉（留着会误导后来者）")
        else:
            R.add("S", "F16", f"字段渲染完整性 ✓（{len(arrays)} 个数组字段均已遍历）")
    else:
        R.add("S", "F16", "无 src/data/*.json，字段渲染未校验")

    # ---------------- F17 内容可溯源（铁律 18）
    sm = find_named_file(site, ("source-map.md", "source_map.md"))
    if not sm:
        R.info("F17", "未找到 source-map.md",
               "有源材料（PDF / 图库 / 现有站）时应建溯源表：每条内容标 `p12 · \"原句\"`。"
               "缺它不算致命，但防编造机制处于未启用状态")
    else:
        lines = [l for l in open(sm, encoding="utf-8", errors="replace").read().split("\n")
                 if l.strip().startswith("|")]
        body = [l for l in lines if not re.match(r"^\|[\s:\-|]+\|$", l.strip())]
        # 表头也算一行，扣掉
        body = body[1:] if body else body
        if not body:
            R.warn("F17", f"{os.path.basename(sm)} 里没有表格行，无法校验溯源覆盖率",
                   "溯源表应为 markdown 表格，每行一条内容 + 出处")
        else:
            cited = [l for l in body if CITE_RE.search(l)]
            rate = len(cited) / len(body)
            if rate < 0.5:
                R.err("F17", f"溯源覆盖率过低：{len(cited)}/{len(body)} = {rate:.0%}（阈值 50%）",
                      "铁律 18：每条内容必须能指回源 —— 补 `p12 · \"原句\"` 或 <url>；"
                      "指不回去的就是编的，删掉")
            else:
                R.add("S", "F17",
                      f"内容可溯源 ✓（{len(cited)}/{len(body)} = {rate:.0%} 条带溯源标记）")

    # ---------------- F18 一份真源（铁律 26）
    master = find_named_file(site, ("MASTER.md",))
    tokfile = find_named_file(site, TOKEN_FILE_NAMES)
    if master and tokfile:
        a = iter_tokens(open(master, encoding="utf-8", errors="replace").read())
        b = iter_tokens(open(tokfile, encoding="utf-8", errors="replace").read())
        shared = sorted(set(a) & set(b))
        drift = [f"{k}：MASTER={a[k]} ≠ {os.path.basename(tokfile)}={b[k]}"
                 for k in shared if norm_val(a[k]) != norm_val(b[k])]
        if drift:
            R.err("F18", f"两份真源值漂移 {len(drift)} 处：{drift[:4]}",
                  f"铁律 26：设计系统只能有一份生效的 token —— 以 "
                  f"{os.path.basename(tokfile)} 为准，把 {os.path.basename(master)} 同步过来")
        elif len(shared) < 3:
            R.info("F18", f"MASTER.md 与 {os.path.basename(tokfile)} 共有 token 仅 "
                          f"{len(shared)} 个，一致性未充分校验",
                   "两边至少要写同一批核心 token，才有得比")
        else:
            R.add("S", "F18", f"一份真源 ✓（{len(shared)} 个共有 token 值一致）")
    elif tokfile and not master:
        R.add("S", "F18", "无 MASTER.md，真源一致性未校验")

    # ---------------- F19 嵌入服从宿主（铁律 14）
    host = None
    for name in ("content-profile.md", "intent-summary.md", "tech-stack.md"):
        p = find_named_file(site, (name,))
        if p:
            t = open(p, encoding="utf-8", errors="replace").read()
            m = re.search(r"(?:交付形态|host)\s*[:：]\s*`?\s*(standalone|embedded|system-only)",
                          t, re.I)
            if m:
                host = m.group(1).lower()
                break
    hostfile = find_named_file(site, ("HOST.md",))
    if host == "embedded":
        if not hostfile:
            R.err("F19", "声明 embedded 却没有 HOST.md",
                  "铁律 14：嵌入宿主 = 服从宿主 —— 先产出 HOST.md 记录宿主令牌，再对齐")
        elif tokfile:
            hv = iter_tokens(open(hostfile, encoding="utf-8", errors="replace").read())
            tv = iter_tokens(open(tokfile, encoding="utf-8", errors="replace").read())
            shared = sorted(set(hv) & set(tv))
            diff = [f"{k}：宿主={hv[k]} ≠ 产出={tv[k]}"
                    for k in shared if norm_val(hv[k]) != norm_val(tv[k])]
            if diff:
                R.err("F19", f"产出与宿主令牌不一致 {len(diff)} 处：{diff[:4]}",
                      "宿主令牌优先；新增数据用新模块、渲染做分支，不覆盖宿主已有实体")
            else:
                R.add("S", "F19", f"宿主对齐 ✓（{len(shared)} 个共有 token 与宿主一致）")
        else:
            R.add("S", "F19", "无 token 文件，宿主对齐未逐值校验")
    elif hostfile:
        R.add("S", "F19", f"存在 HOST.md（交付形态 {host or '未声明'}），未逐值校验")

    # ---------------- F20 产物形状反映技术栈（铁律 29）
    stack = None
    for name in ("tech-stack.md", "content-profile.md", "intent-summary.md"):
        p = find_named_file(site, (name,))
        if p:
            t = open(p, encoding="utf-8", errors="replace").read()
            m = re.search(r"(?:技术栈|stack)\s*[:：]\s*`?\s*"
                          r"(plain-html|astro|eleventy|vite|next|nuxt|hugo)", t, re.I)
            if m:
                stack = m.group(1).lower()
                break
    if stack:
        has_pages = os.path.isdir(os.path.join(site, "src", "pages")) or \
            any(os.sep + "pages" + os.sep in p or "/pages/" in p.replace("\\", "/") for p in pages)
        has_cfg = bool(find_named_file(
            site, ("astro.config.mjs", "astro.config.js", "astro.config.ts")))
        if stack == "plain-html":
            bad = [x for x, hit in (("astro.config", has_cfg), ("src/pages/", has_pages)) if hit]
            if bad:
                R.err("F20", f"技术栈 plain-html，产物却是框架形状（{'、'.join(bad)}）",
                      "铁律 29：产物形状必须反映技术栈 —— plain-html 应是 index.html + 样式表；"
                      "出现 src/pages/ 说明 Phase 1.5 白做了")
            else:
                R.add("S", "F20", "产物形状 ✓（plain-html：无框架目录）")
        elif stack == "astro":
            if not (has_pages or has_cfg):
                R.warn("F20", "技术栈 astro，但既无 src/pages/ 也无 astro.config",
                       "产物形状应当反映技术栈；确认是不是中途换了栈")
            else:
                R.add("S", "F20", "产物形状 ✓（astro：有 src/pages/ 与 astro.config）")

    R.add("S", "F14", f"页面文件 {len(pages)} 个；声明来源 {decl_file or '—'}")
    return emit(R, as_json)


def emit(R: Report, as_json: bool) -> int:
    f = [x for x in R.items if x["level"] == "F"]
    i = [x for x in R.items if x["level"] == "I"]
    s = [x for x in R.items if x["level"] == "S"]
    if as_json:
        print(json.dumps({"file": R.path, "F": f, "I": i, "S": s,
                          "verdict": "FAIL" if f else "PASS"}, ensure_ascii=False, indent=2))
    else:
        print(f"audit_tokens — {R.path}")
        print("=" * 68)
        for lvl, group, sym in (("F 致命", f, "✗"), ("I 重要", i, "!"), ("S 建议", s, "·")):
            for x in group:
                print(f"  {sym} [{x['code']}] {x['msg']}")
                if x["hint"]:
                    print(f"        → {x['hint']}")
            if group:
                print()
        print(f"F {len(f)} / I {len(i)} / S {len(s)}  →  {'FAIL' if f else 'PASS'}（判据见 design-qa.md）")
    return 1 if f else 0


if __name__ == "__main__":
    sys.exit(main())
