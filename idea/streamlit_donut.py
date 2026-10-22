import html
import math
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


def _fmt(value: float) -> str:
    number = abs(value)
    text = f"{number:,.0f}".replace(",", " ") if number.is_integer() else f"{number:,.2f}".replace(",", " ")
    return f"-{text}" if value < 0 else text


def _money(value: float) -> str:
    amount = _fmt(abs(value))
    return f"-💵{amount}" if value < 0 else f"💵{amount}"


def _titles(year: int) -> tuple[str, str]:
    if year == 0:
        return "Текущата година", "е"
    return f"След {year} г.", "ще бъде"


def donut_group(year: int, base: float, accumulated_change: float, origin_x: float, origin_y: float) -> str:
    """One donut translated into a shared SVG. Colors stay on the elements."""
    total = base + accumulated_change
    accent, accent_text, share = donut_accent(base, accumulated_change, total)
    circumference = 2 * math.pi * _RADIUS
    segment = share * circumference
    heading, subheading = _titles(year)
    center = _CELL / 2
    return f"""
    <g transform="translate({origin_x:.0f} {origin_y:.0f})">
      <circle cx="{center:.0f}" cy="{center:.0f}" r="{_RADIUS}" fill="none" stroke="#64748B" stroke-width="24" />
      <circle cx="{center:.0f}" cy="{center:.0f}" r="{_RADIUS}" fill="none" stroke="{accent}" stroke-width="24"
        stroke-dasharray="{segment:.4f} {circumference:.4f}" transform="rotate(-90 {center:.0f} {center:.0f})" />
      <text x="{center:.0f}" y="126" text-anchor="middle" class="heading">{heading}</text>
      <text x="{center:.0f}" y="151" text-anchor="middle" class="subheading">{subheading}</text>
      <text x="{center:.0f}" y="194" text-anchor="middle" class="total">{html.escape(_money(total))}</text>
      <text x="{center:.0f}" y="225" text-anchor="middle" class="base">базата е {html.escape(_fmt(base))}</text>
      <text x="{center:.0f}" y="250" text-anchor="middle" class="change-label" fill="{accent_text}">натрупаната промяна е</text>
      <text x="{center:.0f}" y="273" text-anchor="middle" class="change-value" fill="{accent_text}">{html.escape(_money(accumulated_change))}</text>
    </g>"""


def financial_donuts_page(periods: list[tuple[int, float, float]]) -> str:
    """One responsive SVG. A single period stays one cell; several use two columns."""
    columns = 1 if len(periods) <= 1 else 2
    rows = math.ceil(len(periods) / columns)
    groups = []
    labels = []
    for index, (year, base, change) in enumerate(periods):
        heading, _subheading = _titles(year)
        total = base + change
        labels.append(
            f"{heading}: общо {_fmt(total)}, база {_fmt(base)}, натрупана промяна {_fmt(change)}"
        )
        groups.append(
            donut_group(
                year,
                base,
                change,
                (index % columns) * _CELL,
                (index // columns) * _CELL,
            )
        )
    width = columns * _CELL
    height = rows * _CELL
    max_width = 400 if columns == 1 else width
    label = html.escape(" ".join(labels), quote=True)
    svg = f"""
    <div class="donut-wrap" role="img" aria-label="{label}">
      <svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
        {''.join(groups)}
      </svg>
    </div>
    """
    return f"""<!doctype html><html lang="bg"><head><meta charset="utf-8" />
    <style>
      html, body {{ margin: 0; padding: 0; background: transparent; overflow: hidden; }}
      .donut-wrap {{ width: 100%; max-width: {max_width}px; margin: 0 auto; }}
      svg {{ display: block; width: 100%; height: auto; overflow: visible; font-family: system-ui, -apple-system, 'Segoe UI', sans-serif; }}
      .heading {{ fill: #1F2937; font-size: 19px; font-weight: 700; }}
      .subheading {{ fill: #4B5563; font-size: 14px; }}
      .total {{ fill: #111827; font-size: 31px; font-weight: 700; }}
      .base {{ fill: #64748B; font-size: 15px; font-weight: 650; }}
      .change-label {{ font-size: 12px; font-weight: 650; }}
      .change-value {{ font-size: 19px; font-weight: 700; }}
    </style></head><body>{svg}</body></html>"""


def render_financial_donuts(periods: list[tuple[int, float, float]]) -> None:
    """Render several periods as one SVG donut sheet."""
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
    st.iframe(financial_donuts_page(cleaned), height="content")


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
