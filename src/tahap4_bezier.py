"""
TAHAP 4 — Curve Fitting (Bezier)
==================================
Mengubah titik-titik polygon hasil Tahap 3 menjadi kurva Bezier kubik
menggunakan metode Schneider (Graphics Gems I, 1990).

Apa itu Bezier Curve?
- Kurva yang didefinisikan oleh 4 titik: P0, P1, P2, P3
- P0 = titik awal, P3 = titik akhir
- P1, P2 = titik kontrol (menentukan bentuk kurva)
- Rumus: B(t) = (1-t)³P0 + 3(1-t)²tP1 + 3(1-t)t²P2 + t³P3

Metode Schneider:
- Memecah garis jadi segmen-segmen
- Untuk tiap segmen, hitung titik kontrol optimal pakai least-squares
- Hasil: kurva Bezier yang mendekati titik-titik asli
"""

import sys
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw


# =============================================================================
# MATEMATIKA: Básier Basis Functions
# =============================================================================

def basis_matrix():
    """
    Matriks basis untuk Bezier kubik.

    ═══════════════════════════════════════════════════════════════
    PENJELASAN:
    ═══════════════════════════════════════════════════════════════

    Rumus Bezier kubik:
    B(t) = (1-t)³P0 + 3(1-t)²tP1 + 3(1-t)t²P2 + t³P3

    Bisa ditulis dalam bentuk matriks:
    B(t) = [t³ t² t 1] × M × [P0 P1 P2 P3]ᵀ

    Matriks M (basis matrix):
    ┌                 ┐   ┌                          ┐
    │ -1  3 -3  1     │   │ -1 +3 -3 +1              │
    │  3 -6  3  0     │   │ +3 -6 +3  0              │
    │ -3  3  0  0     │   │ -3 +3  0  0              │
    │  1  0  0  0     │   │ +1  0  0  0              │
    └                 ┘   └                          ┘

    ═══════════════════════════════════════════════════════════════
    """
    return np.array([
        [-1,  3, -3,  1],
        [ 3, -6,  3,  0],
        [-3,  3,  0,  0],
        [ 1,  0,  0,  0],
    ])


def bezier_point(t, p0, p1, p2, p3):
    """
    Hitung titik pada kurva Bezier untuk parameter t.

    Rumus: B(t) = (1-t)³P0 + 3(1-t)²tP1 + 3(1-t)t²P2 + t³P3

    Parameter:
    - t: float 0-1 (0 = titik awal, 1 = titik akhir)
    - p0, p1, p2, p3: 4 titik kontrol (tuple y, x)

    Return: titik (y, x) pada kurva
    """
    t2 = t * t
    t3 = t2 * t
    mt = 1 - t
    mt2 = mt * mt
    mt3 = mt2 * mt

    y = mt3*p0[0] + 3*mt2*t*p1[0] + 3*mt*t2*p2[0] + t3*p3[0]
    x = mt3*p0[1] + 3*mt2*t*p1[1] + 3*mt*t2*p2[1] + t3*p3[1]

    return (y, x)


# =============================================================================
# MATEMATIKA: Parameterisasi Chord-Length
# =============================================================================

def chord_length_parameterize(points):
    """
    Parameterisasi titik-titik berdasarkan panjang tali (chord length).

    ═══════════════════════════════════════════════════════════════
    PENJELASAN:
    ═══════════════════════════════════════════════════════════════

    Kita punya N titik data: Q₀, Q₁, ..., Qₙ₋₁

    Untuk least-squares, kita perlu tahu "posisi relatif" tiap titik
    di sepanjang garis. Parameterisasi = menentukan parameter t
    untuk setiap titik.

    Metode Chord Length:
    - Jarak dari Q₀ ke Qᵢ dibagi total jarak Q₀ ke Qₙ₋₁.
    - Titik pertama: t = 0
    - Titik terakhir: t = 1
    - Titik di antara: proporsional terhadap jarak kumulatif

    Contoh:
    - Q₀ ke Q₁ jarak = 3
    - Q₁ ke Q₂ jarak = 5
    - Q₂ ke Q₃ jarak = 2
    - Total = 10

    Maka:
    - t₀ = 0/10 = 0.0
    - t₁ = 3/10 = 0.3
    - t₂ = 8/10 = 0.8
    - t₃ = 10/10 = 1.0

    ═══════════════════════════════════════════════════════════════
    """
    n = len(points)
    params = np.zeros(n)
    params[0] = 0.0

    for i in range(1, n):
        dy = points[i][0] - points[i-1][0]
        dx = points[i][1] - points[i-1][1]
        dist = (dy*dy + dx*dx) ** 0.5
        params[i] = params[i-1] + dist

    # Normalisasi ke [0, 1]
    if params[-1] > 0:
        params /= params[-1]

    return params


