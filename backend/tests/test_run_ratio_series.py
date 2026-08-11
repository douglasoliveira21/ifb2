from datetime import date

from app.sync.bcb_client import SeriesPoint
from app.sync.run import _ratio_series, _ratio_series_by_state


def test_ratio_series_matches_by_year_and_ignores_zero_denominator() -> None:
    numerator = [
        SeriesPoint(reference_date=date(2023, 1, 1), value=2800.0),
        SeriesPoint(reference_date=date(2024, 1, 1), value=2900.0),
        SeriesPoint(reference_date=date(2025, 1, 1), value=10.0),
    ]
    denominator = [
        SeriesPoint(reference_date=date(2023, 1, 1), value=3500.0),
        SeriesPoint(reference_date=date(2024, 1, 1), value=0.0),
        # 2025 ausente do denominador
    ]

    result = _ratio_series(numerator, denominator)

    assert result == [SeriesPoint(reference_date=date(2023, 1, 1), value=80.0)]


def test_ratio_series_by_state_only_includes_states_present_in_both() -> None:
    numerator = {
        "SP": [SeriesPoint(reference_date=date(2024, 1, 1), value=3499.0)],
        "MA": [SeriesPoint(reference_date=date(2024, 1, 1), value=1800.0)],
    }
    denominator = {
        "SP": [SeriesPoint(reference_date=date(2024, 1, 1), value=4658.0)],
        # MA ausente do denominador
    }

    result = _ratio_series_by_state(numerator, denominator)

    assert list(result.keys()) == ["SP"]
    assert result["SP"] == [SeriesPoint(reference_date=date(2024, 1, 1), value=75.1)]
