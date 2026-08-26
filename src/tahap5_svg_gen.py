"""
TAHAP 5 — SVG Generation
===========================
Mengubah kurva Bezier hasil Tahap 4 menjadi file SVG yang valid
dan bisa dibuka di browser.

Format SVG Path:
- M x,y  = Move to (pindah ke titik)
- C x1,y1 x2,y2 x,y  = Cubic Bezier (kurva kubik)
- Z  = Close path (tutup path)

Contoh:
  <path d="M 10,20 C 15,25 30,35 40,20 Z" fill="red"/>

Alur:
  Kurva Bezier (data JSON) → String SVG Path → Gabungkan → File .svg
"""

import sys
import json
from pathlib import Path


# =============================================================================
# KONVERSI: Bezier → SVG Path String
# =============================================================================

def bezier_to_svg_path(curves):
    """
    Konversi list kurva Bezier jadi string SVG path.

    Format: M x0,y0 C x1,y1 x2,y2 x3,y3 C ... Z

    ═══════════════════════════════════════════════════════════════
    PENJELASAN FORMAT SVG PATH:
    ═══════════════════════════════════════════════════════════════

    SVG path menggunakan huruf sebagai "command":

    M (Move To):
    - Pindahkan "pena" ke titik tertentu.
    - Seperti mengangkat pena dari kertas dan menempatkannya di tempat baru.
    - Contoh: M 10,20 → pindah ke koordinat (10, 20)

    C (Cubic Bézier):
    - Gambar kurva kubik dari posisi saat ini ke titik akhir.
    - Butuh 6 angka: x1,y1 x2,y2 x,y
      - x1,y1 = titik kontrol pertama
      - x2,y2 = titik kontrol kedua
      - x,y = titik akhir kurva
    - Posisi awal = posisi pena saat ini (dari M atau C sebelumnya).

    Z (Close Path):
    - Tutup path: gambar garis dari posisi saat ini ke titik awal (M).
    - Membuat polygon tertutup.

    ═══════════════════════════════════════════════════════════════
    CONTOH:
    ═══════════════════════════════════════════════════════════════

    Diberi 2 kurva Bezier yang saling sambung:
    - Kurva 1: P0(10,20) P1(15,25) P2(30,35) P3(40,20)
    - Kurva 2: P0(40,20) P1(50,10) P2(60,30) P3(70,20)

    SVG Path:
    M 10,20 C 15,25 30,35 40,20 C 50,10 60,30 70,20 Z

    Penjelasan:
    - M 10,20 → mulai dari (10,20)
    - C 15,25 30,35 40,20 → kurva pertama ke (40,20)
    - C 50,10 60,30 70,20 → kurva kedua ke (70,20)
    - Z → tutup path (garis dari (70,20) ke (10,20))

    ═══════════════════════════════════════════════════════════════
    """
    if not curves:
        return ""

    parts = []

    for i, curve in enumerate(curves):
        p0, p1, p2, p3 = curve
        # p0, p1, p2, p3 = (y, x) → format SVG pakai (x, y)

        if i == 0:
            # Kurva pertama: mulai dengan M (Move To)
            parts.append(f"M {p0[1]:.1f},{p0[0]:.1f}")

        # Semua kurva pakai C (Cubic Bezier)
        # C x1,y1 x2,y2 x,y
        parts.append(
            f"C {p1[1]:.1f},{p1[0]:.1f} "
            f"{p2[1]:.1f},{p2[0]:.1f} "
            f"{p3[1]:.1f},{p3[0]:.1f}"
        )

    # Tutup path
    parts.append("Z")

    return " ".join(parts)


# =============================================================================
# GENERATE: Buat File SVG Lengkap
# =============================================================================

def generate_svg(
    bezier_data,
    image_width,
    image_height,
    fill_colors=None,
    output_path="output.svg",
):
    """
    Generate file SVG dari data kurva Bezier.

    ═══════════════════════════════════════════════════════════════
    STRUKTUR SVG:
    ═══════════════════════════════════════════════════════════════

    <svg xmlns="http://www.w3.org/2000/svg"
         width="W" height="H"
         viewBox="0 0 W H">
      <rect width="100%" height="100%" fill="white"/>
      <path d="M ... C ... Z" fill="color1"/>
      <path d="M ... C ... Z" fill="color2"/>
      ...
    </svg>

    ═══════════════════════════════════════════════════════════════
    """
    # Default warna (abu-abu)
    if fill_colors is None:
        fill_colors = ["#555555"]

    # Mulai SVG
    svg_lines = []
    svg_lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{image_width}" height="{image_height}" '
        f'viewBox="0 0 {image_width} {image_height}">'
    )

    # Background putih
    svg_lines.append(
        '  <rect width="100%" height="100%" fill="white"/>'
    )

    # Generate path untuk tiap kontur
    for idx, segmen in enumerate(bezier_data):
        # Konversi kurva ke SVG path string
        path_str = bezier_to_svg_path(segmen)

        # Pilih warna
        color = fill_colors[idx % len(fill_colors)]

        # Buat elemen <path>
        svg_lines.append(
            f'  <path d="{path_str}" fill="{color}"/>'
        )

    # Tutup SVG
    svg_lines.append('</svg>')

    # Tulis ke file
    svg_content = "\n".join(svg_lines)
    with open(output_path, "w") as f:
        f.write(svg_content)

    print(f"SVG disimpan: {output_path}")
    print(f"  Ukuran gambar: {image_width}x{image_height}")
    print(f"  Jumlah path: {len(bezier_data)}")


# =============================================================================
# MAIN: Pipeline
# =============================================================================

def svg_pipeline(bezier_path, width, height, output_path=None, colors=None):
    """
    Pipeline Tahap 5: Load Bezier → Generate SVG.
    """
    stem = Path(bezier_path).stem.replace("_bezier", "")

    if output_path is None:
        output_path = str(Path(bezier_path).parent / f"{stem}_output.svg")

    # Load data Bezier
    with open(bezier_path) as f:
        bezier_data = json.load(f)

    print(f"Data Bezier dimuat: {len(bezier_data)} segmen")

    # Generate SVG
    print()
    print("--- SVG Generation ---")
    generate_svg(bezier_data, width, height, colors, output_path)

    return output_path


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Cara pakai:")
        print("  python tahap5_svg_gen.py <bezier.json> <width> <height> [output.svg]")
        print()
        print("Contoh:")
        print("  python tahap5_svg_gen.py test_binary_clean_contours_bezier.json 64 64")
        print("  python tahap5_svg_gen.py bezier.json 100 80 output.svg")
        sys.exit(1)

    bezier_path = sys.argv[1]
    w = int(sys.argv[2])
    h = int(sys.argv[3])
    out = sys.argv[4] if len(sys.argv) > 4 else None
    svg_pipeline(bezier_path, w, h, out)
