from pathlib import Path
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data/data_hicp.parquet"
DESCRIPTION_DATA_PATH = ROOT / "data/coicop18_names_en_bg_description.parquet"
SPENDING_RANGES_PATH = ROOT / "data/spending_ranges.csv"

DESCRIPTION_COLUMNS = [
    "coicop18",
    "printed page",
    "pdf page",
    "описание / обхват (BG)",
    "включва (BG)",
    "включва също (BG)",
    "изключва (BG)",
]

@st.cache_data(show_spinner="Зареждане на данните...")
def load_data() -> pd.DataFrame:
    """Load the Parquet dataset once and preserve its stored dtypes."""
    return pd.read_parquet(DATA_PATH)


@st.cache_data(show_spinner=False)
def load_description_data() -> pd.DataFrame:
    """Load only the description fields used by the application."""
    table = pq.read_table(
        DESCRIPTION_DATA_PATH,
        columns=DESCRIPTION_COLUMNS,
    )
    normalized_columns = [
        column.cast(pa.string())
        if pa.types.is_large_string(column.type)
        else column
        for column in table.columns
    ]
    normalized_table = pa.Table.from_arrays(
        normalized_columns,
        names=table.column_names,
    )
    return normalized_table.to_pandas(ignore_metadata=True)


@st.cache_data(show_spinner=False)
def load_spending_ranges() -> pd.DataFrame:
    ranges_df = pd.read_csv(SPENDING_RANGES_PATH, sep=";")
    ranges_df["from"] = pd.to_numeric(
        ranges_df["from"],
        errors="coerce",
    )
    ranges_df["to"] = pd.to_numeric(
        ranges_df["to"],
        errors="coerce",
    )
    return ranges_df


def spending_range_row(
    amount: float,
    ranges_df: pd.DataFrame,
) -> pd.Series | None:
    for _, row in ranges_df.iterrows():
        low = row["from"]
        high = row["to"]
        if pd.isna(low) or amount < low:
            continue
        if pd.isna(high) or amount <= high:
            return row
    return None


def format_amount(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def annual_percentage_for_statistic(
    percentage_values: pd.Series,
    statistic: str,
) -> float:
    if statistic == "Минимум":
        return float(percentage_values.min())
    if statistic == "П10":
        return float(percentage_values.quantile(0.10))
    if statistic == "П25":
        return float(percentage_values.quantile(0.25))
    if statistic == "Медиана":
        return float(percentage_values.median())
    if statistic == "Средно":
        return float(percentage_values.mean())
    if statistic == "П75":
        return float(percentage_values.quantile(0.75))
    if statistic == "П90":
        return float(percentage_values.quantile(0.90))
    return float(percentage_values.max())


