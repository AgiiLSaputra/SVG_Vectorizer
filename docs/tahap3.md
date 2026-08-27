# Tahap 3 — Polygon Simplification (Ramer-Douglas-Peucker)

## Ringkasan

Tahap ini menggunakan algoritma **Ramer-Douglas-Peucker (RDP)** untuk **mengurangi jumlah titik** pada polygon hasil tracing (Tahap 2) tanpa mengubah bentuk secara signifikan. Hasilnya: polygon dengan lebih sedikit titik tapi bentuk hampir sama.

**Tujuan utama:** Membuat representasi kontur lebih **efisien** (lebih sedikit titik = file SVG lebih kecil) sambil mempertahankan bentuk objek.

---

## Mengapa Simplifikasi Diperlukan?

### Masalah dari Tahap 2

Hasil tracing menghasilkan **sangat banyak titik** — termasuk titik-titik yang tidak penting (hampir lurus). Contoh:

```
Kontur asli (254 titik):
*---*---*---*---*---*---*---*---*---*---*---*---*
    (setiap piksel tepi jadi 1 titik)

Kontur setelah simplifikasi (5 titik):
*---------------------------*
(hanya titik "penting" yang disimpan)
```

### Dampak ke SVG

| | Sebelum | Sesudah |
|--|---------|---------|
| Titik kontur | 254 | 5 |
| Ukuran file SVG | ~15 KB | ~200 byte |
| Kecepatan render | Lambat | Cepat |

---

## Algoritma Ramer-Douglas-Peucker

### Konsep Inti

Bayangkan Anda punya polygon dengan banyak titik. Anda ingin **membuang titik-titik yang tidak penting** (yang menyimpang sedikit dari garis lurus).

### Alur Algoritma (Recursive / Divide and Conquer)

```
MASUKAN: points (list titik), epsilon (toleransi)

LANGKAH 1: Hubungkan titik PERTAMA (A) dan TERAKHIR (B)
           dengan garis lurus.

LANGKAH 2: Untuk setiap titik di ANTARA A dan B:
           Hitung jarak perpendicular ke garis A→B.

LANGKAH 3: Cari titik dengan jarak MAKSIMUM → sebut D.

LANGKAH 4: KONDISI:
           - Jika jarak(D) > epsilon:
             → Titik D PENTING! Simpan.
             → Recursive: proses [A...D] dan [D...B]
           - Jika jarak(D) <= epsilon:
             → Semua titik antara A dan B BISA DIBUANG.
             → Simpan hanya A dan B.
```

### Contoh Visual

**Polygon asli (banyak titik):**
```
A---*---*---*---*---*---*---*---B
    *   *   *       *   *   *
        *       *       *
```

**Langkah 1:** Hubungkan A→B
```
A===========================B
    *   *   *       *   *   *
        *       *       *
```

**Langkah 2:** Cari titik terjauh → D (titik yang paling jauh dari garis)
```
A===========================B
    *   *   D*      *   *   *  ← D adalah titik terjauh
        *       *       *
```

**Langkah 3:** Jarak D > epsilon → D penting! Simpan.
```
A==========D==============B
    *   *       *   *   *
        *       *       *
```

**Langkah 4:** Recursive: proses [A...D] dan [D...B]

**Hasil akhir:**
```
A==========D==============B
(hanya 3 titik tersisa!)
```

---

## MATEMATIKA: Jarak Titik ke Garis

### Rumus

Diberi:
- Titik P = `(px, py)`
- Garis dari A = `(ax, ay)` ke B = `(bx, by)`

$$d = \frac{|(bx-ax)(ay-py) - (ax-px)(by-ay)|}{\sqrt{(bx-ax)^2 + (by-ay)^2}}$$

### Intuisi

Bayangkan garis dari A ke B. Kita ingin tahu **"seberapa jauh"** titik P dari garis itu.

- Kalau P **tepat di atas garis** → jarak = 0
- Kalau P **jauh di samping** → jarak = besar

Ini adalah jarak **perpendicular** (tegak lurus), bukan jarak ke titik ujung garis.

### Contoh Perhitungan

```
A = (0, 0), B = (10, 0), P = (5, 3)

Jarak = |(10-0)(0-3) - (0-5)(0-0)| / sqrt((10-0)² + (0-0)²)
      = |10×(-3) - (-5)×0| / sqrt(100)
      = |-30| / 10
      = 3.0 piksel
```

### Penerapan di RDP

| Jarak | Keputusan | Alasan |
|-------|-----------|--------|
| > epsilon | **Simpan** titik | Titik ini menyimpang jauh dari garis → penting |
| <= epsilon | **Buang** titik | Titik ini hampir lurus → tidak penting |

---

## Parameter: Epsilon (ε)

### Apa itu Epsilon?

**Epsilon** adalah toleransi maksimum penyimpangan dalam piksel. Ini adalah parameter utama yang mengontrol seberapa banyak titik yang dibuang.

### Pengaruh Epsilon

| Epsilon | Titik Disimpan | Efek |
|---------|----------------|------|
| 0.1 | Banyak | Detail tinggi, file besar |
| 1.0 | Sedang | Seimbang |
| 2.0 | Sedikit | Hemat file, sedikit penyederhanaan |
| 5.0 | Sangat sedikit | Sangat hemat, banyak detail hilang |
| 10.0 | Minimum | Hanya sudut utama tersisa |

