from __future__ import annotations

import hashlib
import re
from copy import deepcopy
from typing import Any


STAGE_ID = "1013R_R97B_P3_DERIVATION_SPINE_FOR_SINGLE_LESSON_TEMPLATE"

SECTION_TO_TEMPLATE_KEY = {
    "basis": "basis",
    "analysis": "student_analysis",
    "goals": "objectives",
    "keypoints": "key_difficult_points",
    "preparation": "preparation",
    "assessment": "assessment_or_homework",
    "reflection": "reflection_or_notes",
}


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _truncate(value: Any, limit: int = 120) -> str:
    text = _clean(value)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def _short_id(*parts: Any) -> str:
    text = "|".join(_clean(part) for part in parts)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]


def _items(value: Any) -> list[str]:
    if isinstance(value, list):
        return [_clean(item) for item in value if _clean(item)]
    if _clean(value):
        return [_clean(value)]
    return []


def _field_candidates(projection_preview: dict[str, Any]) -> dict[str, Any]:
    candidates = projection_preview.get("field_candidates") if isinstance(projection_preview, dict) else {}
    return candidates if isinstance(candidates, dict) else {}


def _execution_map(execution_preview: dict[str, Any]) -> dict[str, Any]:
    execution = execution_preview.get("teacher_execution_map") if isinstance(execution_preview, dict) else {}
    return execution if isinstance(execution, dict) else {}


def _graph(projection_preview: dict[str, Any], understanding_preview: dict[str, Any]) -> dict[str, Any]:
    graph = understanding_preview.get("graph") if isinstance(understanding_preview, dict) else {}
    if isinstance(graph, dict) and graph:
        return graph
    projection = projection_preview.get("field_projection") if isinstance(projection_preview, dict) else {}
    return projection if isinstance(projection, dict) else {}


def _claim_chain_for_section(section_id: str, candidate: dict[str, Any]) -> list[dict[str, Any]]:
    chain = []
    for basis in candidate.get("graph_basis") or []:
        if not isinstance(basis, dict):
            continue
        chain.append(
            {
                "claim_id": basis.get("claim_id"),
                "claim_type": basis.get("claim_type"),
                "graph_path": basis.get("graph_path"),
                "text": _clean(basis.get("text")),
                "source_evidence": _items(basis.get("source_evidence")),
                "teacher_review_required": bool(basis.get("teacher_review_required")),
                "supports_section": section_id,
            }
        )
    return chain


def _section_spine(section_id: str, candidate: dict[str, Any]) -> dict[str, Any]:
    body = _items(candidate.get("items"))
    claim_chain = _claim_chain_for_section(section_id, candidate)
    return {
        "section_id": section_id,
        "title": candidate.get("title"),
        "body": body,
        "derivation_role": {
            "basis": "source_basis",
            "analysis": "student_starting_point_and_learning_risk",
            "goals": "target_shift",
            "keypoints": "difficulty_and_focus",
            "preparation": "material_and_condition_support",
            "assessment": "evidence_plan",
            "reflection": "post_class_gap",
        }.get(section_id, "lesson_section"),
        "claim_chain": claim_chain,
        "source_capsules": deepcopy(candidate.get("source_capsules") or []),
        "projection_policy": candidate.get("projection_policy"),
        "classification": candidate.get("classification") or "r97b_p3_derivation_spine_projection",
        "source_status": "r114c_graph_projected",
        "teacher_review_required": True,
        "preview_only": True,
    }


def _flow_steps(execution_preview: dict[str, Any]) -> list[dict[str, Any]]:
    execution = _execution_map(execution_preview)
    return [step for step in execution.get("classroom_flow") or [] if isinstance(step, dict)]


def _match_flow_step(episode: dict[str, Any], flow: list[dict[str, Any]], index: int) -> dict[str, Any]:
    if not flow:
        return {}
    title = _clean(episode.get("episode_title"))
    source_episode_id = _clean(episode.get("source_episode_id") or episode.get("episode_id"))
    for step in flow:
        if source_episode_id and source_episode_id == _clean(step.get("source_episode_id")):
            return step
    for step in flow:
        if title and title == _clean(step.get("title")):
            return step
    if index < len(flow):
        return flow[index]
    return {}


