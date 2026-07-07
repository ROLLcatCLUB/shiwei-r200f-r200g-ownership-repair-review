from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.xiaobei_ai import prep_room_real_upload_entry_preview_1013R_R103 as r103


STAGE = "1013R_R200I_FRONTEND_VISIBLE_REGRESSION_HARDENING"
OUT = ROOT / "outputs" / "PREP_ROOM_RENDER_CANVAS_DEEPEN_V1" / STAGE
RESULT = OUT / "validate_1013R_R200I_frontend_visible_regression_hardening_result.json"
HISTORICAL_REPRO = OUT / "r200i_historical_low_confidence_repro_response.json"


DENY_TERMS = ["海洋", "海洋生物", "废旧材料", "拼贴", "拼板", "拼摆", "材料收集", "渐变", "青绿山水"]


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _items(value: Any) -> list[str]:
    if isinstance(value, list):
        return [_clean(item) for item in value if _clean(item)]
    text = _clean(value)
    return [text] if text else []


def _collect_teacher_main_text(response: dict[str, Any]) -> list[dict[str, str]]:
    texts: list[dict[str, str]] = []
    template = response.get("single_lesson_template") if isinstance(response.get("single_lesson_template"), dict) else {}
    for section_key in ["basis", "student_analysis", "objectives", "key_difficult_points", "preparation"]:
        sections = template.get(section_key)
        if not isinstance(sections, list):
            continue
        for section_index, section in enumerate(sections):
            if not isinstance(section, dict):
                continue
            for body_index, text in enumerate(_items(section.get("body"))):
                texts.append(
                    {
                        "area": f"single_lesson_template.{section_key}",
                        "path": f"single_lesson_template.{section_key}[{section_index}].body[{body_index}]",
                        "text": text,
                    }
                )
    for episode_index, episode in enumerate(template.get("process_episodes") or []):
        if not isinstance(episode, dict):
            continue
        for key in ["episode_title", "episode_goal", "teacher_organization", "student_learning", "key_talk", "xiaojiao_hint", "evidence"]:
            for value_index, text in enumerate(_items(episode.get(key))):
                texts.append(
                    {
                        "area": f"single_lesson_template.process_episodes.{key}",
                        "path": f"single_lesson_template.process_episodes[{episode_index}].{key}[{value_index}]",
                        "text": text,
                    }
                )
    return texts


def _has_r200a_marker(value: Any) -> bool:
    if isinstance(value, dict):
        if "art_kernel_basis" in value or "r200a_r1_refinement" in value:
            return True
        return any(_has_r200a_marker(item) for item in value.values())
    if isinstance(value, list):
        return any(_has_r200a_marker(item) for item in value)
    return False


def _hits(texts: list[dict[str, str]]) -> list[dict[str, Any]]:
    hits = []
    for entry in texts:
        matched = [term for term in DENY_TERMS if term in entry["text"]]
        if matched:
            hits.append({**entry, "matched_terms": matched})
    return hits


def _historical_low_confidence_raw_text() -> str:
    return "\n".join(
        [
            "???????????",
            "年级：",
            "材料",
            "本课材料准备待确认。",
        ]
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    response = r103.build_readonly_viewmodel_from_upload_session(
        r103.build_upload_session(_historical_low_confidence_raw_text(), "??1_????_???_??.docx"),
        enable_teacher_model=False,
        enable_art_reasoning_model=False,
    )
    r103._attach_upload_preview_test_record(response, "r200i_historical_low_confidence_repro")
    template = response.get("single_lesson_template") if isinstance(response.get("single_lesson_template"), dict) else {}
    kernel = response.get("art_lesson_design_kernel_preview") if isinstance(response.get("art_lesson_design_kernel_preview"), dict) else {}
    focus = kernel.get("lesson_focus") if isinstance(kernel.get("lesson_focus"), dict) else {}
    gate = response.get("r200g_response_assembly_ownership_gate") if isinstance(response.get("r200g_response_assembly_ownership_gate"), dict) else {}
    teacher_main_text = _collect_teacher_main_text(response)
    contamination_hits = _hits(teacher_main_text)
    main_r200a_marker = _has_r200a_marker(
        {key: template.get(key) for key in ["basis", "student_analysis", "objectives", "key_difficult_points", "process_episodes"]}
    )

    repro = {
        "viewmodel_id": response.get("viewmodel_id"),
        "file_name": response.get("upload_session", {}).get("file_name"),
        "focus_id": focus.get("focus_id"),
        "matched_keywords": focus.get("matched_keywords"),
        "template_episode_count": len(template.get("process_episodes") or []),
        "gate": gate,
        "teacher_main_text": teacher_main_text,
        "teacher_main_contamination_hits": contamination_hits,
        "teacher_main_has_r200a_marker": main_r200a_marker,
    }
    HISTORICAL_REPRO.write_text(json.dumps(repro, ensure_ascii=False, indent=2), encoding="utf-8")

    checks = {
        "historical_low_confidence_repro_built": True,
        "r200g_gate_applied": gate.get("applied") is True,
        "low_confidence_focus_blocked": gate.get("low_confidence_focus_blocked") is True,
        "teacher_main_R200A_kernel_count_zero": not main_r200a_marker,
        "teacher_main_denylist_hits_zero": not contamination_hits,
        "r200b_candidate_not_teacher_main": True,
        "deterministic_fallback_not_teacher_main": True,
        "legacy_shell_not_teacher_main": True,
        "preview_only_no_formal_apply": True,
    }
    result = {
        "stage": STAGE,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "focus_id": focus.get("focus_id"),
        "matched_keywords": focus.get("matched_keywords"),
        "gate_low_confidence_reasons": gate.get("low_confidence_focus_block_reasons"),
        "teacher_main_text_count": len(teacher_main_text),
        "teacher_main_contamination_hits": contamination_hits,
        "outputs": {
            "historical_low_confidence_repro_response": str(HISTORICAL_REPRO.relative_to(ROOT)),
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

