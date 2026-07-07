from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any


STAGE_ID = "1013R_R200A_ART_LESSON_DESIGN_KERNEL_PREVIEW"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _items(value: Any) -> list[str]:
    if isinstance(value, list):
        return [_clean(item) for item in value if _clean(item)]
    text = _clean(value)
    return [text] if text else []


def _short_id(*parts: Any) -> str:
    text = "|".join(_clean(part) for part in parts)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]


def _load_json(relative_path: str) -> dict[str, Any]:
    path = _repo_root() / relative_path
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _template_body(template: dict[str, Any], key: str) -> list[str]:
    value = template.get(key)
    if not isinstance(value, list) or not value:
        return []
    first = value[0] if isinstance(value[0], dict) else {}
    return _items(first.get("body"))


def _lesson_header(template: dict[str, Any]) -> dict[str, str]:
    header = template.get("lesson_header") if isinstance(template.get("lesson_header"), dict) else {}
    return {
        "lesson_title": _clean(header.get("lesson_title")),
        "unit_title": _clean(header.get("unit_title")),
        "grade": _clean(header.get("grade")),
        "lesson_code": _clean(header.get("lesson_code")),
    }


def _grade_band(grade: str) -> str:
    text = grade or ""
    if any(token in text for token in ["一", "二", "1", "2"]):
        return "1-2"
    if any(token in text for token in ["三", "四", "3", "4"]):
        return "3-4"
    if any(token in text for token in ["五", "六", "5", "6"]):
        return "5-6"
    return "grade_band_needs_teacher_confirmation"


def _lesson_focus(header: dict[str, str], template: dict[str, Any]) -> dict[str, Any]:
    lesson_title = header.get("lesson_title", "")
    title_text = " ".join([lesson_title, header.get("unit_title", "")])
    haystack = " ".join(
        [
            title_text,
            " ".join(_template_body(template, "basis")),
            " ".join(
                _clean(episode.get("episode_title"))
                for episode in template.get("process_episodes") or []
                if isinstance(episode, dict)
            ),
        ]
    )
    shoe_observation_keywords = ["足下生辉", "画画鞋", "鞋", "靴", "写生", "正面", "侧面", "后面", "鞋底", "鞋面", "鞋带"]
    if any(keyword in title_text for keyword in ["足下生辉", "画画鞋", "鞋", "靴"]) or (
        any(keyword in haystack for keyword in ["鞋", "靴", "鞋底", "鞋面", "鞋带"])
        and any(keyword in haystack for keyword in ["观察", "写生", "正面", "侧面", "后面", "角度", "局部"])
    ):
        return {
            "focus_id": "shoe_observation_drawing_expression",
            "description": "生活物品观察、角度比较、结构细节记录与线描表达",
            "learning_domain": "造型表现 / 欣赏评述",
            "matched_keywords": [keyword for keyword in shoe_observation_keywords if keyword in haystack],
        }
    if any(keyword in title_text for keyword in ["青绿山水", "千里江山", "山水"]) or (
        "青绿" in haystack and any(keyword in haystack for keyword in ["山水", "传统", "矿物", "石青", "石绿", "水墨"])
    ):
        keywords = ["青绿山水", "千里江山", "山水", "传统", "矿物", "石青", "石绿", "水墨"]
        return {
            "focus_id": "ink_or_traditional_color_exploration",
            "description": "传统青绿山水观察、材料层次试探与文化感受",
            "learning_domain": "造型表现 / 欣赏评述 / 文化理解",
            "matched_keywords": [keyword for keyword in keywords if keyword in haystack],
        }
    if any(keyword in haystack for keyword in ["穿穿编编", "编织", "经纬", "纸条", "穿编", "交织"]):
        keywords = ["穿穿编编", "编织", "经纬", "纸条", "穿编", "交织"]
        return {
            "focus_id": "paper_weaving_structure_expression",
            "description": "纸条穿编、经纬结构观察、纹样秩序与手工表达",
            "learning_domain": "设计应用 / 造型表现",
            "matched_keywords": [keyword for keyword in keywords if keyword in haystack],
        }
    if any(keyword in lesson_title for keyword in ["旧鞋", "变废为宝", "材料", "拼装", "改造"]):
        return {
            "focus_id": "material_transformation_expression",
            "description": "材料观察、结构转换、创意表达与安全操作",
            "learning_domain": "综合探索 / 造型表现",
            "matched_keywords": [keyword for keyword in ["旧鞋", "变废为宝", "材料", "拼装", "改造"] if keyword in lesson_title],
        }
    if any(keyword in lesson_title for keyword in ["海洋", "生命", "动物", "环保"]):
        return {
            "focus_id": "theme_observation_expression",
            "description": "主题观察、形象特征提取、表达与交流",
            "learning_domain": "欣赏评述 / 综合探索 / 造型表现",
            "matched_keywords": [keyword for keyword in ["海洋", "生命", "动物", "环保"] if keyword in lesson_title],
        }
    if any(keyword in title_text for keyword in ["旧鞋", "变废为宝", "材料", "拼装", "改造"]):
        return {
            "focus_id": "material_transformation_expression",
            "description": "材料观察、结构转换、创意表达与安全操作",
            "learning_domain": "综合探索 / 造型表现",
            "matched_keywords": [keyword for keyword in ["旧鞋", "变废为宝", "材料", "拼装", "改造"] if keyword in title_text],
        }
    rules = [
        (
            "shoe_observation_drawing_expression",
            shoe_observation_keywords,
            "生活物品观察、角度比较、结构细节记录与线描表达",
            "造型表现 / 欣赏评述",
        ),
        (
            "ink_or_traditional_color_exploration",
            ["水墨", "墨", "青绿山水", "千里江山"],
            "传统色彩或水墨材料的层次试探与文化感受",
            "造型表现 / 文化理解",
        ),
        (
            "paper_weaving_structure_expression",
            ["穿穿编编", "编织", "经纬", "纸条", "穿编", "交织"],
            "纸条穿编、经纬结构观察、纹样秩序与手工表达",
            "设计应用 / 造型表现",
        ),
        (
            "color_gradation_expression",
            ["渐变", "色阶", "冷暖", "色彩", "颜色"],
            "色彩观察、比较、过渡表现与作品交流",
            "造型表现 / 欣赏评述",
        ),
        (
            "material_transformation_expression",
            ["旧鞋", "变废为宝", "材料", "拼装", "改造"],
            "材料观察、结构转换、创意表达与安全操作",
            "综合探索 / 造型表现",
        ),
        (
            "theme_observation_expression",
            ["海洋", "生命", "动物", "环保"],
            "主题观察、形象特征提取、表达与交流",
            "欣赏评述 / 综合探索 / 造型表现",
        ),
    ]
    for focus_id, keywords, description, domain in rules:
        if any(keyword in haystack for keyword in keywords):
            return {
                "focus_id": focus_id,
                "description": description,
                "learning_domain": domain,
                "matched_keywords": [keyword for keyword in keywords if keyword in haystack],
            }
    return {
        "focus_id": "general_art_expression",
        "description": "观察、方法尝试、作品表达与交流评价",
        "learning_domain": "造型表现 / 欣赏评述",
        "matched_keywords": [],
    }


