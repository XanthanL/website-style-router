# 使用教学 —— 从零到改得动


> 本文回答**「怎么做」**：装在哪、每道门在干什么、每个命令怎么用、想改东西动哪个文件。
> 想知道**「为什么这样设计」**，看 [`CONCEPTS.md`](CONCEPTS.md)。
>
> **建议读法**：
> - 只想用起来 → §1 + §2
> - 想查命令 → §3（命令手册）
> - 想改东西 → §4（自定义实战），按难度从 ① 到 ⑧ 走
> - 撞到报错 → §5（排错手册）
> - 要做「老样例 vs 2.0 对比」→ §6

---

## §0 这份文档怎么用

这套 skill 有两种使用方式，**不要混着理解**：

| 角色 | 你做什么 | 你读什么 |
|---|---|---|
| **使用者** | 把内容丢给 agent，让它跑完流程 | §1、§2、§6 |
| **维护者** | 改 skill 本身（加锚点、调参数、加判据） | §3、§4、§5 |

**关键区别**：作为使用者，你**不跑** `emit_tokens.py`——那是 agent 干的活。你只在「G2 落定」那一步点头。

---

## §1 安装与首次运行

### 1.1 装在哪

把整个 `website-style-router/` 目录放进任意 agent 的 skills 目录即可。**路径全部相对于 skill 根目录，无宿主专有依赖。**

| Agent | 放置位置 |
|---|---|
| Claude Code | `~/.claude/skills/website-style-router/` 或项目内 `.claude/skills/website-style-router/` |
| Codex | `.codex/skills/website-style-router/` |
| Cursor | `.cursor/skills/website-style-router/` |
| WorkBuddy / CodeBuddy | `~/.workbuddy/skills/website-style-router/` |
| 其他 | 任何「目录内含 `SKILL.md`」约定都可直接用 |

### 1.2 首次运行：先探环境

**第一次用之前，务必跑一次环境探测。** 它会告诉你本机**能提取什么、不能提取什么**——这直接决定后面哪些源材料要回退给用户。

```bash
python scripts/check_env.py
```

真实输出示例（这台机器）：

```
-- Python 包 -------------------------------------------------------
[MISS] pypdf          未安装          PDF 文本与图片提取
[MISS] pillow         未安装          图片真实编码格式校验与重编码
[----] python-docx    未安装           .docx 文本与内嵌图片提取
[----] openpyxl       未安装          .xlsx / .csv 读取
[----] python-pptx    未安装          .pptx 文本与图片提取

-- 外部命令 --------------------------------------------------------
[OK  ] ffmpeg      ffmpeg version 8.1.2-full_build
[OK  ] node        v22.22.2
[----] tesseract   未找到
[----] whisper     未找到
[----] soffice     未找到
[----] pandoc      未找到

-- 结论 ------------------------------------------------------------
x 必需包缺失：pypdf, pillow
  安装： pip install pypdf pillow
i 按需包未装（遇到对应源格式再装即可）：python-docx, openpyxl, python-pptx
v 可用能力：PDF / 图片 / 文本 / Markdown / 视频抽帧
```

**怎么读这份输出**：

- `[MISS]` = **必需包**，缺了核心功能不可用。**先装它**：`pip install pypdf pillow`
- `[----]` = **按需包**，遇到对应格式再装。不做 docx/xlsx/pptx 就不必装。
- 最后的「必须向用户明说的限制」最重要——比如本机**无 OCR**，那么扫描件就必须请用户提供文字，**不许假装能识别**。这是铁律 17。

### 1.3 依赖分层（记住这张表，能省很多事）

| 类别 | 内容 | 什么时候需要 |
|---|---|---|
| **必需** | `pypdf`、`Pillow` | 只要处理 PDF / 图片就需要 |
| **按需** | `python-docx`、`openpyxl`、`python-pptx` | 遇到 .docx / .xlsx / .pptx 才装 |
| **零依赖** | `emit_tokens.py`、`audit_tokens.py`、`ledger.py`、`validate_skill.py`、`pick_stack.py` | **随时可跑**，不需要装任何东西 |
| **外部命令** | `node`/`npm`（Node 栈）、`ffmpeg`（视频抽帧）、`tesseract`（OCR）、`whisper`（ASR） | 按需 |
| **可选工具** | `uipro`、`npx typeui.sh`、`hue` | 都不是前置条件 |

> **设计要点**：所有**判据类脚本都是零依赖**。这是有意的——判据随时能跑，才不会因为「懒得装环境」而跳过。

---

## §2 一次完整流程走查

用一个真实用例走一遍：**楼下修鞋摊，大爷修鞋四十年，不会电脑，想让人知道还开着、修什么、多少钱。**


### 阶段 -1 · 源材料与交付形态（门 G-1）

**做什么**：先判断用户给的是什么。

这个用例给的是「一段话」，所以走纯文字路径，没有素材要提取。但如果给的是 PDF / 图片 / 视频，就必须：

```bash
python scripts/extract_source.py <输入> <输出目录>
python scripts/verify_assets.py <输出目录>/manifest.json <输出目录>/assets
```

**产出**：`source-map.md`（四段：源 / 内容映射 / 未采用 / 提取告警）

**出口检查**：`verify_assets.py` 三零成立（缺失 0 / 未用 0 / 格式 0）、体积 <15MB、每条告警都记了处置。

**为什么这道门在最前面**：用户给的往往不是文案，而是 PDF / 图库 / 一个 URL。**先把源变成可溯源的结构化数据，否则后面每条结论都是猜的**（铁律 1）。

### 阶段 0 · 意图追问（门 G0）

**做什么**：读 [`intake.md`](intake.md) 的 B0–B11 十二支决策树，**一次一问、每问都给推荐答案**。

这个用例会问到：

- B1 交付形态 → `standalone`（独立站，没有已有主站）
- B2 语言 → 中文单语
- B4 中轴 → 推荐 `left-rail`（信息型）
- B5 区块与尺寸 → 要有「还开着吗 / 修什么 / 多少钱」三块

**出口检查**：C 类问题（必须问的）全部有答案。

**决策权怎么分**（[`decide.md`](decide.md)）：判据是「**错了的返工成本 × 我有没有可靠依据**」。

- 大爷不会电脑 → **C 类，必须问**（这直接决定技术栈）
- 中轴选哪个 → **B 类，给推荐答案让他确认**
- 具体字体 → **A 类，自主决定**

### 阶段 1 · 约束筛选（门 G1）

**做什么**：逐条判定，输出**排除清单**。注意——**不是选，是砍**。

这个用例的排除链：

| 约束 | 排除掉 |
|---|---|
| 维护者非技术 | 一切 Node 栈（astro / next / nuxt / eleventy / vite / hugo） |
| 单页、无交互 | 需要路由或多页模板的栈 |
| 无专业摄影 | 依赖大图的锚点（`editorial-print` × 低质图 = 必崩） |
| 数据极简 | CMS / API 方案 |

**出口检查**：排除项 ≥3 条，且**每条写明被谁排除**（IA / 布局 / 风格三列）。

### 阶段 1.5 · 技术栈选型（门 G1.5）

**做什么**：收集 D1–D8 八个判定项，跑确定性推荐器。

```bash
python scripts/pick_stack.py \
  --pages single --interaction none --maintainer nontech --data inline \
  --host standalone --i18n none --render static --budget lean
```

真实输出：

```
输入判定（D1–D8）
  D1 页面规模 single ｜ D2 交互 none ｜ D3 维护者 nontech
  D4 数据源 inline ｜ D5 形态 standalone ｜ D6 多语言 none
  D7 渲染 static ｜ D8 性能预算 lean

候选排序
  1. plain-html    纯静态 HTML + CSS     得分 10
     目录形状：index.html + style.css + app.js（可选）
       +3 单页，无需路由
       +2 交互轻，原生 JS 够用
       +2 非技术维护者，零构建
       +1 数据简单，运行期读取即可
       +2 首屏预算紧，无运行时

被排除
  × astro         maintainer=nontech：维护者不能碰命令行 / Node 构建链
  × eleventy      maintainer=nontech：维护者不能碰命令行 / Node 构建链
  × next          maintainer=nontech：维护者不能碰命令行 / Node 构建链
  × nuxt          maintainer=nontech：维护者不能碰命令行 / Node 构建链
  × hugo          maintainer=nontech：维护者不能碰命令行 / Node 构建链
  × vite-vanilla  maintainer=nontech：维护者不能碰命令行 / Node 构建链

结论
  选定 `plain-html`。依据：单页，无需路由；交互轻，原生 JS 够用；
  非技术维护者，零构建；数据简单，运行期读取即可；首屏预算紧，无运行时。
```

