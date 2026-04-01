"""
DocShield – Ajout du code-barres sur des images (PNG, JPG, JPEG, WEBP).
"""
import io
from PIL import Image, ImageDraw, ImageFont, ImageFilter


def stamp_image(input_bytes: bytes, barcode_png: bytes, metadata: dict,
                position: str = "bottom", original_ext: str = "png") -> bytes:
    """
    Composite le code-barres sur une image.
    position: 'top' | 'bottom'
    Retourne les bytes de l'image modifiée.
    """
    # Charger l'image source
    src = Image.open(io.BytesIO(input_bytes)).convert("RGBA")
    src_w, src_h = src.size

    # Charger et redimensionner le code-barres
    bc = Image.open(io.BytesIO(barcode_png)).convert("RGBA")

    # Largeur du code-barres = 80% de l'image source (min 300px)
    target_bc_w = max(300, int(src_w * 0.80))
    aspect = bc.height / bc.width
    target_bc_h = int(target_bc_w * aspect)
    bc_resized = bc.resize((target_bc_w, target_bc_h), Image.LANCZOS)

    # Bande de fond pour le code-barres
    band_h = target_bc_h + 20
    band = Image.new("RGBA", (src_w, band_h), (255, 255, 255, 230))

    # Légère ombre sur la bande
    shadow = Image.new("RGBA", (src_w, 4), (0, 0, 0, 40))

    # Canvas final
    total_h = src_h + band_h
    canvas = Image.new("RGBA", (src_w, total_h), (255, 255, 255, 255))

    if position == "top":
        canvas.paste(band, (0, 0))
        canvas.paste(shadow, (0, band_h - 2), shadow)
        canvas.paste(src, (0, band_h), src)
        # Coller le code-barres centré dans la bande
        bc_x = (src_w - target_bc_w) // 2
        bc_y = 10
    else:  # bottom
        canvas.paste(src, (0, 0), src)
        canvas.paste(shadow, (0, src_h), shadow)
        canvas.paste(band, (0, src_h))
        bc_x = (src_w - target_bc_w) // 2
        bc_y = src_h + 10

    canvas.paste(bc_resized, (bc_x, bc_y), bc_resized)

    # Convertir et sauvegarder
    result = canvas.convert("RGB")
    out_buf = io.BytesIO()

    ext_map = {
        "jpg": "JPEG",
        "jpeg": "JPEG",
        "png": "PNG",
        "webp": "WEBP",
    }
    fmt = ext_map.get(original_ext.lower().lstrip("."), "PNG")
    save_kwargs = {"format": fmt}
    if fmt == "JPEG":
        save_kwargs["quality"] = 92
        save_kwargs["optimize"] = True

    result.save(out_buf, **save_kwargs)
    out_buf.seek(0)
    return out_buf.read()
