# Tahap 2 — Contour Tracing (Moore-Neighbor)

## Ringkasan

Tahap ini menyusuri **tepi (boundary)** tiap objek hitam pada gambar biner menggunakan algoritma **Moore-Neighbor Tracing**. Output-nya berupa list titik-titik (x, y) yang membentuk polygon tertutup untuk tiap objek.

**Tujuan utama:** Mengubah gambar biner (grid piksel) menjadi **representasi kontur** (list titik) yang bisa diproses lebih lanjut (simplifikasi, curve fitting, dll).

---

## Apa yang Dilakukan Program

### Alur Kerja (Pipeline)

```
Gambar Biner (0=hitam/objek, 1=putih/background)
    ↓
Scan cari piksel hitam pertama (tepi kiri objek)
    ↓
Mulai Moore-Neighbor Tracing (berjalan sekitar tepi)
    ↓
Kontur tertutup (list titik y,x)
    ↓
Ulangi untuk semua objek
    ↓
Simpan kontur + visualisasi
```

---

## Mengapa Contour Tracing?

### Masalah dari Tahap 0

Di Tahap 0, setiap piksel/blok jadi kotak terpisah. Untuk gambar 64×64, SVG-nya punya **64 elemen `<rect>`**. Untuk gambar 500×500 dengan block_size=1, bisa jadi **250,000 elemen** — sangat besar dan lambat!

### Solusi: Kontur

Dengan tracing, kita hanya menyimpan **tepi objek** (beberapa ratus titik), bukan semua piksel di dalamnya. Ini jauh lebih efisien.

### Perbandingan

| Metode | Gambar 100×100 | Elemen SVG |
|--------|----------------|------------|
| Tahap 0 (rect) | 10,000 piksel | 10,000 `<rect>` |
| Tahap 2 (kontur) | 1 objek | ~400 titik polygon |

---

## Algoritma Moore-Neighbor Tracing

### Konsep Inti

Bayangkan Anda sedang **berjalan mengelilingi sebuah pulau** (objek hitam) dengan tangan kanan selalu menyentuh tepi pulau. Anda berjalan searah jarum jam sampai kembali ke titik awal.

### Tetangga Moore (8 Arah)

Setiap piksel punya 8 tetangga:

```
┌─────┬─────┬─────┐
│ NW  │  N  │ NE  │
│ (-1,-1)│(-1,0)│(-1,1)│
├─────┼─────┼─────┤
│  W  │  P  │  E  │   ← P = piksel pusat
│(0,-1)│(0,0)│(0,1)│
├─────┼─────┼─────┤
│ SW  │  S  │ SE  │
│ (1,-1) │(1,0) │(1,1) │
└─────┴─────┴─────┘
```

**Urutan searah jarum jam (mulai dari Timur):**
- 0: E (Timur) → `(0, +1)`
- 1: SE (Tenggara) → `(+1, +1)`
- 2: S (Selatan) → `(+1, 0)`
- 3: SW (Barat Daya) → `(+1, -1)`
- 4: W (Barat) → `(0, -1)`
- 5: NW (Barat Laut) → `(-1, -1)`
- 6: N (Utara) → `(-1, 0)`
- 7: NE (Timur Laut) → `(-1, +1)`

---

### Langkah Algoritma

#### Langkah 1: Cari Titik Awal

```python
# Scan dari kiri-atas, cari piksel hitam pertama
for y in range(height):
    for x in range(width):
        if binary[y, x] == 0:  # hitam = objek
            return (y, x)
```

**Kenapa dari kiri-atas?**
- Titik ini dijamin berada di **tepi kiri atas** objek.
- Memiliki piksel **putih di sebelah kiri** (karena masih di pinggir).
- Cocok sebagai titik mulai tracing.

#### Langkah 2: Inisialisasi

```python
# Mulai dari putih di KIRI titik awal
current = (start_y, start_x - 1)  # putih
prev_dir = 4  # datang dari arah W (kiri)
```

**Kenapa mulai dari kiri?**
- Kita "datang" dari luar objek (background putih).
- Dengan `prev_dir = 4` (W), pencarian tetangga dimulai dari arah **SE (index 1)** — artinya kita mencari "ke depan" searah jarum jam.

#### Langkah 3: Cari Tetangga Berikutnya

```python
# Mulai cari dari arah SETELAH arah kedatangan
for i in range(8):
    dir_idx = (prev_dir + 1 + i) % 8  # mulai dari arah berikutnya
    dy, dx = DIRECTIONS[dir_idx]
    ny, nx = current_y + dy, current_x + dx
    
    if is_black(binary, ny, nx):
        # Ketemu! Pindah ke sana
        contour.append((ny, nx))
        prev_dir = OPPOSITE[dir_idx]  # arah kedatangan = lawan arah gerak
        current = (ny, nx)
        break
```

