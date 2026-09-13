# 页面粒度与页内导航（IA 的第二半）

> IA 有两个问题，本 skill 以前只答了第一个：
> 1. 「**这一页由哪些区块组成**」→ `architectures/` 的四选一（portfolio / narrative / directory / conversion）
> 2. 「**内容该分成几页，页内怎么走**」→ 本文
>
> 只答第一个，就会得到「**所有站都是单个 index，条目再多也全塞进去；页面再长也只能一翻到底**」。
> 这两个判断都是**内容驱动**的，不是风格驱动的 —— 所以必须由判据决定，不能靠默认。

阈值与规则的唯一真源是 [`pagination.json`](pagination.json)；本文是它的解释与用法。
机器判据在 `scripts/audit_tokens.py` 的 `--site` 模式（**F14 / F15**）。

---

## 0 · 两轴总览

| 轴 | 取值 | 决定什么 | 判据码 |
|---|---|---|---|
| **页面粒度** | `single` / `master-detail` / `multi-page` / `n/a` | 内容分成几个页面 | F14 |
| **页内导航** | `none` / `anchor-jump` / `sticky-toc` / `section-rail` | 长页里怎么快速定位 | F15 |

**两轴都不许留空。** 判定结果写进 `content-profile.md` 的「页面粒度与页内导航」段（格式见 §4），
缺失即 F14 / F15 失败 —— 和「视觉签名」一样，**没有判据的必填项等于不必填**。

---

## 1 · 轴一：页面粒度

### 1.1 三问决策树（先问，再算）

```
问 1  有没有一个「集合」？（作品 / 商品 / 文章 / 房源 / 菜单条目…）
       没有 → single（一段叙事 / 一个转化动作，本来就是一页）
       有   → 继续

问 2  集合里的条目，用户会不会想「只要那一条」？
       （想把它发给别人 / 想从搜索直接落到它 / 想单独收藏）
       会   → master-detail
       不会 → 继续

问 3  除了这个集合，还有几个「各自成篇」的并列主题？
       （关于 / 服务 / 案例 / 博客 / 招聘 / 多语言版… 每个内容量都够独占一页）
       ≥2 个 → multi-page
       其余  → single
```

三问走完，答案唯一。`scripts/pick_pages.py` 把这三问变成了确定性输入。

### 1.2 判据表（机器可复核）

| 判据 | 取值 | 说明 |
|---|---|---|
| `entries` | 整数，无集合记 0 | 同一集合的条目数 |
| `depth` | `shallow` / `medium` / `deep` | 条目平均深度：≤1 段或 ≤1 图 / 2–3 段或 2–5 图 / ≥4 段或 ≥6 图 |
| `shareable` | 是 / 否 | 条目是否需要独立 URL（能被单独分享） |
| `indexable` | 是 / 否 | 条目是否需要被搜索引擎单独收录 |
| `themes` | 整数 | 除集合外**内容量足以独占一页**的并列主题数（只有一段话的「关于」不算） |
| `maintainer` | `nontech` / `tech` | 决定敢不敢用多页 |
| `static_gen` | 能 / 不能 | 能否用单一数据源静态生成多页 |

规则（`pagination.json` 的 `granularity.rules`，按序取首个命中）：

| 序 | 条件 | 结论 |
|---|---|---|
| G1 | `themes ≥ 2` | `multi-page` |
| G2 | `entries ≥ 4` 且 `depth ≥ medium` 且（`shareable` 或 `indexable`） | `master-detail` |
| G3 | `entries ≥ 12` 且 `depth ≥ medium` | `master-detail` |
| G4 | 其余 | `single` |

否决（`granularity.veto`）：

> `maintainer = nontech` **且** `static_gen = 不能` → **降级为 `single`**，
> 并在交付说明里写明代价（哪些内容因此被压成缩略）。

**关键区分：多页 ≠ 多份数据。** 用静态生成（`getStaticPaths` 之类）时，数据仍只有一份，
页面是生成的 —— 维护成本和单页几乎一样。`static_gen = 能` 是「多页不贵」的前提；
如果做不到，多页才真的贵。

### 1.3 各档的产物形状

