"""
Генерира Excel с проекциите от приложението.

Примери:
  python excel_export/export_projection.py 500 Типичен Типично
  python excel_export/export_projection.py --rent 500 --scenario Типичен --level Типично
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from projection_service import build_projection_data

HORIZONS = [1, 2, 3, 5, 10, 15, 20, 30]

SCENARIO_LEVELS = {
    "Оптимистичен": ["Много ниско", "Ниско"],
    "Типичен": ["Типично", "Средно"],
    "Песимистичен": ["Високо", "Много високо"],
    "Екстреми": ["Мин.", "Макс."],
}

STAT_MAP = {
    "Много ниско": "p10",
    "Ниско": "p25",
    "Типично": "median",
    "Средно": "mean",
    "Високо": "p75",
    "Много високо": "p90",
    "Мин.": "min",
    "Макс.": "max",
}


def fmt(n: int | float) -> str:
    return f"{n:,.0f}".replace(",", " ")


def fmt_eur(n: int | float) -> str:
    return f"{fmt(n)} евро"


def normalize_label(text: str) -> str:
    """Маха емоджи/символи отпред, оставя чистото име."""
    cleaned = re.sub(r"^[^\wА-Яа-я]+", "", text.strip(), flags=re.UNICODE)
    return cleaned.strip()


def load_spending_ranges() -> pd.DataFrame:
    path = ROOT / "data" / "spending_ranges.csv"
    last_err: UnicodeDecodeError | None = None
    for enc in ("utf-8-sig", "utf-8", "cp1252", "cp1250", "latin-1"):
        try:
            return pd.read_csv(path, sep=";", encoding=enc)
        except UnicodeDecodeError as e:
            last_err = e
    raise last_err  # pragma: no cover


def _find_spending_range_row(mapping: pd.DataFrame, amount: int) -> pd.Series | None:
    for _, row in mapping.iterrows():
        lo_i = int(row["from"])
        hi = row["to"]
        if pd.isna(hi) or (isinstance(hi, str) and str(hi).strip() == ""):
            if amount >= lo_i:
                return row
            continue
        hi_i = int(float(hi))
        if lo_i <= amount <= hi_i:
            return row
    return None


def spending_range_insight(
    mapping: pd.DataFrame, years: int, spent_abs: int
) -> tuple[str, str]:
    row_match = _find_spending_range_row(mapping, spent_abs)
    if row_match is None:
        return "", ""
    tpl_raw = row_match.get("after_year", "")
    tpl = "" if pd.isna(tpl_raw) else str(tpl_raw).strip()
    after = (
        tpl.replace("{years}", str(years)).replace("{amount}", fmt_eur(spent_abs))
        if tpl
        else ""
    )
    comp_raw = row_match.get("comparison", "")
    if pd.isna(comp_raw):
        return after, ""
    comp = str(comp_raw).strip()
    if not comp or comp.lower() == "nan":
        return after, ""
    return after, comp


def percent_increase_vs_today(growth_rate: float, years: int) -> float:
    return ((1 + growth_rate) ** years - 1) * 100


def rent_after_years_snapshot_df(
    growth_rate: float,
    rent_value: float,
    years: int,
) -> pd.DataFrame:
    monthly_at_horizon = int(round(rent_value * (1 + growth_rate) ** years))
    year_label = f"{years} година" if years == 1 else f"{years} години"
    row_will_be = (
        f"След {year_label} месечният ви наем ще бъде {fmt_eur(monthly_at_horizon)}"
    )
    pct = percent_increase_vs_today(growth_rate, years)
    factor = (1 + growth_rate) ** years - 1
    monthly_delta = int(round(rent_value * factor))
    yearly_delta = monthly_delta * 12
    col = f"След {years} година" if years == 1 else f"След {years} години"
    pct_r2 = round(pct, 2)
    if factor >= 0:
        row_pct = f"С {pct_r2:.2f}% по-висок от текущия".replace(".", ",")
        row_amt = f"С {fmt_eur(monthly_delta)} повече на месец"
        row_year = f"Това са {fmt_eur(yearly_delta)} повече годишно"
    else:
        row_pct = f"{abs(pct_r2):.2f}% по-нисък"
        row_amt = f"С {fmt_eur(abs(monthly_delta))} по-малко на месец"
        row_year = f"Това са {fmt_eur(abs(yearly_delta))} по-малко годишно"

    mapping = load_spending_ranges()
    _, delta_comparison = spending_range_insight(mapping, years, abs(int(monthly_delta)))
    _, yearly_delta_comparison = spending_range_insight(
        mapping, years, abs(int(yearly_delta))
    )
    return pd.DataFrame(
        {
            col: [
                row_will_be,
                row_pct,
                "",
                row_amt,
                delta_comparison,
                "",
                row_year,
                yearly_delta_comparison,
            ]
        }
    )


def total_spending_for_horizon_years(projection_data: dict, n_years: int) -> int:
    chart_df = projection_data["chart_df"]
    return int(
        chart_df.loc[chart_df["Година"] == n_years - 1, "Общо платено"].iloc[0]
    )


def resolve_inputs(rent: int, scenario_raw: str, level_raw: str) -> tuple[str, str, str]:
    scenario = normalize_label(scenario_raw)
    level = normalize_label(level_raw)

    if scenario not in SCENARIO_LEVELS:
        allowed = ", ".join(SCENARIO_LEVELS)
        raise ValueError(f"Невалиден сценарий '{scenario_raw}'. Избери от: {allowed}")

    allowed_levels = SCENARIO_LEVELS[scenario]
    if level not in allowed_levels:
        raise ValueError(
            f"Ниво '{level_raw}' не е валидно за сценарий '{scenario}'. "
            f"Избери от: {', '.join(allowed_levels)}"
        )

    if rent < 0:
        raise ValueError("Наемът трябва да е положителен")
    if rent > 1_000_000:
        raise ValueError("Наемът трябва да е под 1 000 000")

    return scenario, level, STAT_MAP[level]


_TRANSLIT = str.maketrans(
    {
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "g",
        "д": "d",
        "е": "e",
        "ж": "zh",
        "з": "z",
        "и": "i",
        "й": "y",
        "к": "k",
        "л": "l",
        "м": "m",
        "н": "n",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "у": "u",
        "ф": "f",
        "х": "h",
        "ц": "ts",
        "ч": "ch",
        "ш": "sh",
        "щ": "sht",
        "ъ": "a",
        "ь": "",
        "ю": "yu",
        "я": "ya",
        " ": "_",
        ".": "",
    }
)


def slugify(text: str) -> str:
    return text.lower().translate(_TRANSLIT)


def build_excel(
    rent: int,
    scenario: str,
    level: str,
    output_path: Path | None = None,
) -> Path:
    scenario, level, stat_key = resolve_inputs(rent, scenario, level)

    data = build_projection_data(
        selected_stat_key=stat_key,
        indicator_label=level,
        rent_value=rent,
    )
    growth_rate = data["growth_rate"]

    summary_df = pd.DataFrame(
        [
            f"Начален наем: {fmt_eur(data['rent_value'])}",
            f"Сценарий: {scenario}",
            f"Ниво: {level}",
            f"Годишна промяна: {growth_rate:.2%}",
            "Кумулативна промяна",
        ],
        columns=["Обобщение"],
    )

    rent_over_time = data["summary_df"].copy()
    rent_over_time["Месечен наем"] = rent_over_time["Месечен наем"].map(fmt_eur)
    rent_over_time["Годишен наем"] = rent_over_time["Годишен наем"].map(fmt_eur)

    rent_snapshots = pd.concat(
        [
            rent_after_years_snapshot_df(growth_rate, float(rent), y)
            for y in HORIZONS
        ],
        axis=1,
    )

    total_paid = data["total_spending_df"].copy()
    total_paid["Общо платено"] = total_paid["Общо платено"].map(fmt_eur)

    mapping = load_spending_ranges()
    insight_rows = []
    for y in HORIZONS:
        spent = total_spending_for_horizon_years(data, y)
        after_line, comp_line = spending_range_insight(mapping, y, abs(int(spent)))
        insight_rows.append(
            {
                "Години": f"{y}г",
                "Текст": after_line,
                "Сравнение": comp_line,
            }
        )
    total_insights = pd.DataFrame(insight_rows)

    chart_df = data["chart_df"].copy()

    if output_path is None:
        out_dir = ROOT / "output"
        out_dir.mkdir(exist_ok=True)
        filename = (
            f"rent_projection_{rent}_"
            f"{slugify(scenario)}_{slugify(level)}.xlsx"
        )
        output_path = out_dir / filename
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Обобщение", index=False)
        rent_over_time.to_excel(writer, sheet_name="Наем във времето", index=False)
        rent_snapshots.to_excel(writer, sheet_name="Снимки наем 1г-30г", index=False)
        total_paid.to_excel(writer, sheet_name="Общо платен наем", index=False)
        total_insights.to_excel(writer, sheet_name="Сравнения общо платено", index=False)
        chart_df.to_excel(writer, sheet_name="Година по година", index=False)

    return output_path.resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Експорт на проекциите за наем към Excel"
    )
    parser.add_argument("rent", nargs="?", type=int, help="Месечен наем, напр. 500")
    parser.add_argument(
        "scenario",
        nargs="?",
        help="Сценарий: Оптимистичен | Типичен | Песимистичен | Екстреми",
    )
    parser.add_argument(
        "level",
        nargs="?",
        help="Ниво според сценария, напр. Типично",
    )
    parser.add_argument("--rent", dest="rent_opt", type=int)
    parser.add_argument("--scenario", dest="scenario_opt")
    parser.add_argument("--level", dest="level_opt")
    parser.add_argument(
        "-o",
        "--output",
        help="Път до изходния .xlsx (по подразбиране: output/...)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rent = args.rent_opt if args.rent_opt is not None else args.rent
    scenario = args.scenario_opt if args.scenario_opt is not None else args.scenario
    level = args.level_opt if args.level_opt is not None else args.level

    if rent is None or scenario is None or level is None:
        raise SystemExit(
            "Нужни са 3 параметъра: наем, сценарий, ниво.\n"
            "Пример: python excel_export/export_projection.py 500 Типичен Типично"
        )

    path = build_excel(rent=rent, scenario=scenario, level=level, output_path=args.output)
    print(path)


if __name__ == "__main__":
    main()
