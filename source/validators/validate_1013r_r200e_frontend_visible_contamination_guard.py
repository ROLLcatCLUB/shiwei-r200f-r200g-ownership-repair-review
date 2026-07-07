from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.xiaobei_ai import prep_room_document_text_extractor_1013R_R107A as extractor
from backend.xiaobei_ai import prep_room_real_upload_entry_preview_1013R_R103 as r103


STAGE = "1013R_R200E_FRONTEND_VISIBLE_CONTAMINATION_GUARD"
OUT = ROOT / "outputs" / "PREP_ROOM_RENDER_CANVAS_DEEPEN_V1" / STAGE
RESULT = OUT / "validate_1013R_R200E_frontend_visible_contamination_guard_result.json"
SNAPSHOT = OUT / "frontend_visible_text_snapshot.json"
LEDGER = OUT / "content_source_ledger.json"
DENYLIST = OUT / "active_lesson_denylist.json"
REPORT = OUT / "contamination_hit_report.md"


MAIN_SECTION_KEYS = [
    "basis",
    "student_analysis",
    "objectives",
    "key_difficult_points",
    "preparation",
    "assessment_or_homework",
    "reflection_or_notes",
]

EPISODE_KEYS = [
    "episode_title",
    "episode_goal",
    "teacher_organization",
    "student_learning",
    "key_talk",
    "xiaojiao_hint",
    "evidence",
]

MICRO_KEYS = [
    "title",
    "step_name",
    "teacher_action",
    "student_action",
    "screen_or_materials",
    "scaffolds",
    "evidence",
]

DERIVATION_KEYS = [
    "why_now",
    "transition_to_next",
    "assessment_evidence",
    "pedagogy_role",
    "curriculum_candidate_summary",
]


ACTIVE_LESSON_DENYLIST: dict[str, dict[str, Any]] = {
    "shoe_observation_drawing_expression": {
        "label": "足下生辉",
        "deny_terms": ["海洋", "海洋生物", "废旧材料", "拼贴", "拼板", "拼摆", "渐变", "青绿山水", "石青", "石绿"],
    },
    "theme_observation_expression": {
        "label": "走进海洋世界",
        "deny_terms": ["鞋底", "鞋面", "鞋带", "足下生辉", "青绿山水", "石青", "石绿"],
    },
    "ink_or_traditional_color_exploration": {
        "label": "走进青绿山水",
        "deny_terms": ["鞋底", "鞋面", "鞋带", "海洋生物", "废旧材料", "拼贴", "拼板"],
    },
    "paper_weaving_structure_expression": {
        "label": "穿穿编编",
        "deny_terms": ["足下生辉", "鞋底", "海洋", "海洋生物", "青绿山水", "渐变", "废旧材料"],
    },
    "color_gradation_expression": {
        "label": "渐变的魅力",
        "deny_terms": ["足下生辉", "鞋底", "鞋面", "鞋带", "青绿山水", "海洋生物", "废旧材料"],
    },
    "material_transformation_expression": {
        "label": "变废为宝的艺术",
        "deny_terms": ["足下生辉", "鞋底", "鞋面", "鞋带", "青绿山水", "石青", "石绿"],
    },
}


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _items(value: Any) -> list[str]:
    if isinstance(value, list):
        return [_clean(item) for item in value if _clean(item)]
    text = _clean(value)
    return [text] if text else []


def _docx_text(pattern: str) -> tuple[str, str]:
    matches = sorted((ROOT / "knowledge-base" / "lesson-cases").glob(pattern))
    if not matches:
        raise AssertionError(f"missing lesson sample: {pattern}")
    path = matches[0]
    extracted = extractor.extract_document_text(str(path), original_filename=path.name, enable_model_ocr=False)
    if not extracted.get("ok"):
        raise AssertionError(f"document extraction failed: {path.name} {extracted.get('status')}")
    return str(extracted.get("text") or ""), path.name


def _shoe_upload_text() -> tuple[str, str]:
    return (
        "\n".join(
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
        ),
        "课时1_足下生辉_教案.txt",
    )


