def build_script(topic, config):
    """Create a source-grounded Hindi review draft; never invent medical advice."""
    title = topic.get("title", "").strip()
    summary = topic.get("summary", "").strip()
    domain = topic.get("source_domain", "")
    return {
        "brand": config.get("brand", "NUSKHALO"),
        "language": "hi",
        "topic": title,
        "source_summary_original": summary,
        "published_at": topic.get("published", ""),
        "source_domain": domain,
        "source_url": topic.get("source_url", ""),
        "hook": "आज की हेल्थ अपडेट — आधिकारिक स्रोत से।",
        "narration_segments": [
            "नमस्कार। आप देख रहे हैं NUSKHALO हेल्थ अपडेट।",
            f"आज की खबर का विषय है: {title}।",
            "इस वीडियो में स्रोत की मूल जानकारी दिखाई गई है। इसे प्रकाशित करने से पहले सरल हिंदी में अनुवाद और हर स्वास्थ्य तथ्य की जाँच ज़रूरी है।",
            "यह वीडियो चिकित्सा सलाह नहीं है। स्वास्थ्य संबंधी निर्णय के लिए योग्य डॉक्टर से सलाह लें।",
        ],
        "closing": "सही जानकारी पढ़ें। सुरक्षित रहें।",
        "sources": [topic.get("source_url", "")],
        "review_status": "needs_human_translation_and_fact_check",
        "translation_required": True,
        "medical_safety_note": (
            "No diagnosis, cure claims, medication changes, or unsupported advice. "
            "Translate and verify every factual statement against the linked official source."
        )
    }
