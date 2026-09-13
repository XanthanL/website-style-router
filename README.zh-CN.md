# Website Style Router

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Scripts: zero dependency](https://img.shields.io/badge/scripts-zero%20dependency-brightgreen.svg)](scripts/)
[![Version](https://img.shields.io/badge/version-0.9.2-informational.svg)](CHANGELOG.md)

[English](README.md) · **简体中文**

> 把你已有的内容 —— PDF、一堆照片、一张表格、一段视频、一个现有站点，或者就一句话 ——
> 变成一个**能跑起来的**网站，而且是适合这份内容的那种风格。

一个**可移植的 Agent Skill**（遵循 [Agent Skills Specification](https://agentskills.io/specification)）：一个文件夹，没有服务、没有 API key、自身不需要构建。

---

## 它能帮你什么

| 你多半遇过这种事 | 这里怎么做 |
|---|---|
| 十个需求做出来是十个一模一样的站 | 风格靠**排除**选出来（40 锚点 → 11 族 → 1 个），不是从菜单里挑。挑菜单必然向均值收敛，而均值就是人们说的「AI 味」 |
| 不管什么需求，都是同一套骨架（Astro + `src/pages/…`） | **技术栈由你的需求推出来** —— 页数、交互、维护者、数据源、宿主。纯 HTML 是平等的选项之一 |
| 永远只有一个 `index` 首页；长页只能一翻到底 | 分几页、怎么在页内跳转，是**按你的内容算出来的**。三个浅区块就一页；十七件都要能单独分享就给详情页 |
| 文案读着挺像，但你的素材里根本没有 | 每一行都必须**能溯源**（`p12 · "原句"`），指不回去的一律删掉 |

所以它解决的不是「长什么样」，而是**顺序问题**：先定源，再定交付形态，再砍约束空间，最后才谈风格。市面上几乎所有风格工具只做最后一步。

---

## 安装

```bash
npx skills add XanthanL/website-style-router
```

或者直接克隆，把整个文件夹丢进你 agent 的 skills 目录。路径全部相对于 skill 根目录，没有宿主专有依赖：

```bash
git clone https://github.com/XanthanL/website-style-router.git
```

| Agent | 放置位置 |
|---|---|
| Claude Code | `~/.claude/skills/website-style-router/` 或项目内 `.claude/skills/website-style-router/` |
| Codex | `.codex/skills/website-style-router/` |
| Cursor | `.cursor/skills/website-style-router/` |
| WorkBuddy / CodeBuddy | `~/.workbuddy/skills/website-style-router/` |
| 其他 | 任何「目录内含 `SKILL.md`」的约定都能直接用 |

装完先跑一次环境探测，它会在这之前就告诉你本机能提取什么、不能提取什么：

```bash
python scripts/check_env.py
```

## 怎么用

直接描述你要做的东西，把材料给它：

```
用 website-style-router，把这个 PDF 做成一个适合它的网站
（附：原始素材）
```

就这样。流程会自己走完，**只在「落定」那一步停下来找你确认一次** —— 技术栈 + 风格族 + 锚点 + 布局 + 字体。这之前的一切都从你的内容推出来，这之后的一切都是执行。

产出物固定在：`source-map.md`、`references.md`、`tech-stack.md`、`intent-summary.md`、`content-profile.md`、`design-system/MASTER.md`（嵌进已有站时另有 `HOST.md`），以及一个能通过构建的站点。

---

## 详细文档

README 到这里就停了。更深的内容都在这些文档里：

| 文档 | 回答什么 |
|---|---|
| [`CONCEPTS.md`](CONCEPTS.md) | **为什么这样设计**：真实失败模式、四层结构、名词表、四条元规则 |
| [`TUTORIAL.md`](TUTORIAL.md) | **怎么用、怎么改**：逐阶段走查、完整命令手册、八种自定义实战、排错手册、批次工作流，以及仓库里到底装了些什么 |
| [`SKILL.md`](SKILL.md) | 34 条铁律与阶段门 —— agent 实际读的那份 |
| [`references/filemap.md`](references/filemap.md) | 完整文件地图，每个文件的职责 |

> 深度文档目前是**中文优先**，而 JSON 注册表和代码本身与语言无关。欢迎翻译 ——
> [`CONCEPTS.md`](CONCEPTS.md) §10 的术语速查表可以用来对齐用词，保证译文和代码一致。

## 环境要求

- **Python 3.10+** — `pypdf`、`Pillow` 必需；`python-docx`、`openpyxl`、`python-pptx` 按输入格式按需
- **Node 18+** — 仅当选定 astro / next / nuxt / eleventy / vite 时需要（选定 `plain-html` 则产物零依赖）
- **ffmpeg** — 可选，用于视频抽帧
- 外部工具（uipro / typeui / hue）均为可选，不是前置条件

改动本 skill 自身之后跑一次 `python scripts/validate_skill.py`，`ERROR 0` 才算过；无第三方依赖，可直接接 CI。

## 致谢

本 skill 站在这些 MIT 项目肩上，详见 [`THIRD-PARTY.md`](THIRD-PARTY.md)：ui-ux-pro-max-skill、awesome-design-skills (TypeUI)、hue、designer-skills (grill-me)、game-lab。方法学参考了 grill-me 的「一次一问 + 推荐答案」决策树结构。

## License

[MIT](LICENSE) © 2026 XanthanL
