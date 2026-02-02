import os
import re
import inspect
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from .. import models, schemas
from ..db import get_session
from ..auth import get_current_user, get_optional_user
from ..utils.file_utils import save_uploaded_img, save_uploaded_file
from ..services.ai import generate_note_summary, generate_note_todos

router = APIRouter(prefix="/notes", tags=["notes"])
public_router = APIRouter(prefix="/notes", tags=["notes"])

# 文件上传目录
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
IMAGE_DIR = UPLOAD_DIR / "images"
FILE_DIR = UPLOAD_DIR / "files"
IMAGE_DIR.mkdir(exist_ok=True)
FILE_DIR.mkdir(exist_ok=True)

# 文件大小限制：5MB
MAX_FILE_SIZE = 5 * 1024 * 1024


def clean_markdown_for_search(markdown_text: str) -> str:
    """移除 markdown 中的图片和链接语法，只保留纯文本用于搜索"""
    if not markdown_text:
        return ""
    
    text = markdown_text
    # 移除图片语法: ![alt](url) - 完全移除，只保留 alt 文本（如果有）
    text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'\1', text)
    # 移除链接语法: [text](url) - 只保留链接文本
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    return text


def markdown_references_uploaded_files(markdown_text: str) -> bool:
    """判断 markdown 是否引用了已上传的 notes 文件资源路径"""
    if not markdown_text:
        return False
    return "/notes/files/" in markdown_text


def extract_referenced_image_urls(markdown_text: str) -> list[str]:
    """从 markdown 中提取被引用的图片 URL（/notes/files/images/* 或 /notes/share-files/images/*）"""
    if not markdown_text:
        return []
    urls = re.findall(r"\((/notes/(?:share-files|files)/images/[^)\s]+)\)", markdown_text)
    seen = set()
    result: list[str] = []
    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        result.append(url)
    return result


def rewrite_markdown_for_share(markdown_text: str, share_uuid: str, share_user_id: int) -> str:
    """将受保护资源链接改写为分享专用的下载/图片路径。"""
    if not markdown_text:
        return ""

    def replace_path(match: re.Match) -> str:
        file_type = match.group(1)
        raw_name = match.group(2)
        file_name = raw_name.split("?")[0].split("#")[0]
        return (
            f"/notes/share-files/{file_type}/{file_name}"
            f"?note-uuid={share_uuid}&share-user-id={share_user_id}"
        )

    return re.sub(r"/notes/files/(images|files)/([^\s)]+)", replace_path, markdown_text)


def build_note_out(note: models.Note) -> schemas.NoteOut:
    """构造 NoteOut，补齐 images/files 等计算字段"""
    return schemas.NoteOut(
        id=note.id,
        body_md=note.body_md,
        ai_summary=getattr(note, "ai_summary", None),
        is_pinned=bool(note.is_pinned),
        is_shared=bool(getattr(note, "is_shared", False)),
        share_uuid=getattr(note, "share_uuid", None),
        created_at=note.created_at,
        updated_at=note.updated_at,
        images=extract_referenced_image_urls(note.body_md),
        files=None,
    )


def build_todo_out(todo: models.Todo) -> schemas.TodoOut:
    return schemas.TodoOut(
        id=todo.id,
        title=todo.title,
        completed=bool(todo.completed),
        is_pinned=bool(todo.is_pinned),
        is_ai_generated=bool(getattr(todo, "is_ai_generated", False)),
        group_id=todo.group_id,
        created_at=todo.created_at,
        group_items=None,
    )


def build_share_link(note_uuid: str, share_user_id: int, request: Request) -> str:
    """构造前端分享链接地址。"""
    origin = request.headers.get("origin")
    base_url = (origin or str(request.base_url)).rstrip("/")
    return f"{base_url}/view-share-note/?note-uuid={note_uuid}&share-user-id={share_user_id}"


def build_share_note_out(
    note: models.Note,
    share_user: models.User,
    can_edit: bool,
    share_uuid: str,
    share_user_id: int,
) -> schemas.NoteShareOut:
    """构造分享场景的 Note 输出结构。"""
    shared_body = rewrite_markdown_for_share(note.body_md, share_uuid, share_user_id)
    return schemas.NoteShareOut(
        id=note.id,
        body_md=shared_body,
        ai_summary=getattr(note, "ai_summary", None),
        is_pinned=bool(note.is_pinned),
        created_at=note.created_at,
        updated_at=note.updated_at,
        images=extract_referenced_image_urls(shared_body),
        files=None,
        share_user=share_user,
        can_edit=can_edit,
    )


