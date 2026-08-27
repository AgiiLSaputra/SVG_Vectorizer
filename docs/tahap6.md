# Tahap 6 — Full Color (K-Means Clustering Manual)

## Ringkasan

Tahap ini adalah **tahap lanjutan** yang menambahkan dukungan **warna penuh** ke SVG. Caranya:
1. **K-Means clustering** (tanpa scikit-learn!) untuk mengurangi warna gambar jadi N warna.
2. Pisahkan tiap warna jadi **layer biner**.
3. Jalankan **Tahap 2-5** untuk tiap layer.
4. Gabungkan semua path jadi **satu SVG berwarna**.

**Tujuan utama:** Menghasilkan SVG yang **mirip dengan gambar asli** (berwarna), bukan hanya siluet hitam-putih.

---

## Apa yang Dilakukan Program

### Alur Kerja

```
Gambar Berwarna (RGB)
    ↓
K-Means Clustering (reduksi warna)
    ↓
N Klaster Warna (centroid)
    ↓
Pisahkan per warna → N Layer Biner
    ↓
Untuk tiap layer:
    Tahap 2: Contour Tracing
    Tahap 3: Simplification
    Tahap 4: Bezier Fitting
    Tahap 5: SVG Path Generation
    ↓
Gabungkan semua path + warna
    ↓
SVG Berwarna (file .svg)
```

---

## MATEMATIKA: K-Means Clustering

### Apa itu K-Means?

**K-Means** adalah algoritma **unsupervised learning** untuk mengelompokkan data jadi K klaster.

Di konteks ini:
- **Data** = piksel-piksel gambar (koordinat warna RGB)
- **K** = jumlah klaster (jumlah warna yang diinginkan)
- **Output** = label klaster tiap piksel + centroid (warna rata-rata tiap klaster)

### Algoritma K-Means

```
LANGKAH 1: Inisialisasi
  - Pilih K titik secara ACAK dari data → jadi centroid awal

LANGKAH 2: Ulangi sampai konvergen:
  a. ASSIGN: Untuk tiap data, hitung jarak ke SEMUA centroid.
             Pilih centroid TERDEKAT → data itu masuk klaster itu.
  
  b. UPDATE: Pindahkan centroid ke TENGAH-TENGAH (rata-rata)
             semua data di klaster itu.

  c. CEK: Jika perubahan centroid < toleransi → BERHENTI.

LANGKAH 3: Return label + centroid
```

### Jarak: Euclidean Distance

Untuk menentukan piksel mana yang "mirip" warnanya:

$$d = \sqrt{(R_1 - R_2)^2 + (G_1 - G_2)^2 + (B_1 - B_2)^2}$$

Contoh:
- Merah (255, 0, 0) vs Biru (0, 0, 255): $d = \sqrt{255^2 + 0 + 255^2} = 360.6$ (jauh)
- Merah (255, 0, 0) vs Merah Muda (255, 128, 128): $d = \sqrt{0 + 128^2 + 128^2} = 181.0$ (dekat)

### Konvergensi

K-Means berhenti ketika:
- Perubahan centroid antar iterasi **sangat kecil** (< toleransi), ATAU
- Mencapai **maksimum iterasi**

---

## MATEMATIKA: Euclidean Distance dalam Ruang Warna

### Konsep

Piksel warna bisa dianggap sebagai **titik** dalam ruang 3D (R, G, B):

```
B (Biru)
│
│   * (128, 0, 255) — ungu
│
│   * (255, 0, 0) — merah
│
└──────────────── R (Merah)
/
G (Hijau)
```

Jarak antara dua warna = jarak Euclidean antara dua titik dalam ruang 3D.

### Mengapa Euclidean?

- **Sederhana** — mudah dihitung dan dipahami.
- **Cukup bagus** — untuk kebanyakan gambar.
- **Standar** — paling banyak digunakan di K-Means.

---

## Layer Biner

### Konsep

Setelah K-Means selesai, tiap piksel punya **label klaster** (0 sampai K-1). Kita pisahkan jadi **K layer biner**:

```
Gambar asli (4 warna):      Layer merah (klaster 0):
┌───┬───┬───┬───┐          ┌───┬───┬───┬───┐
│ M │ M │ B │ B │          │ 0 │ 0 │ 1 │ 1 │  0 = merah
├───┼───┼───┼───┤    →     ├───┼───┼───┼───┤  1 = bukan merah
│ M │ M │ B │ B │          │ 0 │ 0 │ 1 │ 1 │
├───┼───┼───┼───┤          ├───┼───┼───┼───┤
│ G │ G │ H │ H │          │ 1 │ 1 │ 1 │ 1 │  (tidak ada merah)
├───┼───┼───┼───┤          ├───┼───┼───┼───┤
│ G │ G │ H │ H │          │ 1 │ 1 │ 1 │ 1 │
└───┴───┴───┴───┘          └───┴───┴───┴───┘

M = Merah, B = Biru, G = Hijau, H = Kuning
```

