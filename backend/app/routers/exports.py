import asyncio
import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models, schemas
from ..auth import get_current_user
from ..db import get_session, AsyncSessionLocal
from ..services.note_export import (
    EXPORT_DIR,
    compute_sha256,
    export_csv,
    export_md7z,
    estimate_csv_size,
    estimate_md7z_size,
    write_checksum_report,
)

router = APIRouter(prefix="/notes/exports", tags=["notes"])


def _ensure_export_dir(user_id: int) -> Path:
    user_dir = EXPORT_DIR / f"user_{user_id}"
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


async def _load_notes(
    session: AsyncSession,
    user_id: int,
    note_ids: list[int] | None,
    include_all: bool,
) -> list[models.Note]:
    if include_all:
        stmt = select(models.Note).where(models.Note.user_id == user_id).order_by(models.Note.created_at.desc())
    else:
        ids = note_ids or []
        if not ids:
            return []
        stmt = select(models.Note).where(
            models.Note.user_id == user_id,
            models.Note.id.in_(ids),
        ).order_by(models.Note.created_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


def _make_file_name(export_type: str) -> str:
    if export_type == "csv":
        return "notes_export.csv"
    return "notes_export.7z"


def _parse_range_header(range_header: str, file_size: int) -> tuple[int, int]:
    match = re.match(r"bytes=(\d+)-(\d*)", range_header)
    if not match:
        raise HTTPException(status_code=416, detail="无效的 Range 请求")
    start = int(match.group(1))
    end = int(match.group(2)) if match.group(2) else file_size - 1
    if start >= file_size or end < start:
        raise HTTPException(status_code=416, detail="无效的 Range 请求")
    return start, min(end, file_size - 1)


async def _run_export_job(job_id: int):
    async with AsyncSessionLocal() as session:
        job = await session.get(models.ExportJob, job_id)
        if not job:
            return
        job.status = "processing"
        job.progress = 0
        job.error_message = None
        await session.commit()

        notes = await _load_notes(session, job.user_id, job.note_ids, include_all=False)
        if not notes:
            job.status = "failed"
            job.error_message = "未找到可导出的笔记"
            await session.commit()
            return
        note_ids = [note.id for note in notes]
        file_lookup: dict[str, str] = {}
        if note_ids:
            stmt = select(models.File).where(
                models.File.user_id == job.user_id,
                models.File.note_id.in_(note_ids),
            )
            result = await session.execute(stmt)
            for db_file in result.scalars().all():
                file_lookup[db_file.url_path] = db_file.file_path

        user_dir = _ensure_export_dir(job.user_id)
        file_name = _make_file_name(job.export_type)
        file_path = user_dir / f"{job.id}_{file_name}"

        def update_progress(value: int):
            asyncio.create_task(_update_job_progress(job.id, value))

        try:
            if job.export_type == "csv":
                export_csv(notes, file_path, on_progress=update_progress)
            elif job.export_type == "md7z":
                export_md7z(notes, file_path, file_lookup=file_lookup, on_progress=update_progress)
            else:
                raise ValueError("不支持的导出类型")

            checksum = compute_sha256(file_path)
            report_path = write_checksum_report(file_path, checksum)
            job.file_path = str(file_path)
            job.file_name = file_name
            job.file_size = file_path.stat().st_size
            job.checksum_sha256 = checksum
            job.report_path = str(report_path)
            job.progress = 100
            job.status = "completed"
            await session.commit()
        except Exception as exc:
            job.status = "failed"
            job.error_message = str(exc)
            job.progress = 0
            await session.commit()


async def _update_job_progress(job_id: int, value: int):
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(models.ExportJob)
            .where(models.ExportJob.id == job_id)
            .values(progress=min(100, max(0, value)))
        )
        await session.commit()


