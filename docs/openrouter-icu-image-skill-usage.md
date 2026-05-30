# OpenRouter ICU Image Skill 使用说明

`openrouter-icu-image` 用于通过 OpenRouter ICU 的 OpenAI-compatible image API 同步生成或编辑图片。项目本地 skill 位于：

```text
skills/openrouter-icu-image/
```

同步到全局 Codex 后的位置是：

```text
C:\Users\Administrator\.codex\skills\openrouter-icu-image\
```

安装或更新全局 skill 后，重启 Codex 才能稳定拾取新的 skill 列表。

## 适用场景

- 文本生成图片，例如产品图、插图、封面、UI 背景、论文或文档配图草案。
- 基于本地图片做编辑，例如换背景、调整风格、保留主体生成新场景。
- 使用多张参考图合成视觉资产。
- 需要把最终图片保存到项目目录，并等待文件生成后再继续后续工作。

不适合：

- 处理敏感图片或不应上传到第三方服务的资料。
- 生成需要严格工程精度的图纸、原理图、PCB、医学或法律证据图。
- 后台异步提交后立刻继续工作；本 skill 要求同步等待最终图片落盘。

## 凭据配置

调用 API 前必须配置 `OPENROUTER_ICU_API_KEY`。不要把真实 key 写进仓库文档、提交记录或聊天记录。

PowerShell 当前会话临时配置：

```powershell
$env:OPENROUTER_ICU_API_KEY = "<your_key_here>"
```

如果需要长期使用，建议放在用户级环境变量或本机私密 `.env` 管理中，避免提交到 Git。验证是否已设置时只检查存在性，不打印内容：

```powershell
if ($env:OPENROUTER_ICU_API_KEY) { "OPENROUTER_ICU_API_KEY is set" } else { "OPENROUTER_ICU_API_KEY is NOT set" }
```

全局 skill 也支持读取本机私密文件：

```text
C:\Users\Administrator\.codex\skills\openrouter-icu-image\.env
```

文件内容格式如下。真实 key 只应写在本机私密文件中，不要写入仓库：

```text
OPENROUTER_ICU_API_KEY=<your_key_here>
```

也可以用 helper 脚本隐藏输入并写入全局 `.env`：

```powershell
powershell -ExecutionPolicy Bypass -File C:\Users\Administrator\.codex\skills\openrouter-icu-image\scripts\set_openrouter_icu_key.ps1
```

## 基本命令

在项目根目录运行时，推荐直接调用 repo-local skill 脚本。本机已验证 `python` 可用；如果你的环境安装了 Python launcher，也可以把下面命令中的 `python` 替换为 `py -3`。

```powershell
python skills\openrouter-icu-image\scripts\openrouter_icu_image.py generate `
  --prompt "A clean product photo of a white ceramic coffee mug on a wooden desk, soft natural light" `
  --size 1024x1024 `
  --quality medium `
  --output-format png `
  --output output\openrouter-icu\mug.png
```

如果在 WSL、Linux 或 macOS 中使用，通常可写成：

```bash
python3 skills/openrouter-icu-image/scripts/openrouter_icu_image.py generate \
  --prompt "A clean product photo of a white ceramic coffee mug on a wooden desk, soft natural light" \
  --size 1024x1024 \
  --quality medium \
  --output-format png \
  --output output/openrouter-icu/mug.png
```

## 编辑本地图片

```powershell
python skills\openrouter-icu-image\scripts\openrouter_icu_image.py edit `
  --image input\portrait.png `
  --prompt "Change the background to a clean modern office while preserving the person, clothing, pose, and facial features" `
  --size 1024x1024 `
  --quality medium `
  --output output\openrouter-icu\portrait-office.png
```

多图参考：

```powershell
python skills\openrouter-icu-image\scripts\openrouter_icu_image.py edit `
  --image input\product.png `
  --image input\background-reference.png `
  --prompt "Create a premium product photo using the product from the first image and the environment style from the second image" `
  --size 1536x1024 `
  --quality high `
  --output output\openrouter-icu\product.png
```

