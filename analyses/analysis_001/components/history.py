import streamlit as st
from ..charts import prepare_index_data

def render_history(filtered_df, percentage_values, highlighted_statistics, coicop_labels, selected_coicop, country_dropdown_labels, selected_country):
    chart_data, yearly_values = prepare_index_data(filtered_df)
    first_available_year = int(filtered_df["year"].min())
    last_available_year = int(filtered_df["year"].max())

    if not percentage_values.empty:
        with st.container(key="wide_percent_source_card"):
            with st.expander(
                "📊 Как е избран годишният процент",
                expanded=False,
            ):
                st.dataframe(
                    highlighted_statistics,
                    hide_index=True,
                    width="stretch",
                )
                observation_count = len(percentage_values)
                st.caption(
                    "Сценариите ползват Хармонизирания "
                    "индекс на потребителските цени "
                    "(ХИПЦ). "
                    "Оцветеният ред е годишният процент, "
                    "който сценарият ползва за проекцията. "
                    "Тези осем нива са сметнати от "
                    "годишните изменения на "
                    f"**{coicop_labels[selected_coicop]}** "
                    "за "
                    f"**{country_dropdown_labels[selected_country]}**. "
                    "Налични са "
                    f"**{observation_count} годишни "
                    "наблюдения** — от "
                    f"**{first_available_year} г.** до "
                    f"**{last_available_year} г.** "
                    "Медианата разделя наблюденията на "
                    "две равни части, а средното е "
                    "аритметичната им средна стойност. "
                    "П10, П25, П75 и П90 показват "
                    "съответните персентили на "
                    "историческото разпределение. "
                    "Описаните сценарии са "
                    "ориентировъчни исторически нива, "
                    "а не прогнози. "
                    "Движението на индекса е в "
                    "следващата карта."
                )

    with st.container(key="wide_index_chart_card"):
        with st.expander(
            "📉 Как се е движил индексът",
            expanded=False,
        ):
            st.header(coicop_labels[selected_coicop])
            st.line_chart(
                chart_data,
                x="year",
                y="idx_value",
                x_label="Година",
                y_label="Индексна стойност",
                height=400,
            )
            with st.expander(
                "📋 Точните минали стойности",
                expanded=False,
            ):
                st.dataframe(
                    yearly_values,
                    hide_index=True,
                    width="stretch",
                    column_config={
                        "Изменение на цените (%)": (
                            st.column_config.NumberColumn(
                                format="%.2f"
                            )
                        ),
                        "Индекс на цените": (
                            st.column_config.NumberColumn(
                                format="%.2f"
                            )
                        ),
                    },
                )
                st.caption(
                    "Таблицата съдържа всички налични "
                    "години за периода "
                    f"**{first_available_year}–"
                    f"{last_available_year} г.** и показва "
                    "процентното изменение и стойността на "
                    "индекса за всяка година. Възможно е "
                    "периодът да не съдържа наблюдение за "
                    "всяка календарна година."
                )

