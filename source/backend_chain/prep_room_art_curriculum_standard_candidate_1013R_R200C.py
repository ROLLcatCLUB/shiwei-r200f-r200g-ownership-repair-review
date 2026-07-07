from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any


STAGE_ID = "1013R_R200C_CURRICULUM_STANDARD_SLICE_BINDING_PREVIEW"
DEFAULT_SLICE_JSONL = Path(
    r"E:\codex\xiaobei-knowledge-base\_s_samples\curriculum_standard_0928S\extracted\art_curriculum_standard_slices_0928S.jsonl"
)
DEFAULT_LOCAL_STANDARD_DOCX = Path(
    r"E:\学校工作\教学\小学美术备课智能体\义务教育艺术课程标准2022年版（美术）_整理版.docx"
)
MAX_CANDIDATE_REFS = 6


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _items(value: Any, *, limit: int = 12) -> list[str]:
    if isinstance(value, list):
        return [_clean(item) for item in value if _clean(item)][:limit]
    if isinstance(value, tuple):
        return [_clean(item) for item in value if _clean(item)][:limit]
    text = _clean(value)
    return [text] if text else []


def _slice_path() -> Path:
    configured = _clean(os.environ.get("XIAOBEI_ART_CURRICULUM_SLICES_JSONL"))
    return Path(configured) if configured else DEFAULT_SLICE_JSONL


def _local_standard_docx_path() -> Path:
    configured = _clean(os.environ.get("XIAOBEI_ART_CURRICULUM_STANDARD_DOCX"))
    return Path(configured) if configured else DEFAULT_LOCAL_STANDARD_DOCX


