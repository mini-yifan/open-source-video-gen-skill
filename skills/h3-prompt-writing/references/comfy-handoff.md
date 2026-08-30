# ComfyUI / minimax-h3 handoff

Use this file only when the caller supplies an **H3 prompt brief**. Lock `prompt_mode` from the brief. Write the official structure from `base-en.txt` or `ref-en.txt`, then apply the override table. Do not SSH or submit jobs.

## Overrides (brief present)

| Topic | Official (no brief) | This pipeline (brief present) |
|---|---|---|
| On-screen text | Quote visible letters in the scene | Do not ask the model to paint captions, UI, subtitles, or readable signs |
| Unused video/audio | Do not create labels for unused assets | One unlabeled ignore / `weak_reference` stanza; **do not** assign `<Video N>` or `<Audio N>` to placeholders |
| Word count | `detailed_description` may be 350–500 words | Fit the spoken timeline; do not pad |
| Duration | 4–15 seconds | Match `duration_seconds` (floor 5) |
| Picture labels | Standalone `<Picture N>` only for keyframes | Cite slot `<Picture N>` inside `<Subject N>`; turnarounds are identity locks, not I2VA frame 0 |
| Character count | Describe the subjects in each shot | Obey `VISIBLE_CAST`; state the exact visible instance count of every named character and carry `IDENTITY_CONTINUITY` plus `DUPLICATION_GUARD` into the official prompt body |

If the brief's `prompt_mode` disagrees with a naive reading of the images, **trust the brief**.

## Character uniqueness and duplicate suppression

When the brief contains named characters, write positive exact counts before negative exclusions. Do not leave these constraints only in the brief.

- In T2VA / I2VA / FL2VA / L2VA, place them naturally in `integrated_multimodal_description`; in Ref2VA, place them in `subject_definitions`, `summary` when useful, and `detailed_description`.
- For each shot, translate `VISIBLE_CAST` into wording such as `Exactly one young woman is visible in this shot` or `Exactly one instance of <Subject 1> and exactly one instance of <Subject 2> are visible in the frame.` A voiceover or off-screen speaker has a visible count of zero.
- Keep each named character one continuous physical person with one complete body and stable face, hair, costume, and identity from shot start to shot end.
- Add the relevant exclusions in natural English: `No duplicate, clone, twin, doppelganger, extra copy, lookalike, ghost image, afterimage, motion trail, split body, or suddenly appearing extra person.` For crowd scenes add: `Background extras must not resemble any named character.`
- When several pictures show the same character, define only one subject: `<Subject 1> is one single physical person whose alternate identity views come from <Picture 1>, <Picture 2>, and <Picture 3>; these pictures show the same person, not multiple people.` Never turn alternate views, turnaround panels, expression sheets, or costume references into separate on-screen instances.
- Unless the story requires them, avoid mirrors, glass reflections, human-shaped shadows, motion echoes, or temporal overlays that could read as another body. If a mirror is required, state that there is one physical person and one synchronized optical reflection, not a second independent person.
- A narrative clone, split self, mirror person, or multiple time-state version is an exception only when the brief explicitly authorizes it. Give every authorized instance a distinct position and visible discriminator; do not relax the rule for other characters.
- If exact counting conflicts with vague crowd wording, preserve exact counts for named characters and simplify the crowd description.

## After the brief is chosen: which guide

| `prompt_mode` | Guide | How to write |
|---|---|---|
| T2VA | `base-en.txt` | No alignment line. No Picture/Video/Audio labels. |
| Ref2VA | `ref-en.txt` | Identity / scene / prop stills. Cite Picture slots inside subjects. No I2VA first-frame line. |
| I2VA | `base-en.txt` | Picture 1 **is** the first frame. Use the official 0.00s alignment line. |
| L2VA | `base-en.txt` | Picture 1 **is** the last frame. Prefer the pipeline had switched to U02 / FL2VA. |
| FL2VA | `base-en.txt` | First and last frames. One continuous path; `[Shot 1]` only, no hard-cut list. |

## Picture slots vs `<Subject N>`

Upload order in the brief **is** `<Picture 1>`…`<Picture 9>` (max 9). Cite only the pictures that were actually uploaded. For Ref2VA identity stills:

```text
<Subject 1> is the young woman whose face and costume come from <Picture 1>. Do not copy the white studio backdrop or turnaround grid in <Picture 1>.
```

## Unused image / video / audio slots

U06 always loads 9 image + 3 video + 3 audio inputs. Empty image slots are same-size dark frames; empty video/audio slots are 1-second black / silent placeholders. Official Ref2VA omits unused assets; here add **one unlabeled line** in `subject_definitions` and the same idea once in `retention_analysis`:

```text
Unused ComfyUI image, video, and audio slots are dark/black/silent placeholders; ignore their content, weak_reference, do not copy.
```

Do **not** define extra `<Picture N>`, `<Video 1>`–`<Video 3>`, or `<Audio 1>`–`<Audio 3>` for those placeholders (unresolved labels). Do not describe the black/dark frames as scenes.

## Duration and cuts

- Match `duration_seconds`. Do not write a 4-second timeline.
- `cuts: hard cuts` → later shots `[Shot N] At MM:SS.mmm, the camera cuts to...`
- `cuts: one continuous take, do not cut` → one `[Shot 1]`; state that phrase; no extra cut times.
- 10–15 seconds: 2–4 shots unless the brief says otherwise.

## Example: U06 Ref2VA

```text
subject_definitions:
<Subject 1> is the young Chinese woman whose face, glasses, beauty mark, long black hair, cream cardigan, and dark skirt come from <Picture 1>. Do not copy the white studio backdrop or turnaround grid in <Picture 1>.
<Subject 2> is the old apartment living room in <Picture 2>, with the tall wooden wardrobe, a warm lamp, and cold moonlight.
Unused ComfyUI image, video, and audio slots are dark/black/silent placeholders; ignore their content, weak_reference, do not copy.

summary:
[reference generation] The target video is a 10-second live-action vertical 9:16 scene in which <Subject 1> discovers that the wardrobe in <Subject 2> is not empty. Three hard-cut shots stay on the same woman and the same room.

retention_analysis:
<Subject 1> (appears in [Shot 1], [Shot 2]): fully_preserved - face, glasses, beauty mark, hair, cream cardigan, and dark skirt are retained; the white studio backdrop of <Picture 1> is not used.
<Subject 2> (appears in [Shot 1], [Shot 2], [Shot 3]): fully_preserved - the living room, tall wardrobe, warm lamp, and moonlight are retained.
Unused image, video, and audio placeholders: weak_reference - ignore their content, do not copy.

detailed_description:
The target video is live-action, cinematic, vertical 9:16, with no on-screen text, captions, or UI.
[Shot 1] A medium shot frames <Subject 1> standing in <Subject 2>, phone lowered, listening to the quiet. The camera holds a static shot, locked off, as dust drifts in the moonlight. This shot has no spoken dialogue.
[Shot 2] At 00:04.000, the camera cuts to a medium close-up of <Subject 1> as she turns her head toward the wardrobe. The camera pushes in with small amplitude at slow speed toward her glasses and the beauty mark. <Subject 1> (S1), a young woman with a quiet, slightly tense voice, whispers: <d>[Chinese] 谁在里面？</d>
[Shot 3] At 00:08.000, the camera cuts to a close-up of the wardrobe door in <Subject 2>, a dark seam opening a finger's width, a wet glint in the gap. The camera pushes in with small amplitude at slow speed toward the seam. This shot has no spoken dialogue. Hold the frame to the end.

overall_soundscape: Old-building wood creaks and distant traffic sit under the room. Fabric shifts as she turns; a single wood-grain creak sounds as the door yields, then the space falls nearly silent.

non_diegetic_music: A very low tense drone, almost inaudible until Shot 3, then a thin high string.
```

## Example: U03 T2VA

```text
integrated_multimodal_description: [Shot 1] Live-action, cinematic, vertical 9:16, one continuous take, do not cut. A medium shot frames a single red paper lantern hanging under a wet stone alley arch at night. Fine rain beads on the stone. The camera pushes in with small amplitude at slow speed toward the lantern as it sways a few centimeters and throws orange light on the wet ground. No people. This shot has no spoken dialogue. Hold the lantern until the end.

overall_soundscape: Light rain ticks on stone with distant dripping water under the arch.

non_diegetic_music: N/A
```

## Example: U02 FL2VA

```text
How the reference pictures align with the target video — Picture 1 (from Shot 1) aligns with the 0.00-second mark of the target video; Picture 2 (from Shot 1) aligns with the 8.00-second mark of the target video.

integrated_multimodal_description: [Shot 1] Live-action, cinematic, vertical 9:16, one continuous take, do not cut. The shot begins from Picture 1: a closed wooden wardrobe in cold moonlight. The camera holds a static shot, locked off, as the door eases open a finger's width and moonlight crawls across the grain, ending exactly on the pose, gap, and reflecting eye established by Picture 2. No people. This shot has no spoken dialogue.

overall_soundscape: A wood creak as the door yields, then a held silence.

non_diegetic_music: A single low bowed note that does not resolve.
```
