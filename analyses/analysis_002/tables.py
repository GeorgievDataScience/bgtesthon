"""Analysis 002 table construction and highlighting."""
from html import escape

import pandas as pd


def build_statistics_table(percentage_values: pd.Series):
    statistic_rows = [
        (percentage_values.min(), "Минимум", "Минимум", "Екстреми"),
        (percentage_values.quantile(0.10), "П10", "Много ниско", "Оптимистичен"),
        (percentage_values.quantile(0.25), "П25", "Ниско", "Оптимистичен"),
        (percentage_values.median(), "Медиана", "Типично", "Типичен"),
        (percentage_values.mean(), "Средно", "Средно", "Типичен"),
        (percentage_values.quantile(0.75), "П75", "Високо", "Песимистичен"),
        (percentage_values.quantile(0.90), "П90", "Много високо", "Песимистичен"),
        (percentage_values.max(), "Максимум", "Максимум", "Екстреми"),
    ]
    statistics_df = pd.DataFrame({
        "Процент": [f"{value:.2f}%".replace(".", ",") for value, _, _, _ in statistic_rows],
        "Статистика": [statistic for _, statistic, _, _ in statistic_rows],
        "Ниво": [level for _, _, level, _ in statistic_rows],
        "Сценарии": [scenario for _, _, _, scenario in statistic_rows],
    })
    return statistic_rows, statistics_df


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
    from base64 import b64encode

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


def highlight_statistics_table(statistics_df, selected_statistic):
    def highlight_selected_statistic(row):
        if row["Статистика"] == selected_statistic:
            selected_style = "background-color: #dceeff; color: #123b5d; font-weight: 600;"
            return [selected_style] * len(row)
        return [""] * len(row)
    return statistics_df.style.apply(highlight_selected_statistic, axis=1)


def build_hierarchy_table(selected_details, selected_coicop):
    def hierarchy_label(code_column, name_column):
        code = selected_details[code_column]
        name = selected_details[name_column]
        if pd.isna(code) or pd.isna(name):
            return "Няма"
        return f"{code} — {name}"

    selected_filters = pd.DataFrame({
        "Йерархично ниво": [
            "🌐 Дивизия:", "- > 🗂️ Група:", "- - > 📦 Клас:",
            "- - - > 🧩 Подклас:", "- - - - > 🏷️ Детайлно ниво:",
        ],
        "Код и наименование": [
            hierarchy_label("division code", "division_name_bg"),
            hierarchy_label("group code", "group_name_bg"),
            hierarchy_label("class code", "class_name_bg"),
            hierarchy_label("subclass code", "subclass_name_bg"),
            hierarchy_label("detailed level code", "detailed_level_name_bg"),
        ],
    })

    def highlight_selected_level(row):
        value = str(row["Код и наименование"])
        if value.startswith(f"{selected_coicop} —"):
            selected_style = "background-color: #d9f2d9; color: #0b3d1e; font-weight: 600;"
            return [selected_style] * len(row)
        return [""] * len(row)
    return selected_filters.style.apply(highlight_selected_level, axis=1)
