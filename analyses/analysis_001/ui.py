from .components.history import render_history
from .components.description import render_description
from html import escape
from .calculations import build_projection_tables, total_period_amounts
from .scenarios import scenario_labels, scenario_levels, scenario_statistics
from .tables import build_statistics_table, build_hierarchy_table
from shared.scenario_overview import SCENARIO_BAR_COLORS
from .charts import prepare_index_data
from math import isfinite
from .components.context import load_context
import pandas as pd
import streamlit as st
from shared.data_loader import (
    DATA_PATH, DESCRIPTION_DATA_PATH, SPENDING_RANGES_PATH,
    load_data, load_description_data, load_spending_ranges,
    annual_percentage_for_statistic,
)
from shared.mini_bar_chart import render_mini_bar_chart
from idea.streamlit_donut import render_financial_donuts

def category_sentence_label(details) -> str:
    selected_icon = (
        details.class_icon
        if not pd.isna(details.class_icon)
        else details.group_icon
    )
    icon = "" if pd.isna(selected_icon) else f"{selected_icon} "
    return f"{icon}{details.coicop_names_bg}"


def show_expense_heading(
    lead,
    country_label,
    coicop_label,
    scenario_label,
    level,
    percent_text,
):
    st.markdown(
        "<div class='expense-context'>"
        f"<strong>{escape(lead)}</strong> "
        f"в {escape(country_label)} "
        f"за {escape(coicop_label)} "
        f"при {escape(level.lower())} ниво на "
        f"{escape(scenario_label)} сценарий "
        f"от <strong>{escape(percent_text)} %</strong> на година"
        "</div>",
        unsafe_allow_html=True,
    )


COICOP_GUIDE_URL = (
    "https://unstats.un.org/unsd/classifications/"
    "unsdclassifications/COICOP_2018_pre_copy_edit_publication.pdf"
)

