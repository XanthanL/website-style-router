# 实现说明：分层对照表

> 从 `SKILL.md` 移出（token 预算）。一句话概括：**可枚举的都进 JSON 注册表，确定性的都进 Python 脚本，散文只承载推理。**
> 概念版解释见 [`../CONCEPTS.md`](../CONCEPTS.md) 的「四层结构」。

---

## 实现说明（分层，不是纯 MD）

| 层 | 形式 | 为什么 |
|---|---|---|
| 推理/编排 | MD（SKILL / intake / source / decide / host-align / layouts / checklist / design-qa） | 决策逻辑用散文，agent 推理最稳 |
| **技术栈选型** | MD（`techstack.md`）+ Python（`scripts/pick_stack.py`） | 需求 → 栈的判断必须可复核。**默认继承框架 = 「形状同质化」的成因** |
| **页面粒度与页内导航** | MD（`architectures/granularity.md`）+ JSON（`architectures/pagination.json`）+ Python（`scripts/pick_pages.py`） | 「内容该分几页」与「长页怎么走」是**内容判断，不是风格判断**。写成散文就会退化成「永远单页、永远不加导航」；阈值进注册表，判断进脚本，声明与产物的一致性进判据（F14/F15） |
| 风格注册表 | JSON（`styles/index.json`） | 结构化、按需查、不整体入上下文。纯散文库会诱导"挑一个平均物" |
| 风格族谱与 spec | MD（`styles/families.md`、`styles/specs/*`） | 族谱做收敛；spec 只在命中后读 1 个 |
| **设计参数签名** | JSON（`styles/signatures.json`） | 40 个锚点的可计算设计参数。**风格判断的数值化** —— 让无 spec 的锚点也有确定依据 |
| **字体搭配注册表** | JSON（`styles/fonts.json`） | 40 个锚点的具名字体搭配（**display 全库唯一**）+ **11 族 × 3 对备用池**（同锚点第二次使用有字可换）。字体是辨识度最高的一维，不能塌缩成 serif/sans/mono 三选一 |
| **底色与尺度维度** | JSON（`styles/signatures.json` 的 `_surfacePresets` / `_variantAxes`） | 7 档底色 × 4 条尺度变体轴。**没有这两个维度，深色站与有色底站在架构上做不出来** —— v0.7 把底色明度写死在代码里，5 个站全出 `#FFFFFF` |
| **批次风格账本** | Python（`scripts/ledger.py`）+ JSON（`.style-ledger.json`，项目侧） | **跨站去重是单站排除法做不到的** —— 排除法只看当前这一单，需求画像相似时必然同向收敛。账本补上「上一次用的是什么」 |
| **排版数值系统** | MD（`typography.md`） | 字阶比 / 行高 / 行长 / 字距的族带与公式。**美感判断里能量化的部分** |
| 提取与校验 | Python（`scripts/*.py`） | 确定性工作交给代码，别用眼睛数图 |
| **token 生成** | Python（`scripts/emit_tokens.py`） | 签名 + 字体搭配 → 完整 token（含 OKLCH 推导 + WCAG 对比度求解）。禁手编 |
| **审美审计** | Python（`scripts/audit_tokens.py`） | 数值判据 + **字体搭配判据**（F6）+ **页面结构判据**（F14/F15，`--site`）+ **批次差异度**（F11，`--batch`）可复跑；签名一致性比对 |
| 输出 | 代码（按 `tech-stack.md`：纯 HTML+CSS / Astro / Next / 宿主组件） | MD 只是 spec |
