"""
TAHAP 3 — Polygon Simplification (Ramer-Douglas-Peucker)
==========================================================
Mengurangi jumlah titik pada polygon hasil tracing (Tahap 2)
tanpa mengubah bentuk secara signifikan.

Algoritma Ramer-Douglas-Peucker (RDP) bekerja dengan:
1. Hubungkan titik pertama dan terakhir dengan garis lurus.
2. Cari titik terjauh dari garis tersebut.
3. Jika jarak > epsilon, tambahkan titik itu (recursive).
4. Jika jarak <= epsilon, buang semua titik di tengah.

Hasil: polygon dengan jumlah titik LEBIH SEDIKIT tapi bentuk hampir sama.
"""

import sys
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw


# =============================================================================
# MATEMATIKA: Jarak Titik ke Garis
# =============================================================================

def point_to_line_distance(point, line_start, line_end):
    """
    Hitung jarak perpendicular dari titik ke garis.

    ═══════════════════════════════════════════════════════════════
    PENJELASAN MATEMATIKA:
    ═══════════════════════════════════════════════════════════════

    Diberi:
    - Titik P = (px, py)
    - Garis dari A = (ax, ay) ke B = (bx, by)

    Rumus jarak perpendicular dari titik ke garis:

            |(bx-ax)(ay-py) - (ax-px)(by-ay)|
    d = ─────────────────────────────────────────
              sqrt((bx-ax)² + (by-ay)²)

    ═══════════════════════════════════════════════════════════════
    INTUISI:
    ═══════════════════════════════════════════════════════════════

    Bayangkan garis dari A ke B. Kita ingin tahu "seberapa jauh"
    titik P dari garis itu.

    - Kalau P tepat di atas garis → jarak = 0.
    - Kalau P jauh di samping → jarak = besar.

    Ini adalah jarak "perpendicular" (tegak lurus), bukan jarak
    ke titik ujung garis. Jadi yang diukur adalah "seberapa jauh
    titik menyimpang dari garis lurus".

    Penerapan di RDP:
    - Jika jarak > epsilon → titik ini PENTING (menyimpang jauh dari garis)
    - Jika jarak <= epsilon → titik ini BISA DIBUANG (tidak terlalu menyimpang)

    ═══════════════════════════════════════════════════════════════
    """
    px, py = point
    ax, ay = line_start
    bx, by = line_end

    # Panjang garis A→B (hipotenusa)
    line_len_sq = (bx - ax) ** 2 + (by - ay) ** 2

    # Kasus khusus: garis punya panjang 0 (A = B)
    if line_len_sq == 0:
        # Jarak dari P ke titik A
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5

    # Rumus jarak perpendicular:
    # |cross product| / |panjang garis|
    # Cross product vektor AP dan AB
    cross = abs((bx - ax) * (ay - py) - (ax - px) * (by - ay))
    distance = cross / (line_len_sq ** 0.5)

    return distance


# =============================================================================
# ALGORITMA RAMER-DOUGLAS-PEUCKER
# =============================================================================

def douglas_peucker(points, epsilon):
    """
    Implementasi Ramer-Douglas-Peucker (RDP) untuk simplifikasi polygon.

    ═══════════════════════════════════════════════════════════════
    ALUR ALGORITMA (Recursive / Divide and Conquer):
    ═══════════════════════════════════════════════════════════════

    MASUKAN:
    - points: list titik-titik polygon
    - epsilon: toleransi maksimum penyimpangan (dalam piksel)

    LANGKAH:
    1. Hubungkan titik PERTAMA (A) dan TERAKHIR (B) dengan garis lurus.
    2. Untuk setiap titik di ANTARA A dan B:
       - Hitung jarak titik ke garis A→B.
    3. Cari titik dengan jarak MAKSIMUM → sebut D.
    4. KONDISI:
       - Jika jarak(D) > epsilon:
         → Titik D PENTING! Simpan.
         → Recursive: proses [A...D] dan [D...B] secara terpisah.
       - Jika jarak(D) <= epsilon:
         → Semua titik antara A dan B BISA DIBUANG.
         → Simpan hanya A dan B.

    ═══════════════════════════════════════════════════════════════
    CONTOH VISUAL:
    ═══════════════════════════════════════════════════════════════

    Polygon asli (banyak titik):
        A---*---*---*---*---B
            *   *       *
                *   *

    Setelah RDP (epsilon sesuai):
        A-------*-------B
        (hanya titik yang menyimpang jauh dari garis A→B disimpan)

    ═══════════════════════════════════════════════════════════════

    Parameter:
    - points: list of (y, x) tuples
    - epsilon: float, toleransi dalam piksel

    Return: list of (y, x) yang sudah disederhanakan
    """
    # Kasus dasar: kurang dari 3 titik, tidak bisa disederhanakan
    if len(points) < 3:
        return points

    # Titik awal dan akhir SELALU disimpan
    first = points[0]
    last = points[-1]

    # Cari titik terjauh dari garis first→last
    max_dist = 0
    max_idx = 0

    for i in range(1, len(points) - 1):
        dist = point_to_line_distance(points[i], first, last)
        if dist > max_dist:
            max_dist = dist
            max_idx = i

    # KONDISI: Apakah titik terjauh cukup jauh dari garis?
    if max_dist > epsilon:
        # Ya! Titik ini PENTING (menyimpang jauh dari garis lurus).
        # Recursive: proses dua bagian secara terpisah.
        left = douglas_peucker(points[:max_idx + 1], epsilon)
        right = douglas_peucker(points[max_idx:], epsilon)

        # Gabungkan hasil (titik tengah max_idx tidak duplikat)
        return left[:-1] + right
    else:
        # Tidak! Semua titik antara A dan B cukup lurus.
        # Buang semua titik tengah, simpan hanya A dan B.
        return [first, last]


