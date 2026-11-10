# Command Reference - Link Curator

Semua perintah berawalan tanda garis miring (`/`) dan didaftarkan melalui *command registry* terpusat.

| Perintah | Format / Penggunaan | Modul | Deskripsi |
|---|---|---|---|
| `/bantuan` | `/bantuan` (alias: `/help`, `/?`) | `core` | Menampilkan seluruh daftar perintah yang aktif terdaftar di sistem. |
| `/status` | `/status` | `core` | Menampilkan status koneksi WhatsApp Gateway, LLM, Whitelist, dan Environment. |
| `/daftar` | `/daftar` | `link_curator` | Menampilkan daftar seluruh tema bernomor dan item di dalamnya (Fase 2). |
| `/tema` | `/tema <nama_atau_nomor>` | `link_curator` | Melihat daftar item di bawah tema tertentu (Fase 2). |
| `/item` | `/item <nomor>` | `link_curator` | Membuka detail lengkap suatu item berdasarkan nomor stabil (Fase 2). |
| `/pindah` | `/pindah <nomor> <tema>` | `link_curator` | Memindahkan item ke tema lain (Fase 2). |
| `/hapus` | `/hapus <nomor>` | `link_curator` | Menghapus item dari database tanpa merusak penomoran item lain (Fase 2). |
| `/ya` | `/ya` | `link_curator` | Menyetujui usulan penempatan tema dari antrean konfirmasi (Fase 2). |
| `/tidak` | `/tidak` | `link_curator` | Menolak usulan penempatan tema dari antrean konfirmasi (Fase 2). |
| `/nilai` | `/nilai <nomor> <1-5> [catatan]` | `link_curator` | Memberikan skor umpan balik dan catatan personal untuk evaluasi minat (Fase 3). |
| `/cari` | `/cari <kata_kunci>` | `link_curator` | Melakukan pencarian cepat Full-Text Search (FTS5) pada seluruh catatan tersimpan (Fase 4). |
| `/rekap` | `/rekap [minggu\|bulan]` | `link_curator` | Membuat rekap rangkuman kurasi berkala (Fase 4). |
| `/impor` | `/impor` | `link_curator` | Mengimpor file riwayat chat ekspor WhatsApp (.txt) secara bertahap dan idempoten (Fase 5). |

---

## Pesan Bebas (Tanpa Awalan `/`)
Pesan teks biasa tanpa awalan `/` akan otomatis diproses sebagai:
1. **Tautan Web / URL**: Otomatis diekstrak, dibersihkan dari parameter tracking, dibaca isinya, dianalisis AI secara kritis, dan dibalas dengan format Meta AI.
2. **Pertanyaan Bebas**: Dijawab langsung oleh AI secara kritis dan santai.
