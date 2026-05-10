#!/usr/bin/env python3
"""Publish Markdown source plus rendered PDF/HTML artifacts to Copyparty."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from upload_copyparty import env, safe_component, upload  # noqa: E402


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def run_command(cmd: list[str], cwd: Path) -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    except FileNotFoundError as exc:
        return False, str(exc)
    return proc.returncode == 0, proc.stdout[-4000:]


def pandoc_command(extra_args: list[str], prefer_pixi_for_pdf: bool = False) -> list[str] | None:
    if prefer_pixi_for_pdf and command_exists("pixi"):
        return ["pixi", "exec", "-s", "pandoc", "-s", "typst", "pandoc", *extra_args]
    if command_exists("pandoc"):
        return ["pandoc", *extra_args]
    if command_exists("pixi"):
        # Include typst as well so the same temporary env can render PDF if needed.
        return ["pixi", "exec", "-s", "pandoc", "-s", "typst", "pandoc", *extra_args]
    return None


def render_pdf(md_path: Path, out_path: Path) -> tuple[bool, str]:
    args = [str(md_path), "-o", str(out_path), "--pdf-engine=typst"]
    # Pixi gives deterministic availability of typst even when pandoc is already on PATH.
    cmd = pandoc_command(args, prefer_pixi_for_pdf=True)
    if not cmd:
        return False, "pandoc/pixi not available"
    ok, output = run_command(cmd, md_path.parent)
    if ok and out_path.exists() and out_path.stat().st_size > 0:
        return True, output
    return False, output or "PDF output was not created"


def render_html(md_path: Path, out_path: Path) -> tuple[bool, str]:
    cmd = pandoc_command([str(md_path), "-o", str(out_path), "--standalone"])
    if not cmd:
        return False, "pandoc/pixi not available"
    ok, output = run_command(cmd, md_path.parent)
    if ok and out_path.exists() and out_path.stat().st_size > 0:
        return True, output
    return False, output or "HTML output was not created"


def markdown_link(label: str, url: str) -> str:
    return f"[{label}]({url})"


def upload_artifact(path: Path, remote_dir: str, base_url: str, user: str, password: str) -> str:
    remote_path = f"{remote_dir.rstrip('/')}/{safe_component(path.name)}"
    return upload(path, remote_path, base_url, user, password)


def publish_one(md_path: Path, args: argparse.Namespace, base_url: str, user: str, password: str, base_dir: str) -> int:
    if not md_path.is_file():
        print(f"not a file: {md_path}", file=sys.stderr)
        return 1
    if md_path.suffix.lower() not in {".md", ".markdown"}:
        print(f"not a markdown file: {md_path}", file=sys.stderr)
        return 1

    stamp = time.strftime("%Y%m%d-%H%M%S")
    stem = safe_component(md_path.stem)
    remote_dir = args.remote_dir.strip("/") if args.remote_dir else f"{base_dir.strip('/')}/markdown/{stem}-{stamp}"

    artifacts: list[tuple[str, Path]] = [("Markdown source", md_path)]
    with tempfile.TemporaryDirectory(prefix="copyparty-md-") as tmp_raw:
        tmp = Path(tmp_raw)
        pdf_path = tmp / f"{stem}.pdf"
        html_path = tmp / f"{stem}.html"

        pdf_ok, pdf_log = (False, "disabled")
        if not args.no_pdf:
            pdf_ok, pdf_log = render_pdf(md_path, pdf_path)
            if pdf_ok:
                artifacts.append(("PDF", pdf_path))

        html_ok, html_log = (False, "disabled")
        if args.html or not pdf_ok:
            html_ok, html_log = render_html(md_path, html_path)
            if html_ok:
                artifacts.append(("HTML preview", html_path))

        print(f"file: {md_path}")
        print(f"remote_dir: {remote_dir}")
        print(f"pdf: {'ok' if pdf_ok else 'skipped/failed'}")
        if not pdf_ok and pdf_log:
            print(f"pdf_log: {pdf_log.strip().splitlines()[-1] if pdf_log.strip() else pdf_log}")
        print(f"html: {'ok' if html_ok else 'skipped/failed'}")
        if not html_ok and html_log and (args.html or not pdf_ok):
            print(f"html_log: {html_log.strip().splitlines()[-1] if html_log.strip() else html_log}")

        uploaded: list[tuple[str, str]] = []
        for label, path in artifacts:
            url = upload_artifact(path, remote_dir, base_url, user, password)
            uploaded.append((label, url))

        print("links:")
        label_priority = {"PDF": 0, "Markdown source": 1, "HTML preview": 2}
        for label, url in sorted(uploaded, key=lambda item: label_priority.get(item[0], 99)):
            print(f"- {label}: {url}")
            print(f"  markdown: {markdown_link(label, url)}")
        print()
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Publish Markdown as source plus PDF/HTML artifacts to Copyparty")
    parser.add_argument("paths", nargs="+", help="Markdown files to publish")
    parser.add_argument("--dir", dest="remote_dir", help="remote directory prefix")
    parser.add_argument("--html", action="store_true", help="also generate HTML even if PDF succeeds")
    parser.add_argument("--no-pdf", action="store_true", help="skip PDF generation")
    args = parser.parse_args(argv)

    base_url = env("COPYPARTY_BASE_URL", "https://files.wuhan.shujk.top:19856")
    user = env("COPYPARTY_UPLOAD_USER", "agent")
    password = env("COPYPARTY_UPLOAD_PASSWORD")
    base_dir = os.environ.get("COPYPARTY_DEFAULT_DIR", "agent")

    rc = 0
    for raw in args.paths:
        rc = publish_one(Path(raw).expanduser().resolve(), args, base_url, user, password, base_dir) or rc
    return rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
