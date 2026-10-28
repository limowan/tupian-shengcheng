# 图片生成 Skill

> 让 Claude Code 或 Codex 调用你配置的图片模型，生成或修改图片，并保存结果。

## 功能简介

`tupian-shengcheng` 支持通过 OpenAI 兼容图片接口、聊天兼容接口和火山引擎 Seedream 接口生成图片。它可以独立使用，也可以为其他需要图片的 Skill 提供生图能力。

- 用文字提示生成图片，支持指定模型和尺寸。
- 修改已有图片，具体能力取决于所选接口。
- 使用 Seedream 生成单张图片或组图。
- 通过随附的 Python 脚本请求接口，将结果保存到本地。

图片接口可能产生费用，具体以你使用的服务商为准。

默认优先级：

```text
ai_pixel
→ openai_images
→ https://ai-pixel.online
→ gpt-image-2
```

也就是说，默认先走 pixel 路径，调用 GPT 图片生成模型。

## 安装方式

把本目录复制到你的 Skills 目录，例如：

```powershell
C:\Users\你的用户名\.claude\skills\tupian-shengcheng
```

新仓库发布后，也可以让 AI 帮你安装：

```text
帮我安装一下 https://github.com/limowan/tupian-shengcheng 这个 Skill
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

## 使用方法

也可以直接对 Claude Code 或 Codex 说：

```text
用图片生成 Skill 画一张小红书风格的时间管理知识卡片，竖版，提示词先给我确认。
```

下面的命令在 Skill 目录下执行：

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

## 隐私与数据安全

- `config.json` 和配置备份可能包含真实密钥，请妥善保管，不要分享或提交。
- 提示词和输入图片会发送给你选择的接口服务商，请先确认其隐私政策及素材授权。
- 生成结果保存在本地指定位置，不应将个人素材或生成图片提交到 Skill 仓库。
- 不同模型对中文文字和细节的表现不同，成图后请检查。

## License

本项目当前未附独立许可证文件，使用和分发条款以仓库后续公布的信息为准。

## 关于作者

**墨玩AI** — 独立开发者，和你一起探索 AI 在生活中的有趣用法 🌱

### 我的产品

| 产品 | 说明 | 使用方式 |
|------|------|----------|
| 🌐 墨成AI排版 | AI 快捷公众号文章排版工具 | [mocheng.mowan.work](https://mocheng.mowan.work) |
| 📱 问问毛选 | 毛选语录抽卡，真正的答案之书 | 微信搜「问问毛选」；如小程序不可用，可用[网页版](https://wwmx.mowan.work/app/) |
| ☀️ 坐哪侧 | 出行选座小工具，帮你判断坐哪侧更适合避晒、看日落或赏月 | 微信搜「坐哪侧」 |

### 关注我

| 平台 | 链接 |
|------|------|
| 📕 小红书 | [墨玩AI](https://xhslink.com/m/3Ks23mHtPrL) |
| 📺 B站 | [墨玩AI](https://space.bilibili.com/696270041) |
| 💬 公众号 | 微信搜「墨玩AI」 |

<img src="https://raw.githubusercontent.com/limowan/mowan-mc-type/main/wechat_qrcode.jpg" width="200" alt="墨玩AI 公众号二维码">
