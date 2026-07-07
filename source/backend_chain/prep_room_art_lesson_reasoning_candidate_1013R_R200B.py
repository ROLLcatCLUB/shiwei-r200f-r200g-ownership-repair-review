from __future__ import annotations

import hashlib
import json
import re
import time
from typing import Any


STAGE_ID = "1013R_R200B_ART_LESSON_REASONING_CANDIDATE_PREVIEW"
CANDIDATE_VERSION = "r200b_art_lesson_reasoning_candidate_v1"
SECTION_KEYS = [
    "basis_deepening",
    "student_analysis_deepening",
    "objectives_deepening",
    "key_difficult_points_deepening",
]
SECTION_ALIASES = {
    "basis_deepening": ["basis_deepening", "basis", "lesson_basis", "本课依据", "本课依据候选深化"],
    "student_analysis_deepening": ["student_analysis_deepening", "student_analysis", "learner_analysis", "学情分析", "学情分析候选深化"],
    "objectives_deepening": ["objectives_deepening", "objectives", "teaching_objectives", "教学目标", "教学目标候选深化"],
    "key_difficult_points_deepening": [
        "key_difficult_points_deepening",
        "key_difficult_points",
        "teaching_key_difficult_points",
        "重难点",
        "教学重难点",
        "重难点候选深化",
    ],
}
SOURCE_STATUS_VALUES = {
    "uploaded_source",
    "parser_extracted",
    "model_inference",
    "curriculum_standard_gap",
    "source_gap",
    "teacher_confirm_required",
}


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _truncate(value: Any, limit: int = 420) -> str:
    text = _clean(value)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _items(value: Any, limit: int = 8) -> list[str]:
    if isinstance(value, list):
        return [_truncate(item, 420) for item in value if _clean(item)][:limit]
    text = _truncate(value, 420)
    return [text] if text else []


def _short_id(*parts: Any) -> str:
    text = "|".join(_clean(part) for part in parts)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def _json_clone(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False))


def _first_present(data: dict[str, Any], keys: list[str]) -> Any:
    if not isinstance(data, dict):
        return None
    for key in keys:
        if key in data and data.get(key) not in (None, "", [], {}):
            return data.get(key)
    return None


def _provider_public_status() -> dict[str, Any]:
    try:
        from . import providers

        status = providers.provider_status()
        generation = status.get("generation") or {}
        return {
            "credential_available": bool(status.get("credential_available") or generation.get("credential_available")),
            "provider": generation.get("provider") or status.get("provider_name") or "openai_compatible",
            "model": generation.get("model") or "MiniMax-M3",
            "credential_source": generation.get("credential_source") or status.get("credential_source"),
            "base_url": generation.get("base_url"),
            "provider_family": generation.get("provider_family"),
        }
    except Exception as exc:
        return {
            "credential_available": False,
            "provider": "unavailable",
            "model": "",
            "reason_code": "provider_status_unavailable",
            "safe_message": str(exc)[:300],
        }


def _extract_json(raw_text: str) -> dict[str, Any] | None:
    text = str(raw_text or "").strip()
    if not text:
        return None
    decoder = json.JSONDecoder()
    try:
        parsed, end_index = decoder.raw_decode(text)
        if text[end_index:].strip().strip("`"):
            pass
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass
    for match in re.finditer(r"\{", text):
        try:
            parsed, _ = decoder.raw_decode(text[match.start() :])
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            continue
    return None


def _template_section_body(template: dict[str, Any], key: str) -> list[str]:
    value = template.get(key)
    if not isinstance(value, list) or not value:
        return []
    first = value[0] if isinstance(value[0], dict) else {}
    return _items(first.get("body"), limit=8)


def _lesson_header(template: dict[str, Any]) -> dict[str, str]:
    header = template.get("lesson_header") if isinstance(template.get("lesson_header"), dict) else {}
    return {
        "lesson_title": _clean(header.get("lesson_title")),
        "unit_title": _clean(header.get("unit_title")),
        "grade": _clean(header.get("grade")),
        "lesson_code": _clean(header.get("lesson_code")),
    }


def _template_sections_packet(template: dict[str, Any]) -> dict[str, list[str]]:
    return {
        "basis": _template_section_body(template, "basis"),
        "student_analysis": _template_section_body(template, "student_analysis"),
        "objectives": _template_section_body(template, "objectives"),
        "key_difficult_points": _template_section_body(template, "key_difficult_points"),
        "preparation": _template_section_body(template, "preparation"),
    }


