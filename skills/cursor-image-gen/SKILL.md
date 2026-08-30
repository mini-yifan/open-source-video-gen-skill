---
name: cursor-image-gen
description: >-
  Generate or edit bitmap images by launching a local Cursor Agent (cursor-grok-4.6-high)
  and using Cursor GenerateImage, then saving files to an exact folder. Use when ZCode
  should create, edit, or batch-export photos, illustrations, icons, banners, mockups,
  turnarounds, or reference-guided images, including 文生图, 图生图, 多参考图, and 改图.
  Prefer this over built-in image tools and paid image APIs. Do not use for
  SVG/vector/code-native assets or when the user explicitly requests a different
  image-generation provider.
---

# Cursor Image Gen

Launch a headless Cursor Agent and save bitmaps to a user-chosen directory. Do not call `$imagegen`, `image_gen`, or the OpenAI Images API.

## Skill path

```bash
export ZCODE_HOME="${ZCODE_HOME:-$HOME/.zcode}"
export CURSOR_IMG="$ZCODE_HOME/skills/cursor-image-gen/scripts/generate_with_cursor.mjs"
```

The wrapper needs network and write access to `--output-dir`. In a sandboxed ZCode task, request permission before running it.

Do not invoke PATH `agent`; that binary may be Grok. The wrapper resolves `cursor-agent`.

## Routing

| Intent | How to call |
|---|---|
| New image, no file | `--prompt` only (text2img) |
| Guide from one image | `--reference FILE` (img2img) |
| Several refs (style, face, layout) | repeat `--reference`; optional matching `--reference-role` |
| Edit an existing image | `--mode edit` and/or `--keep` / `--change`; edit target is the first `--reference` |
| Same prompt, several variants | `--n N` |
| Many different assets | `--jobs jobs.json` |
| Independent multi-image set | Launch one wrapper invocation per image concurrently; reuse verified references when applicable |

## Scheduling: sequential vs parallel

Decide automatically from the dependency graph instead of always using one mode:

- Generate one image at a time when there is only one requested asset, when each image depends on the previous result, or when the next prompt must be chosen after inspecting the previous output. This is the normal serial workflow.
- If a reference, identity, style, or layout image must be created first, generate and verify that reference serially. After it exists, launch independent downstream image jobs concurrently when they share the reference but do not depend on one another. Reusing the same local reference file across concurrent jobs is supported.
- For true parallel generation, use one `generate_with_cursor.mjs` invocation per output with a unique filename and start those invocations concurrently through the available execution tools. Do not put all independent jobs into one sequential loop.
- `--jobs` runs several assets through one Cursor Agent invocation, and `--n` makes several `GenerateImage` calls for one prompt. Both are batch mechanisms; neither should be described as guaranteed process-level parallelism. Use separate concurrent wrapper invocations when the user asks for simultaneous multi-image generation.
- Keep dependent edits, reference creation, inspection, and any retry that needs a prior result serial. After a parallel batch finishes, verify every returned file independently and report partial failures clearly.

Need exact pixels, a mask, true transparent PNG, seed, or ControlNet? Read [references/limits.md](references/limits.md), tell the user Cursor cannot do it, and stop. Do not silently switch to `$imagegen`.

Mode details and inner-prompt rules: [references/modes.md](references/modes.md).

## Commands

Text to image:

```bash
node "$CURSOR_IMG" \
  --prompt "a paper-cut red panda, warm studio lighting" \
  --output-dir "/absolute/path/to/output" \
  --filename "red-panda.png" \
  --aspect-ratio 1:1
```

Image to image / edit:

```bash
node "$CURSOR_IMG" \
  --prompt "keep the subject, replace the background with a misty forest" \
  --output-dir "/absolute/path/to/output" \
  --filename "forest-edit.png" \
  --reference "/absolute/path/to/source.png" \
  --mode edit \
  --keep "subject, clothing, face" \
  --change "background only"
```

Multi-reference:

```bash
node "$CURSOR_IMG" \
  --prompt "same person as identity ref, composition matching the layout ref, white background turnaround" \
  --output-dir "/absolute/path/to/output" \
  --filename "character-turnaround.png" \
  --aspect-ratio 16:9 \
  --reference "/absolute/path/to/face.png" \
  --reference-role identity \
  --reference "/absolute/path/to/layout.png" \
  --reference-role composition
```

Batch:

```bash
node "$CURSOR_IMG" \
  --jobs "/absolute/path/to/jobs.json" \
  --output-dir "/absolute/path/to/output"
```

`--aspect-ratio` must be `1:1`, `4:3`, `3:4`, `16:9`, or `9:16`. Optional: `--transparent`, `--avoid "..."`, `--n N`, `--overwrite` (only with explicit user approval). The default Cursor model is `cursor-grok-4.6-high`; pass `--model` only when intentionally overriding it.

## Verify

Treat exit code 0 and JSON `ok: true` as success. Return every absolute path in `outputs`. Inspect the files before telling the user they look right.

Setup only:

```bash
node "$CURSOR_IMG" --doctor
node "$CURSOR_IMG" --help
```

If `--doctor` reports `logged_in: false`, ask the user to run `cursor-agent login` (or set `CURSOR_API_KEY`). Do not fall back to `$imagegen`.
