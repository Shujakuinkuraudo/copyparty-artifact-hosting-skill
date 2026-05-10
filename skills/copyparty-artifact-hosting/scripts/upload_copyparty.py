#!/usr/bin/env python3
"""Upload files to the Shujakuin Copyparty artifact host."""
from __future__ import annotations

import argparse
import mimetypes
import os
import re
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urljoin
from urllib.request import Request, build_opener
from base64 import b64encode

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".avif"}
PDF_EXTS = {".pdf"}


def env(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if not value:
        raise SystemExit(f"missing required environment variable: {name}")
    return value


def safe_component(value: str) -> str:
    value = Path(value).name.strip().replace(" ", "-")
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip(".-")
    return value or "artifact"


def classify(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in IMAGE_EXTS:
        return "images"
    if ext in PDF_EXTS:
        return "pdf"
    return "files"


def build_remote_path(path: Path, base_dir: str, force_dir: str | None, unique: bool) -> str:
    prefix = force_dir.strip("/") if force_dir else f"{base_dir.strip('/')}/{classify(path)}"
    stem = safe_component(path.stem)
    suffix = safe_component(path.suffix) if path.suffix else ""
    if suffix and not suffix.startswith("."):
        suffix = "." + suffix
    if unique:
        stamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"{stem}-{stamp}{suffix}"
    else:
        filename = f"{stem}{suffix}"
    return "/".join(part for part in [prefix, filename] if part)


def upload(path: Path, remote_path: str, base_url: str, user: str, password: str) -> str:
    target = urljoin(base_url.rstrip("/") + "/", quote(remote_path, safe="/._-"))
    data = path.read_bytes()
    ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    req = Request(target, data=data, method="PUT")
    req.add_header("Content-Type", ctype)
    req.add_header("Content-Length", str(len(data)))
    token = b64encode(f"{user}:{password}".encode()).decode()
    req.add_header("Authorization", f"Basic {token}")
    opener = build_opener()
    try:
        with opener.open(req, timeout=120) as resp:
            if resp.status >= 400:
                raise SystemExit(f"upload failed for {path}: HTTP {resp.status}")
    except HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:500]
        raise SystemExit(f"upload failed for {path}: HTTP {exc.code} {detail}") from exc
    except URLError as exc:
        raise SystemExit(f"upload failed for {path}: {exc}") from exc
    return target


def markdown_for(path: Path, url: str) -> str:
    name = path.name
    if path.suffix.lower() in IMAGE_EXTS:
        return f"![{name}]({url})"
    label = "PDF" if path.suffix.lower() in PDF_EXTS else name
    return f"[{label}]({url})"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Upload artifacts to Copyparty")
    parser.add_argument("paths", nargs="+", help="files to upload")
    parser.add_argument("--dir", dest="remote_dir", help="remote directory prefix")
    parser.add_argument("--no-unique", action="store_true", help="do not append a timestamp")
    args = parser.parse_args(argv)

    base_url = env("COPYPARTY_BASE_URL", "https://files.wuhan.shujk.top:19856")
    user = env("COPYPARTY_UPLOAD_USER", "agent")
    password = env("COPYPARTY_UPLOAD_PASSWORD")
    base_dir = os.environ.get("COPYPARTY_DEFAULT_DIR", "agent")

    for raw in args.paths:
        path = Path(raw).expanduser().resolve()
        if not path.is_file():
            raise SystemExit(f"not a file: {path}")
        remote_path = build_remote_path(path, base_dir, args.remote_dir, not args.no_unique)
        url = upload(path, remote_path, base_url, user, password)
        print(f"file: {path}")
        print(f"url: {url}")
        print(f"markdown: {markdown_for(path, url)}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
