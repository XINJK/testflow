"""把 testflow 工件（testpoints / func-cases）转换为 XMind 可导入的 Markdown 大纲。

用法:
    python tools/export_xmind_md.py <artifact.md> [--tp <tpoints.md>] [--out <path>]
输出: 默认同目录 <stem>.xmind.md（UTF-8）
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def parse_frontmatter(text: str) -> dict:
    fm: dict[str, str] = {}
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if line[:1] in (" ", "-", "") or ":" not in line:
                continue
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()
    return fm


def parse_tables(text: str) -> dict:
    tables: dict[str, list] = {}
    section = None
    rows: list = []

    def flush() -> None:
        nonlocal rows
        if section and rows:
            if section not in tables:
                tables[section] = rows
            rows = []

    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("## "):
            flush()
            section = line[3:].strip()
        elif line.startswith("|") and line.endswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(set(c) <= {"-", ":", " "} for c in cells):
                continue
            rows.append(cells)
        else:
            flush()
    flush()
    return tables


def to_dicts(rows: list) -> list:
    if not rows:
        return []
    keys = rows[0]
    out = []
    for r in rows[1:]:
        if len(r) < len(keys):
            r = r + [""] * (len(keys) - len(r))
        elif len(r) > len(keys):
            r = r[: len(keys) - 1] + [" | ".join(r[len(keys) - 1:])]
        out.append(dict(zip(keys, r)))
    return out


def cell(v: str) -> str:
    return (v or "").replace("\n", " ").strip()


def title_of(text: str, default: str) -> str:
    m = re.search(r"^# (.+)$", text, re.M)
    return m.group(1).strip() if m else default


def export_tp(text: str, out: list) -> None:
    fm = parse_frontmatter(text)
    tables = parse_tables(text)
    fps = to_dicts(tables.get("功能点清单", []))
    tps = to_dicts(tables.get("测试点清单", []))
    out.append(f"# {title_of(text, '测试点')}（{cell(fm.get('artifact_id', ''))}）")
    out.append("")
    for fp in fps:
        out.append(f"## {cell(fp.get('ID'))} {cell(fp.get('名称'))}".rstrip())
        out.append("")
        for tp in tps:
            if fp.get("ID") and fp["ID"] not in cell(tp.get("关联FP", "")):
                continue
            out.append(f"### {cell(tp.get('ID'))} {cell(tp.get('名称'))}".rstrip())
            for label, key in (("类型", "类型"), ("设计方法", "设计方法"), ("优先级", "优先级"),
                               ("前置条件", "前置条件"), ("测试数据", "测试数据提示")):
                val = cell(tp.get(key, ""))
                if val and val != "-":
                    out.append(f"- {label}：{val}")
            out.append("")


def export_tcf(text: str, out: list, tp_text) -> None:
    fm = parse_frontmatter(text)
    cases = to_dicts(parse_tables(text).get("用例清单", []))
    tp_fp, fp_name = {}, {}
    if tp_text:
        t = parse_tables(tp_text)
        for tp in to_dicts(t.get("测试点清单", [])):
            tp_fp[cell(tp.get("ID"))] = cell(tp.get("关联FP"))
        for fp in to_dicts(t.get("功能点清单", [])):
            fp_name[cell(fp.get("ID"))] = f"{cell(fp.get('ID'))} {cell(fp.get('名称'))}".rstrip()
    out.append(f"# {title_of(text, '功能测试用例')}（{cell(fm.get('artifact_id', ''))}）")
    out.append("")
    if tp_text:
        groups: dict[str, list] = {}
        for c in cases:
            groups.setdefault(tp_fp.get(cell(c.get("关联TP")), "未分组"), []).append(c)
    else:
        groups = {"": cases}
    for key, items in groups.items():
        out.append(f"## {fp_name.get(key) or '全部用例'}")
        out.append("")
        for c in items:
            out.append(f"### {cell(c.get('ID'))} {cell(c.get('标题'))}".rstrip())
            for label, k in (("关联TP", "关联TP"), ("优先级", "优先级"), ("前置", "前置条件"), ("数据", "测试数据")):
                val = cell(c.get(k, ""))
                if val and val != "-":
                    out.append(f"- {label}：{val}")
            for part in c.get("步骤与预期", "").split("<br>"):
                part = part.strip()
                if part:
                    out.append(f"- {part}")
            out.append("")


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="工件 -> XMind 大纲 Markdown")
    ap.add_argument("artifact")
    ap.add_argument("--tp", default=None, help="测试点工件（用于用例按功能点分组）")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    p = Path(args.artifact)
    if not p.is_absolute():
        p = (ROOT / p).resolve()
    text = p.read_text(encoding="utf-8")
    fm = parse_frontmatter(text)
    out: list = []
    if fm.get("stage") == "testpoints":
        export_tp(text, out)
    elif fm.get("stage") == "func-cases":
        tp_text = None
        if args.tp:
            tp_path = Path(args.tp)
            if not tp_path.is_absolute():
                tp_path = (ROOT / tp_path).resolve()
            tp_text = tp_path.read_text(encoding="utf-8")
        export_tcf(text, out, tp_text)
    else:
        print(f"仅支持 stage=testpoints / func-cases，当前 stage={fm.get('stage')!r}")
        return 1
    dst = Path(args.out) if args.out else p.with_name(p.stem + ".xmind.md")
    if not dst.is_absolute():
        dst = (ROOT / dst).resolve()
    dst.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
    print(f"[完成] {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
