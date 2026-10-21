"""Extract HICP category statistics for one country.

Usage:
    python country_hicp/extract.py Австрия
    python country_hicp/extract.py AT
"""

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "data_hicp.parquet"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"

COLUMNS = [
    "Категория",
    "Наименование",
    "П10",
    "П25",
    "П75",
    "П90",
    "Минимум",
    "Максимум",
    "Средно",
    "Медиана",
    "Години",
]


def load_hicp() -> pd.DataFrame:
    return pd.read_parquet(
        DATA_PATH,
        columns=[
            "geo",
            "country",
            "country_bg",
            "coicop18",
            "coicop_names_bg",
            "year",
            "percentage_change_inx",
        ],
    )


def find_country(df: pd.DataFrame, query: str) -> pd.Series:
    needle = query.casefold().strip()
    countries = (
        df.groupby(["geo", "country", "country_bg"], observed=True)
        .size()
        .reset_index()[["geo", "country", "country_bg"]]
    )
    for column in ("geo", "country", "country_bg"):
        match = countries[
            countries[column].astype(str).str.casefold() == needle
        ]
        if not match.empty:
            return match.iloc[0]
    names = ", ".join(countries["country_bg"].sort_values())
    raise SystemExit(
        f"Няма държава „{query}“. Налични са: {names}"
    )


def year_span(years: pd.Series) -> str:
    if years.empty:
        return "Няма"
    return f"{int(years.min())}–{int(years.max())}"


def statistic_row(group: pd.DataFrame) -> dict:
    values = group["percentage_change_inx"].dropna()
    observed_years = group.loc[
        group["percentage_change_inx"].notna(),
        "year",
    ]
    if values.empty:
        stats = {
            name: pd.NA
            for name in (
                "П10", "П25", "П75", "П90",
                "Минимум", "Максимум", "Средно", "Медиана",
            )
        }
    else:
        stats = {
            "П10": round(float(values.quantile(0.10)), 2),
            "П25": round(float(values.quantile(0.25)), 2),
            "П75": round(float(values.quantile(0.75)), 2),
            "П90": round(float(values.quantile(0.90)), 2),
            "Минимум": round(float(values.min()), 2),
            "Максимум": round(float(values.max()), 2),
            "Средно": round(float(values.mean()), 2),
            "Медиана": round(float(values.median()), 2),
        }
    return {
        "Категория": group["coicop18"].iloc[0],
        "Наименование": group["coicop_names_bg"].iloc[0],
        **stats,
        "Години": year_span(observed_years),
    }


def extract_country(query: str) -> Path:
    df = load_hicp()
    country = find_country(df, query)
    country_df = df[df["geo"] == country["geo"]]
    rows = [
        statistic_row(group)
        for _, group in country_df.groupby("coicop18", sort=True)
    ]
    result = pd.DataFrame(rows, columns=COLUMNS)
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / f"{country['country_bg']}.csv"
    result.to_csv(
        output_path,
        sep=";",
        decimal=",",
        index=False,
        encoding="utf-8-sig",
    )
    print(
        f"{country['country_bg']}: {len(result)} категории, файл {output_path}"
    )
    return output_path


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(
            "Подай една държава, например: "
            "python country_hicp/extract.py Австрия"
        )
    extract_country(sys.argv[1])
