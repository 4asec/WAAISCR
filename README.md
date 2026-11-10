# 🔗 Link Curator

AI pribadi modular yang menerima link/PDF/catatan lewat WhatsApp, membaca, merangkum, menganalisis, mengevaluasi, dan mengelompokkannya ke tema bernomor secara stabil.

---

## 🚀 Fitur Utama Fase 1

- **Pemisahan Modul & Core**: Core independen dari modul; penambahan modul masa depan cukup ditaruh di `modules/<nama_modul>/`.
- **Gateway WhatsApp Fleksibel (Baileys HTTP Bridge)**:
  - Penautan via **QR Code** langsung di terminal.
  - Penautan via **Pairing Code (8 digit)** tanpa scan kamera.
  - Penyimpanan sesi di `auth/whatsapp_session` (otomatis resume saat restart).
  - Reconnect otomatis dengan *exponential backoff* dan pembersihan sesi usang jika *logged out*.
- **Pembersihan URL & Deteksi Platform**: Ekstraksi link otomatis, pembersihan parameter pelacak (*tracking/UTM*), dan deteksi platform.
- **Rantai Ekstraksi Konten (*Fetcher Chain*)**: Ekstraksi artikel web, metadata OpenGraph, GitHub API, dan Reddit JSON.
- **Analisis AI Terstruktur (Gemini API / Ollama Stub)**: Evaluasi objektif, manfaat, risiko, skor 1–5, dan istilah kunci bahasa Inggris (🔹*term*).
- **Proteksi Prompt Injection**: Konten web dibungkus batas ketat `<untrusted_content>` dan disanitasi.
- **Keamanan Whitelist**: Hanya nomor terdaftar yang diproses, nomor lain diabaikan diam-diam.
- **FastAPI Web Dashboard & Endpoint `/health`**: Siap dipantau dari browser atau mikrokontroler IoT (ESP32).

---

## 📱 Panduan Penautan Akun WhatsApp (Linked Device)

Link Curator dapat ditautkan ke akun WhatsApp Anda sebagai **Perangkat Tertaut (*Linked Device*)** dengan dua metode:

### Metode 1: QR Code (Default)
1. Atur di `config.yaml` atau `.env`:
   ```yaml
   whatsapp:
     auth_method: "qr"
   ```
2. Jalankan gateway WhatsApp:
   ```powershell
   cd "D:\Project Kodingan Raffa\link-curator\gateway\whatsapp"
   npm start
   ```
3. Di HP Anda:
   - Buka **WhatsApp** → Ketuk **Titik Tiga / Pengaturan** (pojok kanan atas).
   - Pilih **Perangkat tertaut** (*Linked devices*).
   - Ketuk **Tautkan perangkat** (*Link a device*).
   - Arahkan kamera HP ke **QR Code** yang muncul di terminal.

### Metode 2: Pairing Code 8 Digit (Tanpa Scan Kamera)
Sangat berguna jika kamera HP bermasalah atau menjalankan bot di server/VPS.
1. Atur di `config.yaml` atau `.env`:
   ```yaml
   whatsapp:
     auth_method: "pairing"
     phone_number: "6281234567890" # Ganti dengan nomor WhatsApp HP Anda
   ```
2. Jalankan gateway WhatsApp:
   ```powershell
   cd "D:\Project Kodingan Raffa\link-curator\gateway\whatsapp"
   npm start
   ```
3. Terminal akan menampilkan kode 8 karakter, contoh: `ABCD-1234`.
4. Di HP Anda:
   - Buka **WhatsApp** → **Perangkat tertaut** → **Tautkan perangkat**.
   - Pilih opsi **"Tautkan dengan nomor telepon saja"** (*Link with phone number instead*).
   - Masukkan 8 karakter kode yang tertera di terminal.

> ⚠️ **Catatan Penting Keaktifan HP (Aturan 14 Hari WhatsApp):**
> Sesuai ketentuan resmi WhatsApp, perangkat tertaut (*Linked Device*) akan otomatis terputus (*logged out*) jika HP utama Anda tidak pernah online sama sekali selama **14 hari berturut-turut**. Pastikan HP utama Anda tetap terkoneksi internet sesekali agar sesi bot tidak kedaluwarsa.

---

## 🛠️ Cara Menjalankan

### 1. Salin Environment & Masukkan Gemini API Key
```powershell
cd "D:\Project Kodingan Raffa\link-curator"
Copy-Item .env.example .env
```
Buka file `.env` dan masukkan API key Gemini Anda:
```env
GEMINI_API_KEY=AIzaSy...
```

### 2. Atur Whitelist Nomor Anda
Buka `config.yaml` dan tambahkan nomor WhatsApp Anda:
```yaml
whitelist:
  phone_numbers:
    - "628xxxxxxxxxx"
```

### 3. Jalankan Gateway WhatsApp (Terminal 1)
```powershell
cd "D:\Project Kodingan Raffa\link-curator\gateway\whatsapp"
npm start
```

### 4. Jalankan Python Core & Dashboard (Terminal 2)
```powershell
cd "D:\Project Kodingan Raffa\link-curator"
.\.venv\Scripts\python main.py
```
- Dashboard lokal dapat diakses di: `http://127.0.0.1:8000/`
- Endpoint status kesehatan: `http://127.0.0.1:8000/health`

---

## 🧪 Menjalankan Pengujian (Unit Tests)

```powershell
cd "D:\Project Kodingan Raffa\link-curator"
.\.venv\Scripts\pytest
```
Semua unit test diuji secara otomatis mencakup URL normalization, platform detection, security boundaries, command router, dan whitelist matching.
