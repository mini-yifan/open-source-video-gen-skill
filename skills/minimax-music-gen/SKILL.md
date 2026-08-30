---
name: minimax-music-gen
description: >
  Use when user wants to generate music, songs, or audio tracks. Triggers on any request
  involving music creation, song writing, lyrics generation, audio production, or covers.
  Also triggers when user provides lyrics and wants them turned into a song, or describes
  a mood/scene and wants background music. Supports multilingual triggers — match equivalent
  phrases in any language. Do NOT use for music playback of existing files, music theory
  questions, or music recommendation without generation.
license: MIT
metadata:
  version: "2.0"
  category: creative
---

# MiniMax Music Generation Skill

Generate vocal songs or instrumental tracks with MiniMax Music v2.6 through Tencent Cloud
TokenHub. Supports two creation modes: **Basic** (one-sentence-in, song-out) and
**Advanced Control** (edit lyrics, refine prompt, plan before generating).

## Prerequisites

- **TokenHub API key**: Set `MINIMAX_API_KEY` in the environment. Never put the key in a
  prompt, a skill file, a source file, a filename, or a command-line argument.

  Non-interactive Agent shells may not load `~/.zshrc`. Before checking the variable, load
  the private environment file when it exists:
  ```bash
  MINIMAX_ENV_FILE="${MINIMAX_MUSIC_ENV_FILE:-$HOME/.config/minimax-music.env}"
  if [[ -z "${MINIMAX_API_KEY:-}" && -r "$MINIMAX_ENV_FILE" ]]; then
    source "$MINIMAX_ENV_FILE"
  fi
  ```

  **Verify without printing the key:**
  ```bash
  test -n "$MINIMAX_API_KEY" && echo "MINIMAX_API_KEY is set" || echo "MINIMAX_API_KEY is missing"
  ```

- **Python 3**: The bundled `scripts/tokenhub_music_generate.py` uses only the standard
  library, downloads the returned URL immediately, and writes the audio file locally. If a
  non-interactive shell did not inherit the variable, it also reads the private
  `~/.config/minimax-music.env` fallback file without printing the key.

- **Audio player** (recommended): `mpv`, `ffplay`, or `afplay` (macOS built-in) for local
  playback. `mpv` is preferred for its interactive controls.

## TokenHub API

The current integration uses the Tencent Cloud TokenHub endpoint from the user's API
documentation:

```text
POST https://tokenhub.tencentmaas.com/v1/wand/minimax-music/generation
model: minimax-music-v2.6
```

The request is synchronous. Use `output_format=url` and download the result immediately;
the returned URL is valid for 12 hours. The API documentation does not expose a hard
duration parameter, so words such as “short” or “20-second” in the prompt are soft guidance;
the actual duration is model-controlled.

Supported modes:

- Vocal with supplied lyrics: `lyrics`
- Vocal with generated lyrics: `lyrics_optimizer: true`
- Instrumental: `is_instrumental: true` and a non-empty `prompt`

The old `mmx` workflow and MiniMax free models are not used by this skill. Do not call
`mmx auth login`, `music-2.6-free`, or `music-cover-free` for this integration.

## Storage

All generated music is saved to `MINIMAX_MUSIC_OUTPUT_DIR` when set, otherwise
`~/Music/minimax-gen/`. Create the directory if it doesn't exist. Files are named with a
timestamp and a short slug derived from the prompt:
`YYYYMMDD_HHMMSS_<slug>.mp3`

When the normal home Music directory is not writable in the current environment, use an
explicit writable workspace path for `--out` and report that absolute path to the user.

---

## Language & Interaction

Detect the user's language from their first message and respond in that language for the
entire session. This applies to all interaction text, questions, confirmations, and feedback
prompts.

**User-facing text localization rule**:
- ALL text shown to the user — including preview labels, field names, confirmations, status
  messages, playback info, feedback prompts, **and the prompt/description preview** — MUST
  be fully translated into the user's language.
- The **API prompt** sent to the model should always be written in English for best
  generation quality. However, when previewing the prompt to the user, show a localized
  description in the user's language instead of the raw English prompt. The English prompt
  is an internal implementation detail — the user does not need to see it.
- The templates below are written in English as reference. At runtime, translate every label
  and message into the user's detected language.

**Lyrics language rule**:
- Default lyrics language = the user's language. A Chinese-speaking user gets Chinese lyrics;
  an English-speaking user gets English lyrics.
