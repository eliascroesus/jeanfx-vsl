# Thank-you video edit

Jean's thank-you video, cut from the raw recording in [`thank-you-raw-footage/`](../thank-you-raw-footage/): AB's
thank-you video beat for beat (measured in [`thank-you-vsl-reference/BREAKDOWN.md`](../thank-you-vsl-reference/BREAKDOWN.md)),
with the graphics built to Iman Gadzhi's standard.

**v2** (after feedback on v1: zooms felt wrong, graphics looked cheap, the music didn't fit):

- **Zooms**: AB's zooms were measured again, frame by frame from the size of his face. He pushes in on the word that
  matters and pulls back out on the next phrase; v1's "staircase" reading was wrong. Jean now pushes in on his key
  words ("extremely **seriously**", "your **phone** in your hand", "super **important**", "why I built **the Elite
  Mentorship**"…) and comes back out on the next phrase, never two pushes in a row. Pushes are small (7–12%): Jean's
  camera is already close.
- **Graphics**: no flat green gradient. Every graphic sits on a 3D money set: $100 bills falling in slow motion at
  three depths, light dust, a slow camera push, film grain. The type is Iman's system: wide caps (Archivo Expanded,
  the free match for Monument Extended), words blurring in on the word, one neon accent with a drawn underline,
  handwritten accent lines, a dot grid, glowing frames around screens, glass icon tiles.
- **Music**: AB's own bed (see below).

| | AB's thank-you | Jean's |
| --- | --- | --- |
| Length | 2:41 | 2:38 (from 11:21 of raw) |
| Text graphics | 9 (8 green, 1 red) | 9 (8 money-green, 1 red), same lines |
| Light-leak flashes | 25 | 23 (only on switches) |
| Proof / screens | Discord carousel, application card, guru thumbnails, testimonial wall | The same four |
| Captions | Word by word, rising in | The same |
| Zoom | Push in on the key word, back out on the next phrase | The same, smaller |
| Music | Soft dark pad on G, no beat, ~19 dB under the voice | AB's own bed, 18 dB under |
| Sound effects | An airy shimmer on every light leak | The same, plus soft pops on the icons, whooshes on the screens, swishes on the guru thumbnails, ticks on the application checks |

## How the raw take was cut

The raw recording is one 11:21 take with restarts, repeated lines and long pauses. For every line the cleanest
complete take was picked (usually the last one), the rest was cut, and pauses were trimmed to AB's pace (none longer
than a quarter-second are left). Every take that went in, with the line it carries, is in `TAKES` at the top of
[`04-edit/scripts/plan_ty.py`](../04-edit/scripts/plan_ty.py); `takes_raw` in `edit.json` has the same list.

Three lines were joined from two takes to drop a repeated phrase:

- "But an actual mentorship | and accountability" (he said "and" twice)
- "And instead, | build the correct psychology | that is needed to be a profitable day trader" (he said "that is
  needed" twice, then re-recorded the end)
- "holding you accountable and showing you | every single part of the trading strategy" (several restarts in between)

Also cut: the first "Yo, what's up? It's Jean here", "and the time" before "and that time", the alternative ending
"…that you've always been wanting" (the "dreaming about" take is used), "Scroll down. Scroll down.", and the chat after
the last line ("That was not easy man…").

## What's on screen, in order

| Time | Jean says | On screen |
| --- | --- | --- |
| 0:00 | "Yo, what's up guys? It's Jean here. I just wanted to thank you for filling out the application…" | Face, opens a touch tight and settles; pushes in on "thank you", "Elite Mentorship" |
| 0:06 | "that **90% of the traders couldn't do**" | "THAT 90%": the number counts up in neon with an underline drawing itself; "of the traders couldn't do" handwritten under it |
| 0:09 | "…one step closer… Therefore, I want to take this extremely seriously…" | Face, in on "changing your life around", out, in on "extremely seriously" |
| 0:17 | "the **consistency, profitability**, and that **time, location and financial freedom**" | "CONSISTENCY / PROFITABILITY", then Time, Location, Freedom in glowing glass tiles, popping in on each word |
| 0:23 | "that you've always been dreaming about" | Face |
| 0:25 | "There's countless other traders inside the Elite Mentorship…" | Discord posts drifting past at three depths in glowing frames, captions on top |
| 0:30 | "so there's no reason why you can't as well. So you might be wondering," | Face |
| 0:34 | "**What are the next steps to actually be part of the Elite Mentorship program?**" | "WHAT ARE THE / NEXT STEPS" + the rest handwritten |
| 0:38 | "Well, as I speak to you right now, one of my best students" | Face |
| 0:41 | "is currently **reviewing your application**…" | The application flies in tilted in a glowing frame, then a scan line runs down it and ticks each field |
| 0:46 | "…have your phone in your hand… this call… I know what you're probably feeling…" | Face, in/out on the key words, phone icons over the captions |
| 1:00 | "**Is this something that I can actually commit to? Will this really work out?**" | Handwritten question, then "WILL THIS REALLY / WORK OUT?" |
| 1:04 | "Etc. And honestly, man, I totally get it." | Face |
| 1:06 | "**The odds are stacked against most people in trading**" | Red money set, a neon red chart line crashing down, "THE ODDS ARE STACKED" |
| 1:09 | "especially right now online… misinformation spread" | Face |
| 1:13 | "with **trading gurus**" | Four guru-style thumbnails slamming in with a glitch |
| 1:16 | "**constantly trying to push a course into your face**" | "CONSTANTLY TRYING TO PUSH / A COURSE / into your face" |
| 1:18 | "or trying to sell you a dream… that's exactly why I built the Elite Mentorship… the right psychology" | Face |
| 1:39 | "**to bulletproof you against the ups and downs in trading**" | Shield in a glass tile, a green line drawing the ups and downs behind |
| 1:42 | "And to be honest… And if you're still wondering whether this works," | Face |
| 2:06 | "scroll down below this video and check out the testimonials from the members themselves" | His shot shrinks into a glowing frame and slides up over the wall of Discord posts, tilted back like a floor |
| 2:11 | "**inside the Elite Mentorship** program" | "INSIDE THE / ELITE MENTORSHIP" over the wall |
| 2:13 | "And remember, these are regular people… So if you want to join the JeanFX Elite Mentorship program…" | Face |
| 2:32 | "**be on the lookout for that call from my team**" | The phone ringing in its tile (rings pulsing out), "BE ON THE LOOKOUT" |
| 2:35 | "Thanks once again for applying. I will see you inside." | Face, pushes in on the last line, ends on his last word |

## The music

It's **AB's own music bed**, taken out of his thank-you video: the voice was separated out (demucs), and everything
above 2.2 kHz was cut, which is where the leftovers of his voice and his shimmer sounds sit (his bed has no content up
there). Measured: a soft, dark pad on G (G, D, F#, Bb), no beat. It sits 18 dB under Jean's voice.

The file isn't in this repo, and it's someone else's licensed track: **before this runs as a paid ad, find out what it
is and license it.** The quickest way is to Shazam AB's thank-you video on a phone (this environment can't reach
Shazam). Upload the original track and it replaces the separated copy (`MUSIC` in `plan_ty.py`).

## Where else it differs from AB, and why

- **The application card is a stand-in.** AB shows his real application page (blurred). There's no screenshot of
  Jean's yet, so it's a white "JeanFX Elite Mentorship Application" form, blurred the same way. Upload a screenshot of
  the real page to this folder and it drops straight in (`ty_assets.py` writes `app_card.png`).
- **The guru thumbnails are made from scratch.** AB flashes four real YouTubers' thumbnails; using real people's
  thumbnails in an ad isn't safe, so these are four loud thumbnail-style cards ("$20 → $53,000", "I MADE $1M TRADING",
  "100% WIN RATE", "QUIT YOUR 9-5") with no people in them.
- **The money set is rendered**, not stock footage: the bills are drawn in 3D from a $100 texture (no licence needed).
- **Loudness**: mastered to −14 LUFS like the main VSL (AB's is −16.4).
- **The source is 23.976 fps**; it's put on a 30 fps grid (like AB's 29.97) before cutting.

## Captions that differ from what Whisper heard

Checked against the takes one by one: "one step closer" (not "want to step"), "mentorship and accountability"
("mentality"), "the right psychology" ("the rights encourage"), "cut the amount of time" ("count"), "prop firm
challenges" ("pro-form"), "JeanFX" ("JunFX"). "Be on the lookout for that call **from** my team" is captioned the way
AB's line reads; Jean's audio is closer to "on my team". All in `PFIX` in `plan_ty.py`.

## Files

| File | What it is |
| --- | --- |
| `edit.json` | The whole edit: kept frames, every element, zoom moves, sound effects, music settings |
| `transcript_cut.json` | Every word of the cut with its time (Whisper large-v3-turbo) |
| `islands.json` | Where there's speech in the raw take (used to trim the pauses) |

The scripts live in [`04-edit/scripts/`](../04-edit/scripts/): `plan_ty.py` (the edit: takes, beats, zoom cues),
`ty_design.py` (v2 graphics: money set, titles, glass icon tiles, framed screens, 3D carousel and wall, guru flashes,
neon chart line, framed shrink), `ty_money_bg.py` (renders the money set), `ty_motion.py` (light leaks, line icons,
word-by-word captions), `ty_assets.py` (application card and guru thumbnails), and the shared `render.py` and `mix.py`
(the shimmer is in `make_sfx`). Fonts are in [`04-edit/fonts/`](../04-edit/fonts/) (OFL). To rebuild: `ty_assets.py` and
`ty_money_bg.py` → `plan_ty.py cut` → `transcribe.py` on the cut voice → `plan_ty.py plan thank-you-edit/edit.json` →
`render.py thank-you-edit/edit.json OUT.mp4`.
