from pathlib import Path
import asyncio
import json
import shutil
import subprocess
import tempfile
import textwrap

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1080, 1920
BG_TOP = (8, 18, 38)
BG_BOTTOM = (17, 42, 66)
WHITE = (247, 249, 252)
MUTED = (178, 194, 211)
CYAN = (63, 220, 203)
GOLD = (255, 195, 92)


def _run(command):
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _font_path():
    candidates = [
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansDevanagariUI-Regular.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansDevanagari-Regular.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return path
    fc_match = shutil.which("fc-match")
    if fc_match:
        result = subprocess.run(
            [fc_match, "-f", "%{file}", "Noto Sans Devanagari"],
            check=True, capture_output=True, text=True
        )
        path = result.stdout.strip()
        if path and Path(path).exists():
            return path
    raise RuntimeError("Noto Sans Devanagari font not found. Install fonts-noto-core.")


def _font(size, path):
    return ImageFont.truetype(path, size)


def _gradient():
    image = Image.new("RGB", (WIDTH, HEIGHT))
    pixels = image.load()
    for y in range(HEIGHT):
        t = y / max(1, HEIGHT - 1)
        color = tuple(int(BG_TOP[i] * (1 - t) + BG_BOTTOM[i] * t) for i in range(3))
        for x in range(WIDTH):
            pixels[x, y] = color
    return image


def _wrap(draw, text, font, max_width):
    lines, current = [], ""
    for word in str(text).split():
        trial = (current + " " + word).strip()
        if draw.textbbox((0, 0), trial, font=font)[2] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def _draw_wrapped(draw, text, x, y, font, fill, max_width, line_gap=18, max_lines=8):
    lines = _wrap(draw, text, font, max_width)[:max_lines]
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill, stroke_width=0)
        box = draw.textbbox((x, y), line, font=font)
        y += box[3] - box[1] + line_gap
    return y


def _base_scene(number, label, font_path):
    image = _gradient()
    draw = ImageDraw.Draw(image)
    draw.ellipse((760, -170, 1250, 320), fill=(19, 66, 83))
    draw.ellipse((-250, 1370, 340, 1960), fill=(20, 57, 78))
    draw.rounded_rectangle((58, 72, 1022, 1848), radius=48, outline=(43, 113, 126), width=3)
    draw.text((100, 112), "NUSKHALO", font=_font(52, font_path), fill=CYAN)
    draw.text((100, 183), "HEALTH • VERIFIED SOURCES", font=_font(24, font_path), fill=MUTED)
    draw.rounded_rectangle((100, 280, 980, 360), radius=24, fill=(28, 73, 88))
    draw.text((135, 298), label, font=_font(30, font_path), fill=WHITE)
    draw.text((100, 1750), "HEALTH AWARENESS • REVIEW DRAFT", font=_font(24, font_path), fill=GOLD)
    draw.text((900, 1750), f"{number:02d}/04", font=_font(24, font_path), fill=MUTED)
    return image, draw