**产出**：`tech-stack.md`，含 D1–D8 判定 + 选定栈 + **被排除项（写明被哪条判据排除）** + 落地约束 + **3 条可观测证伪条件**。

**对照**：同样跑一遍「基金会年报」（多页 + 双语 + CMS + 团队维护），结果是 **`astro` 得分 9**，目录形状变成 `src/pages/ + src/components/ + src/styles/`。

> **这就是 Phase 1.5 的意义**：不同需求得到**不同的产物形状**。以前两者都会生成同一套 Astro 骨架。

### 阶段 1.6 · 批次查重（门 G1.6）

**做什么**：如果这批要交付多个站，开工前先问账本「这个组合用过没有」。

```bash
python scripts/ledger.py --check --dir <工作区> \
  --anchor warm-hospitality --family craft --surface paper --variant a --pair 0 \
  --axis center-axis --layout editorial-hero --font-display Gloock
```

撞车时的真实输出：

```
冲突：
  ✗ 锚点「warm-hospitality」已被「站点 A」使用（1 次）—— 高冲突
  ✗ display 字体「Gloock」已被「站点 A」使用（1 次）—— 高冲突
  △ 布局原型「editorial-hero」已被「站点 A」「站点 B」使用（2 次）—— 中冲突

建议：
  · 锚点改选（同族未用）：craft-artisanal、paper-ink、soft-organic
  · 或跨族换锚点（未用）：agentic-minimal、archival-index、art-deco-glam、…
  · 若必须保留该锚点：换组合 —— surface ∈ {deep, ink, slate, stone, white}，
    variant ∈ {b,c,d}，pair ∈ {1,2,3}
  · display 字体已撞车：把 --pair 换成 1/2/3 取族备用池

结论：不通过 —— 存在高冲突，换掉再开工
```

**注意它不只说「撞了」，还说「换成什么」** —— 这是账本和「人眼觉得像不像」的关键差别。

**出口检查**：无高冲突。锚点与 display 字体必须唯一；底色档 / 中轴在同批次出现 ≤2 次。

### 阶段 1.7 · 页面粒度与页内导航（门 G1.7）

**做什么**：回答两个**结构问题**（不是风格问题）——「这些内容该分成几页」「长页里怎么跳」。

```bash
python scripts/pick_pages.py --entries 17 --depth deep --shareable --indexable \
  --ia portfolio --blocks 6 --host standalone
```

真实输出：

```
页面粒度：master-detail
  理由：
    ✓ 条目数 17 ≥ 4，且深度为 deep
    ✓ 需要单独分享某一条（shareable）
    ✓ 需要被搜索引擎索引单条（indexable）
  被排除：
    · single —— 17 条挤在一页，找不到东西
    · multi-page —— 主题只有一个（作品），不需要按主题分目录
  证伪条件：若详情页里没有任何索引页看不到的信息（只是把卡片放大），
            说明拆页是假拆，应退回 single。

页内导航：none
  理由：
    ✓ 区块数 6，但 master-detail 的详情页各自不长，索引页靠卡片网格即可定位
  被排除：
    · anchor-jump —— 无查阅型区块
    · sticky-toc / section-rail —— 单页区块数未达阈值
  证伪条件：若索引页长到需要滚动超过 3 屏才能看完全部条目，应升为 anchor-jump。
```

**这一阶段最容易犯的错**：

| 错法 | 为什么错 |
|---|---|
| 问用户「你要单页还是多页」 | 用户不知道。要问的是**内容规模**（几条、多深、要不要单独分享），由脚本算 |
| 所有站都拆页 | 3 个区块的咖啡店拆页 = 负优化。`single` 是合法结果 |
| 所有站都加目录 | 短页加目录 = 噪声。`none` 也是合法结果 |
| 拆了页但详情页没新信息 | **假子页**：把索引页内容原样放大，等于没拆。F14 抓不到，靠人眼（见 `design-qa.md` 六条人眼判据） |
| 锚点 id 指向不存在的元素 | F15 会抓断链，但**跳过去落点偏了**（被吸顶栏盖住）只有人眼能发现 |

**出口检查**：`content-profile.md` 里写明「页面粒度 + 页内导航 + 依据 + 被排除 + 证伪条件」，
且 `audit_tokens.py --site <站点目录>` **F 级 0**（F14 查声明与实际页数是否一致，F15 查锚点可达）。

> **`master-detail` / `multi-page` 会把工作量从 L1 推到 L2** —— 因为多页意味着共享布局、
> 路由、数据源单一化。这一步判完，回 `SKILL.md` 更新工作量分级。

### 阶段 2 · 落定 ★（门 G2）

**这是全流程唯一的强制人工确认点。**

落定前必须把**十件事**全部定完：

```
技术栈 · 族 · 锚点 · 布局 · 中轴 · 底色档 · 变体轴 · 字体对 · ≥3 条视觉签名
· 页面粒度 + 页内导航
```

为什么必须一次定完：**这几项返工最贵**。等到写完代码再改中轴或改页数，等于重做整站。

**出口检查**：用户明确点头 + 证伪条件写得出来 + 批次查重已过。

### 阶段 3 · token（门 G3）

**做什么**：跑确定性生成器。

```bash
python scripts/emit_tokens.py --anchor warm-hospitality \
  --surface paper --variant a --pair 0
```

真实输出（节选）：

```css
:root {
  --bg:        #FCF5F0;   /* surface=paper · oklch(0.975 0.016 60) */
  --fg:        #231D18;   /* 对 --bg 对比度 15.5:1 */
  --surface:   "paper";
  --variant:   "a";
  --font-display: "Gloock", "Fraunces", Georgia, serif;
  --font-body:    "Nunito Sans", "Inter", "PingFang SC", sans-serif;
  --fs-base: 18px;   /* 1.333^0 × 18 = 18.0 */
  --radius:    8px;
}
```

**然后**：在骨架上做锚点特化，产出 `design-system/MASTER.md`。

**产出**：`MASTER.md` = token + `--axis` + `--surface` + `--variant` + 字体四件套 + **视觉签名段（≥3 条）** + `never` 清单。

**出口检查**：零形容词、`never` 可检查、字阶 ≤6 级、**`audit_tokens.py` F 级 0**。

### 阶段 4 · 搭站（门 G4）

按 `tech-stack.md` 选定的栈来。这个用例是 `plain-html`：

```
index.html + style.css
```

**注意**：产物形状**必须**反映技术栈。如果这里出现了 `src/pages/index.astro`，说明 Phase 1.5 白做了。

### 阶段 5 · 验收（门 G5）

三处全过：

```bash
python scripts/audit_tokens.py <站点>/design-system/MASTER.md --anchor warm-hospitality
python scripts/audit_tokens.py --site <站点目录>          # 结构：页面粒度 + 页内导航
python scripts/audit_tokens.py --batch <批次目录>
# 再过一遍 checklist.md
```

`--site` 是 v0.9 新增的：它检查**结构**（F14 页面粒度是否与声明一致、F15 锚点是否可达），
与不带参数的**数值**审计互补。**数值全过但只有一个 `index` 首页，仍然不合格。**

### 阶段 6 · 微调回访（门 G6）

**交付时交代三件事**（铁律 21）：

1. 我**自主决定**了什么
2. 哪些是**推断**的（依据是什么）
3. 哪些**还没确定**（`[待定]` / `[待填]` 清单）

**交付后立刻记账**：

```bash
python scripts/ledger.py --commit --dir <工作区> --name repair-shop \
  --anchor <slug> --family <族> --surface <档> --variant a --pair 0 \
  --axis left-rail --layout utility-board --ia conversion \
  --font-display <首族名>
```

> **漏记 `--font-display`，批次报告会判「未记录」不通过。** 没记录 = 这一项没被校验。

---

## §3 命令手册

十个脚本。**带 ★ 的是零依赖，随时可跑。**

### ★ `scripts/pick_stack.py` — 技术栈选型

```bash
python scripts/pick_stack.py --pages single --interaction none \
  --maintainer nontech --data inline --host standalone \
  --i18n none --render static --budget lean [--json]
```

| 参数 | 取值 | 含义 |
|---|---|---|
| `--pages` | `single` / `few` / `many` | 页面规模（D1） |
| `--interaction` | `none` / `light` / `heavy` | 交互强度（D2） |
| `--maintainer` | `nontech` / `tech` / `team` | 维护者技术程度（D3） |
| `--data` | `inline` / `single-json` / `cms` / `api` | 数据源（D4） |
| `--host` | `standalone` / `embedded` / `system-only` | 交付形态（D5） |
| `--host-stack` | 宿主栈名 | 仅 `embedded` 时用（D5 补充） |
| `--i18n` | `none` / `multi` | 多语言（D6） |
| `--render` | `static` / `ssr` | 渲染需求（D7） |
| `--budget` | `lean` / `normal` | 性能预算（D8） |

