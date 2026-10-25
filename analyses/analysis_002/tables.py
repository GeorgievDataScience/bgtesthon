"""Analysis 002 table construction and highlighting."""
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
