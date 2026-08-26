"""
TAHAP 2 — Contour Tracing (Moore-Neighbor)
=============================================
Menyusuri tepi (boundary) tiap objek hitam pada gambar biner
menggunakan algoritma Moore-Neighbor tracing.

Output: list titik (x, y) yang membentuk polygon untuk tiap objek.
"""

import sys
import json
from pathlib import Path
import numpy as np
from PIL import Image


# =============================================================================
# 8 DIRECTION: Tetangga Moore (searah jarum jam dari Timur)
# =============================================================================
# (dy, dx) — perubahan baris dan kolom
DIRECTIONS = [
    (0, 1),   # E  (Timur)
    (1, 1),   # SE (Tenggara)
    (1, 0),   # S  (Selatan)
    (1, -1),  # SW (Barat Daya)
    (0, -1),  # W  (Barat)
    (-1, -1), # NW (Barat Laut)
    (-1, 0),  # N  (Utara)
    (-1, 1),  # NE (Timur Laut)
]

# Lawan arah (untuk kembali ke piksel sebelumnya)
OPPOSITE = [4, 5, 6, 7, 0, 1, 2, 3]


def is_black(binary, y, x):
    """Cek apakah piksel (y,x) hitam (nilai 0)."""
    h, w = binary.shape
    if y < 0 or y >= h or x < 0 or x >= w:
        return False
    return binary[y, x] == 0


def moore_neighbor_trace_single(binary, start_y, start_x):
    """
    Trace SATU kontur mulai dari titik (start_y, start_x).

    Algoritma Moore-Neighbor:
    1. Mulai dari piksel hitam, "datang" dari piksel putih di sebelah kiri.
    2. Cari tetangga hitam searah jarum jam.
    3. Pindah ke tetangga yang ditemukan, ulangi.
    4. Berhenti ketika kembali ke titik awal.

    Return: list titik (y, x) yang membentuk kontur.
    """
    h, w = binary.shape

    # Mulai dari putih di kiri titik awal
    current_y, current_x = start_y, start_x - 1
    prev_dir = 4  # datang dari W (kiri)

    contour = [(start_y, start_x)]
    max_steps = h * w

    for _ in range(max_steps):
        # Cari tetangga hitam searah jarum jam
        found = False
        for i in range(8):
            dir_idx = (prev_dir + 1 + i) % 8
            dy, dx = DIRECTIONS[dir_idx]
            ny, nx = current_y + dy, current_x + dx

            if is_black(binary, ny, nx):
                contour.append((ny, nx))
                prev_dir = OPPOSITE[dir_idx]
                current_y, current_x = ny, nx
                found = True
                break

        if not found:
            break

        # Selesai jika kembali ke titik awal
        if (current_y, current_x) == (start_y, start_x) and len(contour) > 2:
            break

    return contour


def find_all_start_points(binary):
    """
    Cari semua titik awal kontur (tepi kiri objek).

    Titik awal = piksel hitam yang punya piksel putih di sebelah kiri.
    Ini memastikan kita hanya mulai dari tepi LUAR objek,
    bukan dari piksel di dalam objek.
    """
    h, w = binary.shape
    starts = []

    for y in range(h):
        for x in range(w):
            if binary[y, x] == 0:  # piksel hitam
                # Cek apakah sebelah kiri putih (atau di luar batas)
                if x == 0 or binary[y, x - 1] == 1:
                    starts.append((y, x))

    return starts


def moore_neighbor_trace(binary):
    """
    Trace semua kontur pada gambar biner.

    Return: list of contours. Tiap contour = list titik (y, x)
    """
    h, w = binary.shape
    visited = np.zeros((h, w), dtype=bool)  # menandai piksel yang sudah ditrace

    all_contours = []
    starts = find_all_start_points(binary)

    for start_y, start_x in starts:
        # Skip jika sudah ditrace
        if visited[start_y, start_x]:
            continue

        # Trace kontur dari titik ini
        contour = moore_neighbor_trace_single(binary, start_y, start_x)

        # Tandai semua piksel kontur sebagai visited
        for y, x in contour:
            if 0 <= y < h and 0 <= x < w:
                visited[y, x] = True

        # Simpan jika kontur cukup layak (minimal 4 titik)
        if len(contour) >= 4:
            all_contours.append(contour)

    return all_contours


# =============================================================================
# VISUALISASI
# =============================================================================

def save_contour_visualization(binary, contours, output_path):
    """Simpan visualisasi kontur sebagai gambar."""
    colors = [
        (255, 0, 0), (0, 150, 0), (0, 0, 255),
        (255, 165, 0), (128, 0, 128), (0, 200, 200),
    ]

    h, w = binary.shape
    img = np.ones((h, w, 3), dtype=np.uint8) * 220
    img[binary == 0] = [40, 40, 40]

    for idx, contour in enumerate(contours):
        color = colors[idx % len(colors)]
        for y, x in contour:
            if 0 <= y < h and 0 <= x < w:
                img[y, x] = color

    Image.fromarray(img).save(output_path)
    print(f"Visualisasi disimpan: {output_path}")


def save_contours_json(contours, output_path):
    """Simpan kontur ke JSON."""
    with open(output_path, "w") as f:
        json.dump(contours, f)
    print(f"Kontur disimpan: {output_path}")


# =============================================================================
# MAIN
# =============================================================================

def trace_contours(binary_path, output_dir="."):
    """Pipeline Tahap 2: load biner -> tracing -> simpan."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    # Load gambar biner
    if binary_path.endswith(".npy"):
        binary = np.load(binary_path)
    else:
        img = Image.open(binary_path).convert("L")
        binary = (np.array(img) < 128).astype(int)

    stem = Path(binary_path).stem
    h, w = binary.shape
    black_count = int(np.sum(binary == 0))
    print(f"Biner: {w}x{h}, piksel hitam: {black_count}")

    # Tracing
    print("Mulai Contour Tracing...")
    contours = moore_neighbor_trace(binary)
    print(f"Kontur ditemukan: {len(contours)}")
    for i, c in enumerate(contours[:10]):
        print(f"  #{i+1}: {len(c)} titik")

    # Simpan hasil
    save_contour_visualization(binary, contours, str(output / f"{stem}_contours.png"))
    save_contours_json(contours, str(output / f"{stem}_contours.json"))

    return contours


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Cara pakai:")
        print("  python tahap2_contour_tracing.py <gambar_biner>")
        print()
        print("Contoh:")
        print("  python tahap2_contour_tracing.py test_image_binary.npy")
        print("  python tahap2_contour_tracing.py test_image_binary.png")
        sys.exit(1)

    trace_contours(sys.argv[1])
