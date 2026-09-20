# Shell argument safety — the leading-dash trap

_Load when writing or reviewing a shell script here that builds text from, or
matches, a token that can start with `-`._

A single token that begins with `-` is parsed as an **option** by most tools
long before it is treated as data. This bit the harness silently for the
codebase's whole history (`codex-review-prompt-printf-fix`, v2026.9.2): the Codex
reviewer prompt was assembled with

```sh
printf '- CRITICAL: …\n'      # WRONG: '- CRITICAL:' is read as options
```

Under `bash` this fails with `printf: - : invalid option` (exit 2) and, because
the script runs `set -uo pipefail` (no `-e`), the line is *dropped silently* —
every review ran without its four severity definitions and no check noticed.

## The guards

- **`printf`** — never put data in the format string. Use `printf '%s\n' '- CRITICAL: …'`
  (the idiom already used elsewhere in `codex-review.sh`), or `printf -- '- …\n'`.
- **`grep`** — a pattern starting with `-` needs the `--` end-of-options marker:
  `grep -Fq -- '- CRITICAL:'`. A bare `grep -F '- CRITICAL:'` trips the same trap
  (this nearly recurred in the fix's own acceptance criterion; the plan-reviewer
  caught it). The harness convention is `grep -Fq -- '…'`.
- Generally, pass `--` before any argument that is data and might lead with `-`
  (`rm --`, `git … --`, etc.).

## The check that would have caught it

The old gate test grepped the **source file** (`grep -F "CRITICAL"
scripts/codex-review.sh`) — it matched the literal that produces the line, so it
passed whether or not the line ever reached the output. A test must assert the
**rendered output**, not the source that emits it: here, the `capture-prompt`
canned reviewer writes the fully rendered prompt to a file, and the gate asserts
`grep -Fq -- '- CRITICAL:'` (and HIGH/MEDIUM/LOW) against *that*. A check on the
producer is not a check on the product.