**输出**：输入判定 + 候选排序（含得分理由）+ 被排除项 + 结论。
**要点**：`embedded` 和 `system-only` 走短路分支——嵌入宿主时技术栈由宿主决定，只做确认。

### ★ `scripts/pick_pages.py` — 页面粒度与页内导航

```bash
python scripts/pick_pages.py --entries 17 --depth deep --shareable --indexable \
  --ia portfolio --blocks 6 --host standalone [--json]
```

| 参数 | 取值 | 含义 |
|---|---|---|
| `--entries` | 整数 | 可列举的条目数（作品数 / 商品数 / 案例数…）。0 表示无可列举条目 |
| `--depth` | `shallow` / `medium` / `deep` | 单条内容的深度（一段话 / 一节 / 一整页） |
| `--shareable` | 开关 | 是否需要**单独分享某一条**（有独立 URL） |
| `--indexable` | 开关 | 是否需要**搜索引擎索引单条** |
| `--themes` | 整数 | 可归纳的主题数（≥2 才可能 `multi-page`） |
| `--maintainer` | `nontech` / `tech` / `team` | 维护者技术程度（`nontech` + 非静态生成 → 否决拆页） |
| `--static-gen` / `--no-static-gen` | 开关 | 是否用静态生成器（一个数据源渲染 N 页） |
| `--ia` | 四个 IA 之一 | 取该 IA 的默认粒度/导航作基线 |
| `--blocks` | 整数 | 单页区块数（判页内导航） |
| `--lookup` | 整数 | **查阅型**区块数（FAQ / 规格表 / 合规）——转化页唯一的导航例外 |
| `--linear` | 开关 | 区块是**说服链**（强顺序） |
| `--screens` | 整数 | 页面高度折合屏数（判 `section-rail`） |
| `--host` | `standalone` / `embedded` / `system-only` | `system-only` 时粒度记 `n-a` |

**输出**：档位 + **逐条理由** + **被排除的档位及原因** + **证伪条件**。

**要点**：

- 阈值全部读 `architectures/pagination.json`，脚本不硬编码 —— 改标准只改那一个 JSON。
- 它**只算档位，不决定形态**。具体做成行内目录还是吸顶条，看 `layouts.md`。
- **`single` 和 `none` 都是合法结论**，不是「没判出来」。内容浅的站可以就是 `single + none`，
  有规格/做法/FAQ 这类查阅型区块的是 `single + anchor-jump`，
  条目需要单独分享的才是 `master-detail + none`。

### ★ `scripts/emit_tokens.py` — token 生成

```bash
python scripts/emit_tokens.py --list                    # 列出 40 个锚点
python scripts/emit_tokens.py --anchor <slug> [选项]     # 生成 token
```

| 参数 | 说明 |
|---|---|
| `--anchor <slug>` | 锚点（必填，除非用 `--list`） |
| `--surface <档>` | 覆盖底色：`white`/`paper`/`tint`/`stone`/`slate`/`ink`/`deep` |
| `--variant <轴>` | `a` 原值 / `b` 收紧 / `c` 放松 / `d` 张扬 |
| `--pair <0-3>` | `0` 锚点主选，`1–3` 取族备用池 |
| `--lang zh\|en` | 正文字体栈倾向 |
| `--css-only` | 只打印 CSS，不带说明头（**写进文件时用这个**） |
| `--out <目录>` | 写 `<anchor>.tokens.md` |

**要点**：这是**确定性**的——同样的参数永远出同样的结果。**不要手编 token**（铁律 22）。

### ★ `scripts/audit_tokens.py` — 产出审计

```bash
python scripts/audit_tokens.py <MASTER.md 或 tokens.css>
python scripts/audit_tokens.py <MASTER.md> --anchor <slug>   # 加签一致性校验
python scripts/audit_tokens.py --site <站点目录>              # 结构：页面粒度 + 页内导航
python scripts/audit_tokens.py --batch <批次目录>             # 跨站差异度
python scripts/audit_tokens.py <file> --json
```

**退出码非 0 = 有 F 级未过 = 没做完。**

F 级失败长这样（真实输出）：

```
audit_tokens — tokens.css
====================================================================
  ✗ [F2] `--fg`（正文主色）对 `--bg` 仅 4.48:1，低于 7.0:1
        → 调亮/调暗该色，或让 emit_tokens.py 按 solve_contrast 重新求解
  ✗ [F3] 正文基准 12px 偏小
        → 中文正文 ≥ 15px，西文 ≥ 14px
  ✗ [F6] 标题与正文同用 `Inter`（= 没做搭配）
        → 同一字体当标题与正文是 AI 均值味的来源；见 fonts.json 的 R2

F 3 / I 2 / S 8  →  FAIL（判据见 design-qa.md）
```

**注意**：对 `.css` 文件跑时，F10（视觉签名）会**自动降级为提示**——因为视觉签名段属于 `MASTER.md`，不在 CSS 里。要对 `MASTER.md` 跑才能校验签名。

**`--site` 模式**（v0.9 新增，查**结构**而非数值）：

```
audit_tokens --site  ·  my-site
====================================================================
  ✓ [F14] 页面粒度声明 `master-detail`，实际 18 个页面文件（1 索引 + 17 详情）
  ✓ [F15] 页内导航声明 `none`，无锚点要求
F 0 / I 0 / S 2  →  PASS
```

失败长这样：

```
  ✗ [F14] content-profile.md 未声明页面粒度
        → 补一行「页面粒度：single|master-detail|multi-page|n-a」（见 architectures/granularity.md §4）
  ✗ [F14] 声明 `master-detail`，但只找到 1 个页面文件
        → 主从结构必须有索引页 + 至少一个详情页（如 src/pages/[slug].astro）
  ✗ [F15] 声明 `anchor-jump`，但页内锚点一个都不可达
        → 目录里的 href="#x" 必须有对应的 id="x"；F15 会逐个验证
  ✗ [F15] 页面声明 `none`，但有 5 个区块
        → 5 个区块以上不给导航等于「一翻到底」；升为 anchor-jump 或说明为何不需要
```

**F14 的核心逻辑**：读 `content-profile.md` 里的粒度声明 → 数实际页面文件 →
`single` 必须恰好 1 页、`master-detail` ≥2、`multi-page` ≥3、`n-a` = 0。
**声明缺失直接失败**（不许「没说」）。

**F16–F20：交付完整性判据**（v0.9.1 新增，`--site` 同样启用）

这五条把「一直写在铁律里、却始终没有机器判据」的要求补上了：

| 编号 | 查什么 | 对应铁律 |
|---|---|---|
| **F16** | 字段渲染完整性：`src/data/*.json` 的数组字段若被代码只取 `[0]`，须另有 `.map()` / `.flatMap()` 渲染其余项 | 19 |
| **F17** | 内容可溯源：`source-map.md` 表格行 ≥50% 带溯源标记（`p12 · "原句"` / URL）。**文件缺失只报 I 级** | 18 |
| **F18** | 一份真源：`MASTER.md` 与 `src/styles/tokens.css` 共有 token 值一致 | 26 |
| **F19** | 嵌入服从宿主：声明 `embedded` 须有 `HOST.md`，且共有 token 与宿主一致 | 14 |
| **F20** | 产物形状反映技术栈：选了 `plain-html` 就不能出现 `astro.config.*` / `src/pages/` | 29 |

**F16 有一条必须知道的实现细节**：它**只认 `.map()` / `.flatMap()`，不认 `forEach`**。

原因是真实踩出来的——最初 `forEach` 也算「渲染过」，结果负向用例一条都没抓到，
因为示例的灯箱脚本里本来就有 `images.forEach(...)`：它只是注册灯箱数据、绑事件，
**页面上一个元素都不会多**，于是「脚本遍历过」掩盖了「模板只渲染第一张图」。

> **这条的通用教训**：判据写松了等于没写，而且**在测试里表现为「全部通过」**，和好判据一模一样。

### ★ `scripts/ledger.py` — 批次账本

```bash
python scripts/ledger.py --check  --dir <工作区> [指纹参数]   # 开工前查重
python scripts/ledger.py --commit --dir <工作区> --name <站名> [指纹参数]  # 交付后记账
python scripts/ledger.py --report --dir <工作区>              # 批次报告
```

指纹参数：`--anchor` `--family` `--surface` `--variant` `--pair` `--axis` `--layout` `--ia` `--font-display`

