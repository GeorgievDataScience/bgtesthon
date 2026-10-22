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


def donut_group(year: int, base: float, accumulated_change: float, center_x: float, center_y: float, kind: str = "forecast") -> str:
    """One donut in a shared SVG. Colors stay on the elements."""
    total = base + accumulated_change
    accent, accent_text, share = donut_accent(base, accumulated_change, total)
    circumference = 2 * math.pi * _RADIUS
    segment = share * circumference
    heading, subheading = _titles(year, kind)
    return f"""
    <g>
      <circle cx="{center_x:.0f}" cy="{center_y:.0f}" r="{_RADIUS}" fill="none" stroke="#64748B" stroke-width="{_STROKE}" />
      <circle cx="{center_x:.0f}" cy="{center_y:.0f}" r="{_RADIUS}" fill="none" stroke="{accent}" stroke-width="{_STROKE}"
        stroke-dasharray="{segment:.4f} {circumference:.4f}" transform="rotate(-90 {center_x:.0f} {center_y:.0f})" />
      <text x="{center_x:.0f}" y="{center_y - 54:.0f}" text-anchor="middle" class="heading">{heading}</text>
      <text x="{center_x:.0f}" y="{center_y - 29:.0f}" text-anchor="middle" class="subheading">{subheading}</text>
      <text x="{center_x:.0f}" y="{center_y + 14:.0f}" text-anchor="middle" class="total">{html.escape(_money(total))}</text>
      <text x="{center_x:.0f}" y="{center_y + 45:.0f}" text-anchor="middle" class="base">базата е {html.escape(_fmt(base))}</text>
      <text x="{center_x:.0f}" y="{center_y + 70:.0f}" text-anchor="middle" class="change-label" fill="{accent_text}">натрупаната промяна е</text>
      <text x="{center_x:.0f}" y="{center_y + 93:.0f}" text-anchor="middle" class="change-value" fill="{accent_text}">{html.escape(_money(accumulated_change))}</text>
    </g>"""


def _centers(count: int) -> tuple[int, int, int, int, str, list[tuple[float, float]]]:
    """Place one roomy donut, or pack several with a short gap between rings."""
    columns = 1 if count <= 1 else 2
    rows = math.ceil(count / columns)
    if count <= 1:
        centers = [(_CELL / 2, _CELL / 2)]
        return columns, rows, _CELL, _CELL, "400px", centers
    outer = _RADIUS + _STROKE / 2
    pitch = 2 * outer + _SHEET_GAP
    width = 2 * _SHEET_MARGIN + columns * (2 * outer) + (columns - 1) * _SHEET_GAP
    height = 2 * _SHEET_MARGIN + rows * (2 * outer) + (rows - 1) * _SHEET_GAP
    centers = []
    for index in range(count):
        column = index % columns
        row = index // columns
        centers.append((
            _SHEET_MARGIN + outer + column * pitch,
            _SHEET_MARGIN + outer + row * pitch,
        ))
    return columns, rows, int(width), int(height), "100%", centers


def financial_donuts_page(periods: list[tuple[int, float, float]], kind: str = "forecast") -> str:
    """One responsive SVG. A single period stays one cell; several use two columns."""
    _columns, _rows, width, height, _max_width, centers = _centers(len(periods))
    groups = []
    labels = []
    for (year, base, change), (center_x, center_y) in zip(periods, centers):
        heading, _subheading = _titles(year, kind)
        total = base + change
        labels.append(
            f"{heading}: общо {_fmt(total)}, база {_fmt(base)}, натрупана промяна {_fmt(change)}"
        )
        groups.append(donut_group(year, base, change, center_x, center_y, kind))
    label = html.escape(" ".join(labels), quote=True)
    return f"""<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{label}">
      <style>
        text {{ font-family: system-ui, -apple-system, 'Segoe UI', sans-serif; }}
        .heading {{ fill: #1F2937; font-size: 19px; font-weight: 700; }}
        .subheading {{ fill: #4B5563; font-size: 14px; }}
        .total {{ fill: #111827; font-size: 31px; font-weight: 700; }}
        .base {{ fill: #64748B; font-size: 15px; font-weight: 650; }}
        .change-label {{ font-size: 12px; font-weight: 650; }}
        .change-value {{ font-size: 19px; font-weight: 700; }}
      </style>
      {''.join(groups)}
    </svg>"""


def render_financial_donuts(periods: list[tuple[int, float, float]], kind: str = "forecast") -> None:
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
    svg = financial_donuts_page(cleaned, kind)
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
