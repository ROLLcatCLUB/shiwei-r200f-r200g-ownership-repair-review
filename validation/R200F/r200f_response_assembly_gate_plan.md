# R200F Response Assembly Gate Plan

R200G implements this policy in R103 response assembly:

1. Save the teacher-main baseline after R114/R97B_P3 projection and before R200A writes.
2. Let R200A/R200B/R200C compute diagnostics and candidates.
3. Before returning the response, restore teacher main sections from the baseline.
4. Attach R200A outputs as diagnostics/candidates only.
5. Mark R110 deterministic draft as folded diagnostic.
6. Emit `r200g_response_assembly_ownership_gate`.
7. Validate with R200E/R200I that teacher-main R200A and unknown counts are zero.