**退出码**：`0` 通过 / `1` 有冲突或不达标 / `2` 用法错误。

**账本落在 `<工作区>/.style-ledger.json`，不进 skill 仓库** —— 它是项目侧状态，跟着具体一批站走。**换一批站就换一个工作区。**

冲突阈值（`UNIQUE_AT`）：

| 字段 | 出现几次算冲突 |
|---|---|
| 锚点 / display 字体 | **1**（必须唯一） |
| 底色档 / 中轴 / 族 / 布局 / IA | **2**（允许一对） |

报告阈值：锚点唯一率 ≥80%、display 唯一率 100%、底色 ≥3 种、
**中轴 ≥2 种 且 单档占比 ≤60%**（v0.9.1 修正，见下）、族比值 ≥60%。

> **为什么中轴从「≥3 种」改成「≥2 种 + 单档 ≤60%」**：中轴总共就 3 档，
> 要求「3 种全出现」等于要求覆盖率 100% —— 那是**配额**不是多样性，
> 会强制每个批次都含一个 `split` 站。改后仍然抓得住「5 站全 left-rail」这种真塌缩。
> **同一个数字「3」在档数不同的维度上含义完全相反**，定阈值时要按档数归一化。

### `scripts/extract_source.py` — 统一提取

```bash
python scripts/extract_source.py <输入路径> <输出目录>
```

输入可以是文件或目录。**所有类型共用同一套产出结构**：

```
<out_dir>/text.md         所有文本，按来源分节（便于溯源）
<out_dir>/assets/         图片 / 视频关键帧 / PPT 内嵌图
<out_dir>/manifest.json   {source, type, units, assets[], warnings[]}
<out_dir>/_WARNINGS.txt   需人工介入的事项（有才生成）
```

**不支持**：`.doc` / `.ppt` / `.wps` 等旧二进制格式（本机无 LibreOffice）→ 会给出明确降级指引。
**依赖**：`pip install pypdf pillow python-docx openpyxl python-pptx`；ffmpeg 需在 PATH。

### `scripts/verify_assets.py` — 素材校验

```bash
python scripts/verify_assets.py <manifest.json> <assets 目录>
```

**三件事**：双向比对（缺失 0 / 未用 0）+ **真实编码格式校验** + 体积。

> **为什么必须有它**：扩展名可能与真实编码不符。真实踩过的坑——JP2 伪装成 `.png`，Chrome 静默渲染成空框。**「引用对了 + 状态码 200」不能证明图片能显示**（铁律 16）。必须用 PIL 读真实 `format`。

### `scripts/extract_pdf_assets.py` — PDF 专用提取

只在需要 **page 级绑定/去重**时用（比如作品集 PDF，要建立「第 12 页 → 哪张图 → 哪段文字」的映射）。

### ★ `scripts/validate_skill.py` — 仓库自检

```bash
python scripts/validate_skill.py            # 默认校验脚本上一级目录
python scripts/validate_skill.py <skill_dir>
python scripts/validate_skill.py --json
```

**改了 skill 自身的任何文件，都要跑这个，要求 `ERROR 0`。**

输出格式：

```
  i frontmatter 顶层键: name, description, license, compatibility, metadata
  i SKILL.md 行数: 290
  i 字体搭配覆盖 40 个锚点，display 字体全库唯一
  i 底色维度覆盖 40 个锚点，7 档 surface 在用
  i 尺度变体轴 4 条：a / b / c / d
  i 族备用池 11 族 / 33 对，display 全库唯一
  i H1 IA 文档与 pagination.json 的默认值一致
--------------------------------------------------------------------
ERROR 0  WARN 0
RESULT: PASS
```

`i` = 信息，`?` = 警告（不影响退出码），`x` = 错误（退出码 1）。

**H 段是 v0.9 新增的仓库层判据**（管 skill 自己，与产出层的 F 段不同）：

| 编号 | 查什么 | 抓什么问题 |
|---|---|---|
| **H1** | 四个 IA 文档写的「默认粒度 / 默认页内导航」与 `pagination.json` 的 `iaDefaults` 一致；注册表含 `falsify` 段 | **文档漂移** —— 改了注册表忘了改文档，或反之。这类漂移单看任何一个文件都自洽，只有交叉比对才暴露 |
| **H3** | 每档 `axis` 须 ≥3 个锚点、跨 ≥2 个布局原型、跨 ≥3 个族 | **维度没正交** —— 某档中轴 100% 绑定单一布局时，选中轴就等于选布局，布局与族的自由度被一起锁死 |

### 通用铁则：改完必跑

| 你改了什么 | 必须跑 |
|---|---|
| skill 里的任何文件 | `python scripts/validate_skill.py` → `ERROR 0` |

---

### ① 换一个字体 / 加一对备用搭配

**改哪里**：`styles/fonts.json`

**场景 A：改某个锚点的字体**

找到该锚点，改 `display` / `body`：

```json
"warm-hospitality": {
  "display": "\"Gloock\", \"Fraunces\", Georgia, serif",
  "body": "\"Nunito Sans\", \"Inter\", \"PingFang SC\", sans-serif",
  "mono": "roboto",
  "cjk": "zh-serif",
  "loading": "self",
  "note": "Gloock 的暖调高对比衬线像手写招牌；正文用 Nunito Sans 的圆端，配『来坐坐』的调性。"
}
```

**场景 B：给某个族的备用池加一对**

找到 `_familyPools.<族>`，追加一条：

```json
{
  "tag": "质朴厚实",
  "display": "\"Vollkorn\", Georgia, serif",
  "body": "\"Karla\", \"Helvetica Neue\", Arial, sans-serif",
  "mono": "plex",
  "cjk": "zh-kai",
  "note": "Vollkorn 的厚实衬线像手工印刷，Karla 的怪诞骨架带手作的不规则感。"
}
```

**验证**：

```bash
python scripts/validate_skill.py
# 期望看到：i 字体搭配覆盖 40 个锚点，display 字体全库唯一
#           i 族备用池 11 族 / 33 对，display 全库唯一
python scripts/emit_tokens.py --anchor warm-hospitality --pair 1   # 看第 1 对备用字体
```

**必须遵守的 6 条硬规则**（`fonts.json` 的 `_rules`，会被自动校验）：

| 规则 | 内容 |
|---|---|
| R1 具名 | `--font-display` 首族**不得**是 `system-ui` / `-apple-system` / `sans-serif` / `serif` / `monospace`。通用栈只能出现在回退位置 |
| R2 分离 | display 首族 ≠ body 首族。同字体当标题与正文 = 没做搭配 |
| R3 全库唯一 | 40 个锚点的 display **全库不重复** |
| R4 中文回退显式 | 必须声明 CJK 回退栈，且不让中文字体渲染西文 |
| R5 字重克制 | 每套搭配实际使用字重 ≤2 |
| R6 可获取 | 只用开源/免费可商用字体（Google Fonts / Fontshare / 官方开源发布） |

**报错怎么办**：

- `display 字体重复（违反 R3 全库唯一）` → 你选的字体已被别的锚点用了，换一个，或改那个锚点。
- `display 首族是通用关键字(Inter)` → 首族必须具名。`Inter` 只能放回退位。
- `display 与 body 同族（未做搭配）` → 换掉其中一个。

---

### ② 调一个锚点的手感

**改哪里**：`styles/signatures.json` 的 `anchors.<slug>`

```json
"warm-hospitality": {
  "r": 1.333,      // 字阶公比 —— 决定气质
  "base": 18,      // 正文基准字号 px
  "lh": 1.8,       // 正文行高倍数
  "wrap": 1080,    // 主容器宽 px
  "ch": 58,        // 正文行长（字符数）
  "unit": 8,       // 间距基数 px
  "trk": -0.01,    // 标题字距 em
  "hue": 25,       // 色相（OKLCH）
  "chr": 2,        // 彩度档 0–3
  "warm": 1.0,     // 色温 -1 冷 … 1 暖
  "rad": 8,        // 圆角 px
  "theme": "light",
  "mot": "soft",   // 动效倾向
  "wts": "400,600",// 使用的字重
  "disp": "mix",   // 标题字体倾向
  "surface": "paper"  // 底色档
}
```

**`r` 是最有杠杆的一个数**（[`typography.md`](typography.md) §1 有族带）：

| 族 | 公比带 | 气质 |
|---|---|---|
| `grid` · `institutional` · `techno` | **1.167 – 1.25** | 平、稳、像表单 |
| `editorial` · `craft` · `industrial` · `commerce` · `nostalgic` | **1.25 – 1.333** | 正常书刊感 |
| `contemplative` · `vernacular` | **1.333 – 1.5** | 疏、慢、有呼吸 |

