import csv
import hashlib
import re
import shutil
import tempfile
from pathlib import Path
from typing import Callable, Iterable

import py7zr

from .. import models

EXPORT_DIR = Path("exports")
EXPORT_DIR.mkdir(exist_ok=True)
SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9_\-\u4e00-\u9fff]+")
FILE_LINK_RE = re.compile(
    r"(?:https?://[^\s\)]+)?/notes/(?:share-files|files)/(images|files)/([^\s\)]+)"
)


def normalize_title(markdown_text: str) -> str:
    if not markdown_text:
        return "未命名"
    for line in markdown_text.splitlines():
        cleaned = line.strip()
        if not cleaned:
            continue
        if cleaned.startswith("!["):
            continue
        cleaned = re.sub(r"^#+\s*", "", cleaned)
        cleaned = re.sub(r"[`*_>]+", "", cleaned)
        cleaned = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", cleaned)
        if not cleaned.strip():
            continue
        return cleaned[:80]
    return "未命名"


def extract_tags(markdown_text: str) -> list[str]:
    if not markdown_text:
        return []
    tags = re.findall(r"(?:^|\s)#([A-Za-z0-9_\-\u4e00-\u9fff]+)", markdown_text)
    seen = set()
    result: list[str] = []
    for tag in tags:
        if tag in seen:
            continue
        seen.add(tag)
        result.append(tag)
    return result


def markdown_to_plain(markdown_text: str) -> str:
    if not markdown_text:
        return ""
    text = re.sub(r"!\[([^\]]*)\]\([^\)]+\)", r"\1", markdown_text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"`{1,3}([^`]+)`{1,3}", r"\1", text)
    text = re.sub(r"[*_>#+-]", "", text)
    return text.strip()


def estimate_csv_size(notes: Iterable[models.Note]) -> int:
    total = 0
    for note in notes:
        title = normalize_title(note.body_md)
        content = markdown_to_plain(note.body_md)
        tags = ",".join(extract_tags(note.body_md))
        total += len(title) + len(content) + len(tags) + 64
    return total


def estimate_md7z_size(notes: Iterable[models.Note]) -> int:
    total = 0
    for note in notes:
        total += len(note.body_md or "") + 128
    return int(total * 0.6)


def compute_sha256(file_path: Path) -> str:
    sha = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def write_checksum_report(file_path: Path, checksum: str) -> Path:
    report_path = file_path.with_suffix(file_path.suffix + ".sha256")
    report_path.write_text(f"{checksum}  {file_path.name}\n", encoding="utf-8")
    return report_path


def export_csv(
    notes: list[models.Note],
    output_path: Path,
    on_progress: Callable[[int], None] | None = None,
):
    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "title", "content", "created_at", "updated_at", "tags", "is_shared", "ai_summary"])
        total = len(notes) or 1
        for index, note in enumerate(notes, start=1):
            title = normalize_title(note.body_md)
            content = markdown_to_plain(note.body_md)
            tags = ",".join(extract_tags(note.body_md))
            writer.writerow([
                note.id,
                title,
                content,
                note.created_at.isoformat(),
                note.updated_at.isoformat() if note.updated_at else "",
                tags,
                "1" if note.is_shared else "0",
                note.ai_summary or "",
            ])
            if on_progress:
                on_progress(int(index / total * 80))


def export_md7z(
    notes: list[models.Note],
    output_path: Path,
    file_lookup: dict[str, str] | None = None,
    on_progress: Callable[[int], None] | None = None,
):
    total = len(notes) or 1
    with tempfile.TemporaryDirectory() as tmp_dir:
        base = Path(tmp_dir)
        assets_root = base / "assets"
        assets_root.mkdir(exist_ok=True)
        copied: set[str] = set()
        for index, note in enumerate(notes, start=1):
            title = normalize_title(note.body_md)
            tags = extract_tags(note.body_md)
            safe_title = SAFE_FILENAME_RE.sub("_", title)
            file_name = f"{note.id}_{safe_title}.md"
            markdown_body = note.body_md or ""
            if file_lookup:
                markdown_body = _rewrite_markdown_with_assets(markdown_body, file_lookup, assets_root, copied)
            content = [
                "---",
                f"id: {note.id}",
                f"title: {title}",
                f"created_at: {note.created_at.isoformat()}",
                f"updated_at: {note.updated_at.isoformat() if note.updated_at else ''}",
                f"tags: {tags}",
                f"is_shared: {note.is_shared}",
                f"ai_summary: {note.ai_summary or ''}",
                "---",
                "",
                markdown_body,
            ]
            (base / file_name).write_text("\n".join(content), encoding="utf-8")
            if on_progress:
                on_progress(int(index / total * 80))

        filters = [{"id": py7zr.FILTER_LZMA2, "preset": 7}]
        with py7zr.SevenZipFile(output_path, "w", filters=filters) as archive:
            archive.writeall(base, arcname="notes")
        if on_progress:
            on_progress(100)


def _rewrite_markdown_with_assets(
    markdown_text: str,
    file_lookup: dict[str, str],
    assets_root: Path,
    copied: set[str],
) -> str:
    def replace(match: re.Match) -> str:
        file_type = match.group(1)
        raw_name = match.group(2)
        file_name = raw_name.split("?")[0].split("#")[0]
        lookup_key = f"/notes/files/{file_type}/{file_name}"
        file_path = file_lookup.get(lookup_key)
        if file_path and file_path not in copied:
            target_dir = assets_root / file_type
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / file_name
            if not target_path.exists():
                try:
                    shutil.copy2(file_path, target_path)
                except FileNotFoundError:
                    pass
            copied.add(file_path)
        return f"./assets/{file_type}/{file_name}"

    return FILE_LINK_RE.sub(replace, markdown_text)