- Only generate lyrics in a different language if the user **explicitly** requests it.
- When a different lyrics language is needed, embed it naturally into the vocal or genre
  description in the prompt. For example, instead of appending "with Korean lyrics", use
  "featuring a Korean female vocalist" or specify a genre that implies the language (e.g.,
  "K-pop", "J-rock", "Mandopop", "Latin pop").

---

## Workflow

### Step 0: Detect Intent

Parse the user's message to determine:

1. **Song category**: vocal (with lyrics), instrumental (no vocals), or cover
2. **Creation mode preference**: did they provide detailed requirements (Advanced) or a
   casual one-liner (Basic)?

If ambiguous, ask using this decision tree:

```
Q1: What type of music?
  - Vocal (with lyrics)
  - Instrumental (no vocals)
  - Cover

Q2: Creation mode?
  - Basic — one-line description, auto-generate
  - Advanced — edit lyrics, refine prompt, plan
```

If the user gives a clear one-liner like "make me a sad piano piece", skip the questions —
infer instrumental + basic mode and proceed.

---

### Step 1: Basic Mode

**Goal**: User provides a short description, the skill auto-generates everything, then calls
the API.

1. **Expand the description into a prompt**: Take the user's one-liner and expand it into a
   rich music prompt. Refer to the **Prompt Writing Guide** appendix at the end of this
   document for style vocabulary, genre/instrument references, and prompt structure.
   **The API prompt should always be written in English** for best generation quality,
   regardless of the user's language.
   
   Follow this pattern:
   ```
   A [mood] [BPM optional] [genre] song, featuring [vocal description],
   about [narrative/theme], [atmosphere], [key instruments and production].
   ```

2. **Show the user a preview** before generating. Translate all labels AND the prompt
   description into the user's language. The English prompt is only used internally when
   calling the API — the user should never see it. Example template (English reference —
   localize everything at runtime):

   ```
   About to generate:
   Type: Vocal / Instrumental
   Description: indie folk, melancholy, acoustic guitar, gentle female voice
   Lyrics: Auto-generated (--lyrics-optimizer)
   
   Confirm? (press enter to confirm, or tell me what to change)
   ```

3. **Call the TokenHub helper**: Generate the music directly and download the returned
   audio URL before it expires.

---

### Step 2: Advanced Control Mode

**Goal**: User has full control over every parameter before generation.

1. **Lyrics phase**:
   - If user provided lyrics: display them formatted with section markers, ask for edits.
     The final lyrics will be passed via `--lyrics` to the TokenHub helper.
   - If user has a theme but no lyrics: use `--lyrics-optimizer` to auto-generate.
   - Support iterative editing: "change the second chorus" -> only rewrite that section.
   - User can also write lyrics themselves and pass via `--lyrics`.

2. **Prompt phase**:
   - Generate a recommended prompt based on the lyrics' mood and content.
   - Present it as editable tags the user can add/remove/modify.
   - Refer to the **Prompt Writing Guide** appendix for the full vocabulary.

