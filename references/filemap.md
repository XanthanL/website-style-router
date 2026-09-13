# 完整文件地图（含每个文件的详细职责）

> 从 `SKILL.md` 移出（token 预算）。`SKILL.md` 里留的是导航够用的精简版。
> 路径以 skill 根目录为基准，本文件在 `references/` 下，故链接用 `../` 回到根。

---

## 本 skill 的文件地图

教学与说明（**给人读的，agent 不需要读**）：

- [`CONCEPTS.md`](../CONCEPTS.md) — **概念介绍**：三个真实失败模式、四层结构（散文/数据/计算/判据）、名词表（含「设计参数签名 vs 视觉签名」与 F 编号歧义的澄清）、核心洞察「单站自洽 ≠ 批次多样」、组合空间、三条元规则
- [`TUTORIAL.md`](../TUTORIAL.md) — **使用教学**：安装与环境探测、一次完整流程走查（逐门）、十脚本命令手册、八种自定义实战（改字体/调参数/加底色/加变体轴/加锚点/加技术栈/加判据/加内容维度）、排错手册、批次对比工作流、阅读路线图

阶段文档：

- [`decide.md`](../decide.md) — **决策权归属**（A 自主 / B 推断确认 / C 必须问 / D 绝不代做）+ 提问预算 + 必须停下来的 5 个触发条件
- [`source.md`](../source.md) — **Phase -1**：13 类输入源的处理预案 + 格式欺骗坑 + 溯源表 + 参考站采集
- [`intake.md`](../intake.md) — **Phase 0/1**：Grill 12 支决策树（交付形态 / 语言 / 参考站 / 中轴 / 区块尺寸 / 技术栈输入 / 页面粒度与页内导航）+ 约束筛选
- [`techstack.md`](../techstack.md) — **Phase 1.5（新）**：技术栈选型 —— 需求 8 判定项 → 7 个候选栈（排除 + 定序）→ `tech-stack.md` 输出契约 + 反模式
- [`host-align.md`](../host-align.md) — **Phase 4 嵌入必读**：宿主令牌采集 + 顶栏底栏同构 + 不破坏其他实体
- [`layouts.md`](../layouts.md) — 5 个布局原型 + **中轴策略** + **视觉签名（反同质化）** + **多图条目/图库硬规则**
- [`typography.md`](../typography.md) — **排版数值系统**：字阶公比族带、行高分层公式、字距规则、行长区间、中西混排、**字体搭配**
- [`design-qa.md`](../design-qa.md) — **审美数值判据**（F 致命 / I 重要 / S 建议 / N 命名）+ 规范 token 词汇表 + 四条人眼判据
- [`checklist.md`](../checklist.md) — 交付前验收（源与形态 / 回源 / 渲染完整性 / 语言 / 中轴 / 站点外壳 / 合规 / **反同质化**）

内容库：

- [`styles/index.json`](../styles/index.json) — **Tier 0**：40 锚点元数据 + 11 族 + `referencePool`(20) + `_specFallback` 降级规则
- [`styles/signatures.json`](../styles/signatures.json) — **Tier 2**：40 锚点的 15 个设计参数 + **7 档底色预设 `_surfacePresets`** + **4 条尺度变体轴 `_variantAxes`** + 11 族默认值 + 字段图例
- [`styles/fonts.json`](../styles/fonts.json) — **Tier 2**：40 锚点的**具名字体搭配**（display / body / mono / cjk）+ **11 族 × 3 对备用池 `_familyPools`** + 加载策略 + 反同质化规则（display 全库唯一）
- [`styles/families.md`](../styles/families.md) — **两级收敛**：11 族本质 / 何时整族命中 / 族内互斥 / 族间切换 / 证伪条件
- [`styles/specs/`](../styles/specs/) — 已落地的 6 个 spec — [diagonal](../styles/specs/diagonal.md) / [provisions-label](../styles/specs/provisions-label.md) / [swiss-utility](../styles/specs/swiss-utility.md) / [museum-modern](../styles/specs/museum-modern.md) / [warm-hospitality](../styles/specs/warm-hospitality.md) / [editorial-print](../styles/specs/editorial-print.md)
- [`architectures/`](../architectures/) — IA 两半：
  - **前半（区块组成）**四选一：[portfolio](../architectures/portfolio.md) / [narrative](../architectures/narrative.md) / [directory](../architectures/directory.md) / [conversion](../architectures/conversion.md)
  - **后半（页面粒度与页内导航）**：[granularity.md](../architectures/granularity.md)（判断框架）+ [pagination.json](../architectures/pagination.json)（阈值注册表，唯一真源）

