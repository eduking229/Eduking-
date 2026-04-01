"""
DocShield – Estampillage de documents PDF avec code-barres Code 128.
Utilise reportlab pour créer l'overlay et pypdf pour la fusion.
"""
import io
from PIL import Image as PILImage

from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4
import pypdf


def stamp_pdf(input_bytes: bytes, barcode_png: bytes, position: str = "bottom") -> bytes:
    """
    Ajoute le code-barres sur chaque page du PDF.
    position: 'bottom' | 'top'
    """
    # Charger le PDF source
    reader = pypdf.PdfReader(io.BytesIO(input_bytes))
    writer = pypdf.PdfWriter()

    # Dimensions du code-barres
    bc_img = PILImage.open(io.BytesIO(barcode_png))
    bc_w_pt = 140 * mm  # largeur en points (1 mm = ~2.83 pt)
    bc_h_pt = bc_w_pt * bc_img.height / bc_img.width

    for page in reader.pages:
        # Récupérer les dimensions de la page
        page_w = float(page.mediabox.width)
        page_h = float(page.mediabox.height)

        # Créer l'overlay avec reportlab
        overlay_buf = io.BytesIO()
        c = rl_canvas.Canvas(overlay_buf, pagesize=(page_w, page_h))

        # Positionnement
        margin = 8 * mm
        x = (page_w - bc_w_pt) / 2  # centré horizontalement

        if position == "top":
            y = page_h - bc_h_pt - margin
        else:  # bottom
            y = margin

        # Dessiner le code-barres (image PNG dans un buffer)
        bc_buf = io.BytesIO(barcode_png)
        c.drawImage(
            bc_buf,
            x, y,
            width=bc_w_pt,
            height=bc_h_pt,
            preserveAspectRatio=True,
            mask="auto",
        )

        # Ligne décorative
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.setLineWidth(0.5)
        if position == "top":
            c.line(margin, page_h - bc_h_pt - margin - 4, page_w - margin, page_h - bc_h_pt - margin - 4)
        else:
            c.line(margin, margin + bc_h_pt + 4, page_w - margin, margin + bc_h_pt + 4)

        c.save()
        overlay_buf.seek(0)

        # Fusionner overlay + page originale
        overlay_reader = pypdf.PdfReader(overlay_buf)
        overlay_page = overlay_reader.pages[0]

        page.merge_page(overlay_page)
        writer.add_page(page)

    # Copier les métadonnées
    if reader.metadata:
        writer.add_metadata(reader.metadata)

    # Ajouter nos métadonnées DocShield
    writer.add_metadata({
        "/Producer": "DocShield v1.0",
        "/DocShieldProtected": "true",
    })

    out_buf = io.BytesIO()
    writer.write(out_buf)
    out_buf.seek(0)
    return out_buf.read()
