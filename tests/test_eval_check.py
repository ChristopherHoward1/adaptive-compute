import contextlib
import io

from adaptive_compute import benchmark
from adaptive_compute import eval as eval_module
from adaptive_compute.benchmark import AdaptiveParams
from adaptive_compute.reference import DEFAULT_ALPHA


def test_check_fails_with_r1_candidate_grid(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(
        benchmark,
        "DEFAULT_CANDIDATES",
        {
            "eb": (
                AdaptiveParams(b=32, alpha=DEFAULT_ALPHA, b_max=320),
                AdaptiveParams(b=64, alpha=DEFAULT_ALPHA, b_max=320),
            ),
            "betting": (AdaptiveParams(b=64, alpha=DEFAULT_ALPHA, b_max=320),),
        },
    )
    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr):
        assert eval_module._check() == 1
    assert "adaptive (eb) did not certify small_effect equivalence" in stderr.getvalue()


def test_check_fails_with_small_betting_budget(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(
        benchmark,
        "DEFAULT_CANDIDATES",
        {
            **benchmark.DEFAULT_CANDIDATES,
            "betting": (AdaptiveParams(b=64, alpha=DEFAULT_ALPHA, b_max=128),),
        },
    )
    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr):
        assert eval_module._check() == 1
    assert "adaptive (betting) did not certify" in stderr.getvalue()


def test_equivalence_guard_passes_with_default_candidates() -> None:
    assert eval_module._equivalence_guard() == (None, 896)
