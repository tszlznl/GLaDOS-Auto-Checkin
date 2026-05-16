"""
GLaDOS 自动签到脚本
支持多账号、多种推送渠道、重试机制、日志脱敏
"""
import os
import json
import time
import random
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from functools import wraps
import requests

from config import config
from pushers import push_all


# ---------- 枚举和类型定义 ----------
class CheckinStatus(Enum):
    """签到状态"""
    SUCCESS = "ok"
    REPEAT = "repeat"
    FAIL = "fail"


@dataclass
class AccountInfo:
    """账号信息"""
    index: int
    email: str
    status: str
    earned_points: int
    total_points: str
    remaining_days: str


@dataclass
class CheckinResult:
    """签到结果"""
    ok: int = 0
    fail: int = 0
    repeat: int = 0
    accounts: List[AccountInfo] = None  # type: ignore

    def __post_init__(self):
        if self.accounts is None:
            self.accounts = []


# ---------- 工具函数 ----------
def retry_on_failure(max_retries: int = None, min_wait: float = None, max_wait: float = None):
    """
    重试装饰器
    Args:
        max_retries: 最大重试次数
        min_wait: 最小等待时间（秒）
        max_wait: 最大等待时间（秒）
    """
    max_retries = max_retries or config.api.MAX_RETRY
    min_wait = min_wait or config.api.RETRY_MIN_WAIT
    max_wait = max_wait or config.api.RETRY_MAX_WAIT

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait_time = min(min_wait * (2 ** attempt), max_wait)
                        print(f"⚠️ 第 {attempt + 1} 次尝试失败: {e}，{wait_time:.1f}秒后重试...")
                        time.sleep(wait_time)
            raise last_exception  # type: ignore
        return wrapper
    return decorator


def mask_email(email: str) -> str:
    """
    邮箱脱敏处理
    Args:
        email: 原始邮箱地址
    Returns:
        脱敏后的邮箱地址
    Examples:
        >>> mask_email("test@example.com")
        'te***@example.com'
        >>> mask_email("a@b.com")
        'a***@b.com'
        >>> mask_email("unknown")
        'unknown'
    """
    if not email or email == "unknown":
        return email

    if "@" not in email:
        return email

    try:
        name, domain = email.rsplit("@", 1)
        if len(name) <= 2:
            masked_name = f"{name[0] if name else ''}***"
        else:
            masked_name = f"{name[:2]}***"
        return f"{masked_name}@{domain}"
    except Exception:
        return email


def mask_cookie(cookie: str) -> str:
    """
    Cookie 脱敏处理（用于日志输出）
    Args:
        cookie: 原始 Cookie
    Returns:
        脱敏后的 Cookie（只显示前后各10个字符）
    """
    if not cookie or len(cookie) <= 20:
        return "***"
    return f"{cookie[:10]}...{cookie[-10:]}"


def validate_cookie(cookie: str) -> Tuple[bool, str]:
    """
    验证 Cookie 格式
    Args:
        cookie: Cookie 字符串
    Returns:
        (是否有效, 错误信息)
    """
    if not cookie or not cookie.strip():
        return False, "Cookie 为空"

    cookie = cookie.strip()

    # 检查是否包含必要的字段
    required_patterns = [
        r"koa:sess",
        r"koa:sess\.sig",
    ]

    for pattern in required_patterns:
        if not re.search(pattern, cookie, re.IGNORECASE):
            return False, f"Cookie 缺少必要字段: {pattern}"

    return True, ""


def safe_json(resp: requests.Response) -> Dict[str, Any]:
    """安全解析 JSON 响应"""
    try:
        return resp.json()
    except Exception:
        return {}


# ---------- 签到逻辑 ----------
def classify_checkin(code: int, message: str) -> CheckinStatus:
    """
    判断签到结果
    Args:
        code: API 返回的状态码
        message: API 返回的消息
    Returns:
        签到状态枚举值
    """
    if code == 0:
        return CheckinStatus.SUCCESS
    if code == 1:
        return CheckinStatus.REPEAT

    # 兜底：关键词匹配
    msg = message.lower()
    if "got" in msg:
        return CheckinStatus.SUCCESS
    if any(kw in msg for kw in ("repeat", "already", "重复", "已签到", "签到过", "请勿")):
        return CheckinStatus.REPEAT

    return CheckinStatus.FAIL


