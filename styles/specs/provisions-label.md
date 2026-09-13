# provisions-label — 商品标签

**族**：commerce ｜ **布局原型**：editorial-hero ｜ **中轴**：left-rail
**image**：preferred（产品图，非氛围图）｜ **icon**：functional ｜ **密度**：balanced

## 何时用

- 卖实体商品（食品 / 地方特产 / 手作），目标是**下单**
- 有产品图但**不依赖氛围场景**
- 需要「食欲」与「合规信任」同时成立
- SKU 少（<20），不需要检索层

## 何时不用

- SKU 多（>20）→ 换 `product-catalog`
- 卖的是空间体验 → 换 `warm-hospitality`
- 无产品图且拿不到 → 换 `swiss-utility`，等有图再回来

## 视觉原理

把**食品包装与价签**放大到网页尺寸：
- 超大品名（包装正面的品牌名逻辑）
- 等宽规格数字（净含量/价格，像电子秤）
- 单一高饱和色（食欲色，红/橙/赭）
- 零装饰图形（包装本身的信息密度已经够了）
- 信息表格化（配料/营养/贮存天然是表格）

## token 骨架

```css
:root {
  --bg:      #FFFFFF;
  --fg:      #141414;
  --muted:   #6E6A66;
  --line:    #E3E0DC;
  --accent:  #C8321E;   /* 辣红 / 食欲色，全站唯一高饱和色 */
  --bg-soft: #F7F5F3;

  --sans: "Inter", "PingFang SC", "Microsoft YaHei", sans-serif;
  --mono: "JetBrains Mono", ui-monospace, Consolas, monospace;  /* 规格数字 */

  --radius: 2px;        /* 接近直角 */
  --shadow: none;       /* 用 1px 线代替 */
  --measure: 1100px;
}
```

## 骨架片段

```html
<section class="hero">
  <h1 class="product-name">手撕兔</h1>          <!-- 超大，字重 800+ -->
  <p  class="claim">先卤后烤，按肌理手撕</p>       <!-- 一句话工艺，非形容词 -->
  <div class="price-row">
    <span class="spec mono">550g</span>
    <span class="price mono">¥58</span>
  </div>
  <a class="cta" href="…">立即购买</a>            <!-- 整页唯一主动作 -->
</section>

<figure class="product-shot">…</figure>          <!-- 产品图，非氛围图 -->

<section class="spec-table">                     <!-- 信息表格化 -->
  <table>… 口味 / 净含量 / 保质期 / 贮存条件 …</table>
</section>

<section class="compliance">                     <!-- ⚠️ 不可折叠 -->
  品名 · 配料表 · 净含量 · 保质期 · 贮存 · 生产者 · SC 编号 · 过敏原 · 食用方法 · 发货/冷链
</section>
```

## 必有

- 单一高饱和食欲色（**只一个**）
- 等宽数字（价格与规格必须对齐）
- **合规区完整可见**：不可折叠、不可隐藏、字号 ≥12px
- 主 CTA 唯一；线下门店若存在，降级为信息（不给并列按钮）

## never（法律红线与视觉红线）

- 装饰性纹样：云纹 / 烫金 / 插画 / 印章纹样 ⚠️ **国潮特产默认陷阱**
- 超过一个高饱和色
- 圆角 > 4px
- 把合规信息折叠、隐藏或缩到 <12px
- 用氛围大图替代产品图
- **疾病预防或治疗功能宣称**（"健胃""抗菌""预防流感"）——食品广告违规
- **极限词**：最 / 第一 / 国家级 / 顶级
- **编造评价与销量**（一条都不行）

## 常见误用

| 误用 | 后果 | 修正 |
|---|---|---|
| 抄品类百科的食疗功效 | **违法** | 百科能写，商品页不能写。全部删除 |
| 上国潮纹样"显得有文化" | 与"标签"语法冲突，且极易撞车 | 零装饰，靠品名与数字的尺度制造冲击 |
| 价格写"58 元起" | 诱导且信息不实 | 每个规格一个确切价 |
| 编 5 条好评"增加可信度" | 违规 + 一旦被发现信任全毁 | 留空并用 `[待填]` 标记；或接真实评价系统 |
| 合规信息放页脚小字 | 违规 | 独立成区，正文级字号 |
