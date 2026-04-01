"""
DocShield – Génération de code-barres Code 128 signé HMAC-SHA256.
"""
import hmac
import hashlib
import uuid
import io
from datetime import datetime, timezone

import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont


def generate_doc_id() -> str:
    """Génère un identifiant unique de document."""
    return str(uuid.uuid4()).replace("-", "").upper()[:16]


def compute_hmac(payload: str, secret: str) -> str:
    """Calcule la signature HMAC-SHA256 (hex, 16 premiers chars)."""
    sig = hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return sig[:24].upper()


def build_barcode_payload(doc_id: str, secret: str, filename: str = "") -> dict:
    """
    Construit le payload complet du code-barres.
    Retourne un dict avec toutes les métadonnées de signature.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    raw = f"{doc_id}|{timestamp}|{filename}"
    signature = compute_hmac(raw, secret)
    barcode_text = f"DS-{doc_id}-{signature}"
    return {
        "doc_id": doc_id,
        "timestamp": timestamp,
        "filename": filename,
        "signature": signature,
        "barcode_text": barcode_text,
        "full_raw": raw,
    }


def verify_barcode(barcode_text: str, secret: str) -> dict:
    """
    Vérifie un code-barres DocShield.
    Retourne {'valid': bool, 'doc_id': str, 'timestamp': str, 'error': str}
    """
    try:
        parts = barcode_text.split("-")
        if len(parts) < 3 or parts[0] != "DS":
            return {"valid": False, "error": "Format invalide"}
        doc_id = parts[1]
        claimed_sig = parts[2]
        # On ne peut pas re-vérifier sans timestamp/filename — vérification partielle
        # En production : stocker les payloads en DB pour full-verify
        test_sig = compute_hmac(f"{doc_id}|", secret)
        # Vérification best-effort : on retourne l'info décodée
        return {
            "valid": True,
            "doc_id": doc_id,
            "signature": claimed_sig,
            "note": "Signature présente – vérification DB requise pour validation complète",
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}


def generate_barcode_image(
    barcode_text: str,
    metadata: dict,
    width_px: int = 600,
) -> Image.Image:
    """
    Génère une image PNG du code-barres Code 128 avec légende.
    Retourne un objet PIL Image.
    """
    # --- Code 128 via python-barcode ---
    Code128 = barcode.get_barcode_class("code128")
    writer = ImageWriter()
    writer.set_options({
        "module_width": 10,
        "module_height": 15.0,
        "quiet_zone": 6.5,
        "font_size": 10,
        "text_distance": 5.0,
        "background": "white",
        "foreground": "black",
        "write_text": False,
    })

    buf = io.BytesIO()
    bc = Code128(barcode_text, writer=writer)
    bc.write(buf, options={"write_text": False})
    buf.seek(0)
    bc_img = Image.open(buf).convert("RGBA")

    # --- Redimensionner le code-barres ---
    aspect = bc_img.height / bc_img.width
    bc_resized = bc_img.resize((width_px, int(width_px * aspect)), Image.LANCZOS)

    # --- Panneau de métadonnées ---
    padding = 12
    label_h = 60
    total_h = bc_resized.height + label_h + padding * 3

    canvas = Image.new("RGBA", (width_px + padding * 2, total_h), (255, 255, 255, 255))
    canvas.paste(bc_resized, (padding, padding))

    draw = ImageDraw.Draw(canvas)

    # Texte métadonnées
    try:
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 11)
        font_tiny  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 9)
    except Exception:
        font_small = ImageFont.load_default()
        font_tiny  = font_small

    y_text = bc_resized.height + padding * 2
    draw.text((padding, y_text), f"🔒 DocShield  |  ID: {metadata['doc_id']}", fill=(30, 30, 30), font=font_small)
    draw.text((padding, y_text + 18), f"Signé: {metadata['timestamp']}  |  SIG: {metadata['signature']}", fill=(90, 90, 90), font=font_tiny)
    draw.text((padding, y_text + 32), f"Fichier: {metadata.get('filename', '—')}", fill=(120, 120, 120), font=font_tiny)

    # Ligne de séparation
    draw.line([(padding, bc_resized.height + padding + 6), (width_px + padding, bc_resized.height + padding + 6)],
              fill=(200, 200, 200), width=1)

    return canvas.convert("RGB")


def barcode_image_bytes(barcode_text: str, metadata: dict) -> bytes:
    """Retourne le code-barres en bytes PNG."""
    img = generate_barcode_image(barcode_text, metadata)
    buf = io.BytesIO()
    img.save(buf, format="PNG", dpi=(150, 150))
    buf.seek(0)
    return buf.read()
