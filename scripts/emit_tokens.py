#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""emit_tokens.py — 由「设计参数签名」确定性生成 MASTER.md 的 token 块。

为什么需要它：40 个锚点里只有 6 个带完整 spec。命中其余 34 个时，若靠
「我大概知道这个风格长什么样」去写 token，必然向 AI 均值收敛。本脚本把
签名的 15 个参数（字阶比 / 基准字号 / 行高 / 容器宽 / 行长 / 栅格 / 字距 /
色相 / 彩度 / 色温 / 圆角 / 基调 / 动效 / 字重 / 标题字体角色）展开成
完整的、对比度经 WCAG 校验的 token 集合 —— 输出是确定的、可复核的，
不是即兴的。

字体（v0.7 起）：不再用三个通用栈兜底，而是从 `styles/fonts.json` 读**每个锚点
专属的具名搭配**（display / body / mono / cjk）。这是修「字体单一」的关键 ——
旧版把字体塌缩成 serif/sans/mono 三选一，40 个锚点的 `--font-display` 几乎一样。
锚点未收录时按「锚点 → 族默认 → 通用」降级，并在输出头部**显式告警**。

三个反同质化维度（v0.8 起，缺一不可）：
  · `--surface`  底色档 white/paper/tint/stone/slate/ink/deep —— 决定 --bg 的明度与彩度。
                 旧版把底色明度写死成近白，40 个锚点全出 #FFFFFF，这是「一批站像同一套
                 模板」最大的单一成因。
  · `--variant`  尺度变体轴 a/b/c/d —— 在同一锚点上做确定性偏移（字阶比 / 基准字号 /
                 栅格基数 / 圆角 / 动效），使同一锚点第二次使用时不逐值相同。
  · `--pair`     字体搭配序号 0-3 —— 0 取锚点专属搭配，1-3 取族备用池。锚点主选每锚点
                 只有一对，第二次使用必然撞车；族池提供至少 4 对可轮换。

用法：
    python scripts/emit_tokens.py --anchor diagonal
    python scripts/emit_tokens.py --anchor ink-wash --lang zh --out /tmp
    python scripts/emit_tokens.py --list
    python scripts/emit_tokens.py --anchor swiss-utility --css-only
    python scripts/emit_tokens.py --anchor swiss-utility --surface ink --variant c --pair 2

输出：stdout 打印 markdown（`MASTER.md` 的 token 段）；`--out <dir>` 则写文件。
本地已有 spec 的锚点会在头部标注：配色以 spec 为准，本输出只补 spec 未给的
字阶 / 行高 / 字距 / 栅格。

**开工前先跑 `scripts/ledger.py --check`**，确认本次的三项指纹没有与同批次已交付的
站撞车。单站自洽不等于批次多样 —— 这是 v0.7 最大的教训。

无第三方依赖。
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)

# ------------------------------------------------------------------ 颜色
def _srgb_encode(c: float) -> float:
    if c <= 0.0031308:
        return 12.92 * c
    return 1.055 * (c ** (1 / 2.4)) - 0.055


def _oklab_to_linear(L: float, a: float, b: float):
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    return (
        +4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
        -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
        -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s,
    )


def oklch_to_rgb01(L: float, C: float, H: float, _depth: int = 0):
    """OKLCH → 0..1 sRGB；越界时二分降彩度（保色相与亮度）。"""
    h = math.radians(H)
    a, b = C * math.cos(h), C * math.sin(h)
    lin = _oklab_to_linear(L, a, b)
    if any(v < -1e-4 or v > 1 + 1e-4 for v in lin):
        if C <= 1e-4 or _depth > 22:
            return tuple(min(1.0, max(0.0, _srgb_encode(min(1.0, max(0.0, v))))) for v in lin)
        return oklch_to_rgb01(L, C * 0.6, H, _depth + 1)
    return tuple(_srgb_encode(min(1.0, max(0.0, v))) for v in lin)


def hex6(rgb) -> str:
    return "#" + "".join(f"{round(max(0.0, min(1.0, c)) * 255):02X}" for c in rgb)


