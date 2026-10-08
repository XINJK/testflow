"""testflow.0.1 输入提取器（确定性，不调用 LLM）。

用法:
    python tools/extract_input.py                # 扫描 artifacts/00-input/ 下所有支持格式
    python tools/extract_input.py <file> [...]   # 只提取指定文件
    python tools/extract_input.py --force        # 已提取过也重新提取

支持: .pdf / .docx / .md / .txt
输出: artifacts/00-input/extracted/<stem>.md，带锚点注释:
    PDF  -> <!-- anchor: p<页码> -->
    DOCX -> <!-- anchor: P<段落序号> --> ；表格 <!-- anchor: T<表格序号> -->
    MD/TXT -> 原样复制，锚点即行号 #L<n>
"""
from __future__ import annotations

import argparse
import datetime as _dt
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = ROOT / "artifacts" / "00-input"
OUT_DIR = INPUT_DIR / "extracted"
SUPPORTED = {".pdf", ".docx", ".md", ".txt"}
SOURCE_MD = INPUT_DIR / "source.md"

SOURCE_TEMPLATE = """# 输入来源元数据（source.md）

每次投放输入后，请补全本文件。代理在引用来源时以 extracted/ 下文本为准。

| 文件 | 格式 | 来源系统/出处 | 版本/日期 | 备注 |
|---|---|---|---|---|
| （待填写） | | | | |
"""


def _safe_stdout() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except Exception:
        pass


def extract_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("缺少 pypdf，请先运行: python -m pip install pypdf python-docx") from exc
    reader = PdfReader(str(path))
    lines = [f"# {path.stem}", ""]
    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        lines.append(f"<!-- anchor: p{i} -->")
        if text:
            for para in text.split("\n"):
                para = para.strip()
                if para:
                    lines.append(para)
        lines.append("")
    return "\n".join(lines)


def extract_docx(path: Path) -> str:
    try:
        import docx  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("缺少 python-docx，请先运行: python -m pip install pypdf python-docx") from exc
    document = docx.Document(str(path))
    lines = [f"# {path.stem}", ""]
    for i, para in enumerate(document.paragraphs, start=1):
        text = para.text.strip()
        if not text:
            continue
        if para.style is not None and para.style.name.startswith("Heading"):
            lines.append(f"<!-- anchor: P{i} -->")
            lines.append(f"## {text}")
        else:
            lines.append(f"<!-- anchor: P{i} -->")
            lines.append(text)
        lines.append("")
    for ti, table in enumerate(document.tables, start=1):
        lines.append(f"<!-- anchor: T{ti} -->")
        for row in table.rows:
            cells = [c.text.strip().replace("\n", "<br>") for c in row.cells]
            lines.append("| " + " | ".join(cells) + " |")
        lines.append("")
    return "\n".join(lines)


def extract_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def collect_inputs(explicit: list[str]) -> list[Path]:
    if explicit:
        files: list[Path] = []
        for item in explicit:
            p = Path(item)
            if not p.is_absolute():
                p = (ROOT / item).resolve()
            files.append(p)
        return files
    files = []
    for p in sorted(INPUT_DIR.iterdir()):
        if p.is_file() and p.suffix.lower() in SUPPORTED and p.name != "source.md":
            files.append(p)
    return files


def main() -> int:
    _safe_stdout()
    parser = argparse.ArgumentParser(description="testflow 输入提取器")
    parser.add_argument("files", nargs="*", help="要提取的文件；缺省扫描 00-input")
    parser.add_argument("--force", action="store_true", help="覆盖已有提取结果")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    files = collect_inputs(args.files)
    if not files:
        print(f"未找到可提取文件（目录: {INPUT_DIR}）。")
        return 1

    if not SOURCE_MD.exists():
        SOURCE_MD.write_text(SOURCE_TEMPLATE, encoding="utf-8")
        print(f"已生成来源模板: {SOURCE_MD.relative_to(ROOT)}（请补全）")

    rc = 0
    for path in files:
        if not path.exists():
            print(f"[跳过] 文件不存在: {path}")
            rc = 1
            continue
        suffix = path.suffix.lower()
        if suffix not in SUPPORTED:
            print(f"[跳过] 不支持的格式: {path.name}")
            continue
        out = OUT_DIR / f"{path.stem}.md"
        if out.exists() and not args.force:
            print(f"[跳过] 已有提取结果（用 --force 覆盖）: {out.relative_to(ROOT)}")
            continue
        try:
            if suffix == ".pdf":
                content = extract_pdf(path)
            elif suffix == ".docx":
                content = extract_docx(path)
            else:
                content = extract_text(path)
        except Exception as exc:
            print(f"[失败] {path.name}: {exc}")
            rc = 1
            continue
        header = f"<!-- source: {path.name} | extracted: {_dt.datetime.now().isoformat(timespec='seconds')} -->\n"
        content = unicodedata.normalize("NFKC", content)
        out.write_text(header + content + "\n", encoding="utf-8")
        print(f"[完成] {path.name} -> {out.relative_to(ROOT)}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
