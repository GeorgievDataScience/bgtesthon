"""SVG line of the historical price index."""
from base64 import b64encode
from html import escape
import math


_WIDTH = 720
_HEIGHT = 340
_LEFT = 54
_RIGHT = 18
_TOP = 28
_BOTTOM = 46
_LIGHT_LINE = "#15803d"
_DARK_LINE = "#4ade80"
_LIGHT_TEXT = "#31333F"
_DARK_TEXT = "#FAFAFA"
_LIGHT_GRID = "#E5E7EB"
_DARK_GRID = "#3F3F46"


def index_line_svg(years, values, *, theme=None) -> str | None:
    """One SVG line of the price index. Missing values break the line."""
    points = _finite_points(years, values)
    if not points:
        return None
    year_min = min(year for year, _value in points)
    year_max = max(year for year, _value in points)
    low, high, ticks = _value_ticks([value for _year, value in points])
    plot_left = _LEFT
    plot_right = _WIDTH - _RIGHT
    plot_top = _TOP
    plot_bottom = _HEIGHT - _BOTTOM
    coords = []
    dots = []
    for year, value in points:
        x = _along(year, year_min, year_max, plot_left, plot_right)
        y = _along(value, low, high, plot_bottom, plot_top)
        coords.append((x, y, year, value))
        dots.append((x, y))
    path = _path(_segments(coords))
    theme_class = "theme-dark" if theme == "dark" else "theme-light" if theme == "light" else ""
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_WIDTH} {_HEIGHT}" '
        f'role="img" aria-label="{escape(_alt(points), quote=True)}" class="{theme_class}">',
        _style(),
        f'<text class="title" x="{plot_left}" y="18">Индексна стойност</text>',
    ]
    for tick in ticks:
        y = _along(tick, low, high, plot_bottom, plot_top)
        parts.append(
            f'<line class="grid" x1="{plot_left}" y1="{y:.1f}" x2="{plot_right}" y2="{y:.1f}" />'
        )
        parts.append(
            f'<text class="tick" x="{plot_left - 8}" y="{y + 4:.1f}" text-anchor="end">'
            f"{escape(_number(tick))}</text>"
        )
    if path:
        parts.append(f'<path class="line" d="{path}" />')
    for x, y in dots:
        parts.append(f'<circle class="dot" cx="{x:.1f}" cy="{y:.1f}" r="2.8" />')
    for year in _year_ticks(year_min, year_max):
        x = _along(year, year_min, year_max, plot_left, plot_right)
        parts.append(
            f'<text class="tick" x="{x:.1f}" y="{plot_bottom + 22:.1f}" text-anchor="middle">'
            f"{year}</text>"
        )
    parts.append(
        f'<text class="title" x="{(plot_left + plot_right) / 2:.1f}" y="{_HEIGHT - 8}" '
        f'text-anchor="middle">Година</text>'
    )
    parts.append("</svg>")
    return "".join(parts)


def index_line_html(years, values, *, theme=None) -> str | None:
    """SVG image markup for the index line. None when nothing can be drawn."""
    svg = index_line_svg(years, values, theme=theme)
    if svg is None:
        return None
    encoded = b64encode(svg.encode("utf-8")).decode("ascii")
    alt = svg.split('aria-label="', 1)[1].split('"', 1)[0]
    return (
        '<div style="width:100%;margin:0.2rem 0 0.6rem">'
        f'<img alt="{alt}" src="data:image/svg+xml;base64,{encoded}" '
        'style="width:100%;height:auto;display:block" />'
        "</div>"
    )


def _finite_points(years, values):
    points = []
    for year, value in zip(years, values):
        try:
            year_number = int(year)
            value_number = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(value_number):
            points.append((year_number, value_number))
    points.sort()
    return points


def _segments(coords):
    """Split the line where a calendar year is missing."""
    segments = []
    current = []
    previous_year = None
    for x, y, year, _value in coords:
        if previous_year is not None and year > previous_year + 1:
            if current:
                segments.append(current)
            current = []
        current.append((x, y))
        previous_year = year
    if current:
        segments.append(current)
    return segments


def _path(segments):
    commands = []
    for segment in segments:
        if len(segment) < 2:
            continue
        x, y = segment[0]
        commands.append(f"M{x:.1f} {y:.1f}")
        for x, y in segment[1:]:
            commands.append(f"L{x:.1f} {y:.1f}")
    return " ".join(commands)