def _pedagogy_moves_for_focus(focus_id: str) -> list[dict[str, str]]:
    common = [
        {
            "move_id": "visual_perception",
            "teacher_label": "看见现象",
            "rule": "先让学生说出可见现象，再抽出本课关键词。",
        },
        {
            "move_id": "method_probe",
            "teacher_label": "试出方法",
            "rule": "用短任务让学生亲手试材料或方法，避免只听概念。",
        },
        {
            "move_id": "expression_task",
            "teacher_label": "完成表达",
            "rule": "把方法收束为可完成的作品、练习或学习单证据。",
        },
        {
            "move_id": "critique_with_evidence",
            "teacher_label": "带证据交流",
            "rule": "展评时要求学生指出作品中的一个可见证据。",
        },
    ]
    focus_specific = {
        "color_gradation_expression": [
            {
                "move_id": "color_transition_control",
                "teacher_label": "控制过渡",
                "rule": "用相邻色阶、叠色、推开或浓淡变化支撑自然过渡，防止直接跳色。",
            }
        ],
        "ink_or_traditional_color_exploration": [
            {
                "move_id": "material_layering",
                "teacher_label": "控制材料层次",
                "rule": "先试浓淡、干湿或叠加，再进入完整作品表达。",
            }
        ],
        "material_transformation_expression": [
            {
                "move_id": "structure_rebuild",
                "teacher_label": "重组结构",
                "rule": "先判断材料形态和连接方式，再设计改造动作。",
            }
        ],
        "theme_observation_expression": [
            {
                "move_id": "feature_extract",
                "teacher_label": "提取特征",
                "rule": "先观察形象、环境或主题特征，再进入表达任务。",
            }
        ],
        "shoe_observation_drawing_expression": [
            {
                "move_id": "angle_structure_observation",
                "teacher_label": "观察角度和结构",
                "rule": "先比较鞋的正面、侧面、后面或局部特征，再把轮廓、比例和细节转成线条表达。",
            }
        ],
        "paper_weaving_structure_expression": [
            {
                "move_id": "warp_weft_structure_probe",
                "teacher_label": "试出经纬结构",
                "rule": "先让学生用纸条体验一上一下的穿插关系，再把经纬秩序转成纹样和作品证据。",
            }
        ],
    }
    return [*common, *focus_specific.get(focus_id, [])]


def _method_for_episode(title: str, index: int, total: int, focus_id: str) -> dict[str, str]:
    text = title or ""
    if any(token in text for token in ["导入", "引入", "回顾"]):
        move = "visual_perception"
        role = "先唤起经验或观察对象，建立本课问题。"
    elif any(token in text for token in ["展评", "分享", "交流", "展示", "小结", "预告"]):
        move = "critique_with_evidence"
        role = "用学生作品和语言作为评价证据，完成回看和修订。"
    elif any(token in text for token in ["认识", "观察", "欣赏", "感知"]):
        move = "visual_perception"
        role = "让学生把看到的现象说清楚，为方法尝试提供依据。"
    elif any(token in text for token in ["探索", "尝试", "练习", "实践", "制作", "改造", "拼装", "上色"]):
        move = "method_probe" if index < total - 2 else "expression_task"
        role = "把观察转成手上操作，并形成可观察的作品或练习证据。"
    elif any(token in text for token in ["示范"]):
        move = "method_probe"
        role = "教师只示范关键难点，避免替学生完成表达。"
    else:
        move = "expression_task" if index >= max(total - 2, 0) else "method_probe"
        role = "按原文顺序推进，但具体方法依据需教师确认。"
    if focus_id == "color_gradation_expression" and move in {"method_probe", "expression_task"}:
        role += " 本课还要检查颜色是否形成逐步过渡。"
    if focus_id == "ink_or_traditional_color_exploration" and move in {"visual_perception", "method_probe", "expression_task"}:
        role += " 本课还要检查学生是否能把青绿山水的色彩层次、材料感受和画面意境联系起来。"
    if focus_id == "shoe_observation_drawing_expression" and move in {"visual_perception", "method_probe", "expression_task"}:
        role += " 本课还要检查学生是否根据观察角度、鞋面结构和局部细节推进表达。"
    if focus_id == "paper_weaving_structure_expression" and move in {"visual_perception", "method_probe", "expression_task"}:
        role += " 本课还要检查学生是否理解经纬穿插关系，并能用纸条秩序形成纹样或小作品。"
    return {"move_id": move, "role": role}


def _standard_control(header: dict[str, str], focus: dict[str, Any]) -> dict[str, Any]:
    contract = _load_json(
        "outputs/PREP_ROOM_RENDER_CANVAS_DEEPEN_V1/"
        "1013I_R6C_curriculum_standard_control_layer_contract/"
        "curriculum_standard_control_layer_contract_1013I_R6C.json"
    )
    required_fields = [
        item.get("field")
        for item in contract.get("required_control_fields", [])
        if isinstance(item, dict) and item.get("field")
    ]
    grade_band = _grade_band(header.get("grade", ""))
    missing = [
        "standard_version_label",
        "standard_ref_ids",
        "academic_quality_or_performance_evidence",
    ]
    if grade_band == "grade_band_needs_teacher_confirmation":
        missing.append("grade_band")
    return {
        "control_layer": "curriculum_standard_control_layer",
        "inherits_from": contract.get("stage") or "1013I_R6C_CURRICULUM_STANDARD_CONTROL_LAYER_CONTRACT",
        "standard_version_label": "missing_structured_standard_ref",
        "subject": "美术",
        "school_stage": "小学",
        "grade_band": grade_band,
        "art_domain_or_learning_domain": focus.get("learning_domain"),
        "core_literacy_tags": ["审美感知", "艺术表现", "创意实践", "文化理解"],
        "learning_task_direction": ["观察", "比较", "方法尝试", "作品表达", "交流评价"],
        "assessment_requirement": "观察学生能否说清发现、完成作品或练习，并用可见证据说明选择。",
        "academic_quality_or_performance_evidence": "candidate_pending_real_standard_ref",
        "content_scope_boundary": "小学美术课堂可理解、可操作、可表达；不越级引入成人化理论。",
        "prohibited_overreach": [
            "不得伪造课标原文。",
            "不得把案例或模型候选当作课标。",
            "不得在缺少结构化课标引用时直接标为正式课标依据。",
        ],
        "standard_ref_ids": [],
        "missing_required_fields": missing,
        "required_control_fields": required_fields,
        "interpretation_status": "missing_structured_standard_ref",
        "teacher_confirmation_status": "pending_teacher_confirm",
        "official_curriculum_claim_created": False,
        "real_curriculum_standard_full_text_parsed": False,
        "teacher_review_required": True,
    }


def _line_mentions_gap(line: str) -> bool:
    return any(token in line for token in ["教材版本", "册次", "页码", "学校实际进度", "进入正式备课前需教师核对"])


def _line_is_duplicate_position(line: str, header: dict[str, str]) -> bool:
    title = header.get("lesson_title", "")
    unit = header.get("unit_title", "")
    if "所属学习位置" in line or "学习位置为" in line:
        return bool(title and title in line) or bool(unit and unit in line)
    return False


