# diagonal — 对角线（Diagonal 品牌语言）

**族**：industrial ｜ **布局原型**：split-narrative（可降级到 catalog-grid）｜ **中轴**：center-axis
**image**：preferred ｜ **icon**：none ｜ **密度**：balanced

## 何时用

- 工业遗产 / 井盐 / 天车 / 结构等题
- 需要复用用户自有品牌语言（DIAGONAL 项目及其子页面）
- **宿主站已有该设计系统时——必须服从宿主令牌**（见 `../../host-align.md`），本 spec 只作对照

## 何时不用

- 独立配色：本锚点的色值来自宿主，不许自创一套相近色
- 圆润可爱化处理（与斜线母题冲突）

## token 骨架（对齐 DIAGONAL 实际值，可直接粘贴）

```css
:root {
  --bg:        #FAFAF8;   /* 纸白，非纯白 */
  --fg:        #1A1A1A;   /* 文本 */
  --muted:     #6B6B66;
  --line:      rgba(0,0,0,.10);
  --accent:    #B33A2A;   /* 暗朱 / 铁氧化物红 = rgb(179,58,42) */
  --bg-soft:   #F2F2F2;

  --sans:  "Inter", "Helvetica Neue", Helvetica, Arial, "PingFang SC", "Microsoft YaHei", sans-serif;
  --serif: "Newsreader", "Noto Serif SC", Georgia, serif;
  --mono:  "JetBrains Mono", ui-monospace, Consolas, monospace;

  --measure: 1080px;
  --gutter:  16px;

  --duration-fast:   160ms;
  --duration-normal: 320ms;
  --ease-out: cubic-bezier(.22,.61,.36,1);
}
```

## 母题（两条，别再加第三条）

```css
/* ① 斜线带：组件级用 135deg（不是 145deg —— 145deg 是页面转场参数，二者不同） */
.diagonal-line {
  background: linear-gradient(135deg,
    rgba(179,58,42,.90) 0%, rgba(179,58,42,.35) 55%, transparent 100%);
}

/* ② 旋转标签：-35deg，永远原点在左上/右下 */
.rotated-label {
  transform: rotate(-35deg);
  transform-origin: left top;
  font-family: var(--mono);
  font-size: 10px;
  letter-spacing: .12em;
  text-transform: uppercase;
}
```

## 骨架片段

```html
<header class="hero">            <!-- 超大衬线字标 + 145deg 斜线装饰（转场用） -->
  <h1 class="wordmark">…</h1>
  <p  class="hero__tag">…</p>
</header>
<main class="split">             <!-- 左文右图 / 交错 -->
  <div class="col-text">…</div>
  <div class="col-media">…</div>
</main>
<footer class="footer">          <!-- 衬线字标 + 标语 + 版权/地点/colophon -->
  <div class="footer__deco"></div><!-- 135deg 装饰带，opacity .04 -->
</footer>
```

## 必有元素

- 衬线字标（`--serif`，weight 700–900，letter-spacing 负值）
- 等宽 `.archive-text`（uppercase + tracking-widest + `--mono`）
- 至少一处 135deg 斜线（`--accent`）
- 紧凑微标签（10–11px，`--mono`）
- `--accent` 只用在：状态点、微标签、hover 遮罩、装饰带

## never

- 圆角 > 4px
- 第二个强调色
- 阴影（用 1px 细线分区替代）
- 把 145deg 当组件角度（那是转场参数，组件用 135deg）
- 中间调灰之外的中性色倾向（暖灰/冷灰都行，但只能一种）

## 常见误用

| 误用 | 后果 | 修正 |
|---|---|---|
| 只改了红色没改斜线角度 | 品牌辨识度丢一半 | 135deg 是签名，必须出现 |
| 作品图被 `object-fit: cover` 裁成统一方格 | 艺术作品的原始比例被破坏 | 论文型内容用 contain；只有商品缩略图才 cover |
| 中轴在肖像/封面/正文之间来回跳 | 页面"散" | 定死 `--axis: center-axis`，图与图注同轴 |
| 自己在独立站里重写了一套 token | 与宿主站不一致 | 去读宿主 `tailwind.config.js` / `globals.css` 抄原文值 |
