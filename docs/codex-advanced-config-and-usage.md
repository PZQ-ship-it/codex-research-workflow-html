# Codex Advanced Config And Usage

本文件记录本仓库可复用的 Codex 高级配置、插件、skills、hooks、subagents 和验证方式。

## Skill 评估与优化闭环

`skill-eval-optimizer` 是本仓库用于测试、压测和优化 Codex skills 的专用 skill。它把 skill 维护拆成可验证闭环：`quick_validate.py` 静态验证、触发/不触发样例、`codex exec --json` trace 捕获、确定性评分、rubric JSON 评分、针对性修改和 forward-testing。

本地入口：

```powershell
python skills\skill-eval-optimizer\scripts\skill_eval_harness.py static-check skills\skill-eval-optimizer
python skills\skill-eval-optimizer\scripts\skill_eval_harness.py init-eval `
  --skill-dir skills\skill-eval-optimizer `
  --out-dir evals\skill-eval\skill-eval-optimizer
```

推荐顺序：

1. 用 `$skill-creator` 创建或修改 skill。
2. 用 `quick_validate.py` 和 `skill_eval_harness.py static-check` 做结构验证。
3. 建 10-20 条 eval prompts，至少包含 direct、implicit、negative control。
4. 用 `codex exec --json` 在隔离目录跑样例并保存 JSONL trace。
5. 用确定性检查和 `--output-schema` rubric 比较 before/after。
6. 如果 eval 需要 AnySearch、OpenAI Developer Docs MCP、GitHub、Hugging Face、Kaggle 或浏览器登录，先调用 `$external-api-onboarding`，把凭据放在用户级私有 `.env` 或 Codex MCP 配置里，不写入仓库。

## Codex Council 插件

`codex-council` 是一个 Codex-only council review 插件，用多个隔离角色做 first opinions、匿名 review/ranking、rubric scoring 和 Chairman synthesis。它适合架构决策、风险 diff、迁移、安全/隐私、性能或 release go/no-go 这类“单次自信错误代价较高”的任务。

### 当前安装状态

- 全局插件路径：`C:\Users\Administrator\.codex\plugins\codex-council`
- 仓库插件路径：`plugins/codex-council/`
- 仓库 marketplace：`.agents/plugins/marketplace.json`
- 上游：`https://github.com/ercoledevs/codex-council`
- 固定 commit：`d10b134baa09240088133a559a67d0bc7b506b91`
- 插件版本：`0.7.0`

本机有两个 Codex CLI 入口：PATH 上的旧 `codex` 和 VS Code 扩展 bundled `codex.exe`。插件验证优先使用 VS Code bundled 版本：

```powershell
$codex = "c:\Users\Administrator\.vscode\extensions\openai.chatgpt-26.5609.30741-win32-x64\bin\windows-x86_64\codex.exe"
& $codex --version
& $codex plugin list --json
```

### 安装与同步命令

全局安装：

```powershell
npx codex-marketplace add ercoledevs/codex-council --plugin --global -y
```

仓库级同步安装：

```powershell
npx codex-marketplace add ercoledevs/codex-council --plugin --project -y
```

注意：`codex plugin marketplace add ercoledevs/codex-council` 当前不适用，因为该上游是单插件仓库，不是包含 marketplace manifest 的 marketplace root。

### 验证命令

插件可见性：

```powershell
$codex = "c:\Users\Administrator\.vscode\extensions\openai.chatgpt-26.5609.30741-win32-x64\bin\windows-x86_64\codex.exe"
& $codex plugin marketplace list
& $codex plugin list --json
```

插件结构验证和估算 smoke test：

```powershell
$py = "C:\ProgramData\Anaconda3\envs\image-to-editable-ppt\python.exe"
& $py plugins\codex-council\scripts\codex_council.py validate --plugin-root plugins\codex-council --strict
& $py plugins\codex-council\scripts\codex_council.py estimate --topic "Install smoke test" --mode fast --token-budget compact
```

单元测试需要在插件根目录运行，否则测试导入不到 `scripts` 包：

```powershell
Push-Location plugins\codex-council
& "C:\ProgramData\Anaconda3\envs\image-to-editable-ppt\python.exe" -m unittest discover -s tests -v
Pop-Location
```

本机默认 `python` 是 Python 3.7.0，运行 `validate --strict` 会因为缺少 `str.removeprefix` 报错；使用 Python 3.9+ 即可。

### 使用方式

在新 Codex 线程里直接说：

```text
Use Codex Council to review this architecture decision.
Focus on blockers, rollback, and verification.
```

重要行为边界：

- Standard/Deep/Expanded 前必须先显示 preflight estimate 并等待用户确认。
- `expanded` 必须显式确认。
- Council 的 role diversity 不是 multi-provider model diversity。
- UI 行为不能在没有 Bob 或等价 browser evidence 时声称已验证。
- 运行完成后应保留 blockers、dissent、verification 和 confidence。

适合搭配后续本地 `codex-deep-think` wrapper：先用 planner 判断是否需要 fanout；风险决策再调用 Codex Council；最后用 consensus/adversarial QA 收敛。
