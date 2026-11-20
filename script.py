def build_script(topic, config):
    """Build a short, cautious Hindi wellness script from a reviewed topic bank."""
    segments = topic.get("narration") or []
    if len(segments) != 4:
        raise ValueError("Each topic must contain exactly four narration segments.")
    return {
        "brand": config.get("brand", "NUSKHALO"),
        "language": "hi",
        "topic": topic["title"],
        "category": topic.get("category", "देसी सेहत"),
        "source_summary_original": topic.get("summary", ""),
        "source_domain": topic.get("source_domain", ""),
        "source_url": topic.get("source_url", ""),
        "narration_segments": segments,
        "sources": [topic.get("source_url", "")],
        "review_status": "needs_human_review",
        "translation_required": False,
        "medical_safety_note": "Awareness only. No diagnosis, cure guarantee, medicine changes, or substitute for professional care."
    }
