# Repository audit — Vibe Video / open-source-video-gen-skill

Date: 2026-09-11 (audited against `main` at `0a40107`).
Audience: repo owner. This is a maintenance review, not a product redesign.

## A. Current health

The repo is a **small, actively maintained agent-skills pack** (20 commits, 2026-08-30 → 2026-09-10). It is not an application with a test suite: nine `SKILL.md` files plus Python/Node helper scripts, bilingual READMEs, `SETUP.md`, and two Chinese usage guides.

**What is in good shape**

- Skill count matches the README: **9 skills** (two templates + seven à la carte). The short-drama pipeline was deliberately slimmed (`fe772b9`) to process-only after dropping screenwriter/director skills; `NOTICE` and most docs were updated for that.
- Credential model is coherent in the docs: AutoDL token is hard-required; image gen is replaceable (agent-native first); music/TTS share the same token on the same instance.
- Security hygiene for secrets is decent: no hardcoded API keys; tokens come from env / `~/.config/autodl.env`; SSH passwords are injected via subprocess env and redacted from logs; `.gitignore` already blocked `.env` / `*.token` / `*.key`.
- Recent work looks finished, not abandoned: Windows-ready panel discovery (`0a40107`), music moved off TokenHub (`2bc353a` + `d62c6b5`), beauty-video-gen added, expression-ref path removed on purpose.
- External links that matter still resolve: MiniMax-H3 GitHub, AutoDL Art app API docs (`https://autodl.art/docs/app_api/`), Bilibili intro. Zero GitHub issues and zero PRs — empty tracker, not a backlog.

**What is not**

- `scripts/doctor.sh` was written for the TokenHub era (`cee067c`) and **was not updated** when music moved to MiniMax Music 3 on AutoDL. It still told users to configure a removed API, treated Cursor as the default image executor, and never checked `httpx` (which every H3 script imports).
- There is **no `requirements.txt`, no tests, no `.github` CI/lint**. A new clone hits `ModuleNotFoundError: httpx` before any video job. `opencv-python` is also undocumented in the self-check.
- GitHub **About text is stale**: it still says “10 个技能…编剧/美术/导演”. Live tree is 9 skills, process-only; screenwriter and director directories are gone.
- Several skill files drifted after policy changes (Cursor-preferring frontmatter vs “agent-native first”; Seedream as if it shipped here; music script only searched `~/.zcode` / `~/.codex`; install one-liner did not `mkdir` the skills dir).

**Verdict:** usable by a motivated user who already has AutoDL + an agent runtime, but first-run docs/tooling lagged the August–September skill rewrites. Quick-win fixes in this PR close the worst of that gap; the list below is what remains.

## B. Prioritized work

### P0 — new users hit this immediately

| Item | Rationale |
|---|---|
| Keep `doctor.sh` aligned with the three-tier model | **Fixed in this PR.** It was still probing TokenHub, calling Cursor the default image backend, and ignoring `httpx` / `expect`-for-music. |
| Document and install Python deps (`httpx` hard; `numpy`/`opencv-python` for the beauty filter) | **Fixed in this PR** (`requirements.txt`, README/SETUP, doctor). Confirmed on a clean environment: `import httpx` and `import cv2` both fail until pip install. |
| Install instructions must create the skills directory | **Fixed in this PR.** `ln -s … ~/.zcode/skills/…` fails if the parent does not exist; Cursor users need `~/.cursor/skills` as well. |
| Update the GitHub repo **About** description | Not changeable from a PR. Still advertises 10 skills and 编剧/导演. That is the first thing GitHub visitors see. |

### P1 — correctness / consistency the owner should schedule next

