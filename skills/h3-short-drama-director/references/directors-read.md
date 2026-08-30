# Director's Read

Read the episode as drama before choosing shots. The goal is to turn approved narrative meaning into visible and audible evidence.

## 1. Source Lock

Record exact paths and approval state for:

- Brief;
- complete episode outline;
- episode dialogue timeline;
- episode script;
- art bible and approved reference assets;
- previous episode ending or previous accepted clip when continuity depends on it.

Precedence inside the approved package:

1. The dialogue timeline controls speaker, wording, order, and duration.
2. The approved script controls playable actions, dramatic causality, staging facts, and emotional beats.
3. The episode outline controls the episode's structural promise and result.
4. The Brief controls the series promise, audience, tone, limits, and platform constraints.
5. The approved art bible controls character and world identity.

If two approved sources disagree, do not repair the contradiction invisibly. Write:

```text
SOURCE_CONFLICT
- source_a: <path and precise fact>
- source_b: <path and precise fact>
- affected_segments: <ids>
- decision_needed: <the smallest question that resolves it>
```

Continue directing unaffected material.

## 2. Select the Lane

Use the narrative lane for short drama. It requires character intention, power, subtext, reaction, and change.

For a non-narrative insert such as a pure product, interface, or informational shot, define `UTILITY_INTENT` instead: the one fact, feature, or action the audience must perceive. Mark narrative-only fields `NON_NARRATIVE_REFUSAL` rather than manufacturing fake psychology.

## 3. Episode Read

Fill these fields before segmenting:

```text
EPISODE_FUNCTION: What this episode must accomplish in the series.
VALUE_TURN: The dominant state that changes, written A -> B.
PRIMARY_POV: Whose perception organizes audience access.
POWER_ARC: Who holds power at the start, how it moves, and who holds it at the end.
AUDIENCE_FEELING: What the audience should feel by the final beat.
CORE_SUBTEXT: The important meaning nobody states directly.
NON_TRANSFERABLE_DETAIL: The specific behavior, object, spatial fact, or image that makes this episode irreplaceable.
STOCK_SOLUTION_REFUSED: The most obvious generic directing solution that will be avoided.
FINAL_IMAGE: The image and sound that should remain after the episode ends.
NEXT_EPISODE_QUESTION: The concrete viewing question created by that final image.
```

`VALUE_TURN` should be playable: protected -> exposed, superior -> cornered, suspicious -> committed, isolated -> allied. Avoid vague labels such as “more dramatic.”

## 4. Segment Read

For each prospective segment, fill:

```text
DRAMATIC_FUNCTION
VALUE_BEFORE
VALUE_AFTER
FELT_INTENT
POV
POWER_START
POWER_END
POWER_SHIFT_TRIGGER
HIDDEN_OBJECTIVE
OBSTACLE
TACTIC
SUBTEXT_OR_CONTRADICTION
VISIBLE_SUPPRESSED_BEHAVIOR
NON_TRANSFERABLE_DETAIL
STOCK_SOLUTION_REFUSED
```

`FELT_INTENT` is the audience experience, not a camera instruction. Examples: “feel the room turn against her before she notices,” “share his effort to hide recognition,” “experience the offer as a trap.”

If a segment contains two unrelated felt intentions or two decisive value turns, split it unless the collision itself is the point.

## 5. Convert Meaning into Evidence

Never leave an abstract directing word unsupported. Use visible or audible carriers:

| Abstract idea | Useful carriers |
|---|---|
| intimidation | distance invaded, exit blocked, opponent forced to look up, breath held, room tone thins |
| concealment | gaze avoids the evidence, hand covers an object, answer arrives too quickly, body shields space |
| status loss | frame ownership narrows, seated figure must rise, others stop following their eyeline |
| attraction resisted | involuntary orientation, delayed withdrawal, interrupted breath, hands stay controlled |
| grief contained | task continues mechanically, jaw or fingers take the strain, voice stays practical until one leak |
| decision | stillness before action, eyeline locks, breath resets, hand releases or commits, spatial direction changes |
| revelation | perception changes before explanation, background or sound recontextualizes, reaction completes the fact |

Use specific body behavior. “She is angry” is not directable. “She keeps her voice level, stops blinking, folds the torn letter once too carefully, then places it between them” is.

## 6. Short-Drama Performance Chain

Build important beats in this order:

1. trigger arrives;
2. instinctive reception;
3. containment, denial, or redirection;
4. one visible leak;
5. choice, action, or line;
6. opponent reaction;
7. situation changes;
8. aftermath lands.

Compress duration by shortening stages, not by deleting causality. The audience should still be able to see what caused the turn.

## 7. Self-Check

Before moving to shot design, verify:

- Could another unrelated scene use the same read unchanged? If yes, it is too generic.
- Does every emotion have a trigger, visible carrier, and consequence?
- Is POV about information and access, not merely camera position?
- Does the power shift change space, behavior, choice, or response?
- Is the non-transferable detail protected from later simplification?
- Is the refused stock solution clear enough to prevent generic coverage?
