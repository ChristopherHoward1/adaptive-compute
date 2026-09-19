#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

if [[ "${TEST_SCRIPTS_RUNNING:-}" == 1 ]]; then
  exit 0
fi

TEST_SCRIPTS_RUNNING=1 bash tests/test-scripts.sh
