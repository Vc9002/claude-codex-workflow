#!/usr/bin/env python3
"""Inspect local Claude session metadata, transcripts, uploads, and outputs."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Iterable


HOME = Path.home()
CLAUDE_ROOTS = [
    HOME / "Library/Application Support/Claude/local-agent-mode-sessions",
    HOME / "Library/Application Support/Claude/claude-code-sessions",
]
CODE_ROOT = HOME / ".claude/projects"
PROJECTS_ROOT = HOME / "Documents/Claude/Projects"


def clean(text: str | None, limit: int | None = None) -> str:
    if not text:
        return ""
    text = re.sub(r"/9j/[A-Za-z0-9+/=\n\r]{200,}", "[base64 image data omitted]", text)
    text = re.sub(r"([A-Za-z0-9+/]{400,}={0,2})", "[long encoded data omitted]", text)
    text = text.replace("\r\n", "\n").strip()
    if limit and len(text) > limit:
        return text[:limit].rstrip() + "\n[truncated]"
    return text


def ms_to_iso(value: Any) -> str:
    if value in (None, ""):
        return ""
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)
    if numeric > 10_000_000_000:
        numeric /= 1000
    return dt.datetime.fromtimestamp(numeric, tz=dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def iter_metadata() -> Iterable[tuple[Path, dict[str, Any]]]:
    for root in CLAUDE_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("local_*.json"):
            if not path.is_file():
                continue
            try:
                data = json.loads(path.read_text(errors="replace"))
            except Exception:
                continue
            if isinstance(data, dict) and "sessionId" in data:
                yield path, data


def session_sort_key(item: tuple[Path, dict[str, Any]]) -> float:
    _, data = item
    for key in ("lastActivityAt", "updatedAt", "createdAt"):
        value = data.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    return 0


def session_dir(meta_path: Path, data: dict[str, Any]) -> Path:
    sid = data.get("sessionId") or meta_path.stem
    candidate = meta_path.with_suffix("")
    if candidate.exists():
        return candidate
    candidate = meta_path.parent / str(sid)
    return candidate


def find_transcripts(root: Path) -> list[Path]:
    paths: list[Path] = []
    if root.exists():
        paths.extend(sorted((root / ".claude/projects").glob("*/*.jsonl")))
        paths.extend(sorted(root.glob(".claude/projects/*/*.jsonl")))
        paths.extend(sorted(root.glob("**/.claude/projects/*/*.jsonl")))
    if not paths and CODE_ROOT.exists():
        paths.extend(sorted(CODE_ROOT.glob("*/*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)[:10])
    seen: set[Path] = set()
    out: list[Path] = []
    for path in paths:
        if path not in seen and path.is_file():
            seen.add(path)
            out.append(path)
    return out


def content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return clean(content)
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if not isinstance(item, dict):
                continue
            typ = item.get("type")
            if typ == "text":
                parts.append(str(item.get("text", "")))
            elif typ == "image":
                source = item.get("source") or {}
                parts.append(f"[image attachment: {source.get('media_type', 'image')}]")
            elif typ == "tool_use":
                parts.append(f"[tool use: {item.get('name', 'tool')}]")
            elif typ == "tool_result":
                parts.append("[tool result omitted]")
        return clean("\n".join(parts))
    return ""


def transcript_messages(paths: list[Path], max_messages: int = 80) -> list[tuple[str, str, str]]:
    messages: list[tuple[str, str, str]] = []
    for path in paths:
        try:
            lines = path.read_text(errors="replace").splitlines()
        except Exception:
            continue
        for raw in lines:
            if not raw.strip():
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if obj.get("isMeta"):
                continue
            msg = obj.get("message")
            if not isinstance(msg, dict):
                if obj.get("type") == "last-prompt" and obj.get("lastPrompt"):
                    messages.append((obj.get("timestamp", ""), "last-prompt", clean(obj.get("lastPrompt"), 3000)))
                continue
            role = msg.get("role")
            if role not in {"user", "assistant"}:
                continue
            text = content_to_text(msg.get("content"))
            if text:
                messages.append((obj.get("timestamp", ""), role, text))
    return messages[-max_messages:]


def iter_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    skip_parts = {"node_modules", ".git", "__pycache__"}
    files = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if skip_parts.intersection(path.relative_to(root).parts):
            continue
        files.append(path)
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)


def extract_docx(path: Path) -> str:
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with zipfile.ZipFile(path) as zf:
        root = ET.fromstring(zf.read("word/document.xml"))
    paras = []
    for p in root.findall(".//w:p", ns):
        texts = [t.text for t in p.findall(".//w:t", ns) if t.text]
        if texts:
            paras.append("".join(texts))
    return clean("\n".join(paras), 6000)


def extract_pptx(path: Path) -> str:
    ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
    chunks: list[str] = []
    with zipfile.ZipFile(path) as zf:
        names = sorted(
            [n for n in zf.namelist() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)],
            key=lambda n: int(re.search(r"slide(\d+)\.xml", n).group(1)),
        )
        for name in names[:30]:
            root = ET.fromstring(zf.read(name))
            texts = [el.text for el in root.findall(".//a:t", ns) if el.text]
            slide_no = int(re.search(r"slide(\d+)\.xml", name).group(1))
            if texts:
                chunks.append(f"Slide {slide_no}: " + " | ".join(texts))
    return clean("\n".join(chunks), 8000)


def extract_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        return "[PDF text extraction skipped: pypdf is not installed in this Python.]"
    reader = PdfReader(str(path))
    chunks = []
    for index, page in enumerate(reader.pages[:20], 1):
        chunks.append(f"Page {index}:\n{page.extract_text() or ''}")
    return clean("\n\n".join(chunks), 10000)


def maybe_extract(path: Path) -> str:
    suffix = path.suffix.lower()
    try:
        if suffix in {".md", ".txt", ".json"}:
            return clean(path.read_text(errors="replace"), 5000)
        if suffix == ".docx":
            return extract_docx(path)
        if suffix == ".pptx":
            return extract_pptx(path)
        if suffix == ".pdf":
            return extract_pdf(path)
    except Exception as exc:
        return f"[Extraction failed: {exc}]"
    return ""


def list_sessions(limit: int, query: str | None) -> None:
    items = sorted(iter_metadata(), key=session_sort_key, reverse=True)
    if query:
        needle = query.lower()
        items = [
            item for item in items
            if needle in " ".join(str(item[1].get(k, "")) for k in ("title", "initialMessage", "cwd", "sessionId")).lower()
        ]
    for path, data in items[:limit]:
        print(json.dumps({
            "lastActivity": ms_to_iso(data.get("lastActivityAt")),
            "created": ms_to_iso(data.get("createdAt")),
            "title": data.get("title"),
            "initialMessage": clean(data.get("initialMessage"), 160),
            "cwd": data.get("cwd"),
            "model": data.get("model"),
            "sessionId": data.get("sessionId"),
            "metadata": str(path),
        }, ensure_ascii=False))


def readout(meta_path: Path, out: Path | None, extract_limit: int) -> str:
    data = json.loads(meta_path.read_text(errors="replace"))
    root = session_dir(meta_path, data)
    files = iter_files(root)
    transcripts = find_transcripts(root)
    messages = transcript_messages(transcripts)

    lines: list[str] = []
    lines.append("# Claude Session Readout")
    lines.append("")
    lines.append(f"- Title: {data.get('title')}")
    lines.append(f"- Session ID: `{data.get('sessionId')}`")
    lines.append(f"- Model: {data.get('model')}")
    lines.append(f"- Created: {ms_to_iso(data.get('createdAt'))}")
    lines.append(f"- Last activity: {ms_to_iso(data.get('lastActivityAt'))}")
    lines.append(f"- CWD: `{data.get('cwd')}`")
    lines.append(f"- Metadata: `{meta_path}`")
    lines.append(f"- Session folder: `{root}`")
    lines.append("")

    if data.get("initialMessage"):
        lines.append("## Initial Message")
        lines.append("")
        lines.append(clean(data.get("initialMessage"), 3000))
        lines.append("")

    lines.append("## File Inventory")
    lines.append("")
    lines.append(f"- Total files in session folder: {len(files)}")
    for name in ("uploads", "outputs", ".claude"):
        count = sum(1 for p in files if name in p.relative_to(root).parts) if root.exists() else 0
        lines.append(f"- `{name}` files: {count}")
    lines.append("")
    for p in files[:80]:
        rel = p.relative_to(root) if root.exists() and p.is_relative_to(root) else p
        lines.append(f"- `{rel}` ({p.stat().st_size} bytes)")
    lines.append("")

    if transcripts:
        lines.append("## Transcript Sources")
        lines.append("")
        for path in transcripts:
            lines.append(f"- `{path}`")
        lines.append("")

    if messages:
        lines.append("## Visible Conversation")
        lines.append("")
        for timestamp, role, text in messages:
            lines.append(f"### {role} {timestamp}".rstrip())
            lines.append("")
            lines.append(clean(text, 4000))
            lines.append("")

    extractable = []
    for path in files:
        if path.suffix.lower() not in {".md", ".txt", ".docx", ".pptx", ".pdf"}:
            continue
        if root.exists():
            rel_parts = path.relative_to(root).parts
            if not rel_parts or rel_parts[0] not in {"uploads", "outputs"}:
                continue
        extractable.append(path)
    if extractable:
        lines.append("## Extracted Document Text")
        lines.append("")
        for path in extractable[:extract_limit]:
            lines.append(f"### {path.name}")
            lines.append("")
            lines.append(f"`{path}`")
            lines.append("")
            extracted = maybe_extract(path)
            lines.append(extracted or "[No text extracted]")
            lines.append("")

    report = "\n".join(lines)
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report)
    return report


def project_docs(limit: int) -> None:
    if not PROJECTS_ROOT.exists():
        return
    files = [p for p in PROJECTS_ROOT.rglob("*") if p.is_file()]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    for path in files[:limit]:
        print(json.dumps({
            "modified": dt.datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec="seconds"),
            "size": path.stat().st_size,
            "path": str(path),
        }, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="List recent Claude sessions as JSON lines.")
    p_list.add_argument("--limit", type=int, default=12)
    p_list.add_argument("--query")

    p_readout = sub.add_parser("readout", help="Write or print a Markdown readout for one session.")
    p_readout.add_argument("--session", required=True, type=Path, help="Path to a local_*.json metadata file.")
    p_readout.add_argument("--out", type=Path)
    p_readout.add_argument("--extract-limit", type=int, default=20)

    p_docs = sub.add_parser("project-docs", help="List recently modified files under ~/Documents/Claude/Projects.")
    p_docs.add_argument("--limit", type=int, default=40)

    args = parser.parse_args()
    if args.command == "list":
        list_sessions(args.limit, args.query)
    elif args.command == "readout":
        report = readout(args.session.expanduser(), args.out.expanduser() if args.out else None, args.extract_limit)
        if args.out:
            print(args.out)
        else:
            print(report)
    elif args.command == "project-docs":
        project_docs(args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
