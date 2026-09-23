No substantive findings.

I reviewed the plan against the diff and the implementation matches the approved scope: `run_pytest` runs pytest once, retries only on `rc > 128`, preserves ordinary failure behavior, and the added fixture cases cover the requested paths.

I attempted to run `bash tests/test-scripts.sh`, but this review sandbox is read-only and the suite failed immediately creating temp fixture directories, so I could not use that as verification.

Codex verdict: APPROVE
