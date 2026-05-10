---
name: copyparty-artifact-hosting
description: Use when an agent needs to upload locally available images, PDFs, screenshots, reports, generated charts, or other files to the Shujakuin Copyparty artifact host and return public Markdown-ready URLs; replaces the old Chevereto image hosting workflow.
---

# Copyparty artifact hosting

Use this skill when you already have a local file and need to share it with the user through a public URL.

## What this skill does

- Uploads images, PDFs, and other local artifacts to `https://files.wuhan.shujk.top:19856`.
- Reads Copyparty credentials from environment variables.
- Returns direct URLs, Markdown image embeds, and Markdown file links.
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

1. Confirm the file exists locally.
2. Run `python3 scripts/upload_copyparty.py <file> ...` from this skill directory.
3. Use the returned URL in the response.
4. For images, prefer Markdown embedding: `![alt](https://...)`.
5. For PDFs or other files, prefer Markdown links: `[PDF](https://...)`.
6. Include the plain URL when the user may want to copy it.

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