def _basis_identity_line(header: dict[str, str], focus: dict[str, Any], existing: list[str]) -> str:
    title = header.get("lesson_title") or "本课"
    unit = header.get("unit_title") or ""
    for line in existing:
        if "围绕" in line and (title in line or "本课是" in line or "本课定位" in line):
            return line
    unit_part = f"“{unit}”中的" if unit else ""
    return f"本课定位为{unit_part}《{title}》。"


def _basis_focus_line(header: dict[str, str], focus: dict[str, Any]) -> str:
    focus_id = str(focus.get("focus_id") or "")
    if focus_id == "shoe_observation_drawing_expression":
        return (
            "本课的学习重心，是让学生从熟悉的鞋出发，比较不同角度的外形、结构和局部细节，"
            "再用线条、形状和画面组织把观察发现表达出来。"
        )
    if focus_id == "color_gradation_expression":
        return "本课的学习重心，是让学生看见颜色逐步变化的现象，并通过试色、叠色或浓淡控制表现自然过渡。"
    if focus_id == "ink_or_traditional_color_exploration":
        return "本课的学习重心，是让学生从青绿山水图像进入，感受传统色彩、矿物材料和画面层次，再用短任务表达观察发现。"
    if focus_id == "paper_weaving_structure_expression":
        return "本课的学习重心，是让学生通过纸条穿插体验经纬结构，理解一上一下的编织秩序，并把秩序转化为纹样或小作品。"
    if focus_id == "material_transformation_expression":
        return "本课的学习重心，是让学生判断材料形态与主题形象之间的关系，再通过剪贴、拼摆或连接形成有意图的作品。"
    if focus_id == "theme_observation_expression":
        return "本课的学习重心，是让学生从主题对象或生活情境中提取可见特征，并把观察发现转化为作品表达和交流证据。"
    return "本课的学习重心，是把观察、方法尝试、作品表达和交流评价连成一条可验证的课堂过程。"


def _line_conflicts_focus(line: str, focus_id: str) -> bool:
    if focus_id == "shoe_observation_drawing_expression":
        return any(token in line for token in ["渐变", "色阶", "颜色逐步", "逐步过渡", "直接跳色", "平涂", "青绿山水"])
    if focus_id == "color_gradation_expression":
        return any(token in line for token in ["鞋底", "鞋面", "鞋带", "不同角度的鞋", "鞋的结构"])
    if focus_id == "ink_or_traditional_color_exploration":
        return any(token in line for token in ["足下生辉", "鞋底", "鞋面", "鞋带", "海洋生物", "废旧材料"])
    if focus_id == "paper_weaving_structure_expression":
        return any(token in line for token in ["足下生辉", "鞋底", "鞋面", "青绿山水", "海洋生物", "渐变", "色阶"])
    return False


def _cross_topic_forbidden_terms(focus_id: str) -> list[str]:
    if focus_id == "shoe_observation_drawing_expression":
        return ["色彩的渐变", "渐变", "色阶", "颜色逐步", "逐步过渡", "直接跳色", "青绿山水", "石青", "石绿"]
    if focus_id == "color_gradation_expression":
        return ["足下生辉", "鞋底", "鞋面", "鞋带", "不同角度的鞋", "鞋的结构", "画画鞋"]
    if focus_id == "ink_or_traditional_color_exploration":
        return ["足下生辉", "鞋底", "鞋面", "鞋带", "海洋生物", "废旧材料"]
    if focus_id == "paper_weaving_structure_expression":
        return ["足下生辉", "鞋底", "鞋面", "青绿山水", "海洋生物", "渐变", "色阶"]
    if focus_id == "material_transformation_expression":
        return ["色彩的渐变", "色阶练习", "青绿色阶", "足下生辉", "画画鞋"]
    if focus_id == "theme_observation_expression":
        return ["色彩的渐变", "色阶练习", "足下生辉", "画画鞋"]
    return []


def _text_items(value: Any) -> list[str]:
    if isinstance(value, str):
        return [_clean(value)] if _clean(value) else []
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            result.extend(_text_items(item))
        return result
    if isinstance(value, dict):
        result = []
        for key in [
            "body",
            "items",
            "text",
            "value",
            "episode_title",
            "episode_goal",
            "teacher_organization",
            "student_learning",
            "key_talk",
            "evidence",
            "title",
            "step_name",
            "teacher_action",
            "student_action",
            "screen_or_materials",
            "scaffolds",
        ]:
            if key in value:
                result.extend(_text_items(value.get(key)))
        return result
    return []


def _cross_topic_guard_for_template(template: dict[str, Any], focus: dict[str, Any]) -> dict[str, Any]:
    focus_id = str(focus.get("focus_id") or "")
    forbidden_terms = _cross_topic_forbidden_terms(focus_id)
    hits: list[dict[str, str]] = []
    if forbidden_terms:
        scan_targets: list[tuple[str, Any]] = []
        for section_key in ["basis", "student_analysis", "objectives", "key_difficult_points"]:
            scan_targets.append((section_key, template.get(section_key)))
        for episode in template.get("process_episodes") or []:
            if isinstance(episode, dict):
                episode_id = str(episode.get("episode_id") or "episode")
                scan_targets.append((f"episode:{episode_id}", episode))
                for micro in episode.get("micro_steps") or []:
                    if isinstance(micro, dict):
                        scan_targets.append((f"micro:{episode_id}:{micro.get('step_id') or ''}", micro))
        for location, value in scan_targets:
            for text in _text_items(value):
                for term in forbidden_terms:
                    if term and term in text:
                        hits.append({"location": location, "term": term, "text": text[:180]})
    return {
        "guard_id": "r200a_cross_topic_visible_text_guard",
        "focus_id": focus_id,
        "forbidden_terms": forbidden_terms,
        "hit_count": len(hits),
        "hits": hits[:20],
        "passed": len(hits) == 0,
        "teacher_review_required": bool(hits),
        "preview_only": True,
    }


def _refined_basis_body(header: dict[str, str], focus: dict[str, Any], old_body: list[str]) -> tuple[list[str], list[str]]:
    notes = []
    body = []
    focus_id = str(focus.get("focus_id") or "")
    for line in old_body:
        if _line_mentions_gap(line):
            notes.append(line)
            continue
        if _line_conflicts_focus(line, focus_id):
            notes.append(f"已降级为焦点不匹配提示：{line}")
            continue
        if _line_is_duplicate_position(line, header):
            notes.append(f"已降级为位置来源提示：{line}")
            continue
        if "承接" in line and "前序" in line:
            body.append(line)
            continue
    identity = _basis_identity_line(header, focus, old_body)
    body.append(identity)
    body.append(_basis_focus_line(header, focus))
    # Keep one non-duplicated source line if it carries a concrete activity and is not the identity line.
    for line in old_body:
        if (
            line in body
            or _line_mentions_gap(line)
            or _line_is_duplicate_position(line, header)
            or _line_conflicts_focus(line, focus_id)
        ):
            continue
        if "定位" in line and ("所属单元" in line or "《" in line):
            notes.append(f"已降级为定位来源提示：{line}")
            continue
        if any(token in line for token in ["任务", "活动", "材料", "作品", "方法", "表达", "表现", "观察", "尝试"]) and len(body) < 3:
            if "本课的学习重心" in line:
                notes.append(f"已降级为旧理解链重复提示：{line}")
                continue
            body.append(line)
    deduped = []
    seen = set()
    for line in body:
        key = re.sub(r"[《》“”\"'\s，。；;：:、]", "", line)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(line)
    return deduped[:3], notes


