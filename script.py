def build_script(topic, config):
    # Safe draft template. Replace with a carefully validated Hindi research workflow.
    # No unsupported cure claims are generated here.
    title = topic["title"]
    return {
        "brand": config.get("brand", "NUSKHALO"),
        "language": "hi",
        "topic": title,
        "hook": "क्या आपने इस स्वास्थ्य विषय के बारे में सही जानकारी सुनी है?",
        "body": (
            "आज हम इस विषय पर उपलब्ध विश्वसनीय जानकारी समझेंगे। "
            "घरेलू उपाय हर व्यक्ति के लिए सुरक्षित या प्रभावी हों, यह जरूरी नहीं। "
            "किसी बीमारी के इलाज या दवा में बदलाव के लिए योग्य डॉक्टर से सलाह लें।"
        ),
        "closing": "ऐसी जानकारी के लिए NUSKHALO को फॉलो करें।",
        "sources": [topic.get("source_url", "")],
        "review_status": "needs_human_review",
        "medical_safety_note": (
            "Do not claim cure, diagnose, recommend medication changes, or omit urgent-care advice. "
            "Verify claims against authoritative clinical/public-health sources."
        )
    }
