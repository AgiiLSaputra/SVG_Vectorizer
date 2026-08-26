"""
TAHAP 1 — Load & Preprocessing
================================
Pipeline ini memproses gambar menjadi gambar biner (hitam-putih)
yang siap untuk contour tracing di Tahap 2.

Alur kerja:
  Gambar RGB → Grayscale → Gaussian Blur (opsional) → Threshold → Biner

Setiap langkah diimplementasikan manual dengan numpy supaya
kita paham apa yang terjadi di balik layar.
"""

import sys
from pathlib import Path
from PIL import Image
import numpy as np


# =============================================================================
# LANGKAH 1: Load Gambar
# =============================================================================

def load_image(image_path: str) -> np.ndarray:
    """
    Load gambar dan kembalikan sebagai array RGB.

    Sama seperti Tahap 0, tapi di sini kita juga menyimpan
    info ukuran untuk keperluan preprocessing.
    """
    img = Image.open(image_path)
    img = img.convert("RGB")
    pixels = np.array(img, dtype=np.float64)
    # dtype float64 supaya operasi matematika (blur, dll) tidak
    # terpotong ke integer sebelum waktunya.
    print(f"Gambar dimuat: {img.size[0]}x{img.size[1]} piksel")
    return pixels


# =============================================================================
# LANGKAH 2: Konversi ke Grayscale
# =============================================================================

def rgb_to_grayscale(pixels: np.ndarray) -> np.ndarray:
    """
    Konversi gambar RGB ke grayscale (skala abu-abu).

    Kenapa grayscale?
    - Kita hanya perlu satu channel (intensitas) untuk membuat
      gambar biner (hitam-putih), bukan tiga channel (R, G, B).
    - Grayscale menyederhanakan data dari 3 dimensi jadi 2 dimensi.

    Rumus luminance (ITU-R BT.601):
      Gray = 0.299*R + 0.587*G + 0.114*B

    Kenapa rumus ini?
    - Mata manusia paling sensitif terhadap warna hijau (0.587 paling besar),
      lalu merah (0.299), dan paling sedikit terhadap biru (0.114).
    - Ini bukan sekadar rata-rata (R+G+B)/3, tapi weighted average
      yang memperhitungkan persepsi mata manusia.

    Input: array shape (H, W, 3) dtype float64
    Output: array shape (H, W) dtype float64, nilai 0-255
    """
    # Ambil channel R, G, B
    r = pixels[:, :, 0]
    g = pixels[:, :, 1]
    b = pixels[:, :, 2]

    # Hitung grayscale dengan weighted average
    gray = 0.299 * r + 0.587 * g + 0.114 * b

    print(f"Grayscale selesai — range nilai: {gray.min():.0f} - {gray.max():.0f}")
    return gray


# =============================================================================
# LANGKAH 3: Gaussian Blur
# =============================================================================

def create_gaussian_kernel(size: int, sigma: float) -> np.ndarray:
    """
    Buat kernel (matriks) Gaussian untuk convolution.

    Apa itu Gaussian kernel?
    - Matriks kecil (misal 3x3 atau 5x5) yang berisi "bobot" berbentuk
      lonceng (Gaussian distribution).
    - Nilai di tengah paling besar, makin ke pinggir makin kecil.
    - Saat di-convolve (digeser) ke seluruh gambar, efeknya adalah
      setiap piksel jadi rata-rata dari tetangganya, tapi tetangga
      yang lebih dekat punya bobot lebih besar.
    - Hasilnya: gambar jadi sedikit buram (blur).

    Kenapa blur sebelum threshold?
    - Noise (piksel acak) bisa bikin threshold menghasilkan
      titik-titik sembarang. Blur menghaluskan noise supaya
      threshold lebih bersih.

    Parameter:
    - size: ukuran kernel (harus ganjil, misal 3, 5, 7)
    - sigma: standar deviasi Gaussian (semakin besar = makin blur)

    Rumus Gaussian 2D:
      G(x, y) = (1 / (2π σ²)) * e^(-(x² + y²) / (2σ²))
    """
    # Buat grid koordinat relatif terhadap tengah kernel
    # Misal size=3: coordinates = [-1, 0, 1] di kedua sumbu
    ax = np.arange(size) - size // 2  # [-1, 0, 1] untuk size=3
    xx, yy = np.meshgrid(ax, ax)  # Buat grid 2D

    # Rumus Gaussian 2D
    kernel = np.exp(-(xx**2 + yy**2) / (2 * sigma**2))

    # Normalisasi supaya total seluruh elemen = 1
    # Kenapa? Supaya kecerahan gambar tetap sama setelah blur.
    # Kalau total > 1, gambar jadi lebih terang; kalau < 1, jadi gelap.
    kernel = kernel / kernel.sum()

    return kernel


