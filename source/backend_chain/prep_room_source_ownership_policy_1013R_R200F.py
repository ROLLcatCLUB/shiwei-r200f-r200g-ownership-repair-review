from __future__ import annotations

import re
from copy import deepcopy
from typing import Any


STAGE_ID = "1013R_R200F_SOURCE_AND_OWNERSHIP_POLICY"

TEACHER_MAIN_ALLOWLIST = [
    "uploaded_source",
    "R114_understanding_graph",
    "R114_execution_map",
    "R114_field_projection",
    "teacher_accepted_provisional_candidate",
]

TEACHER_MAIN_BLOCKLIST = [
    "R200A_kernel",
    "R200B_candidate",
    "deterministic_fallback",
    "legacy_shell",
    "unknown",
]

R200A_ALLOWED_SURFACES = [
    "diagnostic",
    "quality_candidate",
    "pedagogy_suggestion",
    "curriculum_alignment_hint",
    "teacher_review_needed",
    "developer_folded_diagnostics",
]

LOW_CONFIDENCE_FOCUS_BLOCK_REASONS = [
    "title_garbled_or_missing",
    "raw_text_too_thin",
    "template_episode_count_zero",
    "focus_matched_from_weak_keyword_only",
]


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _items(value: Any) -> list[str]:
    if isinstance(value, list):
        return [_clean(item) for item in value if _clean(item)]
    text = _clean(value)
    return [text] if text else []


def _section_items(section: dict[str, Any]) -> list[str]:
    return _items(section.get("items") or section.get("body"))


def _template_section_body(template: dict[str, Any], section_key: str) -> list[str]:
    sections = template.get(section_key)
    if not isinstance(sections, list) or not sections or not isinstance(sections[0], dict):
        return []
    return _items(sections[0].get("body"))


def _template_episode_count(template: dict[str, Any]) -> int:
    episodes = template.get("process_episodes")
    return len(episodes) if isinstance(episodes, list) else 0


def _main_text_source_status(item: dict[str, Any], fallback: str = "uploaded_source") -> str:
    status = _clean(item.get("source_status") or item.get("provenance") or item.get("classification"))
    if status in {"uploaded_lesson_entry_preview", "uploaded_evidence"}:
        return "uploaded_source"
    if status == "needs_teacher_confirm":
        return "source_gap"
    if status:
        return status
    return fallback


def _stamp_template_main_text_sources(template: dict[str, Any]) -> None:
    template_status = _main_text_source_status(template, "uploaded_source")
    for key in ["basis", "student_analysis", "objectives", "key_difficult_points", "preparation", "assessment_or_homework", "reflection_or_notes"]:
        sections = template.get(key)
        if not isinstance(sections, list):
            continue
        for section in sections:
            if not isinstance(section, dict):
                continue
            section["source_status"] = _main_text_source_status(section, template_status)
    for episode in template.get("process_episodes") or []:
        if not isinstance(episode, dict):
            continue
        episode_status = _main_text_source_status(episode, template_status)
        episode["source_status"] = episode_status
        for micro in episode.get("micro_steps") or []:
            if not isinstance(micro, dict):
                continue
            micro["source_status"] = _main_text_source_status(micro, episode_status)


def _stamp_current_lesson_main_text_sources(current_lesson: dict[str, Any]) -> None:
    for section in current_lesson.get("sections") or []:
        if not isinstance(section, dict):
            continue
        section["source_status"] = _main_text_source_status(section, "uploaded_source")
    for step in current_lesson.get("process_steps") or []:
        if not isinstance(step, dict):
            continue
        step["source_status"] = _main_text_source_status(step, "uploaded_source")


