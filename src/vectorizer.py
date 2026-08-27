"""
SVG Vectorizer — Program Utama
================================
Konversi gambar (raster) menjadi SVG (vector) dalam satu command.

Cara pakai:
  python vectorizer.py <gambar_input> [options]

Contoh:
  python vectorizer.py logo.png
  python vectorizer.py photo.jpg -o output.svg -c 16
  python vectorizer.py icon.png --mode color --colors 8
"""

import sys
import os
import json
import argparse
import numpy as np
from pathlib import Path
from PIL import Image


# =============================================================================
# 1. PREPROCESSING (Tahap 1)
# =============================================================================

def load_image(image_path):
    """Load gambar dan konversi ke array RGB float64."""
    img = Image.open(image_path)
    img = img.convert("RGB")
    return np.array(img, dtype=np.float64)


def rgb_to_grayscale(pixels):
    """Konversi RGB ke grayscale (weighted average)."""
    return 0.299 * pixels[:, :, 0] + 0.587 * pixels[:, :, 1] + 0.114 * pixels[:, :, 2]


def create_gaussian_kernel(size, sigma):
    """Buat kernel Gaussian."""
    ax = np.arange(size) - size // 2
    xx, yy = np.meshgrid(ax, ax)
    kernel = np.exp(-(xx**2 + yy**2) / (2 * sigma**2))
    return kernel / kernel.sum()


def apply_gaussian_blur(image, kernel_size=3, sigma=1.0):
    """Terapkan Gaussian blur."""
    if sigma <= 0:
        return image
    kernel = create_gaussian_kernel(kernel_size, sigma)
    h, w = image.shape
    k = kernel_size // 2
    output = np.zeros_like(image)
    padded = np.pad(image, k, mode='edge')
    for y in range(h):
        for x in range(w):
            region = padded[y:y + kernel_size, x:x + kernel_size]
            output[y, x] = np.sum(region * kernel)
    return output


def otsu_threshold(image):
    """Hitung threshold optimal dengan Otsu's method."""
    hist, _ = np.histogram(image.ravel(), bins=256, range=(0, 256))
    total = image.size
    prob = hist / total
    omega = np.cumsum(prob)
    mean = np.cumsum(prob * np.arange(256))
    global_mean = mean[-1]
    variance = np.zeros(256)
    for t in range(256):
        if 0 < omega[t] < 1:
            variance[t] = (global_mean * omega[t] - mean[t])**2 / (omega[t] * (1 - omega[t]))
    return np.argmax(variance)


def threshold_binary(image, threshold=None):
    """Binerisasi gambar grayscale."""
    if threshold is None:
        threshold = otsu_threshold(image)
    return np.where(image <= threshold, 0, 1)


# =============================================================================
# 2. K-MEANS CLUSTERING (Tahap 6)
# =============================================================================

def kmeans(pixels, k, max_iters=50, tol=1e-4):
    """K-Means clustering manual."""
    n = pixels.shape[0]
    indices = np.random.choice(n, size=k, replace=False)
    centroids = pixels[indices].copy()

    for _ in range(max_iters):
        clusters = np.zeros(n, dtype=int)
        for i in range(n):
            dists = np.sqrt(np.sum((centroids - pixels[i])**2, axis=1))
            clusters[i] = np.argmin(dists)

        new_centroids = np.zeros_like(centroids)
        for j in range(k):
            mask = clusters == j
            if np.sum(mask) > 0:
                new_centroids[j] = pixels[mask].mean(axis=0)
            else:
                new_centroids[j] = pixels[np.random.randint(n)]

        shift = np.sqrt(np.sum((new_centroids - centroids)**2))
        centroids = new_centroids
        if shift < tol:
            break

    return clusters, centroids


# =============================================================================
# 3. CONTOUR TRACING (Tahap 2)
# =============================================================================

DIRECTIONS = [
    (0, 1), (1, 1), (1, 0), (1, -1),
    (0, -1), (-1, -1), (-1, 0), (-1, 1),
]
OPPOSITE = [4, 5, 6, 7, 0, 1, 2, 3]


def is_black(binary, y, x):
    h, w = binary.shape
    if y < 0 or y >= h or x < 0 or x >= w:
        return False
    return binary[y, x] == 0


def moore_neighbor_trace(binary):
    """Moore-Neighbor boundary tracing."""
    h, w = binary.shape
    visited = np.zeros((h, w), dtype=bool)
    all_contours = []

    def trace_single(sy, sx):
        cy, cx = sy, sx - 1
        prev_dir = 4
        contour = [(sy, sx)]
        for _ in range(h * w):
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

    for y in range(h):
        for x in range(w):
            if binary[y, x] == 0 and not visited[y, x]:
                if x == 0 or binary[y, x - 1] == 1:
                    contour = trace_single(y, x)
                    for py, px in contour:
                        if 0 <= py < h and 0 <= px < w:
                            visited[py, px] = True
                    if len(contour) >= 4:
                        all_contours.append(contour)

    return all_contours


