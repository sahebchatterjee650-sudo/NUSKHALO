def build_script(topic, config):
    # Source-grounded draft only. Do not invent or medically interpret claims.
    return {
        "brand": config.get("brand", "NUSKHALO"),
        "language": "hi",
        "topic": topic["title"],
        "source_summary_original": topic.get("summary", ""),
        "published_at": topic.get("published", ""),
        "source_domain": topic.get("source_domain", ""),
        "hook": "आज की स्वास्थ्य जानकारी सीधे एक आधिकारिक स्रोत से।",
        "body": (
            "नीचे दिया गया विवरण स्रोत के मूल सारांश पर आधारित है। "
            "वीडियो बनाने से पहले इसे सरल हिंदी में अनुवाद करें और मूल स्रोत से "
            "हर तथ्य की जाँच करें। बिना प्रमाण किसी इलाज, घरेलू नुस्खे या दवा की "
            "सलाह न दें।"
        ),
        "closing": "स्वास्थ्य संबंधी निर्णय के लिए योग्य स्वास्थ्यकर्मी से सलाह लें।",
        "sources": [topic.get("source_url", "")],
        "review_status": "needs_human_translation_and_fact_check",
        "translation_required": True,
        "medical_safety_note": (
            "No diagnosis, cure claims, medication changes, or unsupported advice. "
            "Check every factual statement against the linked official source."
        )
    }
