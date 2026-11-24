"""Create original Hindi product-video drafts from a manually curated Amazon.in catalog.

Do not scrape Amazon pages or copy Amazon product images/descriptions. Enter original
summaries and an Associates Special Link supplied by the account owner.
"""
from pathlib import Path
from datetime import datetime
import json, asyncio, subprocess, shutil, re

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent
W, H = 1080, 1920
BG = (10, 22, 40)
CYAN = (40, 220, 200)
WHITE = (250, 250, 250)
GOLD = (255, 195, 80)


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(p.stderr[-2500:])
    return p


def font_path():
    candidates = [
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansDevanagariUI-Regular.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansDevanagari-Regular.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            return p
    found = shutil.which("fc-match")
    if found:
        p = subprocess.run([found, "-f", "%{file}", "Noto Sans Devanagari"],
                           capture_output=True, text=True).stdout.strip()
        if p and Path(p).exists():
            return p
    raise RuntimeError("Noto Sans Devanagari font not installed")


def wrap(draw, text, font, max_width):
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
    return lines


def draw_lines(draw, text, y, f, fill, max_width=850, gap=20, max_lines=5):
    for line in wrap(draw, text, f, max_width)[:max_lines]:
        draw.text((110, y), line, font=f, fill=fill)
        y += draw.textbbox((0, 0), line, font=f)[3] + gap
    return y


def make_video(product, output):
    import edge_tts
    from PIL import features
    if not features.check("raqm"):
        raise RuntimeError("Pillow RAQM is required for correct Hindi shaping")
    fp = font_path()
    title_font = ImageFont.truetype(fp, 68, layout_engine=ImageFont.Layout.RAQM)
    body_font = ImageFont.truetype(fp, 42, layout_engine=ImageFont.Layout.RAQM)
    small_font = ImageFont.truetype(fp, 30, layout_engine=ImageFont.Layout.RAQM)

    narration = product["hindi_narration"].strip()
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((55, 55, 1025, 1865), radius=48, outline=CYAN, width=4)
    d.text((105, 115), "NUSKHALO", font=small_font, fill=CYAN)
    d.text((105, 205), "आज का उपयोगी गैजेट", font=body_font, fill=GOLD)
    y = draw_lines(d, product["name_hi"], 340, title_font, WHITE, max_lines=4)
    y += 55
    for feature in product["original_features_hi"][:3]:
        d.ellipse((115, y+10, 145, y+40), fill=CYAN)
        y = draw_lines(d, feature, y, body_font, WHITE, max_lines=3) + 32
    y = max(y + 35, 1250)
    draw_lines(d, "कीमत और उपलब्धता बदल सकती है। खरीदने से पहले Amazon पर जाँचें।",
               y, small_font, GOLD, max_lines=3)
    d.text((105, 1755), "लिंक और विवरण वीडियो के साथ • #ad", font=small_font, fill=CYAN)

    output.parent.mkdir(parents=True, exist_ok=True)
    with __import__("tempfile").TemporaryDirectory() as td:
        still = Path(td) / "scene.png"
        audio = Path(td) / "voice.mp3"
        img.save(still)
        async def voice():
            await edge_tts.Communicate(narration, "hi-IN-MadhurNeural", rate="+0%").save(str(audio))
        asyncio.run(voice())
        run(["ffmpeg", "-y", "-loop", "1", "-i", str(still), "-i", str(audio),
             "-vf", "scale=1080:1920,zoompan=z='min(zoom+0.0004,1.04)':d=1:s=1080x1920:fps=25,format=yuv420p",
             "-shortest", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
             "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(output)])
    if not output.exists() or output.stat().st_size < 50000:
        raise RuntimeError("Video validation failed")
    probe = json.loads(run(["ffprobe", "-v", "error", "-show_entries",
                            "stream=codec_type,width,height", "-of", "json", str(output)]).stdout)
    video = next((s for s in probe["streams"] if s.get("codec_type") == "video"), None)
    if not video or video.get("width") != W or video.get("height") != H:
        raise RuntimeError("Expected 1080x1920 vertical video")
    return output


def main():
    catalog = json.loads((ROOT / "amazon_products.json").read_text(encoding="utf-8"))
    products = catalog.get("products", [])
    if not products:
        raise SystemExit("NO_PRODUCTS: add one reviewed product with an Amazon Associates Special Link to amazon_products.json")
    out = ROOT / "output" / "amazon"
    out.mkdir(parents=True, exist_ok=True)
    report = []
    for i, p in enumerate(products[:1], 1):
        required = ["asin", "name_hi", "original_features_hi", "hindi_narration", "affiliate_url"]
        missing = [k for k in required if not p.get(k)]
        if missing:
            raise ValueError(f"Product {i} missing fields: {', '.join(missing)}")
        url = p["affiliate_url"].strip()
        if not url.startswith("https://") or "amazon." not in url and "amzn.to/" not in url:
            raise ValueError("affiliate_url must be a real HTTPS Amazon Associates Special Link")
        if not isinstance(p["original_features_hi"], list) or not p["original_features_hi"]:
            raise ValueError("original_features_hi must be a non-empty list")
        target = out / f"nuskhalo_amazon_{i:02d}.mp4"
        make_video(p, target)
        description = (
            f"{p['name_hi']}\n\n"
            f"{p.get('original_summary_hi','')}\n\n"
            f"खरीदने का लिंक: {url}\n"
            "विज्ञापन / Affiliate disclosure: इस लिंक से योग्य खरीदारी होने पर मुझे कमीशन मिल सकता है।\n"
            "As an Amazon Associate I earn from qualifying purchases. #ad\n"
            "कीमत और उपलब्धता बदल सकती है; खरीदने से पहले Amazon पर वर्तमान विवरण देखें।"
        )
        (out / f"nuskhalo_amazon_{i:02d}.txt").write_text(description, encoding="utf-8")
        report.append({"asin": p["asin"], "video": target.name, "description": f"nuskhalo_amazon_{i:02d}.txt",
                       "status": "draft_for_human_review"})
    (out / "manifest.json").write_text(json.dumps({
        "brand": "NUSKHALO", "created_at": datetime.now().astimezone().isoformat(),
        "publishing": "disabled_by_default", "products": report
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Created {len(report)} private-review product video draft(s). No public post was made.")


if __name__ == "__main__":
    main()
