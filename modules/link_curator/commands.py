from core.config import settings
from core.router import CommandContext, router
from adapters.channel.whatsapp_baileys import WhatsAppBaileysAdapter

wa_adapter = WhatsAppBaileysAdapter()

@router.register(
    name="bantuan",
    description="Menampilkan panduan perintah yang tersedia",
    usage="/bantuan",
    module="core",
    aliases=["help", "?", "bantu"]
)
async def cmd_bantuan(ctx: CommandContext) -> str:
    commands = router.get_all_commands()
    lines = ["🤖 *DAFTAR PERINTAH LINK CURATOR*\n"]
    for name, meta in sorted(commands.items()):
        lines.append(f"• `{meta.usage}` : {meta.description}")
    lines.append("\n_Catatan: Kirim langsung tautan/link web apa saja untuk otomatis dirangkum dan dianalisis._")
    return "\n".join(lines)

@router.register(
    name="status",
    description="Memeriksa status gateway WhatsApp, LLM, dan sistem",
    usage="/status",
    module="core"
)
async def cmd_status(ctx: CommandContext) -> str:
    wa_status = await wa_adapter.get_status()
    status_label = wa_status.get("status", "unknown")

    if status_label == "connected":
        conn_text = "🟢 Terhubung (*Connected*)"
    elif status_label == "reconnecting":
        conn_text = "🟡 Menghubungkan ulang (*Reconnecting*)"
    elif status_label == "logged_out":
        conn_text = "🔴 Sesi habis (*Logged out*) - Butuh tautkan ulang"
    else:
        conn_text = f"⚪ Offline ({wa_status.get('error', 'Gateway tidak aktif')})"

    lines = [
        "📊 *STATUS SISTEM LINK CURATOR*",
        f"• WhatsApp Gateway: {conn_text}",
        f"• Metode Auth: `{settings.whatsapp.auth_method.upper()}`",
        f"• Model LLM: `{settings.llm.model}` (Provider: {settings.llm.provider})",
        f"• Whitelist: `{len(settings.whitelist.phone_numbers)} nomor terdaftar`",
        f"• Environment: `{settings.app.env}`"
    ]
    return "\n".join(lines)

# Stubs for remaining commands to be fully implemented in Phase 2-5
@router.register("daftar", "Menampilkan daftar seluruh tema dan item", "/daftar", "link_curator")
async def cmd_daftar(ctx: CommandContext) -> str:
    return "📚 Fitur `/daftar` tema & item sedang dipersiapkan di Fase 2."

@router.register("tema", "Melihat item dalam suatu tema", "/tema <nama_atau_nomor>", "link_curator")
async def cmd_tema(ctx: CommandContext) -> str:
    return "📂 Fitur `/tema` sedang dipersiapkan di Fase 2."

@router.register("item", "Melihat detail item tertentu", "/item <nomor>", "link_curator")
async def cmd_item(ctx: CommandContext) -> str:
    return "📄 Fitur `/item` sedang dipersiapkan di Fase 2."

@router.register("cari", "Mencari catatan/link berdasarkan kata kunci", "/cari <kata_kunci>", "link_curator")
async def cmd_cari(ctx: CommandContext) -> str:
    return "🔍 Fitur `/cari` FTS5 sedang dipersiapkan di Fase 4."

@router.register("rekap", "Melihat rekap berkala", "/rekap [minggu|bulan]", "link_curator")
async def cmd_rekap(ctx: CommandContext) -> str:
    return "📊 Fitur `/rekap` berkala sedang dipersiapkan di Fase 4."

@router.register("pindah", "Memindahkan item ke tema lain", "/pindah <nomor> <tema>", "link_curator")
async def cmd_pindah(ctx: CommandContext) -> str:
    return "🔄 Fitur `/pindah` tema sedang dipersiapkan di Fase 2."

@router.register("hapus", "Menghapus item tertentu", "/hapus <nomor>", "link_curator")
async def cmd_hapus(ctx: CommandContext) -> str:
    return "🗑️ Fitur `/hapus` sedang dipersiapkan di Fase 2."

@router.register("nilai", "Memberi rating & evaluasi pada item", "/nilai <nomor> <1-5> [catatan]", "link_curator")
async def cmd_nilai(ctx: CommandContext) -> str:
    return "⭐ Fitur `/nilai` umpan balik sedang dipersiapkan di Fase 3."

@router.register("ya", "Menyetujui usulan pengelompokan tema", "/ya", "link_curator")
async def cmd_ya(ctx: CommandContext) -> str:
    return "✅ Fitur konfirmasi antrean `/ya` sedang dipersiapkan di Fase 2."

@router.register("tidak", "Menolak usulan pengelompokan tema", "/tidak", "link_curator")
async def cmd_tidak(ctx: CommandContext) -> str:
    return "❌ Fitur konfirmasi antrean `/tidak` sedang dipersiapkan di Fase 2."

@router.register("impor", "Impor riwayat chat WhatsApp export (.txt)", "/impor", "link_curator")
async def cmd_impor(ctx: CommandContext) -> str:
    return "📥 Fitur `/impor` backlog chat export sedang dipersiapkan di Fase 5."
