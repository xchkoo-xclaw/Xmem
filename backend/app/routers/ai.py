from fastapi import APIRouter, Depends, HTTPException

from .. import models, schemas
from ..auth import get_current_user
from ..services import ai as ai_service

router = APIRouter(prefix="/ai", tags=["ai"])


def _truncate_text(text: str, limit: int = 800) -> str:
    """截断文本以避免上下文过长。"""
    if len(text) <= limit:
        return text
    return text[:limit] + "…"


def _build_context_text(context: schemas.ChatContext | None) -> str:
    """将笔记与记账上下文整理为模型可理解的文本。"""
    if not context:
        return ""
    lines: list[str] = []
    if context.notes:
        lines.append("【笔记】")
        for note in context.notes:
            body = _truncate_text(note.body_md or "")
            lines.append(f"- 笔记#{note.id}: {body}")
    if context.ledgers:
        lines.append("【记账】")
        for ledger in context.ledgers:
            raw = _truncate_text(ledger.raw_text or "")
            amount = f"{ledger.amount} {ledger.category}" if ledger.amount is not None else ledger.category or ""
            suffix = f"（金额/分类：{amount}）" if amount else ""
            lines.append(f"- 记账#{ledger.id}: {raw}{suffix}")
    return "\n".join(lines)


@router.post("/chat", response_model=schemas.ChatResponse)
async def chat(
    payload: schemas.ChatRequest,
    current_user: models.User = Depends(get_current_user),
):
    """AI 对话接口，支持携带笔记/记账上下文。"""
    if not payload.messages:
        raise HTTPException(status_code=400, detail="消息不能为空")
    context_text = _build_context_text(payload.context)
    try:
        reply = ai_service.generate_chat_response(
            [m.model_dump() for m in payload.messages],
            context_text=context_text,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"AI 对话失败: {str(error)}") from error
    return schemas.ChatResponse(reply=reply)
