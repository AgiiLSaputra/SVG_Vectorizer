"""
TAHAP 6 — Full Color (K-Means Clustering Manual)
===================================================
Mengkonversi gambar berwarna menjadi SVG berwarna dengan:
1. K-Means clustering manual untuk reduksi warna
2. Pisahkan tiap klaster jadi layer biner
3. Jalankan Tahap 2-5 untuk tiap layer
4. Gabungkan semua path jadi satu SVG dengan fill warna masing-masing

Tanpa scikit-learn! Semua diimplementasikan manual.
"""

import sys
import json
from pathlib import Path
import numpy as np
from PIL import Image


# =============================================================================
# K-MEANS CLUSTERING (Manual)
# =============================================================================

def kmeans_init_centroids(pixels, k):
    """
    Inisialisasi centroid secara acak.

    ═══════════════════════════════════════════════════════════════
    PENJELASAN:
    ═══════════════════════════════════════════════════════════════

    K-Means membutuhkan K titik pusat (centroid) sebagai titik awal.
    Cara termudah: pilih K piksel secara ACAK dari gambar.

    Ada cara lebih baik (K-Means++), tapi untuk learning
    kita pakai cara sederhana dulu.

    ═══════════════════════════════════════════════════════════════
    """
    n = pixels.shape[0]
    indices = np.random.choice(n, size=k, replace=False)
    return pixels[indices].copy()


def kmeans_assign_clusters(pixels, centroids):
    """
    Assign tiap piksel ke centroid terdekat.

    ═══════════════════════════════════════════════════════════════
    PENJELASAN:
    ═══════════════════════════════════════════════════════════════

    Untuk tiap piksel:
    1. Hitung jarak ke SEMUA centroid.
    2. Pilih centroid TERDEKAT → piksel itu masuk klaster centroid.

    Jarak = Euclidean Distance dalam ruang warna RGB:
    d = sqrt((R₁-R₂)² + (G₁-G₂)² + (B₁-B₂)²)

    ═══════════════════════════════════════════════════════════════
    """
    n = pixels.shape[0]
    k = centroids.shape[0]
    clusters = np.zeros(n, dtype=int)

    for i in range(n):
        min_dist = float('inf')
        for j in range(k):
            # Jarak Euclidean: sqrt(sum((a-b)²))
            diff = pixels[i] - centroids[j]
            dist = np.sqrt(np.sum(diff ** 2))
            if dist < min_dist:
                min_dist = dist
                clusters[i] = j

    return clusters


def kmeans_update_centroids(pixels, clusters, k):
    """
    Update centroid: pindahkan ke rata-rata piksel di tiap klaster.

    ═══════════════════════════════════════════════════════════════
    PENJELASAN:
    ═══════════════════════════════════════════════════════════════

    Setelah semua piksel di-assign ke klaster:
    - Pindahkan centroid klaster j ke TENGAH-TENGAH (rata-rata)
      semua piksel di klaster itu.

    centroid_j = mean(piksel yang masuk klaster j)

    Ini memastikan centroid merepresentasikan "warna rata-rata"
    dari klaster tersebut.

    ═══════════════════════════════════════════════════════════════
    """
    n = pixels.shape[0]
    k_dim = pixels.shape[1]
    new_centroids = np.zeros((k, k_dim))

    for j in range(k):
        # Ambil semua piksel yang masuk klaster j
        mask = clusters == j
        if np.sum(mask) > 0:
            # Hitung rata-rata
            new_centroids[j] = pixels[mask].mean(axis=0)
        else:
            # Klaster kosong → centroid tetap di posisi lama
            new_centroids[j] = pixels[np.random.randint(n)]

    return new_centroids


def kmeans(pixels, k, max_iters=50, tol=1e-4):
    """
    K-Means Clustering: kelompokkan piksel jadi K klaster.

    ═══════════════════════════════════════════════════════════════
    ALGORITMA K-MEANS:
    ═══════════════════════════════════════════════════════════════

    1. Inisialisasi K centroid secara acak.
    2. ULANGI sampai konvergen:
       a. Assign tiap piksel ke centroid terdekat.
       b. Update centroid ke rata-rata klaster.
       c. Jika perubahan centroid < toleransi → berhenti.
    3. Return: label klaster tiap piksel + centroid (warna).

    ═══════════════════════════════════════════════════════════════
    """
    print(f"K-Means: {pixels.shape[0]} piksel, {k} klaster, max {max_iters} iterasi")

    # Inisialisasi centroid
    centroids = kmeans_init_centroids(pixels, k)

    for iteration in range(max_iters):
        # Langkah 1: Assign piksel ke klaster
        clusters = kmeans_assign_clusters(pixels, centroids)

        # Langkah 2: Update centroid
        new_centroids = kmeans_update_centroids(pixels, clusters, k)

        # Langkah 3: Cek konvergensi
        shift = np.sqrt(np.sum((new_centroids - centroids) ** 2))
        centroids = new_centroids

        if shift < tol:
            print(f"  Konvergen di iterasi {iteration + 1} (shift={shift:.6f})")
            break

        if (iteration + 1) % 10 == 0:
            print(f"  Iterasi {iteration + 1}: shift={shift:.4f}")

    return clusters, centroids