**带外即失真**：`r < 1.15` 层级塌陷（用户分不出标题和正文）；`r > 1.7` 正文小字会碎（<12px 中文不可读）。

**验证**：

```bash
python scripts/emit_tokens.py --anchor warm-hospitality --css-only | head -40
python scripts/validate_skill.py     # F5 会查字段合法性（枚举/量纲/区间）
```

**报错怎么办**：

- `签名字段非法` → 看 `_legend`（`signatures.json` 顶部）确认该字段的合法区间。
- 改完发现 `audit_tokens.py` 的 F5 报「正文基准 ≠ 签名」→ 说明你的产出与签名不一致。要么改产出，要么改签名，**不能两边各说各话**。

---

### ③ 加一档底色

**改哪里**：`styles/signatures.json` 的 `_surfacePresets`

```json
"_surfacePresets": {
  "white":  { "L": 1.000, "C": 0.000, "polarity": "light", "note": "纯白。最中性，也最容易撞……" },
  "paper":  { "L": 0.975, "C": 0.010, "polarity": "light", "note": "…" },
  "tint":   { "L": 0.945, "C": 0.026, "polarity": "light", "note": "…" },
  "stone":  { "L": 0.900, "C": 0.014, "polarity": "light", "note": "…" },
  "slate":  { "L": 0.820, "C": 0.018, "polarity": "light", "note": "…" },
  "ink":    { "L": 0.170, "C": 0.012, "polarity": "dark",  "note": "…" },
  "deep":   { "L": 0.115, "C": 0.018, "polarity": "dark",  "note": "…" }
}
```

**字段含义**：

- `L` = OKLCH 明度，**必须落在 [0.0, 1.0]**
- `C` = OKLCH 彩度，**必须落在 [0.0, 0.2]**
- `polarity` = `light` 或 `dark`，**决定前景色和 accent 的求解方向**

**验证**：

```bash
# 七档底色的实际产出
for s in white paper tint stone slate ink deep; do
  echo -n "$s  "
  python scripts/emit_tokens.py --anchor warm-hospitality --surface $s --css-only | grep -E '^\s*--bg:'
done
python scripts/validate_skill.py     # F10 查预设合法性与锚点覆盖
```

**报错怎么办**：

- `_surfacePresets 字段非法: xxx(L=1.8)` → 明度越界，改回 [0,1]。
- `锚点引用了不存在的 surface 档` → 某个锚点的 `surface` 写了个不存在的档名（拼写错误）。
- `40 个锚点只用了 2 档 surface —— 底色空间未被利用` → 至少让锚点分布在 ≥3 档上。

**加完新档别忘了**：给至少几个锚点分配这个新档，否则它会「存在但没人用」，F10 的覆盖率检查虽然过，但实际没起作用。

---

### ④ 加一条尺度变体轴

**改哪里**：`styles/signatures.json` 的 `_variantAxes`

```json
"_variantAxes": {
  "a": { "label": "原值", "dr": 0.0,   "dbase": 0,  "dunit": 1.0, "drad": 0,  "mot": null },
  "b": { "label": "收紧", "dr": -0.06, "dbase": -1, "dunit": 0.5, "drad": -2, "mot": "snap" },
  "c": { "label": "放松", "dr": 0.05,  "dbase": 1,  "dunit": 1.5, "drad": 3,  "mot": "soft" },
  "d": { "label": "张扬", "dr": 0.12,  "dbase": 2,  "dunit": 2.0, "drad": 8,  "mot": "drift" }
}
```

**安全边界**（`validate_skill.py` 的 F11 会查）：

| 字段 | 含义 | 安全范围 |
|---|---|---|
| `dr` | 字阶公比偏移 | 绝对 ≤ **0.25** |
| `dbase` | 基准字号偏移（px） | 绝对 ≤ **3** |
| `dunit` | 间距单位倍数 | **[0.3, 3.0]** |
| `drad` | 圆角偏移（px） | 绝对 ≤ **12** |
| `mot` | 动效倾向 | `snap` / `soft` / `drift` / `null` |

**验证**：

```bash
python scripts/emit_tokens.py --anchor warm-hospitality --variant d --css-only | grep -E 'font-size|--space-1'
python scripts/validate_skill.py    # F11 查轴数与偏移范围
```

**报错怎么办**：

- `_variantAxes 只有 1 条` → 至少要 2 条（含原值）。
- `偏移量超出安全范围: d(dr=0.9)` → 改回 ±0.25 内。**偏移太大产出的字阶会畸形**，这是 clamp 存在的原因。

---

### ⑤ 加一个新锚点 ★最需要小心的一步

**一个锚点不是「一个地方加一行」，而是三份数据必须同时存在。**

| 文件 | 加什么 |
|---|---|
| `styles/index.json` | 锚点元数据（属于哪个族、绑哪个 layout/axis、图文策略、when/never） |
| `styles/signatures.json` | 它的 15 个数值参数 + `surface` |
| `styles/fonts.json` | 它的字体对（**display 必须全库唯一**） |

**为什么必须三处一致**：`index.json` 说它属于哪个族，`signatures.json` 说它的数值，`fonts.json` 说它用哪对字体。**漏任何一处，`emit_tokens.py` 都会缺一半输入。**

**`index.json` 的锚点形状**：

```json
{
  "slug": "my-new-anchor",
  "name": "中文名",
  "family": "craft",
  "typeui": "cafe",
  "oneLiner": "一句话描述这个风格的调性。",
  "layout": "editorial-hero",
  "axis": "center-axis",
  "imagePolicy": "required",
  "iconPolicy": "decorative",
  "density": "airy",
  "when": ["什么情况下该选它", "第二条", "第三条"],
  "never": ["什么情况下绝不能用它"]
}
```

**验证**：

```bash
python scripts/validate_skill.py
# 期望：ERROR 0
# F3 查「签名覆盖 index.json 的全部锚点，不多不少」
# F8 查「fonts.json 覆盖全部锚点」
# E1 查 layout/family/axis 是否落在定义域内
python scripts/emit_tokens.py --list | grep my-new-anchor
python scripts/emit_tokens.py --anchor my-new-anchor
```

**报错怎么办**：

- `F3 签名覆盖不上：多/少 xxx` → `index.json` 和 `signatures.json` 的锚点集合不一致。
- `F8 fonts.json 缺 N 个锚点的字体搭配` → `fonts.json` 漏了。
- `E1 锚点的 layout 不在定义域内` → `layout` 必须是 [`layouts.md`](layouts.md) 定义的 5 个之一；`family` 必须是 11 族之一；`axis` 必须是 3 档之一。
- `F8 display 字体重复` → 新锚点的 display 撞了，换一个。

> **顺序建议**：先在 `index.json` 加元数据 → 在 `signatures.json` 加参数（可先抄同族锚点再改）→ 在 `fonts.json` 加字体。每加一处跑一次 `validate_skill.py`，报错信息会直接告诉你还缺什么。

---

### ⑥ 加一个技术栈

**改两个地方**：

1. [`techstack.md`](techstack.md) 的候选表 —— 加一行说明与适用条件
2. `scripts/pick_stack.py` 的候选定义 —— 加评分规则与排除规则

**验证**：

```bash
python scripts/pick_stack.py --pages few --interaction light --maintainer tech \
  --data single-json --host standalone --i18n none --render static --budget normal
python scripts/validate_skill.py    # F9 查 techstack.md 与 pick_stack.py 都存在
```

**别忘了**：新栈要同步更新 `SKILL.md` 的 frontmatter `description`（关键词列表）和 `compatibility`（环境要求，比如新栈需要什么运行时）。

---

### ⑦ 加一条判据 ★必须配负向测试

**这一步有硬性要求：加了判据，必须同时加一条负向测试。** 否则你只是又造了一个「可能永远返回 PASS 的判据」。

**改哪里**：

| 判据类型 | 加到哪 |
|---|---|
| **数值判据**（检查产出的 token） | `scripts/audit_tokens.py` |
| **结构判据**（检查产出的页面结构） | `scripts/audit_tokens.py` 的 `--site` 模式（v0.9 起） |
| **仓库判据**（检查 skill 自己） | `scripts/validate_skill.py` |

**同时必须更新**：

- [`design-qa.md`](design-qa.md) —— 数值判据的说明与修法
- [`checklist.md`](checklist.md) —— 如果它属于交付前必过项

---

### ⑧ 加一个内容维度（页面粒度 / 页内导航就是这么加的）★

**这是 v0.9 加页面粒度时走的路，照抄即可。** 适用场景：你想让 skill 对某类**内容事实**
自动做出判断（而不是写一段散文让 agent 即兴发挥）。

