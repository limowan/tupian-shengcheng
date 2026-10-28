import argparse
import base64
import json
import mimetypes
import os
import re
import sys
import time
from pathlib import Path
import urllib.error
import urllib.request

try:
    import requests
except ImportError:
    requests = None

FLOW2API_BASE_URL = "https://flow2api.uniky.net/v1/chat/completions"
FLOW2API_MODEL = "gemini-3.1-flash-image-landscape"
LEGACY_BASE_URL = "https://llm.devoi.net/v1/chat/completions"
LEGACY_MODEL = "gemini-3-pro-image-preview"
OPENAI_IMAGES_BASE_URL = "https://cf.ai-pixel.online"
OPENAI_IMAGES_MODEL = "gpt-image-2"
VOLCENGINE_BASE_URL = "https://ark.cn-beijing.volces.com/api/plan/v3/images/generations"
VOLCENGINE_MODEL = "doubao-seedream-5.0-lite"
DEFAULT_PROFILE = "ai_pixel"
DEFAULT_REQUEST_MODE = "openai_images"
ENV_API_KEYS = ("IMAGE_API_KEY", "FLOW2API_API_KEY", "OPENAI_API_KEY", "DEVOI_API_KEY")
ENV_BASE_URLS = ("IMAGE_API_BASE_URL", "FLOW2API_BASE_URL")
ENV_MODELS = ("IMAGE_MODEL", "FLOW2API_MODEL")
ENV_PROFILE = "IMAGE_PROFILE"
ENV_REQUEST_MODE = "IMAGE_REQUEST_MODE"


class UrllibResponse:
    def __init__(self, status_code: int, headers, content: bytes):
        self.status_code = status_code
        self.headers = headers
        self.content = content
        self.text = content.decode("utf-8", errors="replace")

    def json(self):
        return json.loads(self.text)

    def iter_lines(self, decode_unicode=False):
        for line in self.content.splitlines():
            if decode_unicode:
                yield line.decode("utf-8", errors="replace")
            else:
                yield line

    def iter_content(self, chunk_size=8192):
        for idx in range(0, len(self.content), chunk_size):
            yield self.content[idx : idx + chunk_size]


def http_post(url: str, headers: dict, payload: dict, stream: bool, timeout: int):
    if requests is not None:
        return requests.post(url, headers=headers, json=payload, stream=stream, timeout=timeout)

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return UrllibResponse(resp.status, resp.headers, resp.read())
    except urllib.error.HTTPError as exc:
        return UrllibResponse(exc.code, exc.headers, exc.read())


def http_get(url: str, timeout: int):
    if requests is not None:
        return requests.get(url, stream=True, timeout=timeout)

    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return UrllibResponse(resp.status, resp.headers, resp.read())
    except urllib.error.HTTPError as exc:
        return UrllibResponse(exc.code, exc.headers, exc.read())


def encode_multipart_form(fields: dict, files: list[tuple[str, Path]]) -> tuple[bytes, str]:
    boundary = f"----tupian-shengcheng-{int(time.time() * 1000)}"
    body = bytearray()

    for name, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        body.extend(str(value).encode("utf-8"))
        body.extend(b"\r\n")

    for name, path in files:
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(
            f'Content-Disposition: form-data; name="{name}"; filename="{path.name}"\r\n'.encode(
                "utf-8"
            )
        )
        body.extend(f"Content-Type: {mime}\r\n\r\n".encode("utf-8"))
        body.extend(path.read_bytes())
        body.extend(b"\r\n")

    body.extend(f"--{boundary}--\r\n".encode("utf-8"))
    return bytes(body), boundary


