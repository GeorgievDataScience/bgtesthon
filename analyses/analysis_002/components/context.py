"""Load analysis data and build selector choices.

Kept separate from Streamlit widget rendering so new analyses can follow
the same interface boundary without coupling to Analysis 002.
"""
from dataclasses import dataclass
import pandas as pd
import streamlit as st
from shared.data_loader import (
    DATA_PATH, DESCRIPTION_DATA_PATH, SPENDING_RANGES_PATH,
    load_data, load_description_data, load_spending_ranges,
)

REQUIRED_COLUMNS = {
    "geo", "country", "country_bg", "coicop18", "coicop18_names",
    "coicop_names_bg", "division code", "division_name_bg",
    "group code", "group_name_bg", "group_icon", "class code",
    "class_name_bg", "class_icon", "subclass code",
    "subclass_name_bg", "detailed level code", "detailed_level_name_bg",
    "percentage_change_inx", "year", "idx_value",
}

def flag_emoji(geo_code: str) -> str:
    flag_codes = {"EL": "GR", "UK": "GB"}
    country_code = flag_codes.get(geo_code, geo_code)
    return "".join(chr(0x1F1E6 + ord(letter) - ord("A")) for letter in country_code)

@dataclass
class AnalysisContext:
    df: pd.DataFrame
    description_df: pd.DataFrame
    spending_ranges_df: pd.DataFrame
    coicop_details: pd.DataFrame
    countries: list
    country_dropdown_labels: dict
    coicop_values: list
    coicop_labels: dict

def load_context() -> AnalysisContext:
    try:
        df = load_data()
    except FileNotFoundError:
        st.error(f"Файлът с данни не е намерен: `{DATA_PATH}`")
        st.stop()
    except Exception as exc:
        st.error(f"Данните не могат да бъдат заредени: {exc}")
        st.stop()

    missing_columns = REQUIRED_COLUMNS.difference(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        st.error(f"Във файла липсват необходимите колони: {missing}")
        st.stop()

    try:
        description_df = load_description_data()
    except FileNotFoundError:
        st.error(
            "Файлът с описания не е намерен: "
            f"`{DESCRIPTION_DATA_PATH}`"
        )
        st.stop()
    except Exception as exc:
        st.error(f"Описанията не могат да бъдат заредени: {exc}")
        st.stop()

    try:
        spending_ranges_df = load_spending_ranges()
    except FileNotFoundError:
        st.error(
            "Файлът с диапазони не е намерен: "
            f"`{SPENDING_RANGES_PATH}`"
        )
        st.stop()
    except Exception as exc:
        st.error(f"Диапазоните не могат да бъдат заредени: {exc}")
        st.stop()

    country_details = df.groupby(
        "country",
        observed=True,
        sort=False,
    )[["country_bg", "geo"]].first()
    country_labels = country_details["country_bg"].to_dict()
    country_dropdown_labels = {
        country: f"{flag_emoji(row.geo)} {row.country_bg}"
        for country, row in country_details.iterrows()
    }
    countries = sorted(
        country_details.index.tolist(),
        key=country_labels.__getitem__,
    )
    coicop_details = df.groupby(
        "coicop18",
        observed=True,
        sort=False,
    )[
        [
            "coicop_names_bg",
            "division code",
            "division_name_bg",
            "group code",
            "group_name_bg",
            "group_icon",
            "class code",
            "class_name_bg",
            "class_icon",
            "subclass code",
            "subclass_name_bg",
            "detailed level code",
            "detailed_level_name_bg",
        ]
    ].first()
    coicop_values = coicop_details.index.tolist()
    coicop_labels = {}
    for code, row in coicop_details.iterrows():
        selected_icon = (
            row.class_icon
            if not pd.isna(row.class_icon)
            else row.group_icon
        )
        icon = "" if pd.isna(selected_icon) else f"{selected_icon} "
        coicop_labels[code] = f"{icon}{code} — {row.coicop_names_bg}"

    if not countries or not coicop_values:
        st.warning("Няма налични стойности за филтриране.")
        st.stop()
    return AnalysisContext(
        df=df, description_df=description_df,
        spending_ranges_df=spending_ranges_df,
        coicop_details=coicop_details, countries=countries,
        country_dropdown_labels=country_dropdown_labels,
        coicop_values=coicop_values, coicop_labels=coicop_labels,
    )
