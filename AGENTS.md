# Agent Operating Notes

## Dependency Update Safety

Dependabot branches (for example `dependabot/pip/*`) are machine-generated convenience branches, not approval signals.

This repository has a known compatibility risk with dependency churn around `pymedphys` and related imaging/medical stack packages. Because upstream movement can outpace `pymedphys` compatibility, agents must treat dependency updates as high-risk changes.

### Hard rules for agents

- Do not auto-merge dependency update PRs or branches.
- Do not assume a green lockfile update is safe.
- Require explicit maintainer approval before merging dependency updates.
- For dependency PRs, run and report relevant tests before proposing merge.
- If `pymedphys` is added/updated/removed, require extra caution and manual review.

When in doubt, prefer deferring dependency bumps over introducing a potential clinical/imaging workflow regression.

---

## Clinical Decision Boundary

This application is used in a **radiation oncology research context** — specifically
the pipeline from clinical DICOM data to radiomics research output. Changes that
affect what data is produced, accepted, or rejected must be approved by the clinical
lead before implementation.

### Hard rules for agents

- Do not implement behaviour changes that affect clinical output without a recorded
  clinical decision. Write a proposal in `docs/proposals/` and wait for approval.
- Do not treat a technically safe fix as automatically clinically appropriate.
  "Safe from a software point of view" and "safe from a clinical point of view"
  are not the same thing.
- Do not add error messages, blocks, or fallbacks that silently alter what data
  reaches the research pipeline without clinical sign-off.

### DICOM standard context

- DICOM datasets in this application reflect real-world clinical data, not idealised
  test data. Required objects under the standard (e.g. RTSS, RTDOSE) may be absent
  for valid clinical reasons.
- Do not assume a missing DICOM object is an error. It may be the normal state for
  a given patient at a given point in their treatment pathway.
- Any code that gates functionality on the presence of a DICOM object (e.g. RTSS)
  must have a recorded clinical rationale for that gate.

### Known open decisions

- **PyRadiomics export with no RTSS present** — crashes silently (KeyError: 'rtss').
  Proposal written at `docs/proposals/pyradiomics_missing_rtss.md`.
  Awaiting clinical lead approval before any code change is made.

---

## Known Dependency Warnings

These warnings appear at runtime but originate in third-party packages, not in the
OnkoDICOM source. Do not suppress them. Do not attempt to fix them in this codebase.
The fix belongs upstream. Monitor each dependency for a release that resolves it.

### `dicompyler-core` — pydicom pixel_data_handlers deprecation

```
WARNING - The 'pydicom.pixel_data_handlers' module will be removed in v4.0,
please use 'from pydicom.pixels.utils import pixel_dtype' instead
```

- **Source:** `dicompylercore/dicomparser.py` line 16 imports `pixel_dtype` from
  `pydicom.pixel_data_handlers.util` (old path).
- **Root cause:** pydicom 3.x moved this to `pydicom.pixels.utils`. `dicompyler-core`
  has not yet been updated to use the new path.
- **Call chain:** OnkoDICOM → `dicompylercore` DVH calculations → `dicomparser.py`
- **Action:** None required in OnkoDICOM. Watch `dicompyler-core` upstream for a fix.
  Do not suppress this warning.