### Contoh untuk Polygon 254 Titik

| Epsilon | Titik Tersisa | Persentase |
|---------|---------------|------------|
| 0.5 | ~50 | 80% dibuang |
| 1.0 | ~20 | 92% dibuang |
| 2.0 | 5 | 98% dibuang |
| 5.0 | 4 | 98% dibuang |

---

## Cara Memilih Epsilon

### Aturan Umum

```
epsilon terlalu kecil (0.1):
  → Terlalu banyak titik tersisa
  → File SVG masih besar
  → Tidak ada penyederhanaan yang berarti

epsilon tepat (1.0 - 3.0):
  → Jumlah titik wajar
  → Bentuk tetap terjaga
  → File SVG jauh lebih kecil

epsilon terlalu besar (10.0+):
  → Terlalu banyak detail hilang
  → Polygon jadi sangat kasar
  → Bentuk berubah drastis
```

### Tips

1. **Mulai dari 1.0**, lalu naikkan/kecilkan sesuai kebutuhan.
2. **Cek visual:** Buka hasil simplifikasi dan bandingkan dengan asli.
3. **Sesuaikan per kontur:** Kontur kompleks butuh epsilon lebih kecil.

---

## Parameter Program

| Parameter | Default | Keterangan |
|-----------|---------|------------|
| `contours_path` | (wajib) | Path ke file JSON kontur dari Tahap 2 |
| `epsilon` | 2.0 | Toleransi simplifikasi (piksel) |
| `output_dir` | `"."` | Direktori output |

---

## Cara Menjalankan

```bash
# Dengan epsilon default (2.0)
python tahap3_simplification.py test_binary_clean_contours.json

# Dengan epsilon custom
python tahap3_simplification.py contours.json 1.0
python tahap3_simplification.py contours.json 5.0
```

---

## Output yang Dihasilkan

| File | Keterangan |
|------|------------|
| `*_simplified.json` | Kontur yang sudah disederhanakan (siap untuk Tahap 4) |

---

## Contoh Output

```
Kontur dimuat: 5 kontur
Epsilon (toleransi): 2.0 piksel

--- Douglas-Peucker Simplification ---
  Kontur 1: 254 -> 5 titik (hemat 98%)
  Kontur 2: 60 -> 5 titik (hemat 92%)
  Kontur 3: 60 -> 5 titik (hemat 92%)
  Kontur 4: 60 -> 5 titik (hemat 92%)
  Kontur 5: 60 -> 5 titik (hemat 92%)

Total: 494 -> 25 titik (hemat 469 = 95%)
Kontur disimpan: test_binary_clean_contours_simplified.json
```

---

## Kompleksitas

| Aspek | Nilai |
|-------|-------|
| **Time** | O(n log n) rata-rata, O(n²) worst case |
| **Space** | O(n) untuk rekursi |

Di mana n = jumlah titik polygon.

---

## Edge Cases / Potensi Masalah

| Masalah | Penjelasan | Solusi |
|---------|------------|--------|
| Polygon < 3 titik | Tidak bisa disederhanakan | Kembalikan apa adanya |
| Semua titik lurus | Jarak semua = 0 | Hanya tersisa 2 titik (awal & akhir) |
| Epsilon = 0 | Tidak ada yang dibuang | Pertahankan semua titik |
| Epsilon terlalu besar | Polygon jadi garis lurus | Kurangi epsilon |

---

## Mengapa Douglas-Peucker?

| Algoritma | Kelebihan | Kekurangan |
|-----------|-----------|------------|
| **Douglas-Peucker** | Sederhana, cepat, hasil bagus | Tidak preserve kesejajaran |
| Visvalingam | Lebih smooth | Lebih kompleks |
| Lang | Preserves sudut | Butuh parameter tambahan |
| Reumann-Witkam | Cocok untuk kurva | Tidak untuk polygon tertutup |

Douglas-Peucker dipilih karena:
1. **Standar industri** — paling banyak digunakan.
2. **Mudah dipahami** — recursive divide & conquer.
3. **Cukup untuk learning** — hasil langsung terlihat.

---

## Analisis Matematika Lanjutan

### Mengapa Recursive?

RDP menggunakan pendekatan **divide and conquer**:
1. Masalah besar → pecah jadi 2 masalah lebih kecil
2. Selesaikan masing-masing secara rekursif
3. Gabungkan hasil

Ini efisien karena:
- Setiap iterasi, kita menambahkan **1 titik penting**
- Rekursi berhenti ketika tidak ada lagi titik yang menyimpang

### Kasus Worst Case

Untuk polygon spiral:
```
Titik-titik membentuk spiral → banyak titik yang menyimpang dari garis
→ banyak titik yang disimpan
→ waktu eksekusi mendekati O(n²)
```

Namun untuk polygon normal (kontur objek), waktu eksekusi mendekati **O(n log n)**.

---

## File yang Dihasilkan

| File | Keterangan |
|------|------------|
| `tahap3_simplification.py` | Script utama Tahap 3 |
| `*_simplified.json` | Kontur hasil simplifikasi |