def rel_lum(rgb) -> float:
    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(rgb1, rgb2) -> float:
    a, b = rel_lum(rgb1), rel_lum(rgb2)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def solve_contrast(target: float, ref_rgb, C: float, H: float, lo: float, hi: float,
                   ref_is_light: bool) -> float:
    """求「刚好满足 target」的亮度 L —— 保留色相与彩度，只调明度。

    light 底色：对比度随 L 增大而下降 → 取仍满足 target 的**最亮**值（灰阶不至于发黑）。
    dark 底色：反过来，取仍满足 target 的**最暗**值。
    """
    for _ in range(50):
        mid = (lo + hi) / 2
        c = contrast(oklch_to_rgb01(mid, C, H), ref_rgb)
        if c >= target:
            if ref_is_light:
                lo = mid      # 还能更亮一点，继续上探
            else:
                hi = mid      # 还能更暗一点，继续下探
        else:
            if ref_is_light:
                hi = mid
            else:
                lo = mid
    return lo if ref_is_light else hi


# ------------------------------------------------------------------ 字阶
TIERS = [("xs", -1.0), ("base", 0.0), ("lg", 1.0), ("xl", 2.0), ("2xl", 3.0)]


def type_scale(base: int, r: float):
    """返回 [(name, px, exact)]，共 6 级（含 display）。"""
    out = []
    for name, exp in TIERS:
        px = base * (r ** exp)
        out.append((name, px, px))
    disp_exp = 4.0 if r >= 1.4 else 5.0
    px = base * (r ** disp_exp)
    out.append(("display", px, px))
    return out


def round_px(v: float) -> float:
    if v < 12:
        return round(v * 2) / 2          # 小字号保留 0.5 精度
    return float(round(v))


def leading(tier: str, lh: float) -> float:
    table = {
        "display": min(1.22, max(1.02, lh - 0.62)),
        "2xl":     min(1.32, max(1.08, lh - 0.48)),
        "xl":      min(1.42, max(1.14, lh - 0.34)),
        "lg":      min(1.52, max(1.22, lh - 0.22)),
        "base":    lh,
        "xs":      min(1.95, max(lh, lh + 0.05)),
    }
    return round(table[tier], 2)


MOTION = {
    "snap":  ("120ms", "200ms", "cubic-bezier(.2,0,.2,1)"),
    "soft":  ("180ms", "320ms", "cubic-bezier(.22,.61,.36,1)"),
    "drift": ("300ms", "600ms", "cubic-bezier(.16,.84,.24,1)"),
    "none":  ("0ms", "0ms", "linear"),
}
CHROMA = {0: 0.055, 1: 0.115, 2: 0.185}

# 字体：v0.7 起从 styles/fonts.json 读「具名搭配」，不再用三个通用栈兜底。
# 这里的 FONT_FALLBACK 只在 fonts.json 缺失或锚点未收录时启用 —— 它是降级路径，
# 不是默认值。命中降级会在输出里显式告警，避免「悄悄退回 Inter 均值」。
FONT_FALLBACK = {
    "serif": '"Newsreader", "Source Han Serif SC", "Noto Serif SC", Georgia, "Songti SC", serif',
    "sans":  '"Inter", -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif',
    "mono":  '"JetBrains Mono", ui-monospace, SFMono-Regular, Consolas, "Noto Sans Mono CJK SC", monospace',
}

# 底色：v0.8 起由 signatures.json 的 _surfacePresets 决定，不再写死 L=0.985。
# 旧版把底色的明度硬编码成近白，无论命中哪个锚点，--bg 都是 #FFFFFF —— 这是
# 「一批站看起来像同一套模板」最大的单一成因。这里的 DEFAULT_SURFACE 只是
# 签名文件缺字段时的兜底，等价于旧行为，命中会告警。
DEFAULT_SURFACE = {
    "L": 0.985, "C": 0.006, "polarity": "light", "name": "(兜底 paper)",
    "note": "signatures.json 未给出 surface，按旧版近白底处理",
}