def _evidence_text(item: Any) -> str:
    if isinstance(item, dict):
        return _clean(item.get("evidence") or item.get("proves") or item.get("what_it_proves"))
    return _clean(item)


def _transition_role(micro_index: int, micro_count: int) -> str:
    if micro_count <= 1:
        return "complete_episode_move"
    if micro_index == 0:
        return "open_episode_and_set_task"
    if micro_index == micro_count - 1:
        return "collect_evidence_and_prepare_transition"
    return "advance_core_operation"


def _episode_title(episode: dict[str, Any], index: int) -> str:
    return _clean(episode.get("episode_title")) or _clean(episode.get("title")) or f"环节{index + 1}"


def _teacher_usable_evidence(raw_evidence: str, title: str) -> str:
    evidence = _clean(raw_evidence)
    if evidence and "需从学生任务" not in evidence and "需教师确认" not in evidence:
        return evidence
    if any(token in title for token in ["导入", "引入"]):
        return "学生能说出一个看得见的发现或提出一个与本课对象相关的问题。"
    if any(token in title for token in ["观察", "指导", "发现"]):
        return "学生能指认具体观察位置，并用可见词说明自己的判断。"
    if any(token in title for token in ["写生", "画", "动手", "创作", "练习", "制作"]):
        return "学生作品或练习中能留下来自观察、方法尝试或调整过程的可见痕迹。"
    if any(token in title for token in ["展示", "交流", "小结", "评价", "分享", "展评"]):
        return "学生能指着作品或学习产出说明一个依据，并听取或给出一条调整建议。"
    return evidence or "本环节至少需要留下一个口头发现、作品痕迹或同伴交流证据。"


def _transition_to_next(
    *,
    title: str,
    next_title: str,
    evidence: str,
    flow_step: dict[str, Any],
) -> str:
    explicit = _clean(flow_step.get("transition_to_next")) if isinstance(flow_step, dict) else ""
    if explicit and explicit not in {"用本环节证据支撑下一环节推进。", "下一环节过渡需教师确认。"}:
        return explicit
    if not next_title:
        return "用本环节收集到的作品、语言或过程证据收束本课学习。"
    if any(token in title for token in ["导入", "引入"]):
        return f"先确认学生已经说出可见发现或问题，再进入“{next_title}”。"
    if any(token in title for token in ["观察", "指导", "发现"]):
        return f"把学生确认的观察角度、结构或方法标准带入“{next_title}”。"
    if any(token in title for token in ["写生", "画", "动手", "创作", "练习", "制作"]):
        return f"用学生的作品痕迹和困难点作为“{next_title}”的交流材料。"
    if evidence:
        return f"先收集“{_truncate(evidence, 80)}”，再转入“{next_title}”。"
    return f"确认本环节任务完成后，再进入“{next_title}”。"


def _episode_spine(
    episode: dict[str, Any],
    flow_step: dict[str, Any],
    index: int,
    next_episode: dict[str, Any] | None = None,
) -> dict[str, Any]:
    basis = flow_step.get("source_basis") if isinstance(flow_step.get("source_basis"), dict) else {}
    evidence_items = flow_step.get("evidence_to_watch") if isinstance(flow_step.get("evidence_to_watch"), list) else []
    evidence_text = "；".join(text for text in (_evidence_text(item) for item in evidence_items) if text)
    why_now = _clean(flow_step.get("why_now")) or _clean(episode.get("episode_goal")) or "本环节推进依据需教师结合上传原文确认。"
    title = _episode_title(episode, index)
    next_title = _episode_title(next_episode, index + 1) if isinstance(next_episode, dict) else ""
    usable_evidence = _teacher_usable_evidence(evidence_text, title)
    student_before = f"进入“{title}”前，学生尚未完成本环节证据。"
    student_after = _clean(flow_step.get("student_action")) or _clean(episode.get("student_learning"))
    return {
        "episode_id": episode.get("episode_id"),
        "episode_title": episode.get("episode_title"),
        "why_now": why_now,
        "student_state_before": student_before,
        "student_state_after": student_after,
        "teacher_move": _clean(flow_step.get("teacher_move")) or _clean(episode.get("key_teacher_talk")),
        "likely_stuck_point": _clean(flow_step.get("likely_stuck_point")),
        "assessment_evidence": usable_evidence,
        "transition_from_previous": "承接上一环节的观察、操作或表达结果。" if index else "从本课依据和学情判断进入第一环节。",
        "transition_to_next": _transition_to_next(
            title=title,
            next_title=next_title,
            evidence=usable_evidence,
            flow_step=flow_step,
        ),
        "source_claim_id": basis.get("claim_id"),
        "source_claim_type": basis.get("claim_type"),
        "source_evidence": _items(basis.get("source_evidence")),
        "teacher_review_required": True,
        "preview_only": True,
    }