def render():
    st.caption(
        "🌍 Изберете държава, 🛒 категория от ХИПЦ и 🎯 сценарий, "
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

        selected_scenario = st.radio(
            "Изберете сценарий",
            options=list(scenario_labels),
            format_func=scenario_labels.__getitem__,
            horizontal=True,
        )

        selected_scenario_level = st.radio(
            "Изберете ниво на сценария",
            options=scenario_levels[selected_scenario],
            horizontal=True,
        )

        selected_statistic = scenario_statistics[
            (selected_scenario, selected_scenario_level)
        ]
        preview_percentages = df.loc[
            (df["country"] == selected_country)
            & (df["coicop18"] == selected_coicop),
            "percentage_change_inx",
        ].dropna()
        if preview_percentages.empty:
            st.caption("Няма процент за тази комбинация.")
        else:
            preview_percentage = annual_percentage_for_statistic(
                preview_percentages,
                selected_statistic,
            )
            preview_percentage_text = (
                f"{preview_percentage:.2f}".replace(".", ",")
            )
            st.caption(
                "Годишна промяна: "
                f"{preview_percentage_text}%"
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
            "scenario": selected_scenario,
            "scenario_level": selected_scenario_level,
            "entered_value": entered_value,
        }

    shown = st.session_state.get("shown_selection")
    if st.session_state.get("results_visible") and shown:
        selected_country = shown["country"]
        selected_coicop = shown["coicop"]
        selected_scenario = shown["scenario"]
        selected_scenario_level = shown["scenario_level"]
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
                statistic_rows, _ = build_statistics_table(percentage_values)
                selected_statistic = scenario_statistics[
                    (selected_scenario, selected_scenario_level)
                ]
                statistic_values = {
                    statistic: value
                    for value, statistic, _, _ in statistic_rows
                }
                selected_percentage = statistic_values[
                    selected_statistic
                ]
                overview_rows = []
                for (scenario, level), (light, _dark) in zip(
                    (
                        (scenario, level)
                        for scenario, levels in scenario_levels.items()
                        for level in levels
                    ),
                    SCENARIO_BAR_COLORS,
                ):
                    statistic = scenario_statistics[(scenario, level)]
                    change = statistic_values[statistic]
                    overview_rows.append((
                        f"{change:.2f}%".replace(".", ","),
                        statistic,
                        scenario_labels[scenario],
                        level,
                        light,
                    ))

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
                        annual_factor = 1 + selected_percentage / 100

                        if annual_factor <= 0:
                            st.error(
                                "Избраният процент не позволява "
                                "смислено натрупване."
                            )
                        else:
                            projection = build_projection_tables(annual_value, annual_factor)
                            projected_values = projection.projected_values
                            yearly_rounded = projection.yearly_rounded
                            monthly_rounded = projection.monthly_rounded

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
                            percent_text = (
                                f"{selected_percentage:.2f}"
                                .replace(".", ",")
                                .rstrip("0")
                                .rstrip(",")
                            )
                            sentence_country = country_dropdown_labels[
                                selected_country
                            ]
                            sentence_category = category_sentence_label(
                                selected_details
                            )
                            sentence_scenario = scenario_labels[
                                selected_scenario
                            ]
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
                                show_all_years = bool(
                                    st.session_state.get(
                                        "projection_show_all_years_check",
                                        False,
                                    )
                                )
                                expense_kind = (
                                    "Годишният"
                                    if show_yearly
                                    else "Месечният"
                                )
                                show_expense_heading(
                                    f"{expense_kind} ви разход",
                                    sentence_country,
                                    sentence_category,
                                    sentence_scenario,
                                    selected_scenario_level,
                                    percent_text,
                                )
                                view_col, years_col = st.columns(
                                    [1, 1],
                                    vertical_alignment="center",
                                )
                                with view_col:
                                    st.checkbox(
                                        "Годишен разход",
                                        key="projection_show_yearly",
                                    )
                                with years_col:
                                    st.checkbox(
                                        "Всички години",
                                        key="projection_show_all_years_check",
                                    )
                                key_years = [0, 1, 2, 5, 10, 30]
                                comparison_rounded = (
                                    yearly_rounded
                                    if show_yearly
                                    else monthly_rounded
                                )
                                base_amount = comparison_rounded[0]
                                donut_years = list(range(31)) if show_all_years else key_years
                                render_mini_bar_chart(
                                    values=[
                                        comparison_rounded[year]
                                        for year in key_years
                                    ],
                                    labels=[
                                        "сега" if year == 0 else f"след {year} г."
                                        for year in key_years
                                    ],
                                )
                                render_financial_donuts([
                                    (
                                        shown_year,
                                        base_amount,
                                        comparison_rounded[shown_year] - base_amount,
                                    )
                                    for shown_year in donut_years
                                ])

                            else:
                                show_expense_heading(
                                    "Общият ви разход по периоди",
                                    sentence_country,
                                    sentence_category,
                                    sentence_scenario,
                                    selected_scenario_level,
                                    percent_text,
                                )
                                show_all_total_years = st.checkbox(
                                    "Всички години",
                                    key="totals_show_all_years_check",
                                )
                                total_periods = [1, 2, 5, 10, 30]
                                donut_periods = (
                                    list(range(1, 31))
                                    if show_all_total_years
                                    else total_periods
                                )
                                total_amounts = {
                                    period: total_period_amounts(
                                        period, projected_values, annual_value
                                    )
                                    for period in donut_periods
                                }
                                render_mini_bar_chart(
                                    values=[
                                        total_amounts[period][0]
                                        for period in total_periods
                                    ],
                                    labels=[
                                        f"за {period} г."
                                        for period in total_periods
                                    ],
                                )
                                render_financial_donuts(
                                    [
                                        (
                                            period,
                                            total_amounts[period][1],
                                            total_amounts[period][2],
                                        )
                                        for period in donut_periods
                                    ],
                                    kind="total",
                                )

            st.divider()
            show_sources = st.checkbox(
                "💡 Източници и методика",
                key="show_sources_method",
            )
            if show_sources:
                render_history(filtered_df, percentage_values, overview_rows, coicop_labels, selected_coicop, country_dropdown_labels, selected_country)
                render_description(description_df, selected_coicop, highlighted_hierarchy)