def load_signatures():
    """读 styles/signatures.json 全文（含 _surfacePresets / _variantAxes）。"""
    p = os.path.join(SKILL, "styles", "signatures.json")
    return json.load(open(p, encoding="utf-8"))


def resolve_surface(sigdoc: dict, sig: dict, want: str | None):
    """确定底色档。显式 --surface > 锚点 surface > 兜底。

    返回 (preset, name, source)。preset 是 _surfacePresets 里的一条。
    """
    presets = sigdoc.get("_surfacePresets") or {}
    name = want or sig.get("surface")
    if name and name in presets:
        p = dict(presets[name])
        p["name"] = name
        return p, name, ("命令行 --surface 指定" if want else "锚点推荐值")
    if name:
        # 显式指定了但预设里没有 —— 这是错误，不能静默兜底
        raise SystemExit(
            f"未知 surface：{name}（可用：{', '.join(sorted(presets)) or '无'}）"
        )
    return dict(DEFAULT_SURFACE), DEFAULT_SURFACE["name"], "⚠️ 降级：签名无 surface 字段"


def apply_variant(sig: dict, axis: dict | None):
    """按变体轴对签名做确定性偏移，并 clamp 到安全范围。

    为什么需要它：signatures.json 是「一个锚点 = 一套常量」。同一锚点第二次
    使用时，若原样输出，token 会与上一站逐值相同 —— 这正是 hongda 与 acute-angle
    撞车的原因。变体轴在**不改锚点气质**的前提下把尺度参数推开一档。
    """
    if not axis:
        return dict(sig)
    out = dict(sig)
    out["r"] = round(min(1.62, max(1.15, sig["r"] + axis.get("dr", 0.0))), 3)
    out["base"] = int(min(20, max(13, sig["base"] + axis.get("dbase", 0))))
    out["unit"] = int(min(24, max(2, round(sig["unit"] * axis.get("dunit", 1.0)))))
    out["rad"] = int(min(24, max(0, sig["rad"] + axis.get("drad", 0))))
    if axis.get("mot"):
        out["mot"] = axis["mot"]
    return out


def load_fonts():
    """读 styles/fonts.json。返回 dict 或 None（缺失时走 FONT_FALLBACK）。"""
    p = os.path.join(SKILL, "styles", "fonts.json")
    if not os.path.exists(p):
        return None
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return None


def resolve_fonts(fonts, slug: str, family: str, sig: dict, pair: int = 0):
    """锚点主选 → 族备用池 → 族默认 → 通用 四级降级。

    pair=0 取锚点专属搭配；pair>=1 取 `_familyPools[family][pair-1]`。
    为什么需要 pair：锚点主选每个锚点只有**一对**。同一锚点第二次使用时，
    若原样复用，两站的 `--font-display` 会一字不差（acute-angle 与 hongda 就是
    这么撞的）。族备用池让同一锚点至少有 4 对具名字体可轮换。

    返回 (display, body, mono, cjk, source, note)。
    """
    entry = None
    source = ""
    if fonts and pair > 0:
        pool = (fonts.get("_familyPools") or {}).get(family) or []
        if 0 <= pair - 1 < len(pool):
            entry = pool[pair - 1]
            source = f"族备用池 `{family}` 第 {pair} 对 · {entry.get('tag', '')}"
    if fonts and entry is None:
        entry = (fonts.get("anchors") or {}).get(slug)
        if entry:
            source = f"锚点 `{slug}`"
            if pair > 0:
                source += f"（⚠️ 族池无第 {pair} 对，已回退主选）"
        else:
            entry = (fonts.get("_familyDefaults") or {}).get(family)
            if entry:
                source = f"族默认 `{family}`"
    if not entry:
        # 降级到旧的三通用栈，并标注告警来源
        disp, body = sig["disp"], "sans"
        if disp == "serif":
            body = "serif"
        elif disp == "mono":
            disp, body = "mono", "sans"
        return (FONT_FALLBACK[disp], FONT_FALLBACK[body], FONT_FALLBACK["mono"],
                FONT_FALLBACK["serif"], "⚠️ 降级：fonts.json 未命中", "")

    mono = (fonts.get("_monoStacks") or {}).get(entry["mono"], FONT_FALLBACK["mono"])
    cjk = (fonts.get("_cjkStacks") or {}).get(entry["cjk"], FONT_FALLBACK["serif"])
    return entry["display"], entry["body"], mono, cjk, source, entry.get("note", "")


