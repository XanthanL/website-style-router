# Website Style Router

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Scripts: zero dependency](https://img.shields.io/badge/scripts-zero%20dependency-brightgreen.svg)](scripts/)
[![Version](https://img.shields.io/badge/version-0.9.1-informational.svg)](CHANGELOG.md)

[English](README.md) · **简体中文**

> 从「已有内容」推导网站风格选型、信息架构与布局，产出**能跑**的站点。
> Derive a website's visual direction, IA and layout from content you already have — and ship a site that actually builds.

一个**可移植的 Agent Skill**（遵循 [Agent Skills Specification](https://agentskills.io/specification)）。把 PDF / 图库 / 文档 / 视频 / 现有站 / 一句描述，变成「风格族 → 锚点 → 布局 → token → 站点」的一条确定路径。

它不解决「长什么样」这一个问题，而是解决**顺序问题**：先定源，再定交付形态，再砍约束空间，最后才谈风格。市面上几乎所有风格工具（TypeUI / Curio / uipro）只做最后一步。

---

## 它解决什么

把内容丢给 AI 做站，最常见的失败不是"不好看"，而是：

| 失败 | 本 skill 的对策 |
|---|---|
| 选型靠"挑一个" → 输出向均值收敛 = 一眼 AI 味 | 禁止菜单式选型，改为**约束排除 + 两级收敛**（40 锚点 → 11 族 → 1 锚点） |
| 只换配色，布局还是那套模板 | 每个锚点强制声明 `layout` + `axis`，**风格必须驱动布局** |
| **不管什么需求都生成同一套骨架（Astro + src/pages/…）** | **Phase 1.5 技术栈选型**：先按需求（页数 / 交互 / 维护者 / 数据源 / 宿主 / 语言 / 渲染 / 性能）排除 + 定序，产出 `tech-stack.md`，写 3 条证伪条件 |
| **40 个锚点的字体都是 `Inter, -apple-system…`** | **`styles/fonts.json` 字体搭配注册表**：每个锚点一对具名字体（display **全库唯一**），由 `emit_tokens.py` 落成 `--font-display`/`--font-body`；`audit_tokens.py` F6 机器校验 |
| **不同项目产出同一个形状，只是文案不同** | **反同质化门（单站 + 跨站）**：每站声明 ≥3 条结构级视觉签名；跨站由 `scripts/ledger.py` 记批次账本（锚点 / 字体 / 底色 / 变体轴 / 族）事前查重，`audit_tokens.py --batch` 事后机检 |
| **五个站摆一起，底色全是 `#FFFFFF`、字阶逐值相同** | **底色维度（surface）+ 尺度变体轴（variant）**：7 档底色预设（white/paper/tint/stone/slate/ink/deep，含深底）× 4 条变体轴（原值/收紧/放松/张扬），同一锚点第二次使用必须换组合，组合空间 40×4×7×4 |
| **同一个锚点复用，字体注册表就"无字可用"** | **族级备用池 `_familyPools`**：11 族 × 3 对备用搭配（与 40 个锚点的主搭配零重复），`validate_skill.py` F12 校验覆盖与唯一性 |
| **不管内容多少，永远只有一个 `index` 首页，详细内容没地方放** | **页面粒度（granularity）判据**：`scripts/pick_pages.py` 读内容事实（条目数 / 深度 / 是否要分享单条）算出 `single` / `master-detail` / `multi-page`，`audit_tokens.py --site` F14 机检「声明 = 实际页数」 |
| **长页只能一翻到底，找不到关键部位** | **页内导航（inPageNav）判据**：档位由内容定（`none` / `anchor-jump` / `sticky-toc` / `section-rail`），形态由布局定；F15 校验锚点**可达**（含断链检测） |
| **字段定义了却没渲染 / 内容编的 / 两份真源不一致 / 嵌入不服从宿主 / 产物形状与技术栈不符** | **F16–F20 交付完整性判据**（v0.9.1）：字段必须渲染、内容可溯源、一份真源、嵌入服从宿主、产物形状反映技术栈 —— 这五条此前只写在铁律里，没有机器判据 |
| 页面里全是编的内容 | 强制**逐条溯源**（`p12 · "原句"`），指不回去的删掉 |
| 图片引用对了、校验也过了，但打开是空的 | 用 PIL 读**真实编码格式**（JP2 伪装 `.png` 是真实踩过的坑） |
| 该问的不问，用户事后逐个指导 | `decide.md` 四档决策权（A 自主 / B 推断确认 / C 必须问 / D 绝不代做） |
| 嵌进已有站点后把宿主风格搞坏 | `host-align.md`：**同构而非相似**，宿主令牌优先 |

## 安装

同一份文件放进任意 agent 的 skills 目录即可，路径全部相对于 skill 根目录，无宿主专有依赖。

```bash
git clone https://github.com/XanthanL/website-style-router.git
```

| Agent | 放置位置 |
|---|---|
| Claude Code | `~/.claude/skills/website-style-router/` 或项目内 `.claude/skills/website-style-router/` |
| Codex | `.codex/skills/website-style-router/` |
| Cursor | `.cursor/skills/website-style-router/` |
| WorkBuddy / CodeBuddy | `~/.workbuddy/skills/website-style-router/` |
| 其他 | 任何「目录内含 `SKILL.md`」约定都可直接使用 |

装完后先跑一次环境探测，它会告诉你本机能提取什么、不能提取什么：

```bash
python scripts/check_env.py
```

**想先弄懂它是怎么设计的**，读两份根目录文档：

| 文档 | 回答什么 |
|---|---|
| [`CONCEPTS.md`](CONCEPTS.md) | **为什么这样设计**：三个真实失败模式、四层结构、名词表、核心洞察、三条元规则 |
| [`TUTORIAL.md`](TUTORIAL.md) | **怎么用、怎么改**：完整流程走查、命令手册、八种自定义实战、排错手册、批次对比工作流 |

## 使用

直接描述你要做的东西，把材料给它：

```
用 website-style-router，把这个 PDF 做成一个适合它的网站
（附：Vivian portfolio.pdf）
```

流程会自动走完 8 个阶段，**只在「落定」那一步停下来找你要确认**：

```
-1  源材料 & 交付形态  →  提取、溯源、校验    [门 G-1]
 0  Grill（意图追问）  →  一次一问 + 推荐答案  [门 G0]
 1  约束筛选           →  砍掉 80% 空间        [门 G1]
1.5 技术栈选型         →  需求 → 栈（排除+定序） [门 G1.5]
1.6 批次查重           →  账本查重 + 换组合     [门 G1.6]
1.7 页面粒度 & 页内导航 →  内容 → 几页 / 怎么跳   [门 G1.7]
 2  落定 ★             →  栈+族+锚点+布局+字体  [门 G2 · 唯一强制人工确认]
 3  token              →  MASTER.md            [门 G3]
 4  搭站 / 嵌入         →  可构建产物          [门 G4]
 5  验收               →  checklist 逐条        [门 G5]
 6  微调回访           →  主动过 6 项          [门 G6]
```

**1.7 是判出来的，不是问出来的。** 内容只有 3 个区块就 `single`，条目多且有深度就 `master-detail`；长页给锚点，短页不给。`pick_pages.py` 输出档位 + 逐条理由 + 被排除的档位 + 证伪条件，每一步都可复核。**"不拆页"和"不加目录"同样是一个判断结果**，不是遗漏。

产出物固定为这几个文件：`source-map.md`、`references.md`、`tech-stack.md`、`intent-summary.md`、`content-profile.md`、`design-system/MASTER.md`（嵌入时另有 `HOST.md`）、批次状态文件 `.style-ledger.json`，以及一个能通过构建的站点。

## 内容库

- **40 个风格锚点**（`styles/index.json`）— 每个都带 `layout` / `axis` / `imagePolicy` / `iconPolicy` / `density` / `when` / `never`
- **40 套字体搭配**（`styles/fonts.json`）— 每个锚点一对具名 display × body 字体，**display 全库唯一**，含 mono / 中文回退 / 加载策略；这是"字体单一"的修法
- **33 对族级备用搭配**（`styles/fonts.json` 的 `_familyPools`）— 11 族 × 3 对，供同锚点第二次使用时轮换
- **7 档底色预设**（`styles/signatures.json` 的 `_surfacePresets`）— white / paper / tint / stone / slate / ink / deep，含两档深底；这是"五个站全白底"的修法
- **4 条尺度变体轴**（`styles/signatures.json` 的 `_variantAxes`）— 原值 / 收紧 / 放松 / 张扬，对字阶公比、基准字号、间距单位、圆角做带 clamp 的偏移
- **7 个候选技术栈**（`techstack.md` + `scripts/pick_stack.py`）— plain-html / astro / eleventy / vite / next / nuxt / hugo，按需求 8 判定项排除 + 定序
- **11 个风格族**（`styles/families.md`）— 收敛用的中间层，族由「内容支撑力 / 转化目标 / 密度诉求」决定，**不由品类决定**
- **6 个完整 spec**（`styles/specs/`）— diagonal / provisions-label / swiss-utility / museum-modern / warm-hospitality / editorial-print，可直接粘的 token 骨架
- **4 个 IA 原型**（`architectures/`）— portfolio / narrative / directory / conversion，每个都带「默认页面粒度 + 默认页内导航」（可被内容推翻）
- **2 条内容维度**（`architectures/pagination.json` + `scripts/pick_pages.py`）— 页面粒度（single / master-detail / multi-page）× 页内导航（none / anchor-jump / sticky-toc / section-rail），阈值与规则集中在注册表，脚本只读不硬编码
- **20 个参考池**（`referencePool`）— 含 game-lab 的 70 种可切换皮肤作为灵感来源
- 本地 spec 不够时按 `_specFallback` 三级降级，可外接 `npx typeui.sh pull <slug>` 的 67 种风格

## 13 类输入源预案

PDF / 图片 / docx / xlsx+csv / pptx / md+txt / 视频 / 音频 / 现有站 / 参考站 / 纯文字 / 混合 / 无输入 —— 每一类都有自己的提取路径、降级方案和坑（见 `source.md`）。

不能处理的情况会**明说**，不会假装：本机没有 OCR 时扫描件要用户提供文字；没有 ASR 时视频旁白要用户提供字幕。`scripts/check_env.py` 会先告知。

## 目录结构

```
website-style-router/
├── SKILL.md                  # 入口：34 条铁律索引 + 阶段门 + 文件地图（给 agent 读，正文 4.1k token）
├── CONCEPTS.md               # 概念介绍：为什么这样设计（给人读）
├── TUTORIAL.md               # 使用教学：怎么用、怎么改（给人读）
├── decide.md                 # 决策权 A/B/C/D + 提问预算
├── source.md                 # Phase -1：13 类输入源预案
├── intake.md                 # Phase 0/1：Grill 决策树 + 约束筛选
├── techstack.md              # Phase 1.5：技术栈选型（需求 → 栈）
├── host-align.md             # Phase 4：嵌入已有站的对齐规则
├── layouts.md                # 5 个布局原型 + 中轴 + 视觉签名 + 页内导航形态
├── typography.md             # 排版数值系统 + 字体搭配
├── checklist.md              # 交付前验收（含反同质化 + 页面粒度与可导航性）
├── references/               # SKILL.md 的按需加载层：rules.md（铁律全文）/ architecture.md / filemap.md
├── architectures/            # IA 两半：四选一原型 + pagination.json（页面粒度/页内导航阈值）+ granularity.md
├── styles/                   # index.json（40 锚点）+ families.md + signatures.json（含底色/变体轴）+ fonts.json（含族备用池）+ specs/
└── scripts/                  # check_env / pick_stack / pick_pages / extract_source / extract_pdf_assets / verify_assets / emit_tokens / audit_tokens / ledger / validate_skill
```

`examples/`、`testing/`、`docs/` 本机存在但**不随仓库发布** —— 这里只发 skill 本体，见 `.gitignore`。

`scripts/` 里三个**判断与反同质化专用**工具：

```bash
python scripts/pick_pages.py --entries 17 --depth deep --shareable --ia portfolio
                                                    # 页面粒度 + 页内导航推荐（事前，带理由与证伪条件）
python scripts/ledger.py --dir <工作区> --check     # 开新站前查重（事前）
python scripts/ledger.py --dir <工作区> --commit    # 落定后记账
python scripts/ledger.py --dir <工作区> --report    # 批次健康报告（人读）
python scripts/audit_tokens.py --site <站点目录>     # 产出层结构审计（F14–F20：粒度 / 导航 / 字段渲染 / 溯源 / 真源 / 宿主 / 技术栈形状）
python scripts/audit_tokens.py --batch <工作区>      # 产出层批次差异度（事后，无 FAIL 才算过）
```

## 示例

三次从头跑完的完整案例（咖啡店 / 自贡手撕兔 / 艺术家作品集 PDF）产出了**三种不同的页面粒度结论** —— 说明粒度是真被判断出来的，不是默认单页。三个案例的布局、字体、底色、签名也刻意各不相同，正是为了演示「风格驱动布局」与「批次不撞车」。**案例产物是本机开发资产，不随仓库发布。**

三个例子同时演示**三种不同的页面粒度判断结果**（这是"判断真的会发生"的实证，不是巧合）：

| 示例 | 页面粒度 | 页内导航 | 为什么 |
|---|---|---|---|
| `12sqm-coffee` | `single` | `none` | 3 个区块，内容浅，拆页和目录都是负优化 |
| `zigong-rabbit` | `single` | `anchor-jump` | 单页够用，但有规格/做法/FAQ 三个查阅型区块 |
| `vivian-peng-portfolio` | `master-detail` | `none` | 17 件作品，每件要能单独分享 → 索引 + `[slug]` 详情（构建 18 页） |

## 环境要求

- **Python 3.10+** — `pypdf`、`Pillow` 必需；`python-docx`、`openpyxl`、`python-pptx` 按输入格式按需
- **Node 18+** — 仅当 Phase 1.5 选定 astro / next / nuxt / eleventy / vite 时需要（选定 `plain-html` 则产物零依赖）
- **ffmpeg** — 可选，用于视频抽帧
- 外部工具（uipro / typeui / hue）均为可选，不是前置条件

改动本 skill 自身之后，跑两遍自检（均无第三方依赖，可直接接 CI）：

```bash
python scripts/validate_skill.py      # 规范与内部一致性（A–H 段，含 H3 中轴供给、H4 铁律索引与全文一致），ERROR 0 才算过
```

本 skill 的每条判据都按同一条规矩造：**一个永远返回 PASS 的判据等于没有判据**。
每条都要拿一处确定的违规去验证它真会报错，再拿合规输入验证它不会误报 ——
正向测试只能证明「不误报」，证明不了「能报错」。

两条真实教训（都写在 `CHANGELOG.md` 里）：

- **判据写松了等于没写**：F16 最初把 `forEach` 也算「渲染过」，而示例的灯箱脚本里就有 `images.forEach(...)`，于是「脚本里遍历过」掩盖了「模板只渲染第一张」，**负向用例一条都没抓到**。收紧为只认 `map`/`flatMap` 才生效。
- **正向防误报要专门找盲区**：F17/F19/F20 在三个示例上根本不触发（示例没有 `source-map.md`、也没声明 host/stack）。只跑示例会误以为判据没生效 → 为此造了 `GOLD_SITE`。

## 致谢

本 skill 站在这些 MIT 项目肩上，详见 [`THIRD-PARTY.md`](THIRD-PARTY.md)：ui-ux-pro-max-skill、awesome-design-skills (TypeUI)、hue、designer-skills (grill-me)、game-lab。方法学参考了 grill-me 的「一次一问 + 推荐答案」决策树结构。

## License

[MIT](LICENSE) © 2026 XanthanL
