# 📌 GLaDOS 自动签到

一个基于 **GitHub Actions** 的 **GLaDOS 自动签到脚本**。

**无需服务器、无需编程基础**，每天自动帮你签到。

---

## ✨ 功能说明

- ✅ **每天自动签到**
- 🔁 **已签到自动识别，不会报错**
- 👥 **支持多个账号**
- 📊 **查询总积分和剩余天数**
- 📬 **多种签到结果推送渠道**
  - PushDeer / Server酱 / Telegram / PushPlus
  - 钉钉机器人 / 飞书机器人 / 企业微信机器人 / 云湖机器人
- 🔧 **每月自动空提交保活，防止 GitHub Actions 被暂停**
- 🔄 **网络请求自动重试（指数退避）**
- 🔒 **日志脱敏处理，保护隐私**
- ✅ **Cookie 格式预验证**
- 🆓 **完全免费，使用 GitHub Actions**

---

## 📂 项目结构

```
.
├── checkin.py                 # 签到脚本主逻辑
├── config.py                  # 配置模块（集中管理常量）
├── pushers.py                 # 推送模块（策略模式）
├── test_checkin.py            # 单元测试
├── requirements.txt           # 依赖管理
└── .github/workflows/
    └── glados.yml             # GitHub Actions 配置
```

---

## 🚀 使用教程

### 第一步：Fork 本项目

1. 点击右上角 **Fork**
2. Fork 到你自己的 GitHub 账号下

👉 后续所有操作都在你 **自己的仓库** 中完成

---

### 第二步：获取 GLaDOS Cookie

1. 打开浏览器，登录：https://glados.cloud
2. 按 **F12** 打开开发者工具
3. 找到：
   - Chrome：`Application` → `Cookies`
   - Firefox：`存储` → `Cookies`
4. 选择 `glados.cloud`
5. **复制完整 Cookie 内容**

示例（示意）：
```
koa:sess=xxxxxx; koa:sess.sig=yyyyyy
```

⚠️ **必须是完整的一整段，不要只复制一半**

---

### 第三步：添加 GitHub Secrets

进入你 Fork 后的仓库：

1. 点击 **Settings**
2. 左侧选择 **Secrets and variables → Actions**
3. 点击 **New repository secret**

#### 添加第一个 Secret（必填）

- **Name**：`COOKIES`
- **Value**：粘贴刚才复制的 Cookie

点击 **Save**

---

### （可选）第四步：开启签到结果推送

项目支持 **八种推送渠道**，你可以按需配置任意一种或多种：

#### 🦌 方式一：PushDeer

开源轻量推送，支持 iOS / Android / Web。

1. 注册 PushDeer：https://www.pushdeer.com
2. 获取你的 `SENDKEY`
3. 在 GitHub Secrets 中添加：
   - **Name**：`SENDKEY`
   - **Value**：你的 PushDeer key

#### 🔔 方式二：Server酱 (S酱)

通过微信推送通知，注册即用。

1. 注册 Server酱 Turbo：https://sct.ftqq.com
2. 获取你的 SendKey
3. 在 GitHub Secrets 中添加：
   - **Name**：`SERVERCHAN_KEY`
   - **Value**：你的 Server酱 SendKey

#### 🤖 方式三：Telegram Bot

通过 Telegram 机器人推送，全球可用。

1. 在 Telegram 搜索 `@BotFather`
2. 发送 `/newbot` 创建机器人，拿到 `TG_BOT_TOKEN`
3. 打开你新建的机器人，先发一条任意消息
4. 访问：`https://api.telegram.org/bot<你的TG_BOT_TOKEN>/getUpdates`
5. 在返回内容中找到你的 `chat.id`（这就是 `TG_CHAT_ID`）
6. 在 GitHub Secrets 中添加：
   - **Name**：`TG_BOT_TOKEN`
   - **Value**：你的 Telegram Bot Token
   - **Name**：`TG_CHAT_ID`
   - **Value**：你的聊天 ID（数字，可能是负数）

#### 📮 方式四：PushPlus（推送加）

通过微信公众号推送通知。

1. 注册 PushPlus：https://www.pushplus.plus
2. 微信扫码登录，获取你的 Token
3. 在 GitHub Secrets 中添加：
   - **Name**：`PUSHPLUS_TOKEN`
   - **Value**：你的 PushPlus Token

#### 🔔 方式五：钉钉机器人

通过钉钉群机器人推送通知，支持加签安全验证。

1. 在钉钉群中添加自定义机器人
2. 安全设置选择"自定义关键词"，关键词填写 **pushplus**
3. 复制机器人的 Webhook 地址
4. 在 GitHub Secrets 中添加：
   - **Name**：`DINGTALK_WEBHOOK`
   - **Value**：完整的 Webhook 地址
   - **Name**：`DINGTALK_SECRET`（可选，加签验证密钥）
   - **Value**：机器人的加签密钥

> 💡 **提示**：如果机器人设置了加签安全验证，必须配置 `DINGTALK_SECRET`。

#### 🐦 方式六：飞书机器人

通过飞书群机器人推送通知，支持加签安全验证。

1. 在飞书群中添加自定义机器人
2. 复制机器人的 Webhook 地址
3. 在 GitHub Secrets 中添加：
   - **Name**：`FEISHU_WEBHOOK`
   - **Value**：完整的 Webhook 地址
   - **Name**：`FEISHU_SECRET`（可选，加签验证密钥）
   - **Value**：机器人的加签密钥

#### 💼 方式七：企业微信机器人

通过企业微信群机器人推送通知。

1. 在企业微信群中添加自定义机器人
2. 复制机器人的 Webhook 地址
3. 在 GitHub Secrets 中添加：
   - **Name**：`WECOM_BOT_WEBHOOK`
   - **Value**：完整的 Webhook 地址

