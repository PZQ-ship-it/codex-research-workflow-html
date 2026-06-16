---
name: dianping-explore
description: 大众点评内容探索与低频采集技能。用于搜索大众点评商户、采集少量公开商户评论、封装现成 Dianping 爬虫、准备本地 Playwright 运行环境、规范化 CSV/JSONL 输出，或排查大众点评爬虫环境和登录/Cookie 配置问题。
---

# 大众点评内容探索

帮助用户以低频、人工可控的方式搜索大众点评商户并导出少量评论样本。技能本身只提供流程、包装器、环境检查和输出规范；第三方爬虫源码应放在技能目录外，由 `scripts/cli.py setup-source` 克隆或由用户指定。

## 技能边界

所有操作优先通过本技能目录执行：

```powershell
python scripts\cli.py <子命令>
```

不要把 Cookie、账号、代理密钥或浏览器 profile 写入 skill 仓库。不要在回答里输出 Cookie。不要做高频、大规模、绕过验证码或绕过访问控制的采集。遇到验证码或风控页面时，暂停并要求用户在可见浏览器中手动处理；不能自动破解。

默认第三方适配源是 `HDdssX/dianping_crawler`。它必须安装在外部目录，例如 `%LOCALAPPDATA%\Codex\dianping-explore\HDdssX_dianping_crawler`，并通过 `DIANPING_CRAWLER_ROOT` 或 `--crawler-root` 指向。更多适配说明见 `references/third-party-adapters.md`。

CLI 会自动读取技能私有 `.env`：`%USERPROFILE%\.codex\skills\dianping-explore\.env`。这个文件只能保存在用户级目录，不能提交进 repo。

## 子命令

| 子命令 | 用途 |
|---|---|
| `setup-source` | 克隆默认第三方爬虫到外部目录，可选创建 venv 和安装依赖 |
| `status` | 检查爬虫目录、关键文件、Python/venv、Cookie 环境变量是否就绪 |
| `run-crawler` | 调用现成爬虫搜索商户并采集少量评论，默认使用可见浏览器 |
| `normalize-csv` | 将第三方爬虫输出 CSV 规范化为 JSONL |
| `schema` | 输出本技能的规范化结果字段 |

## 常用流程

### 1. 准备第三方爬虫

```powershell
python scripts\cli.py setup-source --with-venv
```

如需安装 Playwright 浏览器：

```powershell
python scripts\cli.py setup-source --with-venv --install-browser
```

也可以使用 PowerShell 辅助脚本：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup_dianping_explore.ps1 -WithVenv -RunSmoke
```

### 2. 配置 Cookie

只用环境变量传入 Cookie，不要写进仓库或命令行：

```powershell
$env:DIANPING_COOKIE = "<从浏览器复制的 Cookie>"
```

如果用户需要长期保存，用登录辅助脚本打开可见浏览器；用户在浏览器中完成登录/验证后回到终端按 Enter，程序会自动保存本次 Playwright 会话里的大众点评 Cookie：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\assist_dianping_cookie.ps1
```

这个辅助脚本不会读取现有 Chrome/Edge profile，不需要用户复制粘贴 Cookie，也不会打印 Cookie 值。它只写入技能私有 `.env`。

### 3. 检查状态

```powershell
python scripts\cli.py status
```

### 4. 低频采集

先从很小样本开始：

```powershell
python scripts\cli.py run-crawler `
  --keyword "咖啡" `
  --cities "Shanghai" `
  --max-pages 1 `
  --comment-pages 1 `
  --output ".\outputs\dianping-coffee.csv"
```

`run-crawler` 会打开有头浏览器。若出现验证页面，请让用户手动完成验证，再回到终端继续。采集完成后再进入规范化步骤。

### 5. 规范化输出

```powershell
python scripts\cli.py normalize-csv `
  --input ".\outputs\dianping-coffee.csv" `
  --output ".\outputs\dianping-coffee.jsonl"
```

规范化字段见：

```powershell
python scripts\cli.py schema
```

## 结果呈现

向用户汇报时优先给：

- 运行目录和输出文件路径。
- 采集范围：关键词、城市、页数、评论页数。
- 结果摘要：商户数、评论数、字段是否完整。
- 风控状态：是否出现验证码、是否需要用户手动登录或更换更小范围。

## 失败处理

- **找不到爬虫目录**：运行 `setup-source`，或让用户提供 `DIANPING_CRAWLER_ROOT`。
- **Cookie 未配置**：提示用户设置 `DIANPING_COOKIE`，不要要求用户在聊天里粘贴真实 Cookie。
- **依赖缺失**：运行 `setup-source --with-venv --install-browser`。
- **验证码/安全验证**：暂停，要求用户在可见浏览器中手动处理。
- **无结果或字段缺失**：缩小城市/关键词/页数，先跑 `--max-pages 1 --comment-pages 1`。
- **需要换底层项目**：读取 `references/third-party-adapters.md`，按相同 CLI 输出契约新增适配，不要把第三方源码直接提交进 skill 仓库。
