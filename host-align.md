# Host Align — 宿主站对齐与嵌入规程

> **当交付形态 = 「嵌入已有站点的某个路由」时必读。**（交付形态 3 选 1 见 `intake.md` B0）
> 本次真实教训：内容是从零做的，但站是斜靠在一个已有主站上的（`/artists/vivienne-peng`）。
> 用户先后三次要求「统一导航栏」「统一底栏」「要中英双语」——**这三件本该在第一次交付就做完**。

## 铁律

1. **嵌入 = 服从宿主，不是并置两套设计语言。** 明令禁止在宿主站里引入第二套色板 / 字体 / 圆角 / 动效曲线。
2. **顶栏与底栏是"同构"，不是"相似"。** 字标、栏目组、固定行为、滚动态、移动端抽屉、底栏的标语/版权/地点/colophon —— 逐项对齐，包括文案。
3. **宿主令牌优先于本 skill 的风格锚点。** 宿主已有 `--accent: #B33A2A` 时，不许用锚点里的相近色代替；锚点只决定**布局原型与整体气质**，颜色服从宿主。
4. **新增，不改。** 数据用新模块，渲染组件用**分支**（有档案走新，没有走旧），不改宿主现有实体的数据与行为。
5. **不许静默影响其他路由。** 改公共组件前先确认它被谁用；必要时只加可选分支，保持默认路径行为不变。
6. **宿主技术栈优先。** 宿主是 Next 就在 Next 里落地，不要在页面里塞第二套构建链。
   此时 `techstack.md` 的 Phase 1.5 **退化为「确认宿主栈 + 说明本页如何在其内落地」**（`pick_stack.py --host embedded --host-stack <宿主>`），不做重新选型。
   字体同理：`styles/fonts.json` 的锚点搭配会被宿主字体覆盖 —— 嵌入时 `--font-display` 用宿主的那一款，而不是锚点默认的。

---

## 第 1 步 · 采集宿主令牌（先读，别猜）

按框架找这几类文件，**逐个读，把值抄进 `design-system/HOST.md`**：

| 框架 | 令牌在哪 | 组件在哪 |
|---|---|---|
| Next + Tailwind | `tailwind.config.{js,ts}`（theme.extend.colors/fontFamily）、`src/app/globals.css`（`:root` 变量、`@layer components`） | `src/components/*.tsx`（Nav / Footer / LanguageSwitcher） |
| Astro | `src/styles/*.css`、`astro.config.mjs` | `src/layouts/*.astro`、`src/components/*.astro` |
| Vite / 纯静态 | `assets/*.css`（找 `:root{` 与 `[data-style=]`） | 手写 HTML 片段 |
| 只有线上站 | 抓 `<link rel=stylesheet>` → 拉 CSS → 搜 `:root` | 抓 DOM 结构抄骨架 |

必须采到的项：

```
色板      --bg / --fg / --muted / --line / --accent（含精确 hex，不用"差不多"）
字体      sans / serif / mono 的完整字体栈（含中文回退）
字阶      各级 font-size 与行高
间距      间距栅格与主容器 max-width（measure）
圆角      各档 radius
动效      transition duration / easing 曲线
修饰类    .archive-text / .diagonal-line / .prose-zh 等语义工具类的定义
```

⚠️ 本 skill 记忆里的「145deg」曾与宿主实际组件值（**135deg**）不符 —— 那是转场动效的参数，
被误当成组件角度。**一切以读取到的源码为准，不以记忆或印象为准。**

## 第 2 步 · 顶栏 / 底栏同构

从宿主的 `GlobalNav` / `SiteFooter`（或等价物）**逐项搬**：

- 顶栏：字标文字与字号、栏目清单（含顺序与中英文）、`fixed` + 滚动态阈值与背景/模糊/发丝边、当前页高亮方式、语言切换器（胶囊开关的圆点位置与标签）、移动端抽屉（编号、遮罩、Esc、锁滚动）
- 底栏：字标、标语、版权年份区间、地点行、colophon 署名与链接、装饰层（角度与透明度）

**链接要指向宿主的真实地址**（`getAbsoluteUrl` / `CNAME` 里的域名），不要写 `#`。

## 第 3 步 · 语言

宿主双语 → 新页面**必须双语**，且**复用宿主档案里的既有译文**，不另写一份
（同一个人在两个站上出现两种自我介绍是最典型的一致性事故）。

宿主若用 `useI18n` / context，优先沿用；宿主是静态站时按本 skill 的静态方案做：
`.i18n` 节点挂 `data-en` / `data-zh`，切换时遍历替换，同步 `<html lang>` / `<title>` / `localStorage`，
并在 `<head>` 前置一段读缓存的脚本**避免首屏语言闪烁**。

## 第 4 步 · 嵌入路由

```tsx
// 1) 新增数据模块（不塞进宿主已有的 data.ts）
src/content/artists/<slug>.json      // 或 src/lib/<feature>Profile.ts
// 2) 渲染组件做分支，默认路径行为不变
{profile ? <NewProfileView … /> : <LegacyArchiveView … />}
// 3) metadata 也改（title / description 用新内容的真实摘要）
```

**回归检查**：宿主里**其他**实体（本次是另一位艺术家）必须仍走旧路径，行为完全不变。

## 第 5 步 · 素材落地

把资产复制进宿主自己的 public 目录（`public/images/<feature>/<slug>/`），不要跨项目引用
另一个项目的 `assets/`。复制后重跑一次 `scripts/verify_assets.py`。

## 第 6 步 · 验证

- [ ] `npx tsc --noEmit` exit 0（宿主是 TS 项目时）
- [ ] 宿主能起 dev 时抓页面，核对：顶栏字标 / 栏目数 / 底栏标语 / 语言切换器 / 强调色 hex / 组件角度
- [ ] 宿主 **起不了 dev** 时（本环境 `next/font/google` 会因离线抓字体失败），
      明确告知用户「这是环境限制，非改动引入」，并给出可自行验证的命令，**不要假装验证过**
- [ ] 其他实体路径回归正常

## 输出契约

- [ ] `design-system/HOST.md` —— 宿主令牌原文（含来源文件路径，便于别人复核）
- [ ] 顶栏 / 底栏同构清单逐条打勾
- [ ] 语言策略与宿主一致，译文复用宿主档案
- [ ] 新增文件清单 + 「宿主原有实体未受影响」的说明