> ⚠️ **注意**：请勿泄露 Webhook 地址。

#### 🌊 方式八：云湖机器人

通过云湖社交APP机器人推送通知。

1. 下载并注册云湖：https://www.yhchat.com
2. 在云湖中创建机器人，获取 Token
3. 获取接收消息的用户ID或群ID（recvId）
4. 在 GitHub Secrets 中添加：
   - **Name**：`YUNHU_TOKEN`
   - **Value**：你的云湖机器人 Token
   - **Name**：`YUNHU_RECV_ID`
   - **Value**：接收消息的用户ID或群ID
   - **Name**：`YUNHU_RECV_TYPE`（可选，默认 `group`）
   - **Value**：`group` 或 `user`

---

## 👥 多账号如何添加？

### 规则很简单：

> **多个账号的 Cookie，用 `&` 连接**

示例：
```
cookie_账号1 & cookie_账号2 & cookie_账号3
```

⚠️ 注意事项：
- 不要换行
- 不要用逗号
- 每个 cookie 都是完整的一段

---

## ⏰ 自动签到时间说明

项目默认设置为：

```
每天 UTC 04:00 自动运行
```

换算成北京时间：

> 🕛 **每天中午 12 点自动签到**

你无需做任何操作，它会每天自动运行。

---

## 🔧 保活机制

GitHub 会对长期无活动的仓库暂停 Actions。本项目内置了 **每月自动空提交** 机制：

- 每月 1 号 UTC 00:00 自动创建一个空提交
- 防止仓库因"不活跃"被 GitHub 暂停 Actions
- 无需手动操作

---

## 📋 签到结果说明

签到完成后，推送内容包含：

| 字段 | 说明 |
|------|------|
| ✅ 成功 | 签到成功，显示本次获得积分 |
| 🔄 已签到 | 今日已签到过，不重复签到 |
| ❌ 失败 | 签到失败，显示失败原因 |
| 总积分 | 账号当前总积分 |
| 剩余 | 账号剩余天数 |

---

## 📬 推送渠道汇总

| 渠道 | 环境变量 | 必填参数 | 可选参数 |
|------|---------|---------|---------|
| PushDeer | `SENDKEY` | SENDKEY | - |
| Server酱 | `SERVERCHAN_KEY` | SERVERCHAN_KEY | - |
| Telegram | `TG_BOT_TOKEN` + `TG_CHAT_ID` | TG_BOT_TOKEN, TG_CHAT_ID | - |
| PushPlus | `PUSHPLUS_TOKEN` | PUSHPLUS_TOKEN | - |
| 钉钉机器人 | `DINGTALK_WEBHOOK` | DINGTALK_WEBHOOK | DINGTALK_SECRET |
| 飞书机器人 | `FEISHU_WEBHOOK` | FEISHU_WEBHOOK | FEISHU_SECRET |
| 企业微信机器人 | `WECOM_BOT_WEBHOOK` | WECOM_BOT_WEBHOOK | - |
| 云湖机器人 | `YUNHU_TOKEN` + `YUNHU_RECV_ID` | YUNHU_TOKEN, YUNHU_RECV_ID | YUNHU_RECV_TYPE |

---

## 🆕 v4.0.0 更新内容 (2025-05)

### 代码重构
- **重构** 推送模块使用策略模式，代码更优雅可扩展
- **新增** 配置模块 `config.py`，集中管理所有常量
- **新增** 完整的类型注解，提高代码可读性

### 功能增强
- **新增** 网络请求重试机制（指数退避，最多3次）
- **新增** Cookie 格式预验证，提前发现问题
- **新增** 日志脱敏处理，邮箱和 Cookie 自动脱敏

### 工程化改进
- **新增** `requirements.txt` 依赖管理
- **新增** `test_checkin.py` 单元测试
- **优化** GitHub Actions 添加超时和并发控制
- **优化** 使用 pip cache 加速依赖安装

---

## 🔄 历史版本

### v3.0.0 (2025-05)
- **修复** PushPlus 推送域名修复
- **新增** 钉钉/飞书/企业微信/云湖机器人推送渠道

### v2.0.0 (2025-05)
- **新增** Telegram Bot 推送支持
- **新增** PushPlus 推送支持
- **新增** 总积分查询功能
- **新增** 每月自动空提交保活

### v1.0.0
- 基础签到功能
- PushDeer / Server酱推送
- 多账号支持

---

## ❓ 常见问题

**Q: PushPlus 推送失败怎么办？**

A: PushPlus 官方域名为 `www.pushplus.plus`，API 地址为 `https://www.pushplus.plus/send`。请确保你在官网获取 Token。

**Q: 钉钉机器人推送失败？**

A: 请确保在钉钉机器人的安全设置中选择了"自定义关键词"，关键词填写 **pushplus**。如果设置了加签验证，请同时配置 `DINGTALK_SECRET`。

**Q: 飞书机器人推送失败？**

A: 请确保机器人已添加到目标群聊中。如果设置了加签验证，请同时配置 `FEISHU_SECRET`。

**Q: 签到提示 Cookie 失效？**

A: Cookie 有有效期，请重新登录 GLaDOS 获取最新 Cookie 并更新 GitHub Secrets。

**Q: Actions 被暂停了？**

A: 本项目已内置每月空提交保活机制。如果仍被暂停，请手动在 Actions 页面触发一次 `workflow_dispatch`。

**Q: 可以同时配置多个推送渠道吗？**

A: 可以。配置多个 Secrets 即可同时推送到多个渠道，互不影响。

**Q: 日志中的邮箱为什么显示不完整？**

A: 出于隐私保护，邮箱会自动脱敏显示（如 `te***@example.com`），这是正常的安全设计。

---

## 📄 许可证

MIT License
