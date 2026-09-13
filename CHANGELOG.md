# CHANGELOG

遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [SemVer](https://semver.org/lang/zh-CN/)。

## [0.9.2] — 2026-09-13

处理质量审计（`质量审计`）查出的两处 **token 超预算**，约束是**尽量不失原有功能**。

### 诊断

| 项 | v0.9.1 实测 | 建议值 | 性质 |
|---|---|---|---|
| SKILL.md 正文 | **9,195 token**（215 行） | <5,000 | 超 1.8 倍；但**行数远未超**（限 500） |
| `description` | **668 字符 ≈ 490 token** | ~100 | 超约 5 倍 |

两个数字打架的根因：**「<500 行」是按英文散文写的，中文 token 密度约 1.8 倍** ——
中文 skill 按行数永远合规、按 token 可能超标一倍。**中文 skill 必须测 token，不能只测行数。**

### Changed

- **正文 9,195 → 4,136 token（-55%），进入建议区间。** 三段内容搬出 `SKILL.md`，
  原地只留索引 / 精简版，全文进 `references/` 按需读 —— **改的是加载时机，不是信息量**：

  | 搬走的内容 | 去向 | 正文 token |
  |---|---|---|
  | 铁律全文 34 条 | 新建 `references/rules.md`（留 34 条索引，52 行） | 3,098 → **609** |
  | 实现说明的分层对照表 | 新建 `references/architecture.md`（留一句话结论） | 853 → **81** |
  | 完整文件地图 | 新建 `references/filemap.md`（留导航够用的最短版） | 2,338 → **584** |

  敢搬铁律，是因为它的使用场景是「G2 落定前」「G5 验收前」两次自检，
  激活时只需要知道**有哪 34 条**；理由、做法、踩过的坑与对应判据按需回查。

- **`description` 668 → 613 字符（≈490 → 450 token），零触发词丢失。**
  做法是合并「覆盖面」与「关键词」两段的重复项 + 精简连接语，**没有删任何触发词**；
  另把「页面粒度与页内导航」拆成两个独立词（顿号替「与」，长度不变）。

  **压缩前先做了丢失词检测**：新旧两段各自分词后取集合差，断言差集 ⊆ 刻意丢弃集合
  （4 项，均为同义改写或换名），实测差集为**空**。这一步不能省 ——
  「压完就算完」无法区分「精简了」和「悄悄删了长尾触发」。

  **残余差距（未达标，有意保留，已在审计报告登记为已评估风险）**：613 字符 ≈ 450 token
  仍远超 ~100 token 建议值，但继续往下压只有一条路 —— **删触发词**，
  而那正是本 skill 唯一的功能性元数据。反向证据：SkillRouter 基准显示
  **仅用 name/description 路由，准确率比用全文低 31–44%**。

### Added

- **`validate_skill.py` H4 铁律「索引 ↔ `references/rules.md` 全文」一致性** ——
  校验两边编号都从 1 连续、编号集合相同、同编号是同一条、标题条数一致。

  这是本次拆分**新引入的风险**：铁律变成两个文件后可能各改一处 —— 索引少一条而全文还在，
  agent 按索引自检就会**静默漏检**，且没有任何脚本会报错。
  这恰恰是 v0.9.1 用来识别欠账的判据形态：**「违反它的最小产物长什么样，有哪个脚本会报错」**
  答不出脚本名。所以拆完必须立刻补这条判据。

  编号是外部引用锚点（`测试用例集`、`CONCEPTS.md`、脚本报错文案都按号引用），
  所以只看「条数相同」不够 —— 跳号或错位会让引用指向另一条。

- **`判据自测脚本` 52 → 57 条**：H4 的 4 条负向（索引少一条 / 全文少一条 /
  同编号两边不是同一条 / `rules.md` 整份消失）+ 1 条正向防误报
  `VALIDATE-base-pass`（未变异副本必须 `ERROR 0` 且不出现 `[H4]`）。

### Fixed

- 文档同步：审计报告的实测数字、`validate_skill.py` 头部说明、三份文档的判据自测条数
  （52 → 57）、两份 README 的版本号与用例数。

### Changed（发布范围）

仓库只发 skill 本体 —— 研究过程资料、测试基础设施、实跑样例产物**不入库**。
`SKILL.md` 对它们**零引用**，排除不影响 skill 运行。

配套改了两处，否则干净克隆会崩：

- **`validate_skill.py` C2 的两处缺口**：
  - `tokens.css` 补进 `ARTIFACTS` 白名单 —— 它是 `emit_tokens.py` 写进**产出站点**的文件，
    仓库里本就不该有。**之前一直没被报，只是因为 示例产物 里恰好有同名文件**
    （白名单的潜在缺口靠样例偶然掩盖，一排除就暴露成 13 条误报）。
  - 新增 `LOCAL_ONLY_DIRS` / `LOCAL_ONLY_BASENAMES`：指向这三个目录的引用降为 **info**。
    干净克隆里它们必然解析不到，那是预期状态不是断链。**已验证未削弱 C2** ——
    在发布文件里引用一个真正不存在的模块名（不在那三个目录里）仍会 WARN。
- **两份 README + `CONCEPTS.md` + `TUTORIAL.md`**：删掉对不存在脚本的指令
  （`python 判据自测脚本`）、结构树里的三个目录，
  并加一行说明这些路径是本机资产。判据自测的方法论保留，只是不再指向不发布的文件。
- **决策树支数漂移**：`intake.md` 实际是 **B0–B11 共 12 支**（v0.9 加了 B11 页面粒度与页内导航），
  但 `intake.md` 标题、`references/rules.md`、`references/filemap.md`、`SKILL.md` 的 G0 门、
  `TUTORIAL.md` 五处仍写「10 支 / B0–B10」。已全部改正。**此类「真源在文件里、数字在散文里」
  的项目前没有判据把守** —— 是下一版值得补 H5 的候选。

### 已知遗留

- `description` 仍超预算（见上，**有意保留**）。
- 二级引用 6 处、缺 with/without-skill 配对基线、未跨 Haiku/Sonnet/Opus 测试 —— 详见审计报告 §4。

## [0.9.1] — 2026-09-12

用 skill 自己的信条反过来审它自己，修补两处「**说了但没判**」与一处「**判错了方向**」。

### 诊断

全量审计 34 条铁律，只有 **14 条（41%）有机器判据**。其余 20 条里 15 条是价值观/过程性要求，
本就难以机器化；但**有 5 条是本可机器化却没做的**，这是真缺口：

| 铁律 | 内容 | 此前状态 |
|---|---|---|
| 19 | 字段定义了就必须渲染 | 铁律正文里自己写着「引用校验还会 PASS」——**承认了漏洞却一直没补** |
| 18 | 每条内容能指回源（`p12 · "原句"`） | `source-map.md` 只在 `validate_skill.py` 的 `ARTIFACTS` 白名单里，不是真判据 |
| 26 | 一份真源（`MASTER.md` 与 `tokens.css` 值一致） | 记忆里明确要求两者一致，但 **0 个脚本检查** |
| 14 | 嵌入服从宿主 | `embedded` 是三种交付形态之一，**零机检** |
| 29 | 产物形状反映技术栈 | 选了 `plain-html` 却产出 `src/pages/`，说明 Phase 1.5 白做了 |

第二处是**中轴的阈值判错了方向**：`MIN_AXIS_KINDS = 3`，而中轴总共就 3 档 ——
要求「3 种全部出现」等于覆盖率 **100%**，那是**配额**不是多样性。
（`MIN_SURFACE_KINDS = 3` 是在 7 档底色里要求 3 种 = 43%，那才是多样性；
同一个「3」在两个维度上含义完全不同。）后果：每个批次都被强制包含一个 `split` 站，
而 `split` 只有 3 个锚点、还全挤在 `split-narrative` 一个布局原型里 ——
**中轴把布局与族的自由度一起锁死了**。

### Added

- **`audit_tokens.py` F16–F20（产出层，随 `--site` 启用）**：
  - **F16 字段渲染完整性**（铁律 19）：`src/data/*.json` 的数组字段若被代码只取 `[0]`，
    必须有 `.map()` / `.flatMap()` 渲染其余项。**只认 `map`/`flatMap`，不认 `forEach`** ——
    实测 `images.forEach(...)` 出现在灯箱脚本里，掩盖了模板只渲染第一张图，
    这正是「字段定义了却没渲染」的典型形态。
  - **F17 内容可溯源**（铁律 18）：`source-map.md` 表格行 ≥50% 带溯源标记。
    **文件缺失只报 I 级** —— 不是每个项目都要交溯源表，但不能「有表却全是编的」。
  - **F18 一份真源**（铁律 26）：`MASTER.md` 与 `tokens.css` 共有 token 值一致，
    比较前归一化（去空白、转小写）—— 字体栈逗号后的空格差异不能判漂移。
  - **F19 嵌入服从宿主**（铁律 14）：声明 `embedded` 须有 `HOST.md` 且共有 token 一致。
  - **F20 产物形状反映技术栈**（铁律 29）：`plain-html` 不得出现 `astro.config.*` / `src/pages/`。
- **`validate_skill.py` H3 中轴档位供给** —— 每档 `axis` 须 ≥3 个锚点、跨 ≥2 个布局原型、
  跨 ≥3 个族。抓的是**维度没正交**：某档 100% 绑定单一布局时，选它就等于选布局。
- **`判据自测脚本` 40 → 52 条** —— 新增 5 条 F16–F20 负向、
  2 条 H3 负向、2 条中轴阈值用例（`LEDGER-axis-share` 负向 / `LEDGER-axis-two-kinds` 正向）、
  1 条 `--batch` 中轴占比负向，**`PIPE-all-anchors`**（40 个锚点逐个 `emit_tokens` + 单站审计
  必须全 F 级 0 —— 把「被验证过的锚点」从 3/40 拉到 **40/40**），以及 **`SITE-gold-pass`**
  （处处合规的最小站点，补 F17/F19/F20 的**正向防误报** —— 三个示例都没有 `source-map.md`、
  也没声明 host/stack，覆盖不到这三条的正向路径）。

### Changed

- **中轴阈值从「配额」改回「不塌缩」**：`ledger.py` 与 `audit_tokens.py --batch` 同步改为
  **中轴 ≥2 种 且 单档占比 ≤60%**，报告各新增一行「中轴最大占比」。
  仍抓得住「5 站全 left-rail」，但不再强制每批含一个 `split` 站。
  **已做反向验证**：把阈值改回 3，`LEDGER-axis-two-kinds`（3:2 且不含 split）立刻 FAIL，
  失败原因正是「中轴种类」—— 证明旧阈值确实在强制 split。
- **中轴供给扩容**：`swiss-editorial`（瑞士网格分栏）与 `luxury-retail`（单件大图 + 极简信息）
  的 `axis` 改为 `split`。分布从 `left-rail 20 / center-axis 17 / split 3（1 布局 2 族）`
  变为 `left-rail 19 / center-axis 16 / split 5（2 布局 4 族）`。
  注意方向：`luxury-retail` 是 `catalog-grid` 原型却用 `split`，
  与既有的「`editorial-hero` 也可能用 `left-rail`」构成**双向反例** —— 两个方向都不能硬映射。
- `SKILL.md` frontmatter `version` → 0.9.1；`design-qa.md` F 级表补 F16–F20 并修正 F11 的中轴描述；
  `layouts.md` 中轴章节补供给分布、双向反例与「判据是不塌缩、不是凑齐档位」。
- **README 改为英文默认**（开源发布）：原中文版迁到 `README.zh-CN.md`，两份顶部互相链接；
  英文版补了徽章、失败模式对照表、「盒子里有什么」清单、命令速查、仓库结构表与文档索引，
  并明确说明**深度文档目前中文优先**（注册表与代码本身与语言无关）。

### Fixed

- 5 条铁律（14/18/19/26/29）从「写在文档里的必填」变成**有机器判据的必填** ——
  同一个失效方式 v0.7 已经发生过一次（视觉签名），这次一次补 5 条。
- 中轴不再成为批次多样性的必经瓶颈。

### Notes

- **F16 的白名单收紧是一次真实教训**：最初把 `forEach` 也算「渲染过」，
  结果负向用例退出码 0、一条都没抓到 —— 因为示例的灯箱脚本里就有 `images.forEach(...)`。
  `forEach` 通常只做副作用，页面上一个元素都不会多。**判据写松了等于没写。**
- **正向防误报不能省**：F17/F19/F20 在三个示例上全部不触发（示例没有 `source-map.md`、
  也没声明 host/stack），如果只跑示例，会误以为判据没生效。
  `GOLD_SITE` 就是为这个盲区造的。
- **「示例覆盖 3/40」的正确补法不是再堆示例站点**。示例是「输出形状的参考」，
  再建一个要真内容、要维护构建产物，成本极高；而「每个锚点都能产出合格 token」
  是**可以机器全量验证**的事 —— `PIPE-all-anchors` 逐个 emit + 审计 40 个锚点（约 20s），
  一次把验证覆盖从 7.5% 拉到 100%。**别用加内容的方式解决可计算的问题。**
- 组合空间不变：`40 锚点 × 4 变体 × 7 底色 × 4 字体对 × 3 粒度档 × 4 导航档`。

## [0.9.0] — 2026-09-12

补上 **IA 缺失的另一半**：0.8.0 之前，这个 skill 只回答「**这一页由哪些区块组成**」
（portfolio / narrative / directory / conversion 四选一），从不回答「**这些内容该分成几页**」，
也没有规定「**长页里怎么快速跳到关键部位**」。结果是每个站都退化成**单个 `index` 首页**，
内容一多就只能一翻到底 —— 设计达标了，**浏览功能性**没有。

### 诊断

用户反馈的两点，都能指到具体缺口的：

- 「每个网页没有其子网页介绍详细内容，而只有单个 index 首页」→
  **页面粒度（page granularity）这个维度在 skill 里根本不存在**，
  所以 `emit_tokens.py` 产出的永远是单页，`checklist.md` 里也没有任何一项会问「要不要拆页」。
- 「网页内部该有能跳转到某个关键部位的按键」→ **页内导航（in-page navigation）也没有维度**，
  `layouts.md` 只管区块怎么排，不管排完之后人怎么在里面移动。

但用户同时给了**最关键的一句约束**：

> 「上面这些改动不是所有内容方向的网页都需要，或许要增加我们自己的判断。」

这句话直接否定了最省事的做法（无脑加：所有站都拆页 + 所有站都加目录）。
一个 3 区块的咖啡店页加目录、一个 4 件作品的作品集硬拆详情页，都是**负优化**。
所以本次新增的必须是**判断能力**，而不是**默认行为**。

沿用 0.8.0 的教训 —— 「**没有判据的必填等于不必填**」（v0.7 的「视觉签名」就是活例子）——
新维度按 skill 自身的四层结构落地，每一层都有对应载体：

| 层 | 载体 |
|---|---|
| 散文（给人读的判断框架） | `architectures/granularity.md` |
| 数据（阈值唯一真源） | `architectures/pagination.json` |
| 计算（确定性推荐） | `scripts/pick_pages.py` |
| 判据（产出层 + 仓库层 + 负向测试） | `audit_tokens.py --site` 的 F14/F15、`validate_skill.py` 的 H1/H2、`判据自测脚本` |

### Added

- **`architectures/pagination.json`（阈值注册表，唯一真源）** —— 四段：
  `granularity`（档位 `single` / `master-detail` / `multi-page` / `n-a`，规则 G1–G4，否决 V1，阈值）、
  `inPageNav`（档位 `none` / `anchor-jump` / `sticky-toc` / `section-rail`，规则 N1–N5，否决 V1–V2，阈值）、
  `iaDefaults`（四个 IA 各自的默认粒度与默认导航）、`falsify`（各档位的证伪条件）。
  脚本一律读它，**不硬编码阈值** —— 改判断标准只需改这一个 JSON。
- **`architectures/granularity.md`（判断框架，给人读）** —— 两轴总览、三问决策树、
  判据表（每条判据配「为什么」与「反例」）、各档位的**产物形状**（single 一个 `index`；
  master-detail 索引 + `[slug]` 详情；multi-page 按主题分目录）、
  四档导航形态的适用条件、与四个 IA 的关系表（谁被谁推翻）、
  `pick_pages.py` 用法、`content-profile.md` 的声明段格式、交付前自检清单。
- **`scripts/pick_pages.py`（确定性推荐，零依赖）** —— 对标 `pick_stack.py`：
  读注册表 → 输出**档位 + 逐条理由 + 被排除的档位及原因 + 证伪条件**。
  CLI：`--entries --depth --shareable --indexable --themes --maintainer --static-gen/--no-static-gen
  --ia --blocks --lookup --linear --screens --host --json`。
  实测三场景：咖啡店 → `single + none`；作品集 → `master-detail + none`；食品转化页 → `single + anchor-jump`。
- **`audit_tokens.py` F14/F15（产出层判据）** —— 新增 `--site <站点目录>` 模式：
  - **F14 页面粒度一致性**：读 `content-profile.md` 的粒度声明，数实际页面文件
    （`single` 必须恰好 1 页、`master-detail` ≥2、`multi-page` ≥3、`n-a` = 0）；
    **声明缺失即失败**（不许「没说」）。
  - **F15 页内导航可达性**：声明 ≠ `none` 时须有 ≥2 个**可达**锚点；
    声明 `none` 而区块数 ≥5 → 失败（这就是「一翻到底」）；另查**全站锚点断链**。
  - 编号从 **F14** 起（跳过 F12/F13）—— `validate_skill.py` 有独立的 F1–F13 命名空间，
    重号会让引用产生歧义。
- **`validate_skill.py` H 段（仓库层判据）** ——
  **H1**：四个 IA 文档里写的「默认粒度 / 默认页内导航」必须与 `pagination.json` 的 `iaDefaults` 一致
  （抓**文档漂移** —— 改注册表忘了改文档，或反之），并校验注册表含 `falsify` 段；
  **H2**：示例产物 下每个示例跑一遍 `audit_tokens.py --site`，必须 F 级 0。
- **`SKILL.md` 新增铁律 33/34** —— 33「页面粒度是被判出来的，不是被默认成单页的」、
  34「页内导航的档位由内容决定，形态由布局决定」。
- **新阶段门 G1.7「页面粒度与页内导航」** —— 位于 G1.6（批次查重）之后、G2（落定）之前；
  `content-profile.md` 与 `intent-summary.md` 的输出契约各补「页面粒度」「页内导航」两行。
  工作量分级同步更新：G1.7 判出 `master-detail` / `multi-page` 时**必须把 L1 升为 L2**。
- **`intake.md` 新增 B11（Q28–Q30）** —— 明确写下「**不要问『你要单页还是多页』**」：
  用户不知道自己要几页，问了只会得到随口一个答案；正确做法是问内容规模（条目数、深度、是否要分享单条），
  再由 `pick_pages.py` 算。
- **`layouts.md` 新增「页内导航（按布局原型）」** —— 5 个原型的导航形态对照表 + 6 条规则
  （语义 id、目录自身是设计对象、移动端降一档、跳转后焦点、文案一致、静态锚点用普通引号）。
- **`checklist.md` 新增「页面粒度与可导航性（G1.7）」12 条**；
  **`design-qa.md`** F 级表补 F14/F15 行，「四条人眼判据」扩为「六条」
  （新增「详情页有没有索引页看不到的信息」「页内跳转落点准不准」）。
- **`判据自测脚本` 扩到 39 条** —— 新增 10 个变异体
  （`m_f9_missing_pick_pages`、`m_h1_missing_granularity`、`m_h1_drift`、`m_h1_registry_section`、
  `m_site_no_granularity`、`m_site_single_but_two_pages`、`m_site_master_detail_but_one_page`、
  `m_site_no_nav`、`m_site_nav_without_anchor`、`m_site_long_page_none`、`m_site_broken_anchor`）
  与一组**正向防误报**用例（三个示例必须全过）。

### Changed

- **`示例站点/` 改造为 `master-detail` 样板** ——
  新增 `src/layouts/SiteLayout.astro`（抽出顶栏 / 抽屉 / 底栏 / 语言切换，详情页复用）与
  `src/pages/work/[slug].astro`（`getStaticPaths` 一个模板生成 **17 个详情页**）；
  `index.astro` 的卡片主链接从 `#work-{slug}` 改为 `/work/{slug}`，
  灯箱从「唯一详情入口」降为「快速预览」按钮（另留 `打开详情页 ↗` 永久链接）。
  构建实测 **18 页**（1 索引 + 17 详情）。
- **`示例站点/` 改造为 `single + anchor-jump` 样板** ——
  `index.astro` 新增行内目录（4 个锚点）、补 `id`、`scroll-margin-top`，
  并用 `focus({preventScroll:true})` 把焦点移到落点（键盘/读屏可用）。
- **`示例站点/` 保持 `single + none`** —— 刻意**不**加目录、**不**拆页，
  作为「判断的另一半」的对照：**不拆也是判断结果，不是遗漏**。
- `SKILL.md` frontmatter `version` → 0.9.0；`description` 补「页面粒度与页内导航」及
  `page-granularity` / `in-page-navigation` 关键词；阅读顺序表补阶段 1.7。
- `README.md` / `CHANGELOG.md` / `CONCEPTS.md` / `TUTORIAL.md` 同步。

### Fixed

- 所有站默认产出单个 `index` 首页（根因：页面粒度维度不存在，`emit_tokens.py` 无从产出多页）。
- 长页只能一翻到底（根因：`layouts.md` 只管区块排列，不管页内移动）。
- 「页面粒度」若只写成散文必填 → 必然退化为「永远单页」（用 F14 把它变成机器判据）。

### Notes

- **两个新维度都是内容驱动的，不是风格驱动的** —— 所以判断必须发生在 G1.7（落定内容之后），
  而不是风格选型阶段。风格选型是「排除法」，页面粒度是「算出来的」，两者机制不同：
  页面粒度**不进约束筛选表**。
- **多页 ≠ 多份数据**：静态生成下 `getStaticPaths` 从一个数据源渲染 N 页，
  数据仍是一份真源，`audit_tokens.py` 的 F 级数值审计不受影响。
- 组合空间：`40 锚点 × 4 变体 × 7 底色 × 4 字体对 × 3 粒度档 × 4 导航档`。

## [0.8.0] — 2026-09-12

针对 0.7.0 之后暴露的**更深一层失败**：单站看每个都合格，五个摆一起仍然是一个样。

### 诊断（在真实产出上量出来的，不是猜的）

对当时已完成的一批站（v0.7 之前做的 7 个样例站，该目录现已移出本仓库）做了令牌级比对，结果：

- `--bg` **5/5 全部 `#FFFFFF`**；`--font-display` 3/5 相同、`--fs-base` 3/5 相同、`--radius` 3/5 相同、`--axis` 3/5 相同；
- 40 个锚点只用到 3 个（**7.5%**）；两个不同锚点的站产出的 token **一字不差**；
- 视觉签名 5/5 缺失 —— 因为它在 `layouts.md` 里是"必填"，但**没有任何机器判据**。

根因三条，都可指到行：

1. `scripts/emit_tokens.py` 的底色写死 `oklch(0.985, tint_c, tint)` —— 不管选哪个锚点都出近白底；
2. `styles/signatures.json` 的结构是「**一个锚点 = 一套常量**」，不是参数空间 —— 同锚点第二次使用必然逐值相同；
3. `styles/fonts.json` 每个锚点只有**一对**字体，且 R3 要求 display 全库唯一 —— 同锚点复用即"无字可用"。

**核心教训**：0.7.0 的所有判据都是「**单站内自洽**」，没有一条是「**跨站差异**」。
而排除法在批量场景下会**同向收敛** —— 需求画像相似时，它砍掉的是同一批选项。
只有单站判据时，每个站单看都合格，摆一起就塌。

### Added

- **`CONCEPTS.md`（概念介绍，给人读）** —— 回答「为什么这样设计」：三个真实失败模式及其根因、
  四层结构（散文 / 数据 / 计算 / 判据）、完整名词表、核心洞察「单站自洽 ≠ 批次多样」、
  组合空间推导、判据体系、三条元规则、与同类工具的差别。
  其中两处**歧义澄清**是新增的：①「设计参数签名」（`signatures.json` 的 15 个数值）
  与「视觉签名」（`layouts.md` 的 ≥3 条结构手法）是两个无关概念；
  ② `audit_tokens.py` 与 `validate_skill.py` 各自维护**独立的 F 编号**，F1–F6 重号，
  引用时必须带脚本名。
- **`TUTORIAL.md`（使用教学，给人读）** —— 回答「怎么用、怎么改」：安装与环境探测（含真实输出）、
  一次完整流程走查（以 T13-A 修鞋摊为例逐门走）、九个脚本的命令手册、
  **七种自定义实战**（改字体 / 调锚点参数 / 加底色档 / 加变体轴 / 加锚点 / 加技术栈 / 加判据+负向测试）、
  排错手册（含 argparse 与 MSYS 路径坑）、批次对比工作流、阅读路线图、一页速查表。
- **底色维度 `_surfacePresets`（7 档）** —— `white` / `paper` / `tint` / `stone` / `slate` / `ink` / `deep`，
  每档含 `L` / `C` / `polarity`（light\|dark）；40 个锚点全部补 `surface` 字段（分布 white 12 / paper 9 /
  tint 7 / stone 4 / deep 3 / ink 3 / slate 2）。`emit_tokens.py` 据此算底色，深底自动把 accent 压暗以保对比度。
- **尺度变体轴 `_variantAxes`（4 条）** —— `a` 原值 / `b` 收紧 / `c` 放松 / `d` 张扬，对字阶公比 `r`、
  基准字号 `base`、间距单位 `unit`、圆角 `rad` 做**带 clamp 的偏移**（r∈[1.15,1.62]、base∈[13,20]、
  unit∈[2,24]、rad∈[0,24]），另带 `mot` 动效倾向。同锚点第二次使用必须换轴。
- **族级字体备用池 `_familyPools`** —— 11 族 × 3 对 = 33 对，与原有 40 对 display **零重复**，
  解决"同锚点无字可用"。
- **`scripts/ledger.py`（批次风格账本，零依赖）** —— 项目侧状态文件 `.style-ledger.json`。
  `--check` 开新站前查重（冲突维度逐条列出 + 给替代组合）、`--commit` 落定后记账、`--report` 出批次健康报告；
  `--dir` 指定工作区、`--json` 机器可读；退出码 0/1/2。
  唯一性阈值：`anchor` 1、`font_display` 1、`surface` 2、`axis` 2、`family` 2、`layout` 2、`ia` 2。
  报告阈值：锚点唯一率 ≥0.80、字体唯一率 1.00、底色 ≥3 种、变体轴 ≥3 种、族比值 ≥0.60。
- **`audit_tokens.py` F10 视觉签名存在性** —— `MASTER.md` 须含「视觉签名」段且 ≥3 条列表项
  （`.css` 输入自动降级为 info）；**F11 批次差异度** —— 新增 `--batch <工作区>`，
  扫描各站产物指纹，校验底色唯一率 / 字体唯一率 / 锚点唯一率 / 中轴种类 / 族比值；
  中轴值经 `_norm()` 归一到白名单，避免被 markdown 表格污染。
- **`validate_skill.py` F10–F13** —— F10 底色预设合法性与锚点覆盖 ≥3 档；F11 变体轴偏移在安全范围内；
  F12 族池覆盖 11 族、每族 ≥3 对、display 全库唯一；F13 `ledger.py` 与 `audit_tokens.py` 存在。
- **新阶段门 G1.6「批次查重」** —— 位于 G1.5（技术栈）之后、G2（落定）之前。
- **`SKILL.md` 新增铁律 30–32** —— 30「单站自洽 ≠ 批次多样」、31「底色是被选的，不是默认白的」、
  32「同一锚点第二次使用必须换组合」。
- **`layouts.md` 视觉签名菜单扩到每原型 8 条**，组合规则 4 → 6 条（新增"同锚点第二次必须换组"、
  "签名不写进 `MASTER.md` = 没做"）。
- **`checklist.md` 新增「批次差异合规（G1.6）」8 条**；`design-qa.md` F 级表补 F10/F11 行，
  词汇表补 `--surface` / `--variant`。
- **`测试用例集` 新增 T14「同批五站」**（5 锚点 / 5 字体 / ≥3 底色 / ≥4 族，机检验收）
  与扰动脚本 P11/P12；通用评分卡补 G1.6。
- **`判据自测脚本`（判据负向测试，零依赖）** —— 给每条判据植入一处确定的违规，
  断言它被对应的检查码抓住；同时含**正向防误报**用例（合规输入必须通过）。
  覆盖 27 条，分五组：`validate_skill`（F8–F13）、`audit_tokens` 单站（F6/F10）、
  `ledger.py`（查重与报告）、`audit_tokens --batch`（F11）、**端到端**（`emit_tokens.py` 真出
  5 站 token → `--batch` 必须 PASS）。
  只在临时副本里变异，原仓库零改动。**没有它，"判据永远返回 PASS"这个失效模式无法被发现。**
- **三个示例 `MASTER.md` 各补「视觉签名」段**（各 5 条，互不相同）。

### Changed

- **`scripts/emit_tokens.py`** —— `build()` 新增 `surface` / `variant` / `pair` 参数；
  底色计算从写死改为读 `_surfacePresets`；新增 `--surface` / `--variant` / `--pair` 三个 CLI 参数；
  输出新增 `--surface` / `--variant` 指纹变量（供批次比对）；字体解析走族池轮换。
  **兼容性**：不带新参数时行为与 0.7.0 一致（surface 取锚点默认值、variant 取 `a`、pair 取 0）。
- `SKILL.md` frontmatter `version` → 0.8.0；`description` 补 `批次差异度（跨站去重）` 与
  `batch-diversity` / `style-ledger` / `surface-dimension` 关键词；文件地图与实现说明表补
  「底色维度层」「批次账本层」；版本段改写为「开工前先确认版本」并记入本次教训。
- `validate_skill.py`：`make_T07_menu_pdf.py` 加入 `OPTIONAL_FIXTURES`（作者主动移除，降级为 info）；
  `ARTIFACTS` 白名单加入 `.style-ledger.json`。
- `README.md` / `CHANGELOG.md` / `测试用例集` 同步；测试用例数 12 → 14。

### Fixed

- 同批多个站底色全部 `#FFFFFF`（根因：`emit_tokens.py` 写死亮度）。
- 同锚点第二次使用产出**逐值相同**的 token（根因：`signatures.json` 是常量而非参数空间）。
- 「视觉签名」必填但无判据 → 等于不必填（根因：`layouts.md` 只有散文，没有 F 级检查）。
- `audit_tokens.py` 缺 `from collections import Counter` 导致 F11 崩溃。
- F11 中轴取值被 markdown 表格文本污染 → 新增 `_norm()` 白名单归一。
- `_familyPools` 中三处 `mono` 误填 CJK 栈名（`mono-cjk`）→ 改为 `jetbrains`。
- `ledger.py --report` 在未记录 `--font-display` 时把 display 唯一率显示成 `0/5 = 100%`
  —— 这是**假通过**：没记录等于这一项没被校验。改为判「未记录」不通过，
  并在 `--commit` 缺 `--font-display` 时给出 stderr 提示。

### Notes

- **跨站差异的两条腿**：单站（F6/F10）+ 跨站（F11 + G1.6 账本）。任何新判据都必须两条腿都有，
  只有一条时，每个站单看都合格，五个摆一起就塌。
- 组合空间：**40 锚点 × 4 变体 × 7 底色 × 4 字体对 = 4480**（不含布局与 IA 变化）。

## [0.7.0] — 2026-09-12

针对两个真实失败模式的修法：**产出「千篇一律、只是不同的 Markdown 组织器」**，以及**技术栈被默认继承**。

根因（改前可指到具体行）：`styles/signatures.json` 的 15 个参数里**没有字体字段**，只有一个
`disp: serif/sans/mono/mix`；`emit_tokens.py` 的 `FONT` 字典只有 3 个通用栈 —— 于是 40 个锚点产出的
`--font-display` 几乎都是 `"Inter", -apple-system…`，三个示例的 `--sans` 一字不差。技术栈则被放在
「实现说明」表里隐式假设为 Astro，没有独立判断环节。

### Added
- **`techstack.md`（Phase 1.5 · 技术栈选型）** —— 在「约束筛选」之后、「风格与字体」之前：
  需求 8 判定项（D1 页数 / D2 交互 / D3 维护者 / D4 数据源 / D5 交付形态 / D6 多语言 / D7 渲染 / D8 性能预算）
  → 7 个候选栈（`plain-html` / `astro` / `eleventy` / `vite-vanilla` / `next` / `nuxt` / `hugo`）
  → **先排除、再定序** → 输出 `tech-stack.md`（含被排除项与 3 条可观测证伪条件）+ 反模式表。
- **`scripts/pick_stack.py`** —— 技术栈确定性推荐器（零依赖）：把上面的排除与评分固化，输出排序 + 逐条理由 +
  被排除项 + 可直接落进 `tech-stack.md` 的结论；`--json` 可被消费；`embedded` / `system-only` 走短路分支。
- **`styles/fonts.json`（字体搭配注册表）** —— 40 个锚点各一对**具名**字体（display × body）+ mono + 中文回退
  + 加载策略（`self`/`cdn`/`system`）+ 搭配理由；11 族默认值；6 条硬规则（R1 具名 / R2 display≠body /
  **R3 display 全库唯一** / R4 中文回退显式 / R5 字重克制 / R6 可获取）。
- **`layouts.md` 新增「视觉签名（反同质化）」** —— 每个产出须声明 **≥3 条结构级视觉签名**（按布局原型给候选菜单），
  并过「灰度测试」（关掉颜色后签名仍在）；同一批交付里两个站的签名组合不得完全相同。
- **`checklist.md` 新增两节**：「技术栈选型合规（G1.5）」与「反同质化」（含人眼终审：两个产出并排能否一眼看出不同）。
- 新阶段门 **G1.5**；`SKILL.md` 新增铁律 5（先定技术栈，再定风格与字体）与整组「铁律 · 反同质化」（27–29）。
- 新判据 **audit_tokens.py F6**（字体搭配：display/body 存在、首族具名、二者不同）与
  **validate_skill.py F8/F9**（字体注册表覆盖与唯一性；`techstack.md` + `pick_stack.py` 存在）。

### Changed
- `scripts/emit_tokens.py`：字体栈改从 `styles/fonts.json` 读，输出
  `--font-display` / `--font-body` / `--font-mono` / `--font-cjk` / `--font-display-name`，
  并打印搭配理由；锚点未收录时按「锚点 → 族默认 → 通用」降级并**显式告警**（不再悄悄退回 Inter）。
- `SKILL.md` 铁律重编号（1–20 → 1–21，新增第 5 条），原「落地与审美」21–24 → 22–26，新增 23（字体搭配）；
  阅读顺序表新增 Phase 1.5 与 Phase 4（字体表）；输出契约新增 `tech-stack.md`；文件地图与实现说明表同步；
  frontmatter `version` → 0.7.0，`description` 补技术栈与字体关键词，`compatibility` 说明选 `plain-html` 时产物零依赖。
- `intake.md`：Grill 由 9 支扩到 **10 支**（新增 B10 技术栈输入 Q24–Q27）；约束筛选表新增「维护者技术程度」「渲染需求」两维；
  `intent-summary.md` 与「剩余空间」段加入技术栈。
- `decide.md`：B 类清单新增「技术栈」与「字体搭配」「视觉签名」；A 类中「字体回退栈」改为「字体**加载**细节」以免与 B 类冲突；
  强制停顿点的落定项加入技术栈与字体。
- `typography.md`：新增 §0「字体搭配」（先选字再算数值）—— 五种搭配范式、六条硬规则、加载策略与 CJK 体积警告。
- `design-qa.md`：F 级判据新增 F6；规范 token 词汇表补 `--font-display/body/mono/cjk`。
- `README.md`：流程图加 Phase 1.5；「它解决什么」表补三条新失败模式；内容库与目录结构同步。

### Fixed
- **三个站点的字体**：`swiss-utility` → Archivo × Inter、`provisions-label` → Anton × Inter、
  `diagonal` → Prata × Inter（保留宿主字体优先级），全部补 `--font-display`/`--font-body`，
  使 `audit_tokens.py` 的 F6 通过。
- **字体同质化**：40 个锚点的 display 字体此前完全一致（三选一），现**全库唯一**，由 `validate_skill.py` F8 机器保证。

## [0.5.0] — 2026-09-12

面向开源与跨 agent 移植的结构整理，外加一轮**跨文件一致性修复**。流程与 20 条铁律不变。

### Changed
- `SKILL.md` frontmatter 收敛到 Agent Skills 规范字段：`name` / `description` / `license` / `compatibility` / `metadata`。
  - 原顶层的 `version` 移入 `metadata.version` —— 非规范顶层键会让严格解析器（如 claude.ai 上传）直接硬报错。
  - 新增 `license: MIT`、`compatibility`（Python / Node / ffmpeg 依赖与 OCR·ASR 缺失说明）、`metadata`（作者 / 仓库 / 规范 / 关键词）。
- `SKILL.md` 的「引用」段改为 **markdown 相对链接**的文件地图，分「阶段文档 / 内容库 / 工具与示例」三组，便于任意 agent 顺链加载。
- 新增「路径约定」：所有路径相对 skill 根目录，装在 `~/.claude/skills/`、`.codex/skills/`、`.cursor/skills/`、`~/.workbuddy/skills/` 都一致。
- 「本机工具实况」不再硬编码作者机器状态，改为「先跑 `scripts/check_env.py` 探测」并给降级建议（`source.md` 内 8 处硬编码同步改掉）。
- 宿主专有能力表述泛化：`uipro init --ai <target>`；浏览器采集改为「宿主提供的浏览器能力（agent-browser / Playwright / Chrome DevTools MCP）」；Office 专用通道改为条件句，不再绑定某个具体 skill。
- `styles/index.json` 的 `_loadingTiers.T2` 与 `SKILL.md` 对齐为「收敛到 1–2 个后只读这 1–2 个 spec」。
- `layouts.md` 的中轴表由「布局原型 → 中轴」的硬映射，改为**以锚点声明的 `axis` 为准**（附反例说明）。
- `layouts.md` 的 `catalog-grid` 补上**作品变体**（作品卡 / 无价签 / 常见 `center-axis`），不再只描述商业 SKU 目录。

### Added
- `README.md`（中英双段）、`LICENSE`（MIT）、`.gitignore`、`CHANGELOG.md`、`THIRD-PARTY.md`。
- `scripts/check_env.py` —— 探测 Python 依赖 / ffmpeg / OCR / ASR，输出能力表与降级建议，支持 `--json`。
- `scripts/validate_skill.py` —— **规范与自洽自检**，无第三方依赖，可直接接 CI。A 段 frontmatter 规范、B 段结构、C 段文档间引用、D 段仓库卫生、**E 段注册表跨文件一致性**（锚点的 layout / family / axis 必须落在定义域内、spec 必须有同名锚点、示例 `MASTER.md` 必须声明 `--axis`）。A–D 与 E 各做过负向测试（植入 8 类 + 4 类违规，全部被捕获）。
- `styles/index.json` 新增 `_specFallback`：命中锚点但无本地 spec 时的三级降级规则（typeui → 用 7 个元数据字段现场落 token → 换同族带 spec 的锚点），并明确禁止凭印象补 spec。
- `立项调研`（原根目录 `DECISION.md` 归档）——立项调研：为什么是「改写现成选型引擎」而不是自研。

### Fixed
- **注册表与示例互相矛盾**（E 段就是为抓这类漂移而加的）：`styles/index.json` 的 `diagonal` 声明 `layout: split-narrative`，而 `示例站点/content-profile.md` 明确记录「选 `catalog-grid` 而非 `split-narrative`」且站点确实是作品网格 → 锚点改为 `catalog-grid`（`axis: center-axis` 不变）。
- **中轴表与实测值冲突**：`layouts.md` 原把 `editorial-hero` 标为 `center-axis`，但按 `provisions-label` 真实做出的转化页是 `left-rail`（与 `index.json` 一致，页面无任何居中）→ 改为以锚点为准。
- 三份 `design-system/MASTER.md` 全部**缺 `--axis`**（输出契约要求）→ 补齐，其中两份采用 token 表行的形式。
- **品牌斜线角度写错**：某站的 3 份文档写作 145°，而该站 CSS（`index.astro` / `tokens.css`）与 Diagonal 自身的 `.diagonal-line` 都是 **135°**（145° 是页面转场参数，二者极易混）→ 统一为 135°。
- 锚点计数不一致：`styles/index.json`（2 处）与 `styles/families.md`（1 处）误写 41，实际为 **40**。
- 示例对照表写错了锚点 / IA / 布局 / 中轴，素材数量写成「124 张 / 22 MB」（实为 **62 张 / 约 11 MB**）→ 按实测重写，并补上「回归测试」清单。
- 移除示例下的构建产物（`node_modules` / `dist` / `.astro`）与 6 个一次性 `_*.py` 脚本（`_diff` / `_extract` / `_fix_images` / `_gen_diagonal` / `_map` / `_verify`），其职责已由 `scripts/extract_source.py` + `scripts/verify_assets.py` 承接。

## [0.4.0] — 2026-09-12

### Added
- `decide.md` —— 决策权 A/B/C/D 四档 + 提问预算 + 必须停下来的 5 个触发条件。
- `styles/families.md` —— 11 族两级收敛（族内互斥 / 族间切换 / 证伪条件）。
- `styles/specs/` —— 6 个 Tier-2 完整 spec。
- `source.md` 扩为 13 类输入源完整预案 + 格式欺骗坑 + 溯源表。
- `scripts/extract_source.py` —— 13 类源统一提取（已实测）。
- `SKILL.md` 增加阶段门 **G-1…G6** 与阅读顺序表；铁律 16 → 20。

### Changed
- `styles/index.json` 锚点 13 → **40**，新增 `referencePool`(20)。

## [0.3.0] — 2026-09-11

### Added
- Phase -1（源材料 / 交付形态）、Phase 6（微调回访）。
- `source.md`、`host-align.md`、`scripts/`。
- 语言策略、参考站采集、中轴与尺寸、回源可追溯、图库全图可达。

## [0.2.0] — 2026-09-10

### Added
- Grill 阶段（一次一问 + 推荐答案）、`layouts.md` 布局原型、图文策略（`imagePolicy` / `iconPolicy`）、game-lab 灵感池。

## [0.1.0] — 2026-09-09

### Added
- 首个可用版本：IA 四选一（`architectures/`）+ 13 个风格锚点 + token 输出契约。