SAMPLES: list[dict[str, Any]] = [
    {
        "case_id": "shoe_observation_user_repro",
        "source": _shoe_upload_text,
        "expected_focus": "shoe_observation_drawing_expression",
        "reason": "User-reported contamination repro: 足下生辉 must not show ocean/material-transformation terms.",
    },
    {
        "case_id": "color_gradation",
        "source": lambda: _docx_text("*fd1b5bdf60*.docx"),
        "expected_focus": "color_gradation_expression",
    },
    {
        "case_id": "qinglv_landscape",
        "source": lambda: _docx_text("*08f3e01f0b*.docx"),
        "expected_focus": "ink_or_traditional_color_exploration",
    },
    {
        "case_id": "material_transformation",
        "source": lambda: _docx_text("*67d6ab622f*.docx"),
        "expected_focus": "material_transformation_expression",
    },
    {
        "case_id": "ocean_theme",
        "source": lambda: _docx_text("*eeabeca815*.docx"),
        "expected_focus": "theme_observation_expression",
    },
    {
        "case_id": "weaving",
        "source": lambda: _docx_text("*39f6102808*.docx"),
        "expected_focus": "paper_weaving_structure_expression",
    },
]


def _build_response(raw_text: str, file_name: str) -> dict[str, Any]:
    session = r103.build_upload_session(raw_text, file_name)
    response = r103.build_readonly_viewmodel_from_upload_session(
        session,
        enable_teacher_model=False,
        enable_art_reasoning_model=False,
    )
    r103._attach_upload_preview_test_record(response, "r200e_frontend_visible_guard")
    return response


def _classify_source(parent: dict[str, Any], path: str, area: str) -> str:
    source_status = str(parent.get("source_status") or parent.get("classification") or "")
    if area.startswith("r200b_candidate"):
        return "R200B_candidate"
    if area.startswith("curriculum_candidate"):
        return "R200C_curriculum_candidate"
    if "art_lesson_design_kernel_preview" in path or parent.get("art_kernel_basis") or parent.get("r200a_r1_refinement"):
        return "R200A_kernel"
    if "lesson_derivation_spine" in path:
        return "R97B_P3_derivation_spine"
    if path.startswith("single_lesson_template.process_episodes") and "derivation_basis" in path:
        if parent.get("art_kernel_basis"):
            return "R200A_kernel"
        return "R97B_P3_derivation_spine"
    if "import_graph_field_projection_preview" in path or "r114c" in source_status:
        return "R114_field_projection"
    if "import_teacher_execution_map_preview" in path:
        return "R114_execution_map"
    if "import_understanding_v2_graph_preview" in path or parent.get("graph_path") or parent.get("claim_id"):
        return "R114_graph"
    if "import_lesson_understanding_preview" in path:
        return "R112_understanding"
    if "teacher_readable_quality_preview" in path:
        return "deterministic_fallback"
    if path.startswith("runtime_progress_events"):
        return "runtime_event"
    if path.startswith("prep_view_patch.current_lesson.process_steps"):
        if parent.get("source_status") == "uploaded_lesson_entry_preview" or parent.get("source_episode_id"):
            return "uploaded_source"
        return "R103_frontend_process_projection"
    if path.startswith("prep_view_patch.current_lesson.sections"):
        if parent.get("art_kernel_basis") or parent.get("r200a_r1_refinement"):
            return "R200A_kernel"
        if "r114c" in source_status:
            return "R114_field_projection"
        if source_status:
            return source_status
        return "R103_frontend_section_projection"
    if "right_rail_patch" in path:
        return "right_rail_patch"
    if "xiaojiao_context_patch" in path:
        return "xiaojiao_context"
    if source_status in {"uploaded_source", "uploaded_evidence", "uploaded_lesson_entry_preview"}:
        return "uploaded_source"
    if source_status == "provisional_generated_candidate":
        return "provisional_candidate"
    if source_status == "source_gap":
        return "source_gap"
    if "fallback" in source_status:
        return "deterministic_fallback"
    if "legacy" in source_status:
        return "legacy_shell"
    if source_status:
        return source_status
    return "unknown"