| Item | Rationale |
|---|---|
| Re-sync `h3-prompt-writing` with [MiniMax-H3](https://github.com/MiniMax-AI/MiniMax-H3) | README already warns syntax drifts. Official duration in `comfy-handoff.md` is 4–15s; H3 skill and submit path are 5–15s. Worth a dedicated pass against upstream `base-en` / `ref-en`. |
| Add a smoke CI job | No `.github/` at all. Cheap win: `bash scripts/doctor.sh` (expect non-zero without token), `python3 -m py_compile` on `skills/**/scripts/*.py`, `node --check` on the Cursor wrapper. Does not replace a GPU e2e test. |
| Music/TTS still require `expect` + SSH into the instance | Panel discovery is Windows-ready without SSH, but `generate_music.py` / `generate_tts.py` still `sys.exit` without `expect` and scp over password SSH. Linux/Windows users who only followed “expect is optional” will fail optional audio. Doctor now warns; a non-SSH download path would be the real fix. |
| `generate_music.py` skill discovery | **Partially fixed in this PR** (sibling checkout + `~/.cursor` / `~/.agents`). Remaining: music still boots/shuts the GPU itself, which can fight `short-drama-production`’s “one boot per video batch” rule if the agent calls the script instead of `--keep-on`. |
| Fill missing `agents/openai.yaml` | Present for 5/9 skills (`autodl-app-instance`, `cursor-image-gen`, `h3-prompt-writing`, `qwen3-tts`, `short-drama-production`). Missing for `beauty-video-gen`, `character-three-view`, `minimax-h3`, `minimax-music-gen` — Codex/ChatGPT UI will not list them the same way. |
| Pin or range-pin Python packages | `requirements.txt` is unpinned on purpose (no lockfile, no CI). Once CI exists, pin `httpx` / `numpy` / `opencv-python` to versions you actually run. |
| `character-three-view` Seedream fallback | **Docs clarified in this PR** (optional, not shipped). If Seedream is a real fallback you rely on, vendor or submodule it; otherwise remove the third rung later. |

### P2 — polish, hygiene, larger product bets

| Item | Rationale |
|---|---|
| GitHub license detection | Repo `LICENSE` is MIT, but GitHub reports `NOASSERTION`. Worth checking the license picker / `license` field. |
| TLS `verify=False` / `curl -sk` | Documented as needed for AutoDL self-signed chains. Acceptable for this toolchain; do not “fix” by forcing verify without a cert story. |
| Prompt-duration / default-resolution drift | Beauty template defaults 720×1280; `minimax-h3` “user long-term default” is 1920×1088 turbo for character shots. Agents will pick whichever skill they loaded last. |
| Beauty Step 3.5 still says `bright grin` | Conflicts with the later “small/soft/gentle smile” lock. Prompt-quality bug, not a crash. |
| Hardcoded example instance UUIDs | `pro-7880531ea6b3` etc. in skill examples. Fine as illustrations; a first-time agent may copy them. Prefer placeholders. |
| No issue templates / CODEOWNERS / SECURITY.md | Tracker is empty. If you want external contributors, add a bug template pointing at `doctor.sh` output. |
| English usage guides | `README_EN.md` still sends people to Chinese `docs/*.md`. Fine if the audience is CN-first; a short English fashion/drama page would help overseas users. |
| End-to-end fixture | CONTRIBUTING asks for a live episode chain. A recorded dry-run (discover → submit `--dry` if you add one → poll against a mocked history) would catch slot-map regressions without spending GPU. |

## C. Quick wins vs larger efforts

**Done in this PR (quick wins)**

- Rewrite `scripts/doctor.sh` for post-TokenHub reality: agent-native image gen, shared AutoDL music/TTS, `httpx` as hard-required, `expect` as music/TTS-only, `--probe` no longer hits Tencent TokenHub.
- Add `requirements.txt`; install `pip3 install -r requirements.txt` + `mkdir -p` in both READMEs; Cursor symlink variant.
- SETUP: Python 3.9+, `httpx`, expect-for-audio, extra FAQ rows.
- `generate_music.py` locates sibling skills like `generate_tts.py` (clone-and-run and Cursor/Agents paths).
- Fix music skill markdown links (`../../` → `../`) and `$ZCODE_HOME/.zcode/...` (that path doubled `.zcode`).
- Align Cursor / Seedream skill text with README policy; drop leftover “director-card” in `h3-prompt-writing` yaml; beauty-video-gen token bootstrap matches `autodl.env`.
- `.gitignore`: `*.pem`, `*.flac`/`*.wav`, `autodl.env`/`tokenhub.env`, local `slot_map.json` / `task_info.json`.

**Still small, not done here**

- Edit GitHub About (10 skills / 编剧 / 导演).
- Add `agents/openai.yaml` for the four skills that lack it (copy the existing 5-line pattern).
- One GitHub Actions workflow: compile + doctor.

**Larger (do not start as drive-by refactors)**

- SSH-free music/TTS (HTTP download from the Comfy panel, same as H3).
- Automated H3 prompt sync from upstream MiniMax-H3.
- Real GPU integration tests.
- Restoring screenwriter/director as optional creative skills — explicitly out of scope after `fe772b9`; only revisit if the process-only pipeline proves too thin.

## Investigation notes

| Area | Finding |
|---|---|
| Structure | Root docs + `docs/` + `scripts/doctor.sh` + `skills/` (9). No app server, no `package.json`, no `pyproject.toml`. |
| README vs tree | “Nine skills” is accurate. Install block was the main mismatch (no mkdir, no pip, ZCode-only). |
| Dependencies | Python stdlib + `httpx` (H3) + optional `numpy`/`opencv-python`. Node stdlib only for Cursor wrapper. System: ffmpeg, curl, expect (audio). **Nothing was pinned.** |
| TODOs | No meaningful `TODO`/`FIXME` in code. “placeholder” hits are the intended U06 dark/silent fillers (tracked: `blank_1s.mp4`, `silence_1s.mp3`, `neutral_dark.png`). |
| Tests / CI | None. Scripts syntax-check clean (`py_compile`, `node --check`). |
| Issues / PRs | 0 open, 0 closed. |
| Secrets | No keys in tree. Doctor never `source`s env files (grep-only) — keep that. |
| Half-finished | TokenHub leftover in doctor was the smoking gun; GitHub About is the public leftover. |
