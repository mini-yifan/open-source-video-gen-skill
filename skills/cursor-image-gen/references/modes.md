# Modes

Read this when choosing flags or writing `jobs.json`. The wrapper launches one Cursor Agent and that agent must call `GenerateImage` for every job.

## Shared rules

- `--output-dir` is required except for `--doctor` / `--help`.
- `--filename` is a bare name ending in `.png`, `.jpg`, `.jpeg`, or `.webp`.
- `--reference` may repeat. `--reference-role` is optional; if present, the count must match `--reference`. Roles: `subject`, `style`, `composition`, `edit-target`, `identity`.
- `--keep` / `--change` / `--avoid` / `--transparent` are prompt-only extras. They are not native GenerateImage fields.
- `--n` duplicates one prompt into N GenerateImage calls. Filenames become `stem-1.ext`, `stem-2.ext`.
- Character lock: reuse the same identity file across jobs and write face/hair/clothes into each prompt. Do not only write "match the reference".

## text2img

No `--reference`. Pass a concrete `--prompt` (subject, layout, style, lighting, constraints).

## img2img

Exactly one `--reference`. Prompt must say what to preserve and what to change.

## multi-ref

Two or more `--reference` files. Label each with `--reference-role` when roles differ (identity + composition, subject + style, and so on).

## edit

`--mode edit` and/or `--keep` / `--change`. First reference is the edit target. Extra references may lock identity or style.

## jobs.json

One Cursor Agent run, several assets:

```json
[
  {
    "prompt": "white-background character turnaround, three full-body views",
    "filename": "01_character.png",
    "aspect_ratio": "16:9",
    "mode": "multi-ref",
    "references": [
      { "path": "/abs/layout.png", "role": "composition" },
      { "path": "/abs/face.png", "role": "identity" }
    ]
  },
  {
    "prompt": "old apartment living room, night, vertical frame",
    "filename": "01_living-room.png",
    "aspect_ratio": "9:16",
    "mode": "text2img"
  }
]
```

Optional per job: `transparent`, `avoid`, `keep`, `change`, `n`.

`jobs.json` is a single-agent batch, not a guarantee of parallel execution. When several outputs are independent and true concurrency is desired, launch separate wrapper invocations concurrently, one per output, with unique filenames. Generate and verify prerequisite reference images first; then fan out the independent jobs that reuse those references.

## What the wrapper tells Cursor

The inner prompt always states that the user explicitly requested image generation, forbids Seedream and other APIs, requires `GenerateImage`, and lists exact output paths plus `reference_image_paths`. ZCode should not rewrite that inner prompt; pass user visual intent through `--prompt` / jobs only.
