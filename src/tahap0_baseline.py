"""
TAHAP 0 — Baseline: Konversi Gambar ke SVG Rectangles
======================================================
Script ini adalah versi paling sederhana dari Photo-to-SVG Converter.
Setiap blok NxN piksel pada gambar asli dikonversi menjadi satu elemen
<rect> di SVG, dengan warna rata-rata dari blok tersebut.

Tujuan: memastikan pipeline load gambar → proses → output SVG berjalan
end-to-end sebelum masuk ke algoritma yang lebih kompleks.
"""

import sys
from pathlib import Path
from PIL import Image
import numpy as np


def load_image(image_path: str) -> np.ndarray:
    """
    Load gambar dari path dan konversi ke array NumPy.

    Kenapa pakai Pillow?
    - Pillow adalah library standar Python untuk manipulasi gambar.
    - Bisa membaca berbagai format (PNG, JPG, BMP, dll).
    - Hasilnya langsung dikonversi ke array NumPy supaya mudah
      diakses per-piksel: array[y, x] = (R, G, B).

    Return: array 3D dengan shape (height, width, 3) untuk RGB.
    """
    img = Image.open(image_path)
    # Konversi ke RGB agar konsisten (handle gambar RGBA/grayscale)
    img = img.convert("RGB")
    return np.array(img)


def get_block_color(pixels: np.ndarray) -> tuple[int, int, int]:
    """
    Hitung warna rata-rata dari sebuah blok piksel.

    Kenapa rata-rata?
    - Karena kita 'merata-ratakan' semua piksel dalam satu blok
      menjadi satu warna. Ini cara paling sederhana untuk menentukan
      warna dominan sebuah area.
    - Untuk Tahap 0 ini, rata-rata sudah cukup. Di tahap selanjutnya
      kita bisa pakai k-means untuk clustering warna yang lebih akurat.

    Input: array piksel dengan shape (block_h, block_w, 3)
    Return: tuple (R, G, B) bilangan bulat 0-255
    """
    # axis=(0,1) artinya hitung rata-rata di dimensi height & width,
    # jadi tersisa dimensi channel (R, G, B) saja
    mean_rgb = pixels.mean(axis=(0, 1))
    # Bulatkan ke integer karena nilai warna harus bulat
    return int(mean_rgb[0]), int(mean_rgb[1]), int(mean_rgb[2])


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """
    Konversi nilai RGB ke string heksadesimal (#RRGGBB).

    Kenapa hex?
    - Format standar untuk warna di SVG/CSS.
    - Lebih compact daripada "rgb(255, 128, 0)".
    - Contoh: (255, 0, 0) → "#ff0000" (merah).
    """
    return f"#{r:02x}{g:02x}{b:02x}"


def image_to_svg_blocks(
    image_path: str,
    output_path: str,
    block_size: int = 8,
) -> None:
    """
    Fungsi utama: konversi gambar ke SVG berisi blok-blok rect.

    Alur kerja:
    1. Load gambar → array piksel
    2. Iterasi piksel secara berblok NxN
    3. Untuk tiap blok, hitung warna rata-rata
    4. Buat elemen <rect> dengan warna tersebut di posisi yang sesuai
    5. Gabungkan semua <rect> jadi satu file SVG

    Parameter:
    - image_path: path ke gambar input
    - output_path: path untuk menyimpan hasil SVG
    - block_size: ukuran blok NxN (semakin besar = semakin "pixelated")
    """
    # === LANGKAH 1: Load gambar ===
    pixels = load_image(image_path)
    height, width = pixels.shape[:2]  # shape[:2] = (height, width)
    print(f"Gambar dimuat: {width}x{height} piksel")

    # === LANGKAH 2: Hitung dimensi output ===
    # Kita akan punya grid kolom x baris blok.
    # Misal gambar 100x80 dengan block_size=8:
    #   kolom = 100/8 = 12.5 → dibulatkan ke atas = 13 blok
    #   baris = 80/8 = 10 → tepat 10 blok
    # Kenapa dibulatkan ke atas (ceil)? Karena sisa piksel yang tidak
    # muat di blok utuh tetap harus diwakili oleh satu blok tambahan.
    cols = (width + block_size - 1) // block_size  # ceil division
    rows = (height + block_size - 1) // block_size
    print(f"Grid blok: {cols} kolom x {rows} baris (block_size={block_size})")

    # === LANGKAH 3: Mulai membuat SVG ===
    # Kita tulis SVG secara manual (string concatenation) supaya
    # tidak bergantung pada library svgwrite.
    svg_parts = []
    svg_parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n'
    )
    svg_parts.append(
        '  <rect width="100%" height="100%" fill="white"/>\n'
    )
    # Alasannya: SVG default background-nya transparan (kosong).
    # Kita tambahkan rect putih di belakang supaya hasilnya mirip
    # dengan gambar asli (ada background, bukan transparan).

    # === LANGKAH 4: Iterasi tiap blok ===
    rect_count = 0
    for row in range(rows):
        for col in range(cols):
            # Hitung koordinat piksel awal & akhir dari blok ini.
            # Misal block_size=8, row=2, col=3:
            #   y_start = 2*8 = 16
            #   y_end = min(16+8, height) = min(24, height)
            # y_end dipotong (min) supaya tidak melebihi batas gambar
            # (untuk blok di tepi kanan/bawah yang mungkin tidak utuh).
            y_start = row * block_size
            y_end = min(y_start + block_size, height)
            x_start = col * block_size
            x_end = min(x_start + block_size, width)

            # Ambil piksel dari blok ini (slicing array NumPy)
            block_pixels = pixels[y_start:y_end, x_start:x_end]

            # Hitung warna rata-rata blok
            r, g, b = get_block_color(block_pixels)
            color = rgb_to_hex(r, g, b)

            # Buat elemen <rect>
            # x, y = koordinat sudut kiri atas
            # width, height = ukuran blok
            # fill = warna isian (tanpa outline/stroke)
            svg_parts.append(
                f'  <rect x="{x_start}" y="{y_start}" '
                f'width="{x_end - x_start}" height="{y_end - y_start}" '
                f'fill="{color}"/>\n'
            )
            rect_count += 1

    # Tutup tag SVG
    svg_parts.append("</svg>\n")

    # === LANGKAH 5: Tulis ke file ===
    # Gabungkan semua string jadi satu, lalu tulis ke file.
    with open(output_path, "w") as f:
        f.write("".join(svg_parts))

    print(f"SVG berhasil dibuat: {output_path}")
    print(f"Total elemen <rect>: {rect_count}")


# === ENTRY POINT ===
# Script ini bisa dijalankan dari command line:
#   python tahap0_baseline.py <gambar_input> [block_size] [gambar_output]
#
# Contoh:
#   python tahap0_baseline.py logo.png 8 output.svg
#   python tahap0_baseline.py photo.jpg 16 result.svg
if __name__ == "__main__":
    # Minimal harus ada 1 argumen (path gambar input)
    if len(sys.argv) < 2:
        print("Cara pakai:")
        print("  python tahap0_baseline.py <gambar_input> [block_size] [output.svg]")
        print()
        print("Contoh:")
        print("  python tahap0_baseline.py logo.png 8 output.svg")
        sys.exit(1)

    input_path = sys.argv[1]
    block = int(sys.argv[2]) if len(sys.argv) > 2 else 8

    # Default output: nama file yang sama dengan .svg
    if len(sys.argv) > 3:
        output_path = sys.argv[3]
    else:
        output_path = str(Path(input_path).with_suffix(".svg"))

    # Jalankan konversi
    image_to_svg_blocks(input_path, output_path, block)
