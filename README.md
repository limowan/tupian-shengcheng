# 图片生成 Skill

这是一个 Claude/Codex 可用的图片生成 Skill，支持通过 OpenAI 兼容图片接口、聊天兼容接口和火山引擎 Seedream 接口生成图片。

默认优先级：

```text
ai_pixel
→ openai_images
→ https://cf.ai-pixel.online
→ gpt-image-2
```

也就是说，默认先走 pixel 路径，调用 GPT 图片生成模型。

## 安装

把本目录复制到你的 Skills 目录，例如：

```powershell
C:\Users\你的用户名\.claude\skills\tupian-shengcheng
```

## 配置

复制示例配置：

```powershell
Copy-Item config.example.json config.json
```

然后打开 `config.json`，把对应 profile 里的 `api_key` 改成你自己的 API Key。

默认使用：

```json
{
  "active_profile": "ai_pixel"
}
```

如果你只想临时传 Key，也可以不写入 `config.json`：

```powershell
$env:IMAGE_API_KEY="你的 API Key"
python scripts/generate_image.py --prompt "一张极简风格的测试图片"
```

## 使用

直接生图：

```powershell
python scripts/generate_image.py --prompt "一张小红书风格的知识卡片：时间管理"
```

指定尺寸：

```powershell
python scripts/generate_image.py --prompt "一张极简风格的测试图片" --size 1024x1024
```

改图：

```powershell
python scripts/generate_image.py --edit-image "你的原图路径.png" --prompt "只把顶部标题改成：普通人怎么学AI" --size 1024x1536
```

火山引擎 Seedream：

```powershell
python scripts/generate_image.py --profile volcengine --prompt "一张杂志风格的封面" --size 4K
```

## 文件说明

- `SKILL.md`：给 AI 看的 Skill 使用说明。
- `scripts/generate_image.py`：实际调用图片 API 的脚本。
- `config.example.json`：公开示例配置，不包含真实密钥。
- `config.json`：你的本地真实配置，已被 `.gitignore` 排除，不要提交。
- `references/`：接口说明和尺寸参考。

## 注意

- 公开仓库不要提交 `config.json`。
- 公开仓库不要提交 `output/` 里的生成图片。
- 真正发起图片 API 请求前，AI 应先确认模式、模型、输出路径和核心提示词。
