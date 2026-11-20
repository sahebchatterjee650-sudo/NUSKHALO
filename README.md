# NUSKHALO Automation

Hindi-first, seasonal health-awareness Shorts/Reels workflow.

## Important
This is a starter scaffold, not a live publishing system. Uploading is disabled until platform credentials are configured and tested. Health claims must be evidence-checked; never present home remedies as guaranteed cures or advise stopping prescribed treatment.

## Initial workflow
1. Collect candidate topics from configured public RSS feeds.
2. Generate or edit a Hindi script (AI provider is optional and deliberately not wired to a paid API).
3. Review the script and sources.
4. Render a vertical video from licensed clips/assets with FFmpeg.
5. Review the output.
6. Enable YouTube/Meta publishing only after credentials and platform permissions are configured.

## Local setup
- Python 3.11+
- FFmpeg installed and available on PATH

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env
python main.py
```

Place only licensed/owned video clips in `assets/clips/`. The renderer uses multiple clips, motion/crop, captions and audio where supplied. It does not turn a single still image into a fake medical demonstration.

## GitHub Actions
The workflow runs a dry-run build. GitHub-hosted runners have time/storage limits; this is not guaranteed always-on compute. Do not add API keys to source files. Use repository Secrets.

## Publishing
- YouTube: requires OAuth consent and YouTube Data API setup.
- Facebook/Instagram: requires Meta app setup, eligible Page/Instagram professional account, permissions and access tokens.
- Upload functions are intentionally placeholders until you provide and verify those account settings.