def apply_gaussian_blur(image: np.ndarray, kernel_size: int = 3,
                        sigma: float = 1.0) -> np.ndarray:
    """
    Terapkan Gaussian blur ke gambar.

    Proses convolution:
    1. Letakkan kernel di atas piksel.
    2. Kalikan setiap elemen kernel dengan piksel yang tertutup.
    3. Jumlahkan semua hasil perkalian → jadi nilai piksel baru.
    4. Geser kernel ke piksel berikutnya, ulangi sampai habis.

    Kita tidak perlu mengimplementasikan convolution dari nol —
    cukup pakai `scipy.ndimage` atau manual dengan numpy.
    Di sini kita pakai cara manual untuk belajar.

    Parameter:
    - image: array 2D (grayscale)
    - kernel_size: ukuran kernel (ganjil)
    - sigma: standar deviasi Gaussian

    Output: array 2D, ukuran sama dengan input
    """
    kernel = create_gaussian_kernel(kernel_size, sigma)
    print(f"Gaussian kernel ({kernel_size}x{kernel_size}, sigma={sigma}):")
    print(kernel.round(3))

    h, w = image.shape
    k = kernel_size // 2  # Padding size (offset dari tepi)

    # Buat output array kosong (nanti diisi hasil convolution)
    output = np.zeros_like(image)

    # Iterasi setiap piksel (kecuali tepi yang tidak bisa di-convolve)
    # Kenapa skip tepi? Karena kernel butuh tetangga di semua sisi,
    # tapi piksel di tepi tidak punya tetangga lengkap.
    # Kita pakai zero-padding (asumsi piksel di luar gambar = 0).
    for y in range(h):
        for x in range(w):
            # Ambil region yang tertutup kernel (+ padding di tepi)
            y_start = max(0, y - k)
            y_end = min(h, y + k + 1)
            x_start = max(0, x - k)
            x_end = min(w, x + k + 1)

            # Ambil region gambar dan kernel yang sesuai
            region = image[y_start:y_end, x_start:x_end]
            kern = kernel[
                (y_start - (y - k)):(y_end - (y - k)),
                (x_start - (x - k)):(x_end - (x - k))
            ]

            # Kalikan elemen-per-elemen, lalu jumlahkan
            output[y, x] = np.sum(region * kern)

    print(f"Blur selesai — output shape: {output.shape}")
    return output


# =============================================================================
# LANGKAH 4: Thresholding (Otsu's Method Manual)
# =============================================================================

def otsu_threshold(image: np.ndarray) -> float:
    """
    Hitung nilai threshold optimal menggunakan metode Otsu.

    Apa itu Otsu's Method?
    - Cara otomatis menentukan nilai terbaik untuk memisahkan
      piksel jadi dua kelas: "gelap" (objek) dan "terang" (background).
    - Tanpa perlu user menebak-nebak nilai threshold.

    Algoritma:
    1. Buat histogram distribusi intensitas piksel (0-255).
    2. Coba semua kemungkinan nilai threshold t (0-255).
    3. Untuk tiap t, hitung "variance ratio" (antara-klas / total).
    4. Pilih t yang memaksimalkan variance ratio → itu threshold terbaik.

    Kenapa Otsu?
    - Threshold statis (misal 128) tidak cocok untuk semua gambar.
    - Otsu otomatis menyesuaikan dengan distribusi warna gambar.

    Input: array 2D (grayscale, 0-255)
    Output: nilai threshold optimal (float)
    """
    # Hitung histogram (frekuensi tiap nilai intensitas 0-255)
    hist, _ = np.histogram(image.ravel(), bins=256, range=(0, 256))

    # Total piksel
    total = image.size

    # Probabilitas tiap intensitas (p_i = jumlah_piksel_i / total)
    # Ini distribusi probabilitas dari histogram
    prob = hist / total

    # Hitung cumulative sum (ω) dan cumulative mean (μ)
    # ω(k) = total probabilitas dari intensitas 0 sampai k
    # μ(k) = mean intensitas dari 0 sampai k
    omega = np.cumsum(prob)
    mean = np.cumsum(prob * np.arange(256))

    # Mean keseluruhan gambar
    global_mean = mean[-1]

    # Hitung variance antara kelas untuk semua kemungkinan threshold
    # σ²_B(t) = [μ_T * ω(t) - μ(t)]² / [ω(t) * (1 - ω(t))]
    # Threshold terbaik = yang memaksimalkan σ²_B
    variance_between = np.zeros(256)
    for t in range(256):
        if omega[t] == 0 or omega[t] == 1:
            variance_between[t] = 0
        else:
            numerator = (global_mean * omega[t] - mean[t]) ** 2
            denominator = omega[t] * (1 - omega[t])
            variance_between[t] = numerator / denominator

    # Threshold = nilai t yang memaksimalkan variance
    threshold = np.argmax(variance_between)
    print(f"Otsu threshold: {threshold}")
    return threshold


