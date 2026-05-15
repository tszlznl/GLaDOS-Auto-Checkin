# 📌 GLaDOS 自动签到

一个基于 **GitHub Actions** 的 **GLaDOS 自动签到脚本**。
**无需服务器、无需编程基础**，每天自动帮你签到。

------

## ✨ 功能说明

- ✅ **每天自动签到**
- 🔁 **已签到自动识别，不会报错**
- 👥 **支持多个账号**
- 📊 **查询总积分和剩余天数**
- 📬 **多种签到结果推送渠道（PushDeer / Server酱 / Telegram / PushPlus）**
- 🔧 **每月自动空提交保活，防止 GitHub Actions 被暂停**
- 🆓 **完全免费，使用 GitHub Actions**

------

## 📂 项目结构

```
.
├── checkin.py                 # 签到脚本（不用动）
└── .github/workflows/
    └── glados.yml              # GitHub Actions 配置（不用动）
```

------

## 🚀 使用教程

### 第一步：Fork 本项目

1. 点击右上角 **Fork**
2. Fork 到你自己的 GitHub 账号下

👉 后续所有操作都在你 **自己的仓库** 中完成

------

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

------

### 第三步：添加 GitHub Secrets

进入你 Fork 后的仓库：

1. 点击 **Settings**
2. 左侧选择 **Secrets and variables → Actions**
3. 点击 **New repository secret**

#### 添加第一个 Secret（必填）

- **Name**：`COOKIES`
- **Value**：粘贴刚才复制的 Cookie

点击 **Save**

------

### （可选）第四步：开启签到结果推送

项目支持 **四种推送渠道**，你可以按需配置任意一种或多种：

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

1. 注册 PushPlus：https://pushplus.hxtrip.com
2. 微信扫码登录，获取你的 Token
3. 在 GitHub Secrets 中添加：
   - **Name**：`PUSHPLUS_TOKEN`
   - **Value**：你的 PushPlus Token

> ⚠️ **注意**：PushPlus 官方域名已从 `www.pushplus.plus` 迁移到 `pushplus.hxtrip.com`，旧域名已失效。本项目已适配新域名。

------

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

------

## ⏰ 自动签到时间说明

项目默认设置为：

```
每天 UTC 04:00 自动运行
```

换算成北京时间：

> 🕛 **每天中午 12 点自动签到**

你无需做任何操作，它会每天自动运行。

------

## 🔧 保活机制

GitHub 会对长期无活动的仓库暂停 Actions。本项目内置了 **每月自动空提交** 机制：

- 每月 1 号 UTC 00:00 自动创建一个空提交
- 防止仓库因"不活跃"被 GitHub 暂停 Actions
- 无需手动操作

------

## 📋 签到结果说明

签到完成后，推送内容包含：

| 字段 | 说明 |
|------|------|
| ✅ 成功 | 签到成功，显示本次获得积分 |
| 🔄 已签到 | 今日已签到过，不重复签到 |
| ❌ 失败 | 签到失败，显示失败原因 |
| 总积分 | 账号当前总积分 |
| 剩余 | 账号剩余天数 |

------

## 🔄 项目更新日志

### v2.0.0 (2025-05)

- **新增** Telegram Bot 推送支持
- **新增** PushPlus（推送加）推送支持，已适配新域名 `pushplus.hxtrip.com`
- **优化** PushDeer 推送改为直接 HTTP API 调用，移除 `pypushdeer` 第三方库依赖，提升稳定性
- **优化** 签到结果判断逻辑：优先使用 API 返回的 `code` 字段，兜底用 `message` 关键词匹配
- **新增** 总积分查询功能
- **新增** 每月自动空提交保活，防止 GitHub Actions 被暂停
- **修复** PushPlus 推送域名已从 `www.pushplus.plus` 迁移到 `pushplus.hxtrip.com`，旧域名已失效
- **优化** Python 版本升级至 3.11
- **优化** 多账号间请求增加随机延迟，避免请求过快
- **优化** 仅非最后一个账号时延迟，最后一个不等待

### v1.0.0

- 基础签到功能
- PushDeer 推送
- Server酱推送
- 多账号支持

------

## ❓ 常见问题

**Q: PushPlus 推送失败怎么办？**
A: PushPlus 官方域名已从 `www.pushplus.plus` 迁移到 `pushplus.hxtrip.com`，请确保你使用的是新域名获取 Token。本项目已适配新域名。

**Q: 签到提示 Cookie 失效？**
A: Cookie 有有效期，请重新登录 GLaDOS 获取最新 Cookie 并更新 GitHub Secrets。

**Q: Actions 被暂停了？**
A: 本项目已内置每月空提交保活机制。如果仍被暂停，请手动在 Actions 页面触发一次 `workflow_dispatch`。

**Q: 可以同时配置多个推送渠道吗？**
A: 可以。配置多个 Secrets 即可同时推送到多个渠道，互不影响。