def reduce_colors(image_array, n_colors=16):
    """
    Reduksi warna gambar menggunakan K-Means.

    ═══════════════════════════════════════════════════════════════
    PENJELASAN:
    ═══════════════════════════════════════════════════════════════

    Gambar asli punya hingga 16 juta warna (256³).
    Kita reduksi jadi N warna saja supaya:
    1. Lebih mudah diproses (lebih sedikit layer).
    2. File SVG lebih kecil.
    3. Efek "posterisasi" yang artistik.

    ═══════════════════════════════════════════════════════════════
    """
    h, w, c = image_array.shape
    pixels = image_array.reshape(-1, c).astype(np.float64)

    clusters, centroids = kmeans(pixels, n_colors)

    # Bangun gambar baru dengan warna yang sudah direduksi
    reduced = centroids[clusters].reshape(h, w, c).astype(np.uint8)
    labels = clusters.reshape(h, w)

    # Tampilkan distribusi klaster
    print(f"\nDistribusi klaster:")
    for j in range(n_colors):
        count = np.sum(labels == j)
        r, g, b = centroids[j].astype(int)
        pct = count / (h * w) * 100
        print(f"  Klaster {j}: rgb({r},{g},{b}) #{r:02x}{g:02x}{b:02x} = {pct:.1f}%")

    return reduced, labels, centroids


# =============================================================================
# LAYER: Pisahkan per warna
# =============================================================================

def create_color_layers(labels, n_colors):
    """
    Buat layer biner untuk tiap klaster warna.

    Layer = array 2D di mana 0 = piksel ini milik klaster ini,
    1 = piksel lain.

    ═══════════════════════════════════════════════════════════════
    PENJELASAN:
    ═══════════════════════════════════════════════════════════════

    Misal gambar punya 3 warna: merah, biru, hijau.

    Layer merah:
    ┌───┬───┬───┐
    │ 1 │ 1 │ 0 │   0 = merah (objek)
    ├───┼───┼───┤   1 = bukan merah (background)
    │ 1 │ 1 │ 0 │
    └───┴───┴───┘

    Layer biru:
    ┌───┬───┬───┐
    │ 1 │ 1 │ 1 │
    ├───┼───┼───┤   0 = biru
    │ 1 │ 1 │ 1 │   1 = bukan biru
    └───┴───┴───┘

    Setiap layer di-trace secara terpisah seperti Tahap 2.

    ═══════════════════════════════════════════════════════════════
    """
    layers = []
    for j in range(n_colors):
        layer = (labels != j).astype(int)  # 0 = warna ini, 1 = lainnya
        pixel_count = np.sum(labels == j)
        if pixel_count > 0:
            layers.append((j, layer))
    return layers


# =============================================================================
# TRACING: Import dari Tahap 2
# =============================================================================

def moore_neighbor_trace(binary):
    """Moore-Neighbor tracing (sama dengan Tahap 2)."""
    DIRECTIONS = [
        (0, 1), (1, 1), (1, 0), (1, -1),
        (0, -1), (-1, -1), (-1, 0), (-1, 1),
    ]
    OPPOSITE = [4, 5, 6, 7, 0, 1, 2, 3]

    def is_black(b, y, x):
        h, w = b.shape
        if y < 0 or y >= h or x < 0 or x >= w:
            return False
        return b[y, x] == 0

    def trace_single(binary, sy, sx):
        cy, cx = sy, sx - 1
        prev_dir = 4
        contour = [(sy, sx)]
        for _ in range(binary.shape[0] * binary.shape[1]):
            found = False
            for i in range(8):
                di = (prev_dir + 1 + i) % 8
                dy, dx = DIRECTIONS[di]
                ny, nx = cy + dy, cx + dx
                if is_black(binary, ny, nx):
                    contour.append((ny, nx))
                    prev_dir = OPPOSITE[di]
                    cy, cx = ny, nx
                    found = True
                    break
            if not found:
                break
            if (cy, cx) == (sy, sx) and len(contour) > 2:
                break
        return contour

    h, w = binary.shape
    visited = np.zeros((h, w), dtype=bool)
    contours = []

    for y in range(h):
        for x in range(w):
            if binary[y, x] == 0 and not visited[y, x]:
                if x == 0 or binary[y, x - 1] == 1:
                    contour = trace_single(binary, y, x)
                    for py, px in contour:
                        if 0 <= py < h and 0 <= px < w:
                            visited[py, px] = True
                    if len(contour) >= 4:
                        contours.append(contour)

    return contours


