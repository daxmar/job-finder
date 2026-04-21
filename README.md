# Job Finder App

Aplikasi Python berbasis GUI untuk mencari lowongan pekerjaan secara otomatis dari JobStreet Indonesia.

## Persiapan Lingkungan
1. Pastikan Python 3.10+ terinstal.
2. Buat Virtual Environment: `python -m venv venv`.
3. Aktifkan venv: 
   - Windows: `.\venv\Scripts\activate`
4. Instal dependensi: `pip install -r requirements.txt`.

## Cara Menjalankan
Jalankan perintah berikut di terminal:
```bash
python job_finder.py
```

## Fitur
- Pencarian otomatis berdasarkan Keyword dan Lokasi.
- Scraping real-time dari JobStreet.
- Detail lowongan (Deskripsi & Pertanyaan Perusahaan) diambil secara otomatis.
- Tampilan hasil dalam tabel interaktif (Double-click untuk buka link).
- Export ke **Excel** dan **PDF (Format Kartu)**.
- Progress bar dan status update.
- Error handling dan retry.

## Sites Scraped
- JobStreet Indonesia (query: job_type + " " + location)

## Notes
- Menggunakan **Microsoft Edge** (Default di Windows).
- Jika offline, letakkan `msedgedriver.exe` di folder yang sama dengan skrip.

## Distribusi (Membuat .EXE)
Untuk membuat file executable tanpa perlu instal Python di komputer lain:
```bash
pip install pyinstaller
pyinstaller --noconsole --onefile --add-data "msedgedriver.exe;." job_finder.py
```
