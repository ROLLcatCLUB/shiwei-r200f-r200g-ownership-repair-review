# R200F Low-Confidence Focus Block Policy

If any of the following is true, R200A must not write teacher main text:

- title is garbled or missing
- raw text is too thin
- template episode count is zero
- focus matched only by weak generic keywords such as `材料`, `颜色`, or `色彩`

In these cases R103 should return uploaded/R114 projection where available, otherwise source-gap confirmation text.
