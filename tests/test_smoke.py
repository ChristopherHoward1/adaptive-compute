"""Smoke test: the package imports so the Python gate has something real to run."""

import adaptive_compute


def test_package_imports() -> None:
    assert adaptive_compute.__version__