**为什么内容维度必须这么加**：散文式必填一定会退化成「永远用默认值」——
`layouts.md` 的「视觉签名必填」就是活例子（写了必填、没有判据、5/5 缺失）。
内容维度尤其危险，因为「不拆页」看起来永远是对的。

**四步，一层都不能少**：

| 步 | 改哪里 | 做什么 |
|---|---|---|
| **1 数据** | 新建 `architectures/<维度>.json` | 档位定义 + 规则 + 否决条件 + **全部阈值**。这是唯一真源，脚本不许硬编码 |
| **2 散文** | 新建 `architectures/<维度>.md` | 判断框架（给人读）：决策树、判据表、各档产物形状、反模式、证伪条件、声明格式 |
| **3 计算** | 新建 `scripts/pick_pages.py` 这类脚本 | 读注册表 → 输出**档位 + 逐条理由 + 被排除档位 + 证伪条件** |
| **4 判据** | `audit_tokens.py` 的 `--site` + `validate_skill.py` | 校验「声明 = 实际」，并配负向测试 |

**第 4 步的三个必查项**：

```python
# a) 产出层：声明缺失必须失败（不许「没说」）
# b) 产出层：声明档位与实际数量必须一致（single=1 / master-detail≥2 / multi-page≥3）
# c) 仓库层：文档里写的默认值必须与注册表一致（否则改一边忘一边 → 文档漂移）
```

**编号提醒**：`audit_tokens.py` 与 `validate_skill.py` **各自维护独立 F 编号**。
加产出层判据时先看两个脚本各自用到哪，**新号一律往后排**（页面粒度用 F14/F15 就是因为
`validate_skill.py` 已经占了 F12/F13）。仓库层判据用 H 段。

**别忘了**：
- `SKILL.md` 加对应**铁律**与**阶段门**（页面粒度加了铁律 33/34 与 G1.7）；
- `checklist.md` 加交付前必过项；
- 如果判断结果会改变工作量，同步**工作量分级**（`master-detail` 会把 L1 推到 L2）；
- 四个 IA 文档各补「默认值」段 —— 否则 H1 会报「文档缺默认粒度声明」。

---

## §5 排错手册

### 5.1 `validate_skill.py` 常见报错

| 报错 | 含义 | 修法 |
|---|---|---|
| `[C1]` SKILL.md 链接目标不存在 | `SKILL.md` 里有个相对链接指向不存在的文件 | 建那个文件，或改链接 |
| `[C2]` 引用了不存在的文件 | 文档里反引号引用的文件名不存在 | 改成真实文件名，或加进 `ARTIFACTS` 白名单（如果是产出物） |
| `[C3]` 孤儿文件（没有任何文档提到它） | 仓库里有个运行时文件没人引用 | 在某个 `.md` 里提到它 |
| `[D2]` 一次性脚本不应入库 | 下划线开头的临时脚本 | 改名或删除 |
| `[E1] 锚点的 layout 不在定义域内` | `index.json` 里的 layout 拼错或不存在 | 用 [`layouts.md`](layouts.md) 的 5 个原型名 |
| `[F3] 签名覆盖不上` | `index.json` 与 `signatures.json` 锚点集合不一致 | 补齐缺的那个 |
| `[F5] 签名字段非法` | 某锚点参数越界 | 查 `_legend` 的合法区间 |
| `[F8] display 字体重复` | 违反 R3 全库唯一 | 换字体 |
| `[F10] 锚点引用了不存在的 surface 档` | 底色档名拼错 | 用 `_surfacePresets` 里的 7 个键 |
| `[F11] 偏移量超出安全范围` | 变体轴偏移太大 | 收敛到安全区间 |
| `[F12] 族备用池不足 3 对` | 某族备用字体不够 | 补到 ≥3 对 |
| `[F13] 缺 scripts/ledger.py` | 反同质化工具被删了 | 恢复 |

### 5.2 `audit_tokens.py` 常见报错

| 报错 | 含义 | 修法 |
|---|---|---|
| `[F0] 没有解析到任何 CSS 自定义属性` | 喂错文件了 | 确认是 `MASTER.md` 的 token 段或 `tokens.css` |
| `[F1] 缺 --axis` | 中轴未定 | 取值 `left-rail` / `center-axis` / `split` |
| `[F2] --fg 对 --bg 仅 4.48:1，低于 7.0:1` | 对比度不足 | 调明度，或用 `emit_tokens.py` 的 `solve_contrast` 重解 |
| `[F3] 字阶不是等比：偏离的相邻比值 …` | 手挑字号了 | 用模块化字阶重算 |
| `[F3] 正文基准 12px 偏小` | 中文 <15px / 西文 <14px | 调大 `base` |
| `[F4] 间距未全部落在 8px 栅格上` | 混入栅格外数值 | 全部改成 `unit` 的整数倍 |
| `[F5] 正文基准 18px ≠ 签名 17px` | 产出与签名不一致 | 改产出或改签名，**不能两边各说各话** |
| `[F6] 标题与正文同用 Inter` | 没做字体搭配 | 从 `fonts.json` 取搭配 |
| `[F10] MASTER.md 缺「视觉签名」段` | 视觉签名没写 | 见 [`layouts.md`](layouts.md) 的签名菜单，选 ≥3 条写进 `MASTER.md` |
| `[F11] 底色值唯一率 2/7` | 一批站底色撞了 | 换 `--surface` |

`--site` 模式的报错（v0.9）：

| 报错 | 含义 | 修法 |
|---|---|---|
| `[F14] content-profile.md 未声明页面粒度` | 没写声明段 | 补「页面粒度：single\|master-detail\|multi-page\|n-a」+ 依据 + 被排除 + 证伪条件 |
| `[F14] 声明 single 却有 2 个页面文件` | 声明与实际不符 | 要么合并页面，要么把声明改成 `master-detail` |
| `[F14] 声明 master-detail 却只有 1 个页面` | 详情页没做 | 加 `src/pages/[slug].astro` 这类模板（`getStaticPaths` 一模板出 N 页） |
| `[F15] 声明 anchor-jump 但锚点一个都不可达` | 目录的 `href="#x"` 没有对应 `id="x"` | 给目标区块补 `id` |
| `[F15] 页面声明 none 但有 5 个区块` | 长页不给导航 | 升为 `anchor-jump`，或说明为什么不需要 |
| `[F15] 锚点断链：#x 指向不存在的 id` | 改了区块名没改目录 | 同步改，或用 `pick_pages.py` 重新核一遍 |

`--site` 下的交付完整性判据（v0.9.1）：

| 报错 | 含义 | 修法 |
|---|---|---|
| `[F16] 字段 xxx 只渲染了第 1 项` | 数据里有数组，模板只取 `[0]` | 用 `.map()` / `.flatMap()` 渲染其余项。**`forEach` 不算** —— 它只做副作用 |
| `[F17] 溯源覆盖率 20%（阈值 ≥50%）` | 溯源表有，但大部分行没有出处 | 给每行补 `p12 · "原句"` 或 `<url> #selector`；指不回去的内容删掉 |
| `[F18] MASTER.md 的 --accent 与 tokens.css 不一致` | 两份真源漂移（铁律 26） | 以 `tokens.css` 为准回写 `MASTER.md`，或反之——**但不能两边各说各话** |
| `[F19] 声明 embedded 但缺 HOST.md` | 嵌宿主却没交对齐文档 | 补 `HOST.md`，写明宿主令牌来源路径 |
| `[F20] 选定 plain-html 却出现 src/pages/` | 产物形状与技术栈不符 | 要么换回单文件 `index.html`，要么承认栈选错了、重跑 Phase 1.5 |

### 5.3 命令行坑（真实踩过的）

| 现象 | 原因 | 修法 |
|---|---|---|
| `--font-display -apple-system` 报 `unrecognized arguments` | argparse 把 `-apple-system` 当成选项了 | 写成 `--font-display=-apple-system`（用等号） |
| 路径跑到 `E:\e\Code\...` | Git Bash 的 MSYS 路径转换 | 用 Windows 风格路径 `"E:/Code/..."` |
| 账本落到了奇怪的地方 | `--dir` 没给，默认 `.` | 显式传 `--dir <工作区>` |
| `emit_tokens.py` 输出带了说明头，写进 CSS 报错 | 没加 `--css-only` | 加 `--css-only` |
| `--site` 报「找不到页面文件」但目录里明明有 | 页面文件不在 `src/pages/` 下，或扩展名不在白名单（`.astro/.html/.md/.jsx/.tsx/.vue/.svelte`） | 确认站点用的是框架默认的页面目录 |
| `npm run build` 报 `SAFE_DELETE_BULK_CONFIRM_REQUIRED` | 环境有批量删除保护，vite 清依赖缓存触发 | `rm -rf node_modules/.vite` 后再 build |

