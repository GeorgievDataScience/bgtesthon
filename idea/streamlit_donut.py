import html
import math
from base64 import b64encode

import streamlit as st


_TEAL = "#00BFA5"
_TEAL_TEXT = "#009688"
_ROSE = "#E11D48"
_ROSE_TEXT = "#BE123C"


def donut_accent(base: float, change: float, total: float) -> tuple[str, str, float]:
    """Return the accent stroke, text color, and share of the ring.

    A positive change is a share of the total. A negative change is a share of
    the starting base, capped at the whole ring.
    """
    if change >= 0 and base >= 0:
        share = change / total if total > 0 else 0.0
        return _TEAL, _TEAL_TEXT, share
    if change < 0:
        if base > 0:
            share = min(1.0, abs(change) / base)
        elif total < 0:
            share = min(1.0, abs(change) / abs(total))
        else:
            share = 1.0
        return _ROSE, _ROSE_TEXT, share
    if total <= 0:
        share = min(1.0, change / abs(base))
    else:
        share = min(1.0, total / change)
    return _TEAL, _TEAL_TEXT, share


_CELL = 360
_RADIUS = 125
_STROKE = 24
_SHEET_GAP = 18
_SHEET_MARGIN = 6


class _Sheet:
    """Ring size and the text placed inside it."""

    def __init__(
        self,
        radius,
        stroke,
        gap,
        margin,
        heading_size,
        sub_size,
        total_size,
        base_size,
        change_label_size,
        change_value_size,
        heading_dy,
        sub_dy,
        total_dy,
        base_dy,
        change_label_dy,
        change_value_dy,
        outside=False,
        cell_width=0,
        cell_height=0,
        ring_y=0,
        label_dy2=0,
    ):
        self.radius = radius
        self.stroke = stroke
        self.gap = gap
        self.margin = margin
        self.heading_size = heading_size
        self.sub_size = sub_size
        self.total_size = total_size
        self.base_size = base_size
        self.change_label_size = change_label_size
        self.change_value_size = change_value_size
        self.heading_dy = heading_dy
        self.sub_dy = sub_dy
        self.total_dy = total_dy
        self.base_dy = base_dy
        self.change_label_dy = change_label_dy
        self.change_value_dy = change_value_dy
        self.outside = outside
        self.cell_width = cell_width
        self.cell_height = cell_height
        self.ring_y = ring_y
        self.label_dy2 = label_dy2


_ROOMY = _Sheet(125, 24, 18, 6, 19, 14, 31, 15, 12, 19, -54, -29, 14, 45, 70, 93)
_COMPACT = _Sheet(130, 18, 10, 4, 22, 16, 34, 16, 16, 20, -82, -54, -8, 28, 54, 82)
_ROW = _Sheet(
    62, 12, 0, 0, 22, 16, 24, 16, 16, 18,
    -120, -88, 8, 92, 114, 158,
    outside=True, cell_width=184, cell_height=328, ring_y=154, label_dy2=134,
)


def _fmt(value: float) -> str:
    number = abs(value)
    text = f"{number:,.0f}".replace(",", " ") if number.is_integer() else f"{number:,.2f}".replace(",", " ")
    return f"-{text}" if value < 0 else text


def _money(value: float) -> str:
    amount = _fmt(abs(value))
    return f"-💵{amount}" if value < 0 else f"💵{amount}"


def _titles(year: int, kind: str = "forecast") -> tuple[str, str]:
    if kind == "total":
        heading = "За 1 година" if year == 1 else f"За {year} години"
        return heading, "ще сте платили"
    if year == 0:
        return "Текущата година", "е"
    return f"След {year} г.", "ще бъде"


