"""Year-one amounts for every Analysis 002 scenario bar."""

from analyses.analysis_002.tables import scenario_overview_svg
from analyses.analysis_002.calculations import (
    build_projection_tables,
    projected_series,
    projected_values_for,
    total_period_amounts,
    year_one_amount,
)


def test_scenario_overview_uses_the_bar_colors():
    rows = [
        ("0,64%", "П10", "🟢 Оптимистичен", "Много ниско", "#86efac"),
        ("21,60%", "Максимум", "🟣 Екстреми", "Максимум", "#e11d48"),
    ]
    svg = scenario_overview_svg(rows)
    assert svg.count("<svg ") == 1
    assert "Промяна" in svg and "Статистика" in svg
    assert "Сценарии" in svg and "Ниво" in svg
    assert "0,64%" in svg and "Максимум" in svg
    assert 'fill="#86efac"' in svg and 'fill="#e11d48"' in svg
    assert 'fill="#1F2937"' in svg
    assert 'fill="#FFFFFF"' in svg


def test_year_one_amount_matches_the_projection():
    tables = build_projection_tables(2000 * 12, 1 + 0.64 / 100)
    assert year_one_amount(2000, 0.64, False) == tables.monthly_rounded[1]
    assert year_one_amount(2000, 0.64, True) == tables.yearly_rounded[1]


def test_later_horizons_match_the_same_projection():
    tables = build_projection_tables(2000 * 12, 1 + 0.64 / 100)
    series = projected_series(2000, 0.64, False)
    assert series is not None
    for year in (2, 5, 10, 30):
        assert series[year] == tables.monthly_rounded[year]


def test_period_totals_use_the_existing_paid_amount():
    tables = build_projection_tables(2000 * 12, 1 + 0.64 / 100)
    values = projected_values_for(2000, 0.64)
    assert values == tables.projected_values
    for period in (1, 2, 5, 10, 30):
        assert (
            total_period_amounts(period, values, 2000 * 12)[0]
            == total_period_amounts(period, tables.projected_values, 24000)[0]
        )


def test_projected_values_are_missing_when_the_rate_cannot_compound():
    assert projected_values_for(2000, -100) is None


def test_year_one_amount_is_missing_when_the_rate_cannot_compound():
    assert year_one_amount(2000, -100, False) is None