### 5.4 「看着没问题但实际错了」的几类

这类最难查，因为**所有门禁都是绿的**：

| 现象 | 根因 | 怎么发现 |
|---|---|---|
| 图片引用对了、状态码 200，打开是空框 | JP2 伪装 `.png` | `verify_assets.py` 用 PIL 读真实 `format` |
| 数据里有 `images: [...]` 却只渲染第一张 | 字段定义了没渲染 | 人眼比对 `content-profile.md` 与渲染结果（铁律 19） |
| `MASTER.md` 写 `#B83232`，站点实际 `#B33A2A` | 两份真源漂移 | 铁律 26：一份真源，`MASTER.md` 是副本 |
| 5 个站单看都合格，摆一起全一样 | 判据只有单站这一条腿 | `audit_tokens.py --batch` |
| 所有门禁全绿，但视觉签名 5/5 缺失 | 判据不存在 | 判据自测会暴露这类问题 |
| 声明 `master-detail`、页数也对，但详情页只是卡片放大 | **假子页**：拆了等于没拆 | 机器判据查不到，靠人眼（`design-qa.md` 六条人眼判据） |
| 页内目录点了能跳，但落点被吸顶栏盖住一半 | 没设 `scroll-margin-top` | 人眼；F15 只能验「锚点存在且可达」，验不了「落点准」 |
| 目录锚点全对，但键盘用户跳过去焦点还在原处 | 没做跳转后 `focus()` | 人眼 + 无障碍检查（跳转后要 `focus({preventScroll:true})`） |
| `--site` 全绿，但详情页没有独立 URL（仍是 `#anchor`） | 粒度声明对了、实现没跟上 | 人眼：点开卡片看地址栏变不变 |

---

## §6 批次工作流：怎么验证一批站不撞车

**做法很简单：一个工作区，一次 `--batch`，看数字。**

### 6.1 目录怎么放

```
<你的工作区>/
├── site-a/                   ← 每个子目录一个站
├── site-b/
├── site-c/
└── .style-ledger.json        ← 账本自动生成在这里（项目侧，不进 skill 仓库）
```

**关键**：`--batch` 扫描的是**子目录**，每个子目录里要有 `tokens.css` 或 `MASTER.md`。

**想先确认脚本本身好使**，跑这条端到端冒烟测试（走真实流水线出 5 个站，应当 PASS）：

```bash
WS=/tmp/batch-smoke && rm -rf $WS
for spec in "warm-hospitality:paper:a" "provisions-label:white:b" "cyber-terminal:deep:d" \
            "expressive-artistic:tint:c" "concrete-brutalist:stone:b"; do
  slug="${spec%%:*}"; rest="${spec#*:}"; surf="${rest%%:*}"; var="${rest##*:}"
  mkdir -p "$WS/$slug/src/styles"
  python scripts/emit_tokens.py --anchor "$slug" --surface "$surf" \
    --variant "$var" --css-only > "$WS/$slug/src/styles/tokens.css"
done
python scripts/audit_tokens.py --batch $WS
# 期望：底色 5/5 唯一、display 5/5 唯一、中轴不塌缩 → 综合：PASS
```

### 6.2 跑对比

```bash
# 交付前：查重（事前）
python scripts/ledger.py --check --dir <工作区> --anchor … --font-display …

# 交付后：记账
python scripts/ledger.py --commit --dir <工作区> --name <站名> …

# 一批做完：机检（事后）
python scripts/audit_tokens.py --batch <工作区>

# 批次健康报告（人读）
python scripts/ledger.py --report --dir <工作区>
```

**想做「改之前 vs 改之后」的对比实验**，就建两个目录各放一批产物，分别跑 `--batch` 比数字 ——
这正是当初定位「五个站全白底」的方法。

### 6.3 改造前：历史基线（v0.8 之前那批站的实测，已归档）

下面这段是**真实的失败现场**，也是 v0.8 全部改动的出发点。原始样例目录已移出本仓库
（归档在 `E:\Code\testing-example-2026-09-12.bak`），这里保留数字作为对照基准 ——
你的批次若出现同类分布，说明反同质化门没生效。

```
批次差异度审计 · 7 个站
====================================================================
  ✗ 底色值唯一率           2/7 = 29%                   阈值 ≥80%
      撞车：#FFFFFF×6
  ✗ 中轴种类             2 种（left-rail、center-axis）  阈值 ≥2 种
  ✗ 中轴最大占比           left-rail 5/7 = 71%          阈值 ≤60%
  ✗ display 唯一率      5/7 = 71%                     阈值 100%
      撞车：Inter×2
====================================================================
综合：FAIL（3 项不达标）
```

**读这段数字的正确方式**：它证明的不是「脚本会报错」，而是**「每个站单看都合格，
摆一起却全塌了」这件事真的会发生** —— 那 7 个站的 F 级检查全是 0。
这正是「单站自洽 ≠ 批次多样」要解决的问题。

> **注意中轴那两行是 v0.9.1 改过的。** 旧阈值是「≥3 种」，而中轴总共就 3 档，
> 等于要求覆盖率 100% —— 那是**配额**不是多样性，会强制每批含一个 `split` 站。
> 现在改成「≥2 种 **且** 单档占比 ≤60%」：**仍然抓得住塌缩，但不再制造必经点**。

### 6.4 改造后：同一批站重做成 2.0 的实测

这不是模拟数据 —— 是把上面那批站用改造后的 skill 重做（`*-2.0` 目录），再跑同一条命令：

```
批次差异度审计 · 10 个站
====================================================================
  ✓ 底色档种类            5 种（ink、stone、paper、tint、white）  阈值 ≥3 种
  ✓ 底色值唯一率           10/10 = 100%                     阈值 ≥80%
  ✓ 中轴种类             2 种（left-rail、center-axis）       阈值 ≥2 种
  ✓ 中轴最大占比           left-rail 5/10 = 50%             阈值 ≤60%
  ✓ display 唯一率      10/10 = 100%                     阈值 100%
  ✓ 基准字号种类           5 种（15px、14px、17px、18px、16px）    阈值 ≥3 种
  ✓ 间距基数种类           4 种（4px、8px、16px、12px）           阈值 ≥3 种
  ✓ 圆角档种类            4 种（0px、2px、4px、16px）            阈值 ≥2 种
====================================================================
  逐站指纹：
    acute-angle-2.0    ink     left-rail     Familjen Grotesk     #110F09
    hongda-auto-repair-2.0 stone   left-rail     Barlow Condensed     #E1DED4
    laochen-noodles    paper   left-rail     DM Serif Display     #FCF5F0
    maimang-site-2.0   tint    center-axis   Zilla Slab           #F8EADF
    shihua 2.0         tint    center-axis   Marcellus            #FAE9DD
    teapot-artisan     —       center-axis   Ma Shan Zheng        #FBFAF7
    tongguan-lvxin     stone   left-rail     Archivo Black        #D5DFEA
    tutuhuahua 2.0     paper   center-axis   Cormorant Garamond   #F9F7EF
    vinyl-store-site   white   left-rail     Archivo              #FFFFFF
    void-codex         —       center-axis   Sora                 #0C1014
====================================================================
综合：PASS —— 本批次风格差异度达标。
```

**逐站指纹那一栏就是效果本身**：10 个站的底色从 `#110F09`（近黑）一路铺到 `#FFFFFF`（纯白），
display 字体 10 个全不重名。**这就是「各行各业、风格迥异」的可量化版本。**

### 6.5 数字就是你的效果报告

| 指标 | 改造前（7 站） | 改造后（10 站 2.0） | 达标线 |
|---|---|---|---|
| 底色值唯一率 | **2/7 = 29%** | **10/10 = 100%** | ≥80%，目标 100% |
| display 唯一率 | **5/7 = 71%** | **10/10 = 100%** | 100% |
| 中轴 | 2 种、最大占比 71% ✗ | 2 种、**最大占比 50%** ✓ | ≥2 种 且 单档 ≤60% |
| 底色档种类 | 2 种 | **5 种** | ≥3 种 |
| 锚点使用率 | 3/40 = 7.5% | 10 个不同锚点 | ≥5 个不同锚点 |

**别忘了每站交付后记账**，否则下一次对比时账本是空的：

```bash
python scripts/ledger.py --commit --dir <工作区> \
  --name <站名> --anchor <slug> --family <族> --surface <档> \
  --variant <轴> --pair 0 --axis <中轴> --layout <原型> --ia <原型> \
  --font-display <首族名>
```

