# SVG Vectorizer

Program konversi foto (raster) menjadi SVG (vector) dari nol, untuk learning project computer graphics & image processing.

## Struktur Folder

```
SVG Vectorizer/
├── src/                        # Script Python (algoritma)
│   ├── vectorizer.py           # ★ PROGRAM UTAMA (gabungan semua tahap)
│   ├── tahap0_baseline.py      # Baseline: piksel → SVG rect
│   ├── tahap1_preprocessing.py # Grayscale, blur, threshold
│   ├── tahap2_contour_tracing.py # Moore-Neighbor tracing
│   ├── tahap3_simplification.py # Douglas-Peucker simplification
│   ├── tahap4_bezier.py        # Bezier curve fitting
│   ├── tahap5_svg_gen.py       # SVG generation (M, C, Z)
│   └── tahap6_fullcolor.py     # Full color (K-Means manual)
│
├── templates/                  # HTML template (web UI)
│   └── index.html
│
├── static/                     # CSS styling
│   └── style.css
│
├── docs/                       # Dokumentasi lengkap per tahap
│   ├── tahap0.md
│   ├── tahap1.md
│   ├── tahap2.md
│   ├── tahap3.md
│   ├── tahap4.md
│   ├── tahap5.md
│   └── tahap6.md
│
├── tests/                      # Test images & scripts
│   ├── create_test_image.py    # Generate test image berwarna
│   ├── create_test_binary.py   # Generate test image biner
│   ├── test_image.png          # Test image 64x64 (4 kotak warna)
│   └── test_binary_clean.png   # Test image biner (4 kotak hitam)
│
├── output/                     # Hasil output
│   ├── svg/                    # File SVG hasil konversi
│   ├── images/                 # Gambar intermediate (grayscale, binary, dll)
│   └── json/                   # Data kontur & bezier (untuk pipeline)
│
├── app.py                      # Flask web app (UI + upload)
├── requirements.txt            # Python dependencies
└── prompt-photo-to-svg.md      # Prompt asli project
```

## Package yang Digunakan

| Package | Versi | Fungsi |
|---------|-------|--------|
| Python 3 | 3.x | Bahasa pemrograman utama |
| NumPy | ≥1.24 | Array manipulasi & operasi numerik |
| Pillow | ≥9.0 | Load/save gambar (PNG, JPG, BMP, dll) |
| Flask | ≥3.0 | Web server untuk UI & upload |

**Tanpa** OpenCV, scikit-learn, svgwrite, rdp, shapely.

## Cara Install

```bash
pip install -r requirements.txt
```

Atau manual:

```bash
pip install numpy Pillow flask
```

## Cara Jalankan

### Via Web UI (Recommended)

```bash
# Jalankan Flask server
python app.py
```

Buka browser, ketik:

```
http://localhost
```

**Langkah pakai:**

1. Drag & drop gambar ke area upload (atau klik untuk pilih)
2. Atur pengaturan (mode, warna, epsilon, max error)
3. Klik **Konversi ke SVG**
4. Preview SVG muncul, klik **Download SVG** untuk simpan

### Via Bash / Command Line

```bash
# Masuk ke folder project
cd SVG-Vectorizer

# Jalankan vectorizer
python src/vectorizer.py <path_gambar>
```

**Contoh:**

```bash
# Pakai test image bawaan
python src/vectorizer.py tests/test_image.png

# Simpan ke folder output
python src/vectorizer.py tests/test_image.png -o output/svg/hasil.svg

# Gambar sendiri
python src/vectorizer.py D:\Foto\logo.png -o D:\Foto\logo.svg

# Hitam-putih
python src/vectorizer.py logo.png -m bw -o output.svg

# Full color 16 warna
python src/vectorizer.py photo.jpg -m color -c 16 -o output.svg

# Custom toleransi
python src/vectorizer.py icon.png -e 1.0 --max-error 3.0
```

### Opsi Command Line

| Flag          | Fungsi                      | Default                   |
| ------------- | --------------------------- | ------------------------- |
| `-o`          | Path output SVG             | otomatis (nama file sama) |
| `-m`          | Mode: `auto`, `bw`, `color` | `auto`                    |
| `-c`          | Jumlah warna (mode color)   | `8`                       |
| `-e`          | Toleransi simplifikasi (px) | `2.0`                     |
| `--max-error` | Toleransi Bezier (px)       | `2.0`                     |

## Web Interface

Fitur yang tersedia:

- **Upload** — Drag & drop atau klik untuk pilih gambar (maks 16MB)
- **Preview** — Lihat gambar sebelum dikonversi
- **Pengaturan** — Mode (auto/bw/color), jumlah warna, epsilon, max error
- **Tooltip** — Hover tanda `?` untuk penjelasan tiap pengaturan
- **Hasil** — Preview SVG langsung di halaman + download
- **Responsive** — Bisa dipakai di HP maupun desktop

Format gambar yang didukung: PNG, JPG, BMP, GIF, TIFF, WEBP.

## Algoritma yang Diimplementasikan Manual

| Algoritma              | Fungsi                    |
| ---------------------- | ------------------------- |
| Weighted Grayscale     | Konversi RGB ke grayscale |
| Gaussian Blur          | Reduksi noise             |
| Otsu Threshold         | Binerisasi otomatis       |
| Moore-Neighbor Tracing | Contour tracing           |
| Douglas-Peucker        | Polygon simplification    |
| Schneider's Method     | Bezier curve fitting      |
| K-Means Clustering     | Reduksi warna             |

## Tech Stack

- **Backend:** Python 3, Flask, NumPy, Pillow
- **Frontend:** HTML5, CSS3, JavaScript (vanilla)
- **Algoritma:** Dibuat manual tanpa library CV/ML tambahan
