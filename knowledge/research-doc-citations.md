# Research-doc citations

Load this when writing or reviewing a doc that cites external literature
(`docs/prior-art.md` and any successor).

The loop cannot verify a citation. The gate is prose-blind, and reviewers have no
web access — so a wrong author, venue, or year passes every check. A `prior-art.md`
therefore carries fabrication and mis-attribution risk that nothing downstream
catches.

Practice:

- Treat every citation as **unverified until checked against a primary source.**
  Mark uncertain details `(verify)` inline, as `docs/prior-art.md` does.
- **Do not quote a citation in any external write-up** (paper, blog, issue,
  external PR description) until its author / title / venue / year are confirmed
  against the primary source. Internal design docs may carry `(verify)`-marked
  citations; external claims may not.
- Prefer citing the canonical published venue over an arXiv preprint year — the
  two frequently differ by a year (this bit us once: Hyperband is JMLR 2018, not
  the 2016/2017 preprint).
- When in doubt about whether a cited method already subsumes our contribution,
  that is a research-question question, not a formatting one — raise it in review.