**Mengapa mulai dari `(prev_dir + 1)`?**
- Supaya kita tidak langsung balik ke arah datang.
- Kita selalu mencari "ke depan" searah jarum jam.

#### Langkah 4: Selesai

Berhenti ketika kembali ke **titik awal**:

```python
if (current_y, current_x) == (start_y, start_x):
    break  # Kontur tertutup!
```

---

### Contoh Tracing

Misal objek berbentuk kotak 4×4:

```
. . . . . .    . = putih (background)
. ■ ■ ■ . .    ■ = hitam (objek)
. ■ ■ ■ . .
. ■ ■ ■ . .
. . . . . .
```

Tracing dimulai dari piksel (1,1) (tepi kiri objek):

1. Start: (1,1), datang dari (1,0) [putih di kiri]
2. Cari tetangga → dapat (1,2) [SE]
3. Cari tetangga → dapat (1,3) [E]
4. Cari tetangga → dapat (2,3) [SE]
5. ... lanjut mengelilingi ...
6. Kembali ke (1,1) → **selesai!**

Hasil: `[(1,1), (1,2), (1,3), (2,3), (3,3), (3,2), (3,1), (2,1), (1,1)]`

---

## Multiple Objects

### Deteksi Semua Objek

```python
# Cari semua titik awal: piksel hitam dengan putih di kiri
for y in range(height):
    for x in range(width):
        if binary[y, x] == 0:          # hitam
            if x == 0 or binary[y, x-1] == 1:  # putih di kiri
                starts.append((y, x))
```

**Kenapa harus ada putih di kiri?**
- Memastikan kita hanya mulai dari **tepi LUAR** objek.
- Piksel di DALAM objek tidak punya putih di kiri → tidak jadi titik awal.

### Penandaan (Visited)

```python
visited = np.zeros((h, w), dtype=bool)

# Setelah trace, tandai semua titik kontur
for y, x in contour:
    visited[y, x] = True
```

Supaya objek yang sama tidak di-trace dua kali.

---

## Parameter

Tahap ini tidak punya parameter yang bisa diatur user. Input adalah file `.npy` atau `.png` dari Tahap 1.

---

## Cara Menjalankan

```bash
# Dari file .npy (hasil Tahap 1)
python tahap2_contour_tracing.py test_image_binary.npy

# Atau dari gambar biner PNG
python tahap2_contour_tracing.py test_binary_clean.png
```

---

## Output yang Dihasilkan

| File | Keterangan |
|------|------------|
| `*_contours.png` | Visualisasi kontur (warna berbeda tiap objek) |
| `*_contours.json` | Data kontur untuk Tahap 3+ |

### Format JSON

```json
[
  [[y1,x1], [y2,x2], ...],   // kontur 1
  [[y1,x1], [y2,x2], ...]    // kontur 2
]
```

---

## Contoh Output

```
Biner: 64x64, piksel hitam: 3196
Mulai Contour Tracing...
Kontur ditemukan: 5
  #1: 254 titik
  #2: 60 titik
  #3: 60 titik
  #4: 60 titik
  #5: 60 titik
Visualisasi disimpan: test_binary_clean_contours.png
Kontur disimpan: test_binary_clean_contours.json
```

---

## Kompleksitas

| Aspek | Nilai |
|-------|-------|
| **Time** | O(W × H) untuk scan + O(K) per kontur (K = jumlah titik) |
| **Space** | O(W × H) untuk array `visited` |

---

## Edge Cases / Potensi Masalah

| Masalah | Penjelasan | Solusi |
|---------|------------|--------|
| Anti-aliasing | Tepi objek punya piksel semi-transparan | Perlu threshold yang tepat di Tahap 1 |
| Objek 1 piksel | Sangat kecil, kontur minimal | Filter kontur < N titik |
| Lubang di dalam objek | Moore-Neighbor hanya trace tepi luar | Perlu algoritma tambahan (hole detection) |
| Objek menyentuh tepi gambar | Trace terpotong | Saat ini diabaikan |

---

## Mengapa Moore-Neighbor?

| Algoritma | Kelebihan | Kekurangan |
|-----------|-----------|------------|
| **Moore-Neighbor** | Sederhana, mudah dipahami | Hanya trace tepi luar |
| Suzuki-Abe | Bisa deteksi lubang | Lebih kompleks |
| Border Following | Standar industri | Butuh mehrisasi khusus |

Moore-Neighbor dipilih karena:
1. **Mudah dipahami** — cocok untuk learning project.
2. **Cukup** untuk gambar sederhana (logo, ikon).
3. **Basis** untuk algoritma tracing yang lebih kompleks.

---

## File yang Dihasilkan

| File | Keterangan |
|------|------------|
| `tahap2_contour_tracing.py` | Script utama Tahap 2 |
| `create_test_binary.py` | Generator test image biner |
| `test_binary_clean.png` | Test image bersih |
| `test_binary_clean_contours.png` | Visualisasi kontur |
| `test_binary_clean_contours.json` | Data kontur |
