# museum-modern — 美术馆现代

**族**：institutional ｜ **布局原型**：catalog-grid ｜ **中轴**：center-axis
**image**：**required** ｜ **icon**：none ｜ **密度**：balanced

## 何时用

- 美术馆 / 画廊 / 艺术机构 / **艺术家个人站**（作品集最常见的正解）
- 作品图质量高（专业拍摄或高清扫描）
- 需要"专业但不冷漠"——比 `quiet-luxury` 可亲，比 `editorial-print` 视觉优先

## 何时不用

- 低质图或只有手机随拍 → 换 `swiss-utility` / `nostalgic`
- 作品本身就是激进的当代艺术且希望页面被冲击 → 换 `expressive-artistic`
- 需要长文阅读主导 → 换 `editorial-print`

## 视觉原理

**白墙 + 展签**。作品被当作展品对待：占据最大视觉份额，页面只提供中性的承载。

## token 骨架

```css
:root {
  --bg:      #FAFAF8;   /* 纸白，比纯白温和（长时间看图不刺眼） */
  --fg:      #1A1A1A;
  --muted:   #6B6B66;
  --line:    rgba(0,0,0,.10);
  --accent:  #B33A2A;   /* 若宿主站已有品牌色，换为宿主值 */
  --bg-soft: #F0EFEC;   /* 图片容器底色（未加载时也不突兀） */

  --sans:  "Inter", "Helvetica Neue", "PingFang SC", sans-serif;
  --serif: "Newsreader", "Noto Serif SC", Georgia, serif;
  --mono:  "JetBrains Mono", ui-monospace, monospace;

  --measure: 1200px;
  --gutter:  24px;
  --radius:  0;
}
```

## 骨架片段

```html
<header class="hero">
  <h1 class="artist-name">姓名 / NAME</h1>
  <p  class="tags mono">实验艺术 · 新媒体 · 影像</p>
  <p  class="stat mono">17 works — 58 images</p>
</header>

<section class="intro">                     <!-- 肖像紧随姓名之下 -->
  <figure class="intro__portrait"><img …><figcaption class="mono">肖像</figcaption></figure>
  <div class="intro__text"><h2>艺术家自述</h2><p>…</p></div>
</section>

<section class="works">
  <div class="section__head">
    <h2>精选作品</h2>
    <span class="rotated-label mono">17 件</span>
  </div>
  <ul class="grid">                          <!-- 3 / 2 / 1 列 -->
    <li class="card">…</li>
  </ul>
</section>
```

## 必有

- **多图条目的完整图库**：缩略条 + `当前/总数` 计数 + 前后翻页 + 键盘左右 + Esc
  ⚠️ 只渲染 `images[0]` 是**交付不完整**（本次真实事故：49/58 图没上站，校验却 PASS）
- 图注与图同轴（图居中了，figcaption 也必须居中）
- 作品图**按原始比例呈现**（论文型内容用 `contain`，不要用 `cover` 裁成统一方格）
- 年份/媒介用等宽微标签
- 姓名与肖像紧邻（肖像在姓名正下方）

## never

- 低质图
- 促销语气
- 把作品裁成统一比例方格
- 编造展览经历 / 获奖 / 收藏记录
- 联系区默认不做（用户常直接删掉 —— 没明确要就别加）

## 常见误用

| 误用 | 后果 | 修正 |
|---|---|---|
| 只显示每个作品第一张图 | 大量素材没用上 | 做完整图库 |
| `cover` 裁切艺术作品 | 构图被破坏 | `contain` + 容器底色 |
| 肖像与姓名离得很远（分栏两端） | 第一眼看不到"这是谁" | 肖像紧随姓名 |
| 中轴在肖像/封面/正文间跳 | 页面散 | 定死 `--axis: center-axis`，正文保持左对齐 |
| 偷懒不写双语而宿主站是双语的 | 与宿主不一致 | 复用宿主档案里的既有译文 |