# =============================================================================
# 4. SIMPLIFICATION (Tahap 3)
# =============================================================================

def point_to_line_distance(point, line_start, line_end):
    px, py = point
    ax, ay = line_start
    bx, by = line_end
    l2 = (bx - ax)**2 + (by - ay)**2
    if l2 == 0:
        return ((px - ax)**2 + (py - ay)**2)**0.5
    return abs((bx - ax) * (ay - py) - (ax - px) * (by - ay)) / (l2**0.5)


def douglas_peucker(points, epsilon):
    """Ramer-Douglas-Peucker polygon simplification."""
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
# 5. BEZIER CURVE FITTING (Tahap 4)
# =============================================================================

def chord_length_parameterize(points):
    n = len(points)
    params = np.zeros(n)
    for i in range(1, n):
        dy = points[i][0] - points[i - 1][0]
        dx = points[i][1] - points[i - 1][1]
        params[i] = params[i - 1] + (dy * dy + dx * dx)**0.5
    if params[-1] > 0:
        params /= params[-1]
    return params


def bezier_point(t, p0, p1, p2, p3):
    mt = 1 - t
    y = mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0]
    x = mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1]
    return (y, x)


def bezier_least_squares(points, params):
    """Schneider's least-squares Bezier fitting."""
    n = len(points)
    p0, p3 = points[0], points[-1]

    A = np.zeros((n, 2))
    for i in range(n):
        t = params[i]
        A[i, 0] = 3 * (1 - t)**2 * t
        A[i, 1] = 3 * (1 - t) * t**2

    b = np.zeros((n, 2))
    for i in range(n):
        t = params[i]
        b[i, 0] = points[i][0] - (1 - t)**3 * p0[0] - t**3 * p3[0]
        b[i, 1] = points[i][1] - (1 - t)**3 * p0[1] - t**3 * p3[1]

    ATA = A.T @ A
    ATb = A.T @ b
    try:
        x = np.linalg.solve(ATA, ATb)
    except np.linalg.LinAlgError:
        x = np.linalg.lstsq(ATA, ATb, rcond=None)[0]

    p1 = (x[0, 0], x[0, 1])
    p2 = (x[1, 0], x[1, 1])
    return [(p0, p1, p2, p3)]


def fit_bezier_segment(points, max_error):
    """Recursive Bezier fitting dengan splitting."""
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
        d = ((points[i][0] - bp[0])**2 + (points[i][1] - bp[1])**2)**0.5
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
# 6. SVG GENERATION (Tahap 5)
# =============================================================================

def bezier_to_svg_path(curves):
    """Konversi kurva Bezier ke SVG path string."""
    if not curves:
        return ""
    parts = []
    for i, (p0, p1, p2, p3) in enumerate(curves):
        if i == 0:
            parts.append(f"M {p0[1]:.1f},{p0[0]:.1f}")
        parts.append(f"C {p1[1]:.1f},{p1[0]:.1f} {p2[1]:.1f},{p2[0]:.1f} {p3[1]:.1f},{p3[0]:.1f}")
    parts.append("Z")
    return " ".join(parts)


def generate_svg(svg_paths, width, height, output_path):
    """Generate file SVG."""
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '  <rect width="100%" height="100%" fill="white"/>',
    ]
    for path_str, color in svg_paths:
        lines.append(f'  <path d="{path_str}" fill="{color}"/>')
    lines.append('</svg>')

    with open(output_path, "w") as f:
        f.write("\n".join(lines))


# =============================================================================
# PIPELINE UTAMA
# =============================================================================

def process_single_color(pixels, epsilon, max_error):
    """Pipeline hitam-putih: grayscale → threshold → trace → simplify → bezier."""
    gray = rgb_to_grayscale(pixels)
    blurred = apply_gaussian_blur(gray, 3, 1.0)
    binary = threshold_binary(blurred)
    contours = moore_neighbor_trace(binary)

    all_curves = []
    for c in contours:
        s = douglas_peucker(c, epsilon)
        if len(s) >= 2:
            curves = fit_bezier_segment(s, max_error)
            all_curves.extend(curves)

    return all_curves, "#555555"