def _load_slices(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def _grade_band(grade: str) -> str:
    text = _clean(grade)
    if any(token in text for token in ["一", "二", "1", "2"]):
        return "1-2"
    if any(token in text for token in ["三", "四", "五", "3", "4", "5"]):
        return "3-5"
    if any(token in text for token in ["六", "6"]):
        return "6-7"
    return "all_primary_art"


def _lesson_text(template: dict[str, Any]) -> str:
    header = template.get("lesson_header") if isinstance(template.get("lesson_header"), dict) else {}
    parts: list[str] = []
    for key in ["lesson_title", "unit_title", "grade", "lesson_code"]:
        parts.extend(_items(header.get(key)))
    for section_key in [
        "basis",
        "student_analysis",
        "objectives",
        "key_difficult_points",
        "preparation",
        "assessment_or_homework",
        "reflection_or_notes",
    ]:
        for item in template.get(section_key) or []:
            if isinstance(item, dict):
                parts.extend(_items(item.get("text") or item.get("value") or item.get("body")))
            else:
                parts.extend(_items(item))
    for episode in template.get("process_episodes") or []:
        if not isinstance(episode, dict):
            continue
        for key in [
            "episode_title",
            "episode_goal",
            "teacher_organization",
            "student_learning",
            "key_talk",
            "evidence",
        ]:
            parts.extend(_items(episode.get(key), limit=4))
        for micro in episode.get("micro_steps") or []:
            if not isinstance(micro, dict):
                continue
            for key in ["title", "step_name", "teacher_action", "student_action", "evidence"]:
                parts.extend(_items(micro.get(key), limit=2))
    return " ".join(parts)


KEYWORD_GROUPS: list[tuple[str, list[str]]] = [
    ("欣赏评述", ["欣赏", "评述", "观察", "感受", "作品", "展览", "参观", "交流", "说出"]),
    ("造型表现", ["造型", "表现", "创作", "绘画", "色彩", "线条", "形状", "材料", "媒介", "作品"]),
    ("设计应用", ["设计", "应用", "实用", "美观", "包装", "标识", "海报", "物品", "活动设计"]),
    ("综合探索", ["综合", "探索", "项目", "跨学科", "自然", "社会", "科技", "环保", "海洋", "守护"]),
    ("评价证据", ["评价", "互评", "自评", "展示", "分享", "证据", "贴纸", "颁奖", "学习单"]),
    ("传统工艺", ["工艺", "传统", "剪纸", "编织", "陶艺", "印染", "风筝", "工匠"]),
]


def _keywords(text: str) -> set[str]:
    found: set[str] = set()
    for label, terms in KEYWORD_GROUPS:
        if any(term in text for term in terms):
            found.add(label)
        for term in terms:
            if term in text:
                found.add(term)
    return found


def _slice_score(row: dict[str, Any], *, lesson_terms: set[str], target_grade_band: str, lesson_text: str) -> int:
    score = 0
    grade_band = _clean(row.get("grade_band"))
    if grade_band == target_grade_band:
        score += 18
    elif grade_band == "all_primary_art":
        score += 8
    else:
        return -999
    if row.get("art_domain") == "visual_arts":
        score += 4
    evidence_type = _clean(row.get("evidence_type"))
    if evidence_type in {"stage_goal", "content_requirement", "academic_requirement"}:
        score += 5
    elif evidence_type in {"core_literacy", "assessment_tip", "curriculum_concept"}:
        score += 3
    row_text = " ".join(
        [
            _clean(row.get("section_path")),
            _clean(row.get("standard_text")),
            _clean(row.get("key_terms")),
            _clean(row.get("field_support_scope")),
        ]
    )
    row_terms = _keywords(row_text)
    score += len(lesson_terms & row_terms) * 5
    for token in ["海洋", "环保", "展览", "展示", "互评", "评价", "设计", "作品", "材料", "色彩"]:
        if token in lesson_text and token in row_text:
            score += 3
    if _clean(row.get("review_status")) == "pending_review":
        score -= 1
    if _clean(row.get("usable_for_official_claim")).lower() == "true":
        score += 1
    return score


def _summarize_slice(row: dict[str, Any]) -> dict[str, Any]:
    text = _clean(row.get("standard_text"))
    return {
        "slice_id": row.get("slice_id"),
        "source_id": row.get("source_id"),
        "source_level": row.get("source_level"),
        "standard_version_label": f"{row.get('standard_title') or '义务教育艺术课程标准'} {row.get('standard_version') or '2022年版'}",
        "section_path": row.get("section_path"),
        "source_doc": row.get("source_doc"),
        "source_locator": row.get("source_locator"),
        "evidence_type": row.get("evidence_type"),
        "grade_band": row.get("grade_band"),
        "learning_domain": row.get("art_domain"),
        "key_terms": _items(str(row.get("key_terms") or "").replace(";", "；").split("；"), limit=12),
        "field_support_scope": row.get("field_support_scope"),
        "review_status": row.get("review_status"),
        "teacher_review_required": True,
        "candidate_only": True,
        "source_quote_policy": "short_excerpt_only",
        "standard_excerpt": text[:180],
    }


def build_curriculum_standard_candidate_preview(
    *,
    single_lesson_template: dict[str, Any],
    art_lesson_design_kernel_preview: dict[str, Any],
) -> dict[str, Any]:
    template = single_lesson_template if isinstance(single_lesson_template, dict) else {}
    kernel = art_lesson_design_kernel_preview if isinstance(art_lesson_design_kernel_preview, dict) else {}
    header = template.get("lesson_header") if isinstance(template.get("lesson_header"), dict) else {}
    target_grade_band = _grade_band(_clean(header.get("grade") or (kernel.get("lesson_header") or {}).get("grade")))
    path = _slice_path()
    rows = _load_slices(path)
    text = _lesson_text(template)
    terms = _keywords(text)
    scored: list[tuple[int, dict[str, Any]]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        score = _slice_score(row, lesson_terms=terms, target_grade_band=target_grade_band, lesson_text=text)
        if score > 0:
            scored.append((score, row))
    scored.sort(key=lambda item: (-item[0], str(item[1].get("slice_id") or "")))
    candidate_refs = []
    seen: set[str] = set()
    for score, row in scored:
        slice_id = _clean(row.get("slice_id"))
        if not slice_id or slice_id in seen:
            continue
        seen.add(slice_id)
        summary = _summarize_slice(row)
        summary["match_score"] = score
        candidate_refs.append(summary)
        if len(candidate_refs) >= MAX_CANDIDATE_REFS:
            break
    status = "candidate_refs_available" if candidate_refs else ("slice_source_missing" if not rows else "no_candidate_match")
    local_docx = _local_standard_docx_path()
    return {
        "stage": STAGE_ID,
        "status": status,
        "candidate_id": f"r200c_curriculum_refs_{target_grade_band}_{len(candidate_refs)}",
        "candidate_available": bool(candidate_refs),
        "candidate_only": True,
        "teacher_review_required": True,
        "source_path": str(path),
        "source_exists": path.exists(),
        "source_documents": {
            "local_standard_docx": str(local_docx),
            "local_standard_docx_exists": local_docx.exists(),
            "structured_slices_jsonl": str(path),
            "structured_slices_jsonl_exists": path.exists(),
            "source_package": "0928S_art_curriculum_standard_ingest_and_slice",
            "source_package_kind": "local_knowledge_base_structured_slices",
        },
        "source_integrity": {
            "uses_local_standard_docx_reference": local_docx.exists(),
            "uses_structured_slice_index": bool(rows),
            "full_docx_text_dumped_to_prompt": False,
            "candidate_refs_have_source_locator": all(bool(item.get("source_locator")) for item in candidate_refs),
            "candidate_refs_have_short_excerpt": all(bool(item.get("standard_excerpt")) for item in candidate_refs),
        },
        "source_id": "SRC_MOE_ART_CURRICULUM_2022" if rows else None,
        "source_level": "A0" if rows else None,
        "slice_count": len(rows),
        "target_grade_band": target_grade_band,
        "lesson_terms": sorted(terms),
        "candidate_refs": candidate_refs,
        "curriculum_control_patch": {
            "interpretation_status": "candidate_interpretation_pending_teacher_review"
            if candidate_refs
            else "missing_structured_standard_ref",
            "teacher_confirmation_status": "pending_teacher_confirm",
            "standard_ref_ids": [item.get("slice_id") for item in candidate_refs if item.get("slice_id")],
            "standard_version_label": "义务教育艺术课程标准 2022年版",
            "structured_standard_refs_available": bool(candidate_refs),
            "real_curriculum_standard_slices_loaded": bool(rows),
            "real_curriculum_standard_full_text_parsed": False,
            "official_curriculum_claim_created": False,
            "full_standard_text_dumped_to_prompt": False,
        },
        "boundary": {
            "preview_only": True,
            "candidate_only": True,
            "formal_apply_performed": False,
            "database_written": False,
            "memory_written": False,
            "feishu_written": False,
            "provider_called": False,
            "model_called": False,
            "official_curriculum_claim_created": False,
            "full_standard_text_dumped_to_prompt": False,
            "lesson_body_modified": False,
        },
    }


def apply_curriculum_standard_candidate_to_art_kernel(
    art_lesson_design_kernel_preview: dict[str, Any],
    curriculum_standard_candidate_preview: dict[str, Any],
) -> None:
    if not isinstance(art_lesson_design_kernel_preview, dict) or not isinstance(curriculum_standard_candidate_preview, dict):
        return
    patch = curriculum_standard_candidate_preview.get("curriculum_control_patch")
    if not isinstance(patch, dict):
        return
    control = art_lesson_design_kernel_preview.setdefault("curriculum_standard_control", {})
    if not isinstance(control, dict):
        return
    control.update(patch)
    control["candidate_ref_count"] = len(curriculum_standard_candidate_preview.get("candidate_refs") or [])
    control["candidate_refs"] = curriculum_standard_candidate_preview.get("candidate_refs") or []
    if curriculum_standard_candidate_preview.get("candidate_available"):
        missing = control.get("missing_required_fields")
        if isinstance(missing, list):
            control["missing_required_fields"] = [
                item for item in missing if item not in {"standard_version_label", "standard_ref_ids"}
            ]
        art_lesson_design_kernel_preview["kernel_status"] = "KERNEL_READY_WITH_CURRICULUM_CANDIDATE_REFS"


def _focus_id_from_template(single_lesson_template: dict[str, Any]) -> str:
    kernel = single_lesson_template.get("art_lesson_design_kernel_preview")
    if isinstance(kernel, dict):
        focus = kernel.get("lesson_focus")
        if isinstance(focus, dict):
            return _clean(focus.get("focus_id"))
    return ""


def _candidate_basis_text(refs: list[dict[str, Any]]) -> str:
    labels = []
    for ref in refs[:3]:
        if not isinstance(ref, dict):
            continue
        label = _clean(ref.get("section_path")) or _clean(ref.get("evidence_type")) or _clean(ref.get("slice_id"))
        excerpt = _clean(ref.get("standard_excerpt"))
        if label and excerpt:
            labels.append(f"{label}：{excerpt[:48]}")
        elif label:
            labels.append(label)
    return "；".join(labels)


def _curriculum_field_lines(focus_id: str, refs: list[dict[str, Any]]) -> dict[str, str]:
    basis_text = _candidate_basis_text(refs)
    review_tail = "以上为本地课标候选切片，进入正式备课前仍需教师核对。"
    if focus_id == "shoe_observation_drawing_expression":
        return {
            "basis": f"课标候选依据提示：本课可暂按小学3-5年级美术中观察、造型表现与作品交流方向理解，重点服务“看见鞋的角度/结构/细节，并用线条表达”。{review_tail}",
            "student_analysis": "结合课标候选方向看，学情分析应重点确认学生是否能从生活物品中提取可见特征，并把观察语言转成线条、比例和局部细节。",
            "objectives": "课标候选约束下，目标不只写“画一双鞋”，还要保留观察角度、结构细节、线描表达和交流证据。",
            "key_difficult_points": "课标候选约束下，重难点应落在观察证据转化为造型表现：比例、角度、鞋面/鞋底/鞋带等细节不能只靠想象补画。",
        }
    if focus_id == "color_gradation_expression":
        return {
            "basis": f"课标候选依据提示：本课可暂按小学3-5年级美术中色彩观察、表现方法与作品交流方向理解。{review_tail}",
            "student_analysis": "结合课标候选方向看，学情分析应确认学生是否能观察颜色变化，并把感受转成可操作的试色或表现方法。",
            "objectives": "课标候选约束下，目标应同时包含观察色彩变化、尝试表现方法和用作品证据说明效果。",
            "key_difficult_points": "课标候选约束下，重难点应落在颜色变化的观察与表现控制，而不是只写完成涂色任务。",
        }
    generic_basis = f"课标候选依据提示：{basis_text or '本课已匹配本地美术课标候选切片'}。{review_tail}"
    return {
        "basis": generic_basis,
        "student_analysis": "结合课标候选方向看，学情分析应确认学生已有观察、材料尝试、作品表达和交流证据基础。",
        "objectives": "课标候选约束下，目标应同时包含观察/感受、方法尝试、作品表达和证据交流。",
        "key_difficult_points": "课标候选约束下，重难点应落到学生能看见、能操作、能说明的课堂证据。",
    }


def _append_template_section_line(template: dict[str, Any], section_key: str, line: str) -> None:
    if not line:
        return
    section = template.get(section_key)
    if not isinstance(section, list) or not section:
        return
    first = section[0]
    if not isinstance(first, dict):
        return
    body = first.get("body")
    if not isinstance(body, list):
        body = _items(first.get("text") or first.get("value") or body)
    if not any(_clean(item) == line for item in body):
        body.append(line)
    first["body"] = body[:7]
    first.setdefault("source_capsules", []).append(
        {
            "label": "课标候选依据",
            "kind": "curriculum_candidate",
            "source_excerpt": line,
            "display_mode": "click_to_show_candidate_ref",
        }
    )
    first["teacher_review_required"] = True


def _append_current_section_line(current_lesson: dict[str, Any], section_id: str, line: str) -> None:
    if not line:
        return
    for section in current_lesson.get("sections") or []:
        if not isinstance(section, dict) or _clean(section.get("id")) != section_id:
            continue
        items = _items(section.get("items") or section.get("body"), limit=12)
        if not any(_clean(item) == line for item in items):
            items.append(line)
        section["items"] = items[:7]
        section.setdefault("source_capsules", []).append(
            {
                "label": "课标候选依据",
                "kind": "curriculum_candidate",
                "source_excerpt": line,
                "display_mode": "click_to_show_candidate_ref",
            }
        )
        section["teacher_review_required"] = True
        break


def apply_curriculum_standard_candidate_to_template(
    single_lesson_template: dict[str, Any],
    curriculum_standard_candidate_preview: dict[str, Any],
) -> None:
    if not isinstance(single_lesson_template, dict) or not isinstance(curriculum_standard_candidate_preview, dict):
        return
    single_lesson_template["curriculum_standard_candidate_preview"] = curriculum_standard_candidate_preview
    status = (curriculum_standard_candidate_preview.get("curriculum_control_patch") or {}).get(
        "interpretation_status",
        "missing_structured_standard_ref",
    )
    refs = curriculum_standard_candidate_preview.get("candidate_refs") or []
    ref_ids = [item.get("slice_id") for item in refs[:3] if isinstance(item, dict) and item.get("slice_id")]
    ref_summary = _candidate_basis_text(refs)
    field_lines = _curriculum_field_lines(_focus_id_from_template(single_lesson_template), refs)
    for section_key, line in field_lines.items():
        _append_template_section_line(single_lesson_template, section_key, line)
    for episode in single_lesson_template.get("process_episodes") or []:
        if not isinstance(episode, dict):
            continue
        basis = episode.get("derivation_basis")
        if isinstance(basis, dict):
            basis["standard_alignment_status"] = status
            basis["curriculum_candidate_ref_ids"] = ref_ids
            basis["curriculum_candidate_summary"] = ref_summary
            basis["standard_alignment_note"] = "课标候选仅用于教师确认前的依据提示，不作为正式课标结论。"
        for micro in episode.get("micro_steps") or []:
            if isinstance(micro, dict) and isinstance(micro.get("derivation_basis"), dict):
                micro["derivation_basis"]["standard_alignment_status"] = status
                micro["derivation_basis"]["curriculum_candidate_ref_ids"] = ref_ids


def apply_curriculum_standard_candidate_to_current_lesson(
    current_lesson: dict[str, Any],
    curriculum_standard_candidate_preview: dict[str, Any],
) -> None:
    if not isinstance(current_lesson, dict) or not isinstance(curriculum_standard_candidate_preview, dict):
        return
    current_lesson["curriculum_standard_candidate_preview"] = curriculum_standard_candidate_preview
    status = (curriculum_standard_candidate_preview.get("curriculum_control_patch") or {}).get(
        "interpretation_status",
        "missing_structured_standard_ref",
    )
    refs = curriculum_standard_candidate_preview.get("candidate_refs") or []
    ref_ids = [item.get("slice_id") for item in refs[:3] if isinstance(item, dict) and item.get("slice_id")]
    ref_summary = _candidate_basis_text(refs)
    focus_id = ""
    focus = current_lesson.get("lesson_focus_preview")
    if isinstance(focus, dict):
        focus_id = _clean(focus.get("focus_id"))
    kernel = current_lesson.get("art_lesson_design_kernel_preview")
    if not focus_id and isinstance(kernel, dict) and isinstance(kernel.get("lesson_focus"), dict):
        focus_id = _clean(kernel["lesson_focus"].get("focus_id"))
    field_lines = _curriculum_field_lines(focus_id, refs)
    for section_id, line in {
        "basis": field_lines.get("basis", ""),
        "analysis": field_lines.get("student_analysis", ""),
        "goals": field_lines.get("objectives", ""),
        "keypoints": field_lines.get("key_difficult_points", ""),
    }.items():
        _append_current_section_line(current_lesson, section_id, line)
    for step in current_lesson.get("process_steps") or []:
        if not isinstance(step, dict):
            continue
        basis = step.get("derivation_basis")
        if isinstance(basis, dict):
            basis["standard_alignment_status"] = status
            basis["curriculum_candidate_ref_ids"] = ref_ids
            basis["curriculum_candidate_summary"] = ref_summary
            basis["standard_alignment_note"] = "课标候选仅用于教师确认前的依据提示，不作为正式课标结论。"
