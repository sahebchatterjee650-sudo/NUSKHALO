from pathlib import Path
import json
from datetime import datetime
from research import collect_topics
from script import build_script
from video_engine import render_video

ROOT = Path(__file__).parent


def main():
    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    out = ROOT / config.get("output_dir", "output")
    out.mkdir(parents=True, exist_ok=True)

    topics = collect_topics(config)
    if not topics:
        report = [
            "NUSKHALO run report",
            f"Time: {datetime.now().astimezone().isoformat()}",
            "Result: No fresh, trusted RSS candidate topics were returned.",
            "Check RSS diagnostics above. No video can be made without a sourced topic.",
            "Publishing remains disabled."
        ]
        (out / "run_report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
        print("No suitable sourced topics found; diagnostic report saved.")
        return

    topic = topics[0]
    draft = build_script(topic, config)
    draft_path = out / "script_draft.json"
    draft_path.write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Draft created: {draft_path}")

    # Always create a clearly watermarked review preview.
    # This does NOT approve medical claims or enable publishing.
    video_path = out / "nuskhalo_preview.mp4"
    render_video(draft, ROOT / "assets", video_path, config)
    print(f"Review preview created: {video_path}")

    if draft.get("review_status") != "approved":
        print("Human translation and medical fact-check still required. Publishing is paused.")
        return

    print("Draft marked approved. Publishing remains disabled unless separately configured.")


if __name__ == "__main__":
    main()