工具与示例：

- [`scripts/check_env.py`](../scripts/check_env.py) — **首次运行先跑**：探测 Python 依赖 / ffmpeg / OCR / ASR，输出能力表与降级建议
- [`scripts/pick_stack.py`](../scripts/pick_stack.py) — **Phase 1.5**：由需求（页数 / 交互 / 维护者 / 数据源 / 宿主 / 语言 / 渲染 / 性能）**确定性推荐技术栈**（排除 + 定序 + 理由），零依赖
- [`scripts/pick_pages.py`](../scripts/pick_pages.py) — **Phase 1.7**：由内容判据（条目数 / 深度 / 可否独立分享 / 可否收录 / 并列主题数 / 区块数 / 查阅型区块数）**确定性推荐页面粒度与页内导航**（两轴结论 + 理由 + 被排除档位 + 证伪条件），阈值读 `architectures/pagination.json`，零依赖
- [`scripts/ledger.py`](../scripts/ledger.py) — **G1.6 批次查重**：`--check` 查本次选型是否与同批次已交付的站撞车（并给出具体替代项）、`--commit` 记账、`--report` 出批次多样性报告。**跨站去重的唯一机制**，零依赖。`--commit` 须带 `--font-display`（不记录 = 这一项没被校验，报告会判「未记录」不通过）
- [`scripts/extract_source.py`](../scripts/extract_source.py) — **13 类源统一提取** → `text.md` + `assets/` + `manifest.json` + `_WARNINGS.txt`
- [`scripts/extract_pdf_assets.py`](../scripts/extract_pdf_assets.py) — 只做 PDF → 页图/文本映射（需要 page 级绑定/去重时用）
- [`scripts/verify_assets.py`](../scripts/verify_assets.py) — 双向比对 + 真实格式校验 + 体积
- [`scripts/emit_tokens.py`](../scripts/emit_tokens.py) — **签名 + 字体搭配 → 完整 token 骨架**（字阶 / 行高 / 字距 / 栅格 / OKLCH 配色 / 具名字体栈 + WCAG 校验）；支持 `--surface` 底色档 / `--variant` 尺度变体轴 / `--pair` 族备用池字体，零依赖
- [`scripts/audit_tokens.py`](../scripts/audit_tokens.py) — **产出审计**（含 **F6 字体搭配**、**F10 视觉签名**）+ 签名一致性校验；**`--site <站点目录>` 执行 F14/F15 页面结构审计**（声明的页面粒度 / 页内导航 vs 实际页面数与锚点）；**`--batch <目录>` 执行 F11 批次差异度审计**（跨站去重）。零依赖，可接 CI
- [`scripts/validate_skill.py`](../scripts/validate_skill.py) — **改完本 skill 后跑一遍**：校验 frontmatter 是否符合 Agent Skills 规范、文档间引用是否自洽、仓库里有没有混进构建产物；G 段另校验底色维度 / 变体轴 / 族字体池 / 批次账本是否齐备

## 环境与外部依赖

外部依赖均为 MIT，按需调用，**不是前置条件**：

- `uipro`（nextlevelbuilder/ui-ux-pro-max-skill）— 行业推理规则 + 调色板，交叉验证 G3。按目标 agent 换 `--ai` 参数，如 `uipro init --ai codex` / `--ai cursor` / `--ai codebuddy`
- `npx typeui.sh pull <slug>`（bergside/awesome-design-skills）— 本地 spec 不够时的完整风格 spec（67 种）
- `dominikmartn/hue` — 已有品牌资产时的 token 反抽旁路
- **grill-me 方法学**（julianoczkowski/designer-skills）— 「一次一问 + 推荐答案 + 确认」的决策树结构
- **game-lab 风格库**（XanthanL/game-lab）— `data-style` ~70 种可切换皮肤，作为 `referencePool` 灵感来源；只换皮肤层，本 skill 要求布局层也跟着变

宿主能力按需使用，**不硬编码任何一个**：参考站采集用宿主提供的浏览器/截图能力（如 agent-browser、Playwright、Chrome DevTools MCP）或降级为「请用户截图 + 手工摘 CSS」。
