#!/usr/bin/env bash
# Fixed-budget reference eval command.
set -uo pipefail

cd "$(git rev-parse --show-toplevel)" || exit 1

export PYTHONPATH="${PWD}/src${PYTHONPATH:+:${PYTHONPATH}}"
python -m adaptive_compute.eval --check