def build_derivation_spine(
    *,
    single_lesson_template: dict[str, Any],
    import_understanding_v2_graph_preview: dict[str, Any],
    import_teacher_execution_map_preview: dict[str, Any],
    import_graph_field_projection_preview: dict[str, Any],
) -> dict[str, Any]:
    candidates = _field_candidates(import_graph_field_projection_preview)
    flow = _flow_steps(import_teacher_execution_map_preview)
    graph = _graph(import_graph_field_projection_preview, import_understanding_v2_graph_preview)
    sections = {
        section_id: _section_spine(section_id, candidate)
        for section_id, candidate in candidates.items()
        if isinstance(candidate, dict) and section_id in SECTION_TO_TEMPLATE_KEY
    }
    episodes = []
    process_episodes = single_lesson_template.get("process_episodes") or []
    for index, episode in enumerate(process_episodes):
        flow_step = _match_flow_step(episode, flow, index)
        next_episode = process_episodes[index + 1] if index + 1 < len(process_episodes) else None
        episode_spine = _episode_spine(episode, flow_step, index, next_episode)
        micro_spines = []
        micro_steps = episode.get("micro_steps") or []
        for micro_index, micro in enumerate(micro_steps):
            micro_basis = deepcopy(micro.get("decomposition_basis") or {})
            micro_basis.update(
                {
                    "spine_id": f"r97b_p3_micro_{_short_id(episode.get('episode_id'), micro.get('step_id'), micro_index)}",
                    "episode_why_now": episode_spine["why_now"],
                    "transition_role": _transition_role(micro_index, len(micro_steps)),
                    "assessment_evidence": episode_spine["assessment_evidence"],
                    "source_claim_id": episode_spine.get("source_claim_id"),
                    "source_claim_type": episode_spine.get("source_claim_type"),
                }
            )
            micro_spines.append({"step_id": micro.get("step_id"), "basis": micro_basis})
        episodes.append({**episode_spine, "micro_step_spines": micro_spines})

    chain_checks = {
        "basis_supports_analysis": "basis" in sections and "analysis" in sections,
        "analysis_supports_goals": "analysis" in sections and "goals" in sections,
        "goals_support_keypoints": "goals" in sections and "keypoints" in sections,
        "keypoints_support_process": "keypoints" in sections and bool(episodes),
        "process_supports_microsteps": bool(episodes)
        and all(bool(item.get("micro_step_spines")) for item in episodes),
        "every_microstep_has_basis": all(
            bool(micro.get("basis", {}).get("rule") or micro.get("basis", {}).get("episode_why_now"))
            for episode in episodes
            for micro in episode.get("micro_step_spines") or []
        ),
        "transition_or_pointback_present": all(
            _clean(item.get("transition_to_next")) or _clean(item.get("transition_from_previous")) for item in episodes
        ),
    }
    return {
        "stage": STAGE_ID,
        "spine_id": f"r97b_p3_spine_{_short_id(single_lesson_template.get('template_id'), graph.get('graph_id'))}",
        "spine_version": "single_lesson_derivation_spine_v0.1",
        "source_chain": [
            "uploaded_original_text",
            "R114A_understanding_graph",
            "R114B_teacher_execution_map",
            "R114C_graph_field_projection",
            "single_lesson_template",
        ],
        "sections": sections,
        "episodes": episodes,
        "chain_checks": chain_checks,
        "status": "PASS_WITH_GAPS" if all(chain_checks.values()) else "NEEDS_TEACHER_REVIEW",
        "teacher_review_required": True,
        "preview_only": True,
        "formal_apply": False,
        "boundary": {
            "preview_only": True,
            "provider_model_call_added": False,
            "formal_apply_performed": False,
            "database_written": False,
            "memory_written": False,
            "feishu_written": False,
            "R21_modified": False,
            "R36_modified": False,
            "R95_executed": False,
        },
    }