| 档 | 页面清单 | 产物形状 |
|---|---|---|
| `single` | 1 页 | `src/pages/index.astro`（或 `plain-html` 的 `index.html`） |
| `master-detail` | 1 + N | `index` + `work/[slug]`（**一个模板生成 N 个页面**） |
| `multi-page` | ≥3 | `index` + `about` + `services` + `work/[slug]` … |
| `n/a` | 0 | `system-only`：只出 token，不搭站 |

### 1.4 反模式

- **假子页**：详情页只是把索引页的文字原样放大，没有新信息 → 拆了等于没拆，退回 `single`。
- **为拆而拆**：3 条内容、每条一句话，却拆成「列表页 + 3 个详情页」→ 得到 4 个空洞页面。
- **拆分丢数据源**：拆页时把数据抄成两份（索引页硬编码一份、详情页一份）→ 违反「一份真源」。
- **默认单页**：不判断、永远出 `index` → 这正是本文要修的失败模式。

---

## 2 · 轴二：页内导航

### 2.1 判据

| 判据 | 取值 | 说明 |
|---|---|---|
| `blocks` | 整数 | 首页的区块 / 章节数（`<section>` 或同级标题计数） |
| `lookup` | 整数 | 其中**查阅型区块**的个数：FAQ / 规格表 / 合规信息 / 索引 / 附录 |
| `linear` | 是 / 否 | 是否线性阅读（叙事长页是；可跳读的索引页否） |
| `screens` | 整数（可选） | 预估屏数；长图长表会把它推高 |

规则（`pagination.json` 的 `inPageNav.rules`，按序取首个命中）：

| 序 | 条件 | 结论 |
|---|---|---|
| N1 | `blocks ≤ 3` | `none` |
| N2 | `screens ≥ 10` 或 `blocks ≥ 12` | `section-rail` |
| N3 | `blocks ≥ 8` | `sticky-toc` |
| N4 | `blocks ≥ 4` 且（`lookup ≥ 1` 或 `linear`） | `anchor-jump` |
| N5 | 其余 | `none` |

否决（`inPageNav.veto`）：

> **转化页的区块是「说服链」的一环。** 给整页目录 = 请用户跳离说服链。
> 所以 `ia = conversion` 且没有查阅型区块时 → `none`；只有出现 FAQ / 规格 / 合规这类
> 区块时才升为 `anchor-jump`，**且锚点只指向那些区块**，不给整页目录。

### 2.2 四档分别长什么样

| 档 | 形态 | 适合 |
|---|---|---|
| `none` | 什么都不加 | 区块 ≤3；单屏单动作 |
| `anchor-jump` | 顶部一行「跳到：规格 / 常见问题 / 配料表」，或行内目录；**不跟随滚动** | 有查阅型区块的转化页；4–7 章节的叙事页 |
| `sticky-toc` | 桌面粘性侧栏 / 移动折叠目录，**跟随滚动 + 当前位置高亮** | ≥8 区块的信息页、长文档 |
| `section-rail` | 常驻左侧章节轨 + 进度指示 | ≥12 区块或 ≥10 屏的超长页 |

### 2.3 硬规则

1. **锚点必须可达**：每个 `href="#x"` 都要有对应的 `id="x"`。声明了导航却指向不存在的锚点 = 断链（F15 会抓）。
2. **至少 2 个跳转目标**：只有一个锚点不叫导航，叫「回到顶部」。
3. **导航本身也要过中轴与签名**：目录的位置（左轨 / 顶部 / 行内）由 `--axis` 与布局原型决定，
   不是随便贴一个浮动组件。见 `layouts.md` 的「页内导航（按布局原型）」。
4. **不遮挡**：粘性目录在移动端不得挤占首屏超过 1/3 高度，否则降一档。
5. **可访问**：目录是 `<nav aria-label="本页目录">`；跳转后焦点落在目标区块（`tabindex="-1"` + `focus()`）。

### 2.4 反模式

- **给短页加目录**：3 个区块的页面加侧边目录 → 纯噪音。
- **给转化页加整页目录**：请用户跳离说服链。
- **动态生成的假锚点**：`href="#work-{{slug}}"` 但页面上根本没有 `id="work-…"` —— 点了没反应。
- **目录与内容不同步**：加了目录但章节顺序变了没改 → 断链。

