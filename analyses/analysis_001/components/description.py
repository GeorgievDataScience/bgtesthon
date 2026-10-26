from html import escape
import pandas as pd
import streamlit as st

from shared.hierarchy_place import render_hierarchy_place

COICOP_GUIDE_URL = (
    "https://unstats.un.org/unsd/classifications/"
    "unsdclassifications/COICOP_2018_pre_copy_edit_publication.pdf"
)

def render_description(description_df, selected_coicop, selected_details):
    description_match = description_df[
        description_df["coicop18"] == selected_coicop
    ]

    with st.container(key="wide_category_card"):
        with st.expander(
            "📘 Какво означава категорията",
            expanded=False,
        ):
            if description_match.empty:
                st.info(
                    "Няма налична структурирана информация "
                    "за избраната категория."
                )
            else:
                category_description = description_match.iloc[0]

                def category_text(column: str) -> str:
                    value = category_description[column]
                    if pd.isna(value) or (
                        isinstance(value, str)
                        and not value.strip()
                    ):
                        return "Няма"
                    return str(value).strip()

                def bullet_list_html(
                    column: str,
                    empty_message: str,
                ) -> str:
                    value = category_text(column)
                    if value == "Няма":
                        return f"<p>{escape(empty_message)}</p>"
                    items = [
                        line.strip().lstrip("-•").strip()
                        for line in value.splitlines()
                        if line.strip()
                    ]
                    return (
                        "<ul>"
                        + "".join(
                            f"<li>{escape(item)}</li>"
                            for item in items
                        )
                        + "</ul>"
                    )

                with st.container(border=True):
                    st.markdown(
                        "#### 🌳 Място в класификацията"
                    )
                    render_hierarchy_place(selected_details, selected_coicop)

                    st.divider()
                    st.markdown("##### 📝 Описание и обхват")
                    description_scope = category_text(
                        "описание / обхват (BG)"
                    )
                    if description_scope != "Няма":
                        st.write(description_scope)

                    includes_list = bullet_list_html(
                        "включва (BG)",
                        "Няма допълнително посочени елементи.",
                    )
                    also_includes_list = bullet_list_html(
                        "включва също (BG)",
                        "Няма допълнително включени елементи.",
                    )
                    excludes_list = bullet_list_html(
                        "изключва (BG)",
                        "Няма посочени изключения.",
                    )

                    includes_html = (
                        "<details>"
                        "<summary><strong>✅ Какво включва"
                        "</strong></summary>"
                        f"{includes_list}"
                        "</details>"
                    )
                    also_includes_html = (
                        "<details>"
                        "<summary><strong>➕ Включва също"
                        "</strong></summary>"
                        f"{also_includes_list}"
                        "</details>"
                    )
                    excludes_html = (
                        "<details>"
                        "<summary><strong>🚫 Какво не включва"
                        "</strong></summary>"
                        f"{excludes_list}"
                        "</details>"
                    )
                    st.markdown(
                        includes_html,
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        also_includes_html,
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        excludes_html,
                        unsafe_allow_html=True,
                    )

                    printed_page = category_text("printed page")
                    pdf_page = category_text("pdf page")
                    source_url = (
                        f"{COICOP_GUIDE_URL}#page={pdf_page}"
                    )
                    source_html = (
                        "<details>"
                        "<summary><strong>📚 Източник и "
                        "страници</strong></summary>"
                        "<p>Ръководство COICOP 2018</p>"
                        f"<p>Печатна страница: "
                        f"{escape(printed_page)} &nbsp;|&nbsp; "
                        f"PDF страница: {escape(pdf_page)}</p>"
                        f'<p><a href="{escape(source_url)}" '
                        'target="_blank">Отвори страница '
                        f"{escape(pdf_page)} в оригинала ↗"
                        "</a></p>"
                        "<p><small>Поясненията на български "
                        "са превод на оригиналния текст."
                        "</small></p>"
                        "</details>"
                    )
                    st.markdown(
                        source_html,
                        unsafe_allow_html=True,
                    )

            about_coicop_html = (
                "<details>"
                "<summary><strong>ℹ️ За класификацията "
                "COICOP 2018</strong></summary>"
                "<p>COICOP 2018 е международна класификация "
                "на ООН, която подрежда стоките и услугите "
                "според потребностите, които удовлетворяват."
                "</p>"
                "<p>В приложението ръководството помага да "
                "разберете какво включва и изключва избраната "
                "категория. То описва класификацията, а не "
                "стойностите на индекса или измененията на "
                "цените.</p>"
                "<p><strong>Оригинално заглавие:</strong><br>"
                "<em>Classification of Individual Consumption "
                "According to Purpose (COICOP) 2018</em></p>"
                "<p><strong>Формат:</strong> PDF, на английски "
                "език</p>"
                f'<p><a href="{escape(COICOP_GUIDE_URL)}" '
                'target="_blank">⬇️ Изтегли ръководството '
                "COICOP 2018 (PDF)</a></p>"
                "<p><small>Източник: Статистически отдел на "
                "ООН (UNSD).</small></p>"
                "</details>"
            )
            st.markdown(
                about_coicop_html,
                unsafe_allow_html=True,
            )
