# Source — 源材料提取与溯源规程

> **Phase -1 必读。** 用户给的往往不是"文案"，而是一份 PDF、一个图库、一个现有网站、一段视频、甚至一句话。
> 在 Grill 之前，先把**源材料变成结构化、可溯源的数据**。跳过这一步，后面每一条结论都是猜的。

## 铁律

1. **先看清源是什么，再谈做什么。** 不同源类型的提取方式差别极大，不问就动手 = 后面全部返工。
2. **提取必须是脚本，不是手抄。** 手抄 62 张图名、17 个作品必然出错（本次真实踩过：`p16` 实为 `.png` 抄成 `.jpg`、年份抄错、作品名 `Phantom Limb` 抄成 `Imaginary Limbs`）。脚本写一次，反复可跑。
3. **每条文案/每张图都必须能指回源。** 溯源格式：`p12 · "原句"` 或 `<url> #selector`。指不回去的字符串就是编的，删掉。
4. **扩展名不是格式。** 见「格式欺骗」。
5. **只增不丢。** 源里有、决定不用的，必须在 `source-map.md` 写明理由；静默丢弃 = 交付不完整。
6. **提取不了的，明说提取不了。** 本机没有的工具（OCR、ASR）不许假装有，要给用户明确的降级方案。

---

## 一键提取器

所有文本类与图片类源统一走同一个脚本，**产出结构一致**，下游只认这一套：

```bash
python scripts/extract_source.py <输入路径(文件或目录)> <输出目录>
```

产出：

```
<out>/text.md          所有文本，按来源分节（含 p1 / slide 1 / sheet 名）
<out>/assets/          图片 / 视频关键帧 / 文档内嵌图  ← 全部已归一化为真实 JPEG
<out>/manifest.json    {source, files{类型+单位数+资产数}, assets[], warnings[]}
<out>/_WARNINGS.txt    需人工介入的项（有才生成）
```

脚本会自动：按真实编码归一化图片、丢弃 1px 分割线、检测"扫描件无文字层"、给出旧格式的降级指引。

---

## 输入类型 → 处理预案（完整表）

### 1 · PDF

| 子类型 | 识别 | 处理 |
|---|---|---|
| 文字型 / 图册型 | 有文字层（多数设计稿） | `extract_source.py` → 页级文本 + 图片 + `manifest.json` 的 `page` 字段建立"图→页→文字"绑定 |
| 扫描型 | 页多而文字量 <30 字/页 | **本机若无 OCR**（默认环境即如此，用 `check_env.py` 确认）→ 请用户提供文字内容，或换成可搜索/可导出的 PDF |

- **图归属不能靠看图猜**，只认 `manifest.json` 里 `page` 与同页文本的绑定。
- **坑**：`JPXDecode` 流被写成 `.png`（见下）；单张最大可达 3MB，62 张就 38MB。
- **校验**：`python scripts/verify_assets.py <assets> <data.json>`

### 2 · 图片（单张 / 文件夹 / 压缩包）

- 单张 / 文件夹 → `extract_source.py`（自动归一化为 JPEG、丢弃碎片、列出尺寸）
- 压缩包 → **先解压再跑**（`unzip` / Windows 用 `Expand-Archive`），**不要**直接把 zip 当输入
- **坑**：`heic`（iPhone 默认）PIL 常读不了 → 明确告知用户转 jpg；`.avif` 同理
- **产出后**：按尺寸与比例分桶（横/竖/方），这直接决定布局原型能否成立

### 3 · 文档（docx / doc / wps）

- `.docx` → `python-docx`（**需先安装**，`check_env.py` 会告知）：段落 + 标题层级 + 列表 + 表格 + 内嵌图
- `.doc` / `.wps` / `.wpt`（旧二进制）→ **本机若无 libreoffice**（默认环境即如此）。给用户的降级方案：另存为 `.docx`，或导出 PDF
- ⚠️ 若宿主自带 Office 文件专用通道（某些 agent 有专门的文档 skill / 插件），**生成/编辑** Office 文件走它；**读取**用本脚本即可，不依赖任何宿主能力

### 4 · 纯文本 / Markdown / TXT / JSON / SRT

