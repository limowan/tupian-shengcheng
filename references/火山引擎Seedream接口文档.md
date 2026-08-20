# 火山引擎 Seedream API 文档

## 接口地址

```
POST https://ark.cn-beijing.volces.com/api/v3/images/generations
```

注意：Coding Plan 接口路径为 `/api/plan/v3/images/generations`，标准接口为 `/api/v3/images/generations`。

## 认证

```
Authorization: Bearer <API_KEY>
```

## 模型列表

| 模型名称 | Model ID |
|---------|----------|
| Seedream 5.0 lite | doubao-seedream-5-0-260128 (别名: doubao-seedream-5-0-lite-260128) |
| Seedream 4.5 | doubao-seedream-4-5-251128 |
| Seedream 4.0 | doubao-seedream-4-0-250828 |

## 支持的场景

| 场景 | 说明 |
|------|------|
| 文生图 | 纯文本输入，单图输出 |
| 文生组图 | 纯文本输入，多图输出 |
| 单图生图 | 单图+文本输入，单图输出 |
| 多图生图 | 多图+文本输入，单图输出（多图融合） |
| 单图生组图 | 单图+文本输入，多图输出 |
| 多图生组图 | 多图+文本输入，多图输出 |
| 联网搜索 | Seedream 5.0 lite 支持，融合实时网络信息 |
| 流式输出 | 生成完任一图片后即返回 |

## 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| model | string | 是 | 模型 ID |
| prompt | string | 是 | 文本提示词，建议不超过300汉字或600英文单词 |
| size | string | 否 | 图像尺寸，支持分辨率档位或像素值 |
| image | string/array | 否 | 参考图，单图为字符串，多图为数组。支持 URL 或 Base64 |
| output_format | string | 否 | 输出格式：png, jpeg（5.0 lite 支持自定义，4.5/4.0 默认 jpeg） |
| watermark | boolean | 否 | 是否添加水印，false=不添加，true=右下角"AI生成" |
| response_format | string | 否 | 返回方式：url（图片下载链接）, b64_json（Base64） |
| stream | boolean | 否 | 是否流式输出 |
| sequential_image_generation | string | 否 | 组图模式：auto=开启组图, disabled=关闭 |
| sequential_image_generation_options | object | 否 | 组图选项，如 {"max_images": 4} |
| optimize_prompt_options | object | 否 | 提示词优化：{"mode": "standard"} 或 {"mode": "fast"}（仅4.0支持fast） |
| tools | array | 否 | 工具列表，如 [{"type": "web_search"}]（仅5.0 lite支持） |

## 图像尺寸 (size)

### 方式1：分辨率档位

在 prompt 中用自然语言描述宽高比，由模型判断具体尺寸。

| 模型 | 支持的档位 |
|------|-----------|
| Seedream 5.0 lite | 2K, 3K, 4K |
| Seedream 4.5 | 2K, 4K |
| Seedream 4.0 | 1K, 2K, 4K |

### 方式2：指定像素值

格式：`{width}x{height}`，默认 2048x2048

- 宽高比范围：[1/16, 16]
- 总像素范围：
  - Seedream 5.0 lite: [2560x1440=3686400, 4096x4096=16777216]
  - Seedream 4.5: [2560x1440=3686400, 4096x4096=16777216]
  - Seedream 4.0: [1280x720=921600, 4096x4096=16777216]

### 推荐像素值表

#### Seedream 5.0 lite

| 比例 | 2K | 3K | 4K |
|------|----|----|-----|
| 1:1 | 2048x2048 | 3072x3072 | 4096x4096 |
| 3:4 | 1728x2304 | 2592x3456 | 3520x4704 |
| 4:3 | 2304x1728 | 3456x2592 | 4704x3520 |
| 16:9 | 2848x1600 | 4096x2304 | 5504x3040 |
| 9:16 | 1600x2848 | 2304x4096 | 3040x5504 |
| 3:2 | 2496x1664 | 3744x2496 | 4992x3328 |
| 2:3 | 1664x2496 | 2496x3744 | 3328x4992 |
| 21:9 | 3136x1344 | 4704x2016 | 6240x2656 |

#### Seedream 4.5

