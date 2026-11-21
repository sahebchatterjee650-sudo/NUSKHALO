from pathlib import Path
import asyncio
import shutil
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont, features

W, H = 1080, 1920
NAVY = (7, 16, 34)
BLUE = (12, 39, 69)
CYAN = (42, 224, 207)
WHITE = (248, 250, 255)
MUTED = (171, 192, 211)
GOLD = (255, 190, 78)
RED = (238, 75, 85)


def _run(args):
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError("Command failed: " + " ".join(map(str, args[:4])) + "\n" + result.stderr[-3500:])
    return result


def _font_path():
    options = [
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansDevanagariUI-Regular.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansDevanagari-Regular.ttf",
    ]
    for p in options:
        if Path(p).exists():
            return p
    fc = shutil.which("fc-match")
    if fc:
        p = subprocess.run([fc, "-f", "%{file}", "Noto Sans Devanagari"],
                           capture_output=True, text=True, check=True).stdout.strip()
        if p and Path(p).exists():
            return p
    raise RuntimeError("Noto Sans Devanagari font not found.")


def _font(path, size):
    if not features.check("raqm"):
        raise RuntimeError("Pillow RAQM is required for correct Hindi shaping.")
    return ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)


def _background(seed=0):
    im = Image.new("RGB", (W, H))
    px = im.load()
    for y in range(H):
        t = y / (H - 1)
        col = tuple(int(NAVY[i] * (1-t) + BLUE[i] * t) for i in range(3))
        for x in range(W):
            px[x, y] = col
    d = ImageDraw.Draw(im, "RGBA")
    # Broadcast-style abstract radar rings and diagonal light bands.
    cx, cy = (850 if seed % 2 else 220), (430 + seed * 170) % 1550
    for r in (180, 270, 360, 450):
        d.ellipse((cx-r, cy-r, cx+r, cy+r), outline=(42, 224, 207, 30), width=4)
    for k in range(6):
        x = -350 + k * 260 + seed * 31
        d.polygon([(x, 0), (x+70, 0), (x+620, H), (x+550, H)], fill=(40, 105, 145, 13))
    return im


def _wrap(draw, text, font, width):
    lines, cur = [], ""
    for word in str(text).split():
        test = (cur + " " + word).strip()
        if draw.textbbox((0, 0), test, font=font)[2] <= width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines or [""]


def _paragraph(draw, text, xy, font, fill, width, gap=18, limit=10):
    x, y = xy
    lines = _wrap(draw, text, font, width)[:limit]
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        box = draw.textbbox((x, y), line, font=font)
        y += box[3] - box[1] + gap
    return y


def _chrome(im, scene, section, font_path):
    d = ImageDraw.Draw(im, "RGBA")
    d.rounded_rectangle((54, 62, 1026, 1855), radius=44,
                        fill=(4, 12, 25, 55), outline=(69, 207, 205, 130), width=3)
    d.text((96, 105), "नुस्खालो", font=_font(font_path, 48), fill=CYAN)
    d.text((98, 174), "देसी सेहत • स्वास्थ्य जागरूकता", font=_font(font_path, 23), fill=MUTED)
    d.rounded_rectangle((95, 260, 985, 330), radius=18, fill=(21, 66, 89, 235))
    d.text((126, 277), section.upper(), font=_font(font_path, 25), fill=WHITE)
    # Persistent live-news ticker and draft marker.
    d.rectangle((70, 1692, 1010, 1754), fill=(164, 34, 45, 245))
    d.text((96, 1706), "देसी सेहत", font=_font(font_path, 25), fill=WHITE)
    d.text((700, 1706), "जाँच हेतु ड्राफ्ट", font=_font(font_path, 25), fill=GOLD)
    d.text((95, 1790), "नुस्खालो • मूल स्रोत ज़रूर देखें", font=_font(font_path, 21), fill=MUTED)
    d.text((930, 1790), f"{scene}/04", font=_font(font_path, 21), fill=MUTED)
    return d


def _caption(draw, text, fp):
    draw.rounded_rectangle((105, 1515, 975, 1665), radius=24, fill=(2, 12, 26, 235), outline=(42, 224, 207, 210), width=2)
    _paragraph(draw, text, (135, 1550), _font(fp, 27), WHITE, 805, 10, 3)