def _episodes_packet(template: dict[str, Any], kernel: dict[str, Any]) -> list[dict[str, Any]]:
    method_by_id = {
        str(item.get("episode_id")): item
        for item in kernel.get("episode_method_map") or []
        if isinstance(item, dict)
    }
    result = []
    for index, episode in enumerate(template.get("process_episodes") or []):
        if not isinstance(episode, dict):
            continue
        episode_id = str(episode.get("episode_id") or f"U{index + 1:02d}")
        method = method_by_id.get(episode_id) or {}
        micro_steps = []
        for micro in episode.get("micro_steps") or []:
            if not isinstance(micro, dict):
                continue
            micro_steps.append(
                {
                    "step_id": micro.get("step_id"),
                    "title": _truncate(micro.get("title") or micro.get("micro_title"), 140),
                    "teacher_action": _truncate(micro.get("teacher_action"), 220),
                    "student_action": _truncate(micro.get("student_action"), 220),
                    "evidence": _truncate(micro.get("evidence"), 180),
                    "source_status": micro.get("provenance") or micro.get("source_status"),
                }
            )
        result.append(
            {
                "episode_id": episode_id,
                "episode_title": _truncate(episode.get("episode_title") or episode.get("title"), 140),
                "time_minutes": episode.get("time_minutes") or episode.get("duration_minutes"),
                "goal": _truncate(episode.get("episode_goal") or episode.get("goal"), 260),
                "teacher_organization": _truncate(episode.get("teacher_organization") or episode.get("teacher_action"), 260),
                "student_learning": _truncate(episode.get("student_learning") or episode.get("student_action"), 260),
                "key_talk": _items(episode.get("key_talk") or episode.get("teacher_talk_suggestions"), limit=3),
                "evidence": _items(episode.get("evidence"), limit=4),
                "pedagogy_move_id": method.get("pedagogy_move_id"),
                "pedagogy_role": method.get("pedagogy_role"),
                "student_state_basis": method.get("student_state_basis"),
                "evidence_basis": method.get("evidence_basis"),
                "micro_steps": micro_steps[:6],
            }
        )
    return result[:10]


def _curriculum_candidate_packet(template: dict[str, Any], standard: dict[str, Any]) -> dict[str, Any]:
    candidate = template.get("curriculum_standard_candidate_preview")
    if not isinstance(candidate, dict):
        candidate = {}
    refs = candidate.get("candidate_refs")
    if not isinstance(refs, list):
        refs = standard.get("candidate_refs") if isinstance(standard.get("candidate_refs"), list) else []
    candidate_refs = []
    for item in refs[:6]:
        if not isinstance(item, dict):
            continue
        candidate_refs.append(
            {
                "slice_id": item.get("slice_id"),
                "section_path": item.get("section_path"),
                "evidence_type": item.get("evidence_type"),
                "grade_band": item.get("grade_band"),
                "field_support_scope": item.get("field_support_scope"),
                "source_locator": item.get("source_locator"),
                "standard_excerpt": _truncate(item.get("standard_excerpt"), 220),
                "candidate_only": True,
                "teacher_review_required": True,
            }
        )
    return {
        "interpretation_status": standard.get("interpretation_status"),
        "official_curriculum_claim_created": standard.get("official_curriculum_claim_created"),
        "real_curriculum_standard_full_text_parsed": standard.get("real_curriculum_standard_full_text_parsed"),
        "missing_required_fields": standard.get("missing_required_fields"),
        "standard_ref_ids": standard.get("standard_ref_ids") or [item.get("slice_id") for item in candidate_refs if item.get("slice_id")],
        "candidate_ref_count": len(candidate_refs),
        "candidate_refs": candidate_refs,
        "source_documents": candidate.get("source_documents") or {},
        "source_integrity": candidate.get("source_integrity") or {},
        "candidate_only": True,
        "teacher_review_required": True,
        "full_standard_text_dumped_to_prompt": False,
    }