# =============================================================================
# SIMPLIFICATION: Import dari Tahap 3
# =============================================================================

def point_to_line_distance(point, line_start, line_end):
    px, py = point
    ax, ay = line_start
    bx, by = line_end
    l2 = (bx - ax) ** 2 + (by - ay) ** 2
    if l2 == 0:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    return abs((bx - ax) * (ay - py) - (ax - px) * (by - ay)) / (l2 ** 0.5)


def douglas_peucker(points, epsilon):
    if len(points) < 3:
        return points
    first, last = points[0], points[-1]
    max_dist, max_idx = 0, 0
    for i in range(1, len(points) - 1):
        d = point_to_line_distance(points[i], first, last)
        if d > max_dist:
            max_dist = d
            max_idx = i
    if max_dist > epsilon:
        left = douglas_peucker(points[:max_idx + 1], epsilon)
        right = douglas_peucker(points[max_idx:], epsilon)
        return left[:-1] + right
    return [first, last]


# =============================================================================
# BEZIER: Import dari Tahap 4
# =============================================================================

def chord_length_parameterize(points):
    n = len(points)
    params = np.zeros(n)
    for i in range(1, n):
        dy = points[i][0] - points[i - 1][0]
        dx = points[i][1] - points[i - 1][1]
        params[i] = params[i - 1] + (dy * dy + dx * dx) ** 0.5
    if params[-1] > 0:
        params /= params[-1]
    return params


def bezier_least_squares(points, params):
    n = len(points)
    if n < 2:
        return [(points[0], points[0], points[-1], points[-1])]
    p0, p3 = points[0], points[-1]

    A = np.zeros((n, 2))
    for i in range(n):
        t = params[i]
        A[i, 0] = 3 * (1 - t) ** 2 * t
        A[i, 1] = 3 * (1 - t) * t ** 2

    b = np.zeros((n, 2))
    for i in range(n):
        t = params[i]
        b[i, 0] = points[i][0] - (1 - t) ** 3 * p0[0] - t ** 3 * p3[0]
        b[i, 1] = points[i][1] - (1 - t) ** 3 * p0[1] - t ** 3 * p3[1]

    ATA = A.T @ A
    ATb = A.T @ b
    try:
        x = np.linalg.solve(ATA, ATb)
    except np.linalg.LinAlgError:
        x = np.linalg.lstsq(ATA, ATb, rcond=None)[0]

    p1 = (x[0, 0], x[0, 1])
    p2 = (x[1, 0], x[1, 1])
    return [(p0, p1, p2, p3)]


def bezier_point(t, p0, p1, p2, p3):
    mt = 1 - t
    y = mt ** 3 * p0[0] + 3 * mt ** 2 * t * p1[0] + 3 * mt * t ** 2 * p2[0] + t ** 3 * p3[0]
    x = mt ** 3 * p0[1] + 3 * mt ** 2 * t * p1[1] + 3 * mt * t ** 2 * p2[1] + t ** 3 * p3[1]
    return (y, x)


def fit_bezier_segment(points, max_error):
    if len(points) < 2:
        return []
    if len(points) == 2:
        p0, p3 = points[0], points[-1]
        p1 = ((2 * p0[0] + p3[0]) / 3, (2 * p0[1] + p3[1]) / 3)
        p2 = ((p0[0] + 2 * p3[0]) / 3, (p0[1] + 2 * p3[1]) / 3)
        return [(p0, p1, p2, p3)]

    params = chord_length_parameterize(points)
    curves = bezier_least_squares(points, params)

    p0, p1, p2, p3 = curves[0]
    max_dist, split_idx = 0, len(points) // 2
    for i in range(1, len(points) - 1):
        bp = bezier_point(params[i], p0, p1, p2, p3)
        d = ((points[i][0] - bp[0]) ** 2 + (points[i][1] - bp[1]) ** 2) ** 0.5
        if d > max_dist:
            max_dist = d
            split_idx = i

    if max_dist <= max_error:
        return curves
    else:
        left = fit_bezier_segment(points[:split_idx + 1], max_error)
        right = fit_bezier_segment(points[split_idx:], max_error)
        return left + right


