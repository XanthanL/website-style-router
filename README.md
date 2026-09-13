# Website Style Router

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Scripts: zero dependency](https://img.shields.io/badge/scripts-zero%20dependency-brightgreen.svg)](scripts/)
[![Version](https://img.shields.io/badge/version-0.9.2-informational.svg)](CHANGELOG.md)

**English** · [简体中文](README.zh-CN.md)

> A portable [Agent Skill](https://agentskills.io/specification) that turns content you already have — a PDF, a folder of photos, a spreadsheet, a video, an existing site, or one sentence — into a website that actually builds.

It does not answer "what should it look like". It answers **in what order** the decisions must be made: fix the source first, then the delivery shape, then cut the option space, and only then talk about style. Almost every styling tool on the market (TypeUI, Curio, uipro) does only that last step.

---

## The problem

Hand content to an AI and ask for a site. The most common failure is not "it looks bad" — it is that ten different requests come back as ten copies of the same site.

| Failure | What this skill does instead |
|---|---|
| Picking one style from a menu → output converges on the average = instant "AI look" | No menu selection. **Constraint elimination + two-stage narrowing** (40 anchors → 11 families → 1 anchor) |
| Swapping colors while the layout stays the same template | Every anchor declares `layout` **and** `axis`; **style must drive layout**, not only color |
| Every request gets the same skeleton (Astro + `src/pages/…`) | **Phase 1.5 tech-stack selection**: eliminate and rank by requirements (page count, interaction, maintainer, data source, host, i18n, rendering, perf) → `tech-stack.md` with 3 falsifiable conditions |
| All 40 anchors ship `Inter, -apple-system…` | **Font-pairing registry** (`styles/fonts.json`): one named display × body pair per anchor, **display unique across the whole registry**, emitted into `--font-display`/`--font-body` and verified by `audit_tokens.py` F6 |
| Different projects, same shape, different copy | **Anti-sameness gates, per-site and across a batch**: ≥3 structural visual signatures per site; a batch ledger (`scripts/ledger.py`) pre-checks anchors, typefaces, surfaces, variants and families; `audit_tokens.py --batch` verifies the delivered set |
| Five sites side by side: five white backgrounds, identical type scales | **Surface presets** (7 background tones, two of them dark) × **scale variant axes** (original / tightened / relaxed / expressive). Reusing an anchor requires changing the combination. Combination space: 40 × 4 × 7 × 4 |
| Reusing an anchor runs the font registry dry | **Family-level spare pools** `_familyPools`: 11 families × 3 pairs, zero overlap with the 40 primary pairs |
| Always a single `index`, no room for detail | **Page granularity** is *computed*: `pick_pages.py` reads content facts (entry count, depth, must a single item be shareable) → `single` / `master-detail` / `multi-page`; `audit_tokens.py --site` F14 checks the declaration against the real page count |
| Long pages you can only scroll to the bottom | **In-page navigation**: level from content (`none` / `anchor-jump` / `sticky-toc` / `section-rail`), form from layout; F15 verifies anchors are **reachable** (including broken-link detection) |
| Copy invented out of nothing | Mandatory **per-item traceability** (`p12 · "original line"`). Anything that cannot be traced back gets deleted |
| Image paths resolve, validation passes, page renders empty | Validate the real **encoding** with PIL (JPEG2000 masquerading as `.png` is a bug that was actually hit) |
| Embedding into an existing site wrecks the host's design | `host-align.md`: **isomorphic, not similar** — host tokens win |

---

## Install

The whole thing is one folder. Drop it into any agent's skills directory; every path is relative to the skill root and nothing depends on host-specific tooling.

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

Then probe the environment once — it tells you what this machine can and cannot extract:

```bash
python scripts/check_env.py
```

## Quick start

Describe what you want and hand over the material:

```
Use website-style-router to turn this PDF into a website that suits it.
(attached: the source PDF)
```

The pipeline runs end to end and **stops for your confirmation exactly once**, at "lock-in":

```
-1   Source & delivery shape → extract, trace, validate         [gate G-1]
 0   Grill (intent)          → one question at a time           [gate G0]
 1   Constraint filtering    → cut ~80% of the space            [gate G1]
1.5  Tech-stack selection    → requirements → stack             [gate G1.5]
1.6  Batch de-duplication    → ledger check, swap combination   [gate G1.6]
1.7  Granularity & nav       → content → pages / jump targets   [gate G1.7]
 2   Lock-in ★               → stack+family+anchor+layout+font  [gate G2 · only mandatory human confirm]
 3   Tokens                  → MASTER.md                        [gate G3]
 4   Build / embed           → buildable output                 [gate G4]
 5   Acceptance              → checklist, item by item          [gate G5]
 6   Follow-up               → proactively walk 6 items         [gate G6]
```

**Phase 1.7 is computed, not asked.** Three blocks of shallow content → `single`. Many entries with depth → `master-detail`. Long pages get anchors, short pages do not. `pick_pages.py` prints the level, the reasons, the levels it rejected, and the falsification conditions — every step is auditable. **"Don't split" and "don't add a table of contents" are themselves valid verdicts**, not omissions.

Outputs are fixed: `source-map.md`, `references.md`, `tech-stack.md`, `intent-summary.md`, `content-profile.md`, `design-system/MASTER.md` (plus `HOST.md` when embedding), the batch state file `.style-ledger.json`, and a site that builds.

---

## What's in the box

Everything enumerable lives in a JSON registry, not in prose — prose invites the agent to improvise, and improvisation converges on the average.

| Asset | File | Size |
|---|---|---|
| Style anchors | `styles/index.json` | 40, each with `layout` / `axis` / `imagePolicy` / `iconPolicy` / `density` / `when` / `never` |
| Font pairings | `styles/fonts.json` | 40 named display × body pairs, **display unique repo-wide**, with mono, CJK fallback and loading strategy |
| Family spare pools | `styles/fonts.json` → `_familyPools` | 33 pairs (11 families × 3) for rotating a reused anchor |
| Surface presets | `styles/signatures.json` → `_surfacePresets` | 7 tones: `white` / `paper` / `tint` / `stone` / `slate` / `ink` / `deep` — two of them dark |
| Scale variant axes | `styles/signatures.json` → `_variantAxes` | 4: original / tightened / relaxed / expressive, shifting type ratio, base size, spacing unit and radius with clamps |
| Candidate stacks | `techstack.md` + `scripts/pick_stack.py` | 7: plain-html / astro / eleventy / vite / next / nuxt / hugo |
| Style families | `styles/families.md` | 11 — the narrowing middle layer, chosen by *content leverage / conversion goal / density need*, never by industry |
| Full specs | `styles/specs/` | 6 ready-to-paste token skeletons |
| IA archetypes | `architectures/` | 4: portfolio / narrative / directory / conversion, each with a default granularity and default in-page nav (overridable by content) |
| Content dimensions | `architectures/pagination.json` + `scripts/pick_pages.py` | granularity × in-page nav; thresholds live in the registry, scripts never hard-code them |
| Reference pool | `referencePool` | 20, including game-lab's 70 switchable skins |

When a local spec is missing, `_specFallback` degrades in three tiers, the middle one pulling from `npx typeui.sh pull <slug>` (67 styles).

**13 input-source playbooks** — PDF / image / docx / xlsx+csv / pptx / md+txt / video / audio / existing site / reference site / plain text / mixed / no input — each with its own extraction path, fallback and known traps (see `source.md`). When something cannot be handled it says so: no OCR means scanned PDFs need text from you; no ASR means video narration needs subtitles from you. `check_env.py` tells you up front.

---

## Commands

Four deterministic scripts decide things (no LLM guessing), four check things:

```bash
python scripts/pick_stack.py --pages 20 --interactive low --maintainer non-tech
                                                    # requirements → stack, with reasons
python scripts/pick_pages.py --entries 17 --depth deep --shareable --ia portfolio
                                                    # granularity + in-page nav, with reasons and falsifiers
python scripts/emit_tokens.py --anchor provisions-label --surface paper --variant b
                                                    # tokens are generated, never hand-written
python scripts/audit_tokens.py <MASTER.md>          # per-site numeric audit      (F1–F6, F10)
python scripts/audit_tokens.py --site <site-dir>    # declaration vs. artifact    (F14–F20)
python scripts/audit_tokens.py --batch <workspace>  # cross-site diversity        (F11)
python scripts/ledger.py    --check / --commit / --report    # batch ledger
python scripts/validate_skill.py                    # repo self-check
```

---

## Granularity in practice

Granularity is **computed**, so the verdict tracks the content:

| Content shape | Granularity | In-page nav | Why |
|---|---|---|---|
| 3 blocks, shallow | `single` | `none` | Splitting or adding a ToC would be a downgrade |
| One page, three lookup blocks (specs / prep / FAQ) | `single` | `anchor-jump` | One page is enough, but readers jump between sections |
| 17 items, each must be shareable | `master-detail` | `none` | Index plus one detail page per item |

---

## Requirements

- **Python 3.10+** — `pypdf` and `Pillow` required; `python-docx`, `openpyxl`, `python-pptx` on demand by input format
- **Node 18+** — only if Phase 1.5 picks astro / next / nuxt / eleventy / vite. Pick `plain-html` and the output has zero dependencies
- **ffmpeg** — optional, for video frame extraction
- External tools (uipro / typeui / hue) are all optional

## Self-check

After changing the skill itself, run both. Neither needs third-party packages, so both can go straight into CI:

```bash
python scripts/validate_skill.py      # spec + internal consistency — ERROR 0 to pass
```

Every criterion in this skill was built to one rule: **a criterion that always returns PASS is the same as no criterion.** Each is exercised against a known violation to confirm it actually fires, and against compliant input to confirm it does not produce false alarms — a positive test proves "no false alarms", never "it can actually fail".

Two examples of why that discipline matters:

- F16 (fields must be rendered) initially accepted `forEach` as "rendered". A lightbox script contained `images.forEach(...)`, so "the script iterated over them" masked "the template only rendered the first image" — **not one case fired**. It now accepts only `map` / `flatMap`.
- Every criterion also carries a **false-alarm guard** (compliant input must pass). F17/F19/F20 only fire on deliveries that declare a source map, a host, or a stack, so a purpose-built compliant fixture covers their positive path.

---

## Repository layout

```
website-style-router/
├── SKILL.md                  # entry point: 34-rule index + phase gates + file map (agent reads this; ~4.1k tokens)
├── CONCEPTS.md               # why it is designed this way          (for humans)
├── TUTORIAL.md               # how to use it, how to change it      (for humans)
├── decide.md                 # decision rights A/B/C/D + question budget
├── source.md                 # Phase -1: the 13 input-source playbooks
├── intake.md                 # Phase 0/1: Grill decision trees + constraint filtering
├── techstack.md              # Phase 1.5: tech-stack selection
├── host-align.md             # Phase 4: alignment rules when embedding
├── layouts.md                # 5 layout archetypes + axis + visual signatures + nav forms
├── typography.md             # typographic numeric system + font pairings
├── checklist.md              # pre-delivery acceptance
├── references/               # on-demand layer for SKILL.md: rules.md (full 34 rules) · architecture.md · filemap.md
├── architectures/            # IA: 4 archetypes + pagination.json + granularity.md
├── styles/                   # index.json, families.md, signatures.json, fonts.json, specs/
└── scripts/                  # check_env · pick_stack · pick_pages · extract_source ·
                              # extract_pdf_assets · verify_assets · emit_tokens ·
                              # audit_tokens · ledger · validate_skill
```


## Documentation

| Document | Answers |
|---|---|
| [`CONCEPTS.md`](CONCEPTS.md) | **Why it is designed this way** — three real failure modes, the four-layer structure, glossary, core insight, three meta-rules |
| [`TUTORIAL.md`](TUTORIAL.md) | **How to use and modify it** — full walkthrough, command manual, eight customization recipes, troubleshooting, batch workflow |
| [`SKILL.md`](SKILL.md) | The 34 rules and phase gates — what the agent actually reads |

> **Note:** the deep documentation is currently Chinese-first; the registries (`*.json`) and the code are self-describing and language-neutral. Translations are welcome — see [`CONCEPTS.md`](CONCEPTS.md) for the vocabulary, so translated docs stay consistent with the code.

## Credits

Built on these MIT projects, listed in [`THIRD-PARTY.md`](THIRD-PARTY.md): ui-ux-pro-max-skill, awesome-design-skills (TypeUI), hue, designer-skills (grill-me), game-lab. The Grill mechanic ("one question at a time, with a recommended answer") follows grill-me's decision-tree structure.

## License

[MIT](LICENSE) © 2026 XanthanL
