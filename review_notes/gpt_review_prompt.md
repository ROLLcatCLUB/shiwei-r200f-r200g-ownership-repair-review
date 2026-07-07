请审核这个 R200F/R200G/R200I ownership repair 包。

我的核心问题不是“页面好不好看”，而是：

```text
R200A/R200B 这类候选/诊断层，是否已经被挡在教师主正文之外？
教师主正文是否只来自上传原文、R114理解图/执行图/字段投影、或教师确认候选？
```

请重点看：

1. `source/backend_chain/prep_room_source_ownership_policy_1013R_R200F.py`
2. `source/backend_chain/prep_room_real_upload_entry_preview_1013R_R103.py`
3. `source/validators/validate_1013r_r200e_frontend_visible_contamination_guard.py`
4. `source/validators/validate_1013r_r200g_response_assembly_ownership_gate.py`
5. `validation/R200G/validate_1013R_R200G_response_assembly_ownership_gate_result.json`
6. `validation/R200E/content_source_ledger.json`

请判断：

- 这个修复是否真的解决了“主链路混线/串课主因”？
- 还有没有 R200A_kernel / R200B_candidate / deterministic_fallback / unknown 可以进入教师主正文？
- `source_gap` 是否应该继续默认显示，还是要降级折叠？
- 下一步是否应该做 R200H：graph-first main text，还是先继续修 R114 图谱/执行图质量？

注意：这轮不是质量提升包，只是权属守门包。不要把“内容还空”误判为这轮失败；但如果权属守门仍然不严，请直接指出。
