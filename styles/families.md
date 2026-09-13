# Families — 先选族，再选锚点

40 个锚点直接挑 = 又变回菜单式选型（必然向均值收敛）。正确顺序是**两级收敛**：

```
约束筛选（intake.md）→ 剩余空间
      ↓
选族（本文件）—— 由「内容支撑力 / 转化目标 / 密度诉求」决定，⚠️ 不由品类决定
      ↓  40 → 1–2 个族
族内选锚点（styles/index.json 的 when 命中最多、never 冲突最少）
      ↓  族内 3–4 个 → 收敛到 1 个
出 token（Tier 2：只读这 1 个的完整 spec；无本地 spec 时按 index.json 的 _specFallback 降级）
```

## 为什么必须"先选族"

用户在 Grill 里说的是**品类**（"咖啡店""艺术家""企业"），但品类**不决定**视觉族：

- 咖啡店可能是 `craft`（卖空间体验）也可能是 `grid`（只做外带、日更台账）—— 本次真实案例是后者
- 艺术家可能是 `expressive`（作品即界面）也可能是 `contemplative`（静奢）也可能是 `industrial`（纪实档案）
- 企业可能是 `institutional`（合规信任）也可能是 `techno`（科技前沿）

**决定族的是三件事**，都必须在 Grill 里问出来：

| 决定项 | 问题 | 向左 → | 向右 → |
|---|---|---|---|
| **内容支撑力** | 手上有什么撑得住视觉？ | 只有文字 / 无图 | 高质量图 / 影像 / 实物 |
| **转化目标** | 要人读完、查到、还是下单？ | 无目标、纯展示 | 明确购买/留资 |
| **密度诉求** | 用户来扫读还是来感受？ | 扫读、高频、比对 | 感受、慢、一次一件 |

## 11 个族

### editorial · 编辑印刷族
**本质**：用印刷语法组织信息——栏宽、字阶、基线网格、图文关系。
**整族命中当**：主体靠文字成立 / 内容有深度 / 受众愿意读。
**族内**：`editorial-print`（长文图文并置）· `editorial-hero`（一句话主张+行动）· `magazine-grid`（多条目图文交错）· `longform-narrative`（单栏长文）
**⚠️ 族内互斥**：同一站只用 1 个。`editorial-hero` 与 `magazine-grid` 同挂会互相稀释注意力。

### grid · 网格理性族
**本质**：网格即秩序——flush-left、等宽数字、零装饰、可扫读。
**整族命中当**：信息密度高 / 需快速定位 / 视觉资产弱。
**族内**：`swiss-utility`（状态台账）· `swiss-editorial`（理性但有字阶对比）· `data-dense-app`（操作界面）· `technical-drawing`（图纸感）
**⚠️ 与 craft/expressive 互斥**：网格族拒绝一切软性修饰，混入圆角/纹理即崩。

### contemplative · 克系留白族
**本质**：留白与克制本身即内容。
**整族命中当**：客单价高或主体想"不解释" / 素材质量顶级 / 内容量少。
**族内**：`quiet-luxury`（权威感）· `agentic-minimal`（零设计）· `japanese-ma`（东方留白）· `scandinavian-clean`（温和日常）
**⚠️ 前置硬条件**：`quiet-luxury` 与 `japanese-ma` **必须有高质量素材**，无图时整族不成立。

### craft · 材质工艺族
**本质**：材料的触感与手艺痕迹——纸、墨、黏土、布料、食物。
**整族命中当**：卖的是手感/食味/空间体验 / 有实物或环境摄影。
**族内**：`warm-hospitality`（空间体验）· `soft-organic`（亲和大众）· `craft-artisanal`（手艺过程）· `paper-ink`（印刷质感）
**⚠️ 最大陷阱**：「咖啡店/餐厅 → 自动套 warm-hospitality」。先确认"**确实卖空间体验**（有座位、可停留）且**有专业环境摄影**"两条同时成立，否则掉到 grid 或 commerce。

### industrial · 工业纪実族
**本质**：裸露结构与材料证据——混凝土、钢、档案编号、测量线。
**整族命中当**：工业遗产 / 纪实 / 结构本身就是主张。
**族内**：`diagonal`（对角线品牌语言）· `industrial-documentary`（现场纪实）· `concrete-brutalist`（反设计）· `archival-index`（档案检索）
**⚠️ 宿主优先**：若宿主站已有设计系统（如 DIAGONAL），本族锚点必须**服从宿主令牌**，见 `../host-align.md`。

