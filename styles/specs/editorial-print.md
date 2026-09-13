# editorial-print — 编辑印刷

**族**：editorial ｜ **布局原型**：split-narrative ｜ **中轴**：split（正文列左对齐）
**image**：optional ｜ **icon**：none ｜ **密度**：balanced

## 何时用

- 有长文且**受众愿意读**
- 主体是文字 / 出版 / 学术 / 深度内容
- 内容密度中高，需要靠排版建立层级

## 何时不用

- 受众耐心低（手机端快速滑动）→ 换 `utility-board` / `catalog-grid`
- **配图质量低** → 这套语法会把图放大，低质图必崩。改走无图锚点
- SKU 或大量并列条目 → 换 `catalog-grid`

## 视觉原理

**一套印刷语法**：栏宽决定阅读节奏，基线网格保证垂直秩序，图文关系承担叙事。
字体即图形 —— 字号对比可以拉到很大，但要**在同一套比例体系里**。

## token 骨架

```css
:root {
  --bg:      #FFFFFF;
  --fg:      #1A1A1A;
  --muted:   #6E6E6E;
  --line:    #E2E2E2;
  --accent:  #B33A2A;    /* 仅用于引文标记 / 链接 / 分节编号 */

  --sans:  "Inter", "Helvetica Neue", "PingFang SC", sans-serif;
  --serif: "Newsreader", "Noto Serif SC", Georgia, serif;

  /* 字阶：6 级，比例约 1.4–1.5 */
  --fs-1: 15px;   /* 微标签 */
  --fs-2: 17px;   /* 正文 */
  --fs-3: 22px;
  --fs-4: 32px;
  --fs-5: 48px;
  --fs-6: 72px;   /* 标题上限 */

  --measure-text: 65ch;   /* ⚠️ 正文行宽上限，超过 75ch 阅读性骤降 */
  --measure: 1080px;
  --leading-body: 1.7;
  --leading-head: 1.05;
}
```

## 骨架片段

```html
<main class="split">
  <div class="col-text">
    <p class="kicker mono">01 — 分节编号</p>
    <h2 class="serif">小节标题</h2>
    <p class="lead">导语，字号略大。</p>
    <p>正文…（<code>max-width: 65ch</code>）</p>
    <blockquote>引文，用 --accent 的左竖线标记</blockquote>
  </div>
  <div class="col-media">
    <figure><img …><figcaption class="mono">图注 · 编号</figcaption></figure>
  </div>
</main>
```

## 必有

- **两字族分工明确**：衬线做标题/引文，无衬线做正文/标签。不混用
- 正文行宽 ≤ 65ch（中文按 40–45 字算）
- 行高：正文 1.7、标题 1.05
- 图注用等宽微标签，**与图同轴**
- 分节编号（01 / 02 …）

## never

- **低质量配图**（这套会把图放大，直接毁掉）
- 超过两种字族
- 行宽 > 75ch
- 正文用衬线但行高 <1.5
- 首字下沉 + 多语混排（中文首字下沉效果差）
- 居中正文（长文居中极难读 —— 写进 never 清单）

## 与其他锚点的区分

| 容易混 | 区别 |
|---|---|
| `swiss-editorial` | 那个无衬线到底、更冷、无强调色；这个靠衬线撑住"书卷气" |
| `longform-narrative` | 那个是**单栏**长文（65ch 居中一列）；这个允许**分栏图文并置** |
| `magazine-grid` | 那个多条目并列、每屏节奏不同；这个是**一篇内容**的展开 |

## 常见误用

| 误用 | 后果 | 修正 |
|---|---|---|
| 用低质配图 | 整体降级为"廉价杂志" | 无好图就整站不用图，走纯文字排版 |
| 行宽铺满 1200px | 阅读性崩溃 | `max-width: 65ch` |
| 标题和正文都用衬线 | 层级糊在一起 | 字体分工 |
| 首屏只有一个大标题无导语 | 读者不知道要读什么 | 加导语或 kicker |
