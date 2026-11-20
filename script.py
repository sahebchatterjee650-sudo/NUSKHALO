def build_script(topic, config):
    """Source-grounded Hindi draft; no invented medical claims."""
    title = (topic.get("title") or "").strip()
    summary = (topic.get("summary") or "").strip()
    domain = topic.get("source_domain", "")
    return {
        "brand": config.get("brand", "NUSKHALO"),
        "language": "hi",
        "topic": title,
        "source_summary_original": summary,
        "published_at": topic.get("published", ""),
        "source_domain": domain,
        "source_url": topic.get("source_url", ""),
        "narration_segments": [
            "नमस्कार। आप देख रहे हैं NUSKHALO हेल्थ न्यूज़।",
            f"आज की बड़ी खबर है: {title}।",
            "आइए, आधिकारिक स्रोत में दी गई जानकारी को समझते हैं। प्रकाशित करने से पहले इसका सरल हिंदी अनुवाद और हर तथ्य की जाँच ज़रूरी है।",
            "यह वीडियो चिकित्सा सलाह नहीं है। स्वास्थ्य संबंधी निर्णय के लिए योग्य डॉक्टर से सलाह लें।",
        ],
        "sources": [topic.get("source_url", "")],
        "review_status": "needs_human_translation_and_fact_check",
        "translation_required": True,
        "medical_safety_note": (
            "No diagnosis, cure claims, medication changes, or unsupported advice. "
            "Translate and verify every factual statement against the linked official source."
        )
    }
