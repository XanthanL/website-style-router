# Website Style Router

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Scripts: zero dependency](https://img.shields.io/badge/scripts-zero%20dependency-brightgreen.svg)](scripts/)
[![Version](https://img.shields.io/badge/version-0.9.2-informational.svg)](CHANGELOG.md)

**English** · [简体中文](README.zh-CN.md)

> Hand it content you already have — a PDF, a folder of photos, a spreadsheet, a video, an existing site, or one sentence — and get back a website that builds, in a style that fits *that* content.

A portable [Agent Skill](https://agentskills.io/specification): one folder, no service, no API key, no build step of its own.

---

## What it does for you

| You have probably seen this | What happens instead |
|---|---|
| Ten requests come back as ten copies of the same site | Style is chosen by **elimination** (40 anchors → 11 families → 1), never from a menu. Menus converge on the average, and the average is exactly what people call "AI look". |
| Every project gets the same skeleton (Astro + `src/pages/…`) | The **tech stack is derived from your requirements** — page count, interaction, maintainer, data source, host. Plain HTML is a first-class answer. |
| One `index` page forever; long pages you can only scroll to the bottom | Page count and in-page navigation are **computed from your content**. Three shallow blocks stay on one page; seventeen shareable items get detail pages. |
| Text that sounds plausible but was never in your source | Every line must be **traceable** back to the source (`p12 · "original line"`). Anything untraceable gets deleted. |

So it is less "pick a look" and more **get the order right**: fix the source first, then the delivery shape, then cut down the option space, and only then talk about style. Almost every styling tool on the market does only that last step.

---

## Install

```bash
npx skills add XanthanL/website-style-router
```

Or just clone it and drop the folder into your agent's skills directory — every path is relative to the skill root, and nothing depends on host-specific tooling:

```bash
git clone https://github.com/XanthanL/website-style-router.git
```

| Agent | Location |
|---|---|
| Claude Code | `~/.claude/skills/website-style-router/` or `.claude/skills/website-style-router/` in your project |
| Codex | `.codex/skills/website-style-router/` |
| Cursor | `.cursor/skills/website-style-router/` |
| WorkBuddy / CodeBuddy | `~/.workbuddy/skills/website-style-router/` |
| Anything else | Any convention that expects a directory containing `SKILL.md` |

Then probe your environment once. It tells you what this machine can and cannot extract, before you hand it anything:

```bash
python scripts/check_env.py
```

## How to use

Describe what you want and hand over the material:

```
Use website-style-router to turn this PDF into a website that suits it.
(attached: the source PDF)
```

That's it. It walks the pipeline end to end and **stops for your confirmation exactly once**, at lock-in — stack + family + anchor + layout + fonts. Everything before that point is derived from your content; everything after it is execution.

What lands on disk: `source-map.md`, `references.md`, `tech-stack.md`, `intent-summary.md`, `content-profile.md`, `design-system/MASTER.md` (plus `HOST.md` when embedding into an existing site), and a site that builds.

---

## Full documentation

The README stops here on purpose. Everything deeper lives in these:

| Document | Answers |
|---|---|
| [`CONCEPTS.md`](CONCEPTS.md) | **Why it is built this way** — the real failure modes, the four-layer structure, glossary, four meta-rules |
| [`TUTORIAL.md`](TUTORIAL.md) | **How to use and modify it** — phase-by-phase walkthrough, full command manual, eight customization recipes, troubleshooting, batch workflow, and the full inventory of what ships in the box |
| [`SKILL.md`](SKILL.md) | The 34 rules and phase gates — what the agent actually reads |
| [`references/filemap.md`](references/filemap.md) | Complete file map with per-file responsibilities |

> **Note:** the deep documentation is currently Chinese-first; the JSON registries and the code are language-neutral. Translations are welcome — [`CONCEPTS.md`](CONCEPTS.md) §10 fixes the vocabulary, so translated docs stay consistent with the code.

## Requirements

- **Python 3.10+** — `pypdf` and `Pillow` required; `python-docx`, `openpyxl`, `python-pptx` on demand by input format
- **Node 18+** — only if the selected stack is astro / next / nuxt / eleventy / vite. Pick `plain-html` and the output has zero dependencies
- **ffmpeg** — optional, for video frame extraction
- External tools (uipro / typeui / hue) are all optional

Changed the skill itself? Run `python scripts/validate_skill.py` — `ERROR 0` to pass, no third-party packages needed, so it drops straight into CI.

## Credits

Built on these MIT projects, listed in [`THIRD-PARTY.md`](THIRD-PARTY.md): ui-ux-pro-max-skill, awesome-design-skills (TypeUI), hue, designer-skills (grill-me), game-lab. The Grill mechanic ("one question at a time, with a recommended answer") follows grill-me's decision-tree structure.

## License

[MIT](LICENSE) © 2026 XanthanL