def _looks_garbled(text: str) -> bool:
    cleaned = _clean(text)
    if not cleaned:
        return True
    question_marks = cleaned.count("?") + cleaned.count("？")
    if question_marks >= max(3, len(cleaned) // 3):
        return True
    return "�" in cleaned


def _lesson_focus(kernel: dict[str, Any]) -> dict[str, Any]:
    focus = kernel.get("lesson_focus") if isinstance(kernel.get("lesson_focus"), dict) else {}
    return focus


def _low_confidence_reasons(response: dict[str, Any], baseline: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    template = response.get("single_lesson_template") if isinstance(response.get("single_lesson_template"), dict) else {}
    kernel = response.get("art_lesson_design_kernel_preview") if isinstance(response.get("art_lesson_design_kernel_preview"), dict) else {}
    upload = response.get("upload_session") if isinstance(response.get("upload_session"), dict) else {}
    focus = _lesson_focus(kernel)
    header = template.get("lesson_header") if isinstance(template.get("lesson_header"), dict) else {}
    title = _clean(header.get("lesson_title") or header.get("title") or upload.get("file_name"))
    if _looks_garbled(title):
        reasons.append("title_garbled_or_missing")
    raw_excerpt = _clean(upload.get("raw_excerpt"))
    if len(raw_excerpt) < 80:
        reasons.append("raw_text_too_thin")
    if _template_episode_count(template) == 0:
        reasons.append("template_episode_count_zero")
    matched = focus.get("matched_keywords") if isinstance(focus.get("matched_keywords"), list) else []
    if len([item for item in matched if _clean(item)]) <= 1 and any(_clean(item) in {"材料", "颜色", "色彩"} for item in matched):
        reasons.append("focus_matched_from_weak_keyword_only")
    return list(dict.fromkeys(reasons))


def _collect_r200a_main_candidate_excerpt(response: dict[str, Any]) -> dict[str, Any]:
    template = response.get("single_lesson_template") if isinstance(response.get("single_lesson_template"), dict) else {}
    current_lesson = ((response.get("prep_view_patch") or {}).get("current_lesson") or {}) if isinstance(response.get("prep_view_patch"), dict) else {}
    excerpt = {
        "template_sections": {},
        "current_lesson_sections": {},
        "process_episode_count": _template_episode_count(template),
    }
    for key in ["basis", "student_analysis", "objectives", "key_difficult_points"]:
        body = _template_section_body(template, key)
        if body:
            excerpt["template_sections"][key] = body[:8]
    for section in current_lesson.get("sections") or []:
        if not isinstance(section, dict):
            continue
        section_id = _clean(section.get("id") or section.get("section_id"))
        if section_id in {"basis", "analysis", "goals", "keypoints"}:
            excerpt["current_lesson_sections"][section_id] = _section_items(section)[:8]
    return excerpt


def _restore_template_main_text(template: dict[str, Any], baseline_template: dict[str, Any]) -> None:
    for key in ["basis", "student_analysis", "objectives", "key_difficult_points", "process_episodes"]:
        if key in baseline_template:
            template[key] = deepcopy(baseline_template.get(key))
    template.setdefault("renderer_policy", {})["r200f_teacher_main_allowlist"] = list(TEACHER_MAIN_ALLOWLIST)
    template.setdefault("renderer_policy", {})["r200g_ownership_gate_applied"] = True
    template.setdefault("renderer_policy", {})["r200a_kernel_demoted_from_teacher_main"] = True


def _restore_current_lesson_main_text(current_lesson: dict[str, Any], baseline_current_lesson: dict[str, Any]) -> None:
    if isinstance(baseline_current_lesson.get("sections"), list):
        current_lesson["sections"] = deepcopy(baseline_current_lesson.get("sections"))
    if isinstance(baseline_current_lesson.get("process_steps"), list):
        current_lesson["process_steps"] = deepcopy(baseline_current_lesson.get("process_steps"))
    current_lesson["r200a_kernel_visibility"] = {
        "default_visible": False,
        "allowed_surface": list(R200A_ALLOWED_SURFACES),
        "reason": "R200A is diagnostic/candidate only after R200F ownership policy.",
    }


def apply_response_ownership_gate(response: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    template = response.get("single_lesson_template") if isinstance(response.get("single_lesson_template"), dict) else {}
    prep_patch = response.get("prep_view_patch") if isinstance(response.get("prep_view_patch"), dict) else {}
    current_lesson = prep_patch.get("current_lesson") if isinstance(prep_patch.get("current_lesson"), dict) else {}
    baseline_template = baseline.get("single_lesson_template") if isinstance(baseline.get("single_lesson_template"), dict) else {}
    baseline_current_lesson = baseline.get("current_lesson") if isinstance(baseline.get("current_lesson"), dict) else {}
    r200a_excerpt = _collect_r200a_main_candidate_excerpt(response)
    low_confidence_reasons = _low_confidence_reasons(response, baseline)

    if template and baseline_template:
        _restore_template_main_text(template, baseline_template)
        _stamp_template_main_text_sources(template)
    if current_lesson and baseline_current_lesson:
        _restore_current_lesson_main_text(current_lesson, baseline_current_lesson)
        _stamp_current_lesson_main_text_sources(current_lesson)

    if isinstance(prep_patch, dict):
        prep_patch["single_lesson_template"] = template
    response["single_lesson_template"] = template

    teacher_readable = response.get("teacher_readable_quality_preview")
    if isinstance(teacher_readable, dict):
        teacher_readable["visibility_policy"] = {
            "default_visible": False,
            "allowed_surface": "folded_diagnostic",
            "reason": "R110 deterministic draft is fallback/diagnostic until accepted by teacher.",
        }

    gate = {
        "stage": "1013R_R200G_RESPONSE_ASSEMBLY_OWNERSHIP_GATE",
        "policy_stage": STAGE_ID,
        "applied": True,
        "teacher_main_allowlist": list(TEACHER_MAIN_ALLOWLIST),
        "teacher_main_blocklist": list(TEACHER_MAIN_BLOCKLIST),
        "r200a_demoted_from_teacher_main": True,
        "r200b_candidate_only_enforced": True,
        "deterministic_fallback_default_visible": False,
        "legacy_shell_default_visible": False,
        "low_confidence_focus_block_reasons": low_confidence_reasons,
        "low_confidence_focus_blocked": bool(low_confidence_reasons),
        "demoted_r200a_teacher_main_candidate_excerpt": r200a_excerpt,
        "formal_apply": False,
        "database_written": False,
        "preview_only": True,
    }
    response["r200f_source_ownership_policy"] = {
        "stage": STAGE_ID,
        "teacher_main_allowlist": list(TEACHER_MAIN_ALLOWLIST),
        "teacher_main_blocklist": list(TEACHER_MAIN_BLOCKLIST),
        "r200a_allowed_surfaces": list(R200A_ALLOWED_SURFACES),
        "low_confidence_focus_block_reasons": list(LOW_CONFIDENCE_FOCUS_BLOCK_REASONS),
    }
    response["r200g_response_assembly_ownership_gate"] = gate
    return response
