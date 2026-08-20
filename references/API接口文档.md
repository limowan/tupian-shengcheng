# 文生图接口文档

本文档只保留 `tupian-shengcheng` skill 当前需要的文生图接口约定，不再保留音频转写、文档解析、历史记录等应用内配置项。

如果需要查看这个 skill 历史上的旧调用方式、旧参数和核心代码片段，另读 `原始调用方式归档.md`。

当前脚本已经支持通过 `config.json` 的 `active_profile` 在多种调用方式之间切换，并通过 `request_mode` 明确指定调用模式：

- `openai_images`: 标准图片接口，当前用于 `gpt-image-2`
- `new`: 当前 flow2api 兼容实现，走 `chat/completions`
- `old`: 原始 devoi 调用实现，走 `chat/completions`

本 Skill 使用自己的 `config.json`，不会读取或修改 Codex CLI 的 `%userprofile%\.codex\config.toml` / `auth.json`。截图里的 `wire_api = "responses"` 是 Codex 聊天配置，不是图片接口配置。

默认使用 `ai_pixel` profile。执行层默认是直接生图，只有调用时传入 `--edit-image` 才会走改图接口。

重要工作流约束：即使默认 profile 已经是 `ai_pixel`，实际发起图片 API 请求前，也要先向用户确认模式、模型、输入图片、输出路径和核心提示词。

## gpt-image-2 标准图片接口

- profile: `ai_pixel`
- request_mode: `openai_images`
- 默认 `base_url`: `https://cf.ai-pixel.online`
- 实际请求地址: `https://cf.ai-pixel.online/v1/images/generations`
- 改图请求地址: `https://cf.ai-pixel.online/v1/images/edits`
- 请求方式: `POST`
- Content-Type: `application/json`
- 认证方式: `Authorization: Bearer <api_key>`
- 模型: `gpt-image-2`

如果 `base_url` 只写域名，脚本会自动拼 `/v1/images/generations`；如果已经写完整接口地址，则直接使用。

### gpt-image-2 最小请求体

```json
{
  "model": "gpt-image-2",
  "prompt": "一张极简风格的信息图，主题是高效复盘",
  "size": "1024x1024",
  "quality": "low",
  "n": 1
}
```

当前脚本会从响应中提取：

- `data[0].b64_json`
- `data[0].url`
- 或兼容的嵌套图片字段

### 改图模式

只有用户明确要求改图时才使用：

```powershell
python scripts/generate_image.py --edit-image "C:\temp\source.png" --prompt "只把顶部标题改成：普通人怎么学AI" --out "C:\temp\edited.png" --size 1024x1536 --quality medium
```

当前脚本会把本地图片作为文件上传到 `/v1/images/edits`，不是把图片塞进文生图接口。

### Windows 示例

```powershell
python scripts/generate_image.py --profile gpt_image_2 --prompt "一张极简风格的测试图片" --out "C:\temp\gpt-image-2-test.png" --size 1024x1024 --quality medium
```

如果不想把密钥写入 `config.json`，可以临时设置环境变量：

```powershell
$env:IMAGE_API_KEY="sk-..."
python scripts/generate_image.py --profile gpt_image_2 --prompt "一张极简风格的测试图片" --out "C:\temp\gpt-image-2-test.png"
```

## 原始项目