def _entry(
    *,
    case_id: str,
    focus_id: str,
    area: str,
    path: str,
    text: str,
    parent: dict[str, Any] | None = None,
    default_visible: bool = True,
    teacher_main_text: bool = False,
) -> dict[str, Any] | None:
    cleaned = _clean(text)
    if not cleaned:
        return None
    parent = parent or {}
    return {
        "case_id": case_id,
        "focus_id": focus_id,
        "area": area,
        "path": path,
        "text": cleaned,
        "default_visible": bool(default_visible),
        "teacher_main_text": bool(teacher_main_text),
        "content_source_type": _classify_source(parent, path, area),
        "raw_source_status": parent.get("source_status"),
        "classification": parent.get("classification"),
        "teacher_review_required": bool(parent.get("teacher_review_required")),
        "candidate_only": bool(parent.get("candidate_only")),
    }


def _add_entry(entries: list[dict[str, Any]], **kwargs: Any) -> None:
    item = _entry(**kwargs)
    if item:
        entries.append(item)


def _collect_section_entries(case_id: str, focus_id: str, template: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for section_key in MAIN_SECTION_KEYS:
        sections = template.get(section_key)
        if not isinstance(sections, list):
            continue
        for section_index, section in enumerate(sections):
            if not isinstance(section, dict):
                continue
            for body_index, text in enumerate(_items(section.get("body"))):
                _add_entry(
                    entries,
                    case_id=case_id,
                    focus_id=focus_id,
                    area=f"main_template.{section_key}",
                    path=f"single_lesson_template.{section_key}[{section_index}].body[{body_index}]",
                    text=text,
                    parent=section,
                    default_visible=True,
                    teacher_main_text=True,
                )
            for capsule_index, capsule in enumerate(section.get("source_capsules") or []):
                if not isinstance(capsule, dict):
                    continue
                _add_entry(
                    entries,
                    case_id=case_id,
                    focus_id=focus_id,
                    area=f"folded_source_capsule.{section_key}",
                    path=f"single_lesson_template.{section_key}[{section_index}].source_capsules[{capsule_index}].source_excerpt",
                    text=capsule.get("source_excerpt"),
                    parent=capsule,
                    default_visible=False,
                    teacher_main_text=False,
                )
    return entries


def _collect_episode_entries(case_id: str, focus_id: str, template: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    episodes = template.get("process_episodes")
    if not isinstance(episodes, list):
        return entries
    for episode_index, episode in enumerate(episodes):
        if not isinstance(episode, dict):
            continue
        for key in EPISODE_KEYS:
            for value_index, text in enumerate(_items(episode.get(key))):
                _add_entry(
                    entries,
                    case_id=case_id,
                    focus_id=focus_id,
                    area=f"main_template.process_episodes.{key}",
                    path=f"single_lesson_template.process_episodes[{episode_index}].{key}[{value_index}]",
                    text=text,
                    parent=episode,
                    default_visible=True,
                    teacher_main_text=True,
                )
        derivation = episode.get("derivation_basis") if isinstance(episode.get("derivation_basis"), dict) else {}
        for key in DERIVATION_KEYS:
            for value_index, text in enumerate(_items(derivation.get(key))):
                _add_entry(
                    entries,
                    case_id=case_id,
                    focus_id=focus_id,
                    area=f"main_template.process_episodes.derivation_basis.{key}",
                    path=f"single_lesson_template.process_episodes[{episode_index}].derivation_basis.{key}[{value_index}]",
                    text=text,
                parent=episode,
                    default_visible=True,
                    teacher_main_text=True,
                )
        for micro_index, micro in enumerate(episode.get("micro_steps") or []):
            if not isinstance(micro, dict):
                continue
            for key in MICRO_KEYS:
                for value_index, text in enumerate(_items(micro.get(key))):
                    _add_entry(
                        entries,
                        case_id=case_id,
                        focus_id=focus_id,
                        area=f"main_template.micro_steps.{key}",
                        path=f"single_lesson_template.process_episodes[{episode_index}].micro_steps[{micro_index}].{key}[{value_index}]",
                        text=text,
                        parent=micro,
                        default_visible=True,
                        teacher_main_text=True,
                    )
    return entries


def _walk_strings(
    *,
    case_id: str,
    focus_id: str,
    area: str,
    path: str,
    value: Any,
    parent: dict[str, Any] | None = None,
    default_visible: bool,
    teacher_main_text: bool = False,
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    if isinstance(value, str):
        _add_entry(
            entries,
            case_id=case_id,
            focus_id=focus_id,
            area=area,
            path=path,
            text=value,
            parent=parent or {},
            default_visible=default_visible,
            teacher_main_text=teacher_main_text,
        )
    elif isinstance(value, list):
        for index, item in enumerate(value):
            entries.extend(
                _walk_strings(
                    case_id=case_id,
                    focus_id=focus_id,
                    area=area,
                    path=f"{path}[{index}]",
                    value=item,
                    parent=item if isinstance(item, dict) else parent,
                    default_visible=default_visible,
                    teacher_main_text=teacher_main_text,
                )
            )
    elif isinstance(value, dict):
        current_parent = value
        for key, item in value.items():
            entries.extend(
                _walk_strings(
                    case_id=case_id,
                    focus_id=focus_id,
                    area=area,
                    path=f"{path}.{key}",
                    value=item,
                    parent=current_parent,
                    default_visible=default_visible,
                    teacher_main_text=teacher_main_text,
                )
            )
    return entries


def _collect_current_lesson_section_entries(case_id: str, focus_id: str, current_lesson: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    sections = current_lesson.get("sections")
    if not isinstance(sections, list):
        return entries
    for section_index, section in enumerate(sections):
        if not isinstance(section, dict):
            continue
        section_id = _clean(section.get("id") or section.get("section_id") or f"section_{section_index}")
        for item_index, text in enumerate(_items(section.get("items"))):
            _add_entry(
                entries,
                case_id=case_id,
                focus_id=focus_id,
                area=f"frontend_current_lesson.sections.{section_id}",
                path=f"prep_view_patch.current_lesson.sections[{section_index}].items[{item_index}]",
                text=text,
                parent=section,
                default_visible=True,
                teacher_main_text=True,
            )
    return entries


def _collect_current_lesson_process_entries(case_id: str, focus_id: str, current_lesson: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    steps = current_lesson.get("process_steps")
    if not isinstance(steps, list):
        return entries
    visible_keys = [
        "title",
        "goal",
        "teacher_action",
        "student_task",
        "evidence",
        "source_content",
        "original_source_evidence",
        "screen_hint",
        "teacher_talk_suggestions",
        "source_gap_note",
    ]
    for step_index, step in enumerate(steps):
        if not isinstance(step, dict):
            continue
        for key in visible_keys:
            for value_index, text in enumerate(_items(step.get(key))):
                _add_entry(
                    entries,
                    case_id=case_id,
                    focus_id=focus_id,
                    area=f"frontend_current_lesson.process_steps.{key}",
                    path=f"prep_view_patch.current_lesson.process_steps[{step_index}].{key}[{value_index}]",
                    text=text,
                    parent=step,
                    default_visible=True,
                    teacher_main_text=True,
                )
    return entries


def _collect_runtime_progress_entries(case_id: str, focus_id: str, response: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    events = response.get("runtime_progress_events")
    if not isinstance(events, list):
        return entries
    for event_index, event in enumerate(events):
        if not isinstance(event, dict):
            continue
        for key in ["label", "detail", "teacher_visible_text"]:
            _add_entry(
                entries,
                case_id=case_id,
                focus_id=focus_id,
                area=f"runtime_progress_events.{key}",
                path=f"runtime_progress_events[{event_index}].{key}",
                text=event.get(key),
                parent=event,
                default_visible=True,
                teacher_main_text=False,
            )
    return entries


def _collect_xiaojiao_entries(case_id: str, focus_id: str, response: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    patch = response.get("xiaojiao_context_patch")
    rows = patch.get("rows") if isinstance(patch, dict) else None
    if not isinstance(rows, list):
        return entries
    for row_index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        for key in ["episode_title", "next_action_hint", "evidence_check"]:
            _add_entry(
                entries,
                case_id=case_id,
                focus_id=focus_id,
                area=f"xiaojiao_context_patch.{key}",
                path=f"xiaojiao_context_patch.rows[{row_index}].{key}",
                text=row.get(key),
                parent=row,
                default_visible=True,
                teacher_main_text=False,
            )
    return entries


def _collect_right_rail_guard_entries(case_id: str, focus_id: str, response: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    patch = response.get("right_rail_patch")
    if not isinstance(patch, dict):
        return entries
    for index, text in enumerate(_items(patch.get("must_not_show"))):
        _add_entry(
            entries,
            case_id=case_id,
            focus_id=focus_id,
            area="right_rail_patch.must_not_show",
            path=f"right_rail_patch.must_not_show[{index}]",
            text=text,
            parent=patch,
            default_visible=False,
            teacher_main_text=False,
        )
    return entries


def _collect_frontend_visible_entries(case_id: str, focus_id: str, response: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    template = response.get("single_lesson_template") if isinstance(response.get("single_lesson_template"), dict) else {}
    entries.extend(_collect_section_entries(case_id, focus_id, template))
    entries.extend(_collect_episode_entries(case_id, focus_id, template))

    prep_patch = response.get("prep_view_patch") if isinstance(response.get("prep_view_patch"), dict) else {}
    current_lesson = prep_patch.get("current_lesson") if isinstance(prep_patch.get("current_lesson"), dict) else {}
    entries.extend(_collect_current_lesson_section_entries(case_id, focus_id, current_lesson))
    entries.extend(_collect_current_lesson_process_entries(case_id, focus_id, current_lesson))
    entries.extend(_collect_xiaojiao_entries(case_id, focus_id, response))
    entries.extend(_collect_runtime_progress_entries(case_id, focus_id, response))
    entries.extend(_collect_right_rail_guard_entries(case_id, focus_id, response))
    teacher_readable = response.get("teacher_readable_quality_preview")
    teacher_readable_policy = (
        teacher_readable.get("visibility_policy")
        if isinstance(teacher_readable, dict) and isinstance(teacher_readable.get("visibility_policy"), dict)
        else {}
    )
    teacher_readable_default_visible = teacher_readable_policy.get("default_visible") is not False
    entries.extend(
        _walk_strings(
            case_id=case_id,
            focus_id=focus_id,
            area="right_rail_teacher_readable_quality_preview",
            path="teacher_readable_quality_preview.draft",
            value=(teacher_readable or {}).get("draft") if isinstance(teacher_readable, dict) else {},
            default_visible=teacher_readable_default_visible,
            teacher_main_text=False,
        )
    )
    candidate = response.get("art_lesson_reasoning_candidate_preview")
    entries.extend(
        _walk_strings(
            case_id=case_id,
            focus_id=focus_id,
            area="r200b_candidate_visible_or_near_visible",
            path="art_lesson_reasoning_candidate_preview",
            value=candidate,
            default_visible=False,
            teacher_main_text=False,
        )
    )
    return entries


def _focus_id(response: dict[str, Any]) -> str:
    kernel = response.get("art_lesson_design_kernel_preview") if isinstance(response.get("art_lesson_design_kernel_preview"), dict) else {}
    focus = kernel.get("lesson_focus") if isinstance(kernel.get("lesson_focus"), dict) else {}
    return str(focus.get("focus_id") or "unknown")


def _deny_terms_for_focus(focus_id: str) -> list[str]:
    packet = ACTIVE_LESSON_DENYLIST.get(focus_id) or {}
    return list(packet.get("deny_terms") or [])


def _hit_terms(text: str, terms: list[str]) -> list[str]:
    return [term for term in terms if term and term in text]


def _contamination_hits(entries: list[dict[str, Any]], deny_terms: list[str]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for entry in entries:
        matched = _hit_terms(entry.get("text") or "", deny_terms)
        if not matched:
            continue
        hits.append(
            {
                "case_id": entry.get("case_id"),
                "focus_id": entry.get("focus_id"),
                "matched_terms": matched,
                "area": entry.get("area"),
                "path": entry.get("path"),
                "content_source_type": entry.get("content_source_type"),
                "default_visible": entry.get("default_visible"),
                "teacher_main_text": entry.get("teacher_main_text"),
                "text": entry.get("text"),
            }
        )
    return hits


def _source_policy_violations(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    for entry in entries:
        source_type = entry.get("content_source_type")
        if entry.get("teacher_main_text") and source_type in {"R200B_candidate", "deterministic_fallback", "legacy_shell"}:
            violations.append(
                {
                    "case_id": entry.get("case_id"),
                    "area": entry.get("area"),
                    "path": entry.get("path"),
                    "content_source_type": source_type,
                    "text": entry.get("text"),
                }
            )
        if entry.get("teacher_main_text") and source_type == "unknown":
            violations.append(
                {
                    "case_id": entry.get("case_id"),
                    "area": entry.get("area"),
                    "path": entry.get("path"),
                    "content_source_type": source_type,
                    "text": entry.get("text"),
                }
            )
    return violations


def _count_by_source(entries: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in entries:
        source_type = str(entry.get("content_source_type") or "unknown")
        counts[source_type] = counts.get(source_type, 0) + 1
    return dict(sorted(counts.items()))


def _case_snapshot(case: dict[str, Any], response: dict[str, Any], entries: list[dict[str, Any]], hits: list[dict[str, Any]]) -> dict[str, Any]:
    template = response.get("single_lesson_template") if isinstance(response.get("single_lesson_template"), dict) else {}
    focus_id = _focus_id(response)
    return {
        "case_id": case["case_id"],
        "file_name": response.get("upload_session", {}).get("file_name"),
        "focus_id": focus_id,
        "expected_focus": case.get("expected_focus"),
        "focus_ok": focus_id == case.get("expected_focus"),
        "visible_text_count": len([entry for entry in entries if entry.get("default_visible")]),
        "teacher_main_text_count": len([entry for entry in entries if entry.get("teacher_main_text")]),
        "deny_terms": _deny_terms_for_focus(focus_id),
        "contamination_hit_count": len(hits),
        "teacher_main_contamination_hit_count": len([hit for hit in hits if hit.get("teacher_main_text")]),
        "default_visible_source_type_counts": _count_by_source([entry for entry in entries if entry.get("default_visible")]),
        "teacher_main_source_type_counts": _count_by_source([entry for entry in entries if entry.get("teacher_main_text")]),
        "template_episode_count": len(template.get("process_episodes") or []),
        "boundary": response.get("boundary"),
        "response_keys": sorted(response.keys()),
        "visible_text_sample": [
            {
                "area": entry["area"],
                "source": entry["content_source_type"],
                "text": entry["text"][:220],
            }
            for entry in entries
            if entry.get("default_visible")
        ][:80],
    }


def _write_report(cases: list[dict[str, Any]], hits: list[dict[str, Any]], violations: list[dict[str, Any]], checks: dict[str, bool]) -> None:
    lines = [
        f"# {STAGE}",
        "",
        f"Status: `{'PASS' if all(checks.values()) else 'FAIL'}`",
        "",
        "## Checks",
        "",
    ]
    for key, value in checks.items():
        lines.append(f"- `{key}`: `{str(value).lower()}`")
    lines.extend(["", "## Cases", ""])
    for case in cases:
        lines.append(f"### {case['case_id']} ({case['focus_id']})")
        lines.append("")
        lines.append(f"- expected_focus: `{case.get('expected_focus')}`")
        lines.append(f"- focus_ok: `{str(case.get('focus_ok')).lower()}`")
        lines.append(f"- visible_text_count: `{case.get('visible_text_count')}`")
        lines.append(f"- teacher_main_text_count: `{case.get('teacher_main_text_count')}`")
        lines.append(f"- contamination_hit_count: `{case.get('contamination_hit_count')}`")
        lines.append(f"- teacher_main_contamination_hit_count: `{case.get('teacher_main_contamination_hit_count')}`")
        lines.append(f"- teacher_main_source_type_counts: `{json.dumps(case.get('teacher_main_source_type_counts') or {}, ensure_ascii=False)}`")
        case_hits = [hit for hit in hits if hit.get("case_id") == case["case_id"]]
        if case_hits:
            lines.append("")
            lines.append("Contamination hits:")
            for hit in case_hits[:20]:
                lines.append(
                    f"- `{','.join(hit.get('matched_terms') or [])}` | {hit.get('area')} | {hit.get('content_source_type')} | {hit.get('text')[:180]}"
                )
        lines.append("")
    if violations:
        lines.extend(["## Source Policy Violations", ""])
        for item in violations[:50]:
            lines.append(f"- `{item.get('content_source_type')}` | {item.get('case_id')} | {item.get('area')} | {item.get('text')[:180]}")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    DENYLIST.write_text(json.dumps(ACTIVE_LESSON_DENYLIST, ensure_ascii=False, indent=2), encoding="utf-8")

    all_entries: list[dict[str, Any]] = []
    all_hits: list[dict[str, Any]] = []
    case_results: list[dict[str, Any]] = []

    for case in SAMPLES:
        raw_text, file_name = case["source"]()
        response = _build_response(raw_text, file_name)
        focus_id = _focus_id(response)
        entries = _collect_frontend_visible_entries(case["case_id"], focus_id, response)
        hits = _contamination_hits(entries, _deny_terms_for_focus(focus_id))
        all_entries.extend(entries)
        all_hits.extend(hits)
        case_results.append(_case_snapshot(case, response, entries, hits))

    violations = _source_policy_violations(all_entries)
    default_visible_hits = [hit for hit in all_hits if hit.get("default_visible")]
    teacher_main_hits = [hit for hit in all_hits if hit.get("teacher_main_text")]
    focus_failures = [case for case in case_results if not case.get("focus_ok")]
    entries_without_source = [
        entry
        for entry in all_entries
        if entry.get("teacher_main_text") and entry.get("content_source_type") == "unknown"
    ]
    teacher_main_source_counts = _count_by_source([entry for entry in all_entries if entry.get("teacher_main_text")])
    default_visible_source_counts = _count_by_source([entry for entry in all_entries if entry.get("default_visible")])

    checks = {
        "uses_r103_response_snapshot": True,
        "frontend_visible_snapshot_written": True,
        "content_source_ledger_written": True,
        "active_lesson_denylist_written": True,
        "all_cases_focus_match_expected": not focus_failures,
        "teacher_main_has_no_denylist_hits": not teacher_main_hits,
        "default_visible_has_no_denylist_hits": not default_visible_hits,
        "r200b_candidate_not_teacher_main_text": not any(
            item.get("content_source_type") == "R200B_candidate" for item in all_entries if item.get("teacher_main_text")
        ),
        "deterministic_fallback_not_teacher_main_conclusion": not any(
            item.get("content_source_type") == "deterministic_fallback" for item in all_entries if item.get("teacher_main_text")
        ),
        "legacy_shell_not_default_visible": not any(
            item.get("content_source_type") == "legacy_shell" for item in all_entries if item.get("default_visible")
        ),
        "main_text_entries_have_content_source_type": not entries_without_source,
        "teacher_main_R200A_kernel_count_zero": teacher_main_source_counts.get("R200A_kernel", 0) == 0,
        "teacher_main_unknown_count_zero": teacher_main_source_counts.get("unknown", 0) == 0,
        "default_visible_deterministic_fallback_count_zero": default_visible_source_counts.get("deterministic_fallback", 0) == 0,
        "default_visible_unknown_count_zero": default_visible_source_counts.get("unknown", 0) == 0,
        "preview_only_no_formal_apply": True,
    }

    result = {
        "stage": STAGE,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "summary": {
            "case_count": len(case_results),
            "visible_entry_count": len([entry for entry in all_entries if entry.get("default_visible")]),
            "teacher_main_entry_count": len([entry for entry in all_entries if entry.get("teacher_main_text")]),
            "contamination_hit_count": len(all_hits),
            "default_visible_hit_count": len(default_visible_hits),
            "teacher_main_hit_count": len(teacher_main_hits),
            "source_policy_violation_count": len(violations),
            "focus_failure_count": len(focus_failures),
            "default_visible_source_type_counts": default_visible_source_counts,
            "teacher_main_source_type_counts": teacher_main_source_counts,
        },
        "cases": case_results,
        "contamination_hits": all_hits,
        "source_policy_violations": violations,
        "boundary": {
            "model_called": False,
            "provider_called": False,
            "formal_apply": False,
            "database_written": False,
            "validator_only": True,
        },
        "outputs": {
            "frontend_visible_text_snapshot": str(SNAPSHOT.relative_to(ROOT)),
            "content_source_ledger": str(LEDGER.relative_to(ROOT)),
            "active_lesson_denylist": str(DENYLIST.relative_to(ROOT)),
            "contamination_hit_report": str(REPORT.relative_to(ROOT)),
        },
    }
    SNAPSHOT.write_text(json.dumps({"stage": STAGE, "cases": case_results}, ensure_ascii=False, indent=2), encoding="utf-8")
    LEDGER.write_text(json.dumps({"stage": STAGE, "entries": all_entries}, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_report(case_results, all_hits, violations, checks)
    RESULT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