@router.post("/estimate", response_model=schemas.NoteExportEstimateOut)
async def estimate_export(
    payload: schemas.NoteExportEstimateIn,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    notes = await _load_notes(session, current_user.id, payload.note_ids, payload.include_all)
    if payload.export_type == "csv":
        estimated = estimate_csv_size(notes)
    elif payload.export_type == "md7z":
        estimated = estimate_md7z_size(notes)
    else:
        raise HTTPException(status_code=400, detail="不支持的导出类型")
    return schemas.NoteExportEstimateOut(estimated_size=estimated)


@router.post("", response_model=schemas.NoteExportJobOut)
async def create_export(
    payload: schemas.NoteExportCreateIn,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    notes = await _load_notes(session, current_user.id, payload.note_ids, payload.include_all)
    if not notes:
        raise HTTPException(status_code=400, detail="未选择任何可导出的笔记")
    if payload.export_type not in {"csv", "md7z"}:
        raise HTTPException(status_code=400, detail="不支持的导出类型")

    job = models.ExportJob(
        user_id=current_user.id,
        export_type=payload.export_type,
        status="processing",
        progress=0,
        note_ids=[note.id for note in notes],
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)

    asyncio.create_task(_run_export_job(job.id))
    return schemas.NoteExportJobOut.model_validate(job)


@router.get("", response_model=list[schemas.NoteExportJobOut])
async def list_exports(
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    stmt = select(models.ExportJob).where(models.ExportJob.user_id == current_user.id).order_by(models.ExportJob.created_at.desc())
    result = await session.execute(stmt)
    jobs = result.scalars().all()
    return [schemas.NoteExportJobOut.model_validate(job) for job in jobs]


@router.delete("")
async def clear_exports(
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    stmt = select(models.ExportJob).where(models.ExportJob.user_id == current_user.id)
    result = await session.execute(stmt)
    jobs = result.scalars().all()
    for job in jobs:
        if job.file_path:
            file_path = Path(job.file_path)
            if file_path.exists():
                file_path.unlink()
        if job.report_path:
            report_path = Path(job.report_path)
            if report_path.exists():
                report_path.unlink()
        await session.delete(job)
    await session.commit()
    return {"status": "ok"}


@router.get("/{export_id}", response_model=schemas.NoteExportJobOut)
async def get_export(
    export_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    job = await session.get(models.ExportJob, export_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="导出记录不存在")
    return schemas.NoteExportJobOut.model_validate(job)


@router.get("/{export_id}/download")
async def download_export(
    export_id: int,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    job = await session.get(models.ExportJob, export_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="导出记录不存在")
    if job.status == "expired":
        raise HTTPException(status_code=410, detail="导出已过期")
    if not job.file_path or not job.file_name:
        raise HTTPException(status_code=404, detail="导出文件未生成")
    file_path = Path(job.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="导出文件不存在")

    range_header = request.headers.get("range")
    file_size = file_path.stat().st_size
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Disposition": f'attachment; filename="{job.file_name}"',
    }
    if not range_header:
        return FileResponse(file_path, headers=headers)

    start, end = _parse_range_header(range_header, file_size)
    length = end - start + 1

    def iter_file():
        with open(file_path, "rb") as f:
            f.seek(start)
            remaining = length
            while remaining > 0:
                chunk = f.read(min(1024 * 1024, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk

    headers.update({
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Content-Length": str(length),
    })
    return StreamingResponse(iter_file(), status_code=206, headers=headers, media_type="application/octet-stream")


@router.get("/{export_id}/checksum-report")
async def download_checksum_report(
    export_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    job = await session.get(models.ExportJob, export_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="导出记录不存在")
    if job.status == "expired":
        raise HTTPException(status_code=410, detail="导出已过期")
    if not job.report_path:
        raise HTTPException(status_code=404, detail="校验报告未生成")
    report_path = Path(job.report_path)
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="校验报告不存在")
    headers = {"Content-Disposition": f'attachment; filename="{report_path.name}"'}
    return FileResponse(report_path, headers=headers, media_type="text/plain")