3. **Advanced planning** (optional, offer but don't force):
   - Song structure: verse-chorus-verse-chorus-bridge-chorus or custom
   - BPM suggestion (encode in prompt as tempo descriptor)
   - Reference style: "something like X style" -> map to prompt tags
   - Vocal character description

4. **Final confirmation**: Show complete parameter summary, then generate.

---

### Step 3: Call TokenHub

Use the bundled helper script. Set `SKILL_DIR` to the directory containing this `SKILL.md`.
The helper reads `MINIMAX_API_KEY` and never accepts an API key as a CLI argument.

**Vocal with auto-generated lyrics:**
```bash
python3 "$SKILL_DIR/scripts/tokenhub_music_generate.py" \
  --prompt "<prompt>" \
  --lyrics-optimizer \
  --out "${MINIMAX_MUSIC_OUTPUT_DIR:-$HOME/Music/minimax-gen}/<filename>.mp3"
```

**Vocal with user-provided lyrics:**
```bash
python3 "$SKILL_DIR/scripts/tokenhub_music_generate.py" \
  --prompt "<prompt>" \
  --lyrics "<lyrics with section markers>" \
  --out "${MINIMAX_MUSIC_OUTPUT_DIR:-$HOME/Music/minimax-gen}/<filename>.mp3"
```

**Instrumental (no vocal):**
```bash
python3 "$SKILL_DIR/scripts/tokenhub_music_generate.py" \
  --prompt "<prompt>" \
  --instrumental \
  --format mp3 \
  --sample-rate 44100 --bitrate 256000 \
  --out "${MINIMAX_MUSIC_OUTPUT_DIR:-$HOME/Music/minimax-gen}/<filename>.mp3"
```

The TokenHub music endpoint accepts the main creative controls through `prompt`; encode
genre, mood, tempo, scene, instruments, and production details in a vivid English sentence
instead of sending unsupported `mmx` structured flags.

Display a progress indicator while waiting. The request can take 30-120 seconds. Never print
the authorization header or the signed audio URL.

---

### Step 4: Playback

After generation, detect an available audio player and play the file.

**Detect player:**
```bash
command -v mpv || command -v ffplay || command -v afplay
```

**Play based on detected player (in priority order):**

| Player | Command | Controls |
|--------|---------|----------|
| `mpv` (preferred) | `mpv --no-video <absolute-output-path>.mp3` | space = pause/resume, q = quit, left/right = seek |
| `ffplay` | `ffplay -nodisp -autoexit <absolute-output-path>.mp3` | q = quit |
| `afplay` (macOS) | `afplay <absolute-output-path>.mp3` | Ctrl+C = stop |
| None found | Do not attempt playback | Show file path only |

After starting playback, tell the user (localize all text):

```
Now playing: <filename>.mp3
Saved to: <absolute-output-path>.mp3
```

Do NOT show playback controls (e.g. keyboard shortcuts) — they don't work in this
environment since the player runs in the background.

If no player is found (localize all text):

```
No audio player detected.
File saved to: <absolute-output-path>.mp3
Tip: Install mpv for the best playback experience (brew install mpv).
```

---

### Step 5: Feedback & Iteration

After playback, ask for feedback:

```
How was this song?
  1. Love it, keep it!
  2. Not quite, adjust and regenerate
  3. Fine-tune lyrics/style then regenerate
  4. Don't want it, start over
```

Based on feedback:
- **Satisfied**: Done. Mention the file path again.
- **Adjust & regenerate**: Ask what to change (prompt? lyrics? style?), apply edits,
  re-run generation. Keep the old file with a `_v1` suffix for comparison.
- **Fine-tune**: Enter Advanced Control Mode with the current parameters pre-filled.
- **Delete & restart**: Remove the file, go back to Step 0.

---

## Cover Mode

Cover generation is not part of the current Tencent Cloud TokenHub MiniMax Music v2.6
documented endpoint. Do not call the old `mmx music cover` / `music-cover-free` workflow.
If the user requests a cover, explain that this integration currently supports new vocal
songs and instrumentals only, then ask whether to use another provider.

---

## Error Handling

| Error | Action |
|-------|--------|
| `MINIMAX_API_KEY` missing | Ask the user to configure the environment variable; never ask them to put it in the prompt |
| HTTP 401/403 | Check TokenHub activation, API key validity, and account permissions |
| HTTP 402 / code `401007` | In Tencent Cloud Console → TokenHub → Online Inference Service, enable postpaid billing; a Token Plan balance alone may not activate this route. Do not loop retries |
| HTTP 402 / code `401009` | The specific API Key quota is exhausted. Check TokenHub API Key Management and Token Plan/API Key usage or limits; account balance alone does not prove this Key has remaining quota. Do not loop retries |
| HTTP 429 | Retry once after a short backoff, then report rate limiting |
| HTTP 5xx or timeout | Retry once, then report the status and request ID if available |
| Content filter | Adjust the prompt to remove disallowed content |
| Invalid lyrics format | Auto-fix section markers, warn user |
| No audio player found | Save file and tell user the path, suggest installing mpv |
| Network error | Show error detail, suggest checking connection |

---

## Important Notes

- **Never reproduce copyrighted lyrics.** When doing covers, always write original lyrics
  inspired by the song's theme. Explain this to the user.
- **Prompt language**: The API prompt works best with English tags. Chinese tags are also
  acceptable. Mixing is OK.
- **Section markers in lyrics**: The API recognizes `[verse]`, `[chorus]`, `[bridge]`,
  `[outro]`, `[intro]`. Always include them when providing `--lyrics`.
- **File management**: If the configured output directory has more than 50 files, suggest cleanup
  when starting a new session.
- **Duration**: There is no documented duration argument. Use a concise prompt for a short
  test, but report the actual duration returned in `extra_info.music_duration`.
- **Lyrics language via style**: When the user wants lyrics in a specific language, express
  it through the vocal description or genre (e.g., "Japanese female vocalist", "Mandopop
  ballad") rather than appending a language directive to the prompt.
- **Commercial use**: Keep `aigc_watermark` off only when appropriate for the user's use case;
  confirm the current Tencent Cloud terms before commercial release.

---

## Appendix: Prompt Writing Guide

See [references/prompt_guide.md](references/prompt_guide.md) for the complete prompt writing guide,
including genre/vocal/instrument references and BPM tables.