def http_multipart_post(
    url: str,
    headers: dict,
    fields: dict,
    files: list[tuple[str, Path]],
    timeout: int,
):
    if requests is not None:
        opened = []
        try:
            upload_files = []
            for name, path in files:
                handle = open(path, "rb")
                opened.append(handle)
                mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
                upload_files.append((name, (path.name, handle, mime)))
            return requests.post(
                url,
                headers=headers,
                data=fields,
                files=upload_files,
                timeout=timeout,
            )
        finally:
            for handle in opened:
                handle.close()

    body, boundary = encode_multipart_form(fields, files)
    request_headers = dict(headers)
    request_headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    req = urllib.request.Request(url, data=body, headers=request_headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return UrllibResponse(resp.status, resp.headers, resp.read())
    except urllib.error.HTTPError as exc:
        return UrllibResponse(exc.code, exc.headers, exc.read())


def load_config(config_path: Path) -> dict:
    if not config_path.exists():
        return {}
    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def first_env(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return None


def default_base_url_for_mode(request_mode: str) -> str:
    if request_mode == "old":
        return LEGACY_BASE_URL
    if request_mode == "openai_images":
        return OPENAI_IMAGES_BASE_URL
    if request_mode == "volcengine":
        return VOLCENGINE_BASE_URL
    return FLOW2API_BASE_URL


def default_model_for_mode(request_mode: str) -> str:
    if request_mode == "old":
        return LEGACY_MODEL
    if request_mode == "openai_images":
        return OPENAI_IMAGES_MODEL
    if request_mode == "volcengine":
        return VOLCENGINE_MODEL
    return FLOW2API_MODEL


def normalize_openai_images_url(base_url: str) -> str:
    base_url = base_url.rstrip("/")
    if base_url.endswith("/v1/images/generations"):
        return base_url
    if base_url.endswith("/v1"):
        return f"{base_url}/images/generations"
    return f"{base_url}/v1/images/generations"


def normalize_openai_edits_url(base_url: str) -> str:
    base_url = base_url.rstrip("/")
    if base_url.endswith("/v1/images/edits"):
        return base_url
    if base_url.endswith("/v1/images/generations"):
        return base_url[: -len("/generations")] + "/edits"
    if base_url.endswith("/v1"):
        return f"{base_url}/images/edits"
    return f"{base_url}/v1/images/edits"


def extract_image_url(text: str) -> str | None:
    if not text:
        return None
    text = text.strip()
    if text.startswith("data:image/"):
        return text
    match = re.search(r"!\[[^\]]*\]\(([^)]+)\)", text)
    if match:
        return match.group(1).strip()
    urls = re.findall(r"https?://\S+", text)
    for url in urls:
        if re.search(r"\.(png|jpe?g|webp|gif)(\?|$)", url, re.IGNORECASE):
            return url.strip()
    return urls[0].strip() if urls else None


def infer_ext_from_url(url: str) -> str:
    if url.startswith("data:image/"):
        match = re.match(r"data:image/([^;]+);base64,", url, re.IGNORECASE)
        if match:
            ext = match.group(1).lower()
            if ext == "jpeg":
                return ".jpg"
            return "." + ext
    for ext in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
        if re.search(re.escape(ext) + r"(\?|$)", url, re.IGNORECASE):
            return ext
    return ".png"


def infer_ext_from_content_type(content_type: str) -> str:
    content_type = (content_type or "").split(";", 1)[0].strip().lower()
    mapping = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }
    return mapping.get(content_type, ".png")


def extract_image_ref(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return extract_image_url(value)
    if isinstance(value, list):
        for item in value:
            found = extract_image_ref(item)
            if found:
                return found
        return None
    if not isinstance(value, dict):
        return None

    for key in ("b64_json", "base64"):
        raw = value.get(key)
        if isinstance(raw, str) and raw.strip():
            cleaned = re.sub(r"\s+", "", raw)
            return f"data:image/png;base64,{cleaned}"

    for key in ("image_url", "url", "image", "image_uri"):
        found = extract_image_ref(value.get(key))
        if found:
            return found

    for key in ("data", "images", "output", "result", "message", "choices", "content"):
        found = extract_image_ref(value.get(key))
        if found:
            return found

    text = value.get("text")
    if isinstance(text, str):
        return extract_image_url(text)
    return None


def extract_text_fragments(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        fragments = []
        for item in value:
            fragments.extend(extract_text_fragments(item))
        return fragments
    if not isinstance(value, dict):
        return []

    fragments = []
    for key in ("text", "content"):
        if key in value:
            fragments.extend(extract_text_fragments(value.get(key)))

    for key in ("image_url", "url", "b64_json", "base64"):
        if key in value:
            image_ref = extract_image_ref({key: value.get(key)})
            if image_ref:
                fragments.append(image_ref)
                break
    return fragments


def parse_streaming_response_legacy(resp) -> str:
    content = ""
    for line in resp.iter_lines(decode_unicode=True):
        if not line:
            continue
        if line.startswith("data:"):
            data = line[len("data:") :].strip()
            if data == "[DONE]":
                break
            try:
                obj = json.loads(data)
            except Exception:
                continue
            choices = obj.get("choices") or []
            if not choices:
                continue
            delta = choices[0].get("delta") or {}
            piece = delta.get("content")
            if piece:
                content += piece
    return content


def parse_streaming_response_compatible(resp) -> str:
    content = ""
    for line in resp.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data:"):
            continue
        data = line[len("data:") :].strip()
        if data == "[DONE]":
            break
        try:
            obj = json.loads(data)
        except Exception:
            continue
        choices = obj.get("choices") or []
        if not choices:
            continue
        delta = choices[0].get("delta") or {}
        piece = delta.get("content")
        if isinstance(piece, str):
            content += piece
            continue
        parts = extract_text_fragments(piece)
        if parts:
            content += "\n".join(parts)
    return content


def request_image_legacy(
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    stream: bool,
    timeout: int,
) -> tuple[str, str | bytes, str | None]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 tupian-shengcheng/1.0",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": stream,
    }
    resp = http_post(base_url, headers, payload, stream, timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"API error {resp.status_code}: {resp.text[:500]}")

    if stream:
        text = parse_streaming_response_legacy(resp)
    else:
        data = resp.json()
        choices = data.get("choices") or []
        if not choices:
            text = ""
        else:
            msg = choices[0].get("message") or {}
            text = msg.get("content") or ""

    image_url = extract_image_url(text)
    if image_url:
        return ("image_ref", image_url, infer_ext_from_url(image_url))
    return ("text", text, None)


def request_image_compatible(
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    stream: bool,
    timeout: int,
) -> tuple[str, str | bytes, str | None]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 tupian-shengcheng/1.0",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": stream,
    }
    resp = http_post(base_url, headers, payload, stream, timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"API error {resp.status_code}: {resp.text[:500]}")

    content_type = (resp.headers.get("Content-Type") or "").lower()
    if content_type.startswith("image/"):
        return ("binary", resp.content, infer_ext_from_content_type(content_type))

    if stream:
        text = parse_streaming_response_compatible(resp)
        image_ref = extract_image_ref(text)
        if image_ref:
            return ("image_ref", image_ref, infer_ext_from_url(image_ref))
        return ("text", text, None)

    try:
        data = resp.json()
    except ValueError:
        text = resp.text
        image_ref = extract_image_ref(text)
        if image_ref:
            return ("image_ref", image_ref, infer_ext_from_url(image_ref))
        return ("text", text, None)

    image_ref = extract_image_ref(data)
    if image_ref:
        return ("image_ref", image_ref, infer_ext_from_url(image_ref))

    choices = data.get("choices") or []
    if choices:
        msg = choices[0].get("message") or {}
        text = "\n".join(extract_text_fragments(msg.get("content"))).strip()
        return ("text", text, None)
    return ("text", json.dumps(data, ensure_ascii=False), None)


def request_image_openai_images(
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    size: str,
    quality: str,
    n: int,
    timeout: int,
) -> tuple[str, str | bytes, str | None]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 tupian-shengcheng/1.0",
    }
    payload = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "quality": quality,
        "n": n,
    }
    endpoint = normalize_openai_images_url(base_url)
    resp = http_post(endpoint, headers, payload, False, timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"API error {resp.status_code}: {resp.text[:500]}")

    content_type = (resp.headers.get("Content-Type") or "").lower()
    if content_type.startswith("image/"):
        return ("binary", resp.content, infer_ext_from_content_type(content_type))

    try:
        data = resp.json()
    except ValueError:
        text = resp.text
        image_ref = extract_image_ref(text)
        if image_ref:
            return ("image_ref", image_ref, infer_ext_from_url(image_ref))
        return ("text", text, None)

    image_ref = extract_image_ref(data)
    if image_ref:
        return ("image_ref", image_ref, infer_ext_from_url(image_ref))
    return ("text", json.dumps(data, ensure_ascii=False), None)


