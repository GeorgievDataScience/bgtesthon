from pathlib import Path

import pandas as pd

from calculations import (
    annual_inflation_calc,
    rent_growth_df,
    rent_growth_simple_df,
    total_spending_simple_df,
    summary_stats,
)

DATA_PATH = Path("data") / "clean_data.csv"



def load_data() -> pd.DataFrame:
    return pd.read_csv(DATA_PATH)


def get_growth_rate_for_stat(selected_stat_key: str) -> float:
    df = load_data()
    annual = annual_inflation_calc(df)
    return summary_stats(annual, selected_stat_key)



def build_projection_data(
    selected_stat_key: str,
    indicator_label: str,
    rent_value: float,
) -> dict:
    growth_rate = get_growth_rate_for_stat(selected_stat_key)
    result_df = rent_growth_df(30, rent_value, growth_rate)

    summary_df = rent_growth_simple_df(result_df)
    total_spending_df = total_spending_simple_df(result_df)

    return {
        "rent_value": rent_value,
        "growth_rate": growth_rate,
        "indicator_label": indicator_label,
        "summary_df": summary_df,
        "total_spending_df": total_spending_df,
        "chart_df": result_df[
            ["Година", "Месечен наем", "Годишен наем", "Общо платено"]
        ],
    }