- 直接读，几乎无损耗
- `SRT/VTT`（字幕）→ 天然带时间轴，是视频内容的**最佳替代源**（比抽帧描述准得多）
- **坑**：编码。中文文件可能是 GBK → 用 `errors="replace"` 读并在 warning 里标注可疑乱码

### 5 · 表格（xlsx / xlsm / csv）

- `csv` → 标准库；`xlsx` → `openpyxl`（**需先安装**，`check_env.py` 会告知；用 `data_only=True` 取计算值）
- 每表最多转 400 行 Markdown，超出截断并 warning
- **坑**：`xlsx` 里存的是公式而非值 → `data_only=True` 也拿不到未缓存的公式结果，需用户另存
- **用途**：SKU 表 / 展览清单 / 价目表 —— 这是 `commerce` 与 `institutional` 族的直接数据源

### 6 · 演示（pptx / ppt / key）

- `.pptx` → `python-pptx`（**需先安装**，`check_env.py` 会告知）：逐页文本 + 内嵌图
- `.ppt` / `.key` → 无解 → 请另存为 `.pptx` 或导出 PDF
- **坑**：PPT 的文本常在文本框而非占位符里，图常在形状填充里 —— 脚本两条都取

### 7 · 视频（mp4 / mov / mkv / webm）

- **有 ffmpeg 时**（`check_env.py` 会告知）→ 场景变化抽帧（`scene>0.3`，最多 40 帧）+ 首帧 + 音轨转 16k wav
- ⛔ **没有 ASR**：**旁白/字幕不会自动转写**
- 降级顺序（按优先级）：
  1. 请用户提供**字幕文件**（`.srt`）→ 最准
  2. 请用户提供文字稿
  3. 我按关键帧写**画面描述**，并**明确标注为「观察」而非原文**
- 绝不把"我以为视频里说了什么"当成文案写进站

### 8 · 音频（mp3 / wav / m4a）

- 有 ffmpeg 时转 16k 单声道 wav（本 skill 不内置 ASR，转码只是为将来接 ASR 预留）
- ⛔ 同视频：**没有转写能力** → 一律请用户提供文字稿
- **不允许**按时长/文件名猜内容

### 9 · 现有网站（要改造的那一个）

- 本地项目 → 直接读源码：路由表、现有区块清单、现用 token、组件清单
- 线上 URL → 抓 DOM 结构 + `<link rel=stylesheet>` 的 CSS
- **这是 `embedded` 形态的前置动作**，产出 `design-system/HOST.md`（见 `host-align.md`）

### 10 · 参考站（用户说"像 X 那样"）

- URL / 截图 / Figma 都算。走下方「参考站采集」
- ⚠️ **Figma 是参考，不是资产源**：从 Figma 截图里抠图会得到低质素材，要请用户导出原始图片

### 11 · 只有一段文字要求

- **不许脑补内容**。走 Grill（`intake.md`）把内容问出来
- 产出 `content-profile.md` 的「待补」表，页面用 `[待填]` + 红色虚线框标记
- 只有一句需求时，**先确认能否用"占位结构 + 待补清单"交付**，而不是编一套看起来完整的内容

### 12 · 混合多源（常态）

- **主源定内容，副源定风格**：主源（PDF/表格）提供文字与图，副源（参考站/现有站）提供视觉语言
- 冲突时**主源赢内容，副源赢形式**
- 两个源互相矛盾（同一人两个年份）→ **停下来问用户**（`decide.md` 触发条件 3）

### 13 · 什么都没有

- 走 Phase 0 的完整 Grill，并把"没有素材"作为**硬约束**输入筛选：
  无图 → 排除依赖图的所有布局原型（`editorial-hero` / `catalog-grid` / `split-narrative`）

---

## 格式欺骗（本次踩过的坑，必查）

pypdf / PyMuPDF 按 PDF 流的 `/Filter` 猜扩展名：

- `JPXDecode`（JPEG2000 / JP2）流会被写成 **`.png`**
- Chrome / Edge **不支持 JP2**（只有 Safari 能解）
- 后果：**HTTP 200、控制台零报错、图片位置只留空框**
- 所以「引用对了 + 状态码 200」**不能证明图片能显示**