def _along(value, start, end, pixel_start, pixel_end):
    if end == start:
        return (pixel_start + pixel_end) / 2
    return pixel_start + (value - start) / (end - start) * (pixel_end - pixel_start)


def _value_ticks(values):
    low = min(values)
    high = max(values)
    span = high - low
    pad = span * 0.08 if span else max(abs(low) * 0.08, 1)
    low -= pad
    high += pad
    step = _nice_step(high - low)
    nice_low = math.floor(low / step) * step
    nice_high = math.ceil(high / step) * step
    for _attempt in range(3):
        ticks = _steps(nice_low, nice_high, step)
        if len(ticks) <= 6:
            return nice_low, nice_high, ticks
        step *= 2
        nice_low = math.floor(low / step) * step
        nice_high = math.ceil(high / step) * step
    return nice_low, nice_high, _steps(nice_low, nice_high, step)


def _nice_step(span):
    raw = span / 5
    magnitude = 10 ** math.floor(math.log10(raw))
    for factor in (1, 2, 2.5, 5, 10):
        candidate = factor * magnitude
        count = span / candidate
        if 3 <= count <= 6:
            return candidate
    return 10 * magnitude


def _steps(start, end, step):
    ticks = []
    value = start
    guard = 0
    while value <= end + step * 0.001 and guard < 12:
        ticks.append(round(value, 6))
        value += step
        guard += 1
    return ticks


def _year_ticks(first, last):
    span = last - first
    if span <= 8:
        return list(range(first, last + 1))
    step = 5 if span <= 40 else 10
    ticks = [first]
    year = math.ceil((first + 1) / step) * step
    while year < last:
        if year - ticks[-1] >= step * 0.6:
            ticks.append(year)
        year += step
    if last - ticks[-1] < step * 0.6:
        ticks[-1] = last
    else:
        ticks.append(last)
    return ticks


def _number(value):
    if abs(value - round(value)) < 1e-6:
        return str(int(round(value)))
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return text.replace(".", ",")


def _alt(points):
    shown = ", ".join(f"{year} {_number(value)}" for year, value in points)
    return f"Индекс по години: {shown}"


def _style():
    return (
        "<style>"
        f".line{{fill:none;stroke:{_LIGHT_LINE};stroke-width:2.5;"
        "stroke-linejoin:round;stroke-linecap:round}"
        f".dot{{fill:{_LIGHT_LINE}}}"
        f".grid{{stroke:{_LIGHT_GRID};stroke-width:1}}"
        f".tick,.title{{fill:{_LIGHT_TEXT};"
        "font-family:Segoe UI,Source Sans Pro,sans-serif}"
        ".tick{font-size:13px}"
        ".title{font-size:14px;font-weight:600}"
        "@media (prefers-color-scheme:dark){"
        f".line{{stroke:{_DARK_LINE}}}"
        f".dot{{fill:{_DARK_LINE}}}"
        f".grid{{stroke:{_DARK_GRID}}}"
        f".tick,.title{{fill:{_DARK_TEXT}}}"
        "}"
        f"svg.theme-light .line{{stroke:{_LIGHT_LINE}}}"
        f"svg.theme-light .dot{{fill:{_LIGHT_LINE}}}"
        f"svg.theme-light .grid{{stroke:{_LIGHT_GRID}}}"
        f"svg.theme-light .tick,svg.theme-light .title{{fill:{_LIGHT_TEXT}}}"
        f"svg.theme-dark .line{{stroke:{_DARK_LINE}}}"
        f"svg.theme-dark .dot{{fill:{_DARK_LINE}}}"
        f"svg.theme-dark .grid{{stroke:{_DARK_GRID}}}"
        f"svg.theme-dark .tick,svg.theme-dark .title{{fill:{_DARK_TEXT}}}"
        "</style>"
    )


def render_index_line(chart_data):
    """Draw the index line through st.html."""
    import streamlit as st

    theme = None
    try:
        theme = st.context.theme.type
    except Exception:
        theme = None
    html = index_line_html(
        chart_data["year"].tolist(),
        chart_data["idx_value"].tolist(),
        theme=theme,
    )
    if html is None:
        st.caption("Няма индексни стойности за този период.")
        return
    st.html(html)