def _grade_cognition_line(header: dict[str, str]) -> str:
    grade = header.get("grade") or "三年级"
    if "三" in grade or "3" in grade or "年级待确认" in grade or "上传原文未提供" in grade:
        return (
            "三年级学生通常能从生活经验、直观图片和具体材料出发，说出看到的形象、颜色或材料特征，"
            "但把观察发现、方法选择和作品意图连成一段完整说明还不稳定。"
        )
    return "本年段学生的认知水平、表达方式和材料操作基础仍需结合班级实际确认。"


def _prior_experience_line(header: dict[str, str], focus_id: str, old_basis: list[str]) -> str:
    joined = " ".join([header.get("lesson_title", ""), header.get("unit_title", ""), *old_basis])
    if focus_id == "shoe_observation_drawing_expression" or any(token in joined for token in ["足下生辉", "画画鞋", "鞋"]):
        return "前置经验上，学生已有生活中观察鞋、图像观察和基础线描经验；本课要把熟悉物品推进到有角度、有结构、有细节的观察写生。"
    if "变废为宝" in joined or "旧鞋" in joined:
        return "前置经验上，学生已接触海洋主题观察或前序设计草图，能提出初步想法；本课要把草图、材料观察和制作表达连接起来。"
    if focus_id == "color_gradation_expression" or "色阶" in joined or "渐变" in joined:
        return "前置经验上，学生可能已经观察过颜色深浅、冷暖或相近色变化；本课要把直观感受推进到色阶、浓淡或渐变控制。"
    if focus_id == "ink_or_traditional_color_exploration" or "青绿" in joined:
        return "前置经验上，学生可能已有山水画、传统色彩或图像观察经验；本课要把初步感受推进到画面色彩、空间和意境的观察表达。"
    if focus_id == "paper_weaving_structure_expression" or any(token in joined for token in ["穿穿编编", "编织", "经纬", "纸条"]):
        return "前置经验上，学生可能已有折纸、剪纸或简单手工经验；本课要把零散操作推进到理解经纬穿插、纸条排列和纹样秩序。"
    if "海洋" in joined:
        return "前置经验上，学生多半有海洋动物或海洋环境的生活印象；本课要把零散印象推进到特征观察和主题表达。"
    if focus_id == "material_transformation_expression":
        return "前置经验上，学生可能已有剪贴、拼摆或材料收集经验；本课要把这些经验转成有意图的美术表达。"
    return "前置经验上，学生已有的生活观察、图像经验和材料经验需要教师结合本单元前课进一步确认。"


def _content_difficulty_line(focus_id: str) -> str:
    if focus_id == "shoe_observation_drawing_expression":
        return "本课难点在于学生能否从不同角度看出鞋的外形比例、鞋面结构、鞋底方向和局部细节，并避免凭记忆画成符号化的鞋。"
    if focus_id == "material_transformation_expression":
        return "本课难点不只是完成手工作品，而是让学生判断材料形态、连接方式和海洋生物特征之间的关系，避免材料堆砌。"
    if focus_id == "color_gradation_expression":
        return "本课难点在于学生能否理解颜色是逐步过渡的，并在操作中避免直接跳色、平涂或只追求颜色好看。"
    if focus_id == "ink_or_traditional_color_exploration":
        return "本课难点在于学生能否从青绿山水中看见色彩层次、材料质感和画面空间，而不是只把作品理解成绿色山水图。"
    if focus_id == "paper_weaving_structure_expression":
        return "本课难点在于学生能否理解经纬纸条一上一下的穿插规律，并在操作中保持排列顺序、松紧和纹样变化。"
    if focus_id == "theme_observation_expression":
        return "本课难点在于学生能否从海洋主题的直观印象中提取形象、环境或保护问题，并转化为作品表达。"
    return "本课难点在于学生能否把看到的现象、尝试的方法和最终作品效果联系起来说明。"


def _technique_level_line(focus_id: str) -> str:
    if focus_id == "shoe_observation_drawing_expression":
        return "绘画与表现基础上，学生能画出熟悉物品的大致轮廓，但比例、遮挡、局部纹样和线条轻重需要观察提示、局部示范和巡视反馈。"
    if focus_id == "material_transformation_expression":
        return "技法与材料基础上，学生有基础剪贴、拼摆和简单连接经验，但安全切割、结构稳定、材料服务造型意图仍需要教师示范和巡视支架。"
    if focus_id == "color_gradation_expression":
        return "技法与表现基础上，学生能进行基本涂画或试色，但水分、浓淡、叠色和色阶连续控制需要分步示范与短练习。"
    if focus_id == "ink_or_traditional_color_exploration":
        return "材料与表现基础上，学生能观察颜色和画面大关系，但对石青、石绿、墨色浓淡和层次叠加的控制需要短示范与试探。"
    if focus_id == "paper_weaving_structure_expression":
        return "手工基础上，学生能剪贴和折叠纸张，但连续穿插、压住经线、保持纸条间距和形成纹样需要步骤提示与巡视纠偏。"
    if focus_id == "theme_observation_expression":
        return "绘画与表达基础上，学生能画出熟悉形象的大致外形，但特征提取、画面组织和用语言说明选择仍需要支架。"
    return "技法与表现基础上，学生能完成基础造型或涂画，但方法选择、细节调整和作品说明仍需课堂支架。"


def _real_class_gap_line(focus_id: str) -> str:
    if focus_id == "shoe_observation_drawing_expression":
        return "真实学情缺口：本班学生的观察写生经验、线描控制水平、是否能带鞋或使用图片观察，上传原文未充分提供，需教师确认。"
    if focus_id == "material_transformation_expression":
        return "真实学情缺口：本班学生的工具安全习惯、废旧材料准备情况、前序草图完成度和合作制作经验，上传原文未充分提供，需教师确认。"
    if focus_id == "ink_or_traditional_color_exploration":
        return "真实学情缺口：本班学生的传统山水图像经验、颜料使用经验和对青绿材料的感受基础，上传原文未充分提供，需教师确认。"
    if focus_id == "paper_weaving_structure_expression":
        return "真实学情缺口：本班学生剪纸条、保持间距、连续穿插和处理纸张松紧的经验，上传原文未充分提供，需教师确认。"
    return "真实学情缺口：本班学生的前序作品、材料熟练度、表达水平和课堂支持需求，上传原文未充分提供，需教师确认。"


def _refined_student_analysis_body(header: dict[str, str], focus: dict[str, Any], old_basis: list[str]) -> list[str]:
    focus_id = str(focus.get("focus_id") or "")
    return [
        _grade_cognition_line(header),
        _prior_experience_line(header, focus_id, old_basis),
        _content_difficulty_line(focus_id),
        _technique_level_line(focus_id),
        _real_class_gap_line(focus_id),
    ]


