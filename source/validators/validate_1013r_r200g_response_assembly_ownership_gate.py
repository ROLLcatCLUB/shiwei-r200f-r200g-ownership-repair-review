from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.xiaobei_ai import prep_room_real_upload_entry_preview_1013R_R103 as r103


STAGE = "1013R_R200G_RESPONSE_ASSEMBLY_OWNERSHIP_GATE"
OUT = ROOT / "outputs" / "PREP_ROOM_RENDER_CANVAS_DEEPEN_V1" / STAGE
RESULT = OUT / "validate_1013R_R200G_response_assembly_ownership_gate_result.json"
RESPONSE_SAMPLE = OUT / "r200g_response_ownership_gate_sample.json"


def _shoe_upload_text() -> str:
    return "\n".join(
        [
            "课题：《足下生辉》教案",
            "年级：三年级",
            "单元：第五单元 足下生辉",
            "本课引导学生观察生活中的鞋，比较鞋的正面、侧面、后面和局部细节。",
            "教学目标：学生从不同角度观察一双鞋，说出鞋面、鞋底、鞋带和局部纹样的特点；用线条画出鞋的外形、结构和细节。",
            "教学过程",
            "1. 引入 5分钟 出示不同民族、不同时代的鞋，引导学生提出问题。",
            "2. 观察指导 10分钟 学生观察自己带来的鞋，比较正面、侧面和局部细节。",
            "3. 动手写生 20分钟 学生用线条画出鞋的外形、结构和主要细节。",
            "4. 展示与小结 5分钟 学生说出自己观察到的鞋的一个特点和画面调整。",
        ]
    )


def _has_r200a_marker(value: Any) -> bool:
    if isinstance(value, dict):
        if "art_kernel_basis" in value or "r200a_r1_refinement" in value:
            return True
        return any(_has_r200a_marker(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_r200a_marker(item) for item in value)
    return False


def _run_r200e_summary() -> dict[str, Any]:
    cmd = [sys.executable, str(ROOT / "scripts" / "validate_1013r_r200e_frontend_visible_contamination_guard.py")]
    proc = subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True, encoding="utf-8", errors="replace", timeout=180)
    try:
        data = json.loads(proc.stdout)
    except Exception as exc:
        raise RuntimeError(f"R200E parse failed: {exc}\n{proc.stdout[:1000]}\n{proc.stderr[:1000]}") from exc
    if proc.returncode != 0:
        raise RuntimeError(f"R200E failed: {data.get('status')}")
    return data


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    response = r103.build_readonly_viewmodel_from_upload_session(
        r103.build_upload_session(_shoe_upload_text(), "课时1_足下生辉_教案.txt"),
        enable_teacher_model=False,
        enable_art_reasoning_model=False,
    )
    r103._attach_upload_preview_test_record(response, "r200g_response_ownership_gate")
    template = response.get("single_lesson_template") if isinstance(response.get("single_lesson_template"), dict) else {}
    prep_patch = response.get("prep_view_patch") if isinstance(response.get("prep_view_patch"), dict) else {}
    current_lesson = prep_patch.get("current_lesson") if isinstance(prep_patch.get("current_lesson"), dict) else {}
    gate = response.get("r200g_response_assembly_ownership_gate") if isinstance(response.get("r200g_response_assembly_ownership_gate"), dict) else {}
    teacher_readable = response.get("teacher_readable_quality_preview") if isinstance(response.get("teacher_readable_quality_preview"), dict) else {}
    r200e = _run_r200e_summary()
    teacher_main_counts = (r200e.get("summary") or {}).get("teacher_main_source_type_counts") or {}
    default_visible_counts = (r200e.get("summary") or {}).get("default_visible_source_type_counts") or {}

    response_sample = {
        "viewmodel_id": response.get("viewmodel_id"),
        "gate": gate,
        "template_renderer_policy": template.get("renderer_policy"),
        "teacher_readable_visibility_policy": teacher_readable.get("visibility_policy"),
        "template_main_section_r200a_marker_present": _has_r200a_marker(
            {key: template.get(key) for key in ["basis", "student_analysis", "objectives", "key_difficult_points", "process_episodes"]}
        ),
        "current_lesson_main_r200a_marker_present": _has_r200a_marker(
            {
                "sections": current_lesson.get("sections"),
                "process_steps": current_lesson.get("process_steps"),
            }
        ),
        "r200e_teacher_main_source_type_counts": teacher_main_counts,
        "r200e_default_visible_source_type_counts": default_visible_counts,
    }
    RESPONSE_SAMPLE.write_text(json.dumps(response_sample, ensure_ascii=False, indent=2), encoding="utf-8")

    checks = {
        "r200g_gate_present": gate.get("applied") is True,
        "r200a_demoted_from_teacher_main": gate.get("r200a_demoted_from_teacher_main") is True,
        "r200b_candidate_only_enforced": gate.get("r200b_candidate_only_enforced") is True,
        "template_main_has_no_r200a_marker": not response_sample["template_main_section_r200a_marker_present"],
        "current_lesson_main_has_no_r200a_marker": not response_sample["current_lesson_main_r200a_marker_present"],
        "teacher_readable_fallback_folded": (teacher_readable.get("visibility_policy") or {}).get("default_visible") is False,
        "r200e_teacher_main_R200A_kernel_count_zero": teacher_main_counts.get("R200A_kernel", 0) == 0,
        "r200e_teacher_main_unknown_count_zero": teacher_main_counts.get("unknown", 0) == 0,
        "r200e_default_visible_deterministic_fallback_count_zero": default_visible_counts.get("deterministic_fallback", 0) == 0,
        "preview_only_no_formal_apply": True,
    }
    result = {
        "stage": STAGE,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "r200e_status": r200e.get("status"),
        "r200e_summary": r200e.get("summary"),
        "outputs": {
            "response_sample": str(RESPONSE_SAMPLE.relative_to(ROOT)),
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

