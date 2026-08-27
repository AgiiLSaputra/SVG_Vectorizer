# Tahap 4 — Curve Fitting (Bezier)

## Ringkasan

Tahap ini mengubah titik-titik polygon hasil simplifikasi (Tahap 3) menjadi **kurva Bezier kubik** menggunakan metode **Schneider** (Graphics Gems I, 1990). Hasilnya: kurva smooth yang mendekati bentuk asli objek.

**Tujuan utama:** Mengubah polygon (titik-titik lurus) menjadi kurva yang **halus dan natural** — seperti yang dihasilkan software desain vektor (Illustrator, Inkscape).

---

## Mengapa Bezier Curve?

### Masalah dari Tahap 3

Hasil simplifikasi masih berupa **polygon** (garis-garis lurus antar titik):

```
Polygon (garis lurus):
*-------*-------*
|               |
*-------*-------*

Kurva Bezier (halus):
╭───────╮
│       │
╰───────╯
```

### Keunggulan Bezier

1. **Smooth** — tidak ada sudut tajam.
2. **Efisien** — 4 titik kontrol bisa gambarkan kurva kompleks.
3. **Scalable** — bisa di-zoom tanpa kehilangan kualitas.
4. **Standar** — digunakan di SVG, PostScript, font, dll.

---

## Apa itu Kurva Bezier Kubik?

### Definisi

Kurva Bezier kubik didefinisikan oleh **4 titik**:
- **P0** = titik awal (sudah diketahui)
- **P1** = titik kontrol 1 (menentukan arah mulai)
- **P2** = titik kontrol 2 (menentukan arah akhir)
- **P3** = titik akhir (sudah diketahui)

```
P0 -------- P1
  \        /
   \      /    ← Kurva mengikuti P1 dan P2
    \    /
     \  /
      \/
      /\
     /  \
    /    \
   /      \
  /        \
P2 -------- P3
```

### Rumus Matematika

$$B(t) = (1-t)^3 P_0 + 3(1-t)^2 t P_1 + 3(1-t) t^2 P_2 + t^3 P_3$$

Di mana:
- $t \in [0, 1]$ — parameter (0 = titik awal, 1 = titik akhir)
- $P_0, P_1, P_2, P_3$ — 4 titik kontrol (koordinat y, x)

### Basis Functions

Tiap titik kontrol punya "bobot" yang berubah seiring $t$:

| Fungsi | Rumus | Perilaku |
|--------|-------|----------|
| $B_0(t)$ | $(1-t)^3$ | Besar saat $t=0$, nol saat $t=1$ |
| $B_1(t)$ | $3(1-t)^2 t$ | Puncak di $t=1/3$ |
| $B_2(t)$ | $3(1-t) t^2$ | Puncak di $t=2/3$ |
| $B_3(t)$ | $t^3$ | Nol saat $t=0$, besar saat $t=1$ |

### Contoh: Kurva Lurus

Jika P1 dan P2 terletak **tepat di garis lurus** antara P0 dan P3:
```
P0 --- P1 --- P2 --- P3
```
→ Hasilnya adalah garis lurus (tidak ada lengkungan).

### Contoh: Kurva Melengkung

Jika P1 dan P2 **menyimpang** dari garis lurus:
```
P0
 \
  P1
   \
    *  ← titik tengah kurva (t=0.5)
   /
  P2
 /
P3
```
→ Hasilnya adalah kurva yang melengkung mengikuti P1 dan P2.

---

## MATEMATIKA: Parameterisasi Chord-Length

### Masalah

Kita punya N titik data: $Q_0, Q_1, \ldots, Q_{N-1}$. Untuk least-squares, kita perlu menentukan **parameter $t_i$** untuk setiap titik $Q_i$.

### Solusi: Chord Length

$$t_i = \frac{\sum_{k=1}^{i} \|Q_k - Q_{k-1}\|}{\sum_{k=1}^{N-1} \|Q_k - Q_{k-1}\|}$$

**Intuisi:** Parameter $t$ proporsional terhadap **jarak kumulatif** dari titik pertama.

### Contoh

```
Q₀ --3-- Q₁ --5-- Q₂ --2-- Q₃
Total jarak = 10

t₀ = 0/10  = 0.0
t₁ = 3/10  = 0.3
t₂ = 8/10  = 0.8
t₃ = 10/10 = 1.0
```

---

## MATEMATIKA: Least-Squares Bezier Fitting

### Masalah

Diketahui:
- Titik data: $Q_0, Q_1, \ldots, Q_{N-1}$
- Titik awal $P_0 = Q_0$, titik akhir $P_3 = Q_{N-1}$
- Vektor tangent awal dan akhir

Dicari:
- Titik kontrol $P_1$ dan $P_2$ yang **meminimalkan error** antara kurva Bezier dan titik data.

### Langkah Schneider's Method

#### Langkah 1: Parameterisasi

Tentukan $t_i$ untuk tiap $Q_i$ menggunakan chord length.

#### Langkah 2: Bangun Matriks A

Untuk tiap titik data $Q_i$, hitung **basis functions**:

$$A_i = \begin{bmatrix} B_1(t_i) & B_2(t_i) \end{bmatrix}$$

Di mana:
- $B_1(t) = 3(1-t)^2 t$ — koefisien untuk $P_1$
- $B_2(t) = 3(1-t) t^2$ — koefisien untuk $P_2$

#### Langkah 3: Hitung Vektor b

$$b_i = Q_i - B_0(t_i) P_0 - B_3(t_i) P_3$$

