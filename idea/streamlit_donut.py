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


def render_financial_donut(year: int, base: float, accumulated_change: float, *, height: int = 380) -> None:
    """Render a responsive, dependency-free SVG donut for any finite base and change."""
    base = float(base)
    accumulated_change = float(accumulated_change)
    if not all(math.isfinite(x) for x in (base, accumulated_change)):
        st.error("Невалидни стойности за диаграмата.")
        return

    total = base + accumulated_change
    accent, accent_text, share = donut_accent(base, accumulated_change, total)
    radius = 125
    circumference = 2 * math.pi * radius
    segment = share * circumference
    if year == 0:
        heading = "Текущата година"
        subheading = "е"
    else:
        heading = f"След {year} г."
        subheading = "ще бъде"

    def fmt(value: float) -> str:
        number = abs(value)
        text = f"{number:,.0f}".replace(",", " ") if number.is_integer() else f"{number:,.2f}".replace(",", " ")
        return f"-{text}" if value < 0 else text

    def money(value: float) -> str:
        amount = fmt(abs(value))
        return f"-💵{amount}" if value < 0 else f"💵{amount}"

    # Use a real SVG viewBox to preserve positions on narrow screens.
    svg = f"""
    <div class="donut-wrap" role="img" aria-label="{heading}: общо {fmt(total)}, база {fmt(base)}, натрупана промяна {fmt(accumulated_change)}">
      <svg viewBox="0 0 360 360" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
        <circle cx="180" cy="180" r="{radius}" fill="none" stroke="#64748B" stroke-width="24" />
        <circle cx="180" cy="180" r="{radius}" fill="none" stroke="{accent}" stroke-width="24"
          stroke-dasharray="{segment:.4f} {circumference:.4f}" transform="rotate(-90 180 180)" />
        <text x="180" y="126" text-anchor="middle" class="heading">{heading}</text>
        <text x="180" y="151" text-anchor="middle" class="subheading">{subheading}</text>
        <text x="180" y="194" text-anchor="middle" class="total">{html.escape(money(total))}</text>
        <text x="180" y="225" text-anchor="middle" class="base">базата е {html.escape(fmt(base))}</text>
        <text x="180" y="250" text-anchor="middle" class="change-label">натрупаната промяна е</text>
        <text x="180" y="273" text-anchor="middle" class="change-value">{html.escape(money(accumulated_change))}</text>
      </svg>
    </div>
    """
    page = f"""<!doctype html><html lang="bg"><head><meta charset="utf-8" />
    <style>
      html, body {{ margin: 0; padding: 0; background: transparent; overflow: hidden; }}
      .donut-wrap {{ width: 100%; max-width: 400px; margin: 0 auto; }}
      svg {{ display: block; width: 100%; height: auto; overflow: visible; font-family: system-ui, -apple-system, 'Segoe UI', sans-serif; }}
      .heading {{ fill: #1F2937; font-size: 19px; font-weight: 700; }}
      .subheading {{ fill: #4B5563; font-size: 14px; }}
      .total {{ fill: #111827; font-size: 31px; font-weight: 700; }}
      .base {{ fill: #64748B; font-size: 15px; font-weight: 650; }}
      .change-label {{ fill: {accent_text}; font-size: 12px; font-weight: 650; }}
      .change-value {{ fill: {accent_text}; font-size: 19px; font-weight: 700; }}
    </style></head><body>{svg}</body></html>"""
    st.iframe(page, height="content")


# Demo only. In the real app, replace these sample values with existing calculations.
if __name__ == "__main__":
    st.title("Прогноза по години")
    selected_year = st.slider("Година от прогнозата", min_value=0, max_value=30, value=30)
    example_base = 200.0
    example_change = 42.0 * selected_year / 30.0  # DEMO, not a financial model
    render_financial_donut(selected_year, example_base, example_change)
