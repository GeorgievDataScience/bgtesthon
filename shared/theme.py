from base64 import b64encode
from pathlib import Path
import streamlit as st

def apply_theme():

    @st.cache_resource
    def load_flag_font() -> str:
        font_path = Path(__file__).resolve().parents[1] / "static/TwemojiCountryFlags.woff2"
        return b64encode(font_path.read_bytes()).decode("ascii")


    flag_font_css = """
        <style>
        @font-face {
            font-family: "Twemoji Country Flags";
            src: url("data:font/woff2;base64,__FLAG_FONT_DATA__")
                 format("woff2");
            font-display: swap;
            unicode-range: U+1F1E6-1F1FF;
        }

        div[data-baseweb="select"] *,
        div[data-baseweb="popover"] *,
        input[role="combobox"],
        [data-testid="stAlert"] *,
        [role="option"] {
            font-family: "Twemoji Country Flags", "Source Sans Pro", sans-serif !important;
        }

        .st-key-wide_filters {
            width: min(98vw, 1800px);
            position: relative;
            left: 50%;
            transform: translateX(-50%);
        }

        .st-key-wide_history_card,
        .st-key-wide_percent_source_card,
        .st-key-wide_index_chart_card,
        .st-key-wide_category_card {
            width: min(92vw, 1400px);
            position: relative;
            left: 50%;
            transform: translateX(-50%);
        }

        [role="option"] {
            white-space: normal !important;
            height: auto !important;
            min-height: 2.5rem;
        }

        .expense-context {
            font-family: "Twemoji Country Flags", "Segoe UI Emoji", "Source Sans Pro", sans-serif;
            font-size: 1.05rem;
            line-height: 1.55;
            margin: 0.2rem 0 0.9rem 0;
        }
        </style>
        """.replace("__FLAG_FONT_DATA__", load_flag_font())

    st.markdown(
        flag_font_css,
        unsafe_allow_html=True,
    )