@retry_on_failure()
def checkin_request(
    session: requests.Session,
    url: str,
    headers: Dict[str, str],
    payload: Dict[str, str],
    timeout: int
) -> Dict[str, Any]:
    """
    执行签到请求（带重试）
    """
    r = session.post(
        url,
        headers=headers,
        data=json.dumps(payload),
        timeout=timeout,
    )
    return safe_json(r)


@retry_on_failure()
def get_status(
    session: requests.Session,
    url: str,
    headers: Dict[str, str],
    timeout: int
) -> Dict[str, Any]:
    """
    获取账号状态（带重试）
    """
    r = session.get(url, headers=headers, timeout=timeout)
    return safe_json(r)


def checkin_account(
    session: requests.Session,
    cookie: str,
    index: int
) -> AccountInfo:
    """
    执行单个账号的签到
    Args:
        session: requests Session 对象
        cookie: 账号 Cookie
        index: 账号序号
    Returns:
        账号信息
    """
    headers = dict(config.request.headers_base)
    headers["cookie"] = cookie

    email = "unknown"
    days = "-"
    total_points = "-"
    earned = 0
    status = ""

    try:
        # 1. 签到
        j = checkin_request(
            session,
            config.api.CHECKIN_URL,
            headers,
            config.request.PAYLOAD,
            config.api.TIMEOUT,
        )
        code = j.get("code", -2)
        message = j.get("message", "")
        earned = j.get("points", 0) or 0

        result = classify_checkin(code, message)

        if result == CheckinStatus.SUCCESS:
            status = f"✅ 成功 (+{earned}积分)"
        elif result == CheckinStatus.REPEAT:
            status = "🔄 已签到"
        else:
            status = f"❌ 失败({message})"

        # 2. 查询账号状态
        try:
            s = get_status(session, config.api.STATUS_URL, headers, config.api.TIMEOUT)
            data = s.get("data") or {}
            email = data.get("email", email)
            if data.get("leftDays") is not None:
                days = f"{int(float(data['leftDays']))} 天"
        except Exception:
            pass  # 状态查询失败不影响签到结果

        # 3. 查询总积分
        try:
            p = get_status(session, config.api.POINTS_URL, headers, config.api.TIMEOUT)
            if p.get("points") is not None:
                total_points = f"{int(float(p['points']))} 积分"
        except Exception:
            pass  # 积分查询失败不影响签到结果

    except Exception as e:
        status = f"❌ 异常({e})"

    # 邮箱脱敏
    masked_email = mask_email(email)

    return AccountInfo(
        index=index,
        email=masked_email,
        status=status,
        earned_points=earned,
        total_points=total_points,
        remaining_days=days,
    )


def main() -> None:
    """主函数"""
    # 解析 Cookie
    cookies = [c.strip() for c in os.getenv("COOKIES", "").split("&") if c.strip()]

    if not cookies:
        push_all("GLaDOS 签到", "❌ 未检测到 COOKIES，请配置 GitHub Secrets")
        return

    print(f"📋 检测到 {len(cookies)} 个账号")

    # 验证 Cookie 格式
    for idx, cookie in enumerate(cookies, 1):
        is_valid, error_msg = validate_cookie(cookie)
        if not is_valid:
            print(f"⚠️ 账号 {idx} Cookie 格式异常: {error_msg}")
            print(f"   Cookie 片段: {mask_cookie(cookie)}")

    session = requests.Session()
    result = CheckinResult()

    for idx, cookie in enumerate(cookies, 1):
        print(f"\n🔄 正在处理账号 {idx}/{len(cookies)}...")

        account = checkin_account(session, cookie, idx)
        result.accounts.append(account)

        # 统计结果
        if "✅" in account.status:
            result.ok += 1
        elif "🔄" in account.status:
            result.repeat += 1
        else:
            result.fail += 1

        # 非最后一个账号时随机延迟
        if idx < len(cookies):
            delay = random.uniform(config.delay.MIN_DELAY, config.delay.MAX_DELAY)
            time.sleep(delay)

    # 生成报告
    lines = []
    for acc in result.accounts:
        lines.append(
            f"{acc.index}. {acc.email} | {acc.status} | "
            f"总积分:{acc.total_points} | 剩余:{acc.remaining_days}"
        )

    title = f"GLaDOS 签到完成 ✅{result.ok} ❌{result.fail} 🔄{result.repeat}"
    content = "\n".join(lines)

    print(f"\n{'='*50}")
    print(content)
    print(f"{'='*50}")

    push_all(title, content)


if __name__ == "__main__":
    main()
