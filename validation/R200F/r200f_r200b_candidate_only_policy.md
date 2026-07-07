# R200F R200B Candidate-Only Policy

R200B remains candidate-only.

It may generate model-backed or deterministic repair suggestions, but those suggestions must not enter teacher main text unless explicitly accepted by the teacher in a later formal acceptance path.

Required flags:

- `candidate_only = true`
- `teacher_review_required = true`
- `renderer_may_apply_candidate = false`
- `formal_apply = false`
