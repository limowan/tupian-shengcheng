---
name: tupian-shengcheng
description: Generate images through OpenAI-compatible image or chat/completions endpoints and save the resulting image. Use when users ask to create images, need a dedicated image-generation backend, or want to wire image generation into other skills/workflows (e.g., baoyu-xhs-images).
---

# 图片生成（OpenAI 兼容）

## Overview

通过 OpenAI 兼容接口生成图片，并自动保存最终返回的图片。现在支持三类后端：

- 标准图片接口：`/v1/images/generations`，用于 `gpt-image-2`
- 标准改图接口：`/v1/images/edits`，仅当用户明确要求改图时使用
- 兼容聊天接口：`/v1/chat/completions`，用于原来的 flow2api / devoi 图片模型
- 火山引擎接口：`/api/plan/v3/images/generations`，用于字节跳动 Seedream 系列模型

这个 Skill 使用自己的 `config.json`，不读取也不修改 Codex CLI 的 `config.toml` / `auth.json`。
首次安装时，如果 `config.json` 不存在，先让用户复制 `config.example.json` 为 `config.json`，再填入自己的 API Key。

## Default Behavior

- 默认使用 `active_profile` 指定的 profile（当前为 `ai_pixel`，即 `gpt-image-2`）。
- 默认模式是直接生图：走 `/v1/images/generations`。
- 只有当用户明确说”改图””修改这张图””基于这张图调整””把图里的文字改成...”等，才使用 `--edit-image` 走 `/v1/images/edits`。
- 即使已有默认配置，真正发起图片 API 请求前，也必须先向用户确认：模式（生图/改图）、模型、输入图片（如有）、输出路径和核心提示词。
- 用户确认后再执行；不要因为默认配置存在就直接发请求。

## Profile 路由规则

当用户提到以下关键词时，必须使用 `--profile volcengine`（火山引擎 Seedream）：
- “即梦”、”jimeng”
- “字节生图”、”字节的生图模型”、”字节的模型”
- “doubao”、”豆包”
- “seedream”
- “火山引擎”、”volcengine”

其他情况使用默认 profile（当前为 `ai_pixel` / `gpt-image-2`）。

## Quick Start

```bash
python scripts/generate_image.py --prompt "一张小红书风格的知识卡片：时间管理" --out "C:\temp\time.png"

python scripts/generate_image.py --profile gpt_image_2 --prompt "一张极简风格的测试图片" --out "C:\temp\gpt-image-2-test.png" --size 1024x1024

python scripts/generate_image.py --edit-image "C:\temp\source.png" --prompt "只把顶部标题改成：普通人怎么学AI" --out "C:\temp\edited.png" --size 1024x1536

# 火山引擎 Seedream（即梦/字节生图）
python scripts/generate_image.py --profile volcengine --prompt "一张杂志风格的封面" --out "C:\temp\cover.png" --size 4K

# 火山引擎指定像素尺寸
python scripts/generate_image.py --profile volcengine --prompt "横版海报" --out "C:\temp\poster.png" --size 2848x1600

# 火山引擎组图生成
python scripts/generate_image.py --profile volcengine --prompt "生成4张连贯插画" --out "C:\temp\group.png" --size 2K --sequential auto --max-images 4

# 火山引擎图生图
python scripts/generate_image.py --profile volcengine --prompt "将服装改为红色" --image "https://example.com/input.png" --out "C:\temp\edited.png" --size 2K
```

## Configuration

默认配置模板在 `config.example.json`，本地真实配置在 `config.json`：
- `active_profile`: 当前启用的调用方式（默认 `ai_pixel`）
- `profiles.ai_pixel`: 标准图片接口，模型为 `gpt-image-2`（ai-pixel.online）
- `profiles.gpt_image_2`: 标准图片接口，模型为 `gpt-image-2`（tokenclub.top）
- `profiles.volcengine`: 火山引擎接口，模型为 `doubao-seedream-5.0-lite`
- `profiles.new`: 兼容聊天接口（flow2api）
- `profiles.old`: 原始调用代码（devoi）
- 每个 profile 都可单独配置 `request_mode` / `base_url` / `model` / `api_key`

