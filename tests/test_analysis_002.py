"""Year-one amounts for every Analysis 002 scenario bar."""

from analyses.analysis_002.calculations import build_projection_tables, year_one_amount


def test_year_one_amount_matches_the_projection():
    tables = build_projection_tables(2000 * 12, 1 + 0.64 / 100)
    assert year_one_amount(2000, 0.64, False) == tables.monthly_rounded[1]
    assert year_one_amount(2000, 0.64, True) == tables.yearly_rounded[1]


def test_year_one_amount_is_missing_when_the_rate_cannot_compound():
    assert year_one_amount(2000, -100, False) is None
