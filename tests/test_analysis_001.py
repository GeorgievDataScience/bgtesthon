"""Regression checks for extracted pure calculation helpers."""
from analyses.analysis_001.calculations import breakdown_text, projection_labels_for

def test_breakdown():
    assert breakdown_text(100, 25) == "100 + 💵25"
    assert breakdown_text(100, -25) == "100 - 💵25"

def test_projection_labels():
    assert projection_labels_for("Месечният", [100, 105], [0, 1]) == [
        "Месечният ви разход за текущата година е 💵100.",
        "Месечният ви разход след 1 г. ще бъде 💵105.",
    ]
