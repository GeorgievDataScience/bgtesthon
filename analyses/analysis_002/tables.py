"""Analysis 002 table construction and highlighting."""
import pandas as pd

from shared.hierarchy_place import build_hierarchy_table
from shared.scenario_overview import (
    render_scenario_overview,
    scenario_overview_svg,
)


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


def highlight_statistics_table(statistics_df, selected_statistic):
    def highlight_selected_statistic(row):
        if row["Статистика"] == selected_statistic:
            selected_style = "background-color: #dceeff; color: #123b5d; font-weight: 600;"
            return [selected_style] * len(row)
        return [""] * len(row)
    return statistics_df.style.apply(highlight_selected_statistic, axis=1)
