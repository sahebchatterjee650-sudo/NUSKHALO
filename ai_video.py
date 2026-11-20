"""Agnes Video 2.5 Flash realistic vertical B-roll. Requires AGNES_API_KEY."""
import os, time, subprocess
from pathlib import Path
from urllib.parse import urlparse
import requests

API_ROOT = "https://apihub.agnes-ai.com"
MODEL = "agnes-video-2.5-flash"

VISUALS = {
 "honey-cough": "close-up macro of a real Indian home kitchen, an adult hand slowly pouring golden honey from a wooden dipper into a clear cup of warm water, gentle steam, natural morning window light, authentic utensils, documentary food cinematography",
 "turmeric-milk": "real Indian home kitchen, adult hand adding a small pinch of turmeric to warm milk in a saucepan and gently stirring with a spoon, subtle steam, warm natural light, authentic everyday setting",
 "amla-vitamin-c": "fresh Indian amla gooseberries being rinsed under clean running water, then sliced on a wooden chopping board, close-up texture and natural droplets, cozy winter morning kitchen light",
 "healthy-khichdi": "step-by-step realistic Indian cooking close-up, moong dal rice carrots and peas simmering together in a steel pot, adult hand gently stirring with ladle, appetizing steam, home kitchen",
 "balanced-plate": "overhead realistic Indian thali being arranged with colorful seasonal vegetables, dal, whole grain roti and rice, adult hands placing small bowls, bright natural daylight",
 "sugar-honey": "close-up of a teaspoon of honey being measured beside a small bowl of sugar on a clean Indian kitchen counter, realistic food photography, neutral daylight",
 "hydration": "adult Indian person filling a clear glass with drinking water from a clean steel water jug at home, natural daylight, close-up realistic hands and water",
 "food-safety": "adult washing fresh vegetables under clean running water in a bright Indian home kitchen, close-up hands and vegetables, documentary realism",
 "whole-grains": "close-up of Indian millets, jowar, bajra and whole wheat grains being poured into small bowls on a rustic kitchen counter, natural daylight",
 "fruit-veg": "fresh seasonal Indian fruits and vegetables arranged on a kitchen counter, adult hand selecting guava and papaya, realistic close-up food documentary"
}

def _prompt(topic):
    scene = VISUALS.get(topic.get("id"), "realistic Indian home kitchen preparing a simple healthy meal with fresh local ingredients")
    return (scene + ". Vertical 9:16 portrait composition, photorealistic live-action footage, "
            "natural human hand movement, realistic ingredient textures, gentle cinematic camera movement, "
            "soft natural lighting, authentic Indian home environment, documentary food cinematography. "
            "No text, no captions, no logos, no watermark, no medical demonstrations, no exaggerated effects.")

def _request(method, path, key, **kwargs):
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    last = None
    for attempt in range(5):
        response = requests.request(method, API_ROOT + path, headers=headers, timeout=90, **kwargs)
        if response.status_code in (408,429,500,502,503,504,520,522,524):
            last = f"HTTP {response.status_code}: {response.text[:800]}"
            delay = min(60, 8 * (2 ** attempt))
            print(f"Agnes temporary error; retrying in {delay}s: {last}")
            time.sleep(delay)
            continue
        if response.status_code >= 400:
            raise RuntimeError(f"Agnes API HTTP {response.status_code}: {response.text[:1200]}")
        return response.json()
    raise RuntimeError("Agnes retries exhausted: " + str(last))

def generate_health_broll(topic, output_path, config):
    key = os.getenv("AGNES_API_KEY", "").strip()
    if not key:
        print("AI_VIDEO_SKIPPED: AGNES_API_KEY secret is not configured; using motion-graphics fallback.")
        return False
    seconds = str(int(config.get("ai_video_duration_seconds", 5)))
    if not 4 <= int(seconds) <= 12:
        raise ValueError("Agnes video duration must be 4–12 seconds.")
    payload = {
        "model": MODEL, "prompt": _prompt(topic), "mode": "text",
        "seconds": seconds, "size": "720P", "aspect_ratio": "9:16", "n": 1
    }
    print(f"AI_VIDEO_REQUEST provider=Agnes model={MODEL} seconds={seconds} aspect_ratio=9:16")
    created = _request("POST", "/v1/videos", key, json=payload)
    video_id = created.get("video_id") or created.get("id") or created.get("task_id")
    if not video_id:
        raise RuntimeError(f"Agnes create response missing video_id: {created}")
    deadline = time.time() + int(config.get("ai_video_timeout_seconds", 900))
    while time.time() < deadline:
        data = _request("GET", "/agnesapi", key, params={"video_id": video_id, "model_name": MODEL})
        status = str(data.get("status", "")).lower()
        print(f"AI_VIDEO_TASK status={status}")
        if status == "completed":
            url = data.get("url")
            if not url or urlparse(url).scheme != "https":
                raise RuntimeError("Agnes completed without a valid HTTPS video URL.")
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with requests.get(url, stream=True, timeout=120) as response:
                response.raise_for_status()
                with output_path.open("wb") as handle:
                    for chunk in response.iter_content(1024 * 1024):
                        if chunk: handle.write(chunk)
            if output_path.stat().st_size < 30000:
                raise RuntimeError("Agnes video download is unexpectedly small.")
            print(f"AI_VIDEO_READY bytes={output_path.stat().st_size}")
            return True
        if status == "failed":
            raise RuntimeError(f"Agnes video generation failed: {data}")
        time.sleep(10)
    raise TimeoutError(f"Agnes video task {video_id} timed out.")

def composite_ai_broll(main_video, ai_video, duration=5):
    main_video, ai_video = Path(main_video), Path(ai_video)
    if not main_video.exists() or not ai_video.exists():
        raise FileNotFoundError("Main video or Agnes AI B-roll file is missing.")
    temp = main_video.with_name(main_video.stem + "_realistic.mp4")
    vf = ("[1:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
          "setsar=1,fps=25,trim=duration="+str(duration)+",setpts=PTS-STARTPTS[ai];"
          "[0:v]trim=start="+str(duration)+",setpts=PTS-STARTPTS[rest];"
          "[ai][rest]concat=n=2:v=1:a=0[v]")
    cmd = ["ffmpeg","-y","-i",str(main_video),"-i",str(ai_video),
           "-filter_complex",vf,"-map","[v]","-map","0:a?","-c:v","libx264",
           "-preset","veryfast","-crf","19","-c:a","copy","-shortest",
           "-movflags","+faststart",str(temp)]
    result = subprocess.run(cmd,capture_output=True,text=True)
    if result.returncode:
        raise RuntimeError("AI B-roll composition failed: "+result.stderr[-2500:])
    if not temp.exists() or temp.stat().st_size < 50000:
        raise RuntimeError("AI B-roll composition produced invalid MP4.")
    temp.replace(main_video)
    print(f"REALISTIC_AI_OPENING_READY bytes={main_video.stat().st_size}")
