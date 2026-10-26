"""SVG table of a category's place in the COICOP hierarchy."""
from base64 import b64encode
from html import escape

import pandas as pd

_WIDTH = 720
_HEADER = 36
_FONT = 15
_LINE = 22
_PAD_X = 16
_PAD_Y = 11
_LEVELS = (
    ("division code", "division_name_bg", "🌐 Дивизия:"),
    ("group code", "group_name_bg", "- > 🗂️ Група:"),
    ("class code", "class_name_bg", "- - > 📦 Клас:"),
    ("subclass code", "subclass_name_bg", "- - - > 🧩 Подклас:"),
    ("detailed level code", "detailed_level_name_bg", "- - - - > 🏷️ Детайлно ниво:"),
)
_SELECTED_FILL = "#d9f2d9"
_SELECTED_INK = "#0b3d1e"


def hierarchy_rows(selected_details, selected_coicop):
    """Five classification rows: level label, code and name, and whether it is the chosen one."""
    chosen = f"{selected_coicop} —"
    rows = []
    for code_column, name_column, level in _LEVELS:
        label = _hierarchy_label(selected_details, code_column, name_column)
        rows.append((level, label, str(label).startswith(chosen)))
    return rows


def build_hierarchy_table(selected_details, selected_coicop):
    """Styled frame kept for the existing hierarchy check."""
    rows = hierarchy_rows(selected_details, selected_coicop)
    frame = pd.DataFrame({
        "Йерархично ниво": [level for level, _label, _picked in rows],
        "Код и наименование": [label for _level, label, _picked in rows],
    })

    def highlight_selected_level(row):
        if str(row["Код и наименование"]).startswith(f"{selected_coicop} —"):
            selected_style = "background-color: #d9f2d9; color: #0b3d1e; font-weight: 600;"
            return [selected_style] * len(row)
        return [""] * len(row)

    return frame.style.apply(highlight_selected_level, axis=1)


def hierarchy_svg(rows, *, theme=None) -> str:
    """One SVG table. Each row is (level, label, selected). Long names wrap."""
    level_width = max(_text_width(level, _FONT) for level, _label, _picked in rows) + 28
    name_left = _PAD_X + level_width
    name_width = _WIDTH - name_left - _PAD_X
    laid_out = []
    height = _HEADER
    for level, label, selected in rows:
        lines = _wrap(label, name_width, _FONT)
        row_height = _PAD_Y * 2 + len(lines) * _LINE
        laid_out.append((level, lines, selected, height, row_height))
        height += row_height
    theme_class = "theme-dark" if theme == "dark" else "theme-light" if theme == "light" else ""
    alt = "; ".join(f"{level} {label}" for level, label, _selected in rows)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_WIDTH} {height}" '
        f'role="img" aria-label="{escape(alt, quote=True)}" class="{theme_class}">',
        _style(),
        f'<clipPath id="place"><rect width="{_WIDTH}" height="{height}" rx="10"/></clipPath>',
        '<g clip-path="url(#place)">',
        f'<rect class="head-bg" width="{_WIDTH}" height="{_HEADER}"/>',
        f'<text class="head" x="{_PAD_X}" y="24">Йерархично ниво</text>',
        f'<text class="head" x="{name_left:.0f}" y="24">Код и наименование</text>',
    ]
    for index, (level, lines, selected, top, row_height) in enumerate(laid_out):
        band = "selected" if selected else "band alt" if index % 2 else "band"
        ink = "picked" if selected else "cell"
        parts.append(
            f'<rect class="{band}" y="{top}" width="{_WIDTH}" height="{row_height}"/>'
        )
        level_y = top + (row_height - _LINE) / 2 + _FONT * 0.75
        parts.append(
            f'<text class="{ink}" x="{_PAD_X}" y="{level_y:.1f}">{escape(level)}</text>'
        )
        block = len(lines) * _LINE
        first = top + (row_height - block) / 2 + _FONT * 0.75
        for line_index, line in enumerate(lines):
            parts.append(
                f'<text class="name {ink}" x="{name_left:.0f}" y="{first + line_index * _LINE:.1f}">'
                f"{escape(line)}</text>"
            )
    parts.append("</g></svg>")
    return "".join(parts)


