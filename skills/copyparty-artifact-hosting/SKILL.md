---
name: copyparty-artifact-hosting
description: Use when an agent needs to upload locally available images, PDFs, Markdown reports, screenshots, generated charts, or other files to the Shujakuin Copyparty artifact host and return public Markdown-ready URLs; can compile Markdown to PDF/HTML before upload; replaces the old Chevereto image hosting workflow.
---

# Copyparty artifact hosting

Use this skill when you already have a local file and need to share it with the user through a public URL.

## What this skill does

- Uploads images, PDFs, Markdown reports, and other local artifacts to `https://files.wuhan.shujk.top:19856`.
- Reads Copyparty credentials from environment variables.
- Returns direct URLs, Markdown image embeds, and Markdown file links.
- Can publish Markdown by uploading the source and compiling PDF/HTML artifacts first.
- Replaces the old `chevereto-image-hosting` / `pic.shujk.top` workflow.

## Environment

Required:

- `COPYPARTY_BASE_URL` — default service URL, normally `https://files.wuhan.shujk.top:19856`
- `COPYPARTY_UPLOAD_USER` — normally `agent`
- `COPYPARTY_UPLOAD_PASSWORD` — upload key/password

Optional:

- `COPYPARTY_DEFAULT_DIR` — default upload prefix, default `agent`

If a required value is missing, report the missing variable and do not upload.

## Workflow

### Upload an existing artifact

1. Confirm the file exists locally.
2. Run `python3 scripts/upload_copyparty.py <file> ...` from this skill directory.
3. Use the returned URL in the response.
4. For images, prefer Markdown embedding: `![alt](https://...)`.
5. For PDFs or other files, prefer Markdown links: `[PDF](https://...)`.
6. Include the plain URL when the user may want to copy it.

### Publish a Markdown report

Use this when the user asks for a Markdown report, shareable notes, or a PDF rendered from Markdown.

1. Write the Markdown file locally.
2. Run `python3 scripts/publish_markdown.py <report.md>` from this skill directory.
3. The script uploads the Markdown source and tries to compile/upload PDF and HTML variants.
4. Return the PDF link first when available, then the Markdown source, then the HTML preview.

Markdown publishing behavior:

- Prefer PDF output via Pandoc + Typst.
- If `pandoc` is not available, use Pixi when available: `pixi exec -s pandoc -s typst ...`.
- If PDF compilation fails, still generate and upload standalone HTML when possible.
- Always upload the original `.md` source.
- Do not upload Markdown containing secrets or private logs.

## Rules

- Upload only files the user asked to share or files that are useful to show the result.
- Do not upload secrets, private config files, `.env`, Vault files, auth databases, or raw logs with credentials.
- Do not re-host files that are already public unless the user asks for a durable mirror.
- Keep alt text short and descriptive.
- If upload fails, briefly report the failure and use the best non-hosted fallback.

## Command examples

Single file:

```bash
python3 scripts/upload_copyparty.py path/to/image.png
```

Multiple files:

```bash
python3 scripts/upload_copyparty.py chart.png report.pdf notes.txt
```

Custom remote directory:

```bash
python3 scripts/upload_copyparty.py --dir reports/2026-05 chart.png report.pdf
```

Publish Markdown with PDF/HTML fallback:

```bash
python3 scripts/publish_markdown.py report.md
```

Publish Markdown into a fixed remote directory:

```bash
python3 scripts/publish_markdown.py --dir reports/2026-05/demo report.md
```