# =============================================================================
# MATEMATIKA: Least-Squares Bezier Fitting (Schneider's Method)
# =============================================================================

def estimate_initial_tangents(points, params):
    """
    Estimasi vektor tangent di titik awal dan akhir.

    ═══════════════════════════════════════════════════════════════
    PENJELASAN:
    ═══════════════════════════════════════════════════════════════

    Untuk Bezier kubik, kita butuh 4 titik kontrol:
    - P0 = titik awal (sudah diketahui = Q₀)
    - P3 = titik akhir (sudah diketahui = Qₙ₋₁)
    - P1, P2 = titik kontrol yang harus DIHITUNG

    Schneider's method butuh "arah tangent" di ujung kurva:
    - Tangent awal: arah kurva saat t = 0 (dari P0 ke P1)
    - Tangent akhir: arah kurva saat t = 1 (dari P2 ke P3)

    Estimasi: rata-rata vektor dari titik pertama ke 2-3 titik berikutnya.

    ═══════════════════════════════════════════════════════════════
    """
    n = len(points)

    # Tangent awal: rata-rata vektor dari Q₀ ke Q₁ dan Q₂
    if n >= 3:
        d01 = (points[1][0] - points[0][0], points[1][1] - points[0][1])
        d02 = (points[2][0] - points[0][0], points[2][1] - points[0][1])
        t0 = (
            d01[0] * 0.5 + d02[0] * 0.5,
            d01[1] * 0.5 + d02[1] * 0.5,
        )
    elif n >= 2:
        t0 = (points[1][0] - points[0][0], points[1][1] - points[0][1])
    else:
        t0 = (0, 0)

    # Tangent akhir: rata-rata vektor dari Qₙ₋₁ ke Qₙ₋₂ dan Qₙ₋₃
    if n >= 3:
        dn1n2 = (points[-2][0] - points[-1][0], points[-2][1] - points[-1][1])
        dn1n3 = (points[-3][0] - points[-1][0], points[-3][1] - points[-1][1])
        t1 = (
            dn1n2[0] * 0.5 + dn1n3[0] * 0.5,
            dn1n2[1] * 0.5 + dn1n3[1] * 0.5,
        )
    elif n >= 2:
        t1 = (points[-2][0] - points[-1][0], points[-2][1] - points[-1][1])
    else:
        t1 = (0, 0)

    return t0, t1


def bezier_least_squares(points, t0, t1):
    """
    Hitung titik kontrol P1, P2 menggunakan least-squares.

    ═══════════════════════════════════════════════════════════════
    ALGORITMA SCHNEIDER (Graphics Gems I, 1990):
    ═══════════════════════════════════════════════════════════════

    Masukan:
    - Titik data: Q₀, Q₁, ..., Qₙ₋₁
    - Titik awal P0 = Q₀, titik akhir P3 = Qₙ₋₁
    - Vektor tangent awal (t0) dan akhir (t1)

    Yang dicari:
    - Titik kontrol P1 dan P2

    Langkah:
    1. Parameterisasi: tentukan tᵢ untuk tiap Qᵢ (chord length)
    2. Hitung matriks A dari basis functions B₁(tᵢ) dan B₂(tᵢ)
    3. Solve persamaan normal: (AᵀA)x = Aᵀb
       untuk mendapatkan P1 dan P2

    Rumus Bezier:
    B(t) = (1-t)³P0 + 3(1-t)²tP1 + 3(1-t)t²P2 + t³P3

    Karena P0 dan P3 sudah diketahui, kita pindahkan ke kanan:
    B(t) - (1-t)³P0 - t³P3 = 3(1-t)²tP1 + 3(1-t)t²P2

    Bentuk matriks:
    [A₁(tᵢ) A₂(tᵢ)] × [P1] = [Qᵢ - B₀(tᵢ)P0 - B₃(tᵢ)P3]
                           [P2]

    Di mana:
    - A₁(t) = 3(1-t)²t  (basis function untuk P1)
    - A₂(t) = 3(1-t)t²  (basis function untuk P2)

    ═══════════════════════════════════════════════════════════════
    """
    n = len(points)
    if n < 2:
        return points[0], points[-1], points[0], points[-1]

    p0 = points[0]
    p3 = points[-1]

    # Parameterisasi chord length
    params = chord_length_parameterize(points)

    # Hitung matriks A (basis functions)
    # A[i, 0] = B₁(tᵢ) = 3(1-tᵢ)²tᵢ  (koefisien untuk P1)
    # A[i, 1] = B₂(tᵢ) = 3(1-tᵢ)tᵢ²  (koefisien untuk P2)
    A = np.zeros((n, 2))
    for i in range(n):
        t = params[i]
        mt = 1 - t
        A[i, 0] = 3 * mt * mt * t      # B1
        A[i, 1] = 3 * mt * t * t       # B2

    # Hitung vektor b (titik data - kontribusi P0 dan P3)
    b = np.zeros((n, 2))
    for i in range(n):
        t = params[i]
        mt = 1 - t
        # Kontribusi P0 dan P3
        b0_contribution = mt * mt * mt * p0[0]   # (1-t)³ * P0.y
        b3_contribution = t * t * t * p3[0]      # t³ * P3.y
        b[i, 0] = points[i][0] - b0_contribution - b3_contribution

        b0_contribution = mt * mt * mt * p0[1]   # (1-t)³ * P0.x
        b3_contribution = t * t * t * p3[1]      # t³ * P3.x
        b[i, 1] = points[i][1] - b0_contribution - b3_contribution

    # Solve least-squares: AᵀAx = Aᵀb
    # x = [P1, P2]
    ATA = A.T @ A
    ATb = A.T @ b

    # Solve x dari ATA @ x = ATb
    try:
        x = np.linalg.solve(ATA, ATb)
    except np.linalg.LinAlgError:
        # Singular matrix, gunakan pseudoinverse
        x = np.linalg.lstsq(ATA, ATb, rcond=None)[0]

    p1 = (x[0, 0], x[0, 1])
    p2 = (x[1, 0], x[1, 1])

    return p0, p1, p2, p3


