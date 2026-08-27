# Tahap 5 — SVG Generation

## Ringkasan

Tahap ini mengubah data kurva Bezier hasil Tahap 4 menjadi **file SVG yang valid** dan bisa dibuka di browser. Setiap kurva Bezier dikonversi menjadi SVG path command (`M`, `C`, `Z`).

**Tujuan utama:** Menghasilkan file `.svg` akhir yang bisa dilihat, di-zoom, dan diedit di software vektor.

---

## Apa yang Dilakukan Program

### Alur Kerja

```
Data Bezier (JSON)
    ↓
Konversi ke SVG Path String
    ↓
Gabungkan jadi SVG Lengkap
    ↓
Simpan ke file .svg
    ↓
Buka di Browser!
```

---

## Format SVG Path

### Command yang Digunakan

SVG path menggunakan **huruf** sebagai command:

| Command | Nama | Keterangan | Angka |
|---------|------|------------|-------|
| `M` | Move To | Pindah ke titik (angkat pena) | x,y |
| `C` | Cubic Bézier | Gambar kurva kubik | x1,y1 x2,y2 x,y |
| `Z` | Close Path | Tutup path ke titik awal | (tidak ada) |

### Penjelasan Tiap Command

#### M (Move To)

```
M 10,20
```

- Pindahkan "pena" ke koordinat (10, 20).
- Seperti **mengangkat pena** dari kertas dan menempatkannya di tempat baru.
- Tidak menggambar apa-apa, hanya memindahkan posisi.

#### C (Cubic Bézier)

```
C 15,25 30,35 40,20
```

- Gambar **kurva kubik** dari posisi saat ini ke titik akhir.
- Butuh **6 angka** (3 pasang koordinat):
  - `15,25` = titik kontrol 1 (menentukan arah mulai)
  - `30,35` = titik kontrol 2 (menentukan arah akhir)
  - `40,20` = titik akhir kurva

#### Z (Close Path)

```
Z
```

- Tutup path: gambar garis dari posisi saat ini ke titik awal (`M`).
- Membuat polygon **tertutup**.

---

## Contoh: Dari Bezier ke SVG Path

### Diberi 2 Kurva Bezier

```
Kurva 1: P0(10,20) P1(15,25) P2(30,35) P3(40,20)
Kurva 2: P0(40,20) P1(50,10) P2(60,30) P3(70,20)
```

### Konversi ke SVG Path

```
M 10,20        ← Mulai dari (10,20)
C 15,25 30,35 40,20   ← Kurva 1 ke (40,20)
C 50,10 60,30 70,20   ← Kurva 2 ke (70,20)
Z              ← Tutup path ke (10,20)
```

### Hasil dalam SVG

```xml
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
  <path d="M 10,20 C 15,25 30,35 40,20 C 50,10 60,30 70,20 Z" fill="red"/>
</svg>
```

---

## Visualisasi: Apa yang Terjadi

```
M 10,20
  ↓
  P1(15,25)
    \
     *  ← kurva mulai dari (10,20) mengikuti P1
    /
C 30,35 40,20
  ↓
      P2(30,35)
        \
         *  ← kurva berakhir di (40,20) mengikuti P2
        /
C 50,10 60,30 70,20
  ↓
  P1(50,10)     P2(60,30)
    \           /
     *---*---*  ← kurva kedua ke (70,20)
        /
Z
  ↓
  Garis dari (70,20) ke (10,20) → path tertutup!
```

---

## Struktur File SVG

```xml
<svg xmlns="http://www.w3.org/2000/svg"
     width="64" height="64"
     viewBox="0 0 64 64">
  <rect width="100%" height="100%" fill="white"/>
  <path d="M ..." fill="#555555"/>
  <path d="M ..." fill="#555555"/>
  ...
</svg>
```

### Penjelasan Tiap Elemen

| Elemen | Fungsi |
|--------|--------|
| `<svg>` | Container utama SVG |
| `xmlns` | Namespace XML (wajib) |
| `width/height` | Ukuran gambar dalam piksel |
| `viewBox` | Area koordinat internal |
| `<rect>` | Background putih (opsional) |
| `<path>` | Kurva Bezier (isi objek) |

---

## Parameter

| Parameter | Default | Keterangan |
|-----------|---------|------------|
| `bezier_path` | (wajib) | Path ke file JSON dari Tahap 4 |
| `width` | (wajib) | Lebar gambar dalam piksel |
| `height` | (wajib) | Tinggi gambar dalam piksel |
| `output_path` | otomatis | Path file output SVG |
| `colors` | `["#555555"]` | Warna fill untuk tiap path |

### Warna

- Default: abu-abu (`#555555`)
- Bisa diatur per-kontur: `["#ff0000", "#00ff00", "#0000ff"]`
- Format: hex (`#RRGGBB`) atau nama warna (`red`)

---

## Cara Menjalankan

```bash
# Dengan parameter default
python tahap5_svg_gen.py test_binary_clean_contours_bezier.json 64 64

# Dengan output custom
python tahap5_svg_gen.py bezier.json 100 80 my_output.svg
```

---

## Output yang Dihasilkan

| File | Keterangan |
|------|------------|
| `*_output.svg` | File SVG yang bisa dibuka di browser |

---

## Contoh Output

```
Data Bezier dimuat: 5 segmen

--- SVG Generation ---
SVG disimpan: test_binary_clean_contours_output.svg
  Ukuran gambar: 64x64
  Jumlah path: 5
```

### Isi SVG

```xml
<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <rect width="100%" height="100%" fill="white"/>
  <path d="M 0.0,0.0 C 73.5,-10.5 73.5,-10.5 63.0,63.0 C -10.5,73.5 -10.5,73.5 0.0,0.0 Z" fill="#555555"/>
  <path d="M 19.0,4.0 C 1.7,0.3 1.7,0.3 3.0,18.0 C 20.3,21.7 20.3,21.7 19.0,4.0 Z" fill="#555555"/>
  ...
</svg>
```

---

## Edge Cases / Potensi Masalah

| Masalah | Penjelasan | Solusi |
|---------|------------|--------|
| Kurva kosong | Tidak ada data Bezier | Skip, generate SVG kosong |
| Koordinat negatif | Bezier bisa menghasilkan koordinat < 0 | SVG bisa handle (tinggal adjust viewBox) |
| Koordinat sangat besar | Out of bounds | Adjust viewBox atau clip |
| Format salah | JSON tidak sesuai | Validasi input |

---

## Cara Membuka Hasil

1. **Browser:** Drag & drop file `.svg` ke browser (Chrome, Firefox, Edge)
2. **Inkscape:** Buka langsung sebagai file vektor
3. **VS Code:** Buka file, install extension SVG
4. **Online:** https://www.svgviewer.dev/

---

## File yang Dihasilkan

| File | Keterangan |
|------|------------|
| `tahap5_svg_gen.py` | Script utama Tahap 5 |
| `*_output.svg` | File SVG final |
