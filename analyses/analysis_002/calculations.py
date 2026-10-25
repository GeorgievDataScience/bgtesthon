"""Pure projection presentation helpers for Analysis 002."""

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


def expense_block(
    year: int,
    amount: int,
    base_value: int,
    change_value: int,
) -> str:
    money = format_amount(amount)
    if year == 0:
        heading = "Текущата година"
        when = f"е 💵{money}"
    else:
        heading = f"След {year} г."
        when = f"ще бъде 💵{money}"
    if change_value >= 0:
        change = f"💵{format_amount(change_value)}"
    else:
        change = f"-💵{format_amount(abs(change_value))}"
    return "\n".join([
        heading,
        when,
        f"базата е {format_amount(base_value)}",
        f"натрупаната промяна е {change}",
    ])


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
        "Годишен разход": [
            expense_block(year, value, yearly_base, value - yearly_base)
            for year, value in zip(projection_years, yearly_rounded)
        ],
    })
    monthly_projection = pd.DataFrame({
        "Месечен разход": [
            expense_block(year, value, monthly_base, value - monthly_base)
            for year, value in zip(projection_years, monthly_rounded)
        ],
    })
    return ProjectionTables(projected_values, yearly_rounded, monthly_rounded, yearly_projection, monthly_projection)


def total_period_amounts(period: int, projected_values: list[float], annual_value: float) -> tuple[int, int, int]:
    """Paid total, unchanged base, and accumulated change for one period."""
    total_paid = round(sum(projected_values[:period]))
    period_base = round(annual_value * period)
    return total_paid, period_base, total_paid - period_base


def build_totals_table(periods: list[int], projected_values: list[float], annual_value: float) -> pd.DataFrame:
    blocks = []
    for period in periods:
        total_paid, period_base, period_change = total_period_amounts(
            period, projected_values, annual_value
        )
        heading = "За 1 година" if period == 1 else f"За {period} години"
        if period_change >= 0:
            change = f"💵{format_amount(period_change)}"
        else:
            change = f"-💵{format_amount(abs(period_change))}"
        blocks.append("\n".join([
            heading,
            f"ще сте платили общо 💵{format_amount(total_paid)}",
            f"базата е {format_amount(period_base)}",
            f"натрупаната промяна е {change}",
        ]))
    return pd.DataFrame({"Общ разход по периоди": blocks})