def first_family(stack: str) -> str:
    """取字体栈的首个字体族名（去引号），用于反同质化比对。"""
    m = re.search(r'"([^"]+)"|\'([^\']+)\'|([A-Za-z][\w\s\-]*)', stack or "")
    if not m:
        return ""
    return (m.group(1) or m.group(2) or m.group(3) or "").strip()



def build(sig: dict, anchor: dict, lang: str, fonts: dict | None = None,
          surface: dict | None = None, variant: dict | None = None, pair: int = 0):
    r = sig["r"]; base = sig["base"]; lh = sig["lh"]
    sp = surface or DEFAULT_SURFACE
    light = sp["polarity"] == "light"
    hue = sig["hue"]; chroma = CHROMA[sig["chr"]]
    warm = sig["warm"]
    tint = 60.0 if warm > 0.3 else (250.0 if warm < -0.3 else 90.0)

    # 底色：由 surface 预设给出明度与彩度，再按色温把彩度放大 —— 暖站偏黄、冷站偏蓝。
    # v0.8 的关键改动：旧版这里写死 L=0.985，所以 40 个锚点的 --bg 全是近白。
    sL = sp["L"]
    sC = sp["C"] * (1.0 + 0.6 * abs(warm))
    bg = oklch_to_rgb01(sL, sC, tint)
    if light:
        bg_soft = oklch_to_rgb01(max(0.0, sL - 0.032), sC * 1.35, tint)
        fg = oklch_to_rgb01(0.235, 0.010 + 0.004 * abs(warm), tint)
    else:
        bg_soft = oklch_to_rgb01(min(1.0, sL + 0.055), sC * 1.35, tint)
        fg = oklch_to_rgb01(0.945, 0.008, tint)

    # muted：次要文本色 —— 解到刚好过 4.5:1，但取"最亮仍达标"的那一档，别解成黑
    ml = solve_contrast(4.55, bg, 0.012, tint, 0.30, 0.90, ref_is_light=light)
    muted = oklch_to_rgb01(ml, 0.012, tint)

    # accent：低彩度锚点（chr=0）本质是"近中性 + 一点点色相"，不要硬撑成品牌色。
    # 浅色底上维持中等明度 0.50；但底色偏深（stone/slate）时要自动压暗，
    # 否则大字对比度会跌破 3:1 —— 这是加了 surface 维度之后新出现的边界。
    if light:
        aL = min(0.50, solve_contrast(3.05, bg, chroma, hue, 0.18, 0.92, True))
    else:
        aL = 0.74
    accent = oklch_to_rgb01(aL, chroma, hue)
    # accent-ink：可用作正文链接的强调色 —— 取"仍 ≥4.5:1 的最亮档"，保住色相辨识度
    ac = max(chroma * 0.85, 0.05)
    il = solve_contrast(4.55, bg, ac, hue, 0.20, 0.92, ref_is_light=light)
    accent_ink = oklch_to_rgb01(il, ac, hue)

    bg_h, fg_h = hex6(bg), hex6(fg)
    line_a = ".12" if light else ".16"
    line_rgb = "0,0,0" if light else "255,255,255"

    scale = [(n, round_px(px), exact) for n, px, exact in type_scale(base, r)]
    spaces = [(i + 1, sig["unit"] * m) for i, m in enumerate([1, 2, 3, 4, 6, 8, 12, 16])]
    rad = sig["rad"]
    if rad == 0:
        rad_sm, rad_lg = 0, 0
    elif rad >= 16:
        rad_sm, rad_lg = round(rad / 2), rad + 8
    else:
        rad_sm, rad_lg = max(2, round(rad / 2)), round(rad * 2)
    d1, d2, ease = MOTION[sig["mot"]]

    f_display, f_body, f_mono, f_cjk, f_source, f_note = resolve_fonts(
        fonts, anchor["slug"], anchor["family"], sig, pair)
    dname, bname = first_family(f_display), first_family(f_body)

    L = []
    A = L.append
    A(":root {")
    A(f"  /* ── 颜色（锚点 `{anchor['slug']}` 签名 · 底色档 `{sp.get('name','?')}` · 色相 {hue}° / 彩度档 {sig['chr']} / 色温 {warm:+.1f}）── */")
    A(f"  --bg:        {bg_h};   /* surface={sp.get('name','?')} · oklch({sL:.3f} {sC:.3f} {tint:.0f}) */")
    A(f"  --bg-soft:   {hex6(bg_soft)};")
    A(f"  --fg:        {fg_h};   /* 对 --bg 对比度 {contrast(fg, bg):.1f}:1 */")
    A(f"  --muted:     {hex6(muted)};   /* 对 --bg 对比度 {contrast(muted, bg):.1f}:1（正文下限 4.5） */")
    A(f"  --line:      rgba({line_rgb},{line_a});")
    A(f"  --accent:    {hex6(accent)};   /* 强调 / 装饰；大字下限 3:1 = {contrast(accent, bg):.1f}:1 */")
    A(f"  --accent-ink:{hex6(accent_ink)};   /* 可做正文链接，对比度 {contrast(accent_ink, bg):.1f}:1 */")
    A(f"  --accent-soft: rgba({','.join(str(round(c*255)) for c in accent)},.10);")
    A("")
    A(f"  /* ── 反同质化指纹（同批次内这三项都必须唯一）── */")
    A(f"  --surface:   \"{sp.get('name','?')}\";   /* 底色档 */")
    if variant:
        A(f"  --variant:   \"{variant['key']}\";   /* 尺度变体轴：{variant['label']} */")
    A("")
    A(f"  /* ── 字体（具名搭配 · 来源：{f_source}）── */")
    A(f"  --font-display: {f_display};")
    A(f"  --font-body:    {f_body};")
    A(f"  --font-mono:    {f_mono};")
    A(f"  --font-cjk:     {f_cjk};")
    A(f"  --font-display-name: \"{dname}\";   /* 反同质化比对用：全库唯一 */")
    A(f"  --font-body-name:    \"{bname}\";")
    if f_note:
        A(f"  /* 搭配理由：{f_note} */")
    wts = [w.strip() for w in sig["wts"].split(",")]
    disp_exp = 4.0 if r >= 1.4 else 5.0
    exp_of = {"xs": -1.0, "base": 0.0, "lg": 1.0, "xl": 2.0, "2xl": 3.0, "display": disp_exp}
    A(f"  --weight-display: {wts[-1]};   /* 标题取重端 */")
    A(f"  --weight-body:    {wts[0]};   /* 正文取轻端；字重总数 ≤2 */")
    A("")
    A(f"  /* ── 字阶（公比 {r}，基准 {base}px，6 级封顶）── */")
    for name, px, exact in scale:
        A(f"  --fs-{name}: {px:g}px;   /* {r}^{exp_of[name]:g} × {base} = {exact:.1f} */")
    A("")
    A("  /* ── 行高（字号越大越紧；CJK 主站整体上浮）── */")
    for name, _, _ in scale:
        A(f"  --lh-{name}: {leading(name, lh)};")
    A("")
    A("  /* ── 字距 ── */")
    A(f"  --trk-display: {sig['trk']}em;   /* 大字负字距 */")
    A(f"  --trk-heading: {round(sig['trk'] / 2, 4)}em;")
    A("  --trk-body:    0em;")
    A("  --trk-label:   0.08em;   /* 全大写 / 微标签正字距 */")
    A("")
    A(f"  /* ── 间距（基数 {sig['unit']}px，全部为它的整数倍）── */")
    for i, v in spaces:
        A(f"  --space-{i}: {v}px;")
    A("")
    A("  /* ── 形状 ── */")
    A(f"  --radius-sm: {rad_sm}px;")
    A(f"  --radius:    {rad}px;")
    A(f"  --radius-lg: {rad_lg}px;")
    A("  --shadow: none;   /* 用 --line 分区替代 */")
    A("")
    A("  /* ── 版心 ── */")
    A(f"  --measure: {sig['wrap']}px;   /* 主容器；全站共用，禁止各区块自定 max-width */")
    A(f"  --prose-width: {sig['ch']}ch;   /* 正文列宽目标（45–75ch 之间才算合格） */")
    A("  --gutter: 16px;   /* 页面边距，独立于纵向节奏栅格 */")
    A("")
    A(f"  /* ── 中轴（决定对齐策略，见 layouts.md）── */")
    A(f"  --axis: {anchor['axis']};")
    A("")
    A(f"  /* ── 动效（性格：{sig['mot']}）── */")
    A(f"  --dur-fast: {d1};")
    A(f"  --dur-normal: {d2};")
    A(f"  --ease: {ease};")
    A("}")
    return "\n".join(L), dict(
        bg=bg_h, fg=fg_h, contrast_bg=contrast(fg, bg),
        surface=sp.get("name", "?"),
        variant=(variant or {}).get("key", "a"),
        variant_label=(variant or {}).get("label", "原值"),
        font_display=dname, font_body=bname,
        font_source=f_source, font_note=f_note)


