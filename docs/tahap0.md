# Tahap 0 — Baseline: Konversi Piksel ke SVG Rectangles

## Ringkasan

Tahap ini adalah versi **paling sederhana** dari Photo-to-SVG Converter. Setiap blok piksel pada gambar asli dikonversi menjadi satu elemen `<rect>` (kotak) di SVG. Tidak ada tracing, tidak ada optimasi — hanya konversi langsung piksel → kotak.

**Tujuan utama:** Memastikan pipeline end-to-end (load gambar → proses → output SVG) berjalan sebelum masuk ke algoritma yang lebih kompleks.

---

## Apa yang Dilakukan Program

### Alur Kerja (Pipeline)

```
Gambar Input (PNG/JPG) 
    ↓
Load ke array NumPy (RGB)
    ↓
Bagi jadi blok NxN piksel
    ↓
Hitung warna rata-rata tiap blok
    ↓
Buat elemen <rect> di SVG
    ↓
Simpan ke file .svg
```

### Langkah Detail

#### 1. Load Gambar (`load_image`)
- Program membaca gambar menggunakan **Pillow** (PIL).
- Gambar dikonversi ke mode **RGB** agar konsisten (handle gambar RGBA/grayscale).
- Hasilnya adalah array NumPy 3D dengan shape `(height, width, 3)` — 3 channel untuk R, G, B.

#### 2. Pembagian Blok (`image_to_svg_blocks`)
- Gambar dibagi menjadi **grid** berukuran `block_size × block_size` piksel.
- Misal gambar 100×80 dengan `block_size=8`:
  - Kolom = ceil(100/8) = **13 blok** (sisa 4 piksel di tepi kanan tetap jadi 1 blok)
  - Baris = ceil(80/8) = **10 blok**

#### 3. Hitung Warna Rata-rata (`get_block_color`)
- Untuk tiap blok, program mengambil semua piksel di dalamnya.
- Dihitung **rata-rata** untuk tiap channel (R, G, B) secara terpisah.
- Contoh: blok berisi piksel merah (255,0,0) dan putih (255,255,255) → rata-rata = (255, 128, 128) → warna merah muda.

#### 4. Konversi ke Hex (`rgb_to_hex`)
- Nilai RGB (0-255) dikonversi ke format **heksadesimal** (#RRGGBB).
- Contoh: (255, 128, 0) → `#ff8000`.
- Format ini standar digunakan di SVG/CSS.

#### 5. Generate SVG
- Program menulis SVG secara manual (string concatenation), **tanpa library `svgwrite`**.
- Struktur SVG:
  ```xml
  <svg xmlns="..." width="W" height="H" viewBox="0 0 W H">
    <rect width="100%" height="100%" fill="white"/>  <!-- background putih -->
    <rect x="0" y="0" width="8" height="8" fill="#ff0000"/>
    <rect x="8" y="0" width="8" height="8" fill="#00ff00"/>
    ...
  </svg>
  ```
- Background putih ditambahkan karena SVG default-nya transparan.

---

## Parameter

| Parameter | Default | Keterangan |
|-----------|---------|------------|
| `image_path` | (wajib) | Path ke gambar input |
| `block_size` | 8 | Ukuran blok NxN piksel. Semakin besar = semakin "pixelated" |
| `output_path` | otomatis | Path output SVG |

### Pengaruh `block_size`

| `block_size` | Blok (64×64) | Efek |
|--------------|--------------|------|
| 4 | 256 | Detail lebih banyak, file SVG lebih besar |
| 8 | 64 | Seimbang (default) |
| 16 | 16 | Sangat pixelated, file kecil |
| 32 | 4 | Sangat kasar |

---

## Cara Menjalankan

```bash
# Dengan block_size default (8)
python tahap0_baseline.py logo.png

# Dengan block_size custom
python tahap0_baseline.py logo.png 16 output.svg

# Dengan test image
python create_test_image.py          # Buat test_image.png dulu
python tahap0_baseline.py test_image.png 8 output.svg
```

---

## Contoh Output

Untuk gambar test 64×64 dengan 4 kotak warna (merah, biru, hijau, kuning):

```
Gambar dimuat: 64x64 piksel
Grid blok: 8 kolom x 8 baris (block_size=8)
SVG berhasil dibuat: output.svg
Total elemen <rect>: 64
```

Setiap kotak 8×8 pada gambar asli → 1 `<rect>` di SVG dengan warna rata-rata.

---

## Konsep Matematika

### Rata-rata Warna (Mean RGB)

$$\bar{R} = \frac{1}{N} \sum_{i=1}^{N} R_i, \quad \bar{G} = \frac{1}{N} \sum_{i=1}^{N} G_i, \quad \bar{B} = \frac{1}{N} \sum_{i=1}^{N} B_i$$

Di mana $N$ = jumlah piksel dalam blok (biasanya `block_size²`).

### Ceiling Division

Untuk menghitung jumlah blok yang dibutuhkan:

$$\text{cols} = \lceil \frac{\text{width}}{\text{block\_size}} \rceil = \frac{\text{width} + \text{block\_size} - 1}{\text{block\_size}}$$

Dibulatkan ke atas karena sisa piksel yang tidak muat di blok utuh tetap harus diwakili satu blok tambahan.

---

## Edge Cases / Potensi Masalah

| Masalah | Penjelasan | Solusi |
|---------|------------|--------|
| Gambar RGBA | Gambar PNG transparan punya 4 channel | Konversi ke RGB dulu |
| Gambar grayscale | Hanya 1 channel | Konversi ke RGB dulu |
| Ukuran tidak habis dibagi | Blok tepi tidak utuh | `min()` untuk batasi width/height blok |
| Background transparan | SVG default transparan | Tambah rect putih di belakang |

---

## File yang Dihasilkan

| File | Keterangan |
|------|------------|
| `tahap0_baseline.py` | Script utama Tahap 0 |
| `create_test_image.py` | Generator test image |
| `output.svg` | Hasil konversi |

---

## Limitasi Tahap Ini

1. **Tidak ada tracing** — setiap blok jadi kotak terpisah, tidak ada kontur.
2. **Tidak ada optimasi** — file SVG bisa besar untuk gambar resolusi tinggi.
3. **Tidak ada smoothing** — hasilnya selalu "pixelated".
4. **Hanya untuk gambar sederhana** — logo, ikon, siluet. Foto realistis hasilnya kurang bagus.

**Tahap selanjutnya** akan menambahkan tracing (Tahap 2), simplifikasi (Tahap 3), dan curve fitting (Tahap 4) untuk menghasilkan SVG yang lebih smooth dan efisien.
