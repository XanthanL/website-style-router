#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""素材双向比对 + 真实格式校验 + 体积统计。

用法:
    python verify_assets.py <assets_dir> <data_file> [data_file ...]

data_file 可以是 .json / .astro / .tsx / .md / .css —— 脚本只做正则扫描，
把其中出现的 p12_03.jpg / p12_03.png 之类文件名当成引用。

检查四件事（任一不过 → 退出码 1）:
    1. 缺失引用   数据里引用了、磁盘上没有        （会 404）
    2. 未使用素材 磁盘上有、没有任何数据引用      （白交付了）
    3. 格式不一致 扩展名 ≠ PIL 读出的真实 format  （JPEG2000 伪 .png = 静默空框）
    4. 体积超标   总量 >= 阈值（默认 15MB）

依赖: pip install pillow
"""
import json
import os
import re
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("需要 pillow: pip install pillow")

REF_RE = re.compile(r"[A-Za-z0-9_\-/]*p(\d{2})_(\d{2})\.(jpg|jpeg|png|webp|gif)", re.I)
# 宽松匹配：只用来判断「磁盘上这个文件到底有没有被任何数据引用」，避免把 keep.jpg
# 这类非 pXX_YY 命名误判为 unused。missing 仍只报 pXX_YY 命名的引用（避免把
# 导航里的 logo.png 这类别处资源误报为缺失）。
ANY_RE = re.compile(r"([A-Za-z0-9_\-]+\.(?:jpg|jpeg|png|webp|gif))", re.I)
EXT_OK = {"jpg": ("JPEG",), "jpeg": ("JPEG",), "png": ("PNG",), "webp": ("WEBP",), "gif": ("GIF",)}
SIZE_LIMIT_MB = 15.0


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    assets_dir = sys.argv[1]
    data_files = sys.argv[2:]

    disk = sorted(f for f in os.listdir(assets_dir)
                  if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")))

    # ---- 收集引用 ----
    refs = set()       # pXX_YY 命名（用于 missing 判定）
    refs_any = set()   # 任意图片名（用于 unused 判定）
    for df in data_files:
        with open(df, "r", encoding="utf-8", errors="replace") as fh:
            content = fh.read()
        for m in REF_RE.finditer(content):
            refs.add(m.group(0).split("/")[-1].lower())
        for m in ANY_RE.finditer(content):
            refs_any.add(m.group(1).lower())

    disk_set = {d.lower() for d in disk}
    missing = sorted(refs - disk_set)
    unused = sorted(disk_set - refs_any)

    # 归一化扩展名后二次比对（数据写 .png、脚本已把文件改成 .jpg 的情况）
    stem = lambda s: s.rsplit(".", 1)[0]
    missing_soft = sorted({m for m in missing if stem(m) in {stem(d) for d in disk_set}})

    # ---- 格式校验 ----
    mismatch = []
    total = 0
    for f in disk:
        p = os.path.join(assets_dir, f)
        total += os.path.getsize(p)
        ext = f.rsplit(".", 1)[-1].lower()
        try:
            with Image.open(p) as im:
                fmt = im.format
        except Exception as e:
            mismatch.append((f, f"OPEN_FAIL {e}"))
            continue
        if fmt not in EXT_OK.get(ext, ()):
            mismatch.append((f, fmt))

    # ---- 报告 ----
    print(f"assets dir  : {assets_dir}")
    print(f"data files  : {len(data_files)}")
    print(f"disk        : {len(disk)} files / {total / 1048576.0:.1f} MB")
    print(f"referenced  : {len(refs)}")
    print(f"missing     : {len(missing)}")
    for m in missing:
        tag = "  ~ 扩展名不符，磁盘有同名不同扩展名" if m in missing_soft else "  × 磁盘无此文件"
        print(f"    {m}{tag}")
    print(f"unused      : {len(unused)}")
    for u in unused:
        print(f"    {u}")
    print(f"fmt mismatch: {len(mismatch)}")
    for f, fmt in mismatch:
        print(f"    {f} -> 真实 {fmt}")

    ok = not missing and not unused and not mismatch and total / 1048576.0 < SIZE_LIMIT_MB
    if total / 1048576.0 >= SIZE_LIMIT_MB:
        print(f"\n! 体积 {total / 1048576.0:.1f} MB 超阈值 {SIZE_LIMIT_MB} MB —— 上线前须压缩/响应式化")
    print("\nRESULT:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
