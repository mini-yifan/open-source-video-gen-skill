# Limits

Cursor `GenerateImage` only accepts `description`, `aspect_ratio` (`1:1`, `4:3`, `3:4`, `16:9`, `9:16`), `filename`, and `reference_image_paths`. If the user needs anything below, say Cursor cannot do it and stop. Do not call `$imagegen` unless they explicitly switch channels.

- Exact pixel sizes (`1080x1920`, `2048x1024`, arbitrary 2K/4K)
- Quality or resolution tiers (`low` / `medium` / `high`, 1K / 2K / 4K)
- True transparent PNG (`background=transparent`). `--transparent` only adds prompt text; alpha is not guaranteed
- Mask inpainting / local redraw from a mask file
- img2img strength, denoise, or `input_fidelity`
- Seed / reproducible noise
- Native `n` that returns several images from one tool call (`--n` is separate GenerateImage calls and will drift)
- Sequential group sets (Seedream lite style)
- ControlNet (pose / canny / depth)
- A dedicated character ID or face embedding (only files + written features)
- A dedicated negative-prompt field (`--avoid` is prompt text)
- Watermark toggle, output format, or compression APIs (the extension is only a filename request)
- Choosing the image backend (Nano Banana and similar are internal)
- Video or SVG/vector output
- Dedicated upscale, outpainting, or background-cutout tools
- Headless clipboard paste (reference images must be local files)