def _refined_objectives_body(focus: dict[str, Any]) -> list[str]:
    focus_id = str(focus.get("focus_id") or "")
    if focus_id == "shoe_observation_drawing_expression":
        return [
            "学生能从正面、侧面、后面或局部角度观察一双鞋，说出外形比例、鞋面结构、鞋底方向或鞋带纹样等2-3个发现。",
            "学生能用线条和形状画出鞋的基本轮廓、主要结构和至少一处局部细节，画面依据来自实际观察而不是凭空想象。",
            "学生能在展示交流中说明自己抓住了哪个角度或细节，并根据同伴或教师提示完成一次画面调整。",
        ]
    if focus_id == "color_gradation_expression":
        return [
            "学生能观察生活或画面中的颜色过渡现象，说出颜色逐步变化的基本特点。",
            "学生能通过试色、叠色、浓淡或色阶排列完成一组有连续变化的色彩表达。",
            "学生能用可见证据说明自己的过渡是否自然，并根据反馈调整一处色彩衔接。",
        ]
    if focus_id == "ink_or_traditional_color_exploration":
        return [
            "学生能观察青绿山水图像，说出色彩层次、山石空间或材料质感中的2-3个发现。",
            "学生能通过短任务尝试石青、石绿或墨色浓淡的层次变化，形成一处可见的材料试探证据。",
            "学生能在交流中说明自己的青绿观察依据，并用作品或学习单记录一处调整想法。",
        ]
    if focus_id == "paper_weaving_structure_expression":
        return [
            "学生能观察纸条穿插或编织样例，说出经线、纬线和一上一下穿插关系。",
            "学生能用纸条完成一次有秩序的穿编尝试，保持基本间距并形成简单纹样。",
            "学生能在交流中指出作品里一处经纬结构或纹样变化，并根据提示调整松紧或排列。",
        ]
    if focus_id == "material_transformation_expression":
        return [
            "学生能观察材料的形态、质感和连接可能，说出材料可以服务哪个造型意图。",
            "学生能通过剪贴、拼摆、连接或组合完成一件结构相对稳定、主题明确的作品。",
            "学生能用作品中的材料选择和结构处理说明自己的创意表达。",
        ]
    if focus_id == "theme_observation_expression":
        return [
            "学生能观察主题对象或情境，说出形象、环境或问题中的关键特征。",
            "学生能把观察到的特征转化为画面、学习单或作品表达。",
            "学生能在交流中用作品证据说明自己的主题理解和表达选择。",
        ]
    return [
        "学生能围绕本课任务完成一次有目标的观察、尝试或表达。",
        "学生能说出自己的学习发现、方法选择或作品特点。",
        "学生能在交流中用课堂证据说明自己的学习成果。",
    ]


def _refined_keypoints_body(focus: dict[str, Any]) -> list[str]:
    focus_id = str(focus.get("focus_id") or "")
    if focus_id == "shoe_observation_drawing_expression":
        return [
            "重点：引导学生从真实鞋或图片中观察不同角度的外形、结构和局部细节，并把观察发现转化为线描表达。",
            "难点：帮助学生处理比例、遮挡、鞋面与鞋底方向、局部纹样等容易被忽略的细节，避免画成概念化、符号化的鞋。",
        ]
    if focus_id == "color_gradation_expression":
        return [
            "重点：引导学生看见颜色逐步变化的规律，并通过试色或色阶练习形成可见的过渡效果。",
            "难点：帮助学生控制水分、浓淡、叠色或色距，避免直接跳色、平涂和只追求颜色好看。",
        ]
    if focus_id == "ink_or_traditional_color_exploration":
        return [
            "重点：引导学生观察青绿山水的色彩层次、材料质感和画面空间关系。",
            "难点：帮助学生把传统图像感受转化为可操作的材料试探和语言表达，避免只停留在颜色好看。",
        ]
    if focus_id == "paper_weaving_structure_expression":
        return [
            "重点：引导学生理解纸条经纬穿插关系，并按一上一下的秩序完成基础穿编。",
            "难点：帮助学生控制纸条间距、松紧和纹样变化，避免只随意穿插或粘贴。",
        ]
    if focus_id == "material_transformation_expression":
        return [
            "重点：引导学生判断材料形态、连接方式和主题造型之间的关系。",
            "难点：帮助学生让材料服务造型意图，兼顾结构稳定、工具安全和作品说明。",
        ]
    if focus_id == "theme_observation_expression":
        return [
            "重点：引导学生提取主题对象、环境或问题中的可见特征。",
            "难点：帮助学生把零散印象转化为有主题、有证据的作品表达。",
        ]
    return [
        "重点：围绕本课任务形成清楚的观察、方法尝试和作品表达。",
        "难点：让学生说清方法选择和学习成果之间的关系。",
    ]


def _has_micro_display_content(micro: dict[str, Any]) -> bool:
    return any(
        _clean(micro.get(key))
        for key in ["teacher_action", "student_action", "screen_or_materials", "scaffolds", "evidence"]
    )


def _episode_text_for_micro(episode: dict[str, Any], micro: dict[str, Any] | None = None) -> str:
    parts = [
        episode.get("episode_title"),
        episode.get("title"),
        episode.get("episode_goal"),
        episode.get("goal"),
        episode.get("teacher_organization"),
        episode.get("student_learning"),
    ]
    if isinstance(micro, dict):
        parts.extend([micro.get("step_name"), micro.get("title")])
    flat: list[str] = []
    for part in parts:
        if isinstance(part, list):
            flat.extend(str(item) for item in part)
        elif part:
            flat.append(str(part))
    return _clean(" ".join(flat))


