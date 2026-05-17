"""
FinShield — Service PDF
Génération de rapports PDF professionnels (ReportLab)
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from osint_service import OSINTResult
from iban_service import IBANResult

# ── Palette ───────────────────────────────────────────────────────────────────
C_NAVY    = colors.HexColor("#1A2B4A")
C_RED     = colors.HexColor("#E63946")
C_GREEN   = colors.HexColor("#52B788")
C_ORANGE  = colors.HexColor("#F4A261")
C_PURPLE  = colors.HexColor("#6A0572")
C_LIGHT   = colors.HexColor("#F8F9FA")
C_GREY    = colors.HexColor("#ADB5BD")
C_WHITE   = colors.white

RISK_COLORS = {
    "low":      C_GREEN,
    "medium":   C_ORANGE,
    "high":     C_RED,
    "critical": C_PURPLE,
}


def _build_styles():
    base = getSampleStyleSheet()
    styles = {}
    styles["title"] = ParagraphStyle(
        "PDFTitle", fontSize=20, textColor=C_NAVY,
        fontName="Helvetica-Bold", spaceAfter=4, alignment=TA_LEFT,
    )
    styles["subtitle"] = ParagraphStyle(
        "PDFSub", fontSize=10, textColor=C_GREY,
        fontName="Helvetica", spaceAfter=2,
    )
    styles["section"] = ParagraphStyle(
        "PDFSection", fontSize=12, textColor=C_NAVY,
        fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=4,
    )
    styles["body"] = ParagraphStyle(
        "PDFBody", fontSize=9, fontName="Helvetica",
        leading=14, spaceAfter=4,
    )
    styles["small"] = ParagraphStyle(
        "PDFSmall", fontSize=7, textColor=C_GREY,
        fontName="Helvetica", leading=10,
    )
    styles["center"] = ParagraphStyle(
        "PDFCenter", fontSize=9, fontName="Helvetica",
        alignment=TA_CENTER,
    )
    return styles


def _meta_table(rows: list[list], col_widths=None) -> Table:
    """Table de métadonnées avec alternance de couleurs."""
    col_widths = col_widths or [4.5 * cm, 12 * cm]
    t = Table(rows, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("FONTNAME",       (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",       (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE",       (0, 0), (-1, -1), 8.5),
        ("TEXTCOLOR",      (0, 0), (0, -1), C_NAVY),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [C_LIGHT, C_WHITE]),
        ("GRID",           (0, 0), (-1, -1), 0.3, C_GREY),
        ("TOPPADDING",     (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 4),
        ("LEFTPADDING",    (0, 0), (-1, -1), 6),
    ]))
    return t


# ── Rapport OSINT ─────────────────────────────────────────────────────────────
def generate_osint_pdf(result: OSINTResult, analyst: str = "FinShield") -> bytes:
    """Génère un rapport PDF complet pour une analyse OSINT."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title=f"Rapport OSINT — {result.entity}",
    )
    S = _build_styles()
    story = []
    now = datetime.now().strftime("%d/%m/%Y à %H:%M")

    # ── En-tête ──
    story.append(Paragraph("🛡️ FinShield OSINT", S["title"]))
    story.append(Paragraph("Rapport de due diligence & analyse OSINT", S["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=2, color=C_NAVY))
    story.append(Spacer(1, 0.4 * cm))

    # ── Informations générales ──
    risk_color = RISK_COLORS.get(result.risk_level, C_GREY)
    meta = [
        ["Entité analysée :", result.entity],
        ["Type d'entité :",   result.entity_type.capitalize()],
        ["Date du rapport :", now],
        ["Analyste :",        analyst],
        ["Niveau de risque :", result.risk_level.upper()],
        ["Score de risque :",  f"{result.risk_score:.0%}"],
    ]
    story.append(_meta_table(meta))
    story.append(Spacer(1, 0.5 * cm))

    # ── Résumé exécutif ──
    story.append(Paragraph("Résumé exécutif", S["section"]))
    story.append(Paragraph(result.summary or "Aucun résumé disponible.", S["body"]))
    story.append(Spacer(1, 0.4 * cm))

    # ── Sanctions ──
    story.append(Paragraph("Vérification Sanctions (OpenSanctions)", S["section"]))
    if result.sanctions_hits:
        rows = [["Entité", "Score", "Listes", "Source"]]
        for h in result.sanctions_hits[:10]:
            rows.append([
                str(h.get("name", "—"))[:35],
                f"{h.get('score', 0):.0%}",
                ", ".join(h.get("datasets", []))[:40],
                str(h.get("source", "—")),
            ])
        t = Table(rows, colWidths=[5 * cm, 2 * cm, 6 * cm, 3 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, 0), C_NAVY),
            ("TEXTCOLOR",   (0, 0), (-1, 0), C_WHITE),
            ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",    (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_LIGHT, C_WHITE]),
            ("GRID",        (0, 0), (-1, -1), 0.3, C_GREY),
            ("TOPPADDING",  (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        ]))
        story.append(t)
    else:
        story.append(Paragraph("✅ Aucun hit sanctions identifié.", S["body"]))
    story.append(Spacer(1, 0.4 * cm))

    # ── Adverse Media ──
    story.append(Paragraph("Adverse Media (Presse & Web)", S["section"]))
    if result.adverse_media:
        for item in result.adverse_media[:6]:
            title = item.get("title", "—")[:80]
            url   = item.get("url", "")[:60]
            story.append(Paragraph(f"• {title}", S["body"]))
            if url:
                story.append(Paragraph(f"  <i>{url}</i>", S["small"]))
    else:
        story.append(Paragraph("✅ Aucun résultat presse négatif identifié.", S["body"]))
    story.append(Spacer(1, 0.4 * cm))

    # ── Analyse détaillée ──
    if result.raw_analysis:
        story.append(Paragraph("Analyse détaillée (IA)", S["section"]))
        for para in result.raw_analysis.split("\n\n")[:8]:
            if para.strip():
                story.append(Paragraph(para.strip(), S["body"]))
    story.append(Spacer(1, 0.4 * cm))

    # ── Sources consultées ──
    story.append(Paragraph("Sources consultées", S["section"]))
    for src in result.sources_checked:
        story.append(Paragraph(f"• {src}", S["body"]))
    story.append(Spacer(1, 0.6 * cm))

    # ── Disclaimer ──
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_GREY))
    story.append(Spacer(1, 0.2 * cm))
    disclaimer = (
        "⚠️ AVERTISSEMENT : Ce rapport est généré automatiquement à des fins "
        "d'aide à la décision AML/KYC. Les informations proviennent de sources "
        "publiques et peuvent être incomplètes, incorrectes ou périmées. "
        "Ce document ne constitue pas un avis juridique. "
        "Toute décision de conformité doit être validée par un professionnel qualifié. "
        "Usage professionnel uniquement — données confidentielles."
    )
    story.append(Paragraph(disclaimer, S["small"]))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


