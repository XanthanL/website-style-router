# warm-hospitality — 暖待客 ⚠️ 最大陷阱

**族**：craft ｜ **布局原型**：editorial-hero ｜ **中轴**：center-axis
**image**：**required**（专业环境/食物摄影）｜ **icon**：decorative ｜ **密度**：airy

> ⚠️ **这是本 skill 里被误用最多的锚点。** 「咖啡店/餐厅 → 自动套暖棕 + 拿铁特写 + serif」是 AI 味最典型的来源。
> **套用前必须确认两条 when 同时成立，缺一条即禁用。**

## 前置条件（两条，缺一不可）

1. **有专业环境/食物摄影**（不是手机随拍）
2. **确实在卖空间体验**（有座位、可停留、来坐坐）

两条不成立时：

| 情况 | 应换 |
|---|---|
| 有图但是随手拍 | `market-stall`（随手拍反而是卖点） |
| 无座位 / 只外带 / 卖"今天有什么" | `swiss-utility` |
| 卖产品本身而非空间 | `provisions-label` / `craft-artisanal` |

## 视觉原理

暖色 + 材质 + "进来坐"的身体感。重点不是"咖啡"，是**停留**。

## token 骨架

```css
:root {
  --bg:      #FBF7F1;    /* 奶油纸 */
  --fg:      #2A231D;    /* 暖黑，不用纯黑 */
  --muted:   #7A6A5C;
  --line:    rgba(42,35,29,.12);
  --accent:  #B4622D;    /* 烘焙橙（仅一个） */
  --bg-soft: #F2EAE0;

  --sans:  "Inter", "PingFang SC", sans-serif;
  --serif: "Newsreader", "Noto Serif SC", Georgia, serif;

  --radius:  8px;        /* 温和圆角，但不要药丸形 */
  --shadow:  0 1px 2px rgba(42,35,29,.06);   /* 极轻，仅一层 */
  --measure: 1120px;
  --gutter:  32px;
}
```

## 骨架片段

```html
<header class="hero">
  <h1 class="serif">店名</h1>
  <p class="claim">一句话说清在卖什么体验</p>
  <a class="cta">到店 / 预约</a>
</header>

<section class="block">                <!-- 环境大图，占满宽 -->
  <img class="env-shot" …>
</section>

<section class="block grid-2">         <!-- 图文交错 2–3 组 -->
  <div class="text">营业时间 · 地址 · 一句人话</div>
  <img …>
</section>

<section class="info">                 <!-- 营业时间/地址要能被快速找到 -->
</section>
```

## 必有

- 环境大图（**不是饮品特写**；特写是 `provisions-label` 的语法）
- 营业时间与地址**可被快速找到**（氛围不能以牺牲实用信息为代价）
- 暖黑而非纯黑（`#2A231D` 一类）
- 圆角温和（6–10px），不要药丸形

## never

- 无专业摄影时使用（会变成廉价的暖色滤镜）
- **命中品类就自动套用**（必须先验两条前置条件）
- 拿铁/拉花特写当首图（撞车率最高的图）
- 手写体用于正文（只可用于短标签）
- 药丸形大圆角 + 多层阴影（那不是"暖"，是"幼儿园"）

## 与其他锚点的区分

| 容易混 | 区别 |
|---|---|
| `craft-artisanal` | 那个讲**工艺过程**（手作步骤、材料近景），这个讲**空间** |
| `provisions-label` | 那个卖**产品**（要下单），这个卖**停留**（要到店） |
| `mid-century-modern` | 那个有**年代感**（1950–60s），这个不分年代 |
| `paper-ink` | 那个是**印刷质感**（纸纹/墨迹），这个要**摄影** |

## 常见误用

| 误用 | 后果 | 修正 |
|---|---|---|
| 无摄影也硬上 | 廉价感，比不做还差 | 换 `swiss-utility`，靠排版撑 |
| 首图放拿铁特写 | 与 90% 同类站撞车 | 放空间全景或人的活动 |
| 氛围占满首屏，找不到营业时间 | 用户流失 | 营业时间进首屏或固定条 |
| 全站三个强调色"更活泼" | 失去克制 | 只留一个烘焙橙 |
