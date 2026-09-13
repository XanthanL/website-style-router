---
name: website-style-router
description: 从「已有内容」推导网站的建站方案：技术栈选型（plain-html / astro / eleventy / vite / next / nuxt / hugo）、风格选型、信息架构、页面粒度、页内导航、布局原型与可执行的排版/色彩/字体 token，产出可运行站点或嵌入已有主站的新页面。当用户提供了尚未建站的内容（艺术家作品集 PDF、艺术项目、餐厅/咖啡店、企业文化机构、独立品牌、实物商品等），或要把已有内容做成一页挂到现有站点时使用。覆盖：源材料提取（PDF/图片/文档/表格/PPT/视频/音频/现有站/参考站/纯文字）、意图追问、决策权归属、约束筛选、风格族收敛、字体搭配、字体选型、批次差异度（跨站去重）、确定性 token 生成、审美数值审计、宿主站对齐、双语、素材校验、上线前验收。触发词：建站、建站方案、官网、用什么框架、设计系统、视觉基调、要不要拆子页面、单页还是多页、详情页、目录、锚点跳转、跳到某一段、侧边目录、布局、排版、字阶、行高、配色、底色、批次查重、风格账本、模仿某站风格、嵌入主站、design system、style selection、tech stack、font pairing、batch diversity、in-page navigation、page granularity。不要用于纯 UI 组件打磨或动效微调（那是 animate / impeccable 的活）。
license: MIT
compatibility: 需要 Python 3.10+ 运行 scripts/（pypdf、Pillow 必需；python-docx、openpyxl、python-pptx 按输入格式按需）。首次使用先跑 python scripts/check_env.py 探测本机能力与降级方案。token 生成、审美审计、技术栈选型、页面粒度选型脚本均零第三方依赖。仅当 Phase 1.5 选定 astro/next/nuxt/eleventy/vite 时才需要 Node 18+（hugo 需 Go 二进制）；选定 plain-html 则产物零依赖、双击即开。ffmpeg 可选（视频抽帧）。默认无 OCR / ASR —— 扫描件与无字幕音频必须回退给用户提供文字。
metadata:
  version: 0.9.2
  author: XanthanL
  repository: https://github.com/XanthanL/website-style-router
  standard: Agent Skills Specification (https://agentskills.io/specification)
  keywords:
    - tech-stack-selection
    - style-selection
    - design-system
    - font-pairing
    - typography
    - information-architecture
    - page-granularity
    - in-page-navigation
    - static-site
    - astro
    - portable-skill
    - batch-diversity
    - style-ledger
    - surface-dimension
---

# Website Style Router

从已有内容出发，依次落定 **源与交付形态 → 意图 → 约束 → 技术栈 → 族与锚点 → layout + axis → 字体与 token → 站点**。

**路径约定**：本文提到的所有相对路径都以本 skill 的根目录为基准（即 `SKILL.md` 所在目录）。无论安装在 `~/.claude/skills/`、`.codex/skills/`、`.cursor/skills/`、`~/.workbuddy/skills/` 还是任意 agent 的 skills 目录，路径不变。

> **第一次接触这套 skill 的人**（不是 agent）先读 [`CONCEPTS.md`](CONCEPTS.md) 建立概念框架，
> 再读 [`TUTORIAL.md`](TUTORIAL.md) 学操作与自定义。本文是给 agent 的执行指令，人读它会偏流程细节。

## 工作量分级（先判级，别让小事跑全套仪式）

| 级 | 何时是这一级 | 必经门 | 说明 |
|---|---|---|---|
| **L0 · 出系统** | `system-only`，或只要 token / 规格，不搭站 | G-1 → G0 → G1 → G1.5 → **G2** → G3 → 审计 | 跳过 G4/G5 的站点项 |
| **L1 · 单页** | 单页独立站、单一内容源、单语 | 全流程，G5 按精简清单 | 最常用 |
| **L2 · 多页 / 嵌入** | 多页 · `embedded` · 多语言 · 有参考站 | 全流程 + [`host-align.md`](host-align.md)，G5 全清单 | 返工最贵 |

判级方法：`system-only` → L0；`embedded` / 多语言 / 有参考站 / 多页 → L2；其余 → L1。

**G1.7 的页面粒度判定可能把 L1 推到 L2。** 判级是**开工前的初判**，不是最终结论 ——
若判出 `master-detail` / `multi-page`，回来把级别改成 L2（页面清单、验收清单都要跟着变）。

**级别只决定跑多少仪式，不决定质量门。** G1.5 技术栈判断、G1.7 页面粒度判断、
G2 人工确认与交付前的审美数值审计（`audit_tokens.py`）在任何级别都必做。

## 阅读顺序（控制上下文，别一次全读）

| 阶段 | 读 | **不读** |
|---|---|---|
| -1 | [`source.md`](source.md)、[`decide.md`](decide.md) 的 C 类清单 | `styles/*` |
| 0 | [`intake.md`](intake.md)（B0–B11 决策树） | — |
| 1 / 1.5 | [`techstack.md`](techstack.md) + 跑 `scripts/pick_stack.py` | 框架官方文档（选型靠需求，不靠查文档） |
| 1.7 | [`architectures/granularity.md`](architectures/granularity.md) + 跑 `scripts/pick_pages.py` | `architectures/*.md` 的其余三份 |
| 2 | [`styles/index.json`](styles/index.json) 的 `families` 段 + [`styles/families.md`](styles/families.md) | `styles/specs/*` |
| 3 | 命中锚点的 `styles/specs/<slug>.md`（**只读 1 个**）+ [`layouts.md`](layouts.md) | 其余 specs |
| 4 | [`typography.md`](typography.md) + `styles/signatures.json` 里**该锚点那一条** + `styles/fonts.json` 里**该锚点那一条** | 全量 signatures / fonts |
| 5 | `embedded` 时读 [`host-align.md`](host-align.md)；提取/校验用 [`scripts/`](scripts/) | — |
| 6 | [`design-qa.md`](design-qa.md) + [`checklist.md`](checklist.md) | — |

> 阶段 1.7 与阶段 2–4 谁先谁后**不影响判断**，但先算页面粒度更省事 ——
> 粒度定了，「要做几个页面」才是已知数，风格与布局才有确定的落点。

## 铁律索引（34 条 · 全部必守）

> 每条只留一句可执行结论。**理由、做法、踩过的坑与对应判据** 见 [`references/rules.md`](references/rules.md)。
> **至少读两遍**：G2 落定前、G5 验收前。编号是外部引用锚点，不可重编号。

**选型**
1. 先定源，再谈设计。
2. 先定交付形态。
3. 先 Grill，再选型。
4. 先砍空间，再选风格。
5. 先定技术栈，再定风格与字体。
6. 先选族，再选锚点。
7. 风格必须驱动布局，不能只驱动颜色。
8. 图文策略是选型的一部分。
9. 只落 token，不落形容词。
10. IA 优先于风格。
11. 风格库按需加载。

**执行**
12. 决策权分明。
13. 人必须在落定后点头。
14. 嵌入宿主 = 服从宿主。
15. 提取与校验必须靠脚本。
16. "引用对了 + 状态码 200"不能证明图片能显示。
17. 提取不了的，明说提取不了。
18. 每条内容必须能指回源。
19. 字段定义了就必须渲染出来。
20. 中轴与尺寸在落定前定完。
21. 交付时交代三件事

**落地与审美**
22. token 由脚本生成，不许手编。
23. 字体必须是被搭配出来的，不是被继承的。
24. 排版数值先于配色。
25. 交付前必须跑审美数值审计。
26. 一份真源。

**反同质化（交付前逐条自检）**
27. 结构必须跟着锚点变，不是换色。
28. 字体搭配逐站不同。
29. 产物形状要能反映技术栈。
30. 单站自洽 ≠ 批次多样。
31. 底色是被选的，不是默认的。
32. 同一锚点第二次使用必须换组合。

**可导航性（IA 的第二半）**
33. 页面粒度是被判断出来的，不是默认单页。
34. 页内导航跟着页面长度与阅读模式走，不是每个站都加。

<!-- 铁律全文见 references/rules.md。本索引由脚本从全文抽取，改全文后须重跑；
     validate_skill.py 的 H4 会校验编号连续与条数。 -->
## 流程与阶段门

每道门都有**出口检查**；不过就退回指定阶段，不许带病前进。门按工作量分级取用（见上）。

| 门 | 阶段 | 关键动作 | 出口检查 | 不过则 |
|---|---|---|---|---|
| **G-1** | 源材料 & 交付形态 | 识别源类型 → `extract_source.py` 提取 → 建 `source-map.md` → `verify_assets.py` | 三零（缺失/未用/格式）成立、体积 <15MB、每条 warnings 已记处置、溯源表四段齐 | 回补源，**继续问不是解法** |
| **G0** | Grill | `intake.md` B0–B11，一次一问 + 推荐答案 | **C 类问题全部有答案**；B 类已给推荐 | 继续问（≤3 轮） |
| **G1** | 约束筛选 | 逐条判定，输出排除清单 | 排除项 ≥3 且写明被谁排除 | 回 G0 补约束 |
| **G1.5** | 技术栈选型 | 收 D1–D8 → 跑 `scripts/pick_stack.py` → 出 `tech-stack.md` | **技术栈是判断出来的**（有被排除项 + 3 条可观测证伪条件）；`embedded` 时为「确认宿主栈」 | 回 G0 补需求 |
| **G1.6** | 批次查重 | 跑 `scripts/ledger.py --check`，把本次指纹（锚点 / 底色档 / 中轴 / display 字体）与同批次已交付的站比对 | **无高冲突**：锚点与 display 字体必须唯一；底色档 / 中轴在同批次出现 ≤2 次 | 换锚点 / 换底色档 / 换变体轴 / 换字体对，再查一遍 |
| **G1.7** | 页面粒度与页内导航 | 收 P1–P7 / N1–N4 → 跑 `scripts/pick_pages.py` → 两轴结论写进 `content-profile.md` | **两轴都有结论且都有理由**（不是默认值）；粒度被推到 `master-detail`/`multi-page` 时同步把工作量级别改为 L2 | 回 G0 补内容量级 |
| **G2** | 落定 ★ | 技术栈 + 1 族 → 1 锚点 → 1 layout + 1 axis + **底色档 + 变体轴 + 字体对** + **≥3 条视觉签名** + **页面粒度 + 页内导航**；写出 3 条证伪条件 | **用户明确点头** + 证伪条件写得出来 + **批次查重已过** + **页面清单列得出来** | 不许开工 |
| **G3** | token | `emit_tokens.py --surface <档> --variant <轴> --pair <n>` 出骨架 → 锚点特化 → `MASTER.md`（含 `--axis` + **视觉签名段**）；`embedded` 另出 `HOST.md` | 零形容词、`never` 可检查、字阶 ≤6 级、**字体搭配非通用默认**、**`audit_tokens.py` F 级 0（含 F10 视觉签名）**、宿主令牌有来源路径 | 重写 |
| **G4** | 搭站 / 嵌入 | 按 G2 的**页面清单**逐页搭：索引页 + 详情页（同一模板生成）；套骨架 → 填真实内容；嵌入走 `host-align.md` 6 步 | 构建通过（站点用 `npm run build`；宿主内改动用宿主自带类型检查，如 `tsc --noEmit`）；**页面文件数与声明的粒度一致** | 修 |
| **G5** | 验收 | `design-qa.md` 数值判据 + `checklist.md` 逐条打勾 + **`audit_tokens.py --site <站点目录>`** + **`audit_tokens.py --batch <批次目录>`** | **四处全过**（含 F14/F15 结构、F11 批次差异度），或未过项标 `[未定]` 并说明 | 修 |
| **G6** | 微调回访 | 主动过 6 项：中轴 / 区块去留 / 语言全覆盖 / 图是否真渲染 / 体积与响应式 / 移动端断点 | 用户确认 | 修 |

**G-1 … G2 是判断段，G3 起是执行段。** 源 → 意图 → 约束 → **技术栈** → **批次查重** →
**页面粒度与页内导航** → 落定（族 / 锚点 / 布局 / 中轴 / 底色 / 变体 / 字体 / 签名 / 语言）
全部判断完、并拿到用户点头之后，才允许开工写代码 —— 这是「先完成所有判断，再开始执行」的落地方式。
**「做几个页面」属于判断段，不属于执行段** —— 它是内容决定的，不是搭站时顺手决定的。
**G2 是唯一的强制人工确认点。** 其余门可自主通过，但必须在 G6 交付说明里交代（铁律 21）。
**交付后立即 `python scripts/ledger.py --commit ... --font-display <首族名>` 记账** —— 不记账，下一个站就查不了重；
漏记 `--font-display`，批次报告会判「未记录」不通过（没记录 = 这一项没被校验）。

## 输出契约

- `source-map.md` — 源 / 内容映射 / 未采用 / 提取告警（四段）
- `references.md` — 有参考站时必出，含「学什么 3 条 / **不学什么 2 条**」
- `tech-stack.md` — **Phase 1.5 必出**：D1–D8 输入判定 + 选定栈 + 被排除项（含被哪条判据排除）+ 落地约束 + 3 条可观测证伪条件
- `intent-summary.md` — 源与形态、成功定义、转化目标、图文策略、语言策略、参考站、技术栈、族与锚点、中轴、区块与尺寸、硬约束
- `content-profile.md` — 画像 + 约束判定 + 被排除项（含被排除的布局）+ **「页面粒度与页内导航」段（两轴结论 + 依据 + 被排除档位 + 页面清单 + 证伪条件）** + **待补表**
- `design-system/MASTER.md` — token + `--axis` + **底色档 `--surface` + 变体轴 `--variant`** + **字体搭配（`--font-display`/`--font-body`/`--font-mono`/`--font-cjk`）** + **视觉签名（≥3 条结构级手法）** + `never` 清单；**须与生效的 tokens 文件逐值一致，且 `audit_tokens.py` F 级为 0（含 F10）**
- `design-system/HOST.md` — `embedded` 必出
- 能通过构建的产物（按 `tech-stack.md` 选定栈：`plain-html` 无构建、`astro`/`next` 用 `npm run build`；宿主内：宿主自带类型检查）；
  **页面文件数须与 `content-profile.md` 声明的页面粒度一致**（`audit_tokens.py --site` 的 F14 会查）
- `intent-summary.md` 里的**页面粒度与页内导航两行摘要**（`master-detail（1 + N）` 这类）
- `.style-ledger.json` — **项目侧状态，不进 skill 仓库**：每站交付后 `ledger.py --commit` 记一条，供下一站查重
- `verify_assets.py` → 缺失 0 / 未用 0 / 格式 0 / 体积 <15MB
- 每条结论可追到某条约束；追不到的标 `[未定]`

## 实现说明（分层，不是纯 MD）

一句话：**可枚举的进 JSON 注册表，确定性的进 Python 脚本，散文只承载推理。**
每层「用什么形式、为什么」的对照表见 [`references/architecture.md`](references/architecture.md)；
概念版见 [`CONCEPTS.md`](CONCEPTS.md)。

## 本 skill 的文件地图（精简）

**完整版（每个文件的详细职责）见 [`references/filemap.md`](references/filemap.md)。**
下面是导航够用的最短版本 —— **用到时才读，不要一次全读**（按上一节的阅读顺序表走）。

**阶段文档**：[`source.md`](source.md) 源提取 · [`intake.md`](intake.md) Grill 决策树 ·
[`decide.md`](decide.md) 决策权 · [`techstack.md`](techstack.md) 技术栈 ·
[`architectures/granularity.md`](architectures/granularity.md) 页面粒度 ·
[`layouts.md`](layouts.md) 布局与中轴 · [`typography.md`](typography.md) 排版数值 ·
[`design-qa.md`](design-qa.md) 审美判据 · [`checklist.md`](checklist.md) 验收 ·
[`host-align.md`](host-align.md) 嵌入（仅 `embedded` 时）

**注册表**（按需查，禁止整体读入上下文）：
[`styles/index.json`](styles/index.json) 40 锚点 ·
[`styles/signatures.json`](styles/signatures.json) 签名 + 底色 + 变体轴 ·
[`styles/fonts.json`](styles/fonts.json) 字体搭配 ·
[`styles/families.md`](styles/families.md) 11 族 · [`styles/specs/`](styles/specs/) 6 个 spec ·
[`architectures/pagination.json`](architectures/pagination.json) 粒度与导航阈值

**脚本**（**跑**它，不要读源码）：
[`check_env.py`](scripts/check_env.py) 环境探测 · [`pick_stack.py`](scripts/pick_stack.py) 技术栈 ·
[`pick_pages.py`](scripts/pick_pages.py) 页面粒度 · [`emit_tokens.py`](scripts/emit_tokens.py) 生成 token ·
[`audit_tokens.py`](scripts/audit_tokens.py) 审计（含 `--site` / `--batch`）·
[`ledger.py`](scripts/ledger.py) 批次账本 · [`extract_source.py`](scripts/extract_source.py) 提取 ·
[`verify_assets.py`](scripts/verify_assets.py) 素材校验 ·
[`extract_pdf_assets.py`](scripts/extract_pdf_assets.py) PDF 页图 ·
[`validate_skill.py`](scripts/validate_skill.py) 改完自检

**外部依赖**（均 MIT、均可选、**不是前置条件**）：`uipro` 交叉验证 ·
`npx typeui.sh pull <slug>` 取 spec · `hue` token 反抽 · grill-me 方法学 · game-lab 皮肤库。
宿主能力（浏览器 / 截图）按需使用，不硬编码任何一个。

## 版本

变更记录见 [`CHANGELOG.md`](CHANGELOG.md)。当前 `0.9.2`。

**开工前先确认版本**：读本文件 frontmatter 的 `metadata.version`，并在产出的 `tech-stack.md` 头部写明。
历史教训：一个站的落盘时间晚于 v0.7 发布，但它读到的仍是 0.6.0 的 SKILL.md ——
产出里没有任何字段能暴露这一点，直到事后比对才发现。**产出不带版本号 = 无法判断用的是哪一版。**
