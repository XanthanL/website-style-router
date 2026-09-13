# swiss-utility — 瑞士实用主义

**族**：grid ｜ **布局原型**：utility-board ｜ **中轴**：left-rail
**image**：**forbidden** ｜ **icon**：functional ｜ **密度**：compact

## 何时用

- 视觉资产质量低或**完全没有**
- 信息需要被**快速扫读**（来查"今天有什么 / 还有没有"）
- 维护者非技术（改一个数据文件即可更新）
- 主体偏实用、日常、高频

## 何时不用

- 需要氛围与情绪 → 换 `warm-hospitality` / `contemplative`
- 条目 <10 且要突出单件 → 换 `editorial-hero`
- 需要品牌辨识度 → 换带母题的锚点

## 视觉原理

像**公交站牌**与**药品说明书**：信息优先，装饰为零。
一屏能扫完的信息量 > 一屏的美感 —— 这是它唯一的目标。

## token 骨架

```css
:root {
  --bg:      #FFFFFF;
  --fg:      #111111;
  --muted:   #767676;
  --line:    #DCDCDC;
  --accent:  #1F3FD8;    /* 钴蓝：信息型强调色，不是咖啡棕 */
  --bg-soft: #F6F6F6;

  --sans: "Inter", "Helvetica Neue", "PingFang SC", sans-serif;
  --mono: "JetBrains Mono", ui-monospace, Consolas, monospace;

  --radius: 0;           /* 直角 */
  --shadow: none;        /* 只用 1px 线 */
  --measure: 960px;
  --row-h: 44px;         /* 行高固定，便于扫读 */
}
```

## 骨架片段

```html
<header class="board-bar">              <!-- 品牌 + 今日状态，无 hero -->
  <span class="brand mono">12㎡ COFFEE</span>
  <span class="live mono">● LIVE · 已更新 07:30</span>
</header>

<main>
  <table class="ledger">
    <!-- 行 = 条目；列 = 状态(文字标签) / 规格(等宽) / 价(等宽) / 操作 -->
    <tr class="is-soldout">
      <td>肯尼亚 AA</td>
      <td><span class="tag">售完</span></td>     <!-- 状态有文字，不靠颜色 -->
      <td class="mono">250g</td>
      <td class="mono">¥68</td>
    </tr>
  </table>
</main>

<footer class="mono">改 src/data/*.json 即更新 · 每日 07:30 发布</footer>
```

## 必有

- `flush-left` 一切（左对齐到底）
- **等宽数字**（价格 / 规格 / 时间列必须对齐）
- 状态用**文字标签**（"售完""在售"），不靠颜色单独传达
- 1px 细线分区（无阴影、无卡片）
- 功能图标：`●` `○` `→` 这类等宽字形，**不用 emoji**

## never

- 居中标题
- 超过两个字重（建议只用 400 / 700）
- 装饰性图形、插画、渐变
- 大圆角
- 任何图片（`imagePolicy: forbidden`）—— 低质图会毁掉这套
- 内容藏在组件里（必须单一数据源，非技术维护者要能改）

## 常见误用

| 误用 | 后果 | 修正 |
|---|---|---|
| 因为品类是"咖啡店"就套暖棕 | AI 味最典型来源 | 卖信息就冷色，卖氛围才暖色 |
| 加上卡片阴影"显得现代" | 与零装饰语法冲突 | 改 1px 线 |
| 用颜色区分售完/在售 | 色盲不可用 | 文字标签 + 删除线 |
| 内容硬编码进组件 | 非技术维护者改不动 | 抽到单一 JSON |
| 加了个 hero 大图 | 首屏信息量归零 | 删掉，直接上表 |
