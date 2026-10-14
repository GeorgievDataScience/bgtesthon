"""Pure projection presentation helpers for Analysis 001."""

from shared.data_loader import format_amount

def projection_labels_for(
    kind: str,
    rounded_values: list[int],
    projection_years: list[int],
) -> list[str]:
    labels = []
    for year, amount in zip(
        projection_years,
        rounded_values,
    ):
        money = format_amount(amount)
        if year == 0:
            labels.append(
                f"{kind} ви разход за "
                "текущата година е "
                f"💵{money}."
            )
        else:
            labels.append(
                f"{kind} ви разход след "
                f"{year} г. ще бъде "
                f"💵{money}."
            )
    return labels


def change_sentence(
    period_label: str,
    base_value: int,
    change_value: int,
) -> str:
    if change_value >= 0:
        change = f"💵{format_amount(change_value)}"
    else:
        change = f"-💵{format_amount(abs(change_value))}"
    return (
        f"{period_label} базата е {format_amount(base_value)}, "
        f"а натрупаната промяна е {change}."
    )



from dataclasses import dataclass
import pandas as pd

@dataclass
class ProjectionTables:
    projected_values: list[float]
    yearly_rounded: list[int]
    monthly_rounded: list[int]
    yearly_table: pd.DataFrame
    monthly_table: pd.DataFrame


def build_projection_tables(annual_value: float, annual_factor: float) -> ProjectionTables:
    """Preserve the original 0–30 year projection and rounding semantics."""
    projection_years = list(range(31))
    projected_values = [annual_value * (annual_factor ** year) for year in projection_years]
    monthly_values = [value / 12 for value in projected_values]
    yearly_rounded = [round(value) for value in projected_values]
    monthly_rounded = [round(value) for value in monthly_values]
    yearly_base = yearly_rounded[0]
    monthly_base = monthly_rounded[0]
    yearly_projection = pd.DataFrame({
        "Годишен разход": projection_labels_for("Годишният", yearly_rounded, projection_years),
        "База и натрупана промяна": [
            change_sentence(
                "За текущата година" if year == 0 else f"След {year} г.",
                yearly_base,
                value - yearly_base,
            )
            for year, value in zip(projection_years, yearly_rounded)
        ],
    })
    monthly_projection = pd.DataFrame({
        "Месечен разход": projection_labels_for("Месечният", monthly_rounded, projection_years),
        "База и натрупана промяна": [
            change_sentence(
                "За текущата година" if year == 0 else f"След {year} г.",
                monthly_base,
                value - monthly_base,
            )
            for year, value in zip(projection_years, monthly_rounded)
        ],
    })
    return ProjectionTables(projected_values, yearly_rounded, monthly_rounded, yearly_projection, monthly_projection)


def build_totals_table(periods: list[int], projected_values: list[float], annual_value: float) -> pd.DataFrame:
    paid_texts = []
    change_texts = []
    for period in periods:
        total_paid = round(sum(projected_values[:period]))
        period_base = round(annual_value * period)
        period_change = total_paid - period_base
        if period == 1:
            paid_texts.append("За 1 година ще сте платили общо " f"💵{format_amount(total_paid)}.")
        else:
            paid_texts.append(f"За {period} години ще сте платили общо " f"💵{format_amount(total_paid)}.")
        period_label = "За 1 година" if period == 1 else f"За {period} години"
        change_texts.append(change_sentence(period_label, period_base, period_change))
    return pd.DataFrame({"Общ разход по периоди": paid_texts, "База и натрупана промяна": change_texts})
