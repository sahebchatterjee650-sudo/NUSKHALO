# NUSKHALO — Desi Health & Wellness Shorts

Hindi-first Indian channel about practical home-care awareness, seasonal foods, healthy Indian recipes, food safety and everyday wellness.

Tagline: **सेहत का देसी ज्ञान, हर दिन आसान उपाय!**

## Daily workflow
- Creates 5 vertical 1080x1920 Hindi Shorts drafts per scheduled run.
- Uses a curated evergreen topic bank with source links (WHO, NHS, NIH/NCCIH).
- Uses Hindi TTS (Edge TTS, hi-IN-MadhurNeural) and animated motion-graphic scenes.
- Saves one script JSON per video plus a daily manifest.
- Publishing is disabled. Human review is required before any upload.

## Health safety
- Home remedies are not described as guaranteed cures.
- No diagnosis, medication changes, or advice to stop prescribed treatment.
- Evidence limitations and important cautions are included in scripts.
- Verify each script and source before publishing. This is general awareness, not medical advice.

## GitHub Actions
Runs daily at 08:30 IST and can be started manually. Artifacts contain MP4 drafts, scripts, and logs. The current build uses no paid video-generation API and does not need an API key.

## Limitations
The current renderer creates motion-graphic scenes with Hindi narration; it does not yet create full cinematic AI footage. TTS/network availability and GitHub runner limits can affect a run.