Setiap layer kemudian di-trace, disederhanakan, dan di-fit Bezier secara terpisah.

---

## Parameter

| Parameter | Default | Keterangan |
|-----------|---------|------------|
| `image_path` | (wajib) | Path ke gambar input |
| `n_colors` | 8 | Jumlah warna (klaster) |
| `epsilon` | 2.0 | Toleransi simplifikasi (piksel) |
| `max_error` | 2.0 | Toleransi Bezier (piksel) |

### Pengaruh `n_colors`

| Warna | Efek |
|-------|------|
| 4 | Sangat direduksi, efek posterisasi kuat |
| 8 | Seimbang (default) |
| 16 | Detail lebih banyak |
| 32 | Hampir seperti asli |
| 64 | Sangat detail, file besar |

---

## Cara Menjalankan

```bash
# Default (8 warna)
python tahap6_fullcolor.py test_image.png

# Custom warna dan toleransi
python tahap6_fullcolor.py photo.jpg 16 3.0 3.0
```

---

## Output yang Dihasilkan

| File | Keterangan |
|------|------------|
| `*_reduced_N.png` | Gambar dengan warna sudah direduksi |
| `*_fullcolor.svg` | SVG berwarna (file akhir) |

---

## Contoh Output

```
Gambar dimuat: 64x64

--- K-Means Clustering (K=4) ---
K-Means: 4096 piksel, 4 klaster, max 50 iterasi
  Konvergen di iterasi 3 (shift=0.000000)

Distribusi klaster:
  Klaster 0: rgb(255,0,0) #ff0000 = 15.3%
  Klaster 1: rgb(0,0,255) #0000ff = 15.3%
  Klaster 2: rgb(127,191,0) #7fbf00 = 30.5%
  Klaster 3: rgb(255,255,255) #ffffff = 39.0%

--- Proses Tiap Layer ---
  rgb(255,0,0) #ff0000: 1 kontur -> 2 kurva
  rgb(0,0,255) #0000ff: 1 kontur -> 2 kurva
  rgb(127,191,0) #7fbf00: 2 kontur -> 4 kurva
  rgb(255,255,255) #ffffff: 5 kontur -> 10 kurva

--- SVG Generation ---
SVG disimpan: test_image_fullcolor.svg
Total path: 4
Warna digunakan: ['#ff0000', '#0000ff', '#7fbf00', '#ffffff']
```

---

## Kompleksitas

| Aspek | Nilai |
|-------|-------|
| **K-Means Time** | O(N × K × I) — N piksel, K klaster, I iterasi |
| **K-Means Space** | O(N + K) |
| **Tracing** | O(W × H) per layer |

---

## Edge Cases / Potensi Masalah

| Masalah | Penjelasan | Solusi |
|---------|------------|--------|
| Warna mirip | Klaster tidak terpisah jelas | Naikkan n_colors |
| Noise warna | Banyak klaster kecil | Naikkan n_colors atau filter klaster kecil |
| K-Means lambat | Banyak piksel | Subsample dulu atau pakai Mini-Batch K-Means |
| Klaster kosong | Tidak ada piksel di suatu klaster | Inisialisasi ulang centroid |
| Warna background | Background jadi klaster sendiri | Biasanya tidak masalah (warna dominan) |

---

## Mengapa K-Means Manual?

| Metode | Kelebihan | Kekurangan |
|--------|-----------|------------|
| **K-Means Manual** | Mudah dipahami, tanpa dependency | Lambat, bisa konvergen ke local min |
| scikit-learn KMeans | Cepat, optimasi | Tidak boleh dipakai (learning project) |
| K-Means++ | Inisialisasi lebih baik | Lebih kompleks |
| Mini-Batch K-Means | Cukup cepat untuk data besar | Kurang presisi |

K-Means manual dipilih karena:
1. **Learning goal** — memahami algoritma dari nol.
2. **Tanpa dependency** — tidak perlu scikit-learn.
3. **Cukup untuk gambar kecil** — tidak butuh optimasi.

---

## File yang Dihasilkan

| File | Keterangan |
|------|------------|
| `tahap6_fullcolor.py` | Script utama Tahap 6 |
| `*_reduced_N.png` | Gambar reduksi warna |
| `*_fullcolor.svg` | SVG berwarna (file akhir) |
