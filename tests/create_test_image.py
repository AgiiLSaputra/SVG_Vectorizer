"""
Generate gambar test sederhana untuk testing Tahap 0.
Membuat gambar 64x64 piksel dengan pola kotak-kotak warna.

Cara pakai:
  python create_test_image.py
"""

from PIL import Image, ImageDraw


def create_test_image(output_path="test_image.png", size=64):
    """
    Membuat gambar test sederhana dengan pola kotak.

    Ukuran kecil (64x64) supaya hasil SVG-nya mudah dilihat
    dan tidak terlalu banyak rect saat pertama kali test.
    """
    img = Image.new("RGB", (size, size), "white")
    draw = ImageDraw.Draw(img)

    # Kotak merah di kiri atas
    draw.rectangle([4, 4, 28, 28], fill="red")

    # Kotak biru di kanan atas
    draw.rectangle([32, 4, 56, 28], fill="blue")

    # Kotak hijau di kiri bawah
    draw.rectangle([4, 32, 28, 56], fill="green")

    # Kotak kuning di kanan bawah
    draw.rectangle([32, 32, 56, 56], fill="yellow")

    img.save(output_path)
    print(f"Test image dibuat: {output_path} ({size}x{size} piksel)")


if __name__ == "__main__":
    create_test_image()