def _build_reasoning_packet(
    *,
    single_lesson_template: dict[str, Any],
    lesson_derivation_spine_preview: dict[str, Any],
    art_lesson_design_kernel_preview: dict[str, Any],
) -> dict[str, Any]:
    template = single_lesson_template if isinstance(single_lesson_template, dict) else {}
    kernel = art_lesson_design_kernel_preview if isinstance(art_lesson_design_kernel_preview, dict) else {}
    standard = kernel.get("curriculum_standard_control") if isinstance(kernel.get("curriculum_standard_control"), dict) else {}
    curriculum_candidate = _curriculum_candidate_packet(template, standard)
    return {
        "task": "r200b_art_lesson_reasoning_candidate",
        "candidate_version": CANDIDATE_VERSION,
        "boundary": {
            "candidate_only": True,
            "teacher_review_required": True,
            "preview_only": True,
            "formal_apply": False,
            "database_written": False,
            "write_to_single_lesson_template": False,
            "raw_chain_of_thought_allowed": False,
            "official_curriculum_claim_allowed": False,
        },
        "lesson_header": _lesson_header(template),
        "current_template_sections": _template_sections_packet(template),
        "process_episodes": _episodes_packet(template, kernel),
        "lesson_derivation_spine_preview": {
            "stage": lesson_derivation_spine_preview.get("stage") if isinstance(lesson_derivation_spine_preview, dict) else "",
            "status": lesson_derivation_spine_preview.get("status") if isinstance(lesson_derivation_spine_preview, dict) else "",
            "section_chain": lesson_derivation_spine_preview.get("section_chain") if isinstance(lesson_derivation_spine_preview, dict) else [],
            "process_chain": lesson_derivation_spine_preview.get("process_chain") if isinstance(lesson_derivation_spine_preview, dict) else [],
        },
        "art_lesson_design_kernel_preview": {
            "kernel_id": kernel.get("kernel_id"),
            "kernel_status": kernel.get("kernel_status"),
            "lesson_focus": kernel.get("lesson_focus"),
            "curriculum_standard_control": curriculum_candidate,
            "cross_topic_guard": kernel.get("cross_topic_guard"),
            "lesson_learning_logic": kernel.get("lesson_learning_logic"),
            "art_pedagogy_kernel": kernel.get("art_pedagogy_kernel"),
            "episode_method_map": kernel.get("episode_method_map"),
            "provider_reasoning_packet_preview": kernel.get("provider_reasoning_packet_preview"),
        },
        "required_output": {
            "hard_required_top_level_keys": ["lesson_reasoning", "episode_reasoning", "quality_checks", "source_gaps"],
            "hard_required_lesson_reasoning_keys": SECTION_KEYS,
            "hard_required_episode_micro_key": "micro_steps",
            "lesson_reasoning": {
                "basis_deepening": ["items with text/basis/evidence_ref/source_status/confidence/teacher_review_required"],
                "student_analysis_deepening": ["items with text/basis/evidence_ref/source_status/confidence/teacher_review_required"],
                "objectives_deepening": ["items with text/basis/evidence_ref/source_status/confidence/teacher_review_required"],
                "key_difficult_points_deepening": ["items with text/basis/evidence_ref/source_status/confidence/teacher_review_required"],
            },
            "episode_reasoning": [
                {
                    "episode_id": "string",
                    "episode_title": "string",
                    "episode_weight_minutes": "number or string",
                    "weight_rationale": "why this episode deserves this amount of classroom weight",
                    "micro_steps": [
                        {
                            "title": "string",
                            "teacher_organization": "string",
                            "student_learning": "string",
                            "key_talk": "string",
                            "transition_or_pointing": "string",
                            "evidence_to_watch": "string",
                            "xiaojiao_reminder": "string",
                            "rationale": "string",
                            "source_status": "model_inference/source_gap/teacher_confirm_required",
                            "teacher_review_required": True,
                        }
                    ],
                }
            ],
            "quality_checks": {
                "basis_to_goal_chain": "string",
                "student_analysis_to_microsteps_chain": "string",
                "source_gap_warning": "string",
            },
            "source_gaps": ["string"],
        },
    }


