#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""环境能力探测 —— 首次运行本 skill 时先跑这个，别凭印象说"本机有这个"。

用法:
    python check_env.py            # 人类可读的能力表
    python check_env.py --json     # 机器可读（供 agent 直接解析）

探测四类：
    1. Python 运行时与版本（脚本要求 3.10+）
    2. Python 包     pypdf / Pillow（必需）；python-docx / openpyxl / python-pptx（按源格式按需）
    3. 外部命令      ffmpeg / ffprobe（视频抽帧）、node / npm / npx（仅产物为站点时需要）
    4. 常被误认为有的能力：OCR(tesseract) / ASR(whisper) / libreoffice / pandoc

退出码恒为 0（这是信息性探测，不是校验）。缺什么会直接给出**降级方案**。
"""
import json
import os
import platform
import shutil
import subprocess
import sys

MIN_PY = (3, 10)

# (import 名, pip 名, 是否必需, 用途, 缺失时的降级方案)
PY_PKGS = [
    ("pypdf", "pypdf", True, "PDF 文本与图片提取", "无法处理 PDF → 请用户导出为 docx/md，或提供图片"),
    ("PIL", "pillow", True, "图片真实编码格式校验与重编码", "无法识别 JP2 伪 .png 的静默空框 → 必须让用户人工确认图片可显示"),
    ("docx", "python-docx", False, " .docx 文本与内嵌图片提取", "pip install python-docx；或请用户另存为 md"),
    ("openpyxl", "openpyxl", False, ".xlsx / .csv 读取", "pip install openpyxl；或请用户导出 CSV"),
    ("pptx", "python-pptx", False, ".pptx 文本与图片提取", "pip install python-pptx；或请用户导出 PDF"),
]

# (命令名, 是否必需, 用途, 缺失时的降级方案)
BINS = [
    ("ffmpeg", False, "视频抽帧 / 音频转码", "无法处理视频 → 请用户提供关键帧截图或已转好的音频"),
    ("ffprobe", False, "读取媒体时长与轨道信息", "无法预判视频规模 → 保守取首帧"),
    ("node", False, "构建产物站点（Astro/Next）时需要", "改用纯 HTML+CSS 产出，或请用户安装 Node 18+"),
    ("npm", False, "同上（安装依赖、跑 build）", "同上"),
    ("npx", False, "可选外部工具：npx typeui.sh pull <slug>", "改用本地 styles/specs/ 与 _specFallback 降级"),
    ("git", False, "克隆示例 / 版本管理", "不影响建站流程"),
    # 明确探测"常被误以为有"的：
    ("tesseract", False, "OCR（扫描件取字）", "本机无 OCR → 必须请用户提供文字或可搜索 PDF，不许假装能识别"),
    ("whisper", False, "ASR（视频旁白转写）", "本机无 ASR → 必须请用户提供 .srt 字幕或文字稿，不许假装能听写"),
    ("soffice", False, "LibreOffice 转换旧格式 .doc/.ppt/.wps", "旧格式不支持 → 请用户另存为 .docx/.pptx 或导出 PDF"),
    ("pandoc", False, "万物转 markdown", "改用 scripts/extract_source.py 的对应分支"),
]


# 取版本号用的参数各不相同，别统一用 -version（node / git 会报 bad option）
VER_ARGS = {
    "ffmpeg": ["-version"], "ffprobe": ["-version"], "soffice": ["--version"],
    "node": ["--version"], "npm": ["--version"], "npx": ["--version"],
    "git": ["--version"], "tesseract": ["--version"], "whisper": ["--help"],
    "pandoc": ["--version"],
}


def has_bin(name):
    return shutil.which(name)


def probe():
    py = sys.version_info
    pym = {"version": platform.python_version(), "executable": sys.executable,
           "ok": (py.major, py.minor) >= MIN_PY}
    pkgs = []
    for mod, pipname, required, why, fix in PY_PKGS:
        try:
            m = __import__(mod)
            v = getattr(m, "__version__", None)
            if v is None and mod == "pptx":
                v = getattr(__import__("pptx"), "__version__", None)
            pkgs.append({"module": mod, "pip": pipname, "required": required,
                         "present": True, "version": str(v) if v else "unknown",
                         "use": why, "fallback": fix})
        except Exception:
            pkgs.append({"module": mod, "pip": pipname, "required": required,
                         "present": False, "version": None, "use": why, "fallback": fix})
    bins = []
    for name, required, why, fix in BINS:
        path = has_bin(name)
        ver = None
        if path:
            try:
                out = subprocess.run([name] + VER_ARGS.get(name, ["--version"]),
                                     capture_output=True, text=True, timeout=8,
                                     errors="replace")
                line = (out.stdout or out.stderr or "").strip().splitlines()
                ver = line[0][:80] if line else "present"
            except Exception:
                ver = "present"
        bins.append({"cmd": name, "required": required, "present": bool(path),
                     "path": path, "version": ver, "use": why, "fallback": fix})
    return {"python": pym, "python_packages": pkgs, "binaries": bins, "platform": {
        "system": platform.system(), "release": platform.release(), "machine": platform.machine(),
        "is_windows": os.name == "nt"}}


def report(d):
    p = d["python"]
    print("=" * 68)
    print("website-style-router · 环境能力探测")
    print("=" * 68)
    print(f"平台    : {d['platform']['system']} {d['platform']['release']} ({d['platform']['machine']})")
    print(f"Python  : {p['version']}  {'OK' if p['ok'] else '!! 需要 >= %d.%d' % MIN_PY}")
    print(f"解释器  : {p['executable']}")

    print("\n-- Python 包 " + "-" * 55)
    miss_req, miss_opt = [], []
    for k in d["python_packages"]:
        mark = "OK  " if k["present"] else ("MISS" if k["required"] else "----")
        print(f"[{mark}] {k['pip']:<14} {k['version'] or '未安装':<12} {k['use']}")
        if not k["present"]:
            (miss_req if k["required"] else miss_opt).append(k)

    print("\n-- 外部命令 " + "-" * 56)
    absent = []
    for b in d["binaries"]:
        mark = "OK  " if b["present"] else "----"
        print(f"[{mark}] {b['cmd']:<11} {(b['version'] or '未找到')[:52]}")
        if not b["present"]:
            absent.append(b)

    print("\n-- 结论 " + "-" * 60)
    if not p["ok"]:
        print(f"x Python {p['version']} 低于要求，脚本可能无法运行。请升级到 3.10+。")
    if miss_req:
        print("x 必需包缺失：" + ", ".join(k["pip"] for k in miss_req))
        print("  安装： pip install " + " ".join(k["pip"] for k in miss_req))
    else:
        print("v 必需包齐备 —— PDF 提取与图片格式校验可用。")
    if miss_opt:
        print("i 按需包未装（遇到对应源格式再装即可）：" + ", ".join(k["pip"] for k in miss_opt))
    print("v 可用能力：PDF / 图片 / 文本 / Markdown" +
          ("" if not has_bin("ffmpeg") else " / 视频抽帧"))

    # 降级提醒只针对会影响流程判断的项
    notices = [b for b in absent if b["cmd"] in
               ("ffmpeg", "node", "npm", "tesseract", "whisper", "soffice")]
    if notices:
        print("\nx 必须向用户明说的限制（不许假装能做到）：")
        for b in notices:
            print(f"   · {b['cmd']:<10} {b['use']}")
            print(f"     -> {b['fallback']}")
    print("\n提示：本表是信息性探测，不作为校验。缺什么按上面的降级方案走，"
          "并把限制写进交付说明（SKILL.md 铁律 17）。")


def main():
    d = probe()
    if "--json" in sys.argv:
        print(json.dumps(d, ensure_ascii=False, indent=2))
    else:
        report(d)
    sys.exit(0)


if __name__ == "__main__":
    main()
