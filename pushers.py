"""
GLaDOS 自动签到推送模块
使用策略模式重构，支持多种推送渠道
"""
import os
import time
import hashlib
import hmac
import base64
import urllib.parse
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import requests

from config import config


@dataclass
class PushResult:
    """推送结果"""
    success: bool
    channel: str
    message: str = ""


class BasePusher(ABC):
    """推送基类"""

    def __init__(self, timeout: int = None):
        self.timeout = timeout or config.api.TIMEOUT

    @property
    @abstractmethod
    def name(self) -> str:
        """推送渠道名称"""
        pass

    @property
    @abstractmethod
    def required_env_vars(self) -> List[str]:
        """必需的环境变量列表"""
        pass

    def is_configured(self) -> bool:
        """检查是否已配置"""
        return all(os.getenv(var) for var in self.required_env_vars)

    @abstractmethod
    def send(self, title: str, content: str) -> PushResult:
        """发送推送"""
        pass

    def _safe_json(self, resp: requests.Response) -> Dict[str, Any]:
        """安全解析 JSON 响应"""
        try:
            return resp.json()
        except Exception:
            return {}

    def _handle_error(self, resp: requests.Response, resp_json: Dict) -> str:
        """处理错误响应"""
        return resp_json.get("message") or resp_json.get("msg") or \
               resp_json.get("errmsg") or resp_json.get("description") or resp.text


class PushDeerPusher(BasePusher):
    """PushDeer 推送"""

    @property
    def name(self) -> str:
        return "PushDeer"

    @property
    def required_env_vars(self) -> List[str]:
        return ["SENDKEY"]

    def send(self, title: str, content: str) -> PushResult:
        key = os.getenv("SENDKEY", "")
        if not key:
            return PushResult(False, self.name, "未配置 SENDKEY")

        try:
            url = "https://api2.pushdeer.com/message/push"
            data = {
                "pushkey": key,
                "text": f"{title}\n\n{content}",
                "type": "text",
            }
            r = requests.post(url, json=data, timeout=self.timeout)
            resp = self._safe_json(r)
            if r.ok and resp.get("code") == 0:
                return PushResult(True, self.name)
            return PushResult(False, self.name, self._handle_error(r, resp))
        except Exception as e:
            return PushResult(False, self.name, str(e))


class ServerChanPusher(BasePusher):
    """Server酱推送"""

    @property
    def name(self) -> str:
        return "Server酱"

    @property
    def required_env_vars(self) -> List[str]:
        return ["SERVERCHAN_KEY"]

    def send(self, title: str, content: str) -> PushResult:
        key = os.getenv("SERVERCHAN_KEY", "")
        if not key:
            return PushResult(False, self.name, "未配置 SERVERCHAN_KEY")

        try:
            r = requests.post(
                f"https://sctapi.ftqq.com/{key}.send",
                data={"title": title, "desp": content},
                timeout=self.timeout,
            )
            resp = self._safe_json(r)
            if r.ok and resp.get("code") == 0:
                return PushResult(True, self.name)
            return PushResult(False, self.name, self._handle_error(r, resp))
        except Exception as e:
            return PushResult(False, self.name, str(e))


class TelegramPusher(BasePusher):
    """Telegram Bot 推送"""

    @property
    def name(self) -> str:
        return "Telegram"

    @property
    def required_env_vars(self) -> List[str]:
        return ["TG_BOT_TOKEN", "TG_CHAT_ID"]

    def send(self, title: str, content: str) -> PushResult:
        bot_token = os.getenv("TG_BOT_TOKEN", "")
        chat_id = os.getenv("TG_CHAT_ID", "")

        if not bot_token or not chat_id:
            return PushResult(False, self.name, "未配置 TG_BOT_TOKEN 或 TG_CHAT_ID")

        text = f"{title}\n\n{content}"
        if len(text) > 4000:
            text = text[:3990] + "\n..."

        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {"chat_id": chat_id, "text": text}
            r = requests.post(url, json=data, timeout=self.timeout)
            resp = self._safe_json(r)
            if r.ok and resp.get("ok"):
                return PushResult(True, self.name)
            return PushResult(False, self.name, self._handle_error(r, resp))
        except Exception as e:
            return PushResult(False, self.name, str(e))


