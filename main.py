from pathlib import Path
import json, time
from datetime import datetime
from desi_topics import daily_topics, TOPICS
from script import build_script
from video_engine import render_video
from ai_video import generate_health_broll, composite_ai_broll

ROOT = Path(__file__).parent

def main():
    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    out = ROOT / config.get("output_dir", "output")
    out.mkdir(parents=True, exist_ok=True)
    count = int(config.get("daily_target", 5))
    if config.get("test_mode", False):
        test_id = config.get("test_topic_id", "honey-cough")
        topics = [item for item in TOPICS if item.get("id") == test_id][:1]
        if not topics:
            raise ValueError(f"Configured test_topic_id not found: {test_id}")
        print(f"TEST MODE: building exactly one video for topic {test_id}")
    else:
        topics = daily_topics(count)
    manifest = []
    for index, topic in enumerate(topics, start=1):
        draft = build_script(topic, config)
        draft["video_number"] = index
        draft["created_at"] = datetime.now().astimezone().isoformat()
        draft_path = out / f"script_{index:02d}.json"
        draft_path.write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
        video_path = out / f"nuskhalo_short_{index:02d}.mp4"
        ai_path = out / f"realistic_broll_{index:02d}.mp4"
        print(f"\n=== Building {index}/{len(topics)}: {topic['title']} ===")
        render_video(draft, ROOT / "assets", video_path, config)
        ai_status = "disabled"
        if config.get("ai_video_enabled", False):
            try:
                if generate_health_broll(topic, ai_path, config):
                    composite_ai_broll(video_path, ai_path, int(config.get("ai_video_duration_seconds", 5)))
                    ai_status = "realistic_ai_opening"
                else:
                    ai_status = "api_key_missing_graphics_fallback"
            except Exception as exc:
                ai_status = "failed_graphics_fallback"
                print(f"AI_VIDEO_WARNING: {exc}")
        manifest.append({
            "number": index, "title": topic["title"], "category": topic.get("category"),
            "video": video_path.name, "script": draft_path.name,
            "source": topic.get("source_url"), "review_status": draft["review_status"],
            "visual_status": ai_status
        })
        # Agnes public free-tier video RPM is documented as low; space requests to avoid bursts.
        if index < len(topics) and config.get("ai_video_enabled", False):
            time.sleep(int(config.get("ai_video_request_spacing_seconds", 65)))
    report = {
        "brand": "NUSKHALO", "channel_type": "Indian Desi Health & Wellness",
        "language": "Hindi", "created_at": datetime.now().astimezone().isoformat(),
        "videos_created": len(manifest), "publishing_enabled": False,
        "videos": manifest,
        "note": "Human review is required before publishing. This workflow does not diagnose or promise cures."
    }
    (out / "daily_manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "run_report.txt").write_text(
        f"NUSKHALO DESI HEALTH RUN\nVideos created: {len(manifest)}\n"
        "Language: Hindi\nPublishing: DISABLED\nHuman review: REQUIRED\n", encoding="utf-8"
    )
    print(f"Created {len(manifest)} Hindi health-awareness Shorts. Publishing remains disabled.")

if __name__ == "__main__":
    main()