def _apply_section_to_template(template: dict[str, Any], section_id: str, section_spine: dict[str, Any]) -> None:
    template_key = SECTION_TO_TEMPLATE_KEY.get(section_id)
    if not template_key:
        return
    target = template.get(template_key)
    if not isinstance(target, list):
        return
    body = _items(section_spine.get("body"))
    if not body:
        return
    if target:
        target[0]["body"] = body
        target[0]["source_status"] = section_spine.get("source_status") or target[0].get("source_status")
        target[0]["derivation_spine_section_id"] = section_id
        target[0]["source_capsules"] = deepcopy(section_spine.get("source_capsules") or [])
        target[0]["graph_basis"] = deepcopy(section_spine.get("claim_chain") or [])
        target[0]["teacher_review_required"] = True


def apply_derivation_spine_to_template(single_lesson_template: dict[str, Any], spine: dict[str, Any]) -> dict[str, Any]:
    template = single_lesson_template
    template["lesson_derivation_spine"] = spine
    template.setdefault("renderer_policy", {})["derivation_spine_applied"] = True
    for section_id, section_spine in (spine.get("sections") or {}).items():
        if isinstance(section_spine, dict):
            _apply_section_to_template(template, section_id, section_spine)
    episode_spines = {
        _clean(item.get("episode_id")): item
        for item in spine.get("episodes") or []
        if isinstance(item, dict)
    }
    for episode in template.get("process_episodes") or []:
        episode_spine = episode_spines.get(_clean(episode.get("episode_id")))
        if not isinstance(episode_spine, dict):
            continue
        episode["derivation_basis"] = {
            key: episode_spine.get(key)
            for key in [
                "why_now",
                "student_state_before",
                "student_state_after",
                "teacher_move",
                "likely_stuck_point",
                "assessment_evidence",
                "transition_from_previous",
                "transition_to_next",
                "source_claim_id",
                "source_claim_type",
                "source_evidence",
            ]
        }
        micro_basis_by_id = {
            _clean(item.get("step_id")): item.get("basis")
            for item in episode_spine.get("micro_step_spines") or []
            if isinstance(item, dict)
        }
        for micro in episode.get("micro_steps") or []:
            basis = micro_basis_by_id.get(_clean(micro.get("step_id")))
            if isinstance(basis, dict):
                micro["derivation_basis"] = basis
    return template


def apply_derivation_spine_to_current_lesson_sections(current_lesson: dict[str, Any], spine: dict[str, Any]) -> None:
    sections = current_lesson.get("sections") or []
    by_id = {
        section_id: section_spine
        for section_id, section_spine in (spine.get("sections") or {}).items()
        if isinstance(section_spine, dict)
    }
    for section in sections:
        section_id = _clean(section.get("id"))
        section_spine = by_id.get(section_id)
        if not isinstance(section_spine, dict):
            continue
        body = _items(section_spine.get("body"))
        if body:
            section["items"] = body
        section["source_status"] = section_spine.get("source_status") or section.get("source_status")
        section["classification"] = section_spine.get("classification") or section.get("classification")
        section["derivation_spine_section_id"] = section_id
        section["source_capsules"] = deepcopy(section_spine.get("source_capsules") or [])
        section["graph_basis"] = deepcopy(section_spine.get("claim_chain") or [])
        section["teacher_review_required"] = True
        section["preview_only"] = True
        section["formal_apply"] = False
