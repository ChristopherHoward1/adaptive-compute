# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and versions use CalVer
(`YYYY.M.MICRO`). Entries below are written only by `scripts/release.sh`.
## [2026.9.5] - 2026-09-22

- Add an offline equivalence-band probe (`eval --equiv-probe`) that measures the
- Confirm-delta: none

## [2026.9.4] - 2026-09-21

- Add a Waudby-Smith–Ramdas betting confidence-sequence band as a selectable adaptive instrument and re-run the §7/§8 gates under both bands over one shared bootstrap stream, testing whether the v0 empirical-Bernstein H1 savings negative survives a tighter anytime-valid instrument.
- Confirm-delta: none

## [2026.9.3] - 2026-09-20

- Add the adaptive Monte-Carlo stopping procedure (anytime-valid
- Confirm-delta: none

## [2026.9.2] - 2026-09-20

- Fixed the Codex review prompt silently dropping its CRITICAL/HIGH/MEDIUM/LOW severity taxonomy (leading-dash `printf`), added a rendered-prompt gate test that catches a re-drop, and bounded the loop's `git fetch origin` against network stalls.
- Confirm-delta: none

## [2026.9.1] - 2026-09-19

- Fix `release.sh tag-after-merge` to tag the commit that set VERSION (by SHA) so merge-commit, squash, and non-ff release-PR merges tag correctly instead of refusing.
- Confirm-delta: none

## [2026.9.0] - 2026-09-19

- Add the fixed-budget reference bootstrap decision procedure and the
- Confirm-delta: none