# =============================================================================
# PECah GARIS: Segmentation (Splitting)
# =============================================================================

def compute_max_error(points, p0, p1, p2, p3, params):
    """
    Hitung error maksimum antara titik data dan kurva Bezier.

    ═══════════════════════════════════════════════════════════════
    PENJELASAN:
    ═══════════════════════════════════════════════════════════════

    Untuk menentukan apakah kurva Bezier cukup bagus mendekati
    titik-titik data, kita hitung "error" (deviasi) terbesar.

    Error = jarak terbesar antara titik data Qᵢ dan titik
    terdekat pada kurva Bezier.

    Jika error > tolerance → kurva perlu dipecah (split)
    Jika error <= tolerance → kurva sudah cukup bagus

    ═══════════════════════════════════════════════════════════════
    """
    max_dist = 0
    split_idx = 0

    for i in range(1, len(points) - 1):
        t = params[i]
        bp = bezier_point(t, p0, p1, p2, p3)

        dy = points[i][0] - bp[0]
        dx = points[i][1] - bp[1]
        dist = (dy*dy + dx*dx) ** 0.5

        if dist > max_dist:
            max_dist = dist
            split_idx = i

    return max_dist, split_idx


def fit_bezier_segment(points, max_error):
    """
    Fit Bezier kubik ke segmen titik dengan recursive splitting.

    ═══════════════════════════════════════════════════════════════
    ALUR ALGORITMA:
    ═══════════════════════════════════════════════════════════════

    1. Parameterisasi titik (chord length)
    2. Estimasi tangent awal & akhir
    3. Hitung titik kontrol P1, P2 (least-squares)
    4. Hitung error maksimum
    5. Jika error > tolerance:
       → Pecah titik di posisi error max
       → Recursive: fit bagian kiri dan kanan
    6. Jika error <= tolerance:
       → Simpan kurva Bezier ini

    ═══════════════════════════════════════════════════════════════
    """
    if len(points) < 2:
        return []

    if len(points) == 2:
        # Hanya 2 titik, garis lurus → bisa langsung jadi Bezier
        p0 = points[0]
        p3 = points[-1]
        # Titik kontrol = 1/3 dan 2/3 di antara p0 dan p3
        p1 = ((2*p0[0] + p3[0])/3, (2*p0[1] + p3[1])/3)
        p2 = ((p0[0] + 2*p3[0])/3, (p0[1] + 2*p3[1])/3)
        return [(p0, p1, p2, p3)]

    # Parameterisasi
    params = chord_length_parameterize(points)

    # Estimasi tangent
    t0, t1 = estimate_initial_tangents(points, params)

    # Fit Bezier
    p0, p1, p2, p3 = bezier_least_squares(points, t0, t1)

    # Hitung error
    max_dist, split_idx = compute_max_error(points, p0, p1, p2, p3, params)

    if max_dist <= max_error:
        # Error cukup kecil, simpan kurva ini
        return [(p0, p1, p2, p3)]
    else:
        # Error terlalu besar, pecah dan recursive
        left = fit_bezier_segment(points[:split_idx + 1], max_error)
        right = fit_bezier_segment(points[split_idx:], max_error)
        return left + right