def _make_scenes(draft, folder, fp, narration):
    title = (draft.get("topic") or "आज की स्वास्थ्य जानकारी").strip()
    summary = (draft.get("source_summary_original") or "मूल स्रोत का सारांश उपलब्ध नहीं है।").strip()
    domain = draft.get("source_domain") or "Official source"
    frames = []

    # 1 — studio-style opener, with a strong visual identity.
    im = _background(0); d = _chrome(im, 1, "Desi health tips", fp)
    d.ellipse((220, 480, 860, 1120), outline=CYAN, width=7)
    d.ellipse((270, 530, 810, 1070), outline=(255, 255, 255), width=2)
    d.text((360, 650), "N", font=_font(fp, 260), fill=WHITE)
    d.text((185, 1190), "नमस्कार!", font=_font(fp, 82), fill=WHITE)
    _paragraph(d, "सेहत के देसी नुस्खे और आसान आदतें।",
               (130, 1320), _font(fp, 43), CYAN, 820, 20, 3)
    _caption(d, narration[0], fp)
    p=folder/"scene01.png"; im.save(p); frames.append(p)

    # 2 — headline card, deliberately asymmetric and high contrast.
    im = _background(1); d = _chrome(im, 2, "Today’s health tip", fp)
    d.rectangle((95, 470, 112, 1390), fill=RED)
    d.text((150, 480), "आज का देसी हेल्थ टिप", font=_font(fp, 45), fill=GOLD)
    _paragraph(d, title, (145, 610), _font(fp, 67), WHITE, 800, 32, 9)
    d.rounded_rectangle((145, 1270, 945, 1450), radius=24, fill=(16, 73, 93, 235))
    d.text((185, 1320), "सेहतमंद आदत • घरेलू देखभाल", font=_font(fp, 29), fill=CYAN)
    _caption(d, narration[1], fp)
    p=folder/"scene02.png"; im.save(p); frames.append(p)

    # 3 — information panel with editorial hierarchy.
    im = _background(2); d = _chrome(im, 3, "जानिए आसान बात", fp)
    d.text((125, 460), "स्रोत की जानकारी", font=_font(fp, 53), fill=GOLD)
    d.rounded_rectangle((120, 570, 960, 1510), radius=32,
                        fill=(5, 20, 39, 220), outline=(42, 224, 207, 150), width=3)
    # A visual quote marker and source excerpt, not invented claims.
    d.text((165, 620), "“", font=_font(fp, 130), fill=CYAN)
    _paragraph(d, summary[:1250], (185, 790), _font(fp, 37), WHITE, 700, 22, 19)
    _caption(d, narration[2], fp)
    p=folder/"scene03.png"; im.save(p); frames.append(p)

    # 4 — source accountability and safety close.
    im = _background(3); d = _chrome(im, 4, "स्रोत और सावधानी", fp)
    d.text((125, 500), "जानकारी का स्रोत", font=_font(fp, 53), fill=GOLD)
    d.rounded_rectangle((120, 620, 960, 870), radius=28, fill=(15, 70, 91, 230))
    _paragraph(d, domain, (165, 690), _font(fp, 42), CYAN, 740, 18, 4)
    d.text((125, 1000), "स्वास्थ्य संबंधी सावधानी", font=_font(fp, 43), fill=WHITE)
    _paragraph(d, "यह वीडियो चिकित्सा सलाह नहीं है। किसी भी स्वास्थ्य निर्णय से पहले योग्य डॉक्टर से सलाह लें।",
               (125, 1110), _font(fp, 39), WHITE, 820, 25, 6)
    d.rounded_rectangle((120, 1430, 960, 1550), radius=24, fill=(98, 58, 20, 235))
    d.text((160, 1466), "स्रोत देखें • सावधानी रखें", font=_font(fp, 30), fill=GOLD)
    _caption(d, narration[3], fp)
    p=folder/"scene04.png"; im.save(p); frames.append(p)
    return frames


async def _voice(text, path):
    import edge_tts
    await edge_tts.Communicate(text, "hi-IN-MadhurNeural", rate="+0%").save(str(path))


def _duration(path):
    r = _run(["ffprobe","-v","error","-show_entries","format=duration",
              "-of","default=noprint_wrappers=1:nokey=1",str(path)])
    return max(1.0, float(r.stdout.strip()))


def render_video(draft, asset_root, output_path, config):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"RAQM={features.check('raqm')}")
    fp = _font_path()
    segments = draft.get("narration_segments") or [
        "नमस्कार। आप देख रहे हैं NUSKHALO हेल्थ अपडेट।",
        f"आज की खबर का विषय है: {draft.get('topic','स्वास्थ्य जानकारी')}।",
        "मूल स्रोत में दी गई जानकारी ध्यान से पढ़ें।",
        "यह चिकित्सा सलाह नहीं है। डॉक्टर से सलाह लें।"
    ]
    if len(segments) != 4:
        raise ValueError("Exactly four narration segments are required.")

    with tempfile.TemporaryDirectory(prefix="nuskhalo_") as tmp:
        folder = Path(tmp)
        scenes = _make_scenes(draft, folder, fp, segments)
        clips=[]
        for i, line in enumerate(segments):
            audio=folder/f"voice{i+1}.mp3"
            asyncio.run(_voice(line, audio))
            seconds=_duration(audio)+0.8
            clip=folder/f"part{i+1}.mp4"
            # Each panel has a distinct slow camera move; audio drives clip length.
            zoom = "min(zoom+0.00045,1.055)" if i % 2 == 0 else "max(zoom-0.00035,1.0)"
            _run(["ffmpeg","-y","-loop","1","-i",str(scenes[i]),"-i",str(audio),
                  "-vf",f"zoompan=z='{zoom}':d=1:s=1080x1920:fps=25,fade=t=in:st=0:d=0.35,format=yuv420p",
                  "-t",f"{seconds:.2f}","-map","0:v:0","-map","1:a:0",
                  "-c:v","libx264","-preset","veryfast","-crf","19",
                  "-c:a","aac","-b:a","160k","-shortest","-movflags","+faststart",str(clip)])
            clips.append(clip)
        concat=folder/"concat.txt"
        concat.write_text("".join(f"file '{p.as_posix()}'\n" for p in clips),encoding="utf-8")
        _run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat),
              "-c","copy","-movflags","+faststart",str(output_path)])

    if not output_path.exists() or output_path.stat().st_size < 50000:
        raise RuntimeError("MP4 validation failed: output missing or too small.")
    probe=_run(["ffprobe","-v","error","-show_entries","stream=codec_type,width,height",
                "-of","json",str(output_path)])
    print("MP4_STREAMS="+probe.stdout)
    print(f"NUSKHALO review MP4 ready: {output_path} ({output_path.stat().st_size} bytes)")