### commerce · 零售商品族
**本质**：把货架与价签搬上网页。
**整族命中当**：有明确购买目标 / SKU 清晰 / 需合规信任。
**族内**：`provisions-label`（少 SKU 强主张）· `product-catalog`（多 SKU 筛选）· `market-stall`（日更小体量）· `luxury-retail`（高单价私洽）
**⚠️ 合规红线**：本族一律受 `intake.md`「实物商品专项」约束——合规信息不可折叠、禁疾病宣称、禁极限词、禁编造评价与销量。

### expressive · 实验艺术族
**本质**：作品即界面，排版本身成为表达手段。
**整族命中当**：主体本身是当代艺术/实验创作 / 受众期待被冲击。
**族内**：`expressive-artistic`（作品即界面）· `deconstructivist`（破碎错位）· `collage-cutout`（拼贴）· `kinetic-type`（动态字体）
**⚠️ 与多语言互斥**：本族锚点几乎都依赖字宽与版式精确控制，双语/多语会失控。

### nostalgic · 复古怀旧族
**本质**：借用某个年代的形式语言与色板制造时间感。
**整族命中当**：历史/档案/老品牌 / 需要年代辨识度。
**族内**：`retro-nostalgic`（做旧纸张）· `art-deco-glam`（1920s 奢华）· `mid-century-modern`（1950–60s 暖木）
**⚠️ 与"前沿科技"定位互斥**。

### techno · 科技未来族
**本质**：以界面质感与数据可视化传达前沿性。
**整族命中当**：科技/AI/游戏产品 / 受众是早期采用者。
**族内**：`glass-tech`（半透明发光）· `cyber-terminal`（命令行故障）· `dark-console`（工作台）
**⚠️**：`glass-tech` 禁用于长文页；`cyber-terminal` 禁用中文长正文（等宽中文极难读）。

### vernacular · 东方与地域族
**本质**：本土书写与材料传统——纸、墨、印、纹样。
**整族命中当**：东方美学主体 / 茶器手作书画 / 需要文化根性。
**族内**：`ink-wash`（水墨）· `washi-japanese`（和纸）· `seal-script-cn`（印章汉字）
**⚠️ 与多语言互斥**（字形冲突）；书法体**不可用于正文**。

### institutional · 机构公信族
**本质**：可预测的结构建立信任。
**整族命中当**：B2B/政企/学术/须多方审阅 / 长期运营。
**族内**：`corporate-structured`（企业）· `institutional-archive`（档案检索）· `museum-modern`（美术馆）
**⚠️ 与个人/艺术主体的"人味"诉求互斥**。

## 族间切换（题变了要整族换，不是换锚点）

| 若发生这种变化 | 应切换到 |
|---|---|
| 从"展示"变成"下单" | → `commerce`（`grid`/`contemplative` 撑不住购买） |
| 从"有专业摄影"变成"只有手机随拍" | `craft`/`contemplative` → `grid` 或 `nostalgic`（做旧能吸收低质图） |
| 从"单品"变成"50+ 条目" | `editorial-hero`/`minimal-state` → `grid` 或 `institutional` |
| 从"单语"变成"多语" | `expressive`/`vernacular` → `grid` 或 `institutional` |
| 从"独立站"变成"嵌入已有主站" | 全部 → **服从宿主**（`../host-align.md`），只保留族决定布局原型 |

## 收敛后的必做验证（证伪条件）

选定 1 个锚点后，写出 **3 条"如果…就说明选错了"**。写得出来才算收敛完成。

示例（本次 `diagonal` + `catalog-grid`）：
```
证伪 1：若宿主 DIAGONAL 的暗朱强调色被换成其他红 → 说明没服从宿主
证伪 2：若作品图被裁成统一方格（cover）导致原比例丢失 → 说明布局原型选错（应 split-narrative）
证伪 3：若中轴在肖像/封面/正文之间来回跳 → 说明 --axis 没定死
```

**写不出证伪条件 = 约束不够，回 Grill 补 B2/B3/B8。**
