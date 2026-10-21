"""Reusable minimal SVG bar chart, drawn from values the caller already has."""

from base64 import b64encode
from html import escape
import math
import re

_SCALES = {"auto", "linear", "log", "hybrid"}
_COLOR = re.compile(r"^#(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6}|[0-9A-Fa-f]{8})$")
_LIGHT_BAR = "#15803d"
_DARK_BAR = "#4ade80"
_LIGHT_TEXT = "#31333F"
_DARK_TEXT = "#FAFAFA"
_LIGHT_ZERO = "#E5E7EB"
_DARK_ZERO = "#3F3F46"


def hybrid_scale(value, threshold):
    """Continuous hybrid scale for a non-negative magnitude."""
    if value <= threshold:
        return value
    return threshold * (1 + math.log(value / threshold))


def chart_fractions(values, scale="auto", hybrid_threshold=100, auto_ratio=100):
    """Signed bar shares of the plot area, plus the scale actually used.

    A share of 1 fills the whole plot. Mixed signs split that area, so the
    positive and negative extremes add up to 1. Missing values stay None.
    """
    numbers = [_number(value) for value in values]
    mode = _resolve_scale(numbers, scale, auto_ratio)
    transformed = [
        None if number is None else _transform(number, mode, hybrid_threshold)
        for number in numbers
    ]
    positive = max((item for item in transformed if item is not None and item > 0), default=0.0)
    negative = max((-item for item in transformed if item is not None and item < 0), default=0.0)
    span = positive + negative
    fractions = []
    for item in transformed:
        if item is None:
            fractions.append(None)
        elif span == 0:
            fractions.append(0.0)
        else:
            fractions.append(item / span)
    return fractions, mode


def render_mini_bar_chart(
    values,
    labels,
    title=None,
    scale="auto",
    color=None,
    height=180,
    hybrid_threshold=100,
    auto_ratio=100,
):
    """Draw one row of vertical bars through ``st.html``.

    Negative values hang below a zero line; the number above each bar is the
    original value. Zero has no height. Invalid values leave an empty slot
    labeled „—“. ``auto`` uses a linear scale, or the hybrid scale when the
    largest positive value is at least ``auto_ratio`` times the smallest.
    """
    import streamlit as st

    theme = None
    try:
        theme = st.context.theme.type
    except Exception:
        theme = None
    st.html(
        build_mini_bar_chart_html(
            values,
            labels,
            title=title,
            scale=scale,
            color=color,
            height=height,
            hybrid_threshold=hybrid_threshold,
            auto_ratio=auto_ratio,
            theme=theme,
        )
    )


def build_mini_bar_chart_html(
    values,
    labels,
    title=None,
    scale="auto",
    color=None,
    height=180,
    hybrid_threshold=100,
    auto_ratio=100,
    theme=None,
):
    if len(values) != len(labels):
        raise ValueError("values and labels must have the same length")
    if not values:
        raise ValueError("values must not be empty")
    if scale not in _SCALES:
        raise ValueError(f"scale must be one of {', '.join(sorted(_SCALES))}")
    if hybrid_threshold <= 0 or auto_ratio <= 0:
        raise ValueError("hybrid_threshold and auto_ratio must be positive")
    if height < 80:
        raise ValueError("height must be at least 80")

    numbers = [_number(value) for value in values]
    fractions, mode = chart_fractions(
        numbers,
        scale=scale,
        hybrid_threshold=hybrid_threshold,
        auto_ratio=auto_ratio,
    )
    bar_color = color if isinstance(color, str) and _COLOR.match(color) else None
    svg = _svg(numbers, labels, fractions, height, theme, bar_color)
    encoded = b64encode(svg.encode("utf-8")).decode("ascii")
    alt = _alt_text(numbers, labels)
    parts = ['<div style="width:100%;margin:0.45rem 0 0.1rem">']
    if title:
        parts.append(
            '<div style="text-align:center;font-weight:600;margin:0 0 0.3rem">'
            f"{escape(str(title))}</div>"
        )
    parts.append(
        f'<img alt="{escape(alt, quote=True)}" '
        f'src="data:image/svg+xml;base64,{encoded}" '
        'style="width:100%;height:auto;display:block" />'
    )
    if mode == "hybrid":
        parts.append(_scale_note("Хибридна скала"))
    elif mode == "log":
        parts.append(_scale_note("Логаритмична скала"))
    parts.append("</div>")
    return "".join(parts)