def request_image_openai_edit(
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    image_path: Path,
    size: str,
    quality: str,
    n: int,
    timeout: int,
) -> tuple[str, str | bytes, str | None]:
    if not image_path.exists():
        raise RuntimeError(f"Edit image not found: {image_path}")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "Mozilla/5.0 tupian-shengcheng/1.0",
    }
    fields = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "quality": quality,
        "n": str(n),
    }
    endpoint = normalize_openai_edits_url(base_url)
    resp = http_multipart_post(endpoint, headers, fields, [("image", image_path)], timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"API error {resp.status_code}: {resp.text[:500]}")

    content_type = (resp.headers.get("Content-Type") or "").lower()
    if content_type.startswith("image/"):
        return ("binary", resp.content, infer_ext_from_content_type(content_type))

    try:
        data = resp.json()
    except ValueError:
        text = resp.text
        image_ref = extract_image_ref(text)
        if image_ref:
            return ("image_ref", image_ref, infer_ext_from_url(image_ref))
        return ("text", text, None)

    image_ref = extract_image_ref(data)
    if image_ref:
        return ("image_ref", image_ref, infer_ext_from_url(image_ref))
    return ("text", json.dumps(data, ensure_ascii=False), None)


def request_image_volcengine(
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    size: str,
    timeout: int,
    image: str | list[str] | None = None,
    output_format: str = "png",
    response_format: str | None = None,
    sequential: str | None = None,
    max_images: int | None = None,
    stream: bool = False,
) -> tuple[str, str | bytes, str | None]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 tupian-shengcheng/1.0",
    }
    payload: dict = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "output_format": output_format,
        "watermark": False,
    }
    if image:
        payload["image"] = image
    if response_format:
        payload["response_format"] = response_format
    if sequential:
        payload["sequential_image_generation"] = sequential
        if max_images:
            payload["sequential_image_generation_options"] = {"max_images": max_images}
    if stream:
        payload["stream"] = True

    resp = http_post(base_url, headers, payload, False, timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"API error {resp.status_code}: {resp.text[:500]}")

    content_type = (resp.headers.get("Content-Type") or "").lower()
    if content_type.startswith("image/"):
        return ("binary", resp.content, infer_ext_from_content_type(content_type))

    try:
        data = resp.json()
    except ValueError:
        text = resp.text
        image_ref = extract_image_ref(text)
        if image_ref:
            return ("image_ref", image_ref, infer_ext_from_url(image_ref))
        return ("text", text, None)

    image_ref = extract_image_ref(data)
    if image_ref:
        return ("image_ref", image_ref, infer_ext_from_url(image_ref))
    return ("text", json.dumps(data, ensure_ascii=False), None)


