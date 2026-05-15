import os
import json
import time
import random
import requests

# ---------- 配置 ----------
CHECKIN_URL = "https://glados.cloud/api/user/checkin"
STATUS_URL = "https://glados.cloud/api/user/status"
POINTS_URL = "https://glados.cloud/api/user/points"

HEADERS_BASE = {
    "origin": "https://glados.cloud",
    "referer": "https://glados.cloud/console/checkin",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "content-type": "application/json;charset=UTF-8",
}

PAYLOAD = {"token": "glados.cloud"}
TIMEOUT = 12


# ---------- 工具函数 ----------

def safe_json(resp):
    """安全解析 JSON 响应"""
    try:
        return resp.json()
    except Exception:
        return {}


# ---------- 推送函数 ----------

def push_deer(key, title, content):
    """推送到 PushDeer（直接调用 HTTP API，无需第三方库）

    API 文档: https://github.com/easychen/pushdeer
    接口地址: https://api2.pushdeer.com/message/push
    """
    if not key:
        return
    try:
        url = "https://api2.pushdeer.com/message/push"
        # type=text 时 text 为完整消息内容；避免 markdown 误解析 | 等符号
        data = {
            "pushkey": key,
            "text": f"{title}\n\n{content}",
            "type": "text",
        }
        r = requests.post(url, json=data, timeout=TIMEOUT)
        resp = safe_json(r)
        if r.ok and resp.get("code") == 0:
            print("✅ PushDeer 推送成功")
        else:
            print(f"⚠️ PushDeer 推送失败: {resp.get('message', r.text)}")
    except Exception as e:
        print(f"⚠️ PushDeer 推送异常: {e}")


def push_serverchan(key, title, content):
    """推送到 Server酱 (Turbo 版)

    API 文档: https://sct.ftqq.com/sendkey
    接口地址: https://sctapi.ftqq.com/<sendkey>.send
    """
    if not key:
        return
    try:
        r = requests.post(
            f"https://sctapi.ftqq.com/{key}.send",
            data={"title": title, "desp": content},
            timeout=TIMEOUT,
        )
        resp = safe_json(r)
        if r.ok and resp.get("code") == 0:
            print("✅ Server酱推送成功")
        else:
            print(f"⚠️ Server酱推送失败: {resp.get('message', r.text)}")
    except Exception as e:
        print(f"⚠️ Server酱推送异常: {e}")


def push_telegram(bot_token, chat_id, title, content):
    """推送到 Telegram Bot

    API 文档: https://core.telegram.org/bots/api#sendmessage
    接口地址: https://api.telegram.org/bot<token>/sendMessage
    """
    if not bot_token or not chat_id:
        return
    text = f"{title}\n\n{content}"
    # Telegram 单条消息上限 4096 字符，做截断避免发送失败
    if len(text) > 4000:
        text = text[:3990] + "\n..."
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {"chat_id": chat_id, "text": text}
        r = requests.post(url, json=data, timeout=TIMEOUT)
        resp = safe_json(r)
        if r.ok and resp.get("ok"):
            print("✅ Telegram 推送成功")
        else:
            print(
                f"⚠️ Telegram 推送失败: HTTP {r.status_code} | "
                f"{resp.get('description', r.text)}"
            )
    except Exception as e:
        print(f"⚠️ Telegram 推送异常: {e}")


def push_pushplus(token, title, content):
    """推送到 PushPlus（推送加）

    API 文档: https://pushplus.hxtrip.com/doc/guide/api.html
    接口地址: https://pushplus.hxtrip.com/send
    ⚠️ 旧域名 www.pushplus.plus 已失效，请使用新域名 pushplus.hxtrip.com
    """
    if not token:
        return
    try:
        url = "https://pushplus.hxtrip.com/send"
        data = {
            "token": token,
            "title": title,
            "content": content,
            "template": "html",
        }
        r = requests.post(url, json=data, timeout=TIMEOUT)
        resp = safe_json(r)
        if r.ok and resp.get("code") == 200:
            print("✅ PushPlus 推送成功")
        else:
            print(f"⚠️ PushPlus 推送失败: {resp.get('msg', r.text)}")
    except Exception as e:
        print(f"⚠️ PushPlus 推送异常: {e}")


