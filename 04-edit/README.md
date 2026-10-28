# Edit

How Jean's VSL is put together, 1:1 in the style of AB Nasdaq's VSL (every element measured in
[`01-vsls/reference-vsls/AB-BREAKDOWN.md`](../01-vsls/reference-vsls/AB-BREAKDOWN.md)). Nothing in here needs
uploading; it's the editing setup.

## Pieces

| Script | What it does |
| --- | --- |
| `scripts/transcribe.py` | Word-level transcript (Whisper large-v3-turbo) → `transcript.json` |
| `scripts/plan.py` | **The edit.** Every visual is anchored to Jean's own words, so it reads like the script. Writes `edit.json`: cuts, elements, AB's zoom moves, captions, sound effects |
| `scripts/render.py` | Renders `edit.json`: the cut A-roll with zooms, every element drawn on top, in parallel chunks; then muxes the audio |
| `scripts/elements.py` | Every AB element: plates, cards, counters, the "Available Balance" pill, PIP name card, split screen, slide-up transition, text behind his head, rolling list, Discord wall, chart animations, B-roll stills |
| `scripts/fx.py` | AB's text: Inter Display (closest free match to SF Pro Display), his sizes and tight spacing, the letter-by-letter blur-in, soft shadow, blue glow |
| `scripts/money.py` | The money drop (bills tumbling in 3D with motion blur and depth blur), the money B-roll, flames |
| `scripts/mix.py` | Voice clean-up, the song bed 12 LU under the voice (3 dB above AB's level, as asked in v3; constant, never ducked), sound effects (+2.5 dB in v3; money sounds built from VSCO 2 CE recordings, CC0), mastered to −14 LUFS |
| `scripts/song_bed.py` | "Me And The Devil" (instrumental) with the boom removed, looped the way AB loops it |
| `scripts/assets.py` | Certificate crops from the Discord screenshots in `02-results-and-b-roll/`, the blurred chart, signal card, phone mockup, "account breached" email, 3D objects |
| `scripts/motion.py` | Motion graphics in place of AB's stock footage: moving light gradients, rising dollar signs, embers, city-light bokeh, self-drawing glowing charts, a neural-network brain, an earnings card, a time card, a marker circle |
| `scripts/proof_clicks.py` | Finds every page switch in Jean's screen recording so each gets a mouse click |
| `scripts/gen_stills.py` | Only used for the $100-bill texture in the money drop (LCM Dreamshaper v7, MIT licence) |

To rebuild: `assets.py` → `gen_stills.py bill_front bill_back` → `proof_clicks.py` → `plan.py` → `render.py`. The song file isn't in this repo (it's
copyrighted and this repo may be public); using it in a paid ad needs a licence.

## What's copied 1:1 from AB

- **Captions**: 2–4 words, lowercase, no punctuation, Inter Display Medium 96 px, spacing −5, white with a soft shadow,
  centred at y 925, hard switch between captions, letter-by-letter blur-in only when a caption appears fresh after a
  graphic, dark fade along the bottom. None during the proof screen recording. Over B-roll they move to the middle.
- **Side text** for the key lines (regular line, heavy caps, key word in his blue #008CFC), each line on its word with
  a click. Jean's shot is dark, so it uses AB's dark-shot version (dark fade, white text), and the shot is held wide
  while it's up.
- **Zoom**: face shots alternate between wide and a 1.22× punch-in (0.3–0.35 s ease-out, or a hard cut), with a slow drift
  while holding. In the proof section the screen recording glides in on each number.
- **Every graphic type**: screenshot flashes on a light-grey plate, PIP name card over a blurred chart, money-drop
  counter, proof screen recording, black counter with a coin flying in, money B-roll with a counter, "Available
  Balance" counting down to $10, white keynote cards, B-roll with captions in the middle, framed "Fear / Greed",
  brain card, two-figure age card, burning bill, rolling list, text behind his head ("ONE SETUP", "INDUCEMENT"), split
  screen with the offer typed as he says it, slide-up transition, trophy + SUCCESS, payout card with money, glowing blue
  caps ("WORK WITH YOU", "FOR FREE", "THE APPLICATION").
- **Music**: the same song, boom removed, at AB's level (15 LU under the voice, never ducked), starting where he starts
  it (0:05.6 into the song) and jumping back the way he does when it reaches ~1:27–1:53.
- **Sound effects**: a crisp tick on every text element, whooshes on switches, a coin swish, a money flutter, a low
  impact before "I put $4,000 in a live account". On top of AB's (v2): a mouse click on every image that pops up and
  on every page switch in the proof screen recording, ticks while counters run and a pop when they land, typing under
  the typed offer list, a soft swish on punch-ins and side text, a notification ding on the "account breached" email,
  a marker sound on the chart circle, and a whoosh on every scene change. v3: a cash-register "cha-ching" (drawer,
  coins, bell, from real recordings) on every money moment, counters that tick up over a rising glockenspiel run and
  land on a cha-ching (the "Available Balance" countdown falls instead and lands on a thud), a fuller money spray under
  the money drops, and a light cha-ching each time Jean says an amount in the proof section.

## Cuts

- "Just start believing it." (AB's line is "…to stop believing it"; Jean's says the opposite)
- The garbled "buy it and scan stuff" aside in the proof section, and the muddled Alpha Capital "old system" aside
- "This will go on for only about 90 days. If you've not made any profits… request a call once every two weeks"
  (reads like a second, different guarantee)
- Pauses over 0.3 s trimmed to 0.12 s

All of them are in `CUTS` at the top of `scripts/plan.py` and can be put back.

## Where it differs from AB, and why

- AB's stock clips and movie clips are licensed footage that can't be copied. Those moments are motion graphics
  instead (v2; the first cut used AI-generated stills, which looked fake): a green gradient with rising dollar signs
  behind "$76,000" and "the money would roll in", a glowing chart drawing itself for "you don't know what you're doing"
  and "go learn one", framed red and green charts for "Fear" and "Greed", a neural-network brain, a weekly-earnings card
  for DoorDash, embers behind "$4,000", city-light bokeh for the night in the car, a time card for the warehouse job,
  and Jean's own chart with a red circle and a review note for "someone to review what you did". AB's 3D objects use
  Microsoft Fluent 3D (MIT).
- Jean-only parts of the script (his DoorDash story, the two problems, the inducement setup, his students) use AB's
  elements in the same way: animated charts for the setup, black student cards with his certificates, the Discord wall.
- AB's master is very quiet (−24 LUFS); this one is mastered to −14 LUFS for YouTube and ads.
- The numbers on screen are the ones Jean says (e.g. $120,000, $76,000). See the questions in
  [`03-raw-vsl-footage/BREAKDOWN.md`](../03-raw-vsl-footage/BREAKDOWN.md) before running it as an ad.

`transcript.json` is Jean's raw video, every word with its start and end time. Times are in the raw video; the
readable version is [`03-raw-vsl-footage/TRANSCRIPT.md`](../03-raw-vsl-footage/TRANSCRIPT.md).