def donut_group(
    year: int,
    base: float,
    accumulated_change: float,
    center_x: float,
    center_y: float,
    kind: str = "forecast",
    heading: str | None = None,
    subheading: str | None = None,
    sheet: _Sheet = _ROOMY,
) -> str:
    """One donut in a shared SVG. Colors stay on the elements."""
    total = base + accumulated_change
    accent, accent_text, share = donut_accent(base, accumulated_change, total)
    circumference = 2 * math.pi * sheet.radius
    segment = share * circumference
    if heading is None or subheading is None:
        default_heading, default_subheading = _titles(year, kind)
        heading = default_heading if heading is None else heading
        subheading = default_subheading if subheading is None else subheading
    return f"""
    <g>
      <circle cx="{center_x:.0f}" cy="{center_y:.0f}" r="{sheet.radius}" fill="none" stroke="#64748B" stroke-width="{sheet.stroke}" />
      <circle cx="{center_x:.0f}" cy="{center_y:.0f}" r="{sheet.radius}" fill="none" stroke="{accent}" stroke-width="{sheet.stroke}"
        stroke-dasharray="{segment:.4f} {circumference:.4f}" transform="rotate(-90 {center_x:.0f} {center_y:.0f})" />
      <text x="{center_x:.0f}" y="{center_y + sheet.heading_dy:.0f}" text-anchor="middle" class="heading">{html.escape(heading)}</text>
      <text x="{center_x:.0f}" y="{center_y + sheet.sub_dy:.0f}" text-anchor="middle" class="subheading">{html.escape(subheading)}</text>
      <text x="{center_x:.0f}" y="{center_y + sheet.total_dy:.0f}" text-anchor="middle" class="total">{html.escape(_money(total))}</text>
      <text x="{center_x:.0f}" y="{center_y + sheet.base_dy:.0f}" text-anchor="middle" class="base">базата е {html.escape(_fmt(base))}</text>
      {(_change_label(center_x, center_y, sheet, accent_text))}
      <text x="{center_x:.0f}" y="{center_y + sheet.change_value_dy:.0f}" text-anchor="middle" class="change-value" fill="{accent_text}">{html.escape(_money(accumulated_change))}</text>
    </g>"""


def _change_label(center_x: float, center_y: float, sheet: _Sheet, accent_text: str) -> str:
    if not sheet.outside:
        y = center_y + sheet.change_label_dy
        return (
            f'<text x="{center_x:.0f}" y="{y:.0f}" text-anchor="middle" '
            f'class="change-label" fill="{accent_text}">натрупаната промяна е</text>'
        )
    first = center_y + sheet.change_label_dy
    second = center_y + sheet.label_dy2
    return (
        f'<text x="{center_x:.0f}" y="{first:.0f}" text-anchor="middle" '
        f'class="change-label" fill="{accent_text}">натрупаната</text>'
        f'<text x="{center_x:.0f}" y="{second:.0f}" text-anchor="middle" '
        f'class="change-label" fill="{accent_text}">промяна е</text>'
    )


def _centers(count: int, columns: int = 2, sheet: _Sheet = _ROOMY) -> tuple[int, int, int, int, str, list[tuple[float, float]]]:
    """Place one roomy donut, or pack several with a short gap between rings."""
    columns = 1 if count <= 1 else columns
    rows = math.ceil(count / columns)
    if sheet.cell_width and count > 1:
        centers = []
        for index in range(count):
            column = index % columns
            row = index // columns
            centers.append((
                column * sheet.cell_width + sheet.cell_width / 2,
                row * sheet.cell_height + sheet.ring_y,
            ))
        return columns, rows, int(columns * sheet.cell_width), int(rows * sheet.cell_height), "100%", centers
    if count <= 1:
        centers = [(_CELL / 2, _CELL / 2)]
        return columns, rows, _CELL, _CELL, "400px", centers
    outer = sheet.radius + sheet.stroke / 2
    pitch = 2 * outer + sheet.gap
    width = 2 * sheet.margin + columns * (2 * outer) + (columns - 1) * sheet.gap
    height = 2 * sheet.margin + rows * (2 * outer) + (rows - 1) * sheet.gap
    centers = []
    for index in range(count):
        column = index % columns
        row = index // columns
        centers.append((
            sheet.margin + outer + column * pitch,
            sheet.margin + outer + row * pitch,
        ))
    return columns, rows, int(width), int(height), "100%", centers