## Dry Run

使用 `--dry-run` 检查请求形状，不发起网络请求：

```powershell
python skills\openrouter-icu-image\scripts\openrouter_icu_image.py generate `
  --prompt "A minimal abstract cover image for a research workflow note" `
  --size 1024x1024 `
  --quality medium `
  --output-format png `
  --output output\openrouter-icu\cover.png `
  --dry-run
```

## 常用参数

| 参数 | 默认/建议 | 说明 |
|---|---|---|
| `--model` | `gpt-image-2` | 默认模型。 |
| `--size` | `1024x1024` | 支持 `1536x1024`、`1024x1536`、`2048x2048` 等。 |
| `--quality` | `medium` | 草稿用 `low`，最终资产可用 `high`。 |
| `--output-format` | `png` | 可按需要改为 `jpeg` 或 `webp`。 |
| `--stream` | 默认启用 | 解析 streaming SSE，并等待最终图片。 |
| `--partial-images` | `2` | streaming 时用于进度图片。 |
| `--events-output` | 可选 | 保存事件日志，便于排障。 |
| `--base-url` | `https://openrouter.icu` | 也接受 `https://openrouter.icu/v1`。 |

自定义尺寸要求：

- 格式为 `WIDTHxHEIGHT`。
- 宽高都能被 16 整除。
- 宽高比在 `1:3` 到 `3:1` 之间。
- 不超过 `3840x2160` 等价像素规模。

## Prompt 写法

图片 prompt 只描述视觉目标，不要把 API 参数、文件路径、key、模型名混进 prompt。

在 `manuscript-to-ppt-workflow` 中生成源事实驱动的学术图时，不要直接临场写 prompt 后生图。必须先通过 `academic-figure-prompt` 产出并确认：

```text
align/academic_figure_prompt_v*.md
stage_status: confirmed
```

然后 `openrouter-icu-image` 只使用该 artifact 中已确认的英文视觉 prompt；模型、尺寸、质量、输出路径仍作为 API/CLI 参数单独设置。

建议包含：

- 主体：人物、产品、场景或图形对象。
- 构图：镜头角度、景别、主体位置、留白。
- 材质和光线：金属、陶瓷、玻璃、自然光、柔光箱。
- 风格：写实、扁平插画、科技感、学术图形。
- 负向约束：保留文字、不要改变主体、不要添加水印。

示例：

```text
A clean editorial cover image for a Codex workflow handbook, showing a structured desk with notes, terminal windows, and schematic planning cards, calm professional lighting, no visible brand logos.
```

## 错误处理

- `401`：检查 `OPENROUTER_ICU_API_KEY` 是否存在或有效。
- `400`：通常是参数、尺寸、格式或 prompt 问题；不要原样重试。
- `403` / `404`：检查模型、权限、文件 ID、图片 URL。
- `408` / `409` / `429` / `5xx`：可以做有限重试和退避。

排障时保留这些信息，但不要输出 key：

- HTTP status
- request id
- model
- size
- quality
- output format
- streaming mode
- 最后一个 SSE event type

## Codex 调用示例

```text
$openrouter-icu-image "生成一张用于 docs 首页的研究工作流封面图，输出到 output/openrouter-icu/workflow-cover.png"
```

```text
$openrouter-icu-image "编辑 input/product.png，把背景换成明亮的桌面摄影棚，保持产品文字和形状不变，输出到 output/openrouter-icu/product-clean.png"
```

## 维护备注

- `skills/openrouter-icu-image/SKILL.md` 是 skill 入口。
- `skills/openrouter-icu-image/references/api.md` 保存完整 API 说明和更多示例。
- `skills/openrouter-icu-image/scripts/openrouter_icu_image.py` 是首选执行脚本。
- 不要提交真实 API key、生成中间日志里的敏感内容或不应公开的参考图片。
