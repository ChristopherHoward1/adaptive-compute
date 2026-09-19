"""Difficulty strata from the frozen-set plug-in delta."""

from __future__ import annotations


def classify_delta(delta: float, margin: float, rho: float = 0.1) -> str:
    if margin <= 0.0:
        msg = "margin must be positive"
        raise ValueError(msg)
    if rho <= 0.0:
        msg = "rho must be positive"
        raise ValueError(msg)

    abs_delta = abs(delta)
    if abs(abs_delta - margin) < rho * margin:
        return "boundary"
    if abs_delta < margin:
        return "equivalent"
    if abs_delta >= 4.0 * margin:
        return "easy"
    return "moderate"