| 比例 | 2K | 4K |
|------|----|----|
| 1:1 | 2048x2048 | 4096x4096 |
| 3:4 | 1728x2304 | 3520x4704 |
| 4:3 | 2304x1728 | 4704x3520 |
| 16:9 | 2848x1600 | 5504x3040 |
| 9:16 | 1600x2848 | 3040x5504 |
| 3:2 | 2496x1664 | 4992x3328 |
| 2:3 | 1664x2496 | 3328x4992 |
| 21:9 | 3136x1344 | 6240x2656 |

#### Seedream 4.0

| 比例 | 1K | 2K | 4K |
|------|----|----|-----|
| 1:1 | 1024x1024 | 2048x2048 | 4096x4096 |
| 3:4 | 864x1152 | 1728x2304 | 3520x4704 |
| 4:3 | 1152x864 | 2304x1728 | 4704x3520 |
| 16:9 | 1312x736 | 2848x1600 | 5504x3040 |
| 9:16 | 736x1312 | 1600x2848 | 3040x5504 |
| 3:2 | 1248x832 | 2496x1664 | 4992x3328 |
| 2:3 | 832x1248 | 1664x2496 | 3328x4992 |
| 21:9 | 1568x672 | 3136x1344 | 6240x2656 |

## 图片传入限制

- 格式：jpeg, png, webp, bmp, tiff, gif, heic, heif
- 传入方式：URL 或 Base64（格式：`data:image/<格式>;base64,<编码>`）
- 宽高比范围：[1/16, 16]
- 宽高长度 > 14px
- 大小：不超过 30MB
- 总像素：不超过 6000x6000=36000000px
- 最多支持传入 14 张参考图
- 输入参考图数量 + 最终生成图片数量 ≤ 15张

## 限流

- 500 张/分钟（IPM）

## 数据保存

- 任务数据（任务状态、图片URL等）仅保留24小时

## 代码示例

### 文生图

```bash
curl https://ark.cn-beijing.volces.com/api/v3/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ARK_API_KEY" \
  -d '{
    "model": "doubao-seedream-5-0-260128",
    "prompt": "充满活力的特写编辑肖像",
    "size": "4K",
    "output_format": "png",
    "watermark": false
}'
```

### 单图生图

```bash
curl https://ark.cn-beijing.volces.com/api/v3/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ARK_API_KEY" \
  -d '{
    "model": "doubao-seedream-5-0-260128",
    "prompt": "将服装材质从银色金属改为透明清水",
    "image": "https://example.com/input.png",
    "size": "2K",
    "output_format": "png",
    "watermark": false
}'
```

### 多图融合

```bash
curl https://ark.cn-beijing.volces.com/api/v3/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ARK_API_KEY" \
  -d '{
    "model": "doubao-seedream-5-0-260128",
    "prompt": "将图1的服装换为图2的服装",
    "image": ["https://example.com/img1.png", "https://example.com/img2.png"],
    "sequential_image_generation": "disabled",
    "size": "2K",
    "output_format": "png",
    "watermark": false
}'
```

### 文生组图

```bash
curl https://ark.cn-beijing.volces.com/api/v3/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ARK_API_KEY" \
  -d '{
    "model": "doubao-seedream-5-0-260128",
    "prompt": "生成一组电影级科幻写实风的4张影视分镜...",
    "size": "2K",
    "sequential_image_generation": "auto",
    "sequential_image_generation_options": {
        "max_images": 4
    },
    "stream": false,
    "output_format": "png",
    "response_format": "url",
    "watermark": false
}'
```

### 联网搜索（仅 5.0 lite）

```bash
curl https://ark.cn-beijing.volces.com/api/v3/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ARK_API_KEY" \
  -d '{
    "model": "doubao-seedream-5-0-260128",
    "prompt": "制作一张上海未来5日的天气预报图",
    "size": "2048x2048",
    "tools": [{"type": "web_search"}],
    "output_format": "png",
    "response_format": "url",
    "watermark": false
}'
```

### 流式输出

设置 `"stream": true`，生成完任一图片后即返回结果。

## 响应格式

### 非流式（response_format: url）

```json
{
  "data": [
    {
      "url": "https://...",
      "index": 0
    }
  ],
  "usage": {
    "tool_usage": {
      "web_search": 0
    }
  }
}
```

### 非流式（response_format: b64_json）

```json
{
  "data": [
    {
      "b64_json": "...",
      "index": 0
    }
  ]
}
```
