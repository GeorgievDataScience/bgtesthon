from .components.history import render_history
from .components.description import render_description
from html import escape
from .calculations import projected_series, projected_values_for, total_period_amounts
from .scenarios import scenario_labels, scenario_levels, scenario_statistics
from .tables import (
    build_hierarchy_table,
    render_scenario_overview,
    build_statistics_table,
)
from .charts import prepare_index_data
from math import isfinite
from .components.context import load_context
import pandas as pd
import streamlit as st
from shared.data_loader import (
    DATA_PATH, DESCRIPTION_DATA_PATH, SPENDING_RANGES_PATH,
    load_data, load_description_data, load_spending_ranges,
)
from shared.mini_bar_chart import render_mini_bar_chart

# One stable color per scenario, in scenario order: low, typical, high, then the two extremes.
_SCENARIO_BAR_COLORS = (
    ("#86efac", "#bbf7d0"),
    ("#16a34a", "#4ade80"),
    ("#94a3b8", "#e2e8f0"),
    ("#475569", "#94a3b8"),
    ("#fdba74", "#fed7aa"),
    ("#ea580c", "#fb923c"),
    ("#38bdf8", "#7dd3fc"),
    ("#e11d48", "#fb7185"),
)

def category_sentence_label(details) -> str:
    selected_icon = (
        details.class_icon
        if not pd.isna(details.class_icon)
        else details.group_icon
    )
    icon = "" if pd.isna(selected_icon) else f"{selected_icon} "
    return f"{icon}{details.coicop_names_bg}"


def show_expense_heading(lead, country_label, coicop_label):
    st.markdown(
        "<div class='expense-context'>"
        f"<strong>{escape(lead)}</strong> "
        f"за {escape(coicop_label)} "
        f"в {escape(country_label)}"
        "</div>",
        unsafe_allow_html=True,
    )


COICOP_GUIDE_URL = (
    "https://unstats.un.org/unsd/classifications/"
    "unsdclassifications/COICOP_2018_pre_copy_edit_publication.pdf"
)

