import datetime as dt
import hashlib
import re
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .config import settings
from . import models
from .db import get_session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def verify_password(password: str, hashed: str) -> bool:
    """校验明文密码与数据库哈希是否匹配。"""
    try:
        return bcrypt.checkpw(_normalize_password_for_bcrypt(password), hashed.encode("utf-8"))
    except Exception:
        return False


def hash_password(password: str) -> str:
    """将明文密码哈希加盐后存储。"""
    hashed = bcrypt.hashpw(_normalize_password_for_bcrypt(password), bcrypt.gensalt(rounds=12))
    return hashed.decode("utf-8")


def _normalize_password_for_bcrypt(password: str) -> bytes:
    """将密码标准化为适配 bcrypt 的输入（超过 72 bytes 先做 SHA-256 预哈希）。"""
    raw = (password or "").encode("utf-8")
    if len(raw) <= 72:
        return raw
    return hashlib.sha256(raw).digest()


def validate_password_strength(password: str) -> None:
    """校验密码强度，不满足则抛出 400。"""
    issues: list[str] = []
    if password is None:
        issues.append("密码不能为空")
    else:
        pw = password.strip()
        if len(pw) < settings.password_min_length:
            issues.append(f"密码长度至少 {settings.password_min_length} 位")
        # if settings.password_require_upper and not re.search(r"[A-Z]", pw):
        #     issues.append("密码需包含大写字母")
        # if settings.password_require_lower and not re.search(r"[a-z]", pw):
        #     issues.append("密码需包含小写字母")
        # if settings.password_require_digit and not re.search(r"\d", pw):
        #     issues.append("密码需包含数字")
        # if settings.password_require_symbol and not re.search(r"[^A-Za-z0-9]", pw):
        #     issues.append("密码需包含符号")
        if settings.password_max_length and len(pw) > settings.password_max_length:
            issues.append(f"密码长度不能超过 {settings.password_max_length} 位")
        if settings.password_disallow_whitespace and re.search(r"\s", password):
            issues.append("密码不能包含空白字符")

    if issues:
        raise HTTPException(status_code=400, detail="；".join(issues))


def create_access_token(data: dict, expires_minutes: Optional[int] = None) -> str:
    """生成带过期时间的 JWT Access Token。"""
    to_encode = data.copy()
    expire = dt.datetime.now(dt.timezone.utc) + dt.timedelta(
        minutes=expires_minutes or settings.access_token_expire_minutes
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_session)
) -> models.User:
    """从 Authorization: Bearer <token> 中解析当前用户。"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证身份",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id: int = int(payload.get("sub"))
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await session.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    return user