def _scale_note(text):
    return (
        '<div style="text-align:center;font-size:0.75rem;line-height:1.2;'
        'opacity:0.6;margin:0.05rem 0 0">'
        f"{escape(text)}</div>"
    )


def _svg(numbers, labels, fractions, height, theme, bar_color):
    count = len(numbers)
    view_w = count * 70
    view_h = float(height)
    bar_top = 32.0
    bar_bottom = view_h - 36.0
    label_y = view_h - 10.0
    value_gap = 16.0
    area = bar_bottom - bar_top
    positive = max((item for item in fractions if item is not None and item > 0), default=0.0)
    negative = max((-item for item in fractions if item is not None and item < 0), default=0.0)
    span = positive + negative
    baseline = bar_bottom if span == 0 else bar_top + (positive / span) * area
    slot = view_w / count
    bar_w = slot * 0.42
    theme_class = "theme-dark" if theme == "dark" else "theme-light" if theme == "light" else ""
    chunks = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {view_w:.0f} {view_h:.0f}" '
        f'width="{view_w:.0f}" height="{view_h:.0f}" '
        f'preserveAspectRatio="xMidYMid meet" class="{theme_class}">',
        _style(bar_color),
    ]
    if negative > 0:
        chunks.append(
            f'<line class="zero" x1="0" y1="{baseline:.2f}" '
            f'x2="{view_w:.0f}" y2="{baseline:.2f}" />'
        )
    for index, (number, label, fraction) in enumerate(zip(numbers, labels, fractions)):
        center = slot * index + slot / 2
        x = center - bar_w / 2
        shown = "—" if number is None else _format_value(number)
        pixel = 0.0 if fraction in (None, 0.0) else abs(fraction) * area
        if pixel > 0:
            if fraction > 0:
                path = _rounded_end(x, baseline - pixel, bar_w, pixel, 6, top=True)
                text_y = baseline - pixel - value_gap
            else:
                path = _rounded_end(x, baseline, bar_w, pixel, 6, top=False)
                text_y = baseline - value_gap
            if path:
                chunks.append(f'<path class="bar" d="{path}" />')
        else:
            text_y = baseline - value_gap
        number_size = _value_size(shown, slot)
        chunks.append(
            f'<text class="num" x="{center:.2f}" y="{text_y:.2f}" text-anchor="middle" '
            f'font-size="{number_size}">{_money_label(shown, number_size)}</text>'
        )
        chunks.append(
            f'<text class="lbl" x="{center:.2f}" y="{label_y:.2f}" text-anchor="middle" '
            f'font-size="13">{escape(_shorten(label))}</text>'
        )
    chunks.append("</svg>")
    return "".join(chunks)


