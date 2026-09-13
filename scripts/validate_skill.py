#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""校验本 skill 是否符合 Agent Skills 规范，且内部引用自洽。

用法:
    python validate_skill.py [skill_dir]      # 默认取脚本上一级目录
    python validate_skill.py --json

检查项（任一 ERROR → 退出码 1；WARN 不影响退出码）：

  A. frontmatter（规范符合性）
     A1 SKILL.md 首行即 `---`，且有闭合的 `---`
     A2 `name` 存在、kebab-case、<=64 字符、与本 skill 目录名一致
     A3 `description` 存在、<=1024 字符
     A4 `compatibility`（若有）<=500 字符
     A5 顶层键只允许规范定义的 6 个：name / description / license / compatibility
        / metadata / allowed-tools —— 非规范顶层键会让严格解析器直接报错
     A6 `metadata` 必须是 map（不是标量或列表）

  B. 结构
     B1 SKILL.md 行数 < 500（规范建议，超出应拆到独立文件）
     B2 声明了 `license`

  C. 引用自洽
     C1 SKILL.md 正文里的每个相对链接目标都存在（含目录）
     C2 各文档互相引用的 `xxx.md` / `xxx.py` / `xxx.json` 都能解析
        —— 本 skill 的「产出物」名（见 ARTIFACTS）豁免，它们不该在仓库里
     C3 报告"存在但没有任何文档提到"的运行时文件（孤儿文件）

  D. 仓库卫生
     D1 无 node_modules / dist / .astro / .next / __pycache__
     D2 无一次性 `_*.py` 脚本
     D3 无 .pdf/.docx/.pptx/.xlsx 等用户源材料

  E. 注册表自洽（跨文件一致性，专抓"文档互相矛盾"）
     E1 styles/index.json 里每个锚点的 layout / family / axis 都必须落在
        layouts.md 的定义域内（5 个布局原型、3 档中轴）与 families 列表内；缺 when/never 则 WARN
     E2 styles/specs/<slug>.md 必须有同名锚点，否则是孤儿 spec
     E3 examples/*/design-system/MASTER.md 必须声明 `--axis`，且声明的锚点要存在

  F. 设计参数签名与产出审计
     F1 styles/signatures.json 存在且可解析（emit_tokens.py 的输入）
     F2 `_legend` 覆盖全部 15 个参数字段（人读得懂才敢改）
     F3 签名覆盖 index.json 的全部锚点，不多不少
     F4 11 个族都有默认值
     F5 每个签名的字段合法（枚举 / 量纲 / 区间）
     F6 每个 spec 都有对应签名（否则 emit_tokens 合并时会缺一半）
     F7 examples/*/MASTER.md 必须通过 audit_tokens.py（审美数值审计 F 级为 0）

  G. 字体搭配 / 技术栈 / 反同质化基础设施（v0.7 起，v0.8 扩展）
     F8 styles/fonts.json 覆盖全部锚点与族、字段合法、mono/cjk 引用有效、
        **display 字体全库唯一**（R3）、display≠body（R2）、首族非通用关键字（R1）
     F9 techstack.md（Phase 1.5 阶段文档）与 scripts/pick_stack.py 存在；
        **页面粒度维度的载体同样必须存在**：architectures/granularity.md（判断框架）、
        architectures/pagination.json（阈值注册表）、scripts/pick_pages.py（确定性推荐）
     F10 底色维度：_surfacePresets ≥3 档且字段合法；锚点全部有 surface 且 ≥3 档在用
     F11 尺度变体轴：_variantAxes ≥2 条，偏移量在安全范围内
     F12 族级字体备用池：覆盖 11 族、每族 ≥3 对、display 全库唯一
     F13 反同质化执行工具存在（scripts/ledger.py / scripts/audit_tokens.py）

  H. 页面粒度与页内导航（v0.9）
     H1 四个 IA 文档都声明了「默认粒度」与「默认页内导航」，且与
        architectures/pagination.json 的 iaDefaults 一致（抓文档漂移）
     H2 examples/*/ 逐个跑 audit_tokens.py --site，必须 F 级 0
        （页面文件数与声明的粒度一致、页内导航锚点可达）
     H3 中轴档位供给：每档 axis ≥3 个锚点、跨 ≥2 个布局原型、跨 ≥3 个族。
        抓的是**维度没正交**：某档 100% 绑定单一布局时，选它就等于选布局，
        批次里还会变成必经点（v0.9 实测：split 只有 3 个锚点且全为 split-narrative）
     H4 铁律「索引 ↔ references/rules.md 全文」一致：编号从 1 连续、集合相同、
        同编号是同一条。v0.9.2 为省 token 把全文搬走后引入的回归风险 ——
        索引删一条而全文还在时，agent 按索引自检会**静默漏检**

  判据本身也要被测：`python testing/negative_tests.py` 给每条判据植入一处违规并断言被抓到。

无第三方依赖（自带极简 YAML 子集解析器，够用于本 frontmatter）。
"""
import json
import os
import re
import sys

STANDARD_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
REF_RE = re.compile(r"`([^`\n]+\.(?:md|json|py|css))`")
JUNK_DIRS = {"node_modules", "dist", ".astro", ".next", "__pycache__", ".git"}
SRC_EXT = (".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls")

# 这些名字是本 skill 的「产出物」，出现在文档里是正常的，**不该**存在于仓库中。
# 不做这个白名单，校验器会把每一处输出契约都误报成"引用不存在"。
# 本地开发资产目录：不随仓库发布（见 .gitignore）。
# 干净克隆里指向它们的引用**必然**悬空，那是预期状态不是断链，故 C2 降级为 info 而非 warn。
# 代价：写错名字时（如 `testing/foo.py`）也只是 info —— 可接受的取舍，
# 因为这几个目录本身不发布，发布物不会因为名字写错而坏掉。
LOCAL_ONLY_DIRS = {"docs", "testing", "examples"}
# 部分文档里写的是裸文件名（`negative_tests.py`）而不是带目录的路径，
# 裸名没有目录前缀可判，只能按名登记。**往 testing/ 加文件时，若文档用裸名引用，需同步这里。**
LOCAL_ONLY_BASENAMES = {"negative_tests.py", "test-cases.md"}

ARTIFACTS = {
    "content-profile.md", "intent-summary.md", "source-map.md", "references.md",
    "MASTER.md", "HOST.md", "tech-stack.md", "text.md", "manifest.json", "_WARNINGS.txt",
    "globals.css", "works.json", "package.json", "package-lock.json", "DECISION.md",
    ".style-ledger.json",
    # tokens.css 是 emit_tokens.py 写进**产出站点**的，skill 仓库里本就不该有。
    # 之前一直没被报，只是因为 examples/ 里恰好有同名文件 —— 白名单的潜在缺口，
    # examples/ 一排除就会暴露成 13 条误报。
    "tokens.css",
}

# 可选夹具：用户已明确移除的回归夹具脚本。缺失不算问题 —— 只报告，不告警。
OPTIONAL_FIXTURES = {"make_T07_menu_pdf.py"}

# H3 中轴档位供给下限。中轴是批次多样性判据之一（ledger --report）。
# 某一档供给过薄时它就不再是「一档选择」，而是**必经点**：批次要凑够种类就得踩它，
# 踩它就必然带出同一个布局原型和同一两个族 —— 布局与族的自由度被中轴一起锁死。
# v0.9 实测：split 只有 3 个锚点且全为 split-narrative，5 站批次凑不齐中轴种类。
MIN_AXIS_ANCHORS = 3      # 每档至少几个锚点
MIN_AXIS_LAYOUTS = 2      # 每档至少跨几个布局原型
MIN_AXIS_FAMILIES = 3     # 每档至少跨几个族

# H4 铁律「索引 ↔ 全文」一致性（v0.9.2 引入：铁律全文搬到 references/rules.md 省 token 后）。
# 拆分引入的新风险：索引与全文变成两个文件，改一处忘另一处 —— 索引删了一条而全文还在，
# agent 按索引自检就会**静默漏检**，且没有任何脚本会报错（这正是 v0.9.1 审出的「欠账」形态）。
# 只看「条数相同」不够：编号是外部引用锚点（testing/test-cases.md / CONCEPTS.md /
# 脚本报错文案都按号引用），跳号或错位会让引用指向另一条。所以查三件事：
#   ① 两边编号都从 1 连续到 N；② 编号集合完全相同；③ 同一编号两边是同一条。
RULES_REL = "references/rules.md"

ERRORS, WARNS, INFOS = [], [], []


def err(check, msg):
    ERRORS.append(f"[{check}] {msg}")


def warn(check, msg):
    WARNS.append(f"[{check}] {msg}")


def info(msg):
    INFOS.append(msg)


# ---------------------------------------------------------------- YAML 子集
def parse_block(lines, i, indent):
    """解析一个缩进块，返回 (value, next_index)。支持 map 与字符串列表。"""
    if i < len(lines) and lines[i].strip().startswith("- "):
        items = []
        while i < len(lines):
            raw = lines[i]
            if not raw.strip():
                i += 1
                continue
            cur = len(raw) - len(raw.lstrip())
            if cur < indent or not raw.strip().startswith("- "):
                break
            items.append(raw.strip()[2:].strip().strip('"').strip("'"))
            i += 1
        return items, i
    out = {}
    while i < len(lines):
        raw = lines[i]
        if not raw.strip():
            i += 1
            continue
        cur = len(raw) - len(raw.lstrip())
        if cur < indent:
            break
        m = re.match(r"^([A-Za-z][\w.\-]*):\s*(.*)$", raw.strip())
        if not m:
            break
        key, val = m.group(1), m.group(2).strip()
        i += 1
        if val == "":
            j = i
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and (len(lines[j]) - len(lines[j].lstrip())) > cur:
                val, i = parse_block(lines, i, len(lines[j]) - len(lines[j].lstrip()))
        else:
            val = val.strip('"').strip("'")
        out[key] = val
    return out, i


def parse_frontmatter(text):
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None, "首行不是 `---`（frontmatter 必须从第一行开始，前面不能有空行）"
    for k in range(1, len(lines)):
        if lines[k].strip() == "---":
            fm, _ = parse_block(lines[1:k], 0, 0)
            return fm, None
    return None, "没有找到闭合的 `---`"


# ---------------------------------------------------------------- 遍历
def walk_paths(root):
    """列出 root 下所有文件与目录的相对路径。遇到依赖/产物目录只记录、不深入。"""
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        keep = []
        for d in dirnames:
            # .git 与 __pycache__ 是运行时/版本产物，不计入也不深入：
            # 否则本校验器运行自身编译出的 __pycache__ 会被自己判成 D1 错误。
            if d == ".git" or d == "__pycache__":
                continue
            out.append(os.path.join(dirpath, d))
            if d not in JUNK_DIRS:
                keep.append(d)
        dirnames[:] = keep
        for f in filenames:
            out.append(os.path.join(dirpath, f))
    return out


def _in_local_only(target):
    """引用是否指向 `docs/` `testing/` `examples/` 这类不发布的目录（见 LOCAL_ONLY_DIRS）。"""
    parts = [p for p in re.split(r"[\\/]+", target.strip()) if p and p != "."]
    if not parts:
        return False
    if any(p in LOCAL_ONLY_DIRS for p in parts):   # 任意一段命中即可（含裸目录名）
        return True
    return os.path.basename(target) in LOCAL_ONLY_BASENAMES


def _rule_titles(text):
    """从铁律全文抽 {编号: 标题}。行形如 `12. **决策权分明。** 理由……`。

    只取首个加粗句作标题：正文里的 `1.`/`2.` 有序列表（做法步骤）不带加粗，不会被误收。
    """
    out = {}
    for m in re.finditer(r"^(\d+)\.\s+\*\*(.+?)\*\*", text, re.M):
        out[int(m.group(1))] = m.group(2).strip()
    return out


def _index_titles(body):
    """从 SKILL.md 的「## 铁律索引」段抽 {编号: 一句结论}。行形如 `12. 决策权分明。`"""
    seg = re.search(r"^## 铁律索引\b.*?(?=^## |\Z)", body, re.M | re.S)
    if not seg:
        return {}
    out = {}
    for m in re.finditer(r"^(\d+)\.\s+(\S.*?)\s*$", seg.group(0), re.M):
        out[int(m.group(1))] = m.group(2).strip()
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    # 默认取「本脚本所在目录的上一级」，与运行时的 CWD 无关
    default_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    root = os.path.abspath(args[0]) if args else default_root
    skill_md = os.path.join(root, "SKILL.md")
    dirname = os.path.basename(root.rstrip(os.sep))

    if not os.path.exists(skill_md):
        err("A1", f"未找到 {skill_md}")
        return report(root)

    text = open(skill_md, "r", encoding="utf-8").read().replace("\r\n", "\n")

    # ---- A. frontmatter ----
    fm, problem = parse_frontmatter(text)
    if problem:
        err("A1", problem)
        return report(root)
    body = text.split("---", 2)[2]
    info(f"frontmatter 顶层键: {', '.join(fm.keys())}")

    unknown = [k for k in fm if k not in STANDARD_KEYS]
    if unknown:
        err("A5", f"非规范顶层键 {unknown} —— 规范只允许 {sorted(STANDARD_KEYS)}；"
                  f"自定义信息请放进 `metadata`")

    name = str(fm.get("name") or "")
    if not name:
        err("A2", "缺少 `name`")
    else:
        if not NAME_RE.match(name):
            err("A2", f"`name` 必须是 kebab-case（小写字母/数字/连字符）：{name}")
        if len(name) > 64:
            err("A2", f"`name` 超过 64 字符：{len(name)}")
        if name != dirname:
            warn("A2", f"`name`（{name}）与目录名（{dirname}）不一致 —— 目录名才是调用名，建议对齐")

    desc = str(fm.get("description") or "")
    if not desc:
        err("A3", "缺少 `description` —— 它是 agent 决定是否加载本 skill 的唯一依据")
    elif len(desc) > 1024:
        err("A3", f"`description` {len(desc)} 字符，超过 1024")

    compat = fm.get("compatibility")
    if compat and len(str(compat)) > 500:
        err("A4", f"`compatibility` {len(str(compat))} 字符，超过 500")

    meta = fm.get("metadata")
    if meta is not None and not isinstance(meta, dict):
        err("A6", "`metadata` 必须是 map（键值对），不是标量或列表")

    if "license" not in fm:
        warn("B2", "未声明 `license` —— 开源仓库建议显式声明")

    # ---- B. 结构 ----
    nlines = len(text.splitlines())
    if nlines >= 500:
        warn("B1", f"SKILL.md {nlines} 行，>=500；规范建议把细节拆到独立文件")
    info(f"SKILL.md 行数: {nlines}")

    # ---- 清点仓库 ----
    all_rel = [os.path.relpath(p, root).replace(os.sep, "/").rstrip("/") for p in walk_paths(root)]
    files = {r for r in all_rel if os.path.isfile(os.path.join(root, r))}
    dirs = {r for r in all_rel if r not in files}
    basenames = {os.path.basename(r) for r in files}

    # ---- C. 引用自洽 ----
    for m in LINK_RE.finditer(body):
        t = m.group(1).split("#")[0].strip().rstrip("/")
        if not t or t.startswith(("http://", "https://", "mailto:")):
            continue
        if t not in files and t not in dirs:
            err("C1", f"SKILL.md 链接目标不存在: {t}")

    for rel in sorted(files):
        if not rel.endswith(".md"):
            continue
        md = os.path.join(root, rel)
        mroot = os.path.dirname(md)
        c = open(md, "r", encoding="utf-8", errors="replace").read()
        for m in REF_RE.finditer(c):
            t = m.group(1).strip()
            if " " in t:          # 形如 `python make_x.py` / `npx typeui.sh ...`：取末段文件名
                t = t.split()[-1]
            if "*" in t or "<" in t or t.startswith(("http", "/")):
                continue
            if os.path.basename(t) in ARTIFACTS:
                continue          # 本 skill 的产出物，不该在仓库里
            if os.path.basename(t) in OPTIONAL_FIXTURES:
                info(f"{rel} 引用了可选夹具 {t}（用户已移除，不影响交付）")
                continue
            if _in_local_only(t):
                # 本地开发资产：不随仓库发布。干净克隆里必然解析不到，属预期状态。
                # 本机保留了这些目录时（gitignore 只管提交、不管磁盘）会正常命中 basenames，
                # 走不到这里 —— 所以这段不会削弱本机自检。
                info(f"{rel} 引用了本地开发资产 {t}（不随仓库发布）")
                continue
            if os.path.basename(t) in basenames:
                continue          # 仓库里同名文件确实存在（可能不在同目录）
            cands = [os.path.normpath(os.path.join(mroot, t)),
                     os.path.normpath(os.path.join(root, t))]
            if not any(os.path.exists(x) for x in cands):
                warn("C2", f"{rel} 引用了不存在的 {t}")

    # 孤儿运行时文件：examples/、docs/、根目录文件与 .md 都不算
    all_md_text = "".join(open(os.path.join(root, r), "r", encoding="utf-8", errors="replace").read()
                          for r in sorted(files) if r.endswith(".md"))
    for rel in sorted(files):
        if rel.startswith(("examples/", "docs/", ".")) or "/" not in rel or rel.endswith(".md"):
            continue
        if os.path.basename(rel) not in all_md_text:
            warn("C3", f"孤儿文件（没有任何文档提到它）: {rel}")

    # ---- D. 仓库卫生 ----
    for rel in sorted(all_rel):
        parts = rel.split("/")
        for j in JUNK_DIRS - {".git"}:
            if j in parts:
                err("D1", f"仓库里不该有构建产物/依赖目录: {rel}")
                break
    for rel in sorted(files):
        base = os.path.basename(rel)
        if base.startswith("_") and base.endswith(".py"):
            err("D2", f"一次性脚本不应入库: {rel}")
        # testing/ 下的是**有意的测试夹具**（扫描件模拟、合成数据），不是用户源材料
        if base.lower().endswith(SRC_EXT) and not rel.startswith("testing/"):
            err("D3", f"用户源材料不应入库: {rel}")

    # ---- E. 注册表自洽（跨文件一致性）----
    # 这一节是为了抓"文档 A 说的"与"文档 B 说的"互相矛盾——
    # 之前真实发生过：index.json 声明某锚点绑定 split-narrative，而官方示例的
    # content-profile 白纸黑字写着"选 catalog-grid 而非 split-narrative"，站点也是那么做的。
    # 单看任何一个文件都自洽，只有交叉比对才暴露；这类漂移靠人眼审查必然漏。
    reg = None
    style_index = os.path.join(root, "styles", "index.json")
    layouts_md = os.path.join(root, "layouts.md")
    if os.path.exists(style_index) and os.path.exists(layouts_md):
        try:
            reg = json.load(open(style_index, encoding="utf-8"))
        except Exception as e:
            err("E1", f"styles/index.json 无法解析: {e}")
    if reg:
        lay = open(layouts_md, encoding="utf-8", errors="replace").read()
        archetypes = set(re.findall(r"^##\s+\d+\s*·\s*([a-z0-9\-]+)", lay, re.M))
        axes = set(re.findall(r"^\|\s*`(left-rail|center-axis|split)`", lay, re.M))
        fam_ids = {f.get("id") for f in reg.get("families", [])}
        anchors = reg.get("anchors", [])
        slugs = {a.get("slug") for a in anchors}
        if not archetypes:
            warn("E1", "layouts.md 未解析到布局原型（检查 `## N · slug` 标题格式是否被改动）")
        for a in anchors:
            s = a.get("slug")
            if archetypes and a.get("layout") not in archetypes:
                err("E1", f"锚点 {s} 的 layout={a.get('layout')!r} 不在 layouts.md 原型里 {sorted(archetypes)}")
            if fam_ids and a.get("family") not in fam_ids:
                err("E1", f"锚点 {s} 的 family={a.get('family')!r} 不在 index.json 的 families 里")
            if axes and a.get("axis") not in axes:
                err("E1", f"锚点 {s} 的 axis={a.get('axis')!r} 不在 layouts.md 的中轴三档里 {sorted(axes)}")
            if not a.get("when") or not a.get("never"):
                warn("E1", f"锚点 {s} 缺 when 或 never —— 选型靠这两项做命中与排除")

        specs_dir = os.path.join(root, "styles", "specs")
        if os.path.isdir(specs_dir):
            specs = {os.path.splitext(f)[0] for f in os.listdir(specs_dir) if f.endswith(".md")}
            orphan = sorted(specs - slugs)
            if orphan:
                err("E2", f"styles/specs/ 里的 spec 没有同名锚点: {orphan}")

        pool = {r.get("slug") for r in reg.get("referencePool", [])}
        ex_dir = os.path.join(root, "examples")
        if os.path.isdir(ex_dir):
            for name in sorted(os.listdir(ex_dir)):
                m = os.path.join(ex_dir, name, "design-system", "MASTER.md")
                if not os.path.isfile(m):
                    continue
                t = open(m, encoding="utf-8", errors="replace").read()
                if "--axis" not in t:
                    err("E3", f"examples/{name}/design-system/MASTER.md 缺 `--axis`（输出契约要求）")
                hit = re.search(r"风格锚点：\s*`([^`]+)`", t)
                if hit and hit.group(1) not in slugs and hit.group(1) not in pool:
                    err("E3", f"examples/{name} 声明的锚点 {hit.group(1)} 不在 index.json 的 anchors/referencePool 里")

    # ---- F. 设计参数签名 & 产出审计 ----
    SIG_FIELDS = ["r", "base", "lh", "wrap", "ch", "unit", "trk", "hue", "chr",
                  "warm", "rad", "theme", "mot", "wts", "disp"]
    sig_path = os.path.join(root, "styles", "signatures.json")
    if not os.path.exists(sig_path):
        err("F1", "缺 styles/signatures.json —— emit_tokens.py 与 audit_tokens.py 都依赖它")
    else:
        try:
            S = json.load(open(sig_path, encoding="utf-8"))
        except Exception as e:
            err("F1", f"styles/signatures.json 无法解析: {e}")
            S = None
        if S:
            legend = S.get("_legend") or {}
            fam_def = S.get("_familyDefaults") or {}
            recs = S.get("anchors") or {}
            miss_legend = [f for f in SIG_FIELDS if f not in legend]
            if miss_legend:
                warn("F2", f"signatures.json 的 _legend 缺字段说明: {miss_legend}")
            if not recs:
                err("F3", "signatures.json 里没有 anchors 记录")
            if reg:
                slugs = {a.get("slug") for a in reg.get("anchors", [])}
                fams = sorted(f.get("id") for f in reg.get("families", []))
                miss = sorted(slugs - set(recs))
                extra = sorted(set(recs) - slugs)
                if miss:
                    err("F3", f"signatures.json 缺 {len(miss)} 个锚点: {miss}")
                if extra:
                    err("F3", f"signatures.json 有多余锚点（index.json 中不存在）: {extra}")
                for fid in fams:
                    if fid not in fam_def:
                        err("F4", f"signatures.json 缺族默认值: {fid}")
            bad_all = []
            for slug in sorted(recs):
                s_ = recs[slug]
                bad = []
                if s_.get("theme") not in ("light", "dark"):
                    bad.append("theme")
                if s_.get("mot") not in ("snap", "soft", "drift", "none"):
                    bad.append("mot")
                if s_.get("disp") not in ("serif", "sans", "mono", "mix"):
                    bad.append("disp")
                if s_.get("chr") not in (0, 1, 2):
                    bad.append("chr")
                if not isinstance(s_.get("r"), (int, float)) or not (1.1 <= s_["r"] <= 1.75):
                    bad.append("r")
                if s_.get("unit") not in (4, 5, 8, 10, 12, 16):
                    bad.append("unit")
                if isinstance(s_.get("wrap"), int) and s_["wrap"] % 4:
                    bad.append("wrap")
                if not isinstance(s_.get("hue"), (int, float)) or not (0 <= s_["hue"] < 360):
                    bad.append("hue")
                if not isinstance(s_.get("warm"), (int, float)) or not (-1 <= s_["warm"] <= 1):
                    bad.append("warm")
                if isinstance(s_.get("lh"), (int, float)) and not (1.3 <= s_["lh"] <= 2.0):
                    bad.append("lh")
                missing = [f for f in SIG_FIELDS if f not in s_]
                if missing:
                    bad.append("缺字段:" + ",".join(missing))
                if bad:
                    bad_all.append(f"{slug}({';'.join(bad)})")
            if bad_all:
                err("F5", f"签名字段非法: {'  '.join(bad_all)}")

            specs_dir = os.path.join(root, "styles", "specs")
            if os.path.isdir(specs_dir):
                specs = {os.path.splitext(x)[0] for x in os.listdir(specs_dir) if x.endswith(".md")}
                orphan = sorted(sp for sp in specs if sp not in recs)
                if orphan:
                    err("F6", f"这些 spec 没有对应签名（emit_tokens 合并时会缺参数）: {orphan}")

    # 产出示例必须通过审美数值审计 —— 否则"参考形状"本身就不合格
    auditor = os.path.join(root, "scripts", "audit_tokens.py")
    ex_dir = os.path.join(root, "examples")
    if os.path.exists(auditor) and os.path.isdir(ex_dir):
        import subprocess
        for name in sorted(os.listdir(ex_dir)):
            master = os.path.join(ex_dir, name, "design-system", "MASTER.md")
            if not os.path.isfile(master):
                continue
            r = subprocess.run([sys.executable, auditor, master], capture_output=True, text=True)
            if r.returncode != 0:
                fails = [x.strip() for x in (r.stdout or "").splitlines() if x.strip().startswith("✗")]
                err("F7", f"examples/{name}/MASTER.md 未通过审美审计: " + " | ".join(fails)[:300])

    # ---- G. 字体搭配注册表 & 技术栈选型（v0.7）----
    # 这两段抓的是「风格区分退化成换色」：字体没做搭配、技术栈没做判断，
    # 都会让不同项目产出同一个形状。靠人眼审查必然漏，必须机器查。
    GENERIC = {"system-ui", "-apple-system", "blinkmacsystemfont", "sans-serif",
               "serif", "monospace", "ui-sans-serif", "ui-serif", "ui-monospace",
               "segoe ui", "arial", "helvetica", "helvetica neue"}

    def first_family(stack):
        m = re.search(r'"([^"]+)"|\'([^\']+)\'|([A-Za-z][\w\s\-]*)', str(stack or ""))
        return (m.group(1) or m.group(2) or m.group(3) or "").strip() if m else ""

    fonts_path = os.path.join(root, "styles", "fonts.json")
    if not os.path.exists(fonts_path):
        err("F8", "缺 styles/fonts.json —— emit_tokens.py 的字体搭配来源，也是反同质化的数据基础")
    else:
        try:
            FN = json.load(open(fonts_path, encoding="utf-8"))
        except Exception as e:
            err("F8", f"styles/fonts.json 无法解析: {e}")
            FN = None
        if FN:
            mono_st = FN.get("_monoStacks") or {}
            cjk_st = FN.get("_cjkStacks") or {}
            fam_def = FN.get("_familyDefaults") or {}
            recs = FN.get("anchors") or {}
            for k in ("_rules", "_loadingLegend", "_cjkStacks", "_monoStacks"):
                if not FN.get(k):
                    warn("F8", f"fonts.json 缺 `{k}` —— 反同质化的判据与图例应写清楚")
            if not recs:
                err("F8", "fonts.json 里没有 anchors 记录")
            if reg:
                slugs = {a.get("slug") for a in reg.get("anchors", [])}
                fams = sorted(f.get("id") for f in reg.get("families", []))
                miss = sorted(slugs - set(recs))
                extra = sorted(set(recs) - slugs)
                if miss:
                    err("F8", f"fonts.json 缺 {len(miss)} 个锚点的字体搭配: {miss}")
                if extra:
                    err("F8", f"fonts.json 有多余锚点: {extra}")
                miss_fam = [f for f in fams if f not in fam_def]
                if miss_fam:
                    err("F8", f"fonts.json 缺族默认字体: {miss_fam}")
            # 字段与枚举合法性
            bad_fonts, displays, pairs = [], [], []
            for slug in sorted(recs):
                e_ = recs[slug]
                bad = []
                for f in ("display", "body", "mono", "cjk", "loading"):
                    if not e_.get(f):
                        bad.append("缺" + f)
                if e_.get("mono") and e_["mono"] not in mono_st:
                    bad.append(f"mono={e_['mono']} 不在 _monoStacks")
                if e_.get("cjk") and e_["cjk"] not in cjk_st:
                    bad.append(f"cjk={e_['cjk']} 不在 _cjkStacks")
                if e_.get("loading") not in ("self", "cdn", "system"):
                    bad.append("loading")
                fd, fb = first_family(e_.get("display")), first_family(e_.get("body"))
                if fd.lower() in GENERIC:
                    bad.append(f"display 首族是通用关键字({fd})")
                if fb.lower() in GENERIC:
                    bad.append(f"body 首族是通用关键字({fb})")
                if fd and fb and fd.lower() == fb.lower():
                    bad.append("display 与 body 同族（未做搭配）")
                if bad:
                    bad_fonts.append(f"{slug}({';'.join(bad)})")
                displays.append((slug, fd))
                pairs.append(fd.lower())
            if bad_fonts:
                err("F8", f"字体搭配字段非法: {'  '.join(bad_fonts)}")
            # R3：display 全库唯一
            seen = {}
            dup = []
            for slug, fd in displays:
                if fd.lower() in seen:
                    dup.append(f"{fd}({seen[fd.lower()]}↔{slug})")
                else:
                    seen[fd.lower()] = slug
            if dup:
                err("F8", f"display 字体重复（违反 R3 全库唯一）: {'  '.join(dup)}")
            info(f"字体搭配覆盖 {len(recs)} 个锚点，display 字体全库唯一")

    # 技术栈选型阶段文档与脚本必须存在（Phase 1.5 的载体）
    for rel, why in (("techstack.md", "Phase 1.5 技术栈选型的阶段文档"),
                     ("scripts/pick_stack.py", "技术栈确定性推荐脚本"),
                     ("architectures/granularity.md", "Phase 1.7 页面粒度与页内导航的判断框架"),
                     ("architectures/pagination.json", "页面粒度与页内导航的阈值注册表（唯一真源）"),
                     ("scripts/pick_pages.py", "页面粒度与页内导航的确定性推荐脚本")):
        if not os.path.exists(os.path.join(root, rel)):
            err("F9", f"缺 {rel}（{why}）—— 该选型环节的载体不成立")

    # ---------------- F10 底色维度（surface）—— 反「全站白底」
    # v0.7 的 5 个测试站 --bg 5/5 全是 #FFFFFF。根因是 emit_tokens.py 把底色明度
    # 写死成 0.985。没有 surface 维度，深色站与有色底站在**架构上做不出来**。
    try:
        SG = json.load(open(os.path.join(root, "styles", "signatures.json"), encoding="utf-8"))
    except Exception as e:
        err("F10", f"styles/signatures.json 无法解析: {e}")
        SG = {}

    sp = SG.get("_surfacePresets") or {}
    if len(sp) < 3:
        err("F10", f"_surfacePresets 只有 {len(sp)} 档，至少 3 档才撑得起批次差异")
    else:
        bad = []
        for name, v in sp.items():
            Lv, Cv, pol = v.get("L"), v.get("C"), v.get("polarity")
            if not isinstance(Lv, (int, float)) or not (0.0 <= Lv <= 1.0):
                bad.append(f"{name}(L={Lv})")
            elif not isinstance(Cv, (int, float)) or not (0.0 <= Cv <= 0.2):
                bad.append(f"{name}(C={Cv})")
            elif pol not in ("light", "dark"):
                bad.append(f"{name}(polarity={pol})")
        if bad:
            err("F10", f"_surfacePresets 字段非法: {'  '.join(bad)}")

    sigs_a = SG.get("anchors") or {}
    no_surf = [k for k, v in sigs_a.items() if not v.get("surface")]
    if sigs_a and no_surf:
        err("F10", f"{len(no_surf)} 个锚点缺 surface 字段: {no_surf[:8]}")
    elif sigs_a:
        used = {v.get("surface") for v in sigs_a.values()}
        unknown = used - set(sp)
        if unknown:
            err("F10", f"锚点引用了不存在的 surface 档: {sorted(unknown)}")
        elif len(used) < 3:
            err("F10", f"{len(sigs_a)} 个锚点只用了 {len(used)} 档 surface —— 底色空间未被利用")
        else:
            info(f"底色维度覆盖 {len(sigs_a)} 个锚点，{len(used)} 档 surface 在用")

    # ---------------- F11 尺度变体轴（variant）—— 反「同锚点逐值相同」
    va = SG.get("_variantAxes") or {}
    if len(va) < 2:
        err("F11", f"_variantAxes 只有 {len(va)} 条，至少 2 条（含原值）才能让同锚点复用不撞车")
    else:
        bad = []
        for k, v in va.items():
            dr, du = v.get("dr", 0), v.get("dunit", 1.0)
            db, drad = v.get("dbase", 0), v.get("drad", 0)
            if not isinstance(dr, (int, float)) or abs(dr) > 0.25:
                bad.append(f"{k}(dr={dr})")
            elif not isinstance(du, (int, float)) or not (0.3 <= du <= 3.0):
                bad.append(f"{k}(dunit={du})")
            elif not isinstance(db, int) or abs(db) > 3:
                bad.append(f"{k}(dbase={db})")
            elif not isinstance(drad, int) or abs(drad) > 12:
                bad.append(f"{k}(drad={drad})")
        if bad:
            err("F11", f"_variantAxes 偏移量超出安全范围: {'  '.join(bad)}")
        else:
            info(f"尺度变体轴 {len(va)} 条：{' / '.join(sorted(va))}")

    # ---------------- F12 族级字体备用池 —— 反「同锚点无字可用」
    # 锚点主选每锚点只有**一对**。第二次使用该锚点时若不换，两站 --font-display
    # 会一字不差（acute-angle 与 hongda 就是这么撞的）。
    try:
        FN2 = json.load(open(os.path.join(root, "styles", "fonts.json"), encoding="utf-8"))
    except Exception as e:
        err("F12", f"styles/fonts.json 无法解析: {e}")
        FN2 = {}

    pools = FN2.get("_familyPools") or {}
    fam_keys = set((FN2.get("_familyDefaults") or {}).keys())
    if fam_keys:
        miss = sorted(fam_keys - set(pools))
        if miss:
            err("F12", f"_familyPools 缺 {len(miss)} 个族: {miss}")
        thin = sorted(k for k, v in pools.items() if len(v) < 3)
        if thin:
            err("F12", f"以下族的备用池不足 3 对（同锚点第二次使用会无字可用）: {thin}")
        if not miss and not thin:
            seen = {}
            dup = []
            for slug, rec in (FN2.get("anchors") or {}).items():
                fd = first_family(rec.get("display", ""))
                if fd:
                    seen.setdefault(fd.lower(), f"锚点 {slug}")
            for fam, pool in pools.items():
                for i, rec in enumerate(pool, 1):
                    fd = first_family(rec.get("display", ""))
                    if not fd:
                        continue
                    if fd.lower() in seen:
                        dup.append(f"{fd}({fam}#{i} ↔ {seen[fd.lower()]})")
                    else:
                        seen[fd.lower()] = f"{fam}#{i}"
            if dup:
                err("F12", f"族备用池 display 与已有搭配重复（R3 扩展）: {'  '.join(dup)}")
            else:
                total = sum(len(v) for v in pools.values())
                info(f"族备用池 {len(pools)} 族 / {total} 对，display 全库唯一")

    # ---------------- F13 反同质化的执行工具必须存在
    for rel, why in (("scripts/ledger.py", "批次风格账本 —— 事前查重，打破跨站同向收敛"),
                     ("scripts/audit_tokens.py", "产出审计 —— 含 F10 视觉签名 / F11 批次差异度")):
        if not os.path.exists(os.path.join(root, rel)):
            err("F13", f"缺 {rel}（{why}）")

    # ---------------- H1 页面粒度与页内导航：IA 文档必须与注册表一致
    # 这一节抓的是「文档 A 说的」与「注册表 B 说的」互相矛盾 —— 与 E 段同一类漂移。
    # 四个 IA 文档各写一份默认粒度，注册表里也有一份；两处不一致时，agent 读到哪个算哪个。
    pg_path = os.path.join(root, "architectures", "pagination.json")
    ia_docs = ("portfolio", "narrative", "directory", "conversion")
    h1_before = len(ERRORS)
    if os.path.exists(pg_path):
        try:
            PG = json.load(open(pg_path, encoding="utf-8"))
        except Exception as e:
            err("H1", f"architectures/pagination.json 无法解析: {e}")
            PG = None
        if PG:
            for key in ("granularity", "inPageNav", "iaDefaults", "falsify"):
                if key not in PG:
                    err("H1", f"pagination.json 缺 `{key}` 段")
            defaults = PG.get("iaDefaults") or {}
            g_levels = set((PG.get("granularity") or {}).get("levels") or {})
            n_levels = set((PG.get("inPageNav") or {}).get("levels") or {})
            if len(g_levels) < 4 or len(n_levels) < 4:
                err("H1", f"pagination.json 档位定义不全：粒度 {sorted(g_levels)} / 导航 {sorted(n_levels)}")
            th = (PG.get("granularity") or {}).get("thresholds") or {}
            nth = (PG.get("inPageNav") or {}).get("thresholds") or {}
            for k in ("entries_master_detail", "entries_master_detail_forced", "themes_multi_page"):
                if not isinstance(th.get(k), int):
                    err("H1", f"granularity.thresholds 缺或非法：{k}")
            for k in ("blocks_none_max", "blocks_anchor_min", "blocks_sticky_min", "blocks_rail_min",
                      "none_contradiction_blocks", "min_anchor_targets"):
                if not isinstance(nth.get(k), int):
                    err("H1", f"inPageNav.thresholds 缺或非法：{k}")
            for ia in ia_docs:
                p = os.path.join(root, "architectures", ia + ".md")
                if not os.path.exists(p):
                    err("H1", f"缺 architectures/{ia}.md")
                    continue
                t = open(p, encoding="utf-8", errors="replace").read()
                mg = re.search(r"默认粒度\**\s*[：:]\s*`?([a-z][a-z\-]*)", t)
                mn = re.search(r"默认页内导航\**\s*[：:]\s*`?([a-z][a-z\-]*)", t)
                if not mg:
                    err("H1", f"architectures/{ia}.md 未声明「默认粒度」"
                              f"（IA 只答了区块组成，没答分几页 —— 这正是 v0.8 的缺口）")
                if not mn:
                    err("H1", f"architectures/{ia}.md 未声明「默认页内导航」")
                want = defaults.get(ia) or {}
                if mg and want.get("granularity") and mg.group(1) != want["granularity"]:
                    err("H1", f"{ia}.md 默认粒度 `{mg.group(1)}` ≠ 注册表 `{want['granularity']}`（文档漂移）")
                if mn and want.get("nav") and mn.group(1) != want["nav"]:
                    err("H1", f"{ia}.md 默认页内导航 `{mn.group(1)}` ≠ 注册表 `{want['nav']}`（文档漂移）")
            gm = os.path.join(root, "architectures", "granularity.md")
            if os.path.exists(gm):
                gt = open(gm, encoding="utf-8", errors="replace").read()
                rows = re.findall(
                    r"^\|\s*`(portfolio|narrative|directory|conversion)`\s*\|\s*`([a-z\-]+)`\s*\|\s*`([a-z\-]+)`",
                    gt, re.M)
                if len(rows) < 4:
                    warn("H1", "granularity.md 的 IA 默认值汇总表解析不全（检查表格格式是否被改动）")
                for ia, g_, n_ in rows:
                    want = defaults.get(ia) or {}
                    if want.get("granularity") and g_ != want["granularity"]:
                        err("H1", f"granularity.md 表里 {ia} 的粒度 `{g_}` ≠ 注册表 `{want['granularity']}`")
                    if want.get("nav") and n_ != want["nav"]:
                        err("H1", f"granularity.md 表里 {ia} 的导航 `{n_}` ≠ 注册表 `{want['nav']}`")
    else:
        err("H1", "缺 architectures/pagination.json（页面粒度的阈值注册表）")
    if len(ERRORS) == h1_before:
        info("H1 IA 文档与 pagination.json 的默认值一致")

    # ---------------- H2 示例的页面结构审计必须通过
    # 与 F7 同构：F7 查示例的 token 数值，H2 查示例的页面结构（F14/F15）。
    # 示例是「输出形状的参考」—— 形状本身不合格，参考价值就是负的。
    if os.path.exists(auditor) and os.path.isdir(ex_dir):
        import subprocess
        for name in sorted(os.listdir(ex_dir)):
            site = os.path.join(ex_dir, name)
            if not os.path.isdir(site) or not os.path.isdir(os.path.join(site, "src")):
                continue
            r = subprocess.run([sys.executable, auditor, "--site", site], capture_output=True, text=True)
            if r.returncode != 0:
                fails = [x.strip() for x in (r.stdout or "").splitlines() if x.strip().startswith("✗")]
                err("H2", f"examples/{name} 未通过页面结构审计: " + " | ".join(fails)[:300])

    # ---------------- H3 中轴档位供给 —— 反「某一档只有两三个锚点、全挤在一个布局里」
    # 这是**维度没正交**的问题，不是锚点数量问题：中轴本该是独立的对齐维度，
    # 但若某档 100% 绑定单一布局原型，选它就等于选布局，批次多样性就白做了。
    # 与 E1（取值合法）互补：E1 保证 axis 在枚举内，H3 保证枚举内每一档都真的有得选。
    h3_before = len(ERRORS)
    by_axis = {}
    if reg:
        for a in anchors:
            ax = a.get("axis")
            if not ax:
                continue
            st = by_axis.setdefault(ax, {"n": 0, "layouts": set(), "families": set()})
            st["n"] += 1
            st["layouts"].add(a.get("layout"))
            st["families"].add(a.get("family"))
        for ax, st in sorted(by_axis.items()):
            if st["n"] < MIN_AXIS_ANCHORS:
                err("H3", f"中轴 `{ax}` 只有 {st['n']} 个锚点（阈值 ≥{MIN_AXIS_ANCHORS}）"
                          f" —— 供给过薄会让它成为批次的必经点")
            if len(st["layouts"]) < MIN_AXIS_LAYOUTS:
                err("H3", f"中轴 `{ax}` 只跨 {len(st['layouts'])} 个布局原型 {sorted(st['layouts'])}"
                          f"（阈值 ≥{MIN_AXIS_LAYOUTS}）—— 选中它就等于选中这个布局")
            if len(st["families"]) < MIN_AXIS_FAMILIES:
                err("H3", f"中轴 `{ax}` 只跨 {len(st['families'])} 个族 {sorted(st['families'])}"
                          f"（阈值 ≥{MIN_AXIS_FAMILIES}）")
        if len(by_axis) < 3:
            err("H3", f"中轴只有 {len(by_axis)} 档 —— 档位太少时「种类数」阈值会退化成配额"
                      f"（见 ledger.py 的 MIN_AXIS_KINDS 注释）")
    if reg and len(ERRORS) == h3_before:
        info("中轴供给 " + " / ".join(
            f"{k} {v['n']}（{len(v['layouts'])} 布局 {len(v['families'])} 族）"
            for k, v in sorted(by_axis.items())))

    # ---------------- H4 铁律索引 ↔ references/rules.md 全文
    # 见文件头 MIN_AXIS_* 下方的 RULES_REL 注释。索引省 token，全文按需读 —— 代价是两份要同步。
    h4_before = len(ERRORS)
    full = {}
    rules_path = os.path.join(root, *RULES_REL.split("/"))
    if not os.path.isfile(rules_path):
        err("H4", f"缺 `{RULES_REL}`（铁律全文；SKILL.md 只留索引，缺了它铁律就只剩一句结论）")
    else:
        full = _rule_titles(open(rules_path, encoding="utf-8").read())
        idx = _index_titles(body)
        if not full:
            err("H4", f"`{RULES_REL}` 没解析到任何 `N. **标题**` 形式的铁律（改了写法？）")
        if not idx:
            err("H4", "SKILL.md 没解析到铁律索引（`## 铁律索引` 段或其编号行改了写法？）")
        if full and idx:
            for label, d in ((RULES_REL, full), ("SKILL.md 索引", idx)):
                miss = [i for i in range(1, max(d) + 1) if i not in d]
                if miss:
                    shown = ", ".join(str(i) for i in miss[:10])
                    err("H4", f"{label} 编号不连续，缺 {shown}{' …' if len(miss) > 10 else ''}"
                              f" —— 编号是外部引用锚点，跳号会让引用指向另一条")
            only_full = sorted(set(full) - set(idx))
            only_idx = sorted(set(idx) - set(full))
            if only_full:
                err("H4", f"铁律 {only_full[:10]} 只在 `{RULES_REL}` 里、索引没有"
                          f" —— agent 只按索引自检，这几条等于没有")
            if only_idx:
                err("H4", f"铁律 {only_idx[:10]} 只在 SKILL.md 索引里、`{RULES_REL}` 没有全文")
            for n in sorted(set(full) & set(idx)):
                a, b = idx[n].rstrip("。").strip(), full[n].rstrip("。").strip()
                if not b.startswith(a):
                    err("H4", f"铁律 {n} 两边不是同一条：索引「{a}」 vs 全文「{b}」")
            mh = re.search(r"## 铁律索引[^\n]*?(\d+)\s*条", body)
            if mh and int(mh.group(1)) != len(full):
                err("H4", f"SKILL.md 标题写 {mh.group(1)} 条，`{RULES_REL}` 实际 {len(full)} 条")
    if len(ERRORS) == h4_before and full:
        info(f"H4 铁律索引与 `{RULES_REL}` 一致（{len(full)} 条，编号 1–{max(full)} 连续）")

    return report(root)


def report(root):
    print("=" * 68)
    print(f"validate_skill · {root}")
    print("=" * 68)
    for i in INFOS:
        print("  i " + i)
    for w in WARNS:
        print("  ? " + w)
    for e in ERRORS:
        print("  x " + e)
    print("-" * 68)
    print(f"ERROR {len(ERRORS)}  WARN {len(WARNS)}")
    print("RESULT:", "PASS" if not ERRORS else "FAIL")
    if "--json" in sys.argv:
        print(json.dumps({"errors": ERRORS, "warnings": WARNS, "info": INFOS},
                         ensure_ascii=False, indent=2))
    sys.exit(0 if not ERRORS else 1)


if __name__ == "__main__":
    main()
