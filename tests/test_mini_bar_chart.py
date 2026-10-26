"""Scale and markup checks for the shared mini bar chart."""
import math
import re
from base64 import b64decode

from analyses.analysis_001.calculations import build_projection_tables
from shared.mini_bar_chart import (
    build_mini_bar_chart_html,
    chart_fractions,
    hybrid_scale,
)

SPREAD = [0, 1, 100, 1000, 10000]


def _svg(html):
    start = html.index("base64,") + len("base64,")
    end = html.index('"', start)
    return b64decode(html[start:end]).decode("utf-8")


def test_hybrid_scale_matches_the_continuous_formula():
    assert hybrid_scale(40, 100) == 40
    assert hybrid_scale(100, 100) == 100
    assert hybrid_scale(1000, 100) == 100 * (1 + math.log(10))
    assert hybrid_scale(10000, 100) == 100 * (1 + math.log(100))


def test_auto_stays_linear_for_moderate_ratios_and_hybrid_for_large_ones():
    moderate, moderate_mode = chart_fractions([1, 50], scale="auto", auto_ratio=100)
    wide, wide_mode = chart_fractions(SPREAD, scale="auto", auto_ratio=100)
    assert moderate_mode == "linear"
    assert moderate == [1 / 50, 1]
    assert wide_mode == "hybrid"
    assert wide_mode != "log"


def test_spread_heights_follow_hybrid_scale_and_keep_real_labels():
    fractions, mode = chart_fractions(SPREAD, scale="hybrid")
    transformed = [hybrid_scale(value, 100) for value in SPREAD]
    assert mode == "hybrid"
    assert fractions[0] == 0
    assert fractions[-1] == 1
    assert fractions == [value / transformed[-1] for value in transformed]
    html = build_mini_bar_chart_html(SPREAD, ["0", "1", "100", "1 хил.", "10 хил."], scale="auto")
    svg = _svg(html)
    assert "10 000" in svg
    assert "Хибридна скала" not in html
    assert f"{transformed[-1]:.2f}" not in svg


def test_equal_nonzero_values_share_full_height_and_zeros_have_none():
    assert chart_fractions([4, 4, 4, 4], scale="linear")[0] == [1, 1, 1, 1]
    assert chart_fractions([0, 0, 0], scale="linear")[0] == [0, 0, 0]


def test_log_scale_uses_log1p_and_is_labeled():
    fractions, mode = chart_fractions([0, 1, 100], scale="log")
    assert mode == "log"
    assert fractions[0] == 0
    assert fractions[1] == math.log1p(1) / math.log1p(100)
    assert fractions[2] == 1
    assert "Логаритмична скала" in build_mini_bar_chart_html(
        [0, 1, 100], ["а", "б", "в"], scale="log"
    )


def test_each_value_sits_above_its_own_bar():
    svg = _svg(build_mini_bar_chart_html([10, 40, 100], ["а", "б", "в"], scale="linear"))
    positions = [
        float(y)
        for y in re.findall(r'class="num"[^>]*y="([\d.]+)"', svg)
    ]
    assert positions[0] > positions[1] > positions[2]


def test_linear_chart_has_no_scale_note():
    html = build_mini_bar_chart_html([1, 2, 3, 4, 5], ["а", "б", "в", "г", "д"])
    assert "скала" not in html


def test_negatives_share_the_axis_with_positives_and_missing_values_stay_blank():
    fractions, mode = chart_fractions([-10, None, 0, 40], scale="linear")
    assert mode == "linear"
    assert fractions[0] == -10 / 50
    assert fractions[1] is None
    assert fractions[2] == 0
    assert fractions[3] == 40 / 50
    svg = _svg(build_mini_bar_chart_html(
        [-10, None, 0, 40], ["а", "б", "в", "г"], theme="dark"
    ))
    assert svg.count("<path ") == 2
    assert ">—<" in svg or ">—</text>" in svg
    assert 'class="theme-dark"' in svg
    assert ".s0{fill:#dcfce7}" in svg
    assert svg.rindex(".s3{fill:") > svg.index(".s0{fill:#dcfce7}")


def test_long_labels_are_shortened_and_six_projection_amounts_are_real():
    svg = _svg(build_mini_bar_chart_html(
        [1, 2],
        ["много дълъг етикет", "б"],
    ))
    assert "много дълъг…" in svg
    result = build_projection_tables(12000, 1.04)
    years = [0, 1, 2, 5, 10, 30]
    values = [result.monthly_rounded[year] - result.monthly_rounded[0] for year in years]
    labels = ["сега" if year == 0 else f"{year} г." for year in years]
    svg = _svg(build_mini_bar_chart_html(values, labels, theme="light"))
    assert svg.count("<text ") == 12
    assert "сега" in svg and "30 г." in svg
    assert f"{values[5]:,}".replace(",", " ") in svg
    assert ".s0{fill:#86efac}" in svg
    assert ".s5{fill:#166534}" in svg
    titled = _svg(build_mini_bar_chart_html(
        [1, 2],
        ["сега", "след 30 г."],
    ))
    assert "след 30 г." in titled


def test_scenario_bars_keep_a_color_for_each_pair():
    colors = (
        ("#86efac", "#bbf7d0"),
        ("#16a34a", "#4ade80"),
        ("#94a3b8", "#e2e8f0"),
        ("#475569", "#94a3b8"),
        ("#fdba74", "#fed7aa"),
        ("#ea580c", "#fb923c"),
        ("#38bdf8", "#7dd3fc"),
        ("#e11d48", "#fb7185"),
    )
    svg = _svg(build_mini_bar_chart_html(
        [1, 2, 3, 4, 5, 6, 7, 8],
        ["а", "б", "в", "г", "д", "е", "ж", "з"],
        colors=colors,
    ))
    assert ".s0{fill:#86efac}" in svg
    assert ".s1{fill:#16a34a}" in svg
    assert ".s6{fill:#38bdf8}" in svg
    assert ".s7{fill:#e11d48}" in svg
    assert "svg.theme-dark .s0{fill:#bbf7d0}" in svg
    assert "svg.theme-dark .s7{fill:#fb7185}" in svg


def test_horizon_charts_can_use_larger_money_and_title():
    html = build_mini_bar_chart_html(
        [1981, 2432],
        ["Много ниско", "Максимум"],
        title="след 1 г.",
        value_size=22,
        title_size="1.6rem",
    )
    assert "font-size:1.6rem" in html
    assert 'font-size="22"' in _svg(html)
    plain = _svg(build_mini_bar_chart_html([1981], ["сега"]))
    assert 'font-size="15"' in plain
