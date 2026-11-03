# FAQ videos

Jean's FAQ videos, cut from the raw clips in the [FAQ raw footage release](https://github.com/eliascroesus/jeanfx-vsl/releases/tag/faq-raw-footage)
and edited exactly like the thank-you video v2 (see [`thank-you-edit/README.md`](../thank-you-edit/README.md)): the 3D
money set behind every graphic, wide caps blurring in word by word with the neon-green accent and drawn underlines,
handwritten accent lines, glass icon tiles, result screenshots in glowing frames, word-by-word captions, light-leak
flashes with the shimmer, and push-in / pull-out zooms on the key words. **No music**, as asked.

| Folder | Raw clip | The question | Raw → cut |
| --- | --- | --- | --- |
| [`0321/`](0321/) | `DJI_…_0321_D.MP4` | **Is JeanFX legit?** (the proof walkthrough) | 5:42 → 2:23 |
| [`0322/`](0322/) | `DJI_…_0322_D.MP4` | **Will I work with Jean or with his assistant?** | 1:28 → 0:51 |
| [`0323/`](0323/) | `DJI_…_0323_D.MP4` | **Can I do this with a full-time job?** | 1:55 → 0:51 |
| [`0324/`](0324/) | `DJI_…_0324_D.MP4` | **Do I need a lot of money to start trading?** | 3:00 → 1:59 |

`DJI_…_0320_D.MP4` (1:47) is only false starts of "Is JeanFX legit?", all re-recorded in 0321, so it isn't edited.

## How each was cut

Each raw clip has restarts and pauses. For every line the cleanest complete take is used (usually the last), the rest
is cut, and pauses are trimmed to the thank-you video's pace. The takes, with the line each carries, are in
[`04-edit/scripts/faq_videos.py`](../04-edit/scripts/faq_videos.py). Cut from 0321: "Hey, boy, remember to cut this",
"recording stopped", the Alpha Capital login code, the "qualified trader" restarts and the run of payout amounts
Whisper couldn't read cleanly.

## What's on screen

**0321 Is JeanFX legit?** "IS JEANFX LEGIT?" card → his results drifting past at three depths on "my students and my
payouts" → his Topstep payout in a glowing frame, then **$36,000** counting up ("in profit, just this year") → FTMO
rewards → **$70,000+** "in just under 4 months" → Alpha Capital $4,956 → a red card, **$12,000** "that I never got to
receive" → the Discord reviews one after another, each on its word (a student's Phase 1, his FTMO reward, a payout post,
Rome funded, his $1,680 Equity Edge payout, a student's payout request, Desmond's $341, Errol's Phase 2) → the Discord
wall drifting past → "BEGINNER → ADVANCED" with a rising neon line.

**0322 Jean or his assistant?** Question card → "ONE-ON-ONE / with me, personally" → the Discord community on "my
assistant answers Q&As in the Discord" → hourglass tile and **6 MONTHS** counting up → Consistent / Disciplined / Show
up tiles → results on "let me show you how you can make money" → "NOT MY ASSISTANT / WITH ME." → the application.

**0323 Full-time job?** Question card → **YES.** "you can still learn how to trade" → 3 SESSIONS: London, New York,
Asia tiles → "I TRADE 2 SESSIONS / Asia is late at night for me" → "YOU DON'T HAVE TO / QUIT YOUR JOB" → his own photos
from his 9-to-5 days (the Schlotzsky's shirt, a night DoorDash drop-off) → his results on "trading helped me get to the
next level".

**0324 Do I need a lot of money?** Question card → "$10K? $20K? $30K?" → "YOU DON'T NEED / $10K … $50K" in red → **2026**
"is not 2015" → PROP FIRMS → "PAY $200 / **$100K** / and get paid every 14 days" → his FTMO, Topstep and Alpha Capital
payouts flying in on "these payout certificates" → "I INVESTED $500 / **$35,000**" counting up → his FTMO account on
"one single $100,000 account" → Investment / Discipline tiles → "$100 – $1,000 / to invest in yourself" → JEANFX ELITE
MENTORSHIP → the application → the ringing phone, "BE ON THE LOOKOUT".

## Captions that differ from what Whisper heard

0321: "payouts" ("parents"), "funded trader" ("funny"), "FTMO" ("FTM"), "$4,956" ("$4,900 of $6,000"), "Rome just got
funded" ("ROMS"), "Phase 1 5K" ("case one"), "$19,000 payout" ("$90,000"). 0324: "$200" ("$20,000"), "a fee of $500"
("$500,000"), "2015" ("2020" / "2026"), "prop firms" ("pro firms"), "$500 to $1,000", "JeanFX" ("GeneFX"). All in
`pfix` in `faq_videos.py`.

## Check with Jean

- **0321's amounts are read off his screen**, which isn't in these clips, so the screenshots shown are the matching ones
  from `02-results-and-b-roll/` (his Topstep payout card, FTMO rewards, Alpha Capital $4,956, the Discord posts). The
  numbers on the counters are the ones he says ($36,000, $70,000+, $12,000). If he has the screen recording, upload it
  and it can go in instead.
- **0324** says "pay $200 to get access to over $100,000" and later "a fee of $500" for a $100K account; both are on
  screen as he says them.

## Files

Each folder has `edit.json` (the whole edit), `transcript_cut.json` (every word of the cut) and `islands.json` (where
there's speech in the raw clip). Scripts: [`plan_faq.py`](../04-edit/scripts/plan_faq.py) (the shared engine, built on
the thank-you planner), [`faq_videos.py`](../04-edit/scripts/faq_videos.py) (clips, takes, caption fixes),
[`faq_beats.py`](../04-edit/scripts/faq_beats.py) (what's on screen in each). To rebuild one:
`plan_faq.py KEY cut` → `transcribe.py` on the cut voice → `plan_faq.py KEY plan faq-edit/KEY/edit.json` →
`render.py faq-edit/KEY/edit.json OUT.mp4`.