---

## §7 阅读路线图

**不要一次全读。** `SKILL.md` 的「阅读顺序」表规定了每阶段读什么，那是**给 agent 的**。这一节是**给你（人）的**。

### 第一次读（约 40 分钟）

| 顺序 | 文件 | 为什么 |
|---|---|---|
| 1 | [`CONCEPTS.md`](CONCEPTS.md) §1–§5 | 建立框架，理解三个失败模式 |
| 2 | [`SKILL.md`](SKILL.md) 的「铁律」五组 | 34 条价值观，比流程更重要 |
| 3 | [`SKILL.md`](SKILL.md) 的「流程与阶段门」表 | 11 道门一览 |
| 4 | [`layouts.md`](layouts.md) 的「视觉签名」节 | 反同质化的核心机制 |
| 5 | [`CONCEPTS.md`](CONCEPTS.md) §4.3 | 分清两个「签名」 |
| 6 | [`architectures/granularity.md`](architectures/granularity.md) | 分清「选出来的维度」与「算出来的维度」——这是 v0.9 的核心 |

### 想改东西时读

| 想改 | 读 |
|---|---|
| 加锚点 | [`layouts.md`](layouts.md)（layout/axis 定义域）+ `styles/families.md`（族）+ `styles/signatures.json` 的 `_legend` |
| 加判据 | [`design-qa.md`](design-qa.md) + `scripts/audit_tokens.py` 的判据实现 |
| 改选型逻辑 | [`intake.md`](intake.md) + [`decide.md`](decide.md) |
| 改技术栈判断 | [`techstack.md`](techstack.md) + `scripts/pick_stack.py` |
| **改页面粒度 / 页内导航判断** | `architectures/pagination.json`（**改阈值只改这里**）+ [`architectures/granularity.md`](architectures/granularity.md) + `scripts/pick_pages.py` |
| 改排版算法 | [`typography.md`](typography.md) + `scripts/emit_tokens.py` |
| 改反同质化机制 | `scripts/ledger.py` + [`CONCEPTS.md`](CONCEPTS.md) §5 |

### 永远不用读

| 文件 | 为什么 |
|---|---|
| `scripts/check_env.py` | 探测脚本，跑就行，不用读 |
| `scripts/extract_pdf_assets.py` | 只在特定场景用 |
| [`THIRD-PARTY.md`](THIRD-PARTY.md) | 致谢清单 |

---

## §8 一页速查表

### 改完必跑

```bash
python scripts/validate_skill.py      # 改了 skill 自身 → ERROR 0
python scripts/audit_tokens.py <MASTER.md>   # 改了产出的数值 → F 级 0
python scripts/audit_tokens.py --site <站点目录>  # 改了产出的结构 → F 级 0
```

### 一次交付的完整命令序列

```bash
# 1. 探环境（首次）
python scripts/check_env.py

# 2. 提取与校验源材料
python scripts/extract_source.py <输入> <输出目录>
python scripts/verify_assets.py <输出目录>/manifest.json <输出目录>/assets

# 3. 技术栈选型
python scripts/pick_stack.py --pages … --interaction … --maintainer … \
  --data … --host … --i18n … --render … --budget …

# 4. 页面粒度与页内导航（内容驱动，算出来的）
python scripts/pick_pages.py --entries … --depth … --shareable --ia … --blocks …

# 5. 批次查重（开工前）
python scripts/ledger.py --check --dir <工作区> --anchor … --surface … \
  --variant … --pair … --axis … --family … --layout … --font-display …

# 6. 生成 token
python scripts/emit_tokens.py --anchor <slug> --surface <档> --variant <轴> \
  --pair <n> --css-only > src/styles/tokens.css

# 7. 审计产出（数值 + 结构）
python scripts/audit_tokens.py design-system/MASTER.md --anchor <slug>
python scripts/audit_tokens.py --site <站点目录>

# 8. 批次审计（一批做完）
python scripts/audit_tokens.py --batch <批次目录>

# 9. 记账（交付后）
python scripts/ledger.py --commit --dir <工作区> --name <站名> --anchor … \
  --family … --surface … --variant … --pair … --axis … --layout … --ia … \
  --font-display …

# 10. 批次报告
python scripts/ledger.py --report --dir <工作区>
```

### 三个数值维度 + 两个内容维度

| 维度 | 参数 | 取值 |
|---|---|---|
| 底色档 | `--surface` | `white` `paper` `tint` `stone` `slate` `ink` `deep` |
| 尺度变体轴 | `--variant` | `a` 原值 / `b` 收紧 / `c` 放松 / `d` 张扬 |
| 字体对 | `--pair` | `0` 主选 / `1` `2` `3` 族备用池 |
| **页面粒度** | `granularity` | `single` / `master-detail` / `multi-page` / `n-a` |
| **页内导航** | `inPageNav` | `none` / `anchor-jump` / `sticky-toc` / `section-rail` |

**前三个是「选」的（排除法），后两个是「算」的（判据法）。** 算出来的不进约束筛选表，
也不问用户 —— 问内容规模，不问结论。

### 四条元规则

1. **凡能被枚举的，就不要写散文**
2. **任何「必填」都必须配机器判据**
3. **加了判据，必须配负向测试**（而且**判据写松了也等于没写** —— F16 只认 `map`/`flatMap`，不认 `forEach`）
4. **定期用规则反审规则本身** —— 逐条问「违反它的最小产物长什么样，哪个脚本会报错？」，答不出脚本名的就是欠账

### 剧本：怎么发现 skill 的欠账

```
1. 列出全部铁律
2. 对每条问：违反它的最小产物长什么样？
3. 那个产物会被哪个脚本、哪条判据报错？
4. 答不出 → 记入欠账，补判据 + 补负向测试
```

v0.9.1 用这个方法审出 34 条铁律里只有 14 条有判据，其中 5 条本可机器化 —— 现已补成 F16–F20。

---

---

## 附：内容库规模清单

> 这份清单原来放在 README 里，因为太细搬到这里。想知道「仓库里到底有什么、各有多大」，看这一节就够。

| 资产 | 文件 | 规模 |
|---|---|---|
| 风格锚点 | `styles/index.json` | 40 个，每个都带 `layout` / `axis` / `imagePolicy` / `iconPolicy` / `density` / `when` / `never` |
| 字体搭配 | `styles/fonts.json` | 40 套具名 display × body 搭配，**display 全库唯一**，含 mono / 中文回退 / 加载策略 |
| 族级备用搭配 | `styles/fonts.json` → `_familyPools` | 33 对（11 族 × 3），供同锚点第二次使用时轮换，与 40 个主搭配零重复 |
| 底色预设 | `styles/signatures.json` → `_surfacePresets` | 7 档：white / paper / tint / stone / slate / ink / deep，含两档深底 |
| 尺度变体轴 | `styles/signatures.json` → `_variantAxes` | 4 条：原值 / 收紧 / 放松 / 张扬，对字阶公比、基准字号、间距单位、圆角做带 clamp 的偏移 |
| 候选技术栈 | `techstack.md` + `scripts/pick_stack.py` | 7 个：plain-html / astro / eleventy / vite / next / nuxt / hugo |
| 风格族 | `styles/families.md` | 11 个，收敛用的中间层，由「内容支撑力 / 转化目标 / 密度诉求」决定，**不由品类决定** |
| 完整 spec | `styles/specs/` | 6 个可直接粘的 token 骨架 |
| IA 原型 | `architectures/` | 4 个：portfolio / narrative / directory / conversion，各带默认页面粒度与默认页内导航（可被内容推翻） |
| 内容维度 | `architectures/pagination.json` + `scripts/pick_pages.py` | 页面粒度 × 页内导航，阈值集中在注册表，脚本只读不硬编码 |
| 参考池 | `referencePool` | 20 个，含 game-lab 的 70 种可切换皮肤 |

本地 spec 不够用时按 `_specFallback` 三级降级，中间一级可外接 `npx typeui.sh pull <slug>` 的 67 种风格。

**13 类输入源预案**：PDF / 图片 / docx / xlsx+csv / pptx / md+txt / 视频 / 音频 / 现有站 / 参考站 / 纯文字 / 混合 / 无输入 —— 每一类都有自己的提取路径、降级方案和坑（见 `source.md`）。
不能处理的情况会**明说**，不会假装：本机没有 OCR 时扫描件要用户提供文字，没有 ASR 时视频旁白要用户提供字幕。`scripts/check_env.py` 会先告知。

---

**下一步**：回到 [`CONCEPTS.md`](CONCEPTS.md) 末尾的「60 秒自我检查清单」，试着回答那八个问题。答得出来，你就真的掌握了。
