import pandas as pd


def annual_inflation_calc(df: pd.DataFrame) -> pd.DataFrame:
    """
    Изчислява годишна средна стойност на индекс и годишна инфлация (YoY).
    Очаква входен DataFrame с колони: Year, Value.
    """
    annual_df = (
        df.groupby("Year")["Value"]
        .mean()
        .reset_index()
        .sort_values("Year")
        .rename(columns={"Value": "Annual_Average"})
    )

    annual_df["Inflation_%"] = annual_df["Annual_Average"].pct_change()
    return annual_df



def summary_stats(df: pd.DataFrame, stat_name: str | None = None):
    """
    Ако stat_name е None -> връща всички статистики като DataFrame.
    Ако stat_name е подаден -> връща една стойност (float).
    """
    stats = {
        "min": df["Inflation_%"].min(),
        "p10": df["Inflation_%"].quantile(0.10),
        "p25": df["Inflation_%"].quantile(0.25),
        "median": df["Inflation_%"].median(),
        "mean": df["Inflation_%"].mean(),
        "p75": df["Inflation_%"].quantile(0.75),
        "p90": df["Inflation_%"].quantile(0.90),
        "max": df["Inflation_%"].max(),
    }

    if stat_name is None:
        return pd.DataFrame(stats, index=["Inflation_%"])

    if stat_name not in stats:
        raise ValueError(
            f"Невалидна статистика '{stat_name}'. Избери от: {list(stats.keys())}"
        )

    return stats[stat_name]



def rent_growth_df(years: int, monthly_rent: float, growth_rate: float) -> pd.DataFrame:
    """
    Модел:
      MonthlyRent(year) = monthly_rent * (1 + growth_rate) ** year
    """
    year = pd.Series(range(0, years + 1), name="Year")

    monthly = (monthly_rent * (1 + growth_rate) ** year).round(0).astype(int)
    annual = (monthly * 12).round(0).astype(int)
    cumulative = annual.cumsum().astype(int)

    return pd.DataFrame(
        {
            "Year": year,
            "Monthly Rent": monthly,
            "Annual Rent": annual,
            "Total Spending": cumulative,
        }
    )



def rent_growth_simple_df(rent_df: pd.DataFrame) -> pd.DataFrame:
    """
    Създава опростена таблица от rent_growth_df().
    """
    selected_years = [0, 1, 2, 3, 5, 10, 15, 20, 30]

    df = rent_df[rent_df["Year"].isin(selected_years)].copy()

    df["After Years"] = df["Year"].apply(
        lambda x: "Your rent for the current year"
        if x == 0
        else f"Your rent after {x} years"
    )

    return df[["After Years", "Monthly Rent", "Annual Rent"]]


def total_spending_simple_df(rent_df: pd.DataFrame) -> pd.DataFrame:
    """
    Таблица за Total Spending по същите години и описания като Projection.
    """
    # Вариант A (консистентен): "In N years..." означава общо платено за N години.
    # Понеже rent_df["Total Spending"] е cumsum по Year (0..y включително),
    # за хоризонт N взимаме стойността при Year=N-1.
    selected_years = [1, 2, 3, 5, 10, 15, 20, 30]

    rows = []
    for n_years in selected_years:
        total = int(
            rent_df.loc[rent_df["Year"] == (n_years - 1), "Total Spending"].iloc[0]
        )
        label = (
            "In 1 year, you will have spent a total of"
            if n_years == 1
            else f"In {n_years} years, you will have spent a total of"
        )
        rows.append({"Spending Info": label, "Total Spending": total})

    return pd.DataFrame(rows)