Di mana:
- $B_0(t) = (1-t)^3$ — koefisien untuk $P_0$
- $B_3(t) = t^3$ — koefisien untuk $P_3$

#### Langkah 4: Solve Persamaan Normal

$$(A^T A) x = A^T b$$

Di mana $x = [P_1, P_2]^T$ (titik kontrol yang dicari).

**Mengapa pakai least-squares?**
- Karena kita punya **N persamaan** (tiap titik data) tapi hanya **2 unknown** ($P_1, P_2$).
- Least-squares menemukan solusi terbaik yang meminimalkan total error kuadrat.

---

## MATEMATIKA: Recursive Splitting

### Masalah

Satu kurva Bezier mungkin **tidak cukup** untuk mendekati polygon yang kompleks. Solusi: **pecah** polygon jadi beberapa segmen, lalu fit Bezier ke tiap segmen.

### Algoritma

```
fit_bezier_segment(points, max_error):
    1. Parameterisasi (chord length)
    2. Estimasi tangent awal & akhir
    3. Hitung P1, P2 (least-squares)
    4. Hitung error maksimum
    5. Jika error > max_error:
       → Cari titik dengan error max (split point)
       → Recursive: fit bagian KIRI dan KANAN
    6. Jika error <= max_error:
       → Simpan kurva Bezier ini
```

### Contoh Visual

**Polygon asli:**
```
A---B---C---D---E---F
```

**Langkah 1:** Fit A→F (seluruh titik)
```
A===================F
    B C D E    ← error besar di sini
```

**Langkah 2:** Error > tolerance → split di D
```
A=======D (kiri)
        D=======F (kanan)
```

**Langkah 3:** Recursive untuk masing-masing bagian
```
A----D (fit bagian kiri → cukup bagus)
D----F (fit bagian kanan → cukup bagus)
```

**Hasil:** 2 kurva Bezier yang menghubungkan A→D→F.

---

## Parameter

| Parameter | Default | Keterangan |
|-----------|---------|------------|
| `contours_path` | (wajib) | Path ke file JSON kontur dari Tahap 3 |
| `max_error` | 2.0 | Toleransi error maksimum (piksel) |

### Pengaruh `max_error`

| Max Error | Kurva | Efek |
|-----------|-------|------|
| 0.5 | Banyak segmen | Sangat presisi, file besar |
| 1.0 | Sedang | Seimbang |
| 2.0 | Sedikit segmen | Hemat file (default) |
| 5.0 | Sangat sedikit | Detail hilang |

---

## Cara Menjalankan

```bash
# Dengan error default (2.0)
python tahap4_bezier.py test_binary_clean_contours_simplified.json

# Dengan error custom
python tahap4_bezier.py contours.json 1.0
```

---

## Output yang Dihasilkan

| File | Keterangan |
|------|------------|
| `*_bezier.json` | Data kurva Bezier untuk Tahap 5 |

### Format JSON

```json
[
  [  // Kurva 1 (4 titik kontrol)
    [[y0,x0], [y1,x1], [y2,x2], [y3,x3]],
    [[y0,x0], [y1,x1], [y2,x2], [y3,x3]]  // Kurva 2
  ],
  [...]  // Kurva dari kontur berikutnya
]
```

---

## Contoh Output

```
Kontur dimuat: 5 kontur
Max error (toleransi): 2.0 piksel

--- Bezier Curve Fitting (Schneider's Method) ---
  Kontur 1: 5 titik -> 2 kurva Bezier
  Kontur 2: 5 titik -> 2 kurva Bezier
  Kontur 3: 5 titik -> 2 kurva Bezier
  Kontur 4: 5 titik -> 2 kurva Bezier
  Kontur 5: 5 titik -> 2 kurva Bezier

Total kurva Bezier: 10
Kurva Bezier disimpan: test_binary_clean_contours_bezier.json
```

---

## Kompleksitas

| Aspek | Nilai |
|-------|-------|
| **Time** | O(N × M) per iterasi, di mana N = jumlah titik, M = jumlah segmen |
| **Space** | O(N) untuk matriks |

---

## Edge Cases / Potensi Masalah

| Masalah | Penjelasan | Solusi |
|---------|------------|--------|
| Polygon < 2 titik | Tidak cukup untuk Bezier | Skip |
| 2 titik saja | Garis lurus | Buat Bezier lurus (P1, P2 = 1/3, 2/3) |
| Semua titik lurus | Tidak ada lengkungan | P1, P2 di garis lurus |
| Error selalu besar | Polygon sangat kompleks | Kurangi max_error atau pakai lebih banyak segmen |
| Singular matrix | ATA tidak bisa di-invert | Pakai pseudoinverse |

---

## Mengapa Schneider's Method?

| Metode | Kelebihan | Kekurangan |
|--------|-----------|------------|
| **Schneider** | Sederhana, cepat, hasil bagus | Tidak optimalkan panjang kurva |
| Levenberg-Marquardt | Optimasi non-linear, hasil terbaik | Lebih kompleks, lambat |
| Minimum Area | Preserves area | Butuh optimasi mahal |
| Immobile Points | Titik tertentu harus di kurva | Konstruksi lebih rumit |

Schneider dipilih karena:
1. **Mudah dipahami** — hanya least-squares + recursive splitting.
2. **Cukup cepat** — O(N) per iterasi.
3. **Standar** — banyak digunakan di literature.

---

## File yang Dihasilkan

| File | Keterangan |
|------|------------|
| `tahap4_bezier.py` | Script utama Tahap 4 |
| `*_bezier.json` | Data kurva Bezier |
