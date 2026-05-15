# AGENTS.md - GLaDOS Auto Checkin

## 项目概览

基于 GitHub Actions 的 GLaDOS 自动签到脚本，支持多账号、多种通知渠道和每月保活。

## 项目结构

```
.
├── checkin.py                 # 主签到脚本（Python）
├── .github/workflows/
│   └── glados.yml             # GitHub Actions 工作流配置
├── index.html                 # 项目介绍页（开发环境预览用）
├── README.md                  # 使用文档
└── styles/main.css            # 样式文件
```

## 技术栈

- **语言**: Python 3.11
- **运行环境**: GitHub Actions (ubuntu-latest)
- **依赖**: requests（仅此一个第三方库）
- **通知渠道**: PushDeer / Server酱 / Telegram / PushPlus

## 关键配置

### 环境变量（GitHub Secrets）

| 变量名 | 必填 | 说明 |
|--------|------|------|
| COOKIES | 是 | GLaDOS Cookie，多账号用 `&` 分隔 |
| SENDKEY | 否 | PushDeer 推送 Key |
| SERVERCHAN_KEY | 否 | Server酱 SendKey |
| TG_BOT_TOKEN | 否 | Telegram Bot Token |
| TG_CHAT_ID | 否 | Telegram Chat ID |
| PUSHPLUS_TOKEN | 否 | PushPlus Token |

### 工作流定时任务

- `0 4 * * *` — 每日 UTC 4:00 签到（北京时间 12:00）
- `0 0 1 * *` — 每月 1 号 UTC 0:00 空提交保活

## 代码风格

- Python 函数命名: snake_case
- 常量: UPPER_SNAKE_CASE
- 所有 HTTP 请求设置 timeout（默认 12 秒）
- 推送函数统一格式: 接收 key/token + title + content，try-except 包裹
- GLaDOS API 签到结果判断: 优先 code 字段，兜底 message 关键词

## 注意事项

- PushPlus 域名已从 `www.pushplus.plus` 迁移到 `pushplus.hxtrip.com`，旧域名失效
- PushDeer 不再依赖 pypushdeer 库，改用直接 HTTP API 调用
- 签到后查询状态和积分为可选操作，失败不影响签到结果推送