# =============================================================================
# MAIN: Fit Semua Kontur
# =============================================================================

def fit_contours_to_bezier(contours, max_error=2.0):
    """
    Fit kurva Bezier ke semua kontur.

    Parameter:
    - contours: list of list titik (y, x)
    - max_error: toleransi error dalam piksel

    Return: list of list kurva Bezier
             tiap kurva = (p0, p1, p2, p3)
    """
    all_beziers = []

    for i, contour in enumerate(contours):
        if len(contour) < 2:
            continue

        beziers = fit_bezier_segment(contour, max_error)
        all_beziers.append(beziers)

        total_pts = sum(4 for _ in beziers)
        print(f"  Kontur {i+1}: {len(contour)} titik -> {len(beziers)} kurva Bezier")

    return all_beziers


# =============================================================================
# VISUALISASI: Gambar Kurva Bezier
# =============================================================================

def draw_bezier_on_image(beziers, shape, output_path, original_contours=None):
    """Gambar kurva Bezier di atas gambar."""
    h, w = shape
    img = np.ones((h, w, 3), dtype=np.uint8) * 240

    # Gambar kontur asli (abu-abu tipis)
    if original_contours:
        for contour in original_contours:
            for y, x in contour:
                if 0 <= y < h and 0 <= x < w:
                    img[y, x] = (180, 180, 180)

    # Gambar kurva Bezier
    colors = [
        (220, 50, 50), (50, 180, 50), (50, 50, 220),
        (220, 160, 0), (160, 0, 220), (0, 180, 180),
    ]

    for idx, segmen in enumerate(beziers):
        color = colors[idx % len(colors)]
        for curve in segmen:
            p0, p1, p2, p3 = curve
            # Gambar kurva dengan sampling titik
            prev = None
            for t_int in range(0, 51):
                t = t_int / 50.0
                y, x = bezier_point(t, p0, p1, p2, p3)
                yi, xi = int(y), int(x)
                if 0 <= yi < h and 0 <= xi < w:
                    img[yi, xi] = color
                if prev is not None:
                    # Gambar garis tipis antar titik sampling
                    py, px = int(prev[0]), int(prev[1])
                    if 0 <= py < h and 0 <= px < w:
                        img[py, px] = color
                prev = (y, x)

    Image.fromarray(img).save(output_path)
    print(f"Visualisasi disimpan: {output_path}")


# =============================================================================
# SAVE: Simpan Kurva Bezier ke JSON
# =============================================================================

def save_bezier_json(beziers, output_path):
    """Simpan kurva Bezier ke JSON untuk Tahap 5."""
    data = []
    for segmen in beziers:
        curves = []
        for p0, p1, p2, p3 in segmen:
            curves.append([list(p0), list(p1), list(p2), list(p3)])
        data.append(curves)

    with open(output_path, "w") as f:
        json.dump(data, f)
    print(f"Kurva Bezier disimpan: {output_path}")


# =============================================================================
# MAIN: Pipeline
# =============================================================================

def bezier_pipeline(contours_path, max_error=2.0, output_dir="."):
    """Pipeline Tahap 4."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    stem = Path(contours_path).stem.replace("_simplified", "")

    # Load kontur
    with open(contours_path) as f:
        contours = json.load(f)

    print(f"Kontur dimuat: {len(contours)} kontur")
    print(f"Max error (toleransi): {max_error} piksel")
    print()

    # Fit Bezier
    print("--- Bezier Curve Fitting (Schneider's Method) ---")
    beziers = fit_contours_to_bezier(contours, max_error)

    # Statistik
    total_curves = sum(len(b) for b in beziers)
    print(f"\nTotal kurva Bezier: {total_curves}")

    # Simpan
    save_bezier_json(beziers, str(output / f"{stem}_bezier.json"))

    return beziers


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Cara pakai:")
        print("  python tahap4_bezier.py <kontur_simplified.json> [max_error]")
        print()
        print("Contoh:")
        print("  python tahap4_bezier.py test_binary_clean_contours_simplified.json")
        print("  python tahap4_bezier.py contours.json 3.0")
        sys.exit(1)

    contours_path = sys.argv[1]
    err = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
    bezier_pipeline(contours_path, err)