def _style(bar_color):
    light = bar_color or _LIGHT_BAR
    dark = bar_color or _DARK_BAR
    return (
        "<style>"
        f".bar{{fill:{light}}}"
        f".num{{fill:{_LIGHT_TEXT};font-weight:700;"
        "font-family:Segoe UI,Source Sans Pro,sans-serif}}"
        ".bill{font-family:\"Segoe UI Emoji\",\"Segoe UI Symbol\",sans-serif}"
        f".lbl{{fill:{_LIGHT_TEXT};font-weight:400;"
        "font-family:Segoe UI,Source Sans Pro,sans-serif}}"
        f".zero{{stroke:{_LIGHT_ZERO};stroke-width:1}}"
        "@media (prefers-color-scheme:dark){"
        f".bar{{fill:{dark}}}"
        f".num,.lbl{{fill:{_DARK_TEXT}}}"
        f".zero{{stroke:{_DARK_ZERO}}}"
        "}"
        f"svg.theme-light .bar{{fill:{light}}}"
        f"svg.theme-light .num,svg.theme-light .lbl{{fill:{_LIGHT_TEXT}}}"
        f"svg.theme-light .zero{{stroke:{_LIGHT_ZERO}}}"
        f"svg.theme-dark .bar{{fill:{dark}}}"
        f"svg.theme-dark .num,svg.theme-dark .lbl{{fill:{_DARK_TEXT}}}"
        f"svg.theme-dark .zero{{stroke:{_DARK_ZERO}}}"
        "</style>"
    )


def _rounded_end(x, y, width, height, radius, top):
    if height <= 0 or width <= 0:
        return ""
    radius = min(radius, width / 2, height)
    bottom = y + height
    right = x + width
    if top:
        return (
            f"M {x:.2f} {bottom:.2f} "
            f"L {x:.2f} {y + radius:.2f} "
            f"A {radius:.2f} {radius:.2f} 0 0 1 {x + radius:.2f} {y:.2f} "
            f"L {right - radius:.2f} {y:.2f} "
            f"A {radius:.2f} {radius:.2f} 0 0 1 {right:.2f} {y + radius:.2f} "
            f"L {right:.2f} {bottom:.2f} Z"
        )
    return (
        f"M {x:.2f} {y:.2f} "
        f"L {x:.2f} {bottom - radius:.2f} "
        f"A {radius:.2f} {radius:.2f} 0 0 0 {x + radius:.2f} {bottom:.2f} "
        f"L {right - radius:.2f} {bottom:.2f} "
        f"A {radius:.2f} {radius:.2f} 0 0 0 {right:.2f} {bottom - radius:.2f} "
        f"L {right:.2f} {y:.2f} Z"
    )


def _resolve_scale(numbers, scale, auto_ratio):
    if scale != "auto":
        return scale
    positives = [number for number in numbers if number is not None and number > 0]
    if len(positives) < 2:
        return "linear"
    if max(positives) / min(positives) >= auto_ratio:
        return "hybrid"
    return "linear"


def _transform(value, mode, hybrid_threshold):
    magnitude = abs(value)
    if mode == "linear":
        scaled = magnitude
    elif mode == "log":
        scaled = math.log1p(magnitude)
    else:
        scaled = hybrid_scale(magnitude, hybrid_threshold)
    if value < 0:
        return -scaled
    return scaled


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    if not math.isfinite(number):
        return None
    return number


def _money_label(shown, size):
    if not shown.startswith("-💵") and not shown.startswith("💵"):
        return escape(shown)
    sign = "-" if shown.startswith("-") else ""
    amount = shown.split("💵", 1)[1]
    bill_size = max(size - 1, 8)
    return (
        f"{escape(sign)}"
        f'<tspan class="bill" font-size="{bill_size}" dy="3">💵</tspan>'
        f'<tspan dy="-3">{escape(amount)}</tspan>'
    )


def _format_value(value):
    if value.is_integer() and abs(value) < 10**15:
        amount = f"{int(abs(value)):,}".replace(",", " ")
    else:
        amount = f"{abs(value):,.2f}".replace(",", " ").replace(".", ",")
    if value < 0:
        return f"-💵{amount}"
    return f"💵{amount}"


def _value_size(text, slot):
    width = sum(2 if char == "💵" else 1 for char in text)
    size = 15
    while size > 8 and width * size * 0.58 > slot * 0.94:
        size -= 1
    return size


def _shorten(label, limit=8):
    text = str(label).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _alt_text(numbers, labels):
    parts = []
    for number, label in zip(numbers, labels):
        shown = "няма" if number is None else _format_value(number)
        parts.append(f"{_shorten(label)} {shown}")
    return ", ".join(parts)