class PushPlusPusher(BasePusher):
    """PushPlus 推送"""

    @property
    def name(self) -> str:
        return "PushPlus"

    @property
    def required_env_vars(self) -> List[str]:
        return ["PUSHPLUS_TOKEN"]

    def send(self, title: str, content: str) -> PushResult:
        token = os.getenv("PUSHPLUS_TOKEN", "")
        if not token:
            return PushResult(False, self.name, "未配置 PUSHPLUS_TOKEN")

        try:
            url = "https://www.pushplus.plus/send"
            data = {
                "token": token,
                "title": title,
                "content": content,
                "template": "html",
            }
            r = requests.post(url, json=data, timeout=self.timeout)
            resp = self._safe_json(r)
            if r.ok and resp.get("code") == 200:
                return PushResult(True, self.name)
            return PushResult(False, self.name, self._handle_error(r, resp))
        except Exception as e:
            return PushResult(False, self.name, str(e))


class DingTalkPusher(BasePusher):
    """钉钉机器人推送"""

    @property
    def name(self) -> str:
        return "钉钉机器人"

    @property
    def required_env_vars(self) -> List[str]:
        return ["DINGTALK_WEBHOOK"]

    def _generate_sign(self, secret: str) -> tuple:
        """生成加签"""
        timestamp = str(round(time.time() * 1000))
        string_to_sign = f"{timestamp}\n{secret}"
        hmac_code = hmac.new(
            secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return timestamp, sign

    def send(self, title: str, content: str) -> PushResult:
        webhook_url = os.getenv("DINGTALK_WEBHOOK", "")
        if not webhook_url:
            return PushResult(False, self.name, "未配置 DINGTALK_WEBHOOK")

        try:
            secret = os.getenv("DINGTALK_SECRET", "")
            if secret:
                timestamp, sign = self._generate_sign(secret)
                separator = "&" if "?" in webhook_url else "?"
                webhook_url = f"{webhook_url}{separator}timestamp={timestamp}&sign={sign}"

            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": title,
                    "text": f"### {title}\n\n{content}",
                },
            }
            headers = {"Content-Type": "application/json"}
            r = requests.post(webhook_url, json=data, headers=headers, timeout=self.timeout)
            resp = self._safe_json(r)
            if r.ok and resp.get("errcode") == 0:
                return PushResult(True, self.name)
            return PushResult(False, self.name, resp.get("errmsg", r.text))
        except Exception as e:
            return PushResult(False, self.name, str(e))


class FeishuPusher(BasePusher):
    """飞书机器人推送"""

    @property
    def name(self) -> str:
        return "飞书机器人"

    @property
    def required_env_vars(self) -> List[str]:
        return ["FEISHU_WEBHOOK"]

    def _generate_sign(self, secret: str) -> tuple:
        """生成加签"""
        timestamp = str(round(time.time()))
        string_to_sign = f"{timestamp}\n{secret}"
        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        sign = base64.b64encode(hmac_code).decode("utf-8")
        return timestamp, sign

    def send(self, title: str, content: str) -> PushResult:
        webhook_url = os.getenv("FEISHU_WEBHOOK", "")
        if not webhook_url:
            return PushResult(False, self.name, "未配置 FEISHU_WEBHOOK")

        try:
            data: Dict[str, Any] = {
                "msg_type": "interactive",
                "card": {
                    "header": {
                        "title": {
                            "tag": "plain_text",
                            "content": title,
                        },
                        "template": "blue",
                    },
                    "elements": [
                        {
                            "tag": "markdown",
                            "content": content,
                        }
                    ],
                },
            }

            secret = os.getenv("FEISHU_SECRET", "")
            if secret:
                timestamp, sign = self._generate_sign(secret)
                data["timestamp"] = timestamp
                data["sign"] = sign

            headers = {"Content-Type": "application/json"}
            r = requests.post(webhook_url, json=data, headers=headers, timeout=self.timeout)
            resp = self._safe_json(r)
            if r.ok and resp.get("code") == 0:
                return PushResult(True, self.name)
            return PushResult(False, self.name, resp.get("msg", r.text))
        except Exception as e:
            return PushResult(False, self.name, str(e))