# =============================================================================
# SVG GENERATION: Import dari Tahap 5
# =============================================================================

def bezier_to_svg_path(curves):
    if not curves:
        return ""
    parts = []
    for i, (p0, p1, p2, p3) in enumerate(curves):
        if i == 0:
            parts.append(f"M {p0[1]:.1f},{p0[0]:.1f}")
        parts.append(f"C {p1[1]:.1f},{p1[0]:.1f} {p2[1]:.1f},{p2[0]:.1f} {p3[1]:.1f},{p3[0]:.1f}")
    parts.append("Z")
    return " ".join(parts)


# =============================================================================
# MAIN: Pipeline Full Color
# =============================================================================

def full_color_pipeline(image_path, n_colors=8, epsilon=2.0, max_error=2.0, output_path=None):
    """
    Pipeline lengkap Tahap 6: Gambar Berwarna → SVG Berwarna.
    """
    stem = Path(image_path).stem

    if output_path is None:
        output_path = str(Path(image_path).parent / f"{stem}_fullcolor.svg")

    # 1. Load gambar
    img = Image.open(image_path).convert("RGB")
    pixels = np.array(img)
    h, w = pixels.shape[:2]
    print(f"Gambar dimuat: {w}x{h}")

    # 2. Reduksi warna dengan K-Means
    print(f"\n--- K-Means Clustering (K={n_colors}) ---")
    reduced, labels, centroids = reduce_colors(pixels, n_colors)

    # Simpan gambar reduksi
    reduced_path = str(Path(image_path).parent / f"{stem}_reduced_{n_colors}.png")
    Image.fromarray(reduced).save(reduced_path)
    print(f"\nGambar reduksi disimpan: {reduced_path}")

    # 3. Buat layer per warna
    print(f"\n--- Membuat Layer per Warna ---")
    layers = create_color_layers(labels, n_colors)
    print(f"Layer valid: {len(layers)} dari {n_colors} klaster")

    # 4. Proses tiap layer (Tahap 2-5)
    print(f"\n--- Proses Tiap Layer ---")
    svg_paths = []
    colors_used = []

    for color_idx, layer in layers:
        r, g, b = centroids[color_idx].astype(int)
        hex_color = f"#{r:02x}{g:02x}{b:02x}"

        # Trace
        contours = moore_neighbor_trace(layer)
        if not contours:
            continue

        # Simplify
        simplified = []
        for c in contours:
            s = douglas_peucker(c, epsilon)
            if len(s) >= 2:
                simplified.append(s)

        # Bezier fit
        all_curves = []
        for s in simplified:
            curves = fit_bezier_segment(s, max_error)
            all_curves.extend(curves)

        if all_curves:
            path_str = bezier_to_svg_path(all_curves)
            svg_paths.append((path_str, hex_color))
            colors_used.append(hex_color)
            print(f"  rgb({r},{g},{b}) {hex_color}: {len(contours)} kontur -> {len(all_curves)} kurva")

    # 5. Generate SVG
    print(f"\n--- SVG Generation ---")
    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        f'  <rect width="100%" height="100%" fill="white"/>',
    ]

    for path_str, color in svg_paths:
        svg_lines.append(f'  <path d="{path_str}" fill="{color}"/>')

    svg_lines.append('</svg>')

    with open(output_path, "w") as f:
        f.write("\n".join(svg_lines))

    print(f"SVG disimpan: {output_path}")
    print(f"Total path: {len(svg_paths)}")
    print(f"Warna digunakan: {colors_used}")

    return output_path


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Cara pakai:")
        print("  python tahap6_fullcolor.py <gambar> [n_colors] [epsilon] [max_error]")
        print()
        print("Contoh:")
        print("  python tahap6_fullcolor.py logo.png")
        print("  python tahap6_fullcolor.py photo.jpg 16 2.0 3.0")
        print()
        print("Parameter:")
        print("  n_colors  — jumlah warna (default=8)")
        print("  epsilon   — toleransi simplifikasi (default=2.0)")
        print("  max_error — toleransi Bezier (default=2.0)")
        sys.exit(1)

    image_path = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    eps = float(sys.argv[3]) if len(sys.argv) > 3 else 2.0
    err = float(sys.argv[4]) if len(sys.argv) > 4 else 2.0
    full_color_pipeline(image_path, n, eps, err)
