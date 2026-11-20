"""Runway text-to-video integration for realistic, topic-specific NUSKHALO B-roll."""
import os
import re
import time
import subprocess
from pathlib import Path
import requests

BASE = "https://api.dev.runwayml.com/v1"
VERSION = "2024-11-06"

def _prompt(topic):
    title = re.sub(r"\s+", " ", str(topic.get("title", ""))).strip()
    summary = re.sub(r"\s+", " ", str(topic.get("summary", ""))).strip()
    context = (title + ". " + summary[:350]).strip()
    return (
        "Photorealistic premium television health-news documentary B-roll, vertical 9:16. "
        "Create a realistic cinematic shot inspired by this health-news topic: " + context + ". "
        "Show a believable modern hospital, clinic, laboratory, healthy food preparation or "
        "public-health setting relevant to the topic. Natural human activity, authentic skin "
        "texture, natural lighting, subtle professional camera movement, documentary realism. "
        "No text, captions, logos, watermarks, patient records, graphic surgery, blood, "
        "sensationalism or medical claims."
    )[:1000]

def generate_health_broll(topic, output_path, config):
    """Generate one paid portrait clip only when RUNWAYML_API_SECRET exists."""
    api_key = os.getenv("RUNWAYML_API_SECRET", "").strip()
    if not api_key:
        print("AI_VIDEO_SKIPPED: Add RUNWAYML_API_SECRET to GitHub Actions secrets; no charge made.")
        return False
    model = config.get("ai_video_model", "gen4.5")
    duration = int(config.get("ai_video_duration_seconds", 5))
    if not 2 <= duration <= 10:
        raise ValueError("ai_video_duration_seconds must be from 2 to 10.")
    headers = {"Authorization": f"Bearer {api_key}", "X-Runway-Version": VERSION,
               "Content-Type": "application/json"}
    payload = {"model": model, "promptText": _prompt(topic),
               "ratio": "720:1280", "duration": duration}
    print(f"AI_VIDEO_REQUEST model={model} duration={duration}s portrait=720:1280")
    response = requests.post(f"{BASE}/text_to_video", headers=headers,
                              json=payload, timeout=60)
    if response.status_code >= 400:
        raise RuntimeError(f"Runway create failed HTTP {response.status_code}: {response.text[:1500]}")
    task_id = response.json().get("id")
    if not task_id:
        raise RuntimeError(f"Runway response missing task id: {response.text[:1000]}")
    deadline = time.time() + int(config.get("ai_video_timeout_seconds", 900))
    while time.time() < deadline:
        time.sleep(5)
        poll = requests.get(f"{BASE}/tasks/{task_id}", headers=headers, timeout=45)
        if poll.status_code >= 400:
            raise RuntimeError(f"Runway poll failed HTTP {poll.status_code}: {poll.text[:1000]}")
        data = poll.json()
        status = data.get("status")
        print(f"AI_VIDEO_TASK status={status} estimatedCost={data.get('estimatedCost')}")
        if status == "SUCCEEDED":
            urls = data.get("output") or []
            if not urls:
                raise RuntimeError(f"Runway succeeded without output URL: {data}")
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with requests.get(urls[0], stream=True, timeout=120) as download:
                download.raise_for_status()
                with output_path.open("wb") as handle:
                    for chunk in download.iter_content(1024 * 1024):
                        if chunk:
                            handle.write(chunk)
            if output_path.stat().st_size < 30000:
                raise RuntimeError("AI video download is unexpectedly small.")
            print(f"AI_VIDEO_READY path={output_path} bytes={output_path.stat().st_size}")
            return True
        if status in ("FAILED", "CANCELED"):
            raise RuntimeError(f"Runway generation {status}: {data}")
    raise TimeoutError(f"Runway task {task_id} timed out.")

def composite_ai_broll(main_video, ai_video, duration=5):
    """Replace the opening visuals with AI B-roll while retaining the original voice track."""
    main_video, ai_video = Path(main_video), Path(ai_video)
    if not main_video.exists() or not ai_video.exists():
        raise FileNotFoundError("Main video or AI B-roll file is missing.")
    temp = main_video.with_name(main_video.stem + "_with_ai.mp4")
    vf = (
        "[1:v]scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,setsar=1[ai];"
        "[0:v][ai]overlay=0:0:enable='between(t,0," + str(duration) + ")',"
        "drawbox=x=55:y=65:w=970:h=180:color=black@0.55:t=fill:"
        "enable='between(t,0," + str(duration) + ")'[v]"
    )
    cmd = [
        "ffmpeg", "-y", "-i", str(main_video), "-stream_loop", "-1", "-i", str(ai_video),
        "-filter_complex", vf, "-map", "[v]", "-map", "0:a?",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
        "-c:a", "copy", "-shortest", "-movflags", "+faststart", str(temp)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError("AI B-roll composition failed: " + result.stderr[-2500:])
    if not temp.exists() or temp.stat().st_size < 50000:
        raise RuntimeError("AI B-roll composition produced an invalid MP4.")
    temp.replace(main_video)
    print(f"AI_BROLL_COMPOSITED: {main_video} ({main_video.stat().st_size} bytes)")