---

## 3 · 与四个 IA 原型的关系

`pagination.json` 的 `iaDefaults` 给每个 IA 一个**默认倾向**，但**默认不等于结论** ——
内容判据可以推翻它（这才是「判断」的意思）：

| IA | 默认粒度 | 默认页内导航 | 会被什么推翻 |
|---|---|---|---|
| `portfolio` | `master-detail` | `none` | 作品 <4 件或每件只有 1 张图 → 降为 `single`；作品 >20 件且带分类 → 升为 `multi-page` |
| `narrative` | `single` | `anchor-jump` | 章节 <4 → 降为 `none`；章节 ≥8 → 升为 `sticky-toc` |
| `directory` | `single` | `none` | 条目 ≥12 且每条有独立深度 → 升为 `master-detail` |
| `conversion` | `single` | `none` | 出现合规 / 规格 / FAQ 区块 → 升为 `anchor-jump` |

> **注意**：`iaDefaults` 只用于「判据不全、需要兜底」时。**能算就不要用默认值** ——
> 默认值会让同 IA 的站又长成一个样，这正是反同质化要防的。

---

## 4 · 怎么用

### 4.1 算一遍

```bash
# 咖啡店：3 条豆单、浅、不可分享、无并列主题
python scripts/pick_pages.py --entries 3 --depth shallow --ia directory --blocks 2

# 艺术家作品集：17 件作品、深度内容、要能被单独分享
python scripts/pick_pages.py --entries 17 --depth deep --shareable \
    --ia portfolio --blocks 3

# 食品转化页：6 个 SKU、有合规信息区块（查阅型）
python scripts/pick_pages.py --entries 6 --depth medium --indexable \
    --ia conversion --blocks 5 --lookup 1
```

输出含：两轴结论 + 逐条理由 + 被排除的档位 + 3 条可观测证伪条件。

### 4.2 写进产出

`content-profile.md` 必须含这一段（`audit_tokens.py --site` 按此解析）：

```markdown
## 页面粒度与页内导航

- 页面粒度：master-detail
- 页内导航：none
- 页面清单：index（作品网格 + 灯箱）/ work/[slug]（单件详情）
- 依据：17 件作品，每件 2–7 张图 + 1 段说明；作品需要能被单独分享与收录（entries=17, depth=deep, shareable=yes）
- 被排除：single（每条会被压成缩略，深度内容无处安放）、multi-page（除作品集合外无并列独立主题）
- 证伪条件：若详情页平均正文 <120 字或图 <2 张 → 退回 single
```

`intent-summary.md` 同步写两行摘要：

```markdown
- 页面粒度：master-detail（1 + N）
- 页内导航：none
```

### 4.3 交付前校验

```bash
python scripts/audit_tokens.py --site examples/vivian-peng-portfolio
```

它比对**声明**与**实际产物**：

| 码 | 查什么 | 不过的修法 |
|---|---|---|
| **F14** | 声明的粒度与实际页面文件数一致；未声明即失败 | `single` → 恰好 1 个页面；`master-detail` → ≥2；`multi-page` → ≥3 |
| **F15** | 声明的页内导航与实际锚点一致 | ≠`none` 时须有 ≥2 个**可达**锚点（`href="#x"` 有对应 `id="x"`）；`none` 时区块数不得 ≥5 |

---

## 5 · 交付前自检

- [ ] `content-profile.md` 里有「页面粒度与页内导航」段，两行都填了，且**不是默认值拍脑袋**
- [ ] 粒度结论能追到 `entries` / `depth` / `shareable` / `indexable` / `themes` 中的某几条
- [ ] 若拆了页：详情页有**索引页没有的信息**（不是原样放大）
- [ ] 若拆了页：数据仍只有**一份真源**（详情页从同一份数据生成）
- [ ] 若没拆页：写明**为什么不需要**（条目少 / 浅 / 不可分享），而不是「没想过」
- [ ] 页内导航档位能追到 `blocks` / `lookup` / `linear` / `screens`
- [ ] 每个锚点都能落到真实存在的 `id`
- [ ] 移动端目录不挤占首屏超过 1/3
- [ ] `python scripts/audit_tokens.py --site <站点目录>` F 级 0
