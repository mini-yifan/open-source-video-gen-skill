# Directing Engine

Use this engine after the director's read. It converts felt intention into a coherent directorial voice and a set of motivated choices.

## 1. One-Intention Law

For each segment, choose one dominant felt intention. Every instrument must either:

- strengthen that intention;
- create a controlled counterpoint that makes it sharper; or
- remain neutral so it does not compete.

If camera says triumph, performance says fear, light says romance, and sound says horror without a deliberate contradiction, the segment has no director.

## 2. Choose a Directorial Voice

Select one primary voice for the episode. A secondary variation may appear only at an explicit pattern break.

| Voice | Performance | Camera and space | Light and sound | Typical use |
|---|---|---|---|---|
| Observational realism | behavior before display; overlaps and imperfect timing | patient frames, motivated reframes, real spatial distance | available-feeling light, truthful room tone | social tension, family conflict, grounded fantasy |
| Intimate minimalism | micro-reactions, withheld speech, precise hands and breath | close access, shallow moves, negative space, few cuts | restrained palette, silence and small sounds | confession, suspicion, emotional injury |
| Restrained classicism | clean objectives, legible reaction order | stable axis, composed coverage, measured push or pull | controlled contrast, clear sonic hierarchy | plot-heavy dialogue, moral choices, reveals |
| Kinetic realism | action under pressure, reactions inside movement | handheld or following movement with spatial anchors | practical light, impacts and breath drive rhythm | chase, escape, physical confrontation |
| Expressive stylization | externalized inner state but still causal | bold angle, scale shift, selective speed or focus changes | shaped color, motifs, subjective sound | magic, rupture, nightmare, emotional peak |
| Graphic coldness | controlled faces, formal gesture, withheld warmth | symmetry, distance, hard geometry, deliberate stillness | hard separation, sparse sound | institutions, judgment, ritual, domination |

Do not copy a filmmaker's surface signature. Choose a voice based on the episode's dramatic need, production limits, references, and H3 reliability.

## 3. Assign Each Instrument a Function

| Instrument | Directing function |
|---|---|
| shot size | regulate intimacy, information, and consequence |
| angle | express access, exposure, or unstable power without caricature |
| lens feel | compress or separate relationships; shape subject-background pressure |
| camera movement | discover, follow, invade, retreat, reveal, reframe, or transfer attention |
| blocking | make objectives and power visible through distance, obstacles, levels, and exits |
| performance | carry reception, containment, leakage, tactic, choice, and aftermath |
| light and color | support visibility, separation, time, danger, transformation, or subjective state |
| sound | define off-screen space, attention, pressure, silence, and transitions |
| duration and cut | allow anticipation, impact, reaction, decision, or release to land |

Name the function before describing the technique. “Slow push-in” is incomplete. “Slow push-in as her practiced calm fails and the room disappears from her attention” is directable.

## 4. Scene-Type Strategies

### Intimate Dialogue

- Direct listening as actively as speaking.
- Protect eye-line and conversational geography.
- Let hands, breath, task, and gaze carry subtext.
- Earn close-ups at a change, not by alternating mechanically.

### Power Confrontation

- Map entrances, exits, height, territory, witnesses, and obstacles.
- Show power before, during, and after the shift.
- Let the losing character attempt a tactic before the frame or blocking confirms loss.
- Use reaction hierarchy: target first when impact matters; aggressor first when intent is the revelation.

### Reveal or Discovery

- Decide who knows, who sees, and when the audience learns.
- Preserve the perception chain: clue -> recognition -> interpretation -> response.
- Do not reveal with camera movement alone if the actor does not register it.
- Let the new fact alter behavior or space within the segment or immediately after it.

### Decision

- Create pressure before stillness.
- Show alternatives in eyeline, object, distance, or opponent.
- Make the physical commitment unmistakable.
- Hold long enough for consequence, then transition on the new state.

### Emotional Low Point

- Reduce display before adding music or visual effects.
- Keep a task, object, or failed routine in the scene.
- Use silence as attention, not emptiness.
- Avoid generic collapse unless the script specifically earns it.

### Action

- Establish geography and objective before complexity.
- Track cause and effect, not decorative motion.
- Preserve one readable hero action per segment.
- Use impacts, breath, footfall, debris, and opponent reaction to complete force.

### Fantasy or VFX Beat

- Anchor the impossible effect to a character decision or perception.
- Define the spatial source, path, environmental response, and human reaction.
- Separate static VFX layout from motion authority.
- Preserve identity and body integrity before increasing spectacle.

### Comedy

- Direct setup, audience expectation, delay, violation, and reaction.
- Protect the straight character and aftermath.
- Do not underline every joke with camera or music.

### Utility Insert

- State one `UTILITY_INTENT`.
- Make the required action or information unmistakable.
- Remove narrative psychology that is not in the source.

## 5. Performance Direction

For each speaking or reacting character, define:

- objective: what they need now;
- obstacle: what blocks it;
- tactic: what they are doing to the other person;
- public behavior: what they choose to show;
- private pressure: what pushes underneath;
- leak: the involuntary visible or audible sign;
- decision: what changes because the tactic succeeds or fails.

Use playable verbs: corner, soothe, test, recruit, shame, distract, delay, provoke, protect. Avoid asking H3 for an emotion without a behavior path.

In ensemble frames, set a focus hierarchy:

1. primary action or speaker;
2. target reaction;
3. secondary witness reaction;
4. neutral background behavior.

Do not give every person equal intensity. Background extras must not imitate named characters or perform the same reaction simultaneously.

## 6. Camera, Cuts, and Spatial Clarity

Move the camera because:

- a character moves and must remain spatially legible;
- attention transfers to new evidence;
- power or access changes;
- hidden information becomes available;
- the audience is pushed closer to or released from a feeling.

Do not move it merely because the shot is long. Choose stillness when the actor's internal change is the event.

Every cut must have a named reason: new information, reaction priority, power transfer, time compression, spatial clarification, rhythmic impact, or transition bridge. Preserve screen direction unless disorientation is deliberate and readable.

## 7. Light, Color, and Sound

Motivate light from the scene's world when possible. Use light progression to mark time, exposure, isolation, danger, or a subjective break. Do not change palette in every segment.

Design sound in layers:

- dialogue and breath;
- performance sounds: cloth, grip, footfall, object contact;
- environment and off-screen geography;
- designed emphasis or subjective sound;
- music space, including deliberate absence.

Specify which sound leads into the shot, which event earns emphasis, and what carries out. Avoid constant score and constant loudness.

## 8. Long-Form Spine

Track these fields across the episode:

```text
ARC_POSITION
SCALE_TREND
MOVEMENT_TREND
LIGHT_TREND
BLOCKING_TREND
SOUND_TREND
PATTERN_BREAK
```

Example progression: public wide frames -> narrowing two-shots -> earned close access -> one abrupt wide after betrayal. A pattern break is powerful only when the preceding pattern is stable.

## 9. Consistency Check

Before locking a director card, ask:

- Does this choice serve `FELT_INTENT` or merely look cinematic?
- Can the performance carry the turn without explanatory effects?
- Is POV consistent with who receives information?
- Is the power shift visible in body, space, or response?
- Is the camera movement motivated and executable within the segment duration?
- Will the cut preserve the reaction and aftermath?
- Does this shot advance the episode spine rather than reset style?