class WeComBotPusher(BasePusher):
    """企业微信机器人推送"""

    @property
    def name(self) -> str:
        return "企业微信机器人"

    @property
    def required_env_vars(self) -> List[str]:
        return ["WECOM_BOT_WEBHOOK"]

    def send(self, title: str, content: str) -> PushResult:
        webhook_url = os.getenv("WECOM_BOT_WEBHOOK", "")
        if not webhook_url:
            return PushResult(False, self.name, "未配置 WECOM_BOT_WEBHOOK")

        try:
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "content": f"### {title}\n\n{content}",
                },
            }
            headers = {"Content-Type": "application/json"}
            r = requests.post(webhook_url, json=data, headers=headers, timeout=self.timeout)
            resp = self._safe_json(r)
            if r.ok and resp.get("errcode") == 0:
                return PushResult(True, self.name)
            return PushResult(False, self.name, resp.get("errmsg", r.text))
        except Exception as e:
            return PushResult(False, self.name, str(e))


class YunhuPusher(BasePusher):
    """云湖机器人推送"""

    @property
    def name(self) -> str:
        return "云湖机器人"

    @property
    def required_env_vars(self) -> List[str]:
        return ["YUNHU_TOKEN", "YUNHU_RECV_ID"]

    def send(self, title: str, content: str) -> PushResult:
        token = os.getenv("YUNHU_TOKEN", "")
        recv_id = os.getenv("YUNHU_RECV_ID", "")

        if not token or not recv_id:
            return PushResult(False, self.name, "未配置 YUNHU_TOKEN 或 YUNHU_RECV_ID")

        try:
            url = "https://chat-go.jwzhd.com/open-apis/v1/bot/send-message"
            recv_type = os.getenv("YUNHU_RECV_TYPE", "group")
            data = {
                "token": token,
                "recvId": recv_id,
                "recvType": recv_type,
                "contentType": 1,
                "content": f"**{title}**\n\n{content}",
            }
            headers = {"Content-Type": "application/json"}
            r = requests.post(url, json=data, headers=headers, timeout=self.timeout)
            resp = self._safe_json(r)
            if r.ok and resp.get("code") == 1:
                return PushResult(True, self.name)
            return PushResult(False, self.name, resp.get("msg") or resp.get("message") or r.text)
        except Exception as e:
            return PushResult(False, self.name, str(e))


class PushManager:
    """推送管理器"""

    def __init__(self):
        self.pushers: List[BasePusher] = [
            PushDeerPusher(),
            ServerChanPusher(),
            TelegramPusher(),
            PushPlusPusher(),
            DingTalkPusher(),
            FeishuPusher(),
            WeComBotPusher(),
            YunhuPusher(),
        ]

    def push_all(self, title: str, content: str) -> List[PushResult]:
        """推送到所有已配置的渠道"""
        results: List[PushResult] = []
        configured_channels: List[str] = []

        for pusher in self.pushers:
            if pusher.is_configured():
                result = pusher.send(title, content)
                results.append(result)
                configured_channels.append(pusher.name)

                if result.success:
                    print(f"✅ {pusher.name} 推送成功")
                else:
                    print(f"⚠️ {pusher.name} 推送失败: {result.message}")

        if not configured_channels:
            print("⚠️ 未配置任何推送服务，请在 Secrets 中设置至少一种推送渠道")
        else:
            print(f"📬 已推送至: {', '.join(configured_channels)}")

        return results


# 全局推送管理器实例
push_manager = PushManager()


def push_all(title: str, content: str) -> List[PushResult]:
    """便捷函数：推送到所有已配置的渠道"""
    return push_manager.push_all(title, content)
