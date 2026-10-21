import html
import json
from decimal import Decimal
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import select

from salesia.shared.infrastructure.models import CompanyModel, CustomerModel


def quotation_pdf(db, row):

    company = db.scalar(select(CompanyModel).where(CompanyModel.id == row.company_id))

    customer = db.scalar(
        select(CustomerModel).where(CustomerModel.id == row.customer_id, CustomerModel.company_id == row.company_id)
    )

    buffer = BytesIO()

    document = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)

    styles = getSampleStyleSheet()

    story = [
        Paragraph(html.escape(company.trade_name or company.legal_name), styles["Title"]),
        Paragraph(f"Cotización {html.escape(row.quotation_number)} · Versión {row.version}", styles["Heading2"]),
        Spacer(1, 12),
    ]

    story.append(
        Paragraph(
            f"Cliente: {html.escape(customer.legal_name)} · Documento: {html.escape(customer.doc_number)}",
            styles["BodyText"],
        )
    )

    story.append(
        Paragraph(
            f"Válida hasta: {html.escape(row.valid_until or 'Sin fecha')} · Moneda: {html.escape(row.currency)} · Pago: {row.payment_terms_days} días",
            styles["BodyText"],
        )
    )

    story.append(Spacer(1, 12))

    data = [["SKU", "Producto", "Cantidad", "Precio", "Total"]]

    for line in json.loads(row.lines_json):
        line_total = Decimal(line["line_subtotal"]) + Decimal(line["line_tax"])

        data.append(
            [
                line["sku"],
                line["name"],
                line["quantity"],
                f"{row.currency} {line['unit_price']}",
                f"{row.currency} {line_total}",
            ]
        )

    table = Table(data, colWidths=[75, 190, 65, 85, 90], repeatRows=1)

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
            ]
        )
    )

    story.extend(
        [
            table,
            Spacer(1, 12),
            Paragraph(f"Subtotal: {row.currency} {row.subtotal_amount}", styles["BodyText"]),
            Paragraph(f"Impuestos: {row.currency} {row.tax_amount}", styles["BodyText"]),
            Paragraph(f"Total: {row.currency} {row.total_amount}", styles["Heading2"]),
        ]
    )

    if row.delivery_terms:
        story.append(Paragraph(f"Entrega: {html.escape(row.delivery_terms)}", styles["BodyText"]))

    if row.special_conditions:
        story.append(Paragraph(f"Condiciones especiales: {html.escape(row.special_conditions)}", styles["BodyText"]))

    if row.notes:
        story.append(Paragraph(f"Notas: {html.escape(row.notes)}", styles["BodyText"]))

    document.build(story)

    buffer.seek(0)

    return buffer
