from pathlib import Path
import asyncio
import subprocess
import textwrap

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1080, 1920
BG = (12, 18, 32)
WHITE = (245, 247, 250)
MUTED = (174, 188, 205)
ACCENT = (48, 180, 150)


def _font(size):
    candidates = [
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansDevanagariUI-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    raise RuntimeError("No usable font found. Install fonts-noto-core in the workflow.")


def _wrap_by_pixels(draw, text, font, max_width):
    words = str(text).split()
    lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textbbox((0, 0), trial, font=font)[2] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _draw_centered(draw, text, y, font, fill, max_width=900, line_gap=22):
    lines = _wrap_by_pixels(draw, text, font, max_width)
    for line in lines:
        box = draw.textbbox((0, 0), line, font=font)
        x = (WIDTH - (box[2] - box[0])) // 2
        draw.text((x, y), line, font=font, fill=fill)
        y += (box[3] - box[1]) + line_gap
    return y


def _make_card(draft, image_path):
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    # Simple branded graphic treatment; no unverified medical imagery or claims.
    draw.rounded_rectangle((55, 70, WIDTH - 55, HEIGHT - 70), radius=42, outline=ACCENT, width=5)
    draw.text((100, 125), "NUSKHALO  |  HEALTH AWARENESS", font=_font( thirty :=  thirty_size()), fill=ACCENT)
    draw.rounded_rectangle((100, 245, WIDTH - 100, 335), radius=24, fill=(100, 43, 30))
    _draw_centered(draw, "DRAFT PREVIEW • NOT FOR PUBLICATION", 265, _font( thirty_size()), WHITE, 820, 8)

    y = 470
    y = _draw_centered(draw, "आज का स्वास्थ्य विषय", y, _font(64), WHITE, 900, 26)
    y += 45
    y = _draw_centered(draw, draft.get("topic", "स्वास्थ्य जागरूकता"), y, _font(48), ACCENT, 860, 24)
    y += 65
    summary = draft.get("source_summary_original", "")
    if summary:
        y = _draw_centered(draw, "आधिकारिक स्रोत से प्राप्त जानकारी", y, _font(34), MUTED, 850, 20)
        y += 25
        y = _draw_centered(draw, summary[:420], y, _font( thirty_size()), WHITE, 850, 18)
    y = max(y + 90, 1330)
    _draw_centered(draw, "किसी भी स्वास्थ्य निर्णय से पहले योग्य डॉक्टर से सलाह लें।", y, _font(35), WHITE, 850, 18)
    source = draft.get("source_domain", "Official source")
    draw.text((100, HEIGHT - 220), f"Source: {source}", font=_font(26), fill=MUTED)
    draw.text((100, HEIGHT - 155), "Human translation & fact-check required", font=_font(27), fill=ACCENT)
    image.save(image_path, quality=95)


def thirty_size():
    return  thirty_size_value()


def thirty_size_value():
    return 32


async def _make_voice(text, audio_path):
    import edge_tts
    voice = "hi-IN-MadhurNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(audio_path))


def render_video(draft, asset_root, output_path, config):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image_path = output_path.with_suffix(".jpg")
    audio_path = output_path.with_suffix(".mp3")
    _make_card(draft, image_path)

    narration = (
        "नमस्कार। NUSKHALO में आपका स्वागत है। "
        "आज हम एक स्वास्थ्य विषय पर जागरूकता की जानकारी साझा कर रहे हैं। "
        "यह प्रारंभिक ड्राफ्ट है। कृपया मूल आधिकारिक स्रोत पढ़ें और "
        "किसी भी स्वास्थ्य संबंधी निर्णय से पहले योग्य डॉक्टर की सलाह लें।"
    )
    has_audio = False
    try:
        asyncio.run(_make_voice(narration, audio_path))
        has_audio = audio_path.exists() and audio_path.stat().st_size > 1000
    except Exception as exc:
        print(f"Hindi voice generation unavailable; creating silent preview: {exc}")

    common = [
        "ffmpeg", "-y", "-loop", "1", "-i", str(image_path)
    ]
    if has_audio:
        common += ["-i", str(audio_path)]
    common += [
        "-vf", "zoompan=z='min(zoom+0.0005,1.04)':d=1:s=1080x1920:fps=25,format=yuv420p",
        "-t", str(config.get("video_seconds", 45)),
    ]
    if has_audio:
        common += ["-map", "0:v:0", "-map", "1:a:0", "-c:a", "aac", "-b:a", "128k", "-shortest"]
    else:
        common += ["-an"]
    common += ["-c:v", "libx264", "-preset", "veryfast", "-movflags", "+faststart", str(output_path)]
    subprocess.run(common, check=True)
    if not output_path.exists() or output_path.stat().st_size < 10000:
        raise RuntimeError("FFmpeg did not create a valid MP4 preview.")
    print(f"MP4 preview ready: {output_path} ({output_path.stat().st_size} bytes)")