def threshold_binary(image: np.ndarray, threshold: float = None) -> np.ndarray:
    """
    Konversi gambar grayscale ke biner (hitam-putih).

    Prinsip kerja:
    - Setiap piksel dibandingkan dengan threshold.
    - Jika <= threshold → 0 (hitam) → bagian OBJEK.
    - Jika > threshold → 1 (putih) → bagian BACKGROUND.

    Kenapa hitam = objek?
    - Karena di tahap selanjutnya kita akan trace kontur
      area hitam. Jadi objek harus berwarna hitam (nilai 0).

    Parameter:
    - image: array 2D grayscale
    - threshold: nilai ambang (jika None, pakai Otsu otomatis)

    Output: array 2D biner, hanya berisi 0 dan 1
    """
    if threshold is None:
        threshold = otsu_threshold(image)

    # Binerisasi: piksel <= threshold → 0 (hitam/objek)
    #             piksel > threshold  → 1 (putih/background)
    binary = np.where(image <= threshold, 0, 1)

    hit_count = np.sum(binary == 0)
    white_count = np.sum(binary == 1)
    print(f"Binerisasi selesai — hitam (objek): {hit_count}, putih (background): {white_count}")
    return binary


# =============================================================================
# FUNGSI UTAMA: Pipeline Tahap 1
# =============================================================================

def preprocess_image(
    image_path: str,
    output_dir: str = ".",
    blur_sigma: float = 1.0,
    blur_kernel: int = 3,
) -> np.ndarray:
    """
    Pipeline lengkap Tahap 1: Load → Grayscale → Blur → Threshold.

    Fungsi ini mengembalikan gambar biner (array 2D, nilai 0 atau 1)
    yang siap untuk diproses di Tahap 2 (Contour Tracing).

    Selain itu, fungsi ini juga menyimpan gambar intermediate
    (grayscale, blurred, binary) sebagai PNG supaya bisa dilihat
    dan dipahami hasil tiap tahap.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    stem = Path(image_path).stem

    # 1. Load gambar
    pixels = load_image(image_path)

    # 2. Konversi ke grayscale
    gray = rgb_to_grayscale(pixels)
    gray_img = Image.fromarray(gray.astype(np.uint8), mode="L")
    gray_path = output_path / f"{stem}_grayscale.png"
    gray_img.save(str(gray_path))
    print(f"Disimpan: {gray_path}")

    # 3. Gaussian blur (opsional)
    if blur_sigma > 0:
        blurred = apply_gaussian_blur(gray, kernel_size=blur_kernel, sigma=blur_sigma)
        blurred_img = Image.fromarray(blurred.astype(np.uint8), mode="L")
        blurred_path = output_path / f"{stem}_blurred.png"
        blurred_img.save(str(blurred_path))
        print(f"Disimpan: {blurred_path}")
    else:
        blurred = gray
        print("Blur dilewati (sigma=0)")

    # 4. Threshold (binerisasi)
    binary = threshold_binary(blurred)
    # Konversi ke 0-255 supaya bisa disimpan sebagai PNG
    binary_img = Image.fromarray((binary * 255).astype(np.uint8), mode="L")
    binary_path = output_path / f"{stem}_binary.png"
    binary_img.save(str(binary_path))
    print(f"Disimpan: {binary_path}")

    # 5. Simpan juga sebagai array untuk tahap selanjutnya
    np.save(str(output_path / f"{stem}_binary.npy"), binary)
    print(f"Array biner disimpan: {output_path / f'{stem}_binary.npy'}")

    return binary


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Cara pakai:")
        print("  python tahap1_preprocessing.py <gambar_input> [sigma] [kernel_size]")
        print()
        print("Contoh:")
        print("  python tahap1_preprocessing.py test_image.png")
        print("  python tahap1_preprocessing.py logo.jpg 2.0 5")
        print()
        print("Parameter:")
        print("  sigma       — kekuatan blur (0=tanpa blur, default=1.0)")
        print("  kernel_size — ukuran kernel blur (ganjil, default=3)")
        sys.exit(1)

    input_path = sys.argv[1]
    sigma = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    ksize = int(sys.argv[3]) if len(sys.argv) > 3 else 3

    preprocess_image(input_path, blur_sigma=sigma, blur_kernel=ksize)
