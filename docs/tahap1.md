# Tahap 1 — Load & Preprocessing (Grayscale, Threshold, Blur)

## Ringkasan

Tahap ini memproses gambar berwarna (RGB) menjadi **gambar biner** (hitam-putih) yang siap untuk contour tracing di Tahap 2. Prosesnya: Grayscale → Gaussian Blur → Threshold Otomatis (Otsu).

**Tujuan utama:** Menyederhanakan gambar dari 3 channel warna menjadi 1 channel biner (0 atau 1), di mana 0 = objek (hitam) dan 1 = background (putih).

---

## Apa yang Dilakukan Program

### Alur Kerja (Pipeline)

```
Gambar RGB (3 channel, 0-255 per channel)
    ↓
Konversi ke Grayscale (1 channel, 0-255)
    ↓
Gaussian Blur (opsional, untuk kurangi noise)
    ↓
Threshold Otomatis (Otsu's Method)
    ↓
Gambar Biner (1 channel, hanya 0 atau 1)
    ↓
Simpan sebagai PNG + array .npy
```

---

## Langkah Detail

### 1. Load Gambar (`load_image`)

```python
img = Image.open(image_path)
img = img.convert("RGB")  # Handle RGBA/grayscale
pixels = np.array(img, dtype=np.float64)
```

- Menggunakan **Pillow** untuk membaca gambar.
- `dtype=float64` supaya operasi matematika (blur, dll) tidak terpotong ke integer.
- Hasil: array shape `(H, W, 3)` dengan nilai 0.0 - 255.0.

---

### 2. Konversi ke Grayscale (`rgb_to_grayscale`)

#### Mengapa Grayscale?

- Gambar RGB punya 3 channel (R, G, B). Untuk membuat gambar biner, kita hanya butuh **1 channel** (intensitas terang/gelap).
- Grayscale menyederhanakan data dari 3 dimensi jadi 2 dimensi.

#### Rumus Luminance (ITU-R BT.601)

```python
Gray = 0.299 × R + 0.587 × G + 0.114 × B
```

**Kenapa bukan rata-rata biasa `(R+G+B)/3`?**

Karena mata manusia **tidak sensitif sama rata** terhadap semua warna:
- **Hijau** (0.587) — mata paling sensitif, bobot paling besar
- **Merah** (0.299) — sensitivitas sedang
- **Biru** (0.114) — mata paling tidak sensitif, bobot paling kecil

Ini disebut **weighted average** — rata-rata berbobot yang memperhitungkan persepsi mata manusia.

#### Hasil

- Input: array shape `(H, W, 3)` → Output: array shape `(H, W)`
- Range nilai: 0 (hitam total) sampai 255 (putih total)

---

### 3. Gaussian Blur (`apply_gaussian_blur`)

#### Mengapa Blur?

- **Noise** (piksel acak/semburat) pada gambar bisa mengganggu proses threshold.
- Tanpa blur, threshold menghasilkan titik-titik sembarang (salt & pepper noise).
- Blur menghaluskan noise supaya threshold lebih bersih.

#### Apa itu Gaussian Blur?

Gaussian blur adalah teknik yang membuat gambar sedikit **buram** dengan cara:
1. Setiap piksel diganti dengan **rata-rata berbobot** dari tetangga-tetangganya.
2. Bobot diambil dari distribusi **Gaussian** (bentuk lonceng).
3. Tetangga yang lebih dekat punya bobot **lebih besar**.

#### Gaussian Kernel

**Kernel** adalah matriks kecil (misal 3×3) yang berisi bobot:

```
Contoh kernel 3×3 (sigma=1.0):
┌────────┬────────┬────────┐
│ 0.075  │ 0.124  │ 0.075  │
├────────┼────────┼────────┤
│ 0.124  │ 0.204  │ 0.124  │   ← Tengah paling besar
├────────┼────────┼────────┤
│ 0.075  │ 0.124  │ 0.075  │
└────────┴────────┴────────┘
Total seluruh elemen = 1.0 (sudah dinormalisasi)
```

**Kenapa total harus = 1?** Supaya kecerahan gambar tetap sama setelah blur. Kalau total > 1 → gambar lebih terang; kalau < 1 → lebih gelap.

#### Rumus Gaussian 2D

$$G(x, y) = \frac{1}{2\pi\sigma^2} e^{-\frac{x^2 + y^2}{2\sigma^2}}$$

- $\sigma$ (sigma) = standar deviasi. Semakin besar = semakin blur.
- $x, y$ = jarak dari pusat kernel.

#### Proses Convolution

1. Letakkan kernel di atas piksel pusat.
2. Kalikan setiap elemen kernel dengan piksel yang tertutup.
3. Jumlahkan semua hasil perkalian → jadi nilai piksel baru.
4. Geser kernel ke piksel berikutnya, ulangi.

---

### 4. Threshold dengan Otsu (`otsu_threshold` + `threshold_binary`)

#### Mengapa Threshold?

- Gambar grayscale punya 256 level abu-abu (0-255).
- Kita perlu memecah jadi **dua kelas**: objek (hitam) dan background (putih).
- Threshold = nilai ambang: piksel ≤ threshold → hitam, > threshold → putih.

#### Masalah: Berapa Threshold yang Tepat?

Kalau pakai threshold **statmis** (misal 128), tidak cocok untuk semua gambar:
- Gambar terang → threshold 128 terlalu rendah (banyak yang jadi hitam padahal background)
- Gambar gelap → threshold 128 terlalu tinggi (objek hilang)

#### Solusi: Otsu's Method