def _make_scenes(draft, workdir, font_path, segments):
    title = draft.get("topic") or "आज की स्वास्थ्य जानकारी"
    summary = draft.get("source_summary_original") or "मूल स्रोत का सारांश उपलब्ध नहीं है।"
    domain = draft.get("source_domain") or "Official source"
    scenes = []

    image, draw = _base_scene(1, "TODAY'S HEALTH UPDATE", font_path)
    draw.text((100, 540), "नमस्कार!", font=_font(78, font_path), fill=WHITE)
    _draw_wrapped(draw, "आज की स्वास्थ्य जानकारी — आधिकारिक स्रोत से।", 100, 700, _font(54, font_path), CYAN, 850, 28, 4)
    draw.rounded_rectangle((100, 1120, 980, 1330), radius=34, fill=(22, 67, 81))
    draw.text((145, 1180), "जानकारी • जागरूकता • सावधानी", font=_font(35, font_path), fill=WHITE)
    draw.rounded_rectangle((90, 1510, 990, 1690), radius=28, fill=(10, 31, 49), outline=(63, 220, 203), width=2)\n    _draw_wrapped(draw, segments[0], 125, 1550, _font(29, font_path), WHITE, 820, 12, 3)\n    p = workdir / "scene_01.png"; image.save(p); scenes.append(p)

    image, draw = _base_scene(2, "THE HEADLINE", font_path)
    draw.text((100, 500), "आज की खबर", font=_font(54, font_path), fill=GOLD)
    _draw_wrapped(draw, title, 100, 650, _font(58, font_path), WHITE, 850, 30, 8)
    draw.rounded_rectangle((100, 1250, 980, 1440), radius=30, fill=(23, 72, 87))
    draw.text((145, 1315), "मूल शीर्षक • आधिकारिक रिपोर्ट", font=_font(32, font_path), fill=CYAN)
    draw.rounded_rectangle((90, 1510, 990, 1690), radius=28, fill=(10, 31, 49), outline=(63, 220, 203), width=2)\n    _draw_wrapped(draw, segments[1], 125, 1550, _font(29, font_path), WHITE, 820, 12, 3)\n    p = workdir / "scene_02.png"; image.save(p); scenes.append(p)

    image, draw = _base_scene(3, "WHAT THE SOURCE SAYS", font_path)
    draw.text((100, 470), "मूल स्रोत का सारांश", font=_font(48, font_path), fill=GOLD)
    _draw_wrapped(draw, summary[:1100], 100, 590, _font(36, font_path), WHITE, 850, 20, 18)
    draw.rounded_rectangle((90, 1510, 990, 1690), radius=28, fill=(10, 31, 49), outline=(63, 220, 203), width=2)\n    _draw_wrapped(draw, segments[2], 125, 1550, _font(29, font_path), WHITE, 820, 12, 3)\n    p = workdir / "scene_03.png"; image.save(p); scenes.append(p)

    image, draw = _base_scene(4, "SOURCE & SAFETY", font_path)
    draw.text((100, 520), "स्रोत की जाँच करें", font=_font(58, font_path), fill=WHITE)
    _draw_wrapped(draw, domain, 100, 650, _font(40, font_path), CYAN, 850, 22, 3)
    _draw_wrapped(draw, "यह वीडियो चिकित्सा सलाह नहीं है। स्वास्थ्य संबंधी निर्णय के लिए योग्य डॉक्टर से सलाह लें।", 100, 900, _font(42, font_path), WHITE, 850, 26, 7)
    draw.rounded_rectangle((100, 1320, 980, 1460), radius=28, fill=(91, 58, 27))
    draw.text((140, 1365), "मानव अनुवाद और तथ्य-जाँच आवश्यक", font=_font(30, font_path), fill=GOLD)
    draw.rounded_rectangle((90, 1510, 990, 1690), radius=28, fill=(10, 31, 49), outline=(63, 220, 203), width=2)\n    _draw_wrapped(draw, segments[3], 125, 1550, _font(29, font_path), WHITE, 820, 12, 3)\n    p = workdir / "scene_04.png"; image.save(p); scenes.append(p)
    return scenes


async def _make_voice(text, audio_path):
    import edge_tts
    communicate = edge_tts.Communicate(text, "hi-IN-MadhurNeural", rate="+2%")
    await communicate.save(str(audio_path))


def _probe_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        check=True, capture_output=True, text=True
    )
    return max(1.0, float(result.stdout.strip()))


def render_video(draft, asset_root, output_path, config):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    font_path = _font_path()
    segments = draft.get("narration_segments") or [
        "नमस्कार। आप देख रहे हैं NUSKHALO हेल्थ अपडेट।",
        f"आज की खबर का विषय है: {draft.get('topic', 'स्वास्थ्य जानकारी')}।",
        "मूल स्रोत पढ़ें और हर तथ्य की जाँच करें।",
        "यह चिकित्सा सलाह नहीं है। डॉक्टर से सलाह लें।",
    ]
    if len(segments) != 4:
        raise ValueError("Expected exactly four narration segments for the four-scene video.")

    with tempfile.TemporaryDirectory(prefix="nuskhalo_") as tmp:
        workdir = Path(tmp)
        scenes = _make_scenes(draft, workdir, font_path, segments)
        clips = []
        for index, narration in enumerate(segments, start=1):
            audio = workdir / f"voice_{index:02d}.mp3"
            asyncio.run(_make_voice(narration, audio))
            duration = _probe_duration(audio) + 0.35
            clip = workdir / f"clip_{index:02d}.mp4"
            _run([
                "ffmpeg", "-y", "-loop", "1", "-i", str(scenes[index - 1]),
                "-i", str(audio),
                "-vf", "scale=1080:1920,zoompan=z='min(zoom+0.00035,1.035)':d=1:s=1080x1920:fps=25,format=yuv420p",
                "-t", f"{duration:.2f}", "-map", "0:v:0", "-map", "1:a:0",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
                "-c:a", "aac", "-b:a", "128k", "-shortest",
                "-movflags", "+faststart", str(clip)
            ])
            clips.append(clip)

        concat_file = workdir / "concat.txt"
        concat_file.write_text(
            "".join(f"file '{clip.as_posix()}'\n" for clip in clips), encoding="utf-8"
        )
        _run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file),
            "-c", "copy", "-movflags", "+faststart", str(output_path)
        ])

    if not output_path.exists() or output_path.stat().st_size < 50000:
        raise RuntimeError("FFmpeg did not create a valid NUSKHALO MP4.")
    print(f"Professional four-scene review video ready: {output_path} ({output_path.stat().st_size} bytes)")
