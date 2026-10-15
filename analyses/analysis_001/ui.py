from .components.history import render_history
from .components.description import render_description
from html import escape
from .calculations import build_projection_tables, build_totals_table
from .scenarios import scenario_labels, scenario_levels, scenario_statistics
from .tables import build_statistics_table, build_hierarchy_table, highlight_statistics_table
from .charts import prepare_index_data
from math import isfinite
from .components.context import load_context
import pandas as pd
import streamlit as st
from shared.data_loader import (
    DATA_PATH, DESCRIPTION_DATA_PATH, SPENDING_RANGES_PATH,
    load_data, load_description_data, load_spending_ranges,
    spending_range_row, annual_percentage_for_statistic,
)

def show_expense_blocks(title, frame):
    st.subheader(title)
    parts = []
    for index, block in enumerate(frame.iloc[:, 0]):
        heading, *details = block.split("\n")
        if index:
            parts.append("<br>")
        parts.append(f"<strong>{escape(heading)}</strong><br>")
        parts.extend(
            f"&emsp;{escape(line.strip())}<br>"
            for line in details
        )
    st.markdown("".join(parts), unsafe_allow_html=True)


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
    spending_ranges_df = context.spending_ranges_df
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
            "Въведете стойност",
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
                statistic_rows, statistics_df = build_statistics_table(percentage_values)
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

                highlighted_statistics = highlight_statistics_table(statistics_df, selected_statistic)

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
                            yearly_projection = projection.yearly_table
                            monthly_projection = projection.monthly_table

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
                            if (
                                projection_section
                                == "📈 Месечен / годишен разход"
                            ):
                                view_col, years_col = st.columns(
                                    [1, 1],
                                    vertical_alignment="center",
                                )
                                with view_col:
                                    show_yearly = st.checkbox(
                                        "Годишен разход",
                                        key="projection_show_yearly",
                                    )
                                with years_col:
                                    show_all_years = st.checkbox(
                                        "Всички години",
                                        key="projection_show_all_years_check",
                                    )
                                st.caption(
                                    "Изреченията показват как се "
                                    "променя месечният или "
                                    "годишният ви разход във "
                                    "времето според избрания "
                                    "сценарий."
                                )
                                key_years = [0, 1, 2, 5, 10, 30]
                                if show_all_years:
                                    monthly_shown = monthly_projection
                                    yearly_shown = yearly_projection
                                else:
                                    monthly_shown = (
                                        monthly_projection.iloc[key_years]
                                    )
                                    yearly_shown = (
                                        yearly_projection.iloc[key_years]
                                    )
                                shown_projection = (
                                    yearly_shown if show_yearly else monthly_shown
                                )
                                show_expense_blocks(
                                    "Годишният ви разход"
                                    if show_yearly
                                    else "Месечният ви разход",
                                    shown_projection,
                                )

                                comparison_years = [
                                    1, 2, 5, 10, 30,
                                ]
                                comparison_labels = [
                                    f"{year} г."
                                    for year in comparison_years
                                ]
                                st.markdown(
                                    "**Приблизителна стойност на "
                                    "надбавката:**"
                                )
                                selected_comparison = st.segmented_control(
                                    "Приблизителна стойност на надбавката",
                                    options=comparison_labels,
                                    default=comparison_labels[0],
                                    key="projection_comparison_year_v3",
                                    label_visibility="collapsed",
                                )
                                if selected_comparison:
                                    year = comparison_years[
                                        comparison_labels.index(
                                            selected_comparison
                                        )
                                    ]
                                    comparison_rounded = (
                                        yearly_rounded
                                        if show_yearly
                                        else monthly_rounded
                                    )
                                    change_value = (
                                        comparison_rounded[year]
                                        - comparison_rounded[0]
                                    )
                                    matched = spending_range_row(
                                        abs(change_value),
                                        spending_ranges_df,
                                    )
                                    if change_value >= 0:
                                        change_text = f"💵{change_value}"
                                    else:
                                        change_text = (
                                            f"-💵{abs(change_value)}"
                                        )
                                    surcharge_kind = (
                                        "Годишната"
                                        if show_yearly
                                        else "Месечната"
                                    )
                                    surcharge_text = (
                                        f"{surcharge_kind} надбавка "
                                        f"след {year} г. е "
                                        f"{change_text}."
                                    )
                                    if matched is not None:
                                        surcharge_text = (
                                            f"{surcharge_text} "
                                            f"{matched['comparison']}"
                                        )
                                    st.markdown(surcharge_text)

                            else:
                                show_all_total_years = st.checkbox(
                                    "Всички години",
                                    key="totals_show_all_years_check",
                                )
                                if show_all_total_years:
                                    periods = list(range(1, 31))
                                else:
                                    periods = [
                                        1, 2, 5, 10, 30,
                                    ]
                                totals_table = build_totals_table(
                                    periods, projected_values, annual_value
                                )
                                st.caption(
                                    "Изреченията показват общо "
                                    "платеното за периодите. "
                                    "Базата е същият разход без "
                                    "ръст, натрупаната промяна е "
                                    "разликата заради сценария."
                                )
                                show_expense_blocks(
                                    "Общ разход по периоди",
                                    totals_table,
                                )

            show_sources = st.checkbox(
                "Източници и методика",
                key="show_sources_method",
            )
            if show_sources:
                render_history(filtered_df, percentage_values, highlighted_statistics, coicop_labels, selected_coicop, country_dropdown_labels, selected_country)
                render_description(description_df, selected_coicop, highlighted_hierarchy)
