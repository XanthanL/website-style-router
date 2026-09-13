#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""统一源材料提取器 —— 按扩展名路由到对应提取路径。

用法:
    python extract_source.py <input_path> <out_dir>
    <input_path> 可以是文件，也可以是目录（目录则遍历）

统一产出（所有类型共用同一套结构，下游只认这个）:
    <out_dir>/text.md        所有文本抽取结果，按来源分节（便于溯源）
    <out_dir>/assets/        图片 / 视频关键帧 / PPT 内嵌图
    <out_dir>/manifest.json  {source, type, units, assets[], warnings[]}
    <out_dir>/_WARNINGS.txt  需人工介入的事项（有才生成）

支持: .pdf .docx .xlsx .xlsm .csv .pptx .md .txt .json 图片 视频 音频 目录
不支持: .doc/.ppt/.wps 等旧二进制格式（本机无 libreoffice）→ 会给出明确降级指引

依赖: pip install pypdf pillow python-docx openpyxl python-pptx
      ffmpeg 需在 PATH（视频抽帧 / 音频转码用）
"""
import io
import json
import os
import shutil
import subprocess
import sys

IMG_EXT = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tif", ".tiff", ".avif", ".heic")
VID_EXT = (".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm")
AUD_EXT = (".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg")
TXT_EXT = (".md", ".txt", ".json", ".csv", ".srt", ".vtt")
OLD_OFFICE = (".doc", ".ppt", ".xls", ".wps", ".wpt", ".et", ".dps")

warnings = []
assets = []


def w(msg):
    warnings.append(msg)
    print("  [WARN] " + msg)


def have_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except Exception:
        return False


def sniff(raw_bytes):
    """真实图片格式（与扩展名无关）。"""
    try:
        from PIL import Image
        with Image.open(io.BytesIO(raw_bytes)) as im:
            return im.format
    except Exception:
        return None


def is_tiny_fragment(raw):
    """1px 分割线之类的碎片 —— PDF 里很常见，不是内容，应静默丢弃。"""
    try:
        from PIL import Image
        with Image.open(io.BytesIO(raw)) as im:
            return (im.size[0] <= 8 or im.size[1] <= 8) and len(raw) < 4096
    except Exception:
        return False


def save_jpeg(raw, out_dir, name, max_edge=2000, quality=88, drop_tiny=True):
    """白底压平 → 限长边 → JPEG。返回文件名；失败或碎片返回 None。"""
    from PIL import Image
    try:
        im = Image.open(io.BytesIO(raw))
        im.load()
    except Exception:
        return None
    # 丢弃分隔线级别的碎片（1px 分割线在 PDF 里很常见）
    if drop_tiny and (im.size[0] <= 8 or im.size[1] <= 8) and len(raw) < 4096:
        return None
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im, mask=im.split()[3])
        im = bg
    elif im.mode != "RGB":
        im = im.convert("RGB")
    wd, ht = im.size
    if max(wd, ht) > max_edge:
        s = max_edge / float(max(wd, ht))
        im = im.resize((max(1, int(wd * s)), max(1, int(ht * s))), Image.LANCZOS)
    fn = name + ".jpg"
    im.save(os.path.join(out_dir, fn), "JPEG", quality=quality, optimize=True, progressive=True)
    return fn


# ---------------------------------------------------------------- PDF
def do_pdf(path, out, adir):
    import pypdf
    r = pypdf.PdfReader(path)
    parts, n_img, text_total = [], 0, 0
    for pno, page in enumerate(r.pages, 1):
        try:
            t = (page.extract_text() or "").strip()
        except Exception:
            t = ""
        text_total += len(t)
        parts.append(f"\n### p{pno}\n\n{t}\n")
        try:
            imgs = list(page.images)
        except Exception:
            imgs = []
        for j, im in enumerate(imgs):
            raw = im.data
            if not raw:
                continue
            fmt = sniff(raw)
            if fmt is None:
                if len(raw) > 4096:
                    w(f"p{pno} 图 {j} 无法解码（真实格式 {fmt}）")
                continue
            # 1px 分割线在 PDF 里很常见，静默丢弃，不算失败
            if is_tiny_fragment(raw):
                continue
            fn = save_jpeg(raw, adir, f"p{pno:02d}_{j:02d}", drop_tiny=False)
            if not fn:
                w(f"p{pno} 图 {j} 保存失败（真实格式 {fmt}）")
                continue
            n_img += 1
            assets.append({"file": f"assets/{fn}", "page": pno, "srcFormat": fmt})
    if len(r.pages) >= 2 and text_total < len(r.pages) * 30:
        w("PDF 文字层几乎为空 —— 疑似扫描件。本机无 tesseract/OCR，"
          "请提供文字内容，或改用可搜索/可导出的 PDF。")
    return {"pages": len(r.pages), "images": n_img}, parts


# ---------------------------------------------------------------- DOCX
def do_docx(path, out, adir):
    import docx
    d = docx.Document(path)
    parts, n_img = [], 0
    for i, p in enumerate(d.paragraphs):
        t = p.text.strip()
        if not t:
            continue
        style = (p.style.name or "").lower()
        prefix = ""
        if "heading 1" in style:
            prefix = "# "
        elif "heading 2" in style:
            prefix = "## "
        elif "heading 3" in style:
            prefix = "### "
        elif "list" in style and not t.startswith(("-", "•", "*")):
            prefix = "- "
        parts.append(prefix + t)
    for ti, tb in enumerate(d.tables):
        parts.append(f"\n**表 {ti + 1}**\n")
        for row in tb.rows:
            parts.append("| " + " | ".join(c.text.strip().replace("\n", " ") for c in row.cells) + " |")
    # 内嵌图片
    for ri, rel in enumerate(d.part.rels.values()):
        if "image" in rel.reltype:
            try:
                raw = rel.target_part.blob
            except Exception:
                continue
            fn = save_jpeg(raw, adir, f"docx_{ri:02d}")
            if fn:
                n_img += 1
                assets.append({"file": f"assets/{fn}", "source": "docx embedded"})
    return {"paragraphs": len(d.paragraphs), "tables": len(d.tables), "images": n_img}, parts


# ---------------------------------------------------------------- XLSX / CSV
def do_sheet(path, out, adir):
    parts = []
    if path.lower().endswith(".csv"):
        import csv
        with open(path, "r", encoding="utf-8-sig", errors="replace", newline="") as f:
            rows = list(csv.reader(f))
        parts.append(f"### {os.path.basename(path)}\n")
        for row in rows[:400]:
            parts.append("| " + " | ".join(row) + " |")
        return {"sheets": 1, "rows": len(rows)}, parts
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True)
    total = 0
    for ws in wb.worksheets:
        parts.append(f"\n### sheet: {ws.title}  ({ws.max_row} 行 × {ws.max_column} 列)\n")
        for row in ws.iter_rows(max_row=min(ws.max_row, 400), values_only=True):
            cells = ["" if c is None else str(c) for c in row]
            if not any(cells):
                continue
            parts.append("| " + " | ".join(cells) + " |")
            total += 1
    if total > 300:
        w(f"表格较大（{total} 行），已截断到 400 行/表。大数据请直接用脚本读取而非全文塞进上下文。")
    return {"sheets": len(wb.worksheets), "rows": total}, parts


# ---------------------------------------------------------------- PPTX
def do_pptx(path, out, adir):
    from pptx import Presentation
    prs = Presentation(path)
    parts, n_img = [], 0
    for i, slide in enumerate(prs.slides, 1):
        buf = [f"\n### slide {i}"]
        for shp in slide.shapes:
            if shp.has_text_frame and shp.text_frame.text.strip():
                buf.append(shp.text_frame.text.strip())
        parts.append("\n".join(buf))
        for shp in slide.shapes:
            if shp.shape_type == 13 or getattr(shp, "image", None):
                try:
                    fn = save_jpeg(shp.image.blob, adir, f"slide{i:02d}")
                    if fn:
                        n_img += 1
                        assets.append({"file": f"assets/{fn}", "slide": i})
                except Exception:
                    pass
    return {"slides": len(prs.slides), "images": n_img}, parts


# ---------------------------------------------------------------- 图片 / 文本
def do_image(path, out, adir):
    with open(path, "rb") as f:
        raw = f.read()
    fmt = sniff(raw)
    base = os.path.splitext(os.path.basename(path))[0]
    fn = save_jpeg(raw, adir, base)
    if not fn:
        w(f"{os.path.basename(path)} 不是 PIL 可解码的图片（真实格式 {fmt}）—— 已原样复制，需人工确认")
        shutil.copy2(path, adir)
        return {"images": 0}, []
    assets.append({"file": f"assets/{fn}", "srcFormat": fmt, "srcName": os.path.basename(path)})
    return {"images": 1}, []


def do_text(path, out, adir):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        txt = f.read()
    return {"chars": len(txt)}, [f"\n### {os.path.basename(path)}\n\n{txt}"]


# ---------------------------------------------------------------- 视频 / 音频
def do_video(path, out, adir, adir_rel):
    if not have_ffmpeg():
        w("未找到 ffmpeg，无法抽帧。请手动提供 3–5 张关键帧截图（首帧/主体/结尾）。")
        return {"frames": 0}, []
    # 场景变化抽帧（阈值调到 0.3，避免抽到一堆几乎相同的帧）
    subprocess.run(["ffmpeg", "-y", "-i", path,
                    "-vf", "select='gt(scene,0.3)',scale='min(1600,iw)':-2",
                    "-vsync", "vfr", "-frames:v", "40",
                    os.path.join(adir, "frame_%03d.jpg")],
                   capture_output=True)
    # 首帧必取
    subprocess.run(["ffmpeg", "-y", "-ss", "0", "-i", path, "-frames:v", "1",
                    "-vf", "scale='min(1600,iw)':-2", os.path.join(adir, "frame_000.jpg")],
                   capture_output=True)
    frames = sorted(f for f in os.listdir(adir) if f.startswith("frame_"))
    for f in frames:
        assets.append({"file": f"assets/{f}", "source": "video keyframe"})
    # 音轨
    subprocess.run(["ffmpeg", "-y", "-i", path, "-vn", "-ac", "1", "-ar", "16000",
                    os.path.join(adir, "_audio.wav")], capture_output=True)
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip()
    w("视频已抽帧。**字幕/旁白没有自动转写**（本环境无 ASR）—— "
      "请提供视频文字稿，或我按关键帧描述画面（会明确标注为『观察』而非原文）。")
    return {"frames": len(frames), "durationSec": dur}, [f"\n### video {os.path.basename(path)}\n时长 {dur}s，抽帧 {len(frames)} 张 → assets/\n"]


def do_audio(path, out, adir):
    if not have_ffmpeg():
        w("未找到 ffmpeg，无法转码音频。请提供音频文字稿。")
        return {"audio": 0}, []
    subprocess.run(["ffmpeg", "-y", "-i", path, "-ac", "1", "-ar", "16000",
                    os.path.join(adir, "_audio.wav")], capture_output=True)
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip()
    w("音频已转 16k 单声道 wav。**没有自动转写**（本环境无 ASR / whisper 未装）—— "
      "请提供文字稿；否则只能按时长与文件名推断用途。")
    return {"durationSec": dur}, [f"\n### audio {os.path.basename(path)}\n时长 {dur}s → assets/_audio.wav\n"]


# ---------------------------------------------------------------- 路由
def route(path, out, adir):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return "pdf", do_pdf(path, out, adir)
    if ext == ".docx":
        return "docx", do_docx(path, out, adir)
    if ext in (".xlsx", ".xlsm", ".csv"):
        return "sheet", do_sheet(path, out, adir)
    if ext == ".pptx":
        return "pptx", do_pptx(path, out, adir)
    if ext in IMG_EXT:
        return "image", do_image(path, out, adir)
    if ext in VID_EXT:
        return "video", do_video(path, out, adir, adir)
    if ext in AUD_EXT:
        return "audio", do_audio(path, out, adir)
    if ext in TXT_EXT:
        return "text", do_text(path, out, adir)
    if ext in OLD_OFFICE:
        w(f"**旧版二进制格式 {ext} 本机无法解析**（无 libreoffice）。"
          f"请在 Word/PPT/WPS 里另存为 .docx/.pptx 或导出 PDF 后重跑。")
        return "unsupported", ({}, [])
    w(f"未识别的扩展名 {ext} —— 已原样复制到 assets/，需人工确认如何处理。")
    try:
        shutil.copy2(path, adir)
    except Exception:
        pass
    return "unknown", ({}, [])


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    src, out = sys.argv[1], sys.argv[2]
    adir = os.path.join(out, "assets")
    os.makedirs(adir, exist_ok=True)

    if os.path.isdir(src):
        files = []
        for root, _, names in os.walk(src):
            for n in names:
                if not n.startswith("."):
                    files.append(os.path.join(root, n))
        files.sort()
    else:
        files = [src]

    meta, parts = {}, []
    for f in files:
        print(f"[{os.path.splitext(f)[1].lower() or '?'}] {os.path.basename(f)}")
        n_assets_before = len(assets)
        kind, (info, txt) = route(f, out, adir)
        meta[os.path.basename(f)] = {"type": kind, **info,
                                     "assets": len(assets) - n_assets_before}
        if txt:
            parts.append(f"\n## 来源: {os.path.basename(f)}\n" + "\n".join(txt))

    with open(os.path.join(out, "text.md"), "w", encoding="utf-8") as fh:
        fh.write("".join(parts) or "（无文本内容被提取）")
    with open(os.path.join(out, "manifest.json"), "w", encoding="utf-8") as fh:
        json.dump({"source": src, "files": meta, "assets": assets,
                   "warnings": warnings}, fh, ensure_ascii=False, indent=2)
    if warnings:
        with open(os.path.join(out, "_WARNINGS.txt"), "w", encoding="utf-8") as fh:
            fh.write("\n".join("- " + x for x in warnings))

    print(f"\nfiles      : {len(files)}")
    print(f"assets     : {len(assets)}")
    print(f"warnings   : {len(warnings)}")
    print(f"-> {os.path.join(out, 'text.md')}")
    print(f"-> {os.path.join(out, 'manifest.json')}")


if __name__ == "__main__":
    main()
