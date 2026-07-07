# 1013R R200F/R200G/R200I Ownership Repair Review

This review package is for GPT/human audit of the backend ownership repair after R200E exposed frontend-visible contamination risk.

## Review conclusion wanted

Please audit whether this repair correctly changes the system from:

```text
R200A/R200B can accidentally become teacher-visible main text
```

to:

```text
R200A is diagnostic/candidate only
R200B is candidate only
teacher main text can only come from uploaded source, R114 graph/execution/field projection, or teacher-accepted candidate
fallback/legacy/unknown cannot enter default teacher main view
```

## What changed

- Added `prep_room_source_ownership_policy_1013R_R200F.py`.
- Added response assembly ownership gate in `prep_room_real_upload_entry_preview_1013R_R103.py`.
- The gate snapshots the teacher-main baseline after R114/R97B_P3 and before R200A.
- After R200A/R200B/R200C run, the gate restores teacher-main template/current_lesson text from the baseline.
- R200A output is kept as diagnostic/candidate metadata, not teacher-main text.
- R200B is explicitly candidate-only.
- Deterministic fallback teacher-readable preview is folded by default.
- Low-confidence focus cases are blocked from using R200A main-text influence.
- Restored baseline text is source-stamped so teacher-main text is not `unknown`.

## What this does not solve

This package does not claim the generated teaching quality is now good. It only repairs ownership boundaries.

Still unresolved and intentionally left for later stages:

- richer source-backed lesson reasoning quality
- curriculum-standard deep integration into the reasoning graph
- concrete学情/目标/重难点 derivation from教材/课标/原教案
- real teacher-facing prose quality improvement
- frontend visual polishing
- formal apply/export/runtime save

## Validation status

All validators were rerun locally on 2026-07-07:

```text
R200F_SOURCE_AND_OWNERSHIP_POLICY: PASS
R200E_FRONTEND_VISIBLE_CONTAMINATION_GUARD: PASS
R200G_RESPONSE_ASSEMBLY_OWNERSHIP_GATE: PASS
R200I_FRONTEND_VISIBLE_REGRESSION_HARDENING: PASS
```

Important R200G summary after repair:

```text
teacher_main_R200A_kernel_count_zero = true
teacher_main_unknown_count_zero = true
default_visible_deterministic_fallback_count_zero = true
teacher_main_hit_count = 0
source_policy_violation_count = 0
```

R200E still records denylist terms in `right_rail_patch.must_not_show`, but these are not default-visible and not teacher-main text; this is expected because it is a negative guard list.

## Boundaries

```text
model_called = false
provider_called = false
formal_apply = false
database_written = false
validator_only = true
R21/R36/R95 not touched
```

## Files

- `source/backend_chain/` contains the backend chain and ownership policy source.
- `source/validators/` contains the R200E/F/G/I validators.
- `validation/R200E/` contains frontend-visible contamination ledger/report/result.
- `validation/R200F/` contains ownership policy documents and allowlist.
- `validation/R200G/` contains response assembly gate result and sample response.
- `validation/R200I/` contains historical low-confidence repro and guard result.
- `SOURCE_MANIFEST.txt` contains SHA256 hashes for copied files.

## Suggested audit questions

1. Does the gate really prevent R200A/R200B from controlling teacher-main text?
2. Is restoring the baseline after R97B_P3 and before R200A the right ownership boundary?
3. Is source-stamping restored baseline micro-steps as uploaded/R114/source_gap acceptable, or should more granular statuses be required?
4. Should `source_gap` be allowed in teacher-main view as a visible teacher-confirmation gap, or should it be folded too?
5. What should be the next stage: R200H graph-first main text, or first tighten R114 graph/execution-map quality?