def process_full_color(pixels, n_colors, epsilon, max_error):
    """Pipeline full color: k-means → per-layer trace → bezier."""
    h, w, c = pixels.shape
    flat_pixels = pixels.reshape(-1, c).astype(np.float64)

    print(f"  K-Means clustering (K={n_colors})...")
    clusters, centroids = kmeans(flat_pixels, n_colors)
    labels = clusters.reshape(h, w)

    svg_paths = []
    for j in range(n_colors):
        mask = labels != j
        layer = mask.astype(int)
        r, g, b = centroids[j].astype(int)
        hex_color = f"#{r:02x}{g:02x}{b:02x}"

        contours = moore_neighbor_trace(layer)
        if not contours:
            continue

        all_curves = []
        for c in contours:
            s = douglas_peucker(c, epsilon)
            if len(s) >= 2:
                curves = fit_bezier_segment(s, max_error)
                all_curves.extend(curves)

        if all_curves:
            path_str = bezier_to_svg_path(all_curves)
            svg_paths.append((path_str, hex_color))

    return svg_paths


def vectorize(image_path, output_path=None, mode="auto", n_colors=8,
              epsilon=2.0, max_error=2.0):
    """
    Fungsi utama: konversi gambar ke SVG.

    Parameter:
    - image_path: path ke gambar input
    - output_path: path output SVG (default: otomatis)
    - mode: "bw" (hitam-putih), "color" (full color), "auto" (otomatis)
    - n_colors: jumlah warna untuk mode color
    - epsilon: toleransi simplifikasi
    - max_error: toleransi Bezier
    """
    if output_path is None:
        stem = Path(image_path).stem
        output_path = str(Path(image_path).parent / f"{stem}.svg")

    # Load gambar
    print(f"Loading: {image_path}")
    pixels = load_image(image_path)
    h, w = pixels.shape[:2]
    print(f"  Ukuran: {w}x{h}")

    # Deteksi mode
    if mode == "auto":
        unique_colors = len(np.unique(pixels.reshape(-1, 3), axis=0))
        if unique_colors <= 10:
            mode = "bw"
            print(f"  Mode: Hitam-Putih ({unique_colors} warna unik)")
        else:
            mode = "color"
            print(f"  Mode: Full Color ({unique_colors} warna unik)")
    else:
        print(f"  Mode: {'Hitam-Putih' if mode == 'bw' else 'Full Color'}")

    print(f"  Epsilon: {epsilon}, Max Error: {max_error}")

    # Proses
    svg_paths = []

    if mode == "bw":
        print("\nPipeline: Grayscale -> Threshold -> Trace -> Simplify -> Bezier")
        curves, color = process_single_color(pixels, epsilon, max_error)
        if curves:
            path_str = bezier_to_svg_path(curves)
            svg_paths.append((path_str, color))
            print(f"  -> {len(curves)} kurva Bezier")
    else:
        print(f"\nPipeline: K-Means (K={n_colors}) -> Trace per layer -> Bezier")
        svg_paths = process_full_color(pixels, n_colors, epsilon, max_error)
        print(f"  -> {len(svg_paths)} path dengan warna berbeda")

    # Generate SVG
    print(f"\nGenerate SVG: {output_path}")
    generate_svg(svg_paths, w, h, output_path)
    file_size = os.path.getsize(output_path)
    print(f"  Selesai! ({file_size:,} bytes)")

    return output_path


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="SVG Vectorizer - Konversi gambar ke SVG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh:
  python vectorizer.py logo.png
  python vectorizer.py photo.jpg -o output.svg -c 16
  python vectorizer.py icon.png --mode bw
  python vectorizer.py picture.png --mode color --colors 8
        """
    )

    parser.add_argument("input", help="Path gambar input (PNG, JPG, BMP)")
    parser.add_argument("-o", "--output", help="Path output SVG (default: otomatis)")
    parser.add_argument("-m", "--mode", choices=["auto", "bw", "color"],
                        default="auto", help="Mode konversi (default: auto)")
    parser.add_argument("-c", "--colors", type=int, default=8,
                        help="Jumlah warna untuk mode color (default: 8)")
    parser.add_argument("-e", "--epsilon", type=float, default=2.0,
                        help="Toleransi simplifikasi dalam piksel (default: 2.0)")
    parser.add_argument("--max-error", type=float, default=2.0,
                        help="Toleransi Bezier dalam piksel (default: 2.0)")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: File '{args.input}' tidak ditemukan!")
        sys.exit(1)

    print("=" * 50)
    print("  SVG VECTORIZER")
    print("=" * 50)

    output = vectorize(
        args.input,
        args.output,
        args.mode,
        args.colors,
        args.epsilon,
        args.max_error,
    )

    print("\n" + "=" * 50)
    print(f"  File SVG: {output}")
    print("=" * 50)


if __name__ == "__main__":
    main()
