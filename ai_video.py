"""Free-tier Agnes AI video generation for NUSKHALO (subject to provider promotion/limits)."""
import os
import re
import time
import subprocess
from pathlib import Path
from urllib.parse import urlparse
import requests

API_ROOT = "https://apihub.agnes-ai.com"
MODEL = "agnes-video-2.5-flash"

def _prompt(topic):
    title = re.sub(r"\s+", " ", str(topic.get("title", ""))).strip()
    summary = re.sub(r"\s+", " ", str(topic.get("summary", ""))).strip()
    context = (title + ". " + summary[:300]).strip()
    return (
        "Vertical 9:16 photorealistic health-news documentary B-roll, 720p, "
        "five seconds, realistic human movement and subtle cinematic camera motion. "
        "Scene should visually illustrate this health news topic: " + context + ". "
        "Use a credible modern clinic, hospital, laboratory, public-health or nutrition "
        "setting as relevant. Natural lighting, realistic people, professional documentary "
        "footage. No text, no subtitles, no logos, no watermark, no readable patient data, "
        "no graphic surgery, no blood, no medical claims."
    )[:1800]

def _request(method, path, key, **kwargs):
    headers = kwargs.pop("headers", {})
    headers.update({"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    response = requests.request(method, API_ROOT + path, headers=headers, timeout=90, **kwargs)
    if response.status_code >= 400:
        raise RuntimeError(f"Agnes API HTTP {response.status_code}: {response.text[:1800]}")
    return response.json()

def generate_health_broll(topic, output_path, config):
    """Returns False when no free API key is configured; never falls back to paid API."""
    key = os.getenv("AGNES_API_KEY", "").strip()
    if not key:
        print("AI_VIDEO_SKIPPED: Set AGNES_API_KEY GitHub Actions secret; no paid provider called.")
        return False
    seconds = int(config.get("ai_video_duration_seconds", 5))
    if not 4 <= seconds <= 12:
        raise ValueError("Agnes video duration must be 4–12 seconds.")
    payload = {
        "model": MODEL,
        "prompt": _prompt(topic),
        "height": 1280,
        "width": 720,
        "num_frames": seconds * 24,
        "frame_rate": 24,
    }
    print(f"AI_VIDEO_REQUEST provider=Agnes model={MODEL} seconds={seconds} resolution=720x1280")
    created = _request("POST", "/v1/videos", key, json=payload)
    video_id = created.get("video_id") or created.get("id")
    if not video_id:
        raise RuntimeError(f"Agnes create response missing video_id: {created}")
    deadline = time.time() + int(config.get("ai_video_timeout_seconds", 900))
    while time.time() < deadline:
        data = _request("GET", "/agnesapi", key, params={"video_id": video_id, "model_name": MODEL})
        status = str(data.get("status", "")).lower()
        print(f"AI_VIDEO_TASK status={status}")
        if status in {"completed", "succeeded", "success", "done"}:
            url = data.get("url") or data.get("video_url")
            if not url:
                raise RuntimeError(f"Agnes completed without a video URL: {data}")
            if urlparse(url).scheme != "https":
                raise RuntimeError("Agnes returned a non-HTTPS video URL; refusing download.")
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with requests.get(url, stream=True, timeout=120) as download:
                download.raise_for_status()
                with output_path.open("wb") as handle:
                    for chunk in download.iter_content(1024 * 1024):
                        if chunk:
                            handle.write(chunk)
            if output_path.stat().st_size < 30000:
                raise RuntimeError("Agnes video download is unexpectedly small.")
            print(f"AI_VIDEO_READY bytes={output_path.stat().st_size}")
            return True
        if status in {"failed", "error", "cancelled"}:
            raise RuntimeError(f"Agnes video generation failed: {data}")
        time.sleep(10)
    raise TimeoutError(f"Agnes video task {video_id} timed out.")

def composite_ai_broll(main_video, ai_video, duration=5):
    main_video, ai_video = Path(main_video), Path(ai_video)
    if not main_video.exists() or not ai_video.exists():
        raise FileNotFoundError("Main video or Agnes AI B-roll file is missing.")
    temp = main_video.with_name(main_video.stem + "_with_ai.mp4")
    vf = (
        "[1:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[ai];"
        "[0:v][ai]overlay=0:0:enable='between(t,0," + str(duration) + ")'[v]"
    )
    cmd = ["ffmpeg","-y","-i",str(main_video),"-stream_loop","-1","-i",str(ai_video),
           "-filter_complex",vf,"-map","[v]","-map","0:a?","-c:v","libx264",
           "-preset","veryfast","-crf","19","-c:a","copy","-shortest",
           "-movflags","+faststart",str(temp)]
    result = subprocess.run(cmd,capture_output=True,text=True)
    if result.returncode:
        raise RuntimeError("AI B-roll composition failed: "+result.stderr[-2500:])
    if not temp.exists() or temp.stat().st_size < 50000:
        raise RuntimeError("AI B-roll composition produced invalid MP4.")
    temp.replace(main_video)
    print(f"AI_BROLL_COMPOSITED bytes={main_video.stat().st_size}")