async def link_files_to_note(session: AsyncSession, note_id: int, body_md: str, user_id: int):
    """
    解析 markdown 内容，将引用的文件与笔记关联
    """
    # 1. 解除该笔记之前关联的所有文件
    stmt = select(models.File).where(models.File.note_id == note_id)
    result = await session.execute(stmt)
    scalars = result.scalars()
    if inspect.isawaitable(scalars):
        scalars = await scalars
    existing_files = scalars.all()
    if inspect.isawaitable(existing_files):
        existing_files = await existing_files
    for f in existing_files:
        f.note_id = None
    
    if not body_md:
        return

    # 2. 解析 markdown 中的 URL
    # 匹配图片 ![]() 和 链接 []()
    # 提取 () 中的内容
    urls = re.findall(r'\((.*?)\)', body_md)
    
    potential_paths = set()
    for url in urls:
        # 简单清洗 URL
        clean_url = url.split('?')[0].split('#')[0]
        filename = Path(clean_url).name
        if not filename:
            continue
            
        # 构造可能的数据库存储路径
        # 我们知道上传的文件只会在 images 或 files 目录下
        potential_paths.add(f"/notes/files/images/{filename}")
        potential_paths.add(f"/notes/files/files/{filename}")
    
    if not potential_paths:
        return

    # 3. 查找并关联
    stmt = select(models.File).where(
        models.File.user_id == user_id,
        models.File.url_path.in_(potential_paths)
    )
    result = await session.execute(stmt)
    scalars = result.scalars()
    if inspect.isawaitable(scalars):
        scalars = await scalars
    files_to_link = scalars.all()
    if inspect.isawaitable(files_to_link):
        files_to_link = await files_to_link
    
    for f in files_to_link:
        f.note_id = note_id


@router.get("", response_model=list[schemas.NoteOut])
async def list_notes(
    q: str | None = None,
    session: AsyncSession = Depends(get_session), 
    current_user: models.User = Depends(get_current_user)
):
    """
    获取所有笔记 如果有搜索关键词则过滤
    Args:
        q: 搜索关键词
    Returns:
        list[schemas.NoteOut]: 笔记列表
    """
    # 先获取所有笔记，按置顶优先，然后按创建时间倒序
    query = select(models.Note).where(models.Note.user_id == current_user.id)
    query = query.order_by(models.Note.is_pinned.desc(), models.Note.created_at.desc())
    result = await session.execute(query)
    notes = result.scalars().all()
    
    # 如果有搜索关键词，在 Python 层面过滤（排除 markdown 图片和链接语法）
    if q is not None and q.strip():
        q_trimmed = q.strip().lower()
        filtered_notes = []
        for note in notes:
            # 清理 markdown 语法后搜索
            cleaned_text = clean_markdown_for_search(note.body_md or "")
            if q_trimmed in cleaned_text.lower():
                filtered_notes.append(note)
        return [build_note_out(n) for n in filtered_notes]
    
    return [build_note_out(n) for n in notes]