# =============================================================================
# WRAPPER: Simplifikasi Semua Kontur
# =============================================================================

def simplify_contours(contours, epsilon=2.0):
    """
    Simplifikasi semua kontur menggunakan Douglas-Peucker.

    Parameter:
    - contours: list of list titik (y, x)
    - epsilon: toleransi simplifikasi (semakin besar = makin banyak titik dibuang)

    Return: list of list titik yang sudah disederhanakan
    """
    simplified = []
    for i, contour in enumerate(contours):
        orig_len = len(contour)
        simp = douglas_peucker(contour, epsilon)
        simp_len = len(simp)
        reduction = (1 - simp_len / orig_len) * 100 if orig_len > 0 else 0
        print(f"  Kontur {i+1}: {orig_len} -> {simp_len} titik (hemat {reduction:.0f}%)")
        simplified.append(simp)
    return simplified


# =============================================================================
# VISUALISASI: Bandingkan Sebelum & Sesudah
# =============================================================================

def save_comparison_visualization(
    original_contours,
    simplified_contours,
    binary_shape,
    output_path,
):
    """
    Gambar visualisasi perbandingan: kontur asli vs hasil simplifikasi.
    """
    h, w = binary_shape
    img = np.ones((h, w, 3), dtype=np.uint8) * 240  # Background abu-abu terang

    colors = [
        (255, 80, 80),    # Merah untuk asli
        (80, 180, 80),    # Hijau untuk simplified
    ]

    # Gambar kontur asli (tipis, merah)
    for contour in original_contours:
        for y, x in contour:
            if 0 <= y < h and 0 <= x < w:
                img[y, x] = colors[0]

    # Gambar kontur simplified (lebih tebal, hijau)
    for simp in simplified_contours:
        for i in range(len(simp) - 1):
            y1, x1 = simp[i]
            y2, x2 = simp[i + 1]
            # Gambar garis antar titik (Bresenham sederhana)
            draw_line(img, y1, x1, y2, x2, colors[1])

        # Gambar titik simplified
        for y, x in simp:
            if 0 <= y < h and 0 <= x < w:
                img[y, x] = (0, 120, 255)  # Biru untuk titik

    Image.fromarray(img).save(output_path)
    print(f"Visualisasi disimpan: {output_path}")


def draw_line(img, y1, x1, y2, x2, color):
    """Gambar garis menggunakan Bresenham's line algorithm (manual)."""
    h, w = img.shape[:2]
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy

    while True:
        if 0 <= y1 < h and 0 <= x1 < w:
            img[y1, x1] = color
        if y1 == y2 and x1 == x2:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x1 += sx
        if e2 < dx:
            err += dx
            y1 += sy


# =============================================================================
# SAVE
# =============================================================================

def save_simplified_json(contours, output_path):
    """Simpan kontur hasil simplifikasi ke JSON."""
    with open(output_path, "w") as f:
        json.dump(contours, f)
    print(f"Kontur disimpan: {output_path}")


# =============================================================================
# MAIN: Pipeline Tahap 3
# =============================================================================

def simplify_pipeline(contours_path, epsilon=2.0, output_dir="."):
    """
    Pipeline Tahap 3: Load kontur → simplifikasi → simpan.
    """
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    stem = Path(contours_path).stem

    # Load kontur dari JSON
    with open(contours_path) as f:
        contours = json.load(f)

    print(f"Kontur dimuat: {len(contours)} kontur")
    print(f"Epsilon (toleransi): {epsilon} piksel")
    print()

    # Simpan kontur asli untuk perbandingan
    original_contours = [list(c) for c in contours]

    # Simplifikasi
    print("--- Douglas-Peucker Simplification ---")
    simplified = simplify_contours(contours, epsilon)

    # Hitung statistik
    total_orig = sum(len(c) for c in original_contours)
    total_simp = sum(len(c) for c in simplified)
    print(f"\nTotal: {total_orig} -> {total_simp} titik "
          f"(hemat {total_orig - total_simp} = "
          f"{(1 - total_simp/total_orig)*100:.0f}%)")

    # Simpan hasil
    save_simplified_json(simplified, str(output / f"{stem}_simplified.json"))

    return simplified


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Cara pakai:")
        print("  python tahap3_simplification.py <kontur.json> [epsilon]")
        print()
        print("Parameter:")
        print("  kontur.json  — file kontur dari Tahap 2")
        print("  epsilon      — toleransi simplifikasi dalam piksel (default=2.0)")
        print()
        print("Contoh:")
        print("  python tahap3_simplification.py test_binary_clean_contours.json")
        print("  python tahap3_simplification.py contours.json 5.0")
        sys.exit(1)

    contours_path = sys.argv[1]
    eps = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
    simplify_pipeline(contours_path, eps)
