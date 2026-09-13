#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PDF -> 图片资产提取 + 真实格式归一化 + 页图/文本映射。

用法:
    python extract_pdf_assets.py <input.pdf> <out_dir>

产出:
    <out_dir>/p<page>_<idx>.jpg       归一化后的图片（真实编码，统一 JPEG）
    <out_dir>/manifest.json           [{page, index, file, w, h, bytes, src_format, text}]
    <out_dir>/_CONVERTED.txt          被改过扩展名的文件清单（若为空则不生成）

为什么需要这个脚本 —— 这不是可选项
    pypdf / PyMuPDF 抓图时按 PDF 流的 /Filter 猜扩展名。JPXDecode 流会被写成 .png，
    但内容其实是 JPEG2000(JP2)。后果极其隐蔽：
      Chrome / Edge 不支持 JP2（只有 Safari 能解）
      → HTTP 200、控制台零报错、图片位置只留一个空框。
    所以「引用对了、状态码 200」并不能证明图片能显示。必须用 PIL 读真实 format。

依赖: pip install pypdf pillow
"""
import io
import json
import os
import sys
from collections import OrderedDict

try:
    from PIL import Image
except ImportError:
    sys.exit("需要 pillow: pip install pillow")
try:
    import pypdf
except ImportError:
    sys.exit("需要 pypdf: pip install pypdf")


def sniff_format(raw: bytes):
    """返回 (PIL format, 是否支持浏览器直出)。不依赖扩展名。"""
    try:
        with Image.open(io.BytesIO(raw)) as im:
            return im.format, im.format in ("JPEG", "PNG", "WEBP", "GIF")
    except Exception:
        return None, False


def normalize_jpeg(raw: bytes, max_edge: int = 2000, quality: int = 88) -> bytes:
    """压平 alpha（白底）→ 限长边 → 存渐进式 JPEG。返回新字节。"""
    with Image.open(io.BytesIO(raw)) as im:
        im = im.convert("RGBA") if im.mode in ("RGBA", "LA", "P") else im.convert("RGB")
        if im.mode == "RGBA":
            bg = Image.new("RGB", im.size, (255, 255, 255))
            bg.paste(im, mask=im.split()[3])
            im = bg
        elif im.mode != "RGB":
            im = im.convert("RGB")
        w, h = im.size
        if max(w, h) > max_edge:
            scale = max_edge / float(max(w, h))
            im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
        out = io.BytesIO()
        im.save(out, "JPEG", quality=quality, optimize=True, progressive=True)
        return out.getvalue()


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    src, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)

    reader = pypdf.PdfReader(src)
    seen = {}
    manifest = []
    converted = []
    idx = 0

    for page_no, page in enumerate(reader.pages, 1):
        try:
            page_text = (page.extract_text() or "").strip()
        except Exception:
            page_text = ""
        try:
            images = list(page.images)
        except Exception:
            images = []

        for j, im in enumerate(images):
            raw = im.data
            if not raw:
                continue
            fmt, browser_ok = sniff_format(raw)
            # 丢弃分隔线级别的碎片（<2KB 且任一边 <=8px）
            try:
                with Image.open(io.BytesIO(raw)) as probe:
                    pw, ph = probe.size
            except Exception:
                continue
            if len(raw) < 2048 and (pw <= 8 or ph <= 8):
                continue

            ext = (im.name.rsplit(".", 1)[-1] if "." in im.name else "").lower()
            need_convert = (not browser_ok) or (ext not in ("jpg", "jpeg", "png", "webp"))
            data = normalize_jpeg(raw) if need_convert else raw
            new_ext = "jpg" if need_convert else ("jpg" if ext in ("jpg", "jpeg") else ext)

            key = hash(data)
            if key in seen:
                manifest.append(OrderedDict(
                    page=page_no, index=j, file=seen[key], dup_of=seen[key],
                    src_format=fmt, note="duplicate"))
                continue

            idx += 1
            fname = f"p{page_no:02d}_{j:02d}.{new_ext}"
            with open(os.path.join(out_dir, fname), "wb") as f:
                f.write(data)
            seen[key] = fname

            if need_convert:
                converted.append(f"{fname}  <-  原名 {im.name} ({fmt})")
            with Image.open(io.BytesIO(data)) as chk:
                cw, ch = chk.size
                cfmt = chk.format

            manifest.append(OrderedDict(
                page=page_no, index=j, file=fname, w=cw, h=ch,
                bytes=len(data), src_format=fmt, out_format=cfmt,
                text=page_text[:400]))

    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    if converted:
        with open(os.path.join(out_dir, "_CONVERTED.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(converted))

    total_mb = sum(m.get("bytes", 0) for m in manifest) / 1048576.0
    print(f"pages      : {len(reader.pages)}")
    print(f"unique imgs: {len(seen)}")
    print(f"converted  : {len(converted)}  (扩展名/编码不一致，已归一化)")
    print(f"total      : {total_mb:.1f} MB")
    if converted:
        print("\n被归一化的文件（必须同步改写数据引用）:")
        for c in converted:
            print("  " + c)
    print(f"\nmanifest -> {os.path.join(out_dir, 'manifest.json')}")


if __name__ == "__main__":
    main()