volcengine profile 额外支持 `default_size` 字段（默认 `4K`），当用户未指定 `--size` 时自动使用。

`ai_pixel` / `gpt_image_2` 的 `base_url` 写域名即可，脚本会自动拼成 `/v1/images/generations`。

注意：截图里的 `wire_api = "responses"` 是 Codex 聊天配置，不是图片接口配置。这里不需要改 Codex 配置。

运行时覆盖：

```bash
set IMAGE_API_KEY=sk-...
python scripts/generate_image.py --prompt "..."

python scripts/generate_image.py --prompt "..." --base-url "https://flow2api.uniky.net/v1/chat/completions" --model "gemini-3.0-pro-image-square"

python scripts/generate_image.py --prompt "..." --profile old

python scripts/generate_image.py --profile gpt_image_2 --prompt "..." --size 1024x1024 --quality medium
```

兼容的环境变量：
- `IMAGE_API_KEY` / `FLOW2API_API_KEY` / `OPENAI_API_KEY` / `DEVOI_API_KEY`
- `IMAGE_API_BASE_URL` / `FLOW2API_BASE_URL`
- `IMAGE_MODEL` / `FLOW2API_MODEL`
- `IMAGE_PROFILE`
- `IMAGE_REQUEST_MODE`

## Script Usage

主脚本：`scripts/generate_image.py`

参数：
- `--prompt` 或 `--prompt-file`
- `--profile` 从 `config.json` 选择 profile
- `--request-mode` 强制指定 `new` / `old` / `openai_images` / `volcengine`
- `--out` 输出文件路径或目录
- `--base-url` / `--model` / `--api-key`
- `--no-stream`，当接口不支持流式时关闭流式
- `--size` / `--quality` / `--n`，用于 `openai_images` 模式。gpt-image-2 支持 `1024x1024`、`1536x1024`、`1024x1536` 和 `auto`（由模型根据提示词自动选择最佳尺寸，推荐默认使用）
- `--edit-image` 指定原图路径；只有用户明确要求改图时使用
- `--image` 参考图 URL，多图用逗号分隔（volcengine 模式）
- `--output-format` 输出格式：png 或 jpeg（volcengine 模式）
- `--response-format` 返回方式：url 或 b64_json（volcengine 模式）
- `--sequential` 组图模式：auto 或 disabled（volcengine 模式）
- `--max-images` 组图最大数量（volcengine 模式）

返回兼容范围：
- `request_mode = old`：按原始代码处理，优先假设响应里有 Markdown 图片链接或纯图片 URL
- `request_mode = new`：按当前兼容逻辑处理
- `request_mode = openai_images`：默认按 OpenAI Images API 文生图处理，发送 `model` / `prompt` / `size` / `quality` / `n`
- `request_mode = volcengine`：火山引擎 Seedream 接口，支持文生图/图生图/组图生成
- `--edit-image`：在 `openai_images` 模式下改图，上传本地图片文件并走 `/v1/images/edits`
- 直接返回图片二进制，例如 `image/png`
- JSON 中返回图片 URL、`data:image/...`、`b64_json`
- `choices[0].message.content` 中返回 Markdown 图片链接或纯图片 URL

如需核对接口约定和可选模型，读取 `references/API接口文档.md`。
如需回看这个 skill 最初的调用方式、旧参数和核心代码，读取 `references/原始调用方式归档.md`。
如需查看火山引擎 Seedream 的完整 API 文档（参数、尺寸表、场景示例），读取 `references/火山引擎Seedream接口文档.md`。
如需确定目标平台的推荐图片尺寸（公众号封面/插图、小红书封面、B站封面、抖音封面等），读取 `references/平台图片尺寸参考.md`。

## When to Use This Skill

- 需要稳定图片生成后端时
- 给 `baoyu-xhs-images` 或其他流程提供图片生成能力
- 需要自定义 OpenAI 兼容 `base_url` 时
- 用户提到"即梦""字节生图""豆包""seedream""火山引擎"时，使用 volcengine profile
