import html
import io
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def sanitize_csv_cell(val: Any) -> str:
    if val is None:
        return ""
    if isinstance(val, (int, float, Decimal)):
        return str(val)
    s = str(val)
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        s = "'" + s
    if any(c in s for c in (",", '"', "\n", "\r")):
        s = '"' + s.replace('"', '""') + '"'
    return s


def build_csv_content(columns: list[str], rows: list[dict[str, Any]]) -> bytes:
    header = ",".join(sanitize_csv_cell(c) for c in columns)
    lines = [header]
    for r in rows:
        lines.append(",".join(sanitize_csv_cell(r.get(c, "")) for c in columns))
    return ("\ufeff" + "\r\n".join(lines)).encode("utf-8")


def build_xlsx_content(columns: list[str], rows: list[dict[str, Any]], report_title: str) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Reporte"
    ws.views.sheetView[0].showGridLines = True
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    header_font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    data_font = Font(name="Calibri", size=9)
    thin_border = Border(
        left=Side(style="thin", color="CBD5E1"),
        right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"),
        bottom=Side(style="thin", color="CBD5E1"),
    )
    for col_idx, col_name in enumerate(columns, 1):
        cell = ws.cell(row=1, column=col_idx, value=col_name)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border
    ws.row_dimensions[1].height = 24
    for row_idx, row_data in enumerate(rows, 2):
        for col_idx, col_name in enumerate(columns, 1):
            val = row_data.get(col_name)
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.font = data_font
            cell.border = thin_border
            if val is None or val == "":
                cell.value = ""
                cell.number_format = "@"
            elif (
                any(k in col_name.lower() for k in ("id", "doc", "sku", "code", "ruc", "series", "number"))
                and isinstance(val, str)
                and val.startswith("0")
            ):
                cell.value = str(val)
                cell.number_format = "@"
            elif isinstance(val, (int, float, Decimal)):
                if isinstance(val, int):
                    cell.value = val
                    cell.number_format = "#,##0"
                else:
                    cell.value = float(val)
                    cell.number_format = "#,##0.00"
            elif isinstance(val, str):
                try:
                    dec = Decimal(val)
                    cell.value = float(dec)
                    cell.number_format = "#,##0.00"
                except Exception:
                    cell.value = val
                    cell.number_format = "@"
            else:
                cell.value = str(val)
                cell.number_format = "@"
    for col in ws.columns:
        max_len = max(len(str(c.value or "")) for c in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 40)
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(841.89 - 28, 16, page_text)
        self.drawString(28, 16, "SalesIA Enterprise · Documento Confidencial de Auditoría y Reportes")
        self.restoreState()


def build_pdf_content(
    columns: list[str],
    rows: list[dict[str, Any]],
    report_title: str,
    branding: dict[str, Any],
    status_condition: Optional[str] = None,
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4), leftMargin=28, rightMargin=28, topMargin=28, bottomMargin=28
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#0F172A"),
    )
    meta_style = ParagraphStyle(
        "DocMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#475569"),
    )
    th_style = ParagraphStyle(
        "THStyle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=9,
        textColor=colors.white,
        alignment=1,
    )
    td_style = ParagraphStyle(
        "TDStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=6.5,
        leading=8.5,
        textColor=colors.HexColor("#1E293B"),
    )
    story = []
    company_name = branding.get("legal_name", "SalesIA Enterprise")
    tax_id = branding.get("tax_id", "")
    cutoff_time = branding.get("cutoff_time", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"))
    tax_line = f" · RUC: {html.escape(tax_id)}" if tax_id else ""
    header_html = f"<b>{html.escape(company_name)}</b>{tax_line}<br/>"
    header_html += f"<b>{html.escape(report_title)}</b> · Corte: {html.escape(cutoff_time)}"
    story.append(Paragraph(header_html, title_style))
    story.append(Spacer(1, 4))
    if status_condition and status_condition.lower() in ("cancelled", "anulada", "refunded"):
        annulled_notice = (
            "<font color='#DC2626'><b>[DOCUMENTO ANULADO / CANCELADO - VALIDEZ TRIBUTARIA NULA]</b></font>"
        )
        story.append(Paragraph(annulled_notice, title_style))
        story.append(Spacer(1, 4))
    story.append(Paragraph(f"Total registros: {len(rows)} | Formato: Reporte Empresarial Sellado SHA-256", meta_style))
    story.append(Spacer(1, 8))
    usable_width = 841.89 - 56
    num_cols = len(columns)
    col_width = usable_width / max(num_cols, 1)
    col_widths = [col_width] * num_cols
    table_data = [[Paragraph(html.escape(col), th_style) for col in columns]]
    for row in rows:
        row_cells = []
        for col in columns:
            val = str(row.get(col, "") or "")
            row_cells.append(Paragraph(html.escape(val), td_style))
        table_data.append(row_cells)
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
                ("LEFTPADDING", (0, 0), (-1, -1), 2.5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2.5),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ]
        )
    )
    story.append(t)
    doc.build(story, canvasmaker=NumberedCanvas)
    return buffer.getvalue()
