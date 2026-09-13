# Third-Party Notices

本仓库**不分发**以下项目的任何代码或数据，仅在文档中引用其方法学，或在运行时以外部命令方式**可选调用**。
下列信息用于致谢与溯源，许可证以各项目仓库当前声明为准。

## 方法学引用

| 项目 | 作者 | 许可证 | 本仓库如何使用 |
|---|---|---|---|
| [grill-me](https://github.com/julianoczkowski/designer-skills) | julianoczkowski | 见仓库 | 借鉴「一次一问 + 给推荐答案 + 确认」的决策树结构，用于本 skill 的 Phase 0（Grill）。本仓库只实现自己的 9 支决策树（`intake.md`），未复制其文本。 |
| [game-lab](https://github.com/XanthanL/game-lab) | XanthanL | 见仓库 | 其 `data-style` 约 70 种可切换皮肤被列为 `referencePool` 的灵感来源。本 skill 明确要求「布局层也要跟着变」，与只换皮肤层的做法不同。 |

## 可选调用的外部工具（运行时按需，非依赖、非分发）

| 项目 | 作者 | 许可证 | 用途 |
|---|---|---|---|
| [ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | nextlevelbuilder | MIT | 行业推理规则 + 调色板，用于交叉验证 G3 的 token 输出 |
| [awesome-design-skills (TypeUI)](https://github.com/bergside/awesome-design-skills) | bergside | MIT | 本地 spec 不足时 `npx typeui.sh pull <slug>` 拉取完整风格 spec（67 种） |
| [hue](https://github.com/dominikmartn/hue) | dominikmartn | MIT | 已有品牌资产时，反抽 token 的旁路 |

## 运行时依赖（由用户自行安装）

| 包 | 许可证 | 用途 |
|---|---|---|
| [pypdf](https://github.com/py-pdf/pypdf) | BSD-3-Clause | PDF 文本与图片提取 |
| [Pillow](https://github.com/python-pillow/Pillow) | MIT-CMU | 图片真实编码格式校验与重编码 |
| [python-docx](https://github.com/python-openxml/python-docx) | MIT | .docx 文本与内嵌图片提取 |
| [openpyxl](https://foss.heptapod.net/openpyxl/openpyxl) | MIT | .xlsx / .csv 读取 |
| [python-pptx](https://github.com/scanny/python-pptx) | MIT | .pptx 文本与图片提取 |
| [ffmpeg](https://ffmpeg.org/) | LGPL / GPL（视构建） | 视频抽帧、音频转码（可选） |

## 示例素材

`examples/vivian-peng-portfolio/assets/` 中的作品图片**版权归艺术家本人所有**，仅用于本地演示，**未纳入版本控制**（见 `.gitignore`）。该目录需从原始画册自行提取后才会生成，详见 `examples/README.md`。

`examples/` 下其余示例（咖啡店 / 自贡手撕兔）为虚构内容，仅作演示。
