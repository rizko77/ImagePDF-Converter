# ImagePDF Converter

Aplikasi desktop Windows untuk mengubah halaman PDF menjadi JPG, PNG, TIF, PSD, CDR, atau AI. Antarmuka dibuat dengan HTML dan berjalan di jendela `pywebview`.

Setiap halaman PDF menghasilkan satu berkas. Jika memilih lebih dari satu PDF, seluruh hasil akan dikemas otomatis ke satu berkas ZIP di folder keluaran.

## Fitur

- Memilih satu atau beberapa berkas PDF sekaligus.
- Menampilkan jumlah halaman dan ukuran setiap PDF sebelum konversi.
- Mengatur resolusi render 150, 200, 300, atau 600 DPI.
- Mengatur kualitas JPG dari 60 sampai 100 (nilai awal 92).
- Memilih format JPG, PNG, TIF, PSD, CDR, atau AI.
- Melihat kemajuan konversi dan membuka folder hasil dari aplikasi.

Format PSD dibuat sebagai gambar RGB 8-bit yang sudah diratakan (flatten). Format CDR berisi gambar PNG yang ditempatkan pada satu halaman. Berkas AI yang dihasilkan adalah PDF satu halaman yang dapat dibuka di Adobe Illustrator, bukan dokumen AI berisi objek vektor hasil konversi.

## Struktur proyek

```text
ImageConverter/
├── main.py                    # Logika aplikasi dan konversi PDF
├── templates/
│   └── index.html             # Antarmuka aplikasi
├── img/
│   ├── ikon.ico               # Ikon Windows
│   ├── ikon.png               # Ikon pada antarmuka
│   └── splash.png             # Gambar splash screen
├── ImagePDF Converter.spec    # Konfigurasi build PyInstaller
├── app.manifest               # Manifest aplikasi Windows
├── version.txt                # Informasi versi berkas Windows
├── requirements.txt           # Dependensi Python
└── README.md
```

Folder `build/` dan `dist/` dibuat oleh PyInstaller. Keduanya bukan sumber aplikasi dan dapat dibuat ulang saat proses build.

## Persyaratan

- Windows 10 atau Windows 11.
- Python 3.10 atau lebih baru. Build yang ada di proyek dibuat dengan Python 3.12; gunakan Python 3.12 untuk hasil build yang paling mendekati.
- Microsoft Edge WebView2 Runtime agar jendela `pywebview` dapat ditampilkan. Runtime ini biasanya sudah tersedia di Windows 10/11. Jika jendela aplikasi tidak terbuka, pasang WebView2 Runtime dari situs resmi Microsoft.

## Instalasi dan menjalankan dari kode sumber

Buka PowerShell pada folder proyek, lalu buat dan aktifkan virtual environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Jika PowerShell menolak aktivasi skrip, jalankan perintah berikut pada sesi tersebut, lalu aktifkan kembali virtual environment:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Pasang paket yang dibutuhkan:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Jalankan aplikasi:

```powershell
python main.py
```

## Cara menggunakan

1. Klik **Tambah Berkas PDF** dan pilih satu atau beberapa PDF.
2. Pilih format keluaran. Untuk JPG, atur kualitas sesuai kebutuhan.
3. Pilih resolusi DPI. DPI lebih tinggi menghasilkan gambar lebih besar dan proses lebih lama.
4. Klik **Telusuri** untuk memilih folder keluaran.
5. Klik **Konversi Sekarang**.
6. Setelah konversi selesai, gunakan tombol **Buka** untuk melihat folder hasil.

Nama hasil mengikuti pola `nama_pdf_page_nomor.ext`, misalnya `dokumen_page_1.jpg`. Jika beberapa PDF dipilih, ZIP diberi nama `Hasil_Konversi_YYYYMMDD_HHMMSS.zip`.

## Build menjadi EXE

Build menggunakan PyInstaller dan berkas `ImagePDF Converter.spec`. Konfigurasi tersebut mengumpulkan folder `templates` dan `img`, memakai ikon `img/ikon.ico`, splash screen `img/splash.png`, `app.manifest`, serta `version.txt`.

Pastikan virtual environment aktif dan paket pada `requirements.txt` sudah terpasang. Jalankan:

```powershell
pyinstaller --clean --noconfirm "ImagePDF Converter.spec"
```

Hasilnya adalah aplikasi mode **one-folder** (EXE beserta berkas pendukung), bukan satu EXE mandiri. Jalankan:

```text
dist\ImagePDF Converter\ImagePDF Converter.exe
```

Untuk membagikan aplikasi, salin seluruh folder `dist\ImagePDF Converter`, bukan hanya EXE-nya. Build perlu dilakukan di Windows. Paket hasil build menyertakan runtime Python dan dependensi sehingga komputer tujuan tidak perlu memasang Python. WebView2 Runtime tetap perlu tersedia di Windows.

Jika ingin membangun ulang dari kondisi bersih, hapus folder `build` dan `dist` secara manual sebelum menjalankan perintah build. Jangan hapus `img` atau `templates`; keduanya diperlukan saat packaging.

## Catatan

- Kode konversi menerima DPI 72 sampai 600. Antarmuka menyediakan pilihan 150, 200, 300, dan 600.
- DPI tinggi, PDF dengan banyak halaman, dan berkas besar membutuhkan lebih banyak waktu serta memori.
- Pemrosesan PDF dilakukan secara lokal oleh aplikasi.
