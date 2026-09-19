import pytest

from adaptive_compute.metrics import auc, delta


def test_auc_matches_known_rank_fixture() -> None:
    scores = [0.1, 0.4, 0.35, 0.8]
    y = [0, 0, 1, 1]

    assert auc(scores, y) == pytest.approx(0.75, abs=1e-12)


def test_auc_handles_ties_with_midranks() -> None:
    scores = [0.5, 0.5, 0.5, 0.2]
    y = [1, 0, 1, 0]

    assert auc(scores, y) == pytest.approx(0.75, abs=1e-12)


def test_delta_is_score_a_minus_score_b() -> None:
    y = [0, 0, 1, 1]
    scores_a = [0.1, 0.4, 0.35, 0.8]
    scores_b = [0.1, 0.8, 0.35, 0.4]

    assert delta(scores_a, scores_b, y) == pytest.approx(0.25, abs=1e-12)
