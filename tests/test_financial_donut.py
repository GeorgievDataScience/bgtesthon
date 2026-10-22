"""Accent shares for the financial donut, including a negative change."""

from idea.streamlit_donut import _ROSE, _TEAL, donut_accent


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