def render():
    st.caption(
        "🌍 Изберете държава и 🛒 категория от ХИПЦ, "
        "след което въведете 💶 месечна стойност. След 🔎 „Покажи“ "
        "ще видите как този разход може да се промени през "
        "следващите 30 години според историческите ценови "
        "изменения. Резултатът е илюстративен, а не прогноза."
    )

    context = load_context()
    df = context.df
    description_df = context.description_df
    coicop_details = context.coicop_details
    countries = context.countries
    country_dropdown_labels = context.country_dropdown_labels
    coicop_values = context.coicop_values
    coicop_labels = context.coicop_labels

    with st.container(key="wide_filters"):

        selected_country = st.selectbox(
            "Държава",
            options=countries,
            format_func=country_dropdown_labels.__getitem__,
        )

        selected_coicop = st.selectbox(
            "Категория от ХИПЦ",
            options=coicop_values,
            format_func=coicop_labels.__getitem__,
        )

        entered_value = st.text_input(
            "Въведете месечен разход 💵",
            placeholder="напр. 1200",
        )
        if entered_value.strip():
            try:
                preview_entered = float(
                    entered_value.replace(" ", "").replace(
                        ",", "."
                    )
                )
            except ValueError:
                preview_entered = None
            if (
                preview_entered is not None
                and isfinite(preview_entered)
                and preview_entered > 1_000_000_000
            ):
                st.error(
                    "Стойността не може да е над 1 милиард."
                )

        show_results = st.button(
            "🔎 Покажи",
            type="primary",
        )

    if show_results:
        st.session_state["results_visible"] = True
        st.session_state["shown_selection"] = {
            "country": selected_country,
            "coicop": selected_coicop,
            "entered_value": entered_value,
        }

    shown = st.session_state.get("shown_selection")
    if st.session_state.get("results_visible") and shown:
        selected_country = shown["country"]
        selected_coicop = shown["coicop"]
        entered_value = shown["entered_value"]
        selected_details = coicop_details.loc[selected_coicop]

        highlighted_hierarchy = build_hierarchy_table(selected_details, selected_coicop)

        filtered_df = df[
            (df["country"] == selected_country)
            & (df["coicop18"] == selected_coicop)
        ]

        if filtered_df.empty:
            st.info("Няма данни за избраната комбинация.")
        else:
            percentage_values = filtered_df[
                "percentage_change_inx"
            ].dropna()

            if percentage_values.empty:
                st.info(
                    "Няма процентни стойности за статистическо "
                    "обобщение."
                )
            else:
                statistic_rows, statistics_df = build_statistics_table(percentage_values)
                statistic_values = {
                    statistic: value
                    for value, statistic, _, _ in statistic_rows
                }

                highlighted_statistics = statistics_df
                scenario_order = [
                    (scenario, level)
                    for scenario, levels in scenario_levels.items()
                    for level in levels
                ]
                overview_rows = []
                for (scenario, level), (light, _dark) in zip(
                    scenario_order,
                    _SCENARIO_BAR_COLORS,
                ):
                    statistic = scenario_statistics[(scenario, level)]
                    change = statistic_values[statistic]
                    change_text = f"{change:.2f}%".replace(".", ",")
                    overview_rows.append((
                        change_text,
                        statistic,
                        scenario_labels[scenario],
                        level,
                        light,
                    ))
                render_scenario_overview(overview_rows)

                input_text = entered_value.strip()
                if not input_text:
                    st.info(
                        "Въведете месечна стойност, за да видите "
                        "30-годишната сценарна проекция."
                    )
                else:
                    normalized_input = (
                        input_text.replace(" ", "").replace(",", ".")
                    )
                    try:
                        monthly_value = float(normalized_input)
                    except ValueError:
                        monthly_value = None

                    if (
                        monthly_value is None
                        or not isfinite(monthly_value)
                        or monthly_value <= 0
                    ):
                        st.error(
                            "Въведете валидно положително число."
                        )
                    elif monthly_value > 1_000_000_000:
                        st.error(
                            "Стойността не може да е над "
                            "1 милиард."
                        )
                    else:
                        annual_value = monthly_value * 12
                        projection_section = st.radio(
                            "Разходи във времето",
                            options=[
                                "📈 Месечен / годишен разход",
                                "💰 Общ разход по периоди",
                            ],
                            horizontal=True,
                            key="projection_section_view_v4",
                            label_visibility="collapsed",
                        )
                        st.divider()
                        sentence_country = country_dropdown_labels[
                            selected_country
                        ]
                        sentence_category = category_sentence_label(
                            selected_details
                        )
                        if (
                            projection_section
                            == "📈 Месечен / годишен разход"
                        ):
                            show_yearly = bool(
                                st.session_state.get(
                                    "projection_show_yearly",
                                    False,
                                )
                            )
                            expense_lead = (
                                "Колко ще плащате на година"
                                if show_yearly
                                else "Колко ще плащате на месец"
                            )
                            show_expense_heading(
                                expense_lead,
                                sentence_country,
                                sentence_category,
                            )
                            yearly_col, all_years_col = st.columns(
                                [1, 1],
                                vertical_alignment="center",
                            )
                            with yearly_col:
                                st.checkbox(
                                    "Годишен разход",
                                    key="projection_show_yearly",
                                )
                            with all_years_col:
                                show_all_years = st.checkbox(
                                    "Всички години",
                                    key="analysis_002_show_all_years",
                                )
                            scenario_pairs = [
                                (scenario, level)
                                for scenario, levels in scenario_levels.items()
                                for level in levels
                            ]
                            scenario_series = [
                                projected_series(
                                    monthly_value,
                                    statistic_values[
                                        scenario_statistics[pair]
                                    ],
                                    show_yearly,
                                )
                                for pair in scenario_pairs
                            ]
                            horizon_labels = [
                                level for _scenario, level in scenario_pairs
                            ]
                            horizons = (
                                range(1, 31)
                                if show_all_years
                                else (1, 2, 5, 10, 30)
                            )
                            for horizon in horizons:
                                render_mini_bar_chart(
                                    values=[
                                        None if series is None else series[horizon]
                                        for series in scenario_series
                                    ],
                                    labels=horizon_labels,
                                    title=f"след {horizon} г.",
                                    value_size=22,
                                    title_size="1.6rem",
                                    height=210,
                                    colors=_SCENARIO_BAR_COLORS,
                                )

                        else:
                            show_expense_heading(
                                "Колко ще сте платили общо",
                                sentence_country,
                                sentence_category,
                            )
                            show_all_periods = st.checkbox(
                                "Всички години",
                                key="analysis_002_show_all_periods",
                            )
                            total_periods = (
                                range(1, 31)
                                if show_all_periods
                                else (1, 2, 5, 10, 30)
                            )
                            total_pairs = [
                                (scenario, level)
                                for scenario, levels in scenario_levels.items()
                                for level in levels
                            ]
                            total_paths = [
                                projected_values_for(
                                    monthly_value,
                                    statistic_values[
                                        scenario_statistics[pair]
                                    ],
                                )
                                for pair in total_pairs
                            ]
                            total_labels = [
                                level for _scenario, level in total_pairs
                            ]
                            for period in total_periods:
                                render_mini_bar_chart(
                                    values=[
                                        None
                                        if path is None
                                        else total_period_amounts(
                                            period, path, annual_value
                                        )[0]
                                        for path in total_paths
                                    ],
                                    labels=total_labels,
                                    title=f"за {period} г.",
                                    value_size=22,
                                    title_size="1.6rem",
                                    height=210,
                                    colors=_SCENARIO_BAR_COLORS,
                                )

            st.divider()
            show_sources = st.checkbox(
                "💡 Източници и методика",
                key="show_sources_method",
            )
            if show_sources:
                render_history(filtered_df, percentage_values, highlighted_statistics, coicop_labels, selected_coicop, country_dropdown_labels, selected_country)
                render_description(description_df, selected_coicop, highlighted_hierarchy)