def _shoe_micro_candidates(text: str) -> list[dict[str, str]]:
    if any(token in text for token in ["展示", "小结", "交流", "评价"]):
        return [
            {
                "step_name": "用观察证据交流作品",
                "teacher_action": "请学生指着作品说明自己抓住了哪个角度或哪处细节，再给出一条可修改建议。",
                "student_action": "说出自己作品中的一个观察证据，并听取同伴或教师的一条调整建议。",
                "screen_or_materials": "学生作品展示区；评价句式：我观察到……所以我画了……",
                "scaffolds": "评价不只说像不像，要说哪里体现了角度、结构或细节。",
                "evidence": "学生能用一句话说明作品里的观察依据，并知道下一步可调整处。",
            }
        ]
    if any(token in text for token in ["导入", "引入", "提出问题"]):
        return [
            {
                "step_name": "比较鞋的第一眼差异",
                "teacher_action": "出示或摆放几双不同类型的鞋，引导学生从外形、角度和局部细节说出第一眼发现。",
                "student_action": "观察鞋的整体外形，说出自己看到的1个差异或想追问的问题。",
                "screen_or_materials": "不同民族、不同时代或不同角度的鞋图；可配真实鞋。",
                "scaffolds": "提示学生先说看得见的形状、鞋面、鞋底、鞋带，不急着评价好不好看。",
                "evidence": "学生能说出至少1个可见观察点或提出一个与鞋的结构/角度有关的问题。",
            }
        ]
    if any(token in text for token in ["观察", "指导", "正面", "侧面", "局部", "细节"]):
        return [
            {
                "step_name": "确定观察角度",
                "teacher_action": "请学生固定一双鞋的摆放角度，先比较正面、侧面或后面的轮廓差异。",
                "student_action": "选择一个观察角度，指出鞋头、鞋跟、鞋底方向或鞋口位置。",
                "screen_or_materials": "真实鞋或多角度鞋图；可用线框标出外轮廓。",
                "scaffolds": "追问：你看到的是正面、侧面还是后面？鞋底朝向哪里？鞋口在哪里？",
                "evidence": "学生能说清自己的观察角度，并指出2个结构位置。",
            },
            {
                "step_name": "抓住结构和局部细节",
                "teacher_action": "把学生观察到的鞋面、鞋底、鞋带、纹样等细节归到“结构”和“装饰”两类。",
                "student_action": "在观察对象上找出一个结构细节和一个局部纹样，准备转成线条画到画面里。",
                "screen_or_materials": "局部放大图或教师板书：轮廓/结构/细节。",
                "scaffolds": "避免只说颜色，要求学生用“鞋面弯曲、鞋底厚薄、鞋带交叉”等可见词描述。",
                "evidence": "学生能说出2-3个可用线条表现进作品的具体细节。",
            },
        ]
    if any(token in text for token in ["写生", "动手", "画", "线条", "轮廓", "结构"]):
        return [
            {
                "step_name": "先画大轮廓和比例",
                "teacher_action": "提醒学生先用轻线确定鞋的长宽比例、鞋头和鞋跟位置，再进入细节。",
                "student_action": "用线条画出鞋的外轮廓，检查鞋头、鞋跟和鞋底方向是否对应观察对象。",
                "screen_or_materials": "真实鞋、观察照片、教师板演的轻线轮廓。",
                "scaffolds": "口诀：先大形，再结构，最后补细节。",
                "evidence": "画面中能看出鞋的基本方向、比例和外轮廓。",
            },
            {
                "step_name": "补结构细节并调整",
                "teacher_action": "巡视时针对鞋面、鞋底、鞋带、纹样等细节给出一处具体调整建议。",
                "student_action": "补充至少一处局部细节，并根据观察对象调整线条或比例。",
                "screen_or_materials": "局部细节提示卡：鞋面、鞋底、鞋带、纹样。",
                "scaffolds": "追问：这条线对应鞋的哪一部分？你画的是看到的，还是想象的？",
                "evidence": "作品中出现至少一处来自观察的局部细节，并完成一次调整。",
            },
        ]
    return [
        {
            "step_name": "围绕鞋的观察推进",
            "teacher_action": "把本环节任务落到观察角度、结构细节和线条表达中的一个具体动作上。",
            "student_action": "完成一个可观察的小任务，并说出自己的观察依据。",
            "screen_or_materials": "真实鞋、鞋图或教师板书观察提示。",
            "scaffolds": "提示学生用可见词描述，不用空泛评价代替观察。",
            "evidence": "学生能留下一个口头发现、画面细节或调整痕迹。",
        }
    ]


def _generic_micro_candidates(text: str, focus_id: str) -> list[dict[str, str]]:
    if focus_id == "color_gradation_expression":
        return [
            {
                "step_name": "观察并试出变化",
                "teacher_action": "引导学生先说出颜色变化的方向，再用短任务试出一种过渡方法。",
                "student_action": "完成一次试色或色阶排列，并说出哪里变化最明显。",
                "screen_or_materials": "色阶示例、试色纸或学生材料。",
                "scaffolds": "追问：颜色是突然变了，还是一步步变了？中间少了哪一格？",
                "evidence": "学生能呈现一组有连续变化的色彩证据。",
            }
        ]
    if focus_id == "ink_or_traditional_color_exploration":
        return [
            {
                "step_name": "观察青绿层次和材料感",
                "teacher_action": "引导学生先看青绿山水中的远近、浓淡和石青石绿的色彩层次，再追问这些颜色给画面带来什么感受。",
                "student_action": "指出画面中一处青绿层次或山石空间关系，并用自己的话说出感受。",
                "screen_or_materials": "青绿山水局部图、石青石绿材料图或教师短示范。",
                "scaffolds": "追问：哪里更浓？哪里更淡？颜色让山水显得远还是近？",
                "evidence": "学生能说出1处青绿层次或材料感受，并能对应到画面位置。",
            }
        ]
    if focus_id == "paper_weaving_structure_expression":
        return [
            {
                "step_name": "试出经纬穿插规律",
                "teacher_action": "用两组纸条示范经线和纬线，放慢一上一下的穿插动作，让学生先判断下一根纸条该从上还是从下进入。",
                "student_action": "用纸条完成一小段穿编，边做边检查经纬关系和纸条间距。",
                "screen_or_materials": "经纬示意图、两色纸条、半成品穿编样例。",
                "scaffolds": "口诀：一上一下，错开穿插；先压住，再穿过。",
                "evidence": "学生能完成一小段有规律的穿编，并指出经线和纬线。",
            }
        ]
    if focus_id == "material_transformation_expression":
        return [
            {
                "step_name": "判断材料如何服务造型",
                "teacher_action": "引导学生先看材料形态，再决定剪贴、拼摆或连接方式。",
                "student_action": "选择一种材料处理方式，并说明它对应作品中的哪个结构。",
                "screen_or_materials": "材料样例、连接方式示范或安全提示。",
                "scaffolds": "追问：这个材料像什么？需要连接在哪里才稳？",
                "evidence": "学生能说出材料选择和造型意图之间的关系。",
            }
        ]
    return [
        {
            "step_name": "完成本环节可见任务",
            "teacher_action": "把本环节目标转成一个可完成、可观察的小任务。",
            "student_action": "完成观察、尝试或表达，并留下可交流的证据。",
            "screen_or_materials": "",
            "scaffolds": "教师根据学生现场表现补充提示。",
            "evidence": "学生能说出本环节的一个发现、方法或作品变化。",
        }
    ]


def _focus_micro_candidates(focus_id: str, episode: dict[str, Any], micro: dict[str, Any] | None = None) -> list[dict[str, str]]:
    text = _episode_text_for_micro(episode, micro)
    if focus_id == "shoe_observation_drawing_expression":
        return _shoe_micro_candidates(text)
    return _generic_micro_candidates(text, focus_id)


def _enrich_episode_micro_steps(episode: dict[str, Any], focus_id: str, standard_status: str | None) -> None:
    micro_steps = [micro for micro in episode.get("micro_steps") or [] if isinstance(micro, dict)]
    if not micro_steps:
        micro_steps = [
            {
                "step_id": f"{episode.get('episode_id') or 'episode'}-r200a-1",
                "step_name": _clean(episode.get("episode_title")) or "本环节推进",
                "provenance": "source_gap",
            }
        ]
    if all(not _has_micro_display_content(micro) for micro in micro_steps):
        basis_micro = micro_steps[0] if micro_steps else {}
        candidates = _focus_micro_candidates(focus_id, episode, basis_micro)
        enriched = []
        for index, candidate in enumerate(candidates):
            source_basis = deepcopy((basis_micro or {}).get("derivation_basis") or {})
            if standard_status:
                source_basis["standard_alignment_status"] = standard_status
            source_basis["r200a_micro_guidance"] = "focus_specific_candidate_for_empty_micro_step"
            enriched.append(
                {
                    **deepcopy(basis_micro),
                    "step_id": f"{episode.get('episode_id') or 'episode'}-r200a-{index + 1}",
                    "step_name": candidate.get("step_name"),
                    "teacher_action": candidate.get("teacher_action"),
                    "student_action": candidate.get("student_action"),
                    "screen_or_materials": candidate.get("screen_or_materials"),
                    "scaffolds": candidate.get("scaffolds"),
                    "evidence": candidate.get("evidence"),
                    "provenance": "provisional_generated_candidate",
                    "source_status": "provisional_generated_candidate",
                    "teacher_review_required": True,
                    "preview_only": True,
                    "formal_apply": False,
                    "derivation_basis": source_basis,
                }
            )
        episode["micro_steps"] = enriched
        episode["micro_step_guidance_status"] = "r200a_focus_specific_candidate"
        return
    for micro in micro_steps:
        if _has_micro_display_content(micro):
            continue
        candidate = _focus_micro_candidates(focus_id, episode, micro)[0]
        for key in ["teacher_action", "student_action", "screen_or_materials", "scaffolds", "evidence"]:
            micro[key] = candidate.get(key) or ""
        micro["provenance"] = micro.get("provenance") or "provisional_generated_candidate"
        micro["source_status"] = micro.get("source_status") or "provisional_generated_candidate"
        micro["teacher_review_required"] = True


