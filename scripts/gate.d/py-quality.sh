#!/usr/bin/env bash
# Python quality gate hook: formatting + static types.
# gate.sh already runs `ruff check` (lint) and pytest; this adds format-check
# and mypy. Each tool skips gracefully when not installed, matching gate.sh.
set -uo pipefail

cd "$(git rev-parse --show-toplevel)" || exit 1

fail=0

if command -v ruff >/dev/null; then
  echo "▶ ruff format --check ."
  ruff format --check . || fail=1
else
  echo "⊘ skipped: ruff format (not installed)"
fi

if command -v mypy >/dev/null; then
  echo "▶ mypy src"
  mypy src || fail=1
else
  echo "⊘ skipped: mypy (not installed)"
fi

exit "$fail"
