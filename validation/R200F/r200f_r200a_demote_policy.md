# R200F R200A Demotion Policy

R200A is no longer a teacher-main writer.

Allowed R200A surfaces:

- diagnostic
- quality candidate
- pedagogy suggestion
- curriculum alignment hint
- teacher-review-needed note
- developer folded diagnostics

R200A must not directly overwrite:

- `basis`
- `student_analysis`
- `objectives`
- `key_difficult_points`
- `process_episodes`
- current lesson main sections

R200A may continue to compute focus, warnings, and quality suggestions, but R103 must demote those outputs before returning the frontend-visible response.
