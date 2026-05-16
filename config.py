"""
GLaDOS 自动签到配置模块
集中管理所有配置常量
"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass(frozen=True)
class APIConfig:
    """API 相关配置"""
    CHECKIN_URL: str = "https://glados.cloud/api/user/checkin"
    STATUS_URL: str = "https://glados.cloud/api/user/status"
    POINTS_URL: str = "https://glados.cloud/api/user/points"
    TIMEOUT: int = 12
    MAX_RETRY: int = 3
    RETRY_MIN_WAIT: float = 2.0
    RETRY_MAX_WAIT: float = 10.0


@dataclass(frozen=True)
class RequestConfig:
    """请求头配置"""
    ORIGIN: str = "https://glados.cloud"
    REFERER: str = "https://glados.cloud/console/checkin"
    USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    CONTENT_TYPE: str = "application/json;charset=UTF-8"
    PAYLOAD: Dict[str, str] = None  # type: ignore

    def __post_init__(self):
        # 使用 object.__setattr__ 因为 dataclass 是 frozen 的
        object.__setattr__(self, 'PAYLOAD', {"token": "glados.cloud"})

    @property
    def headers_base(self) -> Dict[str, str]:
        """获取基础请求头"""
        return {
            "origin": self.ORIGIN,
            "referer": self.REFERER,
            "user-agent": self.USER_AGENT,
            "content-type": self.CONTENT_TYPE,
        }


@dataclass(frozen=True)
class DelayConfig:
    """延迟配置"""
    MIN_DELAY: float = 1.0
    MAX_DELAY: float = 2.0


@dataclass
class Config:
    """主配置类"""
    api: APIConfig = None  # type: ignore
    request: RequestConfig = None  # type: ignore
    delay: DelayConfig = None  # type: ignore

    def __post_init__(self):
        if self.api is None:
            self.api = APIConfig()
        if self.request is None:
            self.request = RequestConfig()
        if self.delay is None:
            self.delay = DelayConfig()


# 全局配置实例
config = Config()
