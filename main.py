from pathlib import Path
import json
from research import collect_topics
from script import build_script
from video_engine import render_video

ROOT = Path(__file__).parent

def main():
    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    out = ROOT / config.get("output_dir", "output")
    out.mkdir(exist_ok=True)

    topics = collect_topics(config)
    if not topics:
        print("No suitable sourced topics found; skipping today's build.")
        return

    # Conservative starter: create one draft per run; expand to 3 only after review.
    topic = topics[0]
    draft = build_script(topic, config)
    draft_path = out / "script_draft.json"
    draft_path.write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Draft created: {draft_path}")

    if draft.get("review_status") != "approved":
        print("Human fact-check required. Video rendering and publishing paused.")
        return

    render_video(draft, ROOT / "assets", out / "nuskhalo_short.mp4", config)
    print("Video rendered. Publishing remains disabled unless separately configured.")

if __name__ == "__main__":
    main()