def _call_provider(packet: dict[str, Any], provider_status: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    started = time.perf_counter()
    log: dict[str, Any] = {
        "provider_called": False,
        "model_called": False,
        "status": "not_started",
        "latency_ms": 0,
        "provider_status": provider_status,
        "raw_response_saved": False,
    }
    if not provider_status.get("credential_available"):
        log.update({"status": "fallback", "reason_code": "provider_credentials_missing"})
        return None, log
    system_prompt = (
        "你是小学美术备课室的教学推理候选生成助手，只输出 JSON。"
        "必须返回一个原始 JSON object，不要 markdown code fence，不要解释文字。"
        "你不能输出思维链、不能写过程自白、不能声称已保存或已应用。"
        "任务是在 single_lesson_template、R200A 美术备课内核和推导主干上，生成可审校的候选稿。"
        "JSON key 必须严格使用英文 schema：lesson_reasoning、episode_reasoning、quality_checks、source_gaps；"
        "lesson_reasoning 下必须使用 basis_deepening、student_analysis_deepening、objectives_deepening、key_difficult_points_deepening；"
        "episode_reasoning 每个环节必须使用 micro_steps 数组。"
        "所有新增判断必须标 source_status，未给出课标原文时不得冒充课标结论，只能标 curriculum_standard_gap 或 teacher_confirm_required。"
        "如果输入中有 curriculum_standard_control.candidate_refs，只能作为候选课标依据引用；可在 evidence_ref 写 slice_id 或 source_locator，"
        "但不得写成“课标明确要求”这类正式结论。"
        "必须遵守 art_lesson_design_kernel_preview.cross_topic_guard，不能把 forbidden_terms 写入不对应课题的候选正文。"
        "候选内容要能解释：本课依据如何推出学情、目标、重难点，教学环节为什么这样拆，小步骤为什么出现，哪里是过渡，哪里是点题。"
        "小教提醒只写判断点、追问点和风险点，不重复教师完整话术。"
    )
    try:
        from . import output_parser, providers

        log["provider_called"] = True
        log["model_called"] = True
        result = providers.generate_json_patch(
            {"stage": STAGE_ID, "mode": "art_lesson_reasoning_candidate", "sandbox_only": True, "candidate_only": True},
            {"system_prompt": system_prompt, "user_prompt": json.dumps(packet, ensure_ascii=False)},
            {
                "provider": provider_status.get("provider") or "openai_compatible",
                "model": provider_status.get("model") or "MiniMax-M3",
                "response_format": "json_object",
                "temperature": 0.18,
                "max_tokens": 5200,
                "timeout_ms": 180000,
            },
        )
        raw_text = str(result.get("raw_text") or "")
        provider_meta = dict(result.get("provider_meta") or {})
        parsed = _extract_json(raw_text)
        parser_meta: dict[str, Any] = {"parser_mode": "inline_json_extract", "raw_response_saved": False}
        if parsed is None:
            try:
                parsed, parser_meta = output_parser.parse_patch_output(raw_text, provider_meta)
            except Exception as parse_exc:
                parser_meta = {
                    "parser_mode": "fallback_failed",
                    "parse_error_code": str(getattr(parse_exc, "code", "") or "json_parse_error"),
                    "parse_subcode": str(getattr(parse_exc, "parse_subcode", "") or ""),
                    "raw_response_saved": False,
                }
        log.update(
            {
                "status": "success" if isinstance(parsed, dict) else "fallback",
                "reason_code": None if isinstance(parsed, dict) else "provider_response_not_json",
                "latency_ms": round((time.perf_counter() - started) * 1000),
                "provider_meta": {
                    key: value
                    for key, value in provider_meta.items()
                    if key not in {"token", "api_key", "authorization"}
                },
                "parser_meta": parser_meta,
                "raw_response_length": len(raw_text),
            }
        )
        return parsed if isinstance(parsed, dict) else None, log
    except Exception as exc:
        log.update(
            {
                "status": "fallback",
                "reason_code": str(getattr(exc, "code", "") or "provider_call_failed"),
                "safe_message": str(exc)[:800],
                "latency_ms": round((time.perf_counter() - started) * 1000),
            }
        )
        return None, log


def _call_episode_repair(
    packet: dict[str, Any],
    provider_status: dict[str, Any],
    first_payload: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    started = time.perf_counter()
    log: dict[str, Any] = {
        "provider_called": False,
        "model_called": False,
        "status": "not_started",
        "latency_ms": 0,
        "raw_response_saved": False,
        "repair_reason": "episode_microsteps_missing",
    }
    if not provider_status.get("credential_available"):
        log.update({"status": "fallback", "reason_code": "provider_credentials_missing"})
        return None, log
    repair_packet = {
        "task": "r200b_episode_microstep_repair",
        "boundary": packet.get("boundary") or {},
        "lesson_header": packet.get("lesson_header") or {},
        "process_episodes": packet.get("process_episodes") or [],
        "lesson_reasoning_keys_already_received": sorted(str(key) for key in first_payload.keys()),
        "required_output": {
            "hard_required_top_level_keys": ["episode_reasoning"],
            "episode_reasoning": [
                {
                    "episode_id": "must copy from input process_episodes",
                    "episode_title": "string",
                    "episode_weight_minutes": "number or string",
                    "weight_rationale": "string",
                    "micro_steps": [
                        {
                            "title": "string",
                            "teacher_organization": "string",
                            "student_learning": "string",
                            "key_talk": "string",
                            "transition_or_pointing": "string",
                            "evidence_to_watch": "string",
                            "xiaojiao_reminder": "string",
                            "rationale": "string",
                            "source_status": "model_inference",
                            "teacher_review_required": True,
                        }
                    ],
                }
            ],
        },
    }
    system_prompt = (
        "你是小学美术备课室的 R200B 候选修复助手，只输出一个原始 JSON object。"
        "不要 markdown code fence，不要解释文字，不要思维链。"
        "上一轮候选缺少 episode_reasoning；本轮只补 episode_reasoning。"
        "每个输入环节至少返回 1 个 micro_steps 候选；复杂环节可返回 2 个。"
        "所有内容仍是 candidate-only，teacher_review_required 必须为 true。"
    )
    try:
        from . import output_parser, providers

        log["provider_called"] = True
        log["model_called"] = True
        result = providers.generate_json_patch(
            {"stage": STAGE_ID, "mode": "art_lesson_reasoning_episode_repair", "sandbox_only": True, "candidate_only": True},
            {"system_prompt": system_prompt, "user_prompt": json.dumps(repair_packet, ensure_ascii=False)},
            {
                "provider": provider_status.get("provider") or "openai_compatible",
                "model": provider_status.get("model") or "MiniMax-M3",
                "response_format": "json_object",
                "temperature": 0.12,
                "max_tokens": 3600,
                "timeout_ms": 180000,
            },
        )
        raw_text = str(result.get("raw_text") or "")
        provider_meta = dict(result.get("provider_meta") or {})
        parsed = _extract_json(raw_text)
        parser_meta: dict[str, Any] = {"parser_mode": "inline_json_extract", "raw_response_saved": False}
        if parsed is None:
            try:
                parsed, parser_meta = output_parser.parse_patch_output(raw_text, provider_meta)
            except Exception as parse_exc:
                parser_meta = {
                    "parser_mode": "fallback_failed",
                    "parse_error_code": str(getattr(parse_exc, "code", "") or "json_parse_error"),
                    "parse_subcode": str(getattr(parse_exc, "parse_subcode", "") or ""),
                    "raw_response_saved": False,
                }
        log.update(
            {
                "status": "success" if isinstance(parsed, dict) else "fallback",
                "reason_code": None if isinstance(parsed, dict) else "provider_response_not_json",
                "latency_ms": round((time.perf_counter() - started) * 1000),
                "provider_meta": {
                    key: value
                    for key, value in provider_meta.items()
                    if key not in {"token", "api_key", "authorization"}
                },
                "parser_meta": parser_meta,
                "raw_response_length": len(raw_text),
            }
        )
        return parsed if isinstance(parsed, dict) else None, log
    except Exception as exc:
        log.update(
            {
                "status": "fallback",
                "reason_code": str(getattr(exc, "code", "") or "provider_call_failed"),
                "safe_message": str(exc)[:800],
                "latency_ms": round((time.perf_counter() - started) * 1000),
            }
        )
        return None, log


def _source_status(value: Any) -> str:
    text = _clean(value)
    if text in SOURCE_STATUS_VALUES:
        return text
    if "gap" in text.lower() or "缺口" in text:
        return "source_gap"
    if "confirm" in text.lower() or "确认" in text:
        return "teacher_confirm_required"
    if "curriculum" in text.lower() or "课标" in text:
        return "curriculum_standard_gap"
    if "source" in text.lower() or "原文" in text:
        return "uploaded_source"
    return "model_inference"


def _confidence(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.62
    return max(0.0, min(1.0, round(number, 2)))


def _normalize_reasoning_items(value: Any, *, limit: int = 5) -> list[dict[str, Any]]:
    if isinstance(value, dict) and isinstance(value.get("items"), list):
        raw_items = value.get("items") or []
    elif isinstance(value, list):
        raw_items = value
    elif _clean(value):
        raw_items = [value]
    else:
        raw_items = []
    items = []
    for raw in raw_items:
        if isinstance(raw, dict):
            text = _truncate(raw.get("text") or raw.get("candidate") or raw.get("body") or raw.get("summary"), 360)
            basis = _truncate(raw.get("basis") or raw.get("why") or raw.get("rationale"), 360)
            evidence = _truncate(raw.get("evidence_ref") or raw.get("evidence") or raw.get("source_evidence"), 260)
            status = _source_status(raw.get("source_status") or raw.get("claim_type"))
            confidence = _confidence(raw.get("confidence"))
        else:
            text = _truncate(raw, 360)
            basis = ""
            evidence = ""
            status = "model_inference"
            confidence = 0.58
        if not text:
            continue
        items.append(
            {
                "text": text,
                "basis": basis,
                "evidence_ref": evidence,
                "source_status": status,
                "confidence": confidence,
                "teacher_review_required": True,
                "candidate_only": True,
            }
        )
    return items[:limit]


def _raw_episode_map(model_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result = {}
    raw_episodes = (
        model_payload.get("episode_reasoning")
        or model_payload.get("episodes")
        or model_payload.get("process_reasoning")
        or model_payload.get("teaching_process_reasoning")
        or model_payload.get("教学过程推理")
        or []
    )
    for item in raw_episodes:
        if not isinstance(item, dict):
            continue
        keys = [
            _clean(item.get("episode_id")),
            _clean(item.get("episode_title")),
            _clean(item.get("title")),
            _clean(item.get("环节标题")),
        ]
        for key in keys:
            if key:
                result[key] = item
    return result


def _normalize_micro_steps(raw_micro_steps: Any) -> list[dict[str, Any]]:
    if isinstance(raw_micro_steps, dict):
        nested = _first_present(
            raw_micro_steps,
            ["items", "steps", "micro_steps", "micro_step_candidates", "step_decomposition", "小步骤"],
        )
        raw_micro_steps = nested if isinstance(nested, list) else [raw_micro_steps]
    if not isinstance(raw_micro_steps, list):
        return []
    result = []
    for index, raw in enumerate(raw_micro_steps):
        if not isinstance(raw, dict):
            continue
        title = _truncate(raw.get("title") or raw.get("micro_title") or f"候选小步骤{index + 1}", 120)
        teacher = _truncate(raw.get("teacher_organization") or raw.get("teacher_action") or raw.get("teacher"), 260)
        student = _truncate(raw.get("student_learning") or raw.get("student_action") or raw.get("student"), 260)
        key_talk = _truncate(raw.get("key_talk") or raw.get("teacher_talk"), 260)
        transition = _truncate(raw.get("transition_or_pointing") or raw.get("transition") or raw.get("pointing"), 240)
        evidence = _truncate(raw.get("evidence_to_watch") or raw.get("evidence"), 220)
        reminder = _truncate(raw.get("xiaojiao_reminder") or raw.get("xiaojiao") or raw.get("risk_reminder"), 240)
        rationale = _truncate(raw.get("rationale") or raw.get("why"), 320)
        if not any([teacher, student, key_talk, transition, evidence, reminder, rationale]):
            continue
        result.append(
            {
                "step_id": _clean(raw.get("step_id")) or f"r200b_micro_{index + 1:02d}",
                "title": title,
                "teacher_organization": teacher,
                "student_learning": student,
                "key_talk": key_talk,
                "transition_or_pointing": transition,
                "evidence_to_watch": evidence,
                "xiaojiao_reminder": reminder,
                "rationale": rationale,
                "source_status": _source_status(raw.get("source_status")),
                "confidence": _confidence(raw.get("confidence")),
                "teacher_review_required": True,
                "candidate_only": True,
            }
        )
    return result[:6]


def _normalize_episode_reasoning(model_payload: dict[str, Any], packet: dict[str, Any]) -> list[dict[str, Any]]:
    raw_by_key = _raw_episode_map(model_payload)
    result = []
    for episode in packet.get("process_episodes") or []:
        if not isinstance(episode, dict):
            continue
        raw = raw_by_key.get(_clean(episode.get("episode_id"))) or raw_by_key.get(_clean(episode.get("episode_title"))) or {}
        raw_micro_steps = _first_present(
            raw,
            [
                "micro_steps",
                "micro_step_candidates",
                "microstep_candidates",
                "microsteps",
                "micro_step_reasoning",
                "microstep_reasoning",
                "small_steps",
                "sub_steps",
                "suggested_micro_steps",
                "step_decomposition",
                "step_candidates",
                "decomposed_steps",
                "小步骤",
                "候选小步骤",
                "小步骤拆分",
                "小步骤候选",
                "环节小步骤",
            ],
        ) if isinstance(raw, dict) else []
        if not raw_micro_steps and isinstance(raw, dict):
            has_episode_level_candidate = any(
                _clean(raw.get(key))
                for key in [
                    "teacher_organization",
                    "teacher_action",
                    "student_learning",
                    "student_action",
                    "key_talk",
                    "transition_or_pointing",
                    "evidence_to_watch",
                    "rationale",
                    "weight_rationale",
                ]
            )
            raw_micro_steps = [raw] if has_episode_level_candidate else []
        micro_steps = _normalize_micro_steps(raw_micro_steps)
        result.append(
            {
                "episode_id": episode.get("episode_id"),
                "episode_title": episode.get("episode_title"),
                "episode_weight_minutes": _clean(raw.get("episode_weight_minutes")) if isinstance(raw, dict) else "",
                "weight_rationale": _truncate(raw.get("weight_rationale") if isinstance(raw, dict) else "", 320),
                "pedagogy_basis": {
                    "pedagogy_move_id": episode.get("pedagogy_move_id"),
                    "pedagogy_role": episode.get("pedagogy_role"),
                    "student_state_basis": episode.get("student_state_basis"),
                    "evidence_basis": episode.get("evidence_basis"),
                },
                "micro_step_candidates": micro_steps,
                "source_status": "model_inference" if micro_steps else "source_gap",
                "teacher_review_required": True,
                "candidate_only": True,
            }
        )
    return result


def _deterministic_episode_micro_reasoning(packet: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for episode in packet.get("process_episodes") or []:
        if not isinstance(episode, dict):
            continue
        micro_candidates = []
        source_micro_steps = episode.get("micro_steps") if isinstance(episode.get("micro_steps"), list) else []
        if source_micro_steps:
            for index, micro in enumerate(source_micro_steps[:3]):
                if not isinstance(micro, dict):
                    continue
                title = _truncate(micro.get("title") or f"候选小步骤{index + 1}", 120)
                teacher = _truncate(micro.get("teacher_action") or episode.get("teacher_organization"), 260)
                student = _truncate(micro.get("student_action") or episode.get("student_learning"), 260)
                evidence = _truncate(micro.get("evidence") or episode.get("evidence_basis") or episode.get("evidence"), 220)
                if not any([title, teacher, student, evidence]):
                    continue
                micro_candidates.append(
                    {
                        "step_id": _clean(micro.get("step_id")) or f"{episode.get('episode_id')}-det-{index + 1}",
                        "title": title,
                        "teacher_organization": teacher,
                        "student_learning": student,
                        "key_talk": _truncate(micro.get("key_talk"), 260),
                        "transition_or_pointing": "候选小步骤来自当前模板与教学法内核，需教师确认后再采用。",
                        "evidence_to_watch": evidence,
                        "xiaojiao_reminder": "小教只提示教师观察证据，不替教师确认。",
                        "rationale": _truncate(episode.get("pedagogy_role") or episode.get("student_state_basis"), 320),
                        "source_status": "teacher_confirm_required",
                        "confidence": 0.52,
                        "teacher_review_required": True,
                        "candidate_only": True,
                    }
                )
        if not micro_candidates:
            title = _truncate(episode.get("episode_title") or "本环节推进", 120)
            micro_candidates.append(
                {
                    "step_id": f"{episode.get('episode_id') or title}-det-1",
                    "title": title,
                    "teacher_organization": _truncate(episode.get("teacher_organization") or "把本环节任务转成一个可观察的小动作。", 260),
                    "student_learning": _truncate(episode.get("student_learning") or "完成本环节对应的观察、操作或表达任务。", 260),
                    "key_talk": "",
                    "transition_or_pointing": "候选小步骤来自当前环节目标与教学法内核，需教师确认后再采用。",
                    "evidence_to_watch": _truncate(episode.get("evidence") or episode.get("evidence_basis") or "学生留下口头发现、作品痕迹或交流证据。", 220),
                    "xiaojiao_reminder": "小教只提示教师观察证据，不替教师确认。",
                    "rationale": _truncate(episode.get("pedagogy_role") or "模型未返回环节小步骤，系统仅提供候选修复。", 320),
                    "source_status": "teacher_confirm_required",
                    "confidence": 0.45,
                    "teacher_review_required": True,
                    "candidate_only": True,
                }
            )
        result.append(
            {
                "episode_id": episode.get("episode_id"),
                "episode_title": episode.get("episode_title"),
                "episode_weight_minutes": "",
                "weight_rationale": "模型未返回稳定环节小步骤；本项为模板与教学法内核生成的候选修复，需教师确认。",
                "pedagogy_basis": {
                    "pedagogy_move_id": episode.get("pedagogy_move_id"),
                    "pedagogy_role": episode.get("pedagogy_role"),
                    "student_state_basis": episode.get("student_state_basis"),
                    "evidence_basis": episode.get("evidence_basis"),
                },
                "micro_step_candidates": micro_candidates[:3],
                "source_status": "teacher_confirm_required",
                "teacher_review_required": True,
                "candidate_only": True,
            }
        )
    return result


def _quality_checks(model_payload: dict[str, Any], normalized: dict[str, Any]) -> dict[str, Any]:
    raw_checks = model_payload.get("quality_checks") if isinstance(model_payload.get("quality_checks"), dict) else {}
    section_items = sum(len(value) for value in normalized.get("lesson_reasoning", {}).values() if isinstance(value, list))
    episode_count = len(normalized.get("episode_reasoning") or [])
    micro_count = sum(len(item.get("micro_step_candidates") or []) for item in normalized.get("episode_reasoning") or [])
    return {
        "basis_to_goal_chain": _truncate(raw_checks.get("basis_to_goal_chain"), 420),
        "student_analysis_to_microsteps_chain": _truncate(raw_checks.get("student_analysis_to_microsteps_chain"), 420),
        "source_gap_warning": _truncate(raw_checks.get("source_gap_warning"), 420),
        "section_reasoning_item_count": section_items,
        "episode_reasoning_count": episode_count,
        "micro_step_candidate_count": micro_count,
        "has_deepening_sections": section_items >= 4,
        "has_episode_microsteps": micro_count >= max(1, episode_count),
        "candidate_only_guard": True,
    }


def _candidate_micro_count(candidate: dict[str, Any]) -> int:
    episodes = candidate.get("episode_reasoning") if isinstance(candidate.get("episode_reasoning"), list) else []
    return sum(len(item.get("micro_step_candidates") or []) for item in episodes if isinstance(item, dict))


def _normalize_model_candidate(model_payload: dict[str, Any], packet: dict[str, Any]) -> dict[str, Any]:
    lesson_reasoning_raw = model_payload.get("lesson_reasoning") if isinstance(model_payload.get("lesson_reasoning"), dict) else {}
    if not lesson_reasoning_raw:
        lesson_reasoning_raw = {
            key: value
            for key, value in model_payload.items()
            if key in {alias for aliases in SECTION_ALIASES.values() for alias in aliases}
        }
    lesson_reasoning = {
        key: _normalize_reasoning_items(_first_present(lesson_reasoning_raw, SECTION_ALIASES.get(key, [key])), limit=5)
        for key in SECTION_KEYS
    }
    normalized = {
        "candidate_version": CANDIDATE_VERSION,
        "candidate_type": "art_lesson_reasoning_candidate",
        "candidate_status": "pending_teacher_review",
        "candidate_only": True,
        "teacher_review_required": True,
        "formal_apply_allowed": False,
        "auto_apply_allowed": False,
        "lesson_header": packet.get("lesson_header") or {},
        "lesson_reasoning": lesson_reasoning,
        "episode_reasoning": _normalize_episode_reasoning(model_payload, packet),
        "source_gaps": _items(model_payload.get("source_gaps"), limit=10),
        "source_policy": {
            "model_inference_visible_as_candidate": True,
            "fallback_visible_as_main_text": False,
            "official_curriculum_claim_created": False,
            "teacher_confirmation_required": True,
        },
    }
    normalized["quality_checks"] = _quality_checks(model_payload, normalized)
    return normalized


def _model_payload_shape(model_payload: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(model_payload, dict):
        return {}
    lesson_reasoning = model_payload.get("lesson_reasoning") if isinstance(model_payload.get("lesson_reasoning"), dict) else {}
    episodes = model_payload.get("episode_reasoning") if isinstance(model_payload.get("episode_reasoning"), list) else []
    first_episode = episodes[0] if episodes and isinstance(episodes[0], dict) else {}
    return {
        "top_level_keys": sorted(str(key) for key in model_payload.keys())[:40],
        "lesson_reasoning_keys": sorted(str(key) for key in lesson_reasoning.keys())[:40],
        "first_episode_keys": sorted(str(key) for key in first_episode.keys())[:40],
        "first_episode_micro_keys": sorted(
            str(key)
            for key in (
                (
                    first_episode.get("micro_steps")
                    or first_episode.get("micro_step_candidates")
                    or first_episode.get("small_steps")
                    or []
                )[0].keys()
                if isinstance(
                    (
                        first_episode.get("micro_steps")
                        or first_episode.get("micro_step_candidates")
                        or first_episode.get("small_steps")
                        or []
                    ),
                    list,
                )
                and (
                    first_episode.get("micro_steps")
                    or first_episode.get("micro_step_candidates")
                    or first_episode.get("small_steps")
                    or []
                )
                and isinstance(
                    (
                        first_episode.get("micro_steps")
                        or first_episode.get("micro_step_candidates")
                        or first_episode.get("small_steps")
                        or []
                    )[0],
                    dict,
                )
                else []
            )
        )[:40],
    }


def build_art_lesson_reasoning_candidate_preview(
    *,
    single_lesson_template: dict[str, Any],
    lesson_derivation_spine_preview: dict[str, Any],
    art_lesson_design_kernel_preview: dict[str, Any],
    enable_model: bool = False,
) -> dict[str, Any]:
    template = single_lesson_template if isinstance(single_lesson_template, dict) else {}
    kernel = art_lesson_design_kernel_preview if isinstance(art_lesson_design_kernel_preview, dict) else {}
    packet = _build_reasoning_packet(
        single_lesson_template=template,
        lesson_derivation_spine_preview=lesson_derivation_spine_preview if isinstance(lesson_derivation_spine_preview, dict) else {},
        art_lesson_design_kernel_preview=kernel,
    )
    candidate_id = f"r200b_candidate_{_short_id(template.get('template_id'), packet.get('lesson_header'), kernel.get('kernel_id'))}"
    provider_status = _provider_public_status()
    model_payload: dict[str, Any] | None = None
    model_log: dict[str, Any] = {
        "provider_called": False,
        "model_called": False,
        "status": "disabled",
        "reason_code": "R200B_model_not_enabled",
        "provider_status": provider_status,
        "raw_response_saved": False,
    }
    if enable_model:
        model_payload, model_log = _call_provider(packet, provider_status)
    candidate = _normalize_model_candidate(model_payload, packet) if isinstance(model_payload, dict) else {}
    if enable_model and isinstance(model_payload, dict) and candidate and _candidate_micro_count(candidate) == 0:
        repair_payload, repair_log = _call_episode_repair(packet, provider_status, model_payload)
        model_log["episode_repair_attempted"] = True
        model_log["episode_repair_log"] = repair_log
        if isinstance(repair_payload, dict) and repair_payload.get("episode_reasoning"):
            model_payload = {
                **model_payload,
                "episode_reasoning": repair_payload.get("episode_reasoning"),
            }
            candidate = _normalize_model_candidate(model_payload, packet)
            model_log["episode_repair_applied"] = _candidate_micro_count(candidate) > 0
        if candidate and _candidate_micro_count(candidate) == 0:
            candidate["episode_reasoning"] = _deterministic_episode_micro_reasoning(packet)
            candidate["quality_checks"] = _quality_checks(model_payload or {}, candidate)
            model_log["episode_deterministic_repair_applied"] = _candidate_micro_count(candidate) > 0
    else:
        model_log["episode_repair_attempted"] = False
        model_log["episode_repair_applied"] = False
        model_log["episode_deterministic_repair_applied"] = False
    if not enable_model:
        status = "disabled"
    elif not provider_status.get("credential_available"):
        status = "provider_credentials_missing"
    elif candidate:
        status = "model_success"
    else:
        status = "model_fallback"
    return {
        "stage": STAGE_ID,
        "candidate_id": candidate_id,
        "status": status,
        "candidate_available": bool(candidate),
        "candidate": candidate,
        "model_quality_enabled": bool(enable_model),
        "provider_called": bool(model_log.get("provider_called")),
        "model_called": bool(model_log.get("model_called")),
        "model_log": model_log,
        "input_contract": {
            "uses_single_lesson_template": True,
            "uses_lesson_derivation_spine": True,
            "uses_art_lesson_design_kernel": True,
            "raw_text_used": False,
            "raw_chain_of_thought_requested": False,
            "renderer_may_apply_candidate": False,
        },
        "provider_reasoning_packet_preview": {
            "packet_id": f"r200b_packet_{_short_id(packet)}",
            "candidate_only": True,
            "teacher_review_required": True,
            "included_keys": sorted(packet.keys()),
            "process_episode_count": len(packet.get("process_episodes") or []),
            "curriculum_candidate_ref_count": len(
                (((packet.get("art_lesson_design_kernel_preview") or {}).get("curriculum_standard_control") or {}).get("candidate_refs") or [])
            ),
            "curriculum_source_documents_included": bool(
                (((packet.get("art_lesson_design_kernel_preview") or {}).get("curriculum_standard_control") or {}).get("source_documents") or {})
            ),
            "cross_topic_guard_included": isinstance(
                (packet.get("art_lesson_design_kernel_preview") or {}).get("cross_topic_guard"),
                dict,
            ),
        },
        "model_payload_shape": _model_payload_shape(model_payload),
        "teacher_review_required": True,
        "preview_only": True,
        "formal_apply": False,
        "boundary": {
            "preview_only": True,
            "candidate_only": True,
            "teacher_review_required": True,
            "provider_called": bool(model_log.get("provider_called")),
            "model_called": bool(model_log.get("model_called")),
            "formal_apply_performed": False,
            "database_written": False,
            "memory_written": False,
            "feishu_written": False,
            "single_lesson_template_written": False,
            "current_lesson_sections_overwritten": False,
            "official_curriculum_claim_created": False,
            "raw_chain_of_thought_exposed": False,
            "R21_modified": False,
            "R36_modified": False,
            "R95_executed": False,
        },
    }
