"""
DocShield – Application Flask principale.
Encodage de documents PDF/DOCX/Images avec code-barres Code 128 signé HMAC-SHA256.
"""
import os
import io
import base64
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, send_file, jsonify
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

from utils.barcode_gen import (
    generate_doc_id,
    build_barcode_payload,
    barcode_image_bytes,
    verify_barcode,
)
from utils.pdf_processor import stamp_pdf
from utils.docx_processor import stamp_docx
from utils.image_processor import stamp_image

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB

SECRET_KEY = os.environ.get("DOCSHIELD_SECRET", "docshield-dev-secret-changeme")

ALLOWED_EXTENSIONS = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "png":  "image/png",
    "jpg":  "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
}

# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[1].lower() if "." in filename else ""


def make_output_filename(original_name: str, doc_id: str) -> str:
    stem = Path(original_name).stem
    ext  = Path(original_name).suffix
    return f"{stem}_docshield_{doc_id[:8]}{ext}"


# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/protect", methods=["POST"])
def protect():
    """
    Endpoint principal : reçoit un fichier et retourne le document estampillé.
    Paramètres POST (multipart):
      - file      : le fichier à protéger
      - position  : 'top' | 'bottom' (défaut: bottom)
    """
    if "file" not in request.files:
        return jsonify({"error": "Aucun fichier reçu"}), 400

    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "Nom de fichier vide"}), 400

    if not allowed_file(f.filename):
        exts = ", ".join(ALLOWED_EXTENSIONS.keys())
        return jsonify({"error": f"Format non supporté. Formats acceptés : {exts}"}), 400

    position = request.form.get("position", "bottom")
    if position not in ("top", "bottom"):
        position = "bottom"

    try:
        file_bytes = f.read()
        ext = get_extension(f.filename)
        original_name = f.filename

        # 1. Générer l'identifiant et la signature
        doc_id = generate_doc_id()
        metadata = build_barcode_payload(doc_id, SECRET_KEY, original_name)

        # 2. Générer l'image du code-barres
        bc_png = barcode_image_bytes(metadata["barcode_text"], metadata)

        # 3. Estampiller le document selon son type
        if ext == "pdf":
            result_bytes = stamp_pdf(file_bytes, bc_png, position)
            mime = "application/pdf"
        elif ext == "docx":
            result_bytes = stamp_docx(file_bytes, bc_png, metadata, position)
            mime = ALLOWED_EXTENSIONS["docx"]
        else:  # image
            result_bytes = stamp_image(file_bytes, bc_png, metadata, position, ext)
            mime = ALLOWED_EXTENSIONS.get(ext, "image/png")

        # 4. Nom du fichier de sortie
        out_name = make_output_filename(original_name, doc_id)

        # 5. Encoder en base64 pour retour JSON
        b64 = base64.b64encode(result_bytes).decode("utf-8")

        return jsonify({
            "success": True,
            "doc_id":    metadata["doc_id"],
            "timestamp": metadata["timestamp"],
            "signature": metadata["signature"],
            "barcode":   metadata["barcode_text"],
            "filename":  out_name,
            "mime":      mime,
            "size":      len(result_bytes),
            "data":      b64,
        })

    except Exception as e:
        app.logger.exception("Erreur lors du traitement")
        return jsonify({"error": f"Erreur interne : {str(e)}"}), 500


@app.route("/api/verify", methods=["POST"])
def verify():
    """
    Vérifie un code-barres DocShield.
    Body JSON: {"barcode": "DS-XXXXX-YYYYY"}
    """
    data = request.get_json(silent=True) or {}
    barcode_text = data.get("barcode", "").strip()

    if not barcode_text:
        return jsonify({"error": "Code-barres manquant"}), 400

    result = verify_barcode(barcode_text, SECRET_KEY)
    return jsonify(result)


@app.route("/api/preview-barcode", methods=["POST"])
def preview_barcode():
    """
    Génère un aperçu du code-barres sans traiter de document.
    Body JSON: {"filename": "test.pdf"}
    """
    data = request.get_json(silent=True) or {}
    filename = data.get("filename", "document.pdf")

    doc_id = generate_doc_id()
    metadata = build_barcode_payload(doc_id, SECRET_KEY, filename)
    bc_png = barcode_image_bytes(metadata["barcode_text"], metadata)
    b64 = base64.b64encode(bc_png).decode("utf-8")

    return jsonify({
        "barcode_image": f"data:image/png;base64,{b64}",
        "doc_id": metadata["doc_id"],
        "signature": metadata["signature"],
        "barcode_text": metadata["barcode_text"],
    })


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "DocShield", "version": "1.0.0"})


# ──────────────────────────────────────────────
# Lancement
# ──────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "production") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)
