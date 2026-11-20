from pathlib import Path
import subprocess

def render_video(draft, asset_root, output_path, config):
    clips_dir = Path(asset_root) / "clips"
    clips = sorted(clips_dir.glob("*.mp4"))
    if len(clips) < 2:
        raise RuntimeError(
            "Add at least two licensed/owned MP4 clips to assets/clips before rendering. "
            "A single still image will not be used as a substitute for moving footage."
        )
    # Concatenate multiple moving clips; production build should add timed Hindi captions,
    # licensed voiceover, audio ducking, transitions, crop-to-fill and source end-card.
    list_file = Path(output_path).with_suffix(".concat.txt")
    list_file.write_text("".join(f"file '{p.resolve().as_posix()}'\n" for p in clips[:5]), encoding="utf-8")
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
        "-t", str(config.get("video_seconds", 45)),
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30",
        "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(output_path)
    ]
    subprocess.run(cmd, check=True)
