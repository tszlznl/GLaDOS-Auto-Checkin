import os
import json
import time
import random
import requests
from pypushdeer import PushDeer

CHECKIN_URL = "https://glados.cloud/api/user/checkin"
STATUS_URL = "https://glados.cloud/api/user/status"
POINTS_CANDIDATES = [
    "https://glados.cloud/api/user/points",
    "https://glados.cloud/api/user/point",
    "https://glados.cloud/api/user/balance",
    "https://glados.cloud/api/user/info",
]

HEADERS_BASE = {
    "origin": "https://glados.cloud",
    "referer": "https://glados.cloud/console/checkin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "content-type": "application/json;charset=UTF-8",
}

PAYLOAD = {"token": "glados.cloud"}
TIMEOUT = 10

def push_deer(sckey, title, text):
    if sckey:
        PushDeer(pushkey=sckey).send_text(title, desp=text)

def push_serverchan(sendkey, title, content):
    if not sendkey:
        return
    url = f"https://sctapi.ftqq.com/{sendkey}.send"
    data = {"title": title, "desp": content}
    try:
        resp = requests.post(url, data=data, timeout=TIMEOUT)
        if resp.status_code == 200:
            result = resp.json()
            if result.get("code") == 0:
                print("✅ Server 酱推送成功")
            else:
                print(f"⚠️ Server 酱推送失败: {result.get('message')}")
        else:
            print(f"⚠️ Server 酱推送失败: HTTP {resp.status_code}")
    except Exception as e:
        print(f"⚠️ Server 酱推送异常: {e}")

def push_all(sendkey_deer, sendkey_sc, title, content):
    if sendkey_deer:
        push_deer(sendkey_deer, title, content)
    if sendkey_sc:
        push_serverchan(sendkey_sc, title, content)
    if not sendkey_deer and not sendkey_sc:
        print("⚠️ 未配置任何推送服务")

def safe_json(resp):
    try:
        return resp.json()
    except:
        return {}

def get_points(session, headers):
    """尝试从多个候选 URL 获取积分，返回整数或 None"""
    for url in POINTS_CANDIDATES:
        try:
            resp = session.get(url, headers=headers, timeout=TIMEOUT)
            if resp.status_code == 200:
                j = safe_json(resp)
                # 尝试常见的字段名
                for key in ["points", "point", "balance", "total_points"]:
                    if key in j:
                        val = j[key]
                        if isinstance(val, (int, float)):
                            return int(val)
                    if "data" in j and isinstance(j["data"], dict):
                        for key2 in ["points", "point", "balance", "total_points"]:
                            if key2 in j["data"]:
                                val = j["data"][key2]
                                if isinstance(val, (int, float)):
                                    return int(val)
                # 如果整个响应就是数字
                if isinstance(j, (int, float)):
                    return int(j)
        except:
            continue
    return None

def main():
    sendkey_deer = os.getenv("SENDKEY", "")
    sendkey_sc = os.getenv("SERVERCHAN_KEY", "")
    cookies_env = os.getenv("COOKIES", "")
    cookies = [c.strip() for c in cookies_env.split("&") if c.strip()]

    if not cookies:
        push_all(sendkey_deer, sendkey_sc, "GLaDOS 签到", "❌ 未检测到 COOKIES")
        return

    session = requests.Session()
    ok = fail = repeat = 0
    lines = []

    for idx, cookie in enumerate(cookies, 1):
        headers = dict(HEADERS_BASE)
        headers["cookie"] = cookie

        email = "unknown"
        points = "-"
        days = "-"

        try:
            # 签到请求
            r = session.post(CHECKIN_URL, headers=headers, data=json.dumps(PAYLOAD), timeout=TIMEOUT)
            j = safe_json(r)
            msg = j.get("message", "")
            msg_lower = msg.lower()

            if "got" in msg_lower:
                ok += 1
                status = "✅ 成功"
                # 签到成功时，可能直接返回 points
                if "points" in j:
                    points = j["points"]
                elif "point" in j:
                    points = j["point"]
            elif "repeat" in msg_lower or "already" in msg_lower:
                repeat += 1
                status = "🔁 已签到"
            else:
                fail += 1
                status = "❌ 失败"

            # 状态接口（获取邮箱、剩余天数）
            s = session.get(STATUS_URL, headers=headers, timeout=TIMEOUT)
            sj = safe_json(s).get("data") or {}
            if sj.get("email"):
                email = sj["email"]
            if sj.get("leftDays") is not None:
                days = f"{int(float(sj['leftDays']))} 天"

            # 如果积分还未获取到，尝试额外请求
            if points == "-":
                pts = get_points(session, headers)
                if pts is not None:
                    points = pts
                else:
                    if idx == 1:
                        print("⚠️ 无法获取积分，请检查 Cookie 或网络")

        except Exception as e:
            fail += 1
            status = "❌ 异常"
            print(f"处理账号 {idx} 时出错: {e}")

        lines.append(f"{idx}. {email} | {status} | 积分:{points} | 剩余:{days}")
        time.sleep(random.uniform(1, 2))

    title = f"GLaDOS 签到完成 ✅{ok} ❌{fail} 🔁{repeat}"
    content = "\n".join(lines)
    print(content)
    push_all(sendkey_deer, sendkey_sc, title, content)

if __name__ == "__main__":
    main()