def download_image(url: str, out_path: Path, timeout: int) -> None:
    if url.startswith("data:image/"):
        match = re.match(r"data:image/[^;]+;base64,(.*)", url, re.IGNORECASE | re.DOTALL)
        if not match:
            raise RuntimeError("Invalid data URI for image")
        data = base64.b64decode(match.group(1))
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "wb") as handle:
            handle.write(data)
        return

    resp = http_get(url, timeout)
    if resp.status_code != 200:
        raise RuntimeError(f"Image download failed {resp.status_code}: {url}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as handle:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                handle.write(chunk)


def save_binary_image(data: bytes, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as handle:
        handle.write(data)


def resolve_output_path(out: str | None, ext: str) -> Path:
    ts = int(time.time())
    if not out:
        return Path.cwd() / f"image_{ts}{ext}"

    out_path = Path(out)
    if out_path.is_dir() or str(out).endswith(("\\", "/")):
        return out_path / f"image_{ts}{ext}"
    if not out_path.suffix:
        return out_path.with_suffix(ext)
    return out_path


def get_profile_config(config: dict, profile_name: str) -> dict:
    profiles = config.get("profiles")
    if isinstance(profiles, dict):
        profile = profiles.get(profile_name)
        if isinstance(profile, dict):
            return profile
    return {}


def resolve_runtime_settings(args, config: dict) -> tuple[str, str, str, str]:
    active_profile = args.profile or os.getenv(ENV_PROFILE) or config.get("active_profile") or DEFAULT_PROFILE
    profile_config = get_profile_config(config, active_profile)
    request_mode = (
        args.request_mode
        or os.getenv(ENV_REQUEST_MODE)
        or profile_config.get("request_mode")
        or config.get("request_mode")
        or DEFAULT_REQUEST_MODE
    )

    if request_mode not in ("old", "new", "openai_images", "volcengine"):
        raise RuntimeError(f"Unsupported request mode: {request_mode}")

    base_url = (
        args.base_url
        or first_env(*ENV_BASE_URLS)
        or profile_config.get("base_url")
        or config.get("base_url")
        or default_base_url_for_mode(request_mode)
    )
    model = (
        args.model
        or first_env(*ENV_MODELS)
        or profile_config.get("model")
        or config.get("model")
        or default_model_for_mode(request_mode)
    )
    api_key = args.api_key or first_env(*ENV_API_KEYS) or profile_config.get("api_key") or config.get("api_key")
    return active_profile, request_mode, base_url, model, api_key


def main() -> int:
    parser = argparse.ArgumentParser(description="OpenAI-compatible image generation")
    parser.add_argument("--prompt", help="Prompt text for image generation")
    parser.add_argument("--prompt-file", help="Read prompt from file")
    parser.add_argument("--profile", default=None, help="Profile name from config.json")
    parser.add_argument("--request-mode", default=None, help="Request mode: new, old, or openai_images")
    parser.add_argument("--base-url", default=None, help="API base URL or full endpoint URL")
    parser.add_argument("--model", default=None, help="Model name")
    parser.add_argument("--api-key", default=None, help="API key (overrides env/config)")
    parser.add_argument("--out", default=None, help="Output file path or directory")
    parser.add_argument("--timeout", type=int, default=600, help="Request timeout seconds")
    parser.add_argument("--no-stream", action="store_true", help="Disable streaming")
    parser.add_argument("--size", default="auto", help="Image size for openai_images mode")
    parser.add_argument("--quality", default="medium", help="Image quality for openai_images mode")
    parser.add_argument("--n", type=int, default=1, help="Number of images for openai_images mode")
    parser.add_argument("--edit-image", default=None, help="Source image path for openai_images edit mode")
    parser.add_argument("--image", default=None, help="Reference image URL(s) for volcengine mode, comma-separated for multiple")
    parser.add_argument("--output-format", default="png", help="Output image format: png or jpeg (volcengine)")
    parser.add_argument("--response-format", default=None, help="Response format: url or b64_json (volcengine)")
    parser.add_argument("--sequential", default=None, help="Sequential image generation: auto or disabled (volcengine)")
    parser.add_argument("--max-images", type=int, default=None, help="Max images for sequential generation (volcengine)")
    args = parser.parse_args()

    if not args.prompt and not args.prompt_file:
        print("Provide --prompt or --prompt-file", file=sys.stderr)
        return 2

    prompt = args.prompt or ""
    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text(encoding="utf-8")

    skill_dir = Path(__file__).resolve().parents[1]
    config = load_config(skill_dir / "config.json")

    active_profile, request_mode, base_url, model, api_key = resolve_runtime_settings(args, config)
    profile_config = get_profile_config(config, active_profile)
    if not api_key:
        print(
            "Missing API key. Set --api-key or IMAGE_API_KEY / FLOW2API_API_KEY / OPENAI_API_KEY / DEVOI_API_KEY or config.json",
            file=sys.stderr,
        )
        return 2

    if request_mode == "openai_images":
        if args.edit_image:
            result_type, payload, ext = request_image_openai_edit(
                base_url,
                api_key,
                model,
                prompt,
                Path(args.edit_image),
                args.size,
                args.quality,
                args.n,
                args.timeout,
            )
        else:
            result_type, payload, ext = request_image_openai_images(
                base_url,
                api_key,
                model,
                prompt,
                args.size,
                args.quality,
                args.n,
                args.timeout,
            )
    elif request_mode == "volcengine":
        vol_image = None
        if args.image:
            parts = [p.strip() for p in args.image.split(",")]
            resolved = []
            for p in parts:
                img_path = Path(p)
                if img_path.exists():
                    img_bytes = img_path.read_bytes()
                    ext_name = img_path.suffix.lstrip(".").lower()
                    if ext_name == "jpg":
                        ext_name = "jpeg"
                    resolved.append(f"data:image/{ext_name};base64,{base64.b64encode(img_bytes).decode()}")
                else:
                    resolved.append(p)
            vol_image = resolved if len(resolved) > 1 else resolved[0]
        vol_size = args.size
        if vol_size == "1024x1024":
            vol_size = profile_config.get("default_size") or "4K"
        result_type, payload, ext = request_image_volcengine(
            base_url,
            api_key,
            model,
            prompt,
            vol_size,
            args.timeout,
            image=vol_image,
            output_format=args.output_format,
            response_format=args.response_format,
            sequential=args.sequential,
            max_images=args.max_images,
        )
    else:
        requester = request_image_legacy if request_mode == "old" else request_image_compatible
        result_type, payload, ext = requester(base_url, api_key, model, prompt, not args.no_stream, args.timeout)
    out_path = resolve_output_path(args.out, ext or ".png")

    if result_type == "binary":
        save_binary_image(payload, out_path)
        print(str(out_path))
        return 0

    if result_type == "image_ref":
        download_image(str(payload), out_path, args.timeout)
        print(str(out_path))
        return 0

    text = str(payload).strip()
    if not text:
        raise RuntimeError(f"Empty response content from profile '{active_profile}'")
    raise RuntimeError(f"No image found in response: {text[:500]}")


if __name__ == "__main__":
    raise SystemExit(main())
