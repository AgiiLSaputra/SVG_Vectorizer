"""
Buat test image sederhana untuk testing contour tracing.
Gambar biner 64x64 dengan 4 kotak hitam terpisah di background putih.
"""

from PIL import Image, ImageDraw


def create_test():
    size = 64
    img = Image.new("L", (size, size), 255)  # Grayscale, putih
    draw = ImageDraw.Draw(img)

    # 4 kotak hitam terpisah
    draw.rectangle([4, 4, 18, 18], fill=0)    # Kiri atas
    draw.rectangle([24, 4, 38, 18], fill=0)   # Kanan atas
    draw.rectangle([4, 24, 18, 38], fill=0)   # Kiri bawah
    draw.rectangle([24, 24, 38, 38], fill=0)  # Kanan bawah

    img.save("test_binary_clean.png")
    print("Dibuat: test_binary_clean.png (4 kotak hitam)")


if __name__ == "__main__":
    create_test()
