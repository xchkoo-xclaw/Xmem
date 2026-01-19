from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .. import models, schemas
from ..auth import create_access_token, verify_password, get_current_user, hash_password, validate_password_strength
from ..db import get_session

router = APIRouter(prefix="/auth", tags=["auth"])

async def write_login_audit(
    session: AsyncSession,
    *,
    email: str,
    user_id: int | None,
    success: bool,
    request: Request,
    reason: str | None = None,
) -> None:
    """写入登录审计日志。"""
    ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    origin = request.headers.get("origin")

    log = models.LoginAuditLog(
        email=email,
        user_id=user_id,
        success=success,
        ip=ip,
        user_agent=user_agent,
        origin=origin,
        reason=reason,
    )
    session.add(log)
    await session.commit()


@router.post("/register", response_model=schemas.UserOut)
async def register(payload: schemas.UserCreate, session: AsyncSession = Depends(get_session)):
    """注册新用户（后端负责密码强度校验与哈希存储）。"""
    # 将邮箱转换为小写，确保数据库中统一存储小写邮箱
    email_lower = payload.email.lower()
    
    exists = await session.execute(select(models.User).where(models.User.email == email_lower))
    if exists.scalars().first():
        raise HTTPException(status_code=400, detail="邮箱已被注册")

    if not payload.password or not payload.password.strip():
        raise HTTPException(status_code=400, detail="密码不能为空")

    validate_password_strength(payload.password)
    hashed = hash_password(payload.password)

    user = models.User(
        email=email_lower,
        user_name=payload.user_name,
        hashed_password=hashed
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.post("/login", response_model=schemas.Token)
async def login(payload: schemas.UserCreate, request: Request, session: AsyncSession = Depends(get_session)):
    """登录并签发 JWT，同时记录登录审计日志。"""
    # 将邮箱转换为小写，确保与数据库中的小写邮箱匹配
    email_lower = payload.email.lower()
    
    result = await session.execute(select(models.User).where(models.User.email == email_lower))
    user = result.scalars().first()
    if not user:
        await write_login_audit(
            session,
            email=email_lower,
            user_id=None,
            success=False,
            request=request,
            reason="user_not_found",
        )
        raise HTTPException(status_code=401, detail="邮箱或密码错误")

    if not verify_password(payload.password, user.hashed_password):
        await write_login_audit(
            session,
            email=email_lower,
            user_id=user.id,
            success=False,
            request=request,
            reason="wrong_password",
        )
        raise HTTPException(status_code=401, detail="邮箱或密码错误")

    await write_login_audit(
        session,
        email=email_lower,
        user_id=user.id,
        success=True,
        request=request,
        reason=None,
    )
    token = create_access_token({"sub": str(user.id)})
    return schemas.Token(access_token=token)


@router.get("/me", response_model=schemas.UserOut)
async def me(current_user: models.User = Depends(get_current_user)):
    """返回当前登录用户信息。"""
    return current_user


@router.post("/change-password")
async def change_password(
    payload: schemas.PasswordChange,
    current_user: models.User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """修改密码（校验旧密码 + 强度校验 + 哈希加盐存储）。"""
    # 验证旧密码
    if not verify_password(payload.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="原密码错误")
    
    validate_password_strength(payload.new_password)
    current_user.hashed_password = hash_password(payload.new_password)
    await session.commit()
    return {"message": "密码修改成功"}

