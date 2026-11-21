"""Generate a cautious, source-grounded Hindi narration with Gemini Free Tier."""
import json
import os
import re
import time
import requests

API_ROOT = "https://generativelanguage.googleapis.com/v1beta"
MODEL = "gemini-2.5-flash"

def _gemini_segments(topic, fallback):
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        print("GEMINI_SKIPPED: GEMINI_API_KEY is not configured; using reviewed topic narration.")
        return fallback

    prompt = f"""
You write Hindi voiceover scripts for NUSKHALO, an Indian health-awareness channel.
Use ONLY the facts in this reviewed source brief. Do not add medical claims, diagnosis,
treatment advice, dosage, guaranteed benefits, or facts not present in the brief.
Topic: {topic.get('title', '')}
Category: {topic.get('category', '')}
Reviewed source summary: {topic.get('summary', '')}
Source domain: {topic.get('source_domain', '')}
Source URL: {topic.get('source_url', '')}
Existing safe narration (retain its meaning and all cautions): {json.dumps(fallback, ensure_ascii=False)}

Return valid JSON only, exactly this shape:
{{"segments":["...","...","...","..."]}}
Write natural, simple spoken Indian Hindi in Devanagari.
There must be exactly 4 segments, each about 20-25 Hindi words, for a total
voiceover target of about 40-48 seconds at a natural pace.
Segment 1: engaging question or hook.
Segment 2: explain the safe, source-supported information.
Segment 3: limitations and important caution, including any age-related warning.
Segment 4: when to seek professional help or a practical balanced takeaway.
Do not include headings, emojis, hashtags, English words, or claims beyond the source.
"""

    url = f"{API_ROOT}/models/{MODEL}:generateContent"
    for attempt in range(3):
        try:
            response = requests.post(
                url,
                params={"key": key},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": 0.35,
                        "responseMimeType": "application/json"
                    }
                },
                timeout=60
            )
            if response.status_code in (429, 500, 502, 503, 504):
                if attempt < 2:
                    wait = 12 * (attempt + 1)
                    print(f"GEMINI_TEMPORARY_HTTP_{response.status_code}; retrying in {wait}s")
                    time.sleep(wait)
                    continue
            response.raise_for_status()
            data = response.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            text = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", text)
            parsed = json.loads(text)
            segments = parsed.get("segments")
            if not isinstance(segments, list) or len(segments) != 4:
                raise ValueError("Gemini response must contain exactly four narration segments.")
            if not all(isinstance(x, str) and x.strip() for x in segments):
                raise ValueError("Gemini returned an empty narration segment.")
            print("GEMINI_SCRIPT_READY model=gemini-2.5-flash segments=4")
            return [x.strip() for x in segments]
        except Exception as exc:
            print(f"GEMINI_SCRIPT_WARNING: {type(exc).__name__}: {exc}")
            if attempt == 2:
                print("Using reviewed topic narration as safe fallback.")
                return fallback
            time.sleep(5 * (attempt + 1))
    return fallback

def build_script(topic, config):
    """Build a source-grounded Hindi wellness script; human review remains mandatory."""
    fallback = topic.get("narration") or []
    if len(fallback) != 4:
        raise ValueError("Each topic must contain exactly four reviewed narration segments.")
    segments = _gemini_segments(topic, fallback)
    return {
        "brand": config.get("brand", "NUSKHALO"),
        "language": "hi",
        "topic": topic["title"],
        "category": topic.get("category", "देसी सेहत"),
        "source_summary_original": topic.get("summary", ""),
        "source_domain": topic.get("source_domain", ""),
        "source_url": topic.get("source_url", ""),
        "narration_segments": segments,
        "sources": [topic.get("source_url", "")],
        "script_model": MODEL if os.getenv("GEMINI_API_KEY", "").strip() else "reviewed-topic-fallback",
        "review_status": "needs_human_review",
        "translation_required": False,
        "medical_safety_note": "Awareness only. No diagnosis, cure guarantee, medicine changes, or substitute for professional care."
    }
