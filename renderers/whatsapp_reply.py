import re
from typing import List, Optional
from core.config import settings
from modules.link_curator.schemas import CuratedItemAnalysis

class WhatsAppReplyRenderer:
    """Formats structured curated analysis into engaging, Meta AI style WhatsApp messages."""

    @staticmethod
    def format_analysis(analysis: CuratedItemAnalysis, item_number: Optional[str] = None) -> str:
        badge = settings.formatting.term_badge
        bold = settings.formatting.bold_terms

        # Format terms helper
        def style_term(term: str) -> str:
            clean = term.strip()
            return f"{badge}*{clean}*" if bold else f"{badge}{clean}"

        # Build term footnotes/highlights if terms exist
        terms_line = ""
        if analysis.important_terms:
            styled_terms = [style_term(t) for t in analysis.important_terms]
            terms_line = f"🔹 *Istilah Kunci:* {', '.join(styled_terms)}\n\n"

        # Star rating display
        stars = "⭐" * analysis.attention_score + "☆" * (5 - analysis.attention_score)

        # Header with optional stable item number
        header = f"📌 *{analysis.title}*"
        if item_number:
            header = f"📌 *[{item_number}] {analysis.title}*"

        # Key benefits list
        benefits_str = ""
        if analysis.key_benefits:
            bullets = [f"  • {b.strip()}" for b in analysis.key_benefits if b.strip()]
            benefits_str = "\n".join(bullets)

        # Drawbacks list
        drawbacks_str = ""
        if analysis.drawbacks_or_risks:
            bullets = [f"  • {d.strip()}" for d in analysis.drawbacks_or_risks if d.strip()]
            drawbacks_str = "\n".join(bullets)

        message = (
            f"{header}\n\n"
            f"💡 *Ringkasan Singkat:*\n{analysis.short_summary}\n\n"
            f"🔍 *Cara Kerja & Konteks:*\n{analysis.simple_explanation}\n\n"
        )

        if benefits_str:
            message += f"🚀 *Manfaat Utama:*\n{benefits_str}\n\n"

        if drawbacks_str:
            message += f"⚠️ *Perlu Diperhatikan:*\n{drawbacks_str}\n\n"

        message += (
            f"📊 *Skor Rekomendasi:* {stars} ({analysis.attention_score}/5)\n"
            f"💬 *Alasan & Evaluasi Kritis:* {analysis.score_reason}. {analysis.critical_notes}\n\n"
            f"🏷️ *Kandidat Tema:* {analysis.suggested_theme} (Keyakinan: {int(analysis.confidence * 100)}%)\n\n"
            f"{terms_line}"
        )

        return message.strip()

    @staticmethod
    def format_fetch_failed(url: str, platform: str, reason: Optional[str] = None) -> str:
        """Friendly message when content could not be read automatically."""
        return (
            f"Maaf, aku belum berhasil membaca otomatis isi dari tautan ({platform}):\n"
            f"`{url}`\n\n"
            "Bisa bantu kirimkan rangkuman singkat, *caption*, atau tangkapan layarnya? "
            "Biar tetap bisa aku analisis dan simpan ke kurasi catatanmu! 📝"
        )