# ── Rapport IBAN ──────────────────────────────────────────────────────────────
def generate_iban_pdf(result: IBANResult) -> bytes:
    """Génère un rapport PDF pour une analyse IBAN."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
        title=f"Rapport IBAN — {result.iban_normalized}",
    )
    S = _build_styles()
    story = []
    now = datetime.now().strftime("%d/%m/%Y à %H:%M")

    story.append(Paragraph("🛡️ FinShield OSINT — Rapport IBAN", S["title"]))
    story.append(HRFlowable(width="100%", thickness=2, color=C_NAVY))
    story.append(Spacer(1, 0.4 * cm))

    validity = "✅ Valide" if result.valid else "❌ Invalide"
    meta = [
        ["IBAN analysé :",      result.iban_normalized or result.iban_raw],
        ["IBAN formaté :",      " ".join((result.iban_normalized or "")[i:i+4] for i in range(0, len(result.iban_normalized or ""), 4))],
        ["Validité :",          validity],
        ["Pays :",              f"{result.country_name} ({result.country_code})"],
        ["Code banque :",       result.bank_code or "—"],
        ["Code succursale :",   result.branch_code or "—"],
        ["Numéro de compte :",  result.account_number or "—"],
        ["Banque :",            result.bank_name or "—"],
        ["BIC/SWIFT :",         result.bic or "—"],
        ["Ville :",             result.city or "—"],
        ["Adresse :",           result.address or "—"],
        ["Niveau de confiance :", result.confidence_label],
        ["Indicateur risque :", result.risk_flag],
        ["Source :",            result.source or "—"],
        ["Date rapport :",      now],
    ]
    story.append(_meta_table(meta))

    if result.errors:
        story.append(Spacer(1, 0.4 * cm))
        story.append(Paragraph("Erreurs détectées", S["section"]))
        for err in result.errors:
            story.append(Paragraph(f"❌ {err}", S["body"]))

    if result.warnings:
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph("Avertissements", S["section"]))
        for w in result.warnings:
            story.append(Paragraph(f"⚠️ {w}", S["body"]))

    story.append(Spacer(1, 0.6 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_GREY))
    story.append(Paragraph(
        "Ce rapport est généré automatiquement. Vérifiez toujours les sources primaires. "
        "Usage professionnel uniquement — FinShield OSINT.",
        S["small"],
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