- 项目地址: [flow2api](https://github.com/TheSmallHanCat/flow2api)

## flow2api 默认接口

- 默认 `base_url`: `https://flow2api.uniky.net/v1/chat/completions`
- 请求方式: `POST`
- Content-Type: `application/json`
- 认证方式: `Authorization: Bearer <api_key>`

## flow2api 最小请求体

```json
{
  "model": "gemini-3.1-flash-image-landscape",
  "messages": [
    {
      "role": "user",
      "content": "请生成一张极简风的信息图，主题是番茄工作法"
    }
  ],
  "stream": true
}
```

flow2api / old 模式只依赖下面 3 个字段：

| 字段 | 必填 | 说明 |
|------|------|------|
| `model` | 是 | 图片生成模型名 |
| `messages` | 是 | 标准 `chat/completions` 消息数组 |
| `stream` | 否 | 是否启用流式，默认可开 |

不再要求或使用应用内那些额外字段，例如 `file`、`input_text`、`prompt_template`、`output_dir` 等。

## cURL 示例

```bash
curl -X POST "https://flow2api.uniky.net/v1/chat/completions" \
  -H "Authorization: Bearer $IMAGE_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"gemini-3.1-flash-image-landscape\",\"messages\":[{\"role\":\"user\",\"content\":\"请生成一张蓝白配色的信息图，主题是高效复盘\"}],\"stream\":true}"
```

## Python 示例

```python
import requests

url = "https://flow2api.uniky.net/v1/chat/completions"
headers = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json",
}
payload = {
    "model": "gemini-3.1-flash-image-landscape",
    "messages": [
        {
            "role": "user",
            "content": "请生成一张适合社交媒体分享的信息图，主题是高质量提问。"
        }
    ],
    "stream": False,
}

resp = requests.post(url, headers=headers, json=payload, timeout=120)
print(resp.status_code)
print(resp.headers.get("Content-Type"))
print(resp.text[:500])
```

## 可选模型

| 模型名称 | 说明 | 尺寸 |
|------|------|------|
| `gemini-2.5-flash-image-landscape` | 图/文生图 | 横屏 |
| `gemini-2.5-flash-image-portrait` | 图/文生图 | 竖屏 |
| `gemini-3.0-pro-image-landscape` | 图/文生图 | 横屏 |
| `gemini-3.0-pro-image-portrait` | 图/文生图 | 竖屏 |
| `gemini-3.0-pro-image-square` | 图/文生图 | 方图 |
| `gemini-3.0-pro-image-four-three` | 图/文生图 | 横屏 4:3 |
| `gemini-3.0-pro-image-three-four` | 图/文生图 | 竖屏 3:4 |
| `gemini-3.0-pro-image-landscape-2k` | 图/文生图(2K) | 横屏 |
| `gemini-3.0-pro-image-portrait-2k` | 图/文生图(2K) | 竖屏 |
| `gemini-3.0-pro-image-square-2k` | 图/文生图(2K) | 方图 |
| `gemini-3.0-pro-image-four-three-2k` | 图/文生图(2K) | 横屏 4:3 |
| `gemini-3.0-pro-image-three-four-2k` | 图/文生图(2K) | 竖屏 3:4 |
| `gemini-3.0-pro-image-landscape-4k` | 图/文生图(4K) | 横屏 |
| `gemini-3.0-pro-image-portrait-4k` | 图/文生图(4K) | 竖屏 |
| `gemini-3.0-pro-image-square-4k` | 图/文生图(4K) | 方图 |
| `gemini-3.0-pro-image-four-three-4k` | 图/文生图(4K) | 横屏 4:3 |
| `gemini-3.0-pro-image-three-four-4k` | 图/文生图(4K) | 竖屏 3:4 |
| `imagen-4.0-generate-preview-landscape` | 图/文生图 | 横屏 |
| `imagen-4.0-generate-preview-portrait` | 图/文生图 | 竖屏 |
| `gemini-3.1-flash-image-landscape` | 图/文生图 | 横屏 |
| `gemini-3.1-flash-image-portrait` | 图/文生图 | 竖屏 |
| `gemini-3.1-flash-image-square` | 图/文生图 | 方图 |
| `gemini-3.1-flash-image-four-three` | 图/文生图 | 横屏 4:3 |
| `gemini-3.1-flash-image-three-four` | 图/文生图 | 竖屏 3:4 |
| `gemini-3.1-flash-image-landscape-2k` | 图/文生图(2K) | 横屏 |
| `gemini-3.1-flash-image-portrait-2k` | 图/文生图(2K) | 竖屏 |
| `gemini-3.1-flash-image-square-2k` | 图/文生图(2K) | 方图 |
| `gemini-3.1-flash-image-four-three-2k` | 图/文生图(2K) | 横屏 4:3 |
| `gemini-3.1-flash-image-three-four-2k` | 图/文生图(2K) | 竖屏 3:4 |
| `gemini-3.1-flash-image-landscape-4k` | 图/文生图(4K) | 横屏 |
| `gemini-3.1-flash-image-portrait-4k` | 图/文生图(4K) | 竖屏 |
| `gemini-3.1-flash-image-square-4k` | 图/文生图(4K) | 方图 |
| `gemini-3.1-flash-image-four-three-4k` | 图/文生图(4K) | 横屏 4:3 |
| `gemini-3.1-flash-image-three-four-4k` | 图/文生图(4K) | 竖屏 3:4 |

## skill 当前兼容的响应形式

`scripts/generate_image.py` 目前兼容以下返回方式，只要最终能拿到图片即可：

1. 直接返回图片二进制  
   例如响应头为 `image/png`、`image/jpeg`、`image/webp`

2. JSON 中直接给图片  
   例如：
   ```json
   {
     "data": [
       {
         "url": "https://example.com/image.png"
       }
     ]
   }
   ```

   或：
   ```json
   {
     "data": [
       {
         "b64_json": "iVBORw0KGgoAAA..."
       }
     ]
   }
   ```

3. `chat/completions` 文本内容中给图片  
   例如：
   ```json
   {
     "choices": [
       {
         "message": {
           "content": "![](https://example.com/image.png)"
         }
       }
     ]
   }
   ```

   也支持纯图片 URL 或 `data:image/...;base64,...`

## 与旧文档的区别

- 不再描述 `/api/generate-image` 这类应用层封装接口
- 不再描述音频、PDF、配置、历史记录等非文生图能力
- 不再要求上传文件或传入应用特定参数
- 只保留 `chat/completions` 风格文生图所需的最小契约

## skill 入口

```bash
python scripts/generate_image.py --prompt "请生成一张关于复利思维的信息图" --out "C:\temp\compound.png"
```

临时使用 `gpt-image-2`：

```bash
python scripts/generate_image.py --profile gpt_image_2 --prompt "请生成一张关于复利思维的信息图" --out "C:\temp\compound.png" --size 1024x1024
```

切到当前方式：

```json
{
  "active_profile": "new"
}
```

临时切到旧方式：

```bash
python scripts/generate_image.py --prompt "请生成一张关于复利思维的信息图" --profile old
```

脚本默认读取：

- `config.json` 中的 `active_profile` 和对应 `profiles.<name>`
- 或环境变量 `IMAGE_API_KEY`、`FLOW2API_API_KEY`、`OPENAI_API_KEY`

其中：

- `request_mode = "openai_images"`: 标准图片接口，当前用于 `gpt-image-2`
- `request_mode = "new"`: 当前兼容实现
- `request_mode = "old"`: 原始调用实现

*文档版本: v2.2 | 最后更新: 2026-04-27*
