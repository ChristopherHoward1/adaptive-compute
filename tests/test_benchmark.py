import json

from adaptive_compute.benchmark import run_benchmark, wilson_interval, write_results


def test_wilson_interval_bounds_observed_rate() -> None:
    lower, upper = wilson_interval(1, 10)

    assert 0.0 <= lower <= 0.1 <= upper <= 1.0


def test_small_benchmark_excludes_unresolved_and_writes_artifacts(tmp_path) -> None:
    result = run_benchmark(n_tune=1, n_test=1)
    md_path = tmp_path / "results.md"
    json_path = tmp_path / "results.json"

    write_results(result, md_path=md_path, json_path=json_path)

    assert result.n_test == 1
    assert result.tuned_params.b > 0
    assert any(summary.stratum != "boundary" for summary in result.summaries)
    assert "H1" in md_path.read_text(encoding="utf-8")
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["n_test"] == 1
    assert "false_stop_test_pass" in payload
    assert "savings_pareto_pass" in payload
