view-prompt-printf-fix`.

Changed:
- [scripts/codex-review.sh](/Users/cboyfly/Documents/repos/adaptive-compute-worktrees/codex-review-prompt-printf-fix/scripts/codex-review.sh): fixed the four severity bullets to use `printf '%s\n' ...`, and wrapped `git fetch origin` with `timeout`/`gtimeout` when available via `WORKTREE_FETCH_TIMEOUT`.
- [scripts/worktree.sh](/Users/cboyfly/Documents/repos/adaptive-compute-worktrees/codex-review-prompt-printf-fix/scripts/worktree.sh): applied the same bounded best-effort fetch behavior.
- [tests/test-scripts.sh](/Users/cboyfly/Documents/repos/adaptive-compute-worktrees/codex-review-prompt-printf-fix/tests/test-scripts.sh): removed the source-grep taxonomy check and added rendered-prompt assertions for `- CRITICAL:`, `- HIGH:`, `- MEDIUM:`, and `- LOW:` using `grep -Fq --`.

Verification:
- `grep -n "printf '- " scripts/codex-review.sh` returns no matches.
- New rendered-prompt taxonomy test passes after the fix.
- Temporarily reverting one bullet to `printf '- ...'` made `FAIL: codex-review rendered prompt includes severity taxonomy`, then I restored it.
- `bash -n` and `git diff --check` passed.
- `bash scripts/gate.sh` did not pass because `pytest -q` segfaults during pytest startup in `_pytest/capture.py`, before repo tests run. `python -m pytest -q` segfaults the same way. Shellcheck and the shell smoke path reached the new test successfully, but the nested gate assertion also fails because of that pytest crash.

Working tree is clean.