def _apply_body_to_template_section(
    template: dict[str, Any],
    section_key: str,
    body: list[str],
    *,
    notes: list[str] | None = None,
    refinement_id: str,
) -> None:
    value = template.get(section_key)
    if not isinstance(value, list) or not value or not isinstance(value[0], dict):
        return
    value[0]["body"] = body
    value[0]["r200a_r1_refinement"] = refinement_id
    value[0]["teacher_review_required"] = True
    if notes:
        value[0]["source_gap_notes"] = notes


def _apply_body_to_current_section(
    current_lesson: dict[str, Any],
    section_id: str,
    body: list[str],
    *,
    notes: list[str] | None = None,
    refinement_id: str,
) -> None:
    for section in current_lesson.get("sections") or []:
        if not isinstance(section, dict) or section.get("id") != section_id:
            continue
        section["items"] = body
        section["body"] = body
        section["r200a_r1_refinement"] = refinement_id
        section["teacher_review_required"] = True
        if notes:
            section["source_gap_notes"] = notes


def build_art_lesson_design_kernel_preview(
    *,
    single_lesson_template: dict[str, Any],
    lesson_derivation_spine_preview: dict[str, Any],
    import_understanding_v2_graph_preview: dict[str, Any] | None = None,
) -> dict[str, Any]:
    template = single_lesson_template if isinstance(single_lesson_template, dict) else {}
    header = _lesson_header(template)
    focus = _lesson_focus(header, template)
    standard = _standard_control(header, focus)
    moves = _pedagogy_moves_for_focus(str(focus.get("focus_id") or ""))
    episodes = [episode for episode in template.get("process_episodes") or [] if isinstance(episode, dict)]
    episode_method_map = []
    for index, episode in enumerate(episodes):
        method = _method_for_episode(
            _clean(episode.get("episode_title")),
            index,
            len(episodes),
            str(focus.get("focus_id") or ""),
        )
        episode_method_map.append(
            {
                "episode_id": episode.get("episode_id"),
                "episode_title": episode.get("episode_title"),
                "pedagogy_move_id": method["move_id"],
                "pedagogy_role": method["role"],
                "student_state_basis": (episode.get("derivation_basis") or {}).get("student_state_before"),
                "evidence_basis": (episode.get("derivation_basis") or {}).get("assessment_evidence")
                or "; ".join(_items(episode.get("evidence"))),
                "teacher_review_required": True,
            }
        )
    microstep_method_map = []
    for episode in episodes:
        episode_method = next(
            (item for item in episode_method_map if item.get("episode_id") == episode.get("episode_id")),
            {},
        )
        for micro in episode.get("micro_steps") or []:
            if not isinstance(micro, dict):
                continue
            micro_basis = micro.get("derivation_basis") if isinstance(micro.get("derivation_basis"), dict) else {}
            microstep_method_map.append(
                {
                    "episode_id": episode.get("episode_id"),
                    "step_id": micro.get("step_id"),
                    "pedagogy_move_id": episode_method.get("pedagogy_move_id"),
                    "pedagogy_role": episode_method.get("pedagogy_role"),
                    "transition_role": micro_basis.get("transition_role"),
                    "evidence_basis": micro_basis.get("assessment_evidence") or micro.get("evidence"),
                    "source_rule": micro_basis.get("rule"),
                    "teacher_review_required": True,
                }
            )
    chain_checks = {
        "curriculum_control_layer_present": bool(standard.get("control_layer")),
        "official_standard_gap_visible": bool(standard.get("missing_required_fields")),
        "pedagogy_moves_present": bool(moves),
        "episodes_mapped_to_pedagogy": bool(episodes) and len(episode_method_map) == len(episodes),
        "microsteps_mapped_to_pedagogy": bool(microstep_method_map),
        "derivation_spine_preserved": isinstance(lesson_derivation_spine_preview, dict)
        and bool(lesson_derivation_spine_preview.get("spine_id")),
        "no_official_standard_claim_without_ref": standard.get("official_curriculum_claim_created") is False,
    }
    kernel_status = "KERNEL_READY_WITH_STANDARD_GAP" if all(chain_checks.values()) else "KERNEL_NEEDS_REVIEW"
    graph = import_understanding_v2_graph_preview.get("graph") if isinstance(import_understanding_v2_graph_preview, dict) else {}
    return {
        "stage": STAGE_ID,
        "kernel_id": f"r200a_art_kernel_{_short_id(template.get('template_id'), header, focus.get('focus_id'))}",
        "kernel_version": "art_lesson_design_kernel_v0.1",
        "kernel_status": kernel_status,
        "lesson_header": header,
        "lesson_focus": focus,
        "source_authority_order": [
            "curriculum_standard_control_layer",
            "textbook_anchor_or_uploaded_original",
            "single_lesson_template",
            "lesson_derivation_spine",
            "art_pedagogy_kernel",
            "provider_or_model_candidate",
            "official_case_reference",
        ],
        "curriculum_standard_control": standard,
        "lesson_learning_logic": {
            "core_learning_problem": _clean((_template_body(template, "student_analysis") or [""])[0]),
            "target_shift": "学生从直观观察进入方法尝试，再用作品或语言给出可见证据。",
            "evidence_rule": "每个关键环节至少对应一个学生表达、作品痕迹、学习单或操作结果。",
            "difficulty_control": "难点必须落到教师可示范、学生可尝试、作品可观察的动作上。",
        },
        "art_pedagogy_kernel": {
            "kernel_type": "elementary_art_pedagogy_rules",
            "moves": moves,
            "teacher_language_rule": "教师话术服务于观察、方法、证据和过渡，不单独堆叙述。",
            "student_learning_rule": "学生学习必须写成任务和可观察证据，不写空泛参与。",
            "xiaojiao_rule": "小教提醒只提示判断点、追问点和风险点，不重复完整教师话术。",
        },
        "episode_method_map": episode_method_map,
        "microstep_method_map": microstep_method_map,
        "provider_reasoning_packet_preview": {
            "provider_call_allowed_later": True,
            "provider_called_now": False,
            "must_include": [
                "single_lesson_template",
                "lesson_derivation_spine_preview",
                "curriculum_standard_control",
                "art_pedagogy_kernel",
                "episode_method_map",
            ],
            "must_not_include": [
                "full_curriculum_standard_text_without_source",
                "raw_chain_of_thought",
                "formal_apply_instruction",
            ],
            "expected_output": "candidate_only_field_patch_or_reasoning_update",
        },
        "chain_checks": chain_checks,
        "teacher_review_required": True,
        "preview_only": True,
        "boundary": {
            "preview_only": True,
            "provider_called": False,
            "model_called": False,
            "formal_apply_performed": False,
            "database_written": False,
            "memory_written": False,
            "feishu_written": False,
            "official_curriculum_claim_created": False,
            "real_curriculum_standard_full_text_parsed": False,
            "R21_modified": False,
            "R36_modified": False,
            "R95_executed": False,
        },
        "source_graph_id": graph.get("graph_id") if isinstance(graph, dict) else None,
    }


