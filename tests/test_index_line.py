"""SVG line for the historical price index."""
import math

from shared.index_line import index_line_html, index_line_svg


def test_index_line_is_one_svg_with_the_years_and_axis_names():
    svg = index_line_svg([1997, 1998, 2025], [48.33, 49.31, 100])
    assert svg is not None
    assert svg.count("<svg ") == 1
    assert svg.count("<path ") == 1
    assert svg.count("<circle ") == 3
    assert "Индексна стойност" in svg
    assert "Година" in svg
    assert ">1997<" in svg and ">2025<" in svg
    assert "#15803d" in svg
    assert "#4ade80" in svg


def test_missing_year_breaks_the_line():
    svg = index_line_svg([2000, 2001, 2003, 2004], [10, 12, 30, 32])
    assert svg.count("<path ") == 1
    assert svg.count("M") == 2
    assert svg.count("<circle ") == 4


def test_invalid_values_are_skipped_and_an_empty_series_draws_nothing():
    svg = index_line_svg([2000, 2001, 2002], [10, math.nan, 14])
    assert svg.count("<circle ") == 2
    assert "<path " not in svg
    assert index_line_svg([2000], [math.nan]) is None
    assert index_line_html([], []) is None


def test_dark_theme_marks_the_svg():
    svg = index_line_svg([2010, 2011], [80, 90], theme="dark")
    assert 'class="theme-dark"' in svg