Otsu menemukan threshold **otomatis** berdasarkan distribusi histogram gambar:

**Algoritma:**
1. Buat histogram: hitung berapa piksel di tiap intensitas (0-255).
2. Coba semua kemungkinan threshold $t$ (0-255).
3. Untuk tiap $t$, bagi piksel jadi dua kelas:
   - Kelas 0 (background): piksel > $t$
   - Kelas 1 (objek): piksel ≤ $t$
4. Hitung **variance antara kelas** (between-class variance):
   $$\sigma_B^2(t) = \frac{[\mu_T \cdot \omega(t) - \mu(t)]^2}{\omega(t) \cdot [1 - \omega(t)]}$$
5. Threshold terbaik = nilai $t$ yang **memaksimalkan** $\sigma_B^2$.

**Intuisi:** Threshold terbaik adalah yang paling memisahkan dua "gugus" piksel (gelap dan terang) dengan variasi antar-kelas maksimum.

#### Hasil Threshold

- Input: grayscale (0-255) → Output: biner (0 atau 1)
- 0 = **hitam** = OBJEK (akan di-trace di Tahap 2)
- 1 = **putih** = BACKGROUND

---

## Parameter

| Parameter | Default | Keterangan |
|-----------|---------|------------|
| `image_path` | (wajib) | Path ke gambar input |
| `blur_sigma` | 1.0 | Kekuatan blur (0 = tanpa blur) |
| `blur_kernel` | 3 | Ukuran kernel blur (harus ganjil: 3, 5, 7...) |
| `output_dir` | `"."` | Direktori output |

### Pengaruh `blur_sigma`

| Sigma | Efek |
|-------|------|
| 0 | Tanpa blur (langsung ke threshold) |
| 0.5 | Blur sangat ringan |
| 1.0 | Blur ringan (default) |
| 2.0 | Blur sedang |
| 5.0 | Blur kuat (banyak detail hilang) |

---

## Cara Menjalankan

```bash
# Default (blur sigma=1.0, kernel=3)
python tahap1_preprocessing.py test_image.png

# Tanpa blur
python tahap1_preprocessing.py test_image.png 0

# Blur kuat + kernel besar
python tahap1_preprocessing.py logo.jpg 2.0 5
```

---

## Output yang Dihasilkan

| File | Keterangan |
|------|------------|
| `*_grayscale.png` | Gambar abu-abu (sebelum blur) |
| `*_blurred.png` | Gambar setelah Gaussian blur |
| `*_binary.png` | Gambar biner hitam-putih (hasil akhir) |
| `*_binary.npy` | Array NumPy biner (untuk Tahap 2) |

**Format `.npy`:** File binary NumPy yang menyimpan array langsung tanpa perlu dekode ulang dari PNG. Lebih cepat dan presisi (tidak ada kompresi lossy).

---

## Contoh Output

```
Gambar dimuat: 64x64 piksel
Grayscale selesai - range nilai: 29 - 255
Disimpan: test_image_grayscale.png
Gaussian kernel (3x3, sigma=1.0):
[[0.075 0.124 0.075]
 [0.124 0.204 0.124]
 [0.075 0.124 0.075]]
Blur selesai - output shape: (64, 64)
Disimpan: test_image_blurred.png
Otsu threshold: 135
Binerisasi selesai - hitam (objek): 1867, putih (background): 2229
Disimpan: test_image_binary.png
```

---

## Konsep Matematika Tambahan

### Convolution

Operasi matematika inti dari Gaussian blur:

$$(f * g)(x, y) = \sum_{j=-k}^{k} \sum_{i=-k}^{k} f(x+i, y+j) \cdot g(i, j)$$

Di mana:
- $f$ = gambar (input)
- $g$ = kernel Gaussian
- $k$ = ukuran kernel // 2

### Normalisasi Kernel

$$g'(i, j) = \frac{g(i, j)}{\sum_{j} \sum_{i} g(i, j)}$$

Memastikan total bobot = 1 supaya kecerahan tidak berubah.

---

## Edge Cases / Potensi Masalah

| Masalah | Penjelasan | Solusi |
|---------|------------|--------|
| Gambar RGBA | Punya 4 channel | `img.convert("RGB")` |
| Gambar grayscale | Hanya 1 channel | `img.convert("RGB")` |
| Noise tinggi | Banyak titik acak | Blur lebih kuat (sigma > 1.0) |
| Gambar sangat terang | Threshold Otsu terlalu tinggi | Kurangi blur atau adjust threshold manual |
| Gambar sangat gelap | Threshold Otsu terlalu rendah | Tambah blur atau adjust threshold manual |
| Konvolusi lambat | Loop Python = O(W × H × K²) | Di tahap ini tidak masalah (prioritas kejelasan) |

---

## Mengapa Pipeline Ini Penting?

1. **Grayscale** → menyederhanakan dari 3 channel ke 1 channel.
2. **Blur** → mengurangi noise yang bisa mengganggu threshold.
3. **Threshold** → memisahkan objek dari background secara otomatis.

Tanpa preprocessing ini, contour tracing di Tahap 2 akan menghasilkan kontur yang **kacau** karena noise dan variasi warna yang tidak perlu.

---

## File yang Dihasilkan

| File | Keterangan |
|------|------------|
| `tahap1_preprocessing.py` | Script utama Tahap 1 |
| `test_image_grayscale.png` | Hasil grayscale |
| `test_image_blurred.png` | Hasil blur |
| `test_image_binary.png` | Hasil biner |
| `test_image_binary.npy` | Array biner untuk Tahap 2 |