@router.post("", response_model=schemas.NoteOut)
async def create_note(
    payload: schemas.NoteCreate,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    if not payload.body_md or not payload.body_md.strip():
        raise HTTPException(status_code=400, detail="笔记内容不能为空")
    note = models.Note(
        user_id=current_user.id,
        body_md=payload.body_md
    )
    session.add(note)
    await session.commit()
    await session.refresh(note)
    
    # 关联文件
    if markdown_references_uploaded_files(note.body_md):
        await link_files_to_note(session, note.id, note.body_md, current_user.id)
        await session.commit()
    
    return build_note_out(note)


@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """上传图片（暂不校验大小）"""
    # 使用通用函数保存图片文件
    file_path = await save_uploaded_img(file, IMAGE_DIR)
    
    # 从完整路径中提取文件名
    file_name = Path(file_path).name
    url_path = f"/notes/files/images/{file_name}"
    
    # 记录到数据库
    db_file = models.File(
        user_id=current_user.id,
        file_path=str(file_path),
        url_path=url_path,
        file_type="image"
    )
    session.add(db_file)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
    
    # 返回URL（使用相对路径，前端会拼接baseURL）
    return {"url": url_path}


@router.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """上传文件（校验大小）"""
    # 使用通用函数保存文件（包含大小验证）
    original_name = file.filename or "file"
    file_path, content = await save_uploaded_file(file, FILE_DIR, max_size=MAX_FILE_SIZE, default_ext=Path(original_name).suffix)
    
    # 从完整路径中提取文件名
    file_name = Path(file_path).name
    url_path = f"/notes/files/files/{file_name}"
    
    # 记录到数据库
    db_file = models.File(
        user_id=current_user.id,
        file_path=str(file_path),
        url_path=url_path,
        file_type="file"
    )
    session.add(db_file)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
    
    # 返回文件信息（使用相对路径，前端会拼接baseURL）
    return {
        "name": original_name,
        "url": url_path,
        "size": len(content)
    }

@router.get("/files/{file_type}/{file_name}")
async def get_note_file(
    file_type: str,
    file_name: str,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """需要鉴权的文件下载端点
    限制下载权限到“当前登录用户且文件已关联到其笔记”，防止公开链接被滥用和越权访问
    """
    # 构造数据库中记录的 url_path，统一匹配方式
    url_path = f"/notes/files/{file_type}/{file_name}"
    # 必须是当前用户的文件
    # 注意：不再强制要求已关联到笔记，以便用户在创建笔记时能预览刚上传（但未保存）的图片
    stmt = select(models.File).where(
        models.File.user_id == current_user.id,
        models.File.url_path == url_path,
    )
    result = await session.execute(stmt)
    db_file = result.scalars().first()
    if not db_file:
        raise HTTPException(status_code=404, detail="文件不存在或未关联到当前用户的笔记")
    # 物理文件存在性校验
    file_path = Path(db_file.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(file_path)


@router.post("/{note_id}/share", response_model=schemas.NoteShareLinkOut)
async def share_note(
    note_id: int,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """生成或返回笔记分享链接。"""
    result = await session.execute(
        select(models.Note).where(models.Note.id == note_id, models.Note.user_id == current_user.id)
    )
    note = result.scalars().first()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")

    if not note.share_uuid:
        note.share_uuid = uuid.uuid4().hex
    note.is_shared = True
    await session.commit()
    await session.refresh(note)

    return schemas.NoteShareLinkOut(
        note_uuid=note.share_uuid,
        share_user_id=current_user.id,
        share_url=build_share_link(note.share_uuid, current_user.id, request),
    )


@router.patch("/{note_id}/share-toggle", response_model=schemas.NoteShareStatusOut)
async def toggle_share_note(
    note_id: int,
    payload: schemas.NoteShareToggleIn,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """切换笔记分享状态：公开/私密。"""
    result = await session.execute(
        select(models.Note).where(models.Note.id == note_id, models.Note.user_id == current_user.id)
    )
    note = result.scalars().first()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")

    if payload.is_shared:
        if not note.share_uuid:
            note.share_uuid = uuid.uuid4().hex
        note.is_shared = True
        await session.commit()
        await session.refresh(note)
        return schemas.NoteShareStatusOut(
            is_shared=True,
            note_uuid=note.share_uuid,
            share_user_id=current_user.id,
            share_url=build_share_link(note.share_uuid, current_user.id, request),
        )
    else:
        note.is_shared = False
        await session.commit()
        await session.refresh(note)
        return schemas.NoteShareStatusOut(
            is_shared=False,
            note_uuid=note.share_uuid,
            share_user_id=current_user.id,
            share_url=None,
        )


@public_router.get("/share", response_model=schemas.NoteShareOut)
async def get_shared_note(
    note_uuid: str,
    share_user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: models.User | None = Depends(get_optional_user),
):
    """获取分享笔记内容（仅在已分享状态下返回）。"""
    result = await session.execute(
        select(models.Note).where(
            models.Note.share_uuid == note_uuid,
            models.Note.user_id == share_user_id,
            models.Note.is_shared.is_(True),
        )
    )
    note = result.scalars().first()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在或未分享")

    result = await session.execute(select(models.User).where(models.User.id == share_user_id))
    share_user = result.scalars().first()
    if not share_user:
        raise HTTPException(status_code=404, detail="分享人不存在")

    can_edit = current_user is not None and current_user.id == note.user_id
    return build_share_note_out(note, share_user, can_edit, note_uuid, share_user_id)


@public_router.get("/share-files/{file_type}/{file_name}")
async def get_shared_note_file(
    file_type: str,
    file_name: str,
    note_uuid: str,
    share_user_id: int,
    session: AsyncSession = Depends(get_session),
):
    """下载分享笔记关联的文件或图片。"""
    if file_type not in {"images", "files"}:
        raise HTTPException(status_code=404, detail="文件不存在")

    result = await session.execute(
        select(models.Note).where(
            models.Note.share_uuid == note_uuid,
            models.Note.user_id == share_user_id,
            models.Note.is_shared.is_(True),
        )
    )
    note = result.scalars().first()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在或未分享")

    url_path = f"/notes/files/{file_type}/{file_name}"
    result = await session.execute(
        select(models.File).where(models.File.note_id == note.id, models.File.url_path == url_path)
    )
    db_file = result.scalars().first()
    if not db_file:
        raise HTTPException(status_code=404, detail="文件不存在或未关联到分享笔记")

    file_path = Path(db_file.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(file_path)




@router.patch("/{note_id}", response_model=schemas.NoteOut)
async def update_note(
    note_id: int,
    payload: schemas.NoteCreate,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    result = await session.execute(
        select(models.Note).where(models.Note.id == note_id, models.Note.user_id == current_user.id)
    )
    note = result.scalars().first()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    
    if not payload.body_md or not payload.body_md.strip():
        raise HTTPException(status_code=400, detail="笔记内容不能为空")
    
    note.body_md = payload.body_md
    
    # 关联文件
    if payload.body_md is not None and markdown_references_uploaded_files(payload.body_md):
        await link_files_to_note(session, note.id, note.body_md, current_user.id)
    
    await session.commit()
    await session.refresh(note)
    return build_note_out(note)


@router.delete("/{note_id}")
async def delete_note(
    note_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    result = await session.execute(
        select(models.Note).where(models.Note.id == note_id, models.Note.user_id == current_user.id)
    )
    note = result.scalars().first()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
        
    # 查询关联的文件并删除物理文件
    stmt = select(models.File).where(models.File.note_id == note_id)
    result = await session.execute(stmt)
    files_to_delete = result.scalars().all()
    
    for f in files_to_delete:
        try:
            if os.path.exists(f.file_path):
                os.remove(f.file_path)
        except Exception as e:
            # 记录错误但继续执行
            print(f"Error deleting file {f.file_path}: {e}")
            
    await session.delete(note)
    await session.commit()
    return {"ok": True}


@router.patch("/{note_id}/pin", response_model=schemas.NoteOut)
async def toggle_pin_note(
    note_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    """切换笔记的置顶状态"""
    result = await session.execute(
        select(models.Note).where(models.Note.id == note_id, models.Note.user_id == current_user.id)
    )
    note = result.scalars().first()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    
    note.is_pinned = not note.is_pinned
    await session.commit()
    await session.refresh(note)
    return build_note_out(note)


@router.post("/{note_id}/ai-summary", response_model=schemas.NoteAiSummaryOut)
async def ai_note_summary(
    note_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    result = await session.execute(
        select(models.Note).where(models.Note.id == note_id, models.Note.user_id == current_user.id)
    )
    note = result.scalars().first()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    if not note.body_md or not note.body_md.strip():
        raise HTTPException(status_code=400, detail="笔记内容不能为空")
    try:
        summary = generate_note_summary(note.body_md)
        note.ai_summary = summary
        await session.commit()
        await session.refresh(note)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 总结失败: {str(e)}") from e
    return schemas.NoteAiSummaryOut(summary=summary)


@router.post("/{note_id}/ai-todos", response_model=schemas.NoteAiTodosOut)
async def ai_note_todos(
    note_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: models.User = Depends(get_current_user),
):
    result = await session.execute(
        select(models.Note).where(models.Note.id == note_id, models.Note.user_id == current_user.id)
    )
    note = result.scalars().first()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    if not note.body_md or not note.body_md.strip():
        raise HTTPException(status_code=400, detail="笔记内容不能为空")
    try:
        titles = generate_note_todos(note.body_md)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 待办生成失败: {str(e)}") from e
    if not titles:
        return schemas.NoteAiTodosOut(todos=[])

    group = models.Todo(
        user_id=current_user.id,
        title="AI 待办",
        is_ai_generated=True,
    )
    session.add(group)
    await session.commit()
    await session.refresh(group)

    todos: list[models.Todo] = []
    for title in titles:
        todo = models.Todo(
            user_id=current_user.id,
            title=title,
            group_id=group.id,
            is_ai_generated=True,
        )
        todos.append(todo)
    session.add_all(todos)
    await session.commit()
    for todo in todos:
        await session.refresh(todo)
    return schemas.NoteAiTodosOut(todos=[build_todo_out(group), *[build_todo_out(todo) for todo in todos]])
