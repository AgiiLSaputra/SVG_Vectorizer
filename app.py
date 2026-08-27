"""
SVG Vectorizer — Web Interface
===============================
Flask web app untuk konversi gambar ke SVG melalui browser.
"""

import os
import uuid
import time
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from werkzeug.utils import secure_filename
from pathlib import Path

from src.vectorizer import vectorize

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "uploads")
app.config["OUTPUT_FOLDER"] = os.path.join(os.path.dirname(__file__), "output", "svg")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "bmp", "gif", "tiff", "webp"}

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(app.config["OUTPUT_FOLDER"], exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "Tidak ada file yang diupload"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Tidak ada file yang dipilih"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Format file tidak didukung. Gunakan: PNG, JPG, BMP, GIF, TIFF, WEBP"}), 400

    # Simpan file upload
    filename = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"
    upload_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
    file.save(upload_path)

    # Ambil parameter
    mode = request.form.get("mode", "auto")
    n_colors = int(request.form.get("colors", 8))
    epsilon = float(request.form.get("epsilon", 2.0))
    max_error = float(request.form.get("max_error", 2.0))

    # Proses vectorize
    output_name = f"{Path(filename).stem}_{uuid.uuid4().hex[:6]}.svg"
    output_path = os.path.join(app.config["OUTPUT_FOLDER"], output_name)

    try:
        start_time = time.time()
        result_path = vectorize(
            upload_path,
            output_path,
            mode=mode,
            n_colors=n_colors,
            epsilon=epsilon,
            max_error=max_error,
        )
        elapsed = round(time.time() - start_time, 2)
        file_size = os.path.getsize(result_path)

        return jsonify({
            "success": True,
            "filename": output_name,
            "original": filename,
            "time": elapsed,
            "size": file_size,
        })
    except Exception as e:
        return jsonify({"error": f"Gagal memproses: {str(e)}"}), 500


@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(
        app.config["OUTPUT_FOLDER"],
        filename,
        as_attachment=True,
        download_name=filename,
    )


@app.route("/preview/<filename>")
def preview(filename):
    return send_from_directory(
        app.config["OUTPUT_FOLDER"],
        filename,
        mimetype="image/svg+xml",
    )


if __name__ == "__main__":
    print("=" * 50)
    print("  SVG VECTORIZER — Web Interface")
    print("  http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, host="0.0.0.0", port=5000)