def apply_art_kernel_to_template(single_lesson_template: dict[str, Any], kernel: dict[str, Any]) -> dict[str, Any]:
    template = single_lesson_template
    template["art_lesson_design_kernel_preview"] = kernel
    template.setdefault("renderer_policy", {})["art_lesson_design_kernel_applied"] = True
    template.setdefault("renderer_policy", {})["basis_student_profile_refined"] = True
    standard = kernel.get("curriculum_standard_control") if isinstance(kernel.get("curriculum_standard_control"), dict) else {}
    header = kernel.get("lesson_header") if isinstance(kernel.get("lesson_header"), dict) else _lesson_header(template)
    focus = kernel.get("lesson_focus") if isinstance(kernel.get("lesson_focus"), dict) else _lesson_focus(header, template)
    old_basis = _template_body(template, "basis")
    refined_basis, basis_notes = _refined_basis_body(header, focus, old_basis)
    refined_analysis = _refined_student_analysis_body(header, focus, old_basis)
    refined_objectives = _refined_objectives_body(focus)
    refined_keypoints = _refined_keypoints_body(focus)
    _apply_body_to_template_section(
        template,
        "basis",
        refined_basis,
        notes=basis_notes,
        refinement_id="r200a_r1_basis_dedupe",
    )
    _apply_body_to_template_section(
        template,
        "student_analysis",
        refined_analysis,
        refinement_id="r200a_r1_student_profile_layers",
    )
    _apply_body_to_template_section(
        template,
        "objectives",
        refined_objectives,
        refinement_id="r200a_r2_focus_objectives",
    )
    _apply_body_to_template_section(
        template,
        "key_difficult_points",
        refined_keypoints,
        refinement_id="r200a_r2_focus_keypoints",
    )
    method_by_episode = {
        _clean(item.get("episode_id")): item
        for item in kernel.get("episode_method_map") or []
        if isinstance(item, dict)
    }
    micro_by_step = {
        _clean(item.get("step_id")): item
        for item in kernel.get("microstep_method_map") or []
        if isinstance(item, dict)
    }
    for section_key in ["basis", "student_analysis", "objectives", "key_difficult_points"]:
        value = template.get(section_key)
        if isinstance(value, list) and value and isinstance(value[0], dict):
            value[0]["art_kernel_basis"] = {
                "kernel_id": kernel.get("kernel_id"),
                "kernel_status": kernel.get("kernel_status"),
                "standard_interpretation_status": standard.get("interpretation_status"),
                "teacher_review_required": True,
            }
    for episode in template.get("process_episodes") or []:
        if not isinstance(episode, dict):
            continue
        _enrich_episode_micro_steps(
            episode,
            str(focus.get("focus_id") or ""),
            standard.get("interpretation_status"),
        )
        method = method_by_episode.get(_clean(episode.get("episode_id")))
        if isinstance(method, dict):
            episode["art_kernel_basis"] = deepcopy(method)
            derivation = episode.get("derivation_basis")
            if isinstance(derivation, dict):
                derivation["pedagogy_move"] = method.get("pedagogy_move_id")
                derivation["pedagogy_role"] = method.get("pedagogy_role")
                derivation["standard_alignment_status"] = standard.get("interpretation_status")
        for micro in episode.get("micro_steps") or []:
            if not isinstance(micro, dict):
                continue
            micro_method = micro_by_step.get(_clean(micro.get("step_id")))
            if isinstance(micro_method, dict):
                micro["art_kernel_basis"] = deepcopy(micro_method)
                basis = micro.get("derivation_basis")
                if isinstance(basis, dict):
                    basis["pedagogy_move"] = micro_method.get("pedagogy_move_id")
                    basis["pedagogy_role"] = micro_method.get("pedagogy_role")
            elif isinstance(method, dict):
                micro["art_kernel_basis"] = {
                    "episode_id": episode.get("episode_id"),
                    "step_id": micro.get("step_id"),
                    "pedagogy_move_id": method.get("pedagogy_move_id"),
                    "pedagogy_role": method.get("pedagogy_role"),
                    "student_state_basis": method.get("student_state_basis"),
                    "evidence_basis": method.get("evidence_basis"),
                    "source": "r200a_episode_method_projected_to_focus_micro_candidate",
                    "teacher_review_required": True,
                    "preview_only": True,
                }
                basis = micro.get("derivation_basis")
                if isinstance(basis, dict):
                    basis["pedagogy_move"] = method.get("pedagogy_move_id")
                    basis["pedagogy_role"] = method.get("pedagogy_role")
    guard = _cross_topic_guard_for_template(template, focus)
    kernel["cross_topic_guard"] = guard
    template.setdefault("renderer_policy", {})["cross_topic_visible_text_guard_passed"] = guard.get("passed") is True
    return template


def apply_art_kernel_to_current_lesson_sections(current_lesson: dict[str, Any], kernel: dict[str, Any]) -> None:
    standard = kernel.get("curriculum_standard_control") if isinstance(kernel.get("curriculum_standard_control"), dict) else {}
    header = kernel.get("lesson_header") if isinstance(kernel.get("lesson_header"), dict) else {}
    focus = kernel.get("lesson_focus") if isinstance(kernel.get("lesson_focus"), dict) else {}
    current_basis = []
    for section in current_lesson.get("sections") or []:
        if isinstance(section, dict) and section.get("id") == "basis":
            current_basis = _items(section.get("items") or section.get("body"))
            break
    refined_basis, basis_notes = _refined_basis_body(header, focus, current_basis)
    refined_analysis = _refined_student_analysis_body(header, focus, current_basis)
    refined_objectives = _refined_objectives_body(focus)
    refined_keypoints = _refined_keypoints_body(focus)
    _apply_body_to_current_section(
        current_lesson,
        "basis",
        refined_basis,
        notes=basis_notes,
        refinement_id="r200a_r1_basis_dedupe",
    )
    _apply_body_to_current_section(
        current_lesson,
        "analysis",
        refined_analysis,
        refinement_id="r200a_r1_student_profile_layers",
    )
    _apply_body_to_current_section(
        current_lesson,
        "goals",
        refined_objectives,
        refinement_id="r200a_r2_focus_objectives",
    )
    _apply_body_to_current_section(
        current_lesson,
        "keypoints",
        refined_keypoints,
        refinement_id="r200a_r2_focus_keypoints",
    )
    for section in current_lesson.get("sections") or []:
        if not isinstance(section, dict):
            continue
        section["art_kernel_basis"] = {
            "kernel_id": kernel.get("kernel_id"),
            "kernel_status": kernel.get("kernel_status"),
            "standard_interpretation_status": standard.get("interpretation_status"),
            "teacher_review_required": True,
            "preview_only": True,
        }
