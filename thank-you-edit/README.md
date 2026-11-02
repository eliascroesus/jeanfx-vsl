# Thank-you video edit

Jean's thank-you video, cut from the raw recording in [`thank-you-raw-footage/`](../thank-you-raw-footage/) and
edited 1:1 in the style of AB's thank-you video (every element measured in
[`thank-you-vsl-reference/BREAKDOWN.md`](../thank-you-vsl-reference/BREAKDOWN.md)).

| | AB's thank-you | Jean's |
| --- | --- | --- |
| Length | 2:41 | 2:38 (from 11:21 of raw) |
| Text cards | 9 (8 green, 1 red) | 9 (8 green, 1 red), same lines |
| Light-leak flashes | 25 | 26 |
| Proof / screens | Discord carousel, application card, guru thumbnails, testimonial wall | The same four |
| Captions | Word by word, rising in | The same |
| Music | Soft pad on G, no beat, ~18 dB under the voice, lifts for the last 40 s | The same, built from orchestra recordings |
| Sound effects | An airy shimmer on every light leak, nothing else | The same |

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

| Time | Jean says | On screen (AB's element) |
| --- | --- | --- |
| 0:00 | "Yo, what's up guys? It's Jean here. I just wanted to thank you for filling out the application…" | Face, opens tight and pulls out, captions |
| 0:06 | "that **90% of the traders couldn't do**" | Green card "That 90%" / "of the traders couldn't do" |
| 0:09 | "…one step closer… Therefore, I want to take this extremely seriously…" | Face, staircase zooms |
| 0:17 | "the **consistency, profitability**, and that **time, location and financial freedom**" | Green card "Consistency / Profitability", then Time, Location, Freedom icons in dashed circles |
| 0:23 | "that you've always been dreaming about" | Face |
| 0:25 | "There's countless other traders inside the Elite Mentorship…" | Discord posts sliding left on the green plate, captions on top |
| 0:30 | "so there's no reason why you can't as well. So you might be wondering," | Face |
| 0:34 | "**What are the next steps to actually be part of the Elite Mentorship program?**" | Green card, four lines building |
| 0:38 | "Well, as I speak to you right now, one of my best students" | Face |
| 0:41 | "is currently **reviewing your application**…" | The application page as a white card, blurred, zooming up from tiny |
| 0:46 | "…have your phone in your hand… this call… I know what you're probably feeling…" | Face, staircase zooms, phone icons over the captions |
| 1:00 | "**Is this something that I can actually commit to? Will this really work out?**" | Green card, two lines (second bigger) |
| 1:04 | "Etc. And honestly, man, I totally get it." | Face |
| 1:06 | "**The odds are stacked against most people in trading**" | Red card with the falling chart line |
| 1:09 | "especially right now online… misinformation spread" | Face |
| 1:13 | "with **trading gurus**" | Four guru-style thumbnails, one after another |
| 1:16 | "**constantly trying to push a course into your face**" | Green card, two lines |
| 1:18 | "or trying to sell you a dream… that's exactly why I built the Elite Mentorship… the right psychology" | Face, staircase zooms |
| 1:39 | "**to bulletproof you against the ups and downs in trading**" | Green card with a shield icon |
| 1:42 | "And to be honest… And if you're still wondering whether this works," | Face, staircase zooms |
| 2:06 | "scroll down below this video and check out the testimonials from the members themselves" | His shot shrinks into a card and slides up over a wall of Discord posts scrolling up |
| 2:11 | "**inside the Elite Mentorship** program" | "Inside the / Elite Mentorship" over the wall |
| 2:13 | "And remember, these are regular people… So if you want to join the JeanFX Elite Mentorship program…" | Face |
| 2:32 | "**be on the lookout for that call from my team**" | Green card with a ringing phone |
| 2:35 | "Thanks once again for applying. I will see you inside." | Face, ends on his last word |

## Where it differs from AB, and why

- **The application card is a stand-in.** AB shows his real application page (blurred). There's no screenshot of
  Jean's yet, so it's a white "JeanFX Elite Mentorship Application" form (name, email, phone, a blue submit button),
  blurred the same way. Upload a screenshot of the real page to this folder and it drops straight in
  (`ty_assets.py` writes `app_card.png`).
- **The guru thumbnails are made from scratch.** AB flashes four real YouTubers' thumbnails; using real people's
  thumbnails in an ad isn't safe, so these are four loud thumbnail-style cards ("$20 → $53,000", "I MADE $1M TRADING",
  "100% WIN RATE", "QUIT YOUR 9-5") with no people in them.
- **Music**: AB's track can't be identified, so the bed is built the same way: a soft string pad (VSCO 2 Community
  Edition, CC0) on a G chord, low-passed, no beat, 18 LU under the voice, lifting 3.5 dB in the low end for the last
  40 s. Free to use in ads.
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

The scripts live in [`04-edit/scripts/`](../04-edit/scripts/): `plan_ty.py` (the edit), `ty_motion.py` (cards, light
leaks, icons, carousel, application card, guru thumbnails, shrink-and-slide, testimonial wall, word-by-word text),
`ty_assets.py` (application card and guru thumbnails), `pad.py` (the music bed), and the shared `render.py` and
`mix.py` (the shimmer is in `make_sfx`). To rebuild: `ty_assets.py` → `plan_ty.py cut` → `transcribe.py` on the cut
voice → `plan_ty.py plan thank-you-edit/edit.json` → `render.py thank-you-edit/edit.json OUT.mp4`.