`extract_source.py` / `extract_pdf_assets.py` 已内置归一化（PIL 读真实 format → 白底压平 → 长边 2000 → JPEG q88 progressive）。
手写流程必须自己查：

```python
from PIL import Image
fmt = Image.open(path).format      # 真实格式，与扩展名无关
```

**任何从 PDF / 设计稿拿到的图，交付前都要过一遍 `verify_assets.py`。**

---

## 参考站采集

不要凭记忆描述某个网站的风格。**实测。**

1. 首屏与关键区块截图（用宿主提供的浏览器/截图能力：agent-browser / Playwright / Chrome DevTools MCP 均可；都没有就请用户截图）
2. 采 CSS 与计算样式：
   - `:root` 自定义属性（色板 / 字阶 / 间距 / 圆角 / 动效曲线）
   - `body` / `h1-h6` / `a` 的字体栈、行高、字距
   - `max-width` 与栅格断点
3. 记**结构性特征**而不只是颜色：中轴、密度、圆角策略、有无分割线、图占比重、动效时长
4. 落成 `references.md`：

```markdown
## 参考站 A — <url>（抓取时间）
- 截图：references/a-hero.png
- 色板：--bg #… / --fg #… / --accent #…
- 字体：sans=… serif=… mono=…
- 中轴：left / center    密度：高 / 中 / 低
- 结构特征：<分割线？圆角？图占比重？>
- **学它的什么**：<具体 3 条>
- **不学它的什么**：<具体 2 条，防止整套照抄>
```

5. **"像它" ≠ "抄它"。** 必须写「不学它的什么」，否则输出会成为该站的劣质复制品。
6. 用户自己已有的站（如 game-lab 的 ~70 种 `data-style`）按**灵感池**处理：取机制不取皮。

---

## 溯源映射表（source-map.md）

提取完立刻建。**后续所有内容都从这里取，不再回头翻源文件。**

```markdown
# Source Map

## 源
| 源 | 类型 | 提取方式 | 产出 |
|---|---|---|---|
| `<path>` | PDF 26页 | `extract_source.py` | 58 图 / text.md / manifest.json |
| `<url>` | 参考站 | 浏览器能力截图 + 抓 CSS（降级：用户截图 + 手工摘 CSS） | references.md |
- 校验：`verify_assets.py` → PASS（缺失 0 / 未用 0 / 格式 0）

## 内容映射
| 目标字段 | 值 | 溯源 | 备注 |
|---|---|---|---|
| works[0].title | Burning Dust | p16 | 源里为整页独立作品，首轮漏收 |
| works[3].title | Electronic Disease—Phantom Limb | p12 正文原句 | 曾误抄为 "Imaginary Limbs" |
| works[6].year | 2016 | p21 正文 "August 2016" | 曾误抄为 2017 |
| about.portrait | assets/p02_00.jpg | p2 | |

## 未采用的源内容
| 内容 | 理由 |
|---|---|
| assets/p08_01.jpg | 与 p08_00 同 MD5（重复） |
| 源 p3 的展评引文 | 第三方署名评论，不适合放入个人站正文 |

## 提取告警（_WARNINGS.txt 原文）
| 告警 | 影响 | 处置 |
|---|---|---|
| 视频无 ASR，未转写 | 缺少旁白文案 | 已请用户提供字幕 |
```

**核对动作**：交付前逐行回源抽查，尤其是**年份、作品名、人名、数字**——这四类抄错率最高。

---

## 输出契约（Phase -1 结束标志）

- [ ] `source-map.md` 存在，含「源 / 内容映射 / 未采用 / 提取告警」四段
- [ ] 每条 `_WARNINGS.txt` 里的告警都已在 `source-map.md` 记明**影响与处置**
- [ ] 素材目录通过 `verify_assets.py`（缺失 0 / 未用 0 / 格式 0 / 体积 < 15MB）
- [ ] 若有参考站 → `references.md` 存在，且写了「不学它的什么」（≥2 条）
- [ ] 每个待渲染字段都能指出它来自哪一页 / 哪个 URL / 哪个 slide / 哪个单元格
- [ ] 指不回去的字段，集中进 `content-profile.md` 的「待补」表，**不用编造值填**
