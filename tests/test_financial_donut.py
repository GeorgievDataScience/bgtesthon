"""Accent shares for the financial donut, including a negative change."""

from idea.streamlit_donut import _ROSE, _TEAL, donut_accent, financial_donuts_page


def test_the_change_ring_is_thicker_than_the_base():
    page = financial_donuts_page([(1, 2000, 13)])
    assert 'stroke="#64748B" stroke-width="24"' in page
    assert 'stroke="#00BFA5" stroke-width="34.8"' in page
    assert page.count('r="125"') == 2


def test_positive_change_is_a_teal_share_of_the_total():
    color, _text, share = donut_accent(2000, 13, 2013)
    assert color == _TEAL
    assert share == 13 / 2013


def test_zero_change_keeps_an_empty_accent():
    _color, _text, share = donut_accent(2000, 0, 2000)
    assert share == 0


def test_negative_change_is_a_rose_share_of_the_base():
    color, _text, share = donut_accent(2000, -13, 1987)
    assert color == _ROSE
    assert share == 13 / 2000


def test_negative_change_larger_than_the_base_fills_the_ring():
    color, _text, share = donut_accent(2000, -2500, -500)
    assert color == _ROSE
    assert share == 1


def test_six_periods_share_one_svg():
    page = financial_donuts_page([
        (0, 2000, 0),
        (1, 2000, 13),
        (2, 2000, 26),
        (5, 2000, 65),
        (10, 2000, 132),
        (30, 2000, -422),
    ])
    assert page.count("<svg ") == 1
    assert page.count("<circle ") == 12
    assert 'viewBox="0 0 599 902"' in page
    assert 'cx="148"' in page and 'cx="451"' in page
    assert page.count('stroke="#00BFA5"') == 5
    assert page.count('stroke="#E11D48"') == 1
    assert "-💵422" in page


def test_all_years_stay_in_one_svg():
    periods = [(year, 2000, year) for year in range(31)]
    page = financial_donuts_page(periods)
    assert page.count("<svg ") == 1
    assert page.count("<circle ") == 62
    assert 'viewBox="0 0 599 4838"' in page
    assert "Текущата година" in page
    assert "След 3 г." in page
    assert "След 30 г." in page


def test_eight_scenarios_fit_on_one_row():
    headings = [
        "Много ниско",
        "Ниско",
        "Типично",
        "Средно",
        "Високо",
        "Много високо",
        "Минимум",
        "Максимум",
    ]
    page = financial_donuts_page(
        [(1, 2000, amount) for amount in (-19, 9, 77, 99, 131, 273, -160, 432)],
        columns=8,
        headings=headings,
        subheading="след 1 г.",
    )
    assert page.count("<svg ") == 1
    assert page.count("<circle ") == 16
    assert 'viewBox="0 0 1472 328"' in page
    assert page.count(">натрупаната<") == 8
    assert page.count(">промяна е<") == 8
    assert "Много високо" in page


def test_eight_scenarios_use_two_rows_of_four():
    headings = [
        "Много ниско",
        "Ниско",
        "Типично",
        "Средно",
        "Високо",
        "Много високо",
        "Минимум",
        "Максимум",
    ]
    page = financial_donuts_page(
        [(1, 2000, amount) for amount in (-19, 9, 77, 99, 131, 273, -160, 432)],
        columns=4,
        headings=headings,
        subheading="след 1 г.",
    )
    assert page.count("<svg ") == 1
    assert page.count("<circle ") == 16
    assert 'viewBox="0 0 1182 590"' in page
    assert "Много ниско" in page
    assert "Много високо" in page
    assert page.count("след 1 г.") == 8
    assert "След 1 г." not in page
    assert page.count('stroke="#E11D48"') == 2
    assert page.count('stroke="#00BFA5"') == 6


def test_total_periods_use_the_paid_heading():
    page = financial_donuts_page([(1, 12000, 0), (30, 360000, 42000)], kind="total")
    assert page.count("<svg ") == 1
    assert "За 1 година" in page
    assert "За 30 години" in page
    assert "ще сте платили" in page
    assert "След 1 г." not in page
