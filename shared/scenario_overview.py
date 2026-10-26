"""Colored scenario table shared by the analyses."""
from base64 import b64encode
from html import escape

# One stable color per scenario, in scenario order: low, typical, high, then the two extremes.
SCENARIO_BAR_COLORS = (
    ("#86efac", "#bbf7d0"),
    ("#16a34a", "#4ade80"),
    ("#94a3b8", "#e2e8f0"),
    ("#475569", "#94a3b8"),
    ("#fdba74", "#fed7aa"),
    ("#ea580c", "#fb923c"),
    ("#38bdf8", "#7dd3fc"),
    ("#e11d48", "#fb7185"),
)


def _text_on(color: str) -> str:
    value = color.lstrip("#")
    red, green, blue = (int(value[index:index + 2], 16) for index in (0, 2, 4))
    luminance = (0.2126 * red + 0.7152 * green + 0.0722 * blue) / 255
    return "#1F2937" if luminance >= 0.58 else "#FFFFFF"


_OVERVIEW_WIDTH = 720
_OVERVIEW_HEADER = 36
_OVERVIEW_ROW = 38
_OVERVIEW_COLUMNS = (
    ("Промяна", 16, 128),
    ("Статистика", 144, 140),
    ("Сценарии", 284, 250),
    ("Ниво", 534, 170),
)


def scenario_overview_svg(rows) -> str:
    """One SVG table. Each row is (change, statistic, scenario, level, color)."""
    height = _OVERVIEW_HEADER + len(rows) * _OVERVIEW_ROW
    labels = []
    parts = [
        f'<rect width="{_OVERVIEW_WIDTH}" height="{_OVERVIEW_HEADER}" fill="#F8FAFC"/>'
    ]
    for title, left, _width in _OVERVIEW_COLUMNS:
        parts.append(
            f'<text class="head" x="{left}" y="24">{escape(title)}</text>'
        )
    for index, (change, statistic, scenario, level, color) in enumerate(rows):
        top = _OVERVIEW_HEADER + index * _OVERVIEW_ROW
        ink = _text_on(color)
        values = (change, statistic, scenario, level)
        labels.append(
            f"{change}, {statistic}, {scenario}, {level}"
        )
        parts.append(
            f'<rect y="{top}" width="{_OVERVIEW_WIDTH}" height="{_OVERVIEW_ROW}" '
            f'fill="{color}"/>'
        )
        baseline = top + 25
        for value, ( _title, left, _width) in zip(values, _OVERVIEW_COLUMNS):
            parts.append(
                f'<text class="cell" x="{left}" y="{baseline}" fill="{ink}">'
                f"{escape(value)}</text>"
            )
    label = escape(" ".join(labels), quote=True)
    body = "".join(parts)
    return (
        f'<svg viewBox="0 0 {_OVERVIEW_WIDTH} {height}" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{label}">'
        "<style>"
        "text{font-family:Segoe UI,Source Sans Pro,sans-serif}"
        ".head{fill:#475569;font-size:14px;font-weight:700}"
        ".cell{font-size:16px;font-weight:650}"
        "</style>"
        f'<clipPath id="overview"><rect width="{_OVERVIEW_WIDTH}" height="{height}" rx="10"/></clipPath>'
        f'<g clip-path="url(#overview)">{body}</g>'
        "</svg>"
    )


def render_scenario_overview(rows) -> None:
    """Show the scenario table as one SVG image."""
    import streamlit as st

    svg = scenario_overview_svg(rows)
    encoded = b64encode(svg.encode("utf-8")).decode("ascii")
    alt = svg.split('aria-label="', 1)[1].split('"', 1)[0]
    st.html(
        '<div style="width:100%;margin:0.2rem 0 0.8rem">'
        f'<img alt="{alt}" src="data:image/svg+xml;base64,{encoded}" '
        'style="width:100%;height:auto;display:block" />'
        "</div>"
    )