def render_hierarchy_place(selected_details, selected_coicop) -> None:
    """Show the classification place as one SVG image."""
    import streamlit as st

    theme = None
    try:
        theme = st.context.theme.type
    except Exception:
        theme = None
    svg = hierarchy_svg(hierarchy_rows(selected_details, selected_coicop), theme=theme)
    encoded = b64encode(svg.encode("utf-8")).decode("ascii")
    alt = svg.split('aria-label="', 1)[1].split('"', 1)[0]
    st.html(
        '<div style="width:100%;margin:0.2rem 0 0.8rem">'
        f'<img alt="{alt}" src="data:image/svg+xml;base64,{encoded}" '
        'style="width:100%;height:auto;display:block" />'
        "</div>"
    )


def _hierarchy_label(selected_details, code_column, name_column):
    code = selected_details[code_column]
    name = selected_details[name_column]
    if pd.isna(code) or pd.isna(name):
        return "Няма"
    return f"{code} — {name}"


def _char_width(char, font):
    if char == "\ufe0f":
        return 0
    if ord(char) > 0x2600:
        return font * 1.2
    if char == " ":
        return font * 0.34
    return font * 0.62


def _text_width(text, font):
    return sum(_char_width(char, font) for char in text)


def _wrap(text, max_width, font):
    words = str(text).split(" ")
    lines = []
    current = ""
    for word in words:
        if not word:
            continue
        trial = word if not current else f"{current} {word}"
        if _text_width(trial, font) <= max_width:
            current = trial
            continue
        if current:
            lines.append(current)
        if _text_width(word, font) <= max_width:
            current = word
            continue
        chunk = ""
        for char in word:
            if _text_width(chunk + char, font) <= max_width:
                chunk += char
            else:
                if chunk:
                    lines.append(chunk)
                chunk = char
        current = chunk
    if current:
        lines.append(current)
    return lines or [""]


def _style():
    return (
        "<style>"
        "text{font-family:Segoe UI,Source Sans Pro,sans-serif}"
        ".head-bg{fill:#F8FAFC}"
        ".band{fill:#FFFFFF}"
        ".alt{fill:#F8FAFC}"
        f".selected{{fill:{_SELECTED_FILL}}}"
        ".head{fill:#475569;font-size:14px;font-weight:700}"
        f".cell{{fill:#1F2937;font-size:{_FONT}px}}"
        f".picked{{fill:{_SELECTED_INK};font-size:{_FONT}px;font-weight:700}}"
        "@media (prefers-color-scheme:dark){"
        ".head-bg{fill:#27272A}"
        ".band{fill:#18181B}"
        ".alt{fill:#27272A}"
        f".selected{{fill:{_SELECTED_FILL}}}"
        ".head{fill:#E5E7EB}"
        ".cell{fill:#FAFAFA}"
        f".picked{{fill:{_SELECTED_INK}}}"
        "}"
        "svg.theme-light .head-bg{fill:#F8FAFC}"
        "svg.theme-light .band{fill:#FFFFFF}"
        "svg.theme-light .alt{fill:#F8FAFC}"
        f"svg.theme-light .selected{{fill:{_SELECTED_FILL}}}"
        "svg.theme-light .head{fill:#475569}"
        "svg.theme-light .cell{fill:#1F2937}"
        f"svg.theme-light .picked{{fill:{_SELECTED_INK}}}"
        "svg.theme-dark .head-bg{fill:#27272A}"
        "svg.theme-dark .band{fill:#18181B}"
        "svg.theme-dark .alt{fill:#27272A}"
        f"svg.theme-dark .selected{{fill:{_SELECTED_FILL}}}"
        "svg.theme-dark .head{fill:#E5E7EB}"
        "svg.theme-dark .cell{fill:#FAFAFA}"
        f"svg.theme-dark .picked{{fill:{_SELECTED_INK}}}"
        "</style>"
    )
