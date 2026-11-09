from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class CuratedItemAnalysis(BaseModel):
    """Pydantic schema for structured LLM analysis output."""
    title: str = Field(description="Judul konten yang ringkas, akurat, dan representatif")
    short_summary: str = Field(description="Ringkasan singkat 2-3 kalimat inti bahasan")
    simple_explanation: str = Field(description="Penjelasan sederhana: apa itu dan bagaimana cara kerjanya")
    key_benefits: List[str] = Field(default_factory=list, description="Poin manfaat utama (maksimal 3-4 poin)")
    drawbacks_or_risks: List[str] = Field(default_factory=list, description="Kekurangan, keterbatasan, atau risiko potensial")
    attention_score: int = Field(ge=1, le=5, description="Skor layak diperhatikan 1 (rendah) sampai 5 (sangat penting)")
    score_reason: str = Field(description="Alasan objektif mengapa skor tersebut diberikan")
    critical_notes: str = Field(description="Catatan evaluasi kritis: konteks nyata, batasan, atau hype check")
    suggested_theme: str = Field(description="Kandidat tema/kategori (contoh: AI, Cybersecurity, Web Development, Productivity)")
    confidence: float = Field(ge=0.0, le=1.0, description="Tingkat keyakinan penempatan tema (0.0 sampai 1.0)")
    important_terms: List[str] = Field(default_factory=list, description="Daftar 1-3 istilah teknis penting dalam bahasa Inggris")