def push_all(title, content):
    """推送到所有已配置的通知渠道

    支持的渠道（按优先顺序）：
    1. PushDeer    - 环境变量 SENDKEY
    2. Server酱    - 环境变量 SERVERCHAN_KEY
    3. Telegram    - 环境变量 TG_BOT_TOKEN + TG_CHAT_ID
    4. PushPlus    - 环境变量 PUSHPLUS_TOKEN
    """
    configured = []

    # PushDeer
    deer_key = os.getenv("SENDKEY", "")
    if deer_key:
        push_deer(deer_key, title, content)
        configured.append("PushDeer")

    # Server酱
    sc_key = os.getenv("SERVERCHAN_KEY", "")
    if sc_key:
        push_serverchan(sc_key, title, content)
        configured.append("Server酱")

    # Telegram
    bot_token = os.getenv("TG_BOT_TOKEN", "")
    chat_id = os.getenv("TG_CHAT_ID", "")
    if bot_token and chat_id:
        push_telegram(bot_token, chat_id, title, content)
        configured.append("Telegram")

    # PushPlus
    pp_token = os.getenv("PUSHPLUS_TOKEN", "")
    if pp_token:
        push_pushplus(pp_token, title, content)
        configured.append("PushPlus")

    if not configured:
        print("⚠️ 未配置任何推送服务，请在 Secrets 中设置至少一种推送渠道")
    else:
        print(f"📬 已推送至: {', '.join(configured)}")


# ---------- 签到逻辑 ----------

def classify_checkin(code, message):
    """
    判断签到结果: 优先根据 code 字段，兜底用 message 关键词。

    GLaDOS API 返回值:
      - code=0  → 签到成功
      - code=1  → 今日已签到
      - 其他    → 签到失败
    部分旧接口或域名可能只返回 message，因此做兜底处理。
    """
    if code == 0:
        return "ok"
    if code == 1:
        return "repeat"
    # 兜底：关键词匹配
    msg = message.lower()
    if "got" in msg:
        return "ok"
    if any(kw in msg for kw in ("repeat", "already", "重复", "已签到", "签到过", "请勿")):
        return "repeat"
    return "fail"


# ---------- 主流程 ----------

def main():
    cookies = [c.strip() for c in os.getenv("COOKIES", "").split("&") if c.strip()]

    if not cookies:
        push_all("GLaDOS 签到", "❌ 未检测到 COOKIES，请配置 GitHub Secrets")
        return

    session = requests.Session()
    ok = fail = repeat = 0
    lines = []

    for idx, cookie in enumerate(cookies, 1):
        headers = dict(HEADERS_BASE)
        headers["cookie"] = cookie

        email, days, total_points = "unknown", "-", "-"

        try:
            # 1. 签到
            r = session.post(
                CHECKIN_URL,
                headers=headers,
                data=json.dumps(PAYLOAD),
                timeout=TIMEOUT,
            )
            j = safe_json(r)
            code = j.get("code", -2)
            message = j.get("message", "")
            earned = j.get("points", 0)

            result = classify_checkin(code, message)
            if result == "ok":
                ok += 1
                status = f"✅ 成功 (+{earned}积分)"
            elif result == "repeat":
                repeat += 1
                status = "🔄 已签到"
            else:
                fail += 1
                status = f"❌ 失败({message})"

            # 2. 查询账号状态（剩余天数、邮箱），允许失败
            try:
                s = session.get(STATUS_URL, headers=headers, timeout=TIMEOUT)
                data = safe_json(s).get("data") or {}
                email = data.get("email", email)
                if data.get("leftDays") is not None:
                    days = f"{int(float(data['leftDays']))} 天"
            except Exception:
                pass  # 状态查询失败不影响签到结果

            # 3. 查询总积分，允许失败
            try:
                p = session.get(POINTS_URL, headers=headers, timeout=TIMEOUT)
                pj = safe_json(p)
                if pj.get("points") is not None:
                    total_points = f"{int(float(pj['points']))} 积分"
            except Exception:
                pass  # 积分查询失败不影响签到结果

        except Exception as e:
            fail += 1
            status = f"❌ 异常({e})"

        lines.append(f"{idx}. {email} | {status} | 总积分:{total_points} | 剩余:{days}")

        # 非最后一个账号时随机延迟，避免请求过快
        if idx < len(cookies):
            time.sleep(random.uniform(1, 2))

    title = f"GLaDOS 签到完成 ✅{ok} ❌{fail} 🔄{repeat}"
    content = "\n".join(lines)

    print(content)
    push_all(title, content)


if __name__ == "__main__":
    main()
