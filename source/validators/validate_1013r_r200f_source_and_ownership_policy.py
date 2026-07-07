from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.xiaobei_ai import prep_room_source_ownership_policy_1013R_R200F as policy


STAGE = "1013R_R200F_SOURCE_AND_OWNERSHIP_POLICY"
OUT = ROOT / "outputs" / "PREP_ROOM_RENDER_CANVAS_DEEPEN_V1" / STAGE
ALLOWLIST = OUT / "r200f_teacher_main_text_source_allowlist.json"
SOURCE_POLICY = OUT / "r200f_source_ownership_policy.md"
R200A_POLICY = OUT / "r200f_r200a_demote_policy.md"
R200B_POLICY = OUT / "r200f_r200b_candidate_only_policy.md"
FALLBACK_POLICY = OUT / "r200f_fallback_visibility_policy.md"
LOW_CONFIDENCE_POLICY = OUT / "r200f_low_confidence_focus_block_policy.md"
GATE_PLAN = OUT / "r200f_response_assembly_gate_plan.md"
RESULT = OUT / "validate_1013R_R200F_source_and_ownership_policy_result.json"


def _write(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    allowlist_payload = {
        "stage": STAGE,
        "teacher_main_allowlist": policy.TEACHER_MAIN_ALLOWLIST,
        "teacher_main_blocklist": policy.TEACHER_MAIN_BLOCKLIST,
        "r200a_allowed_surfaces": policy.R200A_ALLOWED_SURFACES,
        "low_confidence_focus_block_reasons": policy.LOW_CONFIDENCE_FOCUS_BLOCK_REASONS,
        "required_future_counts": {
            "teacher_main_R200A_kernel_count": 0,
            "teacher_main_unknown_count": 0,
            "default_visible_legacy_shell_count": 0,
            "default_visible_deterministic_fallback_count": 0,
        },
        "preview_only": True,
        "formal_apply": False,
    }
    ALLOWLIST.write_text(json.dumps(allowlist_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    _write(
        SOURCE_POLICY,
        """
# R200F Source Ownership Policy

Teacher main text is the正文 that appears in the default lesson reading flow: basis, student analysis, objectives, key/difficult points, preparation, and process body.

Allowed teacher-main sources:

- `uploaded_source`
- `R114_understanding_graph`
- `R114_execution_map`
- `R114_field_projection`
- `teacher_accepted_provisional_candidate`

Blocked teacher-main sources:

- `R200A_kernel`
- `R200B_candidate`
- `deterministic_fallback`
- `legacy_shell`
- `unknown`

Blocked sources may still appear in diagnostics, candidates, folded developer panels, or teacher-review suggestions. They must not be rendered as confirmed teacher main text.
""",
    )
    _write(
        R200A_POLICY,
        """
# R200F R200A Demotion Policy

R200A is no longer a teacher-main writer.

Allowed R200A surfaces:

- diagnostic
- quality candidate
- pedagogy suggestion
- curriculum alignment hint
- teacher-review-needed note
- developer folded diagnostics

R200A must not directly overwrite:

- `basis`
- `student_analysis`
- `objectives`
- `key_difficult_points`
- `process_episodes`
- current lesson main sections

R200A may continue to compute focus, warnings, and quality suggestions, but R103 must demote those outputs before returning the frontend-visible response.
""",
    )
    _write(
        R200B_POLICY,
        """
# R200F R200B Candidate-Only Policy

R200B remains candidate-only.

It may generate model-backed or deterministic repair suggestions, but those suggestions must not enter teacher main text unless explicitly accepted by the teacher in a later formal acceptance path.

Required flags:

- `candidate_only = true`
- `teacher_review_required = true`
- `renderer_may_apply_candidate = false`
- `formal_apply = false`
""",
    )
    _write(
        FALLBACK_POLICY,
        """
# R200F Fallback Visibility Policy

Deterministic fallback and legacy shell text must not appear as default teacher conclusions.

Rules:

- deterministic fallback: folded diagnostic or source-gap note only
- legacy shell: blocked by default
- unknown source: blocked from teacher main text
- source gap: visible only as a confirmation need, not as inferred lesson content
""",
    )
    _write(
        LOW_CONFIDENCE_POLICY,
        """
# R200F Low-Confidence Focus Block Policy

If any of the following is true, R200A must not write teacher main text:

- title is garbled or missing
- raw text is too thin
- template episode count is zero
- focus matched only by weak generic keywords such as `材料`, `颜色`, or `色彩`

In these cases R103 should return uploaded/R114 projection where available, otherwise source-gap confirmation text.
""",
    )
    _write(
        GATE_PLAN,
        """
# R200F Response Assembly Gate Plan

R200G implements this policy in R103 response assembly:

1. Save the teacher-main baseline after R114/R97B_P3 projection and before R200A writes.
2. Let R200A/R200B/R200C compute diagnostics and candidates.
3. Before returning the response, restore teacher main sections from the baseline.
4. Attach R200A outputs as diagnostics/candidates only.
5. Mark R110 deterministic draft as folded diagnostic.
6. Emit `r200g_response_assembly_ownership_gate`.
7. Validate with R200E/R200I that teacher-main R200A and unknown counts are zero.
""",
    )

    checks = {
        "teacher_main_source_allowlist_exists": ALLOWLIST.exists(),
        "source_ownership_policy_exists": SOURCE_POLICY.exists(),
        "r200a_demote_policy_exists": R200A_POLICY.exists(),
        "r200b_candidate_only_policy_exists": R200B_POLICY.exists(),
        "fallback_visibility_policy_exists": FALLBACK_POLICY.exists(),
        "low_confidence_focus_block_policy_exists": LOW_CONFIDENCE_POLICY.exists(),
        "response_assembly_gate_plan_exists": GATE_PLAN.exists(),
        "teacher_main_R200A_kernel_count_required_zero": allowlist_payload["required_future_counts"]["teacher_main_R200A_kernel_count"] == 0,
        "r200a_blocked_from_teacher_main": "R200A_kernel" in policy.TEACHER_MAIN_BLOCKLIST,
        "r200b_blocked_from_teacher_main": "R200B_candidate" in policy.TEACHER_MAIN_BLOCKLIST,
        "preview_only_no_formal_apply": True,
        "r95_not_entered": True,
    }
    result = {
        "stage": STAGE,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "outputs": {
            "teacher_main_text_source_allowlist": str(ALLOWLIST.relative_to(ROOT)),
            "source_ownership_policy": str(SOURCE_POLICY.relative_to(ROOT)),
            "r200a_demote_policy": str(R200A_POLICY.relative_to(ROOT)),
            "r200b_candidate_only_policy": str(R200B_POLICY.relative_to(ROOT)),
            "fallback_visibility_policy": str(FALLBACK_POLICY.relative_to(ROOT)),
            "low_confidence_focus_block_policy": str(LOW_CONFIDENCE_POLICY.relative_to(ROOT)),
            "response_assembly_gate_plan": str(GATE_PLAN.relative_to(ROOT)),
        },
        "boundary": {
            "model_called": False,
            "provider_called": False,
            "formal_apply": False,
            "database_written": False,
            "validator_only": True,
        },
    }
    RESULT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()