def main():
    ap = argparse.ArgumentParser(description="由设计参数签名生成 token 块")
    ap.add_argument("--anchor", help="锚点 slug（见 --list）")
    ap.add_argument("--list", action="store_true", help="列出所有锚点")
    ap.add_argument("--out", help="输出目录（会写 <anchor>.tokens.md）")
    ap.add_argument("--css-only", action="store_true", help="只打印 CSS，不带说明头")
    ap.add_argument("--lang", default="zh", choices=["zh", "en"], help="正文字体栈倾向（默认 zh）")
    ap.add_argument("--surface", help="底色档 white/paper/tint/stone/slate/ink/deep（覆盖锚点推荐值）")
    ap.add_argument("--variant", default="a", help="尺度变体轴 a 原值 / b 收紧 / c 放松 / d 张扬")
    ap.add_argument("--pair", type=int, default=0,
                    help="字体搭配序号：0 锚点主选（默认）/ 1-3 取族备用池")
    a = ap.parse_args()

    sigdoc = load_signatures()
    sigs = sigdoc["anchors"]
    idx_path = os.path.join(SKILL, "styles", "index.json")
    idx = json.load(open(idx_path, encoding="utf-8"))
    anchors = {x["slug"]: x for x in idx["anchors"]}
    presets = sigdoc.get("_surfacePresets") or {}
    axes = sigdoc.get("_variantAxes") or {}

    if a.list or not a.anchor:
        fam = {x["slug"]: x["family"] for x in idx["anchors"]}
        for slug in sorted(sigs):
            has = "★spec" if os.path.exists(os.path.join(SKILL, "styles", "specs", slug + ".md")) else "     "
            print(f"  {slug:<24} {fam[slug]:<14} {str(sigs[slug].get('surface','?')):<7} {has}")
        print(f"\n共 {len(sigs)} 个锚点。★ = 有本地完整 spec（配色以 spec 为准）。")
        print(f"底色档：{' / '.join(sorted(presets))}")
        ax_desc = " / ".join(f"{k}={v.get('label', k)}" for k, v in sorted(axes.items()))
        print(f"变体轴：{ax_desc}")
        return 0 if a.list else 1

    if a.anchor not in sigs:
        print(f"未知锚点：{a.anchor}（用 --list 查看）", file=sys.stderr)
        return 2
    if a.variant not in axes:
        print(f"未知 variant：{a.variant}（可用：{', '.join(sorted(axes))}）", file=sys.stderr)
        return 2

    sig, anchor = sigs[a.anchor], anchors[a.anchor]
    fonts = load_fonts()

    surf, surf_name, surf_src = resolve_surface(sigdoc, sig, a.surface)
    axis = axes.get(a.variant)
    variant = dict(axis, key=a.variant) if axis else None
    eff = apply_variant(sig, axis)

    css, meta = build(eff, anchor, a.lang, fonts, surf, variant, a.pair)
    meta["surface_source"] = surf_src
    spec = os.path.join(SKILL, "styles", "specs", a.anchor + ".md")
    never = anchor.get("never") or []
    when = anchor.get("when") or []

    header = [
        f"# {a.anchor} — token 骨架（由 signatures.json + fonts.json 确定性生成）",
        "",
        f"**族**：{anchor['family']} ｜ **布局原型**：`{anchor['layout']}` ｜ **中轴**：`{anchor['axis']}` ｜ "
        f"**image**：{anchor['imagePolicy']} ｜ **icon**：{anchor['iconPolicy']} ｜ **密度**：{anchor['density']}",
        f"**底色档**：`{meta['surface']}`（{meta.get('surface_source','')}）｜ "
        f"**变体轴**：`{meta['variant']}` {meta['variant_label']}",
        f"**字体搭配**：`{meta['font_display']}`（标题）× `{meta['font_body']}`（正文）—— 来源 {meta['font_source']}",
        "",
        "> **交付前先查批次账本**：`python scripts/ledger.py --check --anchor "
        f"{a.anchor} --surface {meta['surface']}` —— 若与同批次已交付的站撞车，换底色档或换变体轴，"
        "不要靠「看起来还行」蒙过去。",
        "",
    ]
    if meta["font_source"].startswith("⚠️"):
        header += [
            "> ⚠️ **字体降级**：本锚点未在 `styles/fonts.json` 命中具名搭配，已回退到通用栈。",
            "> 通用栈是 AI 均值味的来源 —— 请补 `styles/fonts.json` 的对应条目，不要就这样交付。",
            "",
        ]
    elif meta.get("font_note"):
        header += [f"> 搭配理由：{meta['font_note']}", ""]
    if os.path.exists(spec):
        header += [
            f"> ⚠️ 本锚点**有本地 spec**（`styles/specs/{a.anchor}.md`）。**配色与容器宽以 spec 为准**，"
            "本输出只补 spec 未系统给出的字阶 / 行高 / 字距 / 栅格。",
            "",
        ]
    else:
        header += [
            "> 本锚点**无本地 spec**，以下为签名生成结果 —— 它是**确定的、可复核的**设计参数，不是印象补全。",
            "> 可在此之上做锚点特化，但**不要**改成「看起来更高级」的通用值，那正是 AI 均值味的来源。",
            "> 要动字阶比 / 行高 / 行长三处，先读 `typography.md`。",
            "",
        ]
    header += ["```css", css, "```", ""]
    if never:
        header += ["## never（来自锚点注册表，必须逐条遵守）", ""]
        header += [f"- {n}" for n in never]
        header += [""]
    header += [
        "## 落地后必跑",
        "",
        "```",
        "python scripts/audit_tokens.py <你的 MASTER.md 或 tokens.css>",
        "```",
        "",
        "数值判据不过 = 没做完。判据清单见 `design-qa.md`。",
    ]

    text = css if a.css_only else "\n".join(header)
    if a.out:
        os.makedirs(a.out, exist_ok=True)
        suffix = ""
        if a.variant and a.variant != "a":
            suffix += f".{a.variant}"
        if a.surface:
            suffix += f".{a.surface}"
        if a.pair:
            suffix += f".p{a.pair}"
        p = os.path.join(a.out, f"{a.anchor}{suffix}.tokens.md")
        open(p, "w", encoding="utf-8").write(text + "\n")
        print(f"已写 {p}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