def _sheet_style(sheet: _Sheet) -> str:
    return f"""
        text {{ font-family: system-ui, -apple-system, 'Segoe UI', sans-serif; }}
        .heading {{ fill: #1F2937; font-size: {sheet.heading_size}px; font-weight: 700; }}
        .subheading {{ fill: #4B5563; font-size: {sheet.sub_size}px; }}
        .total {{ fill: #111827; font-size: {sheet.total_size}px; font-weight: 700; }}
        .base {{ fill: #64748B; font-size: {sheet.base_size}px; font-weight: 650; }}
        .change-label {{ font-size: {sheet.change_label_size}px; font-weight: 650; }}
        .change-value {{ font-size: {sheet.change_value_size}px; font-weight: 700; }}
      """


def financial_donuts_page(
    periods: list[tuple[int, float, float]],
    kind: str = "forecast",
    *,
    columns: int = 2,
    headings: list[str] | None = None,
    subheading: str | None = None,
) -> str:
    """One responsive SVG. A single period stays one cell; several use two columns."""
    if columns >= 8:
        sheet = _ROW
    elif columns >= 4:
        sheet = _COMPACT
    else:
        sheet = _ROOMY
    _columns, _rows, width, height, _max_width, centers = _centers(len(periods), columns, sheet)
    groups = []
    labels = []
    for index, ((year, base, change), (center_x, center_y)) in enumerate(zip(periods, centers)):
        heading = None if headings is None else headings[index]
        title, _default_subheading = _titles(year, kind)
        shown = title if heading is None else heading
        total = base + change
        labels.append(
            f"{shown}: общо {_fmt(total)}, база {_fmt(base)}, натрупана промяна {_fmt(change)}"
        )
        groups.append(donut_group(
            year,
            base,
            change,
            center_x,
            center_y,
            kind,
            heading,
            subheading,
            sheet,
        ))
    label = html.escape(" ".join(labels), quote=True)
    return f"""<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{label}">
      <style>{_sheet_style(sheet)}</style>
      {''.join(groups)}
    </svg>"""


def render_financial_donuts(
    periods: list[tuple[int, float, float]],
    kind: str = "forecast",
    *,
    columns: int = 2,
    headings: list[str] | None = None,
    subheading: str | None = None,
) -> None:
    """Render several periods as one SVG image that shrinks with its content."""
    cleaned = []
    for year, base, change in periods:
        base = float(base)
        change = float(change)
        if not all(math.isfinite(x) for x in (base, change)):
            st.error("Невалидни стойности за диаграмата.")
            return
        cleaned.append((int(year), base, change))
    if not cleaned:
        return
    if headings is not None and len(headings) != len(cleaned):
        st.error("Невалидни заглавия за диаграмата.")
        return
    svg = financial_donuts_page(
        cleaned,
        kind,
        columns=columns,
        headings=headings,
        subheading=subheading,
    )
    encoded = b64encode(svg.encode("utf-8")).decode("ascii")
    max_width = "400px" if len(cleaned) == 1 else "100%"
    alt = svg.split('aria-label="', 1)[1].split('"', 1)[0]
    st.html(
        f'<div style="width:100%;max-width:{max_width};margin:0 auto">'
        f'<img alt="{alt}" src="data:image/svg+xml;base64,{encoded}" '
        'style="width:100%;height:auto;display:block" />'
        "</div>"
    )


def render_financial_donut(year: int, base: float, accumulated_change: float, *, height: int = 380) -> None:
    """Render one responsive, dependency-free SVG donut."""
    render_financial_donuts([(year, base, accumulated_change)])


# Demo only. In the real app, replace these sample values with existing calculations.
if __name__ == "__main__":
    st.title("Прогноза по години")
    selected_year = st.slider("Година от прогнозата", min_value=0, max_value=30, value=30)
    example_base = 200.0
    example_change = 42.0 * selected_year / 30.0  # DEMO, not a financial model
    render_financial_donut(selected_year, example_base, example_change)
