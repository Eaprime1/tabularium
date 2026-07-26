# Assignment — Queen-rank suit missions

**From**: Eric, 2026-07-09
**Why you**: assigned directly — "Gemini for Queens."

## The job

Develop the three Queen-rank suit missions, in this order, per the existing
custos roadmap (`moav/custos_moav_keeper_seed_launch.json`, priority #6):

1. **Diamond of Queen**
2. **Club of Queen**
3. **Heart of Queen**

These are a prerequisite: the same roadmap doc states Jacks of All Trades
(assigned elsewhere) is deliberately sequenced to come *after* these three.
Don't skip ahead on that — if the order looks stale to you, flag it back to
Eric rather than assuming.

## Context you'll need

- `atelier/pjl_synthesis_roadmap.json` (custos, sdcard clone, branch
  `feature/session-202607-blackjack21`) — the suit/rank system: suit
  keepers (Spade/Diamond/Club/Heart/5th) are domain entities, process
  characters (Nullifier/Carbonizer/Decimal/Unknown/Sparklizer) are
  transformation steps. Queens haven't been scoped in that file yet as far
  as this session found — you may be starting closer to a blank slate than
  the King/Queen-of-Spades output entries suggest.
- `atelier/club-of-jacks-carbonite-130-draft.md` — same branch — shows the
  tone/style/density this project's character content is written in
  (Threshold Joker / J-21 as the model). Worth reading before drafting so
  the Queens land in the same voice.
- `reference/mission_data_pack.json` (this repo, once merged) — consolidated
  roster and cross-references for all of this.

## Heads up

The developed content you'll be building from currently lives only on one
branch of one local clone (`/sdcard/pixel8a/custos`,
`feature/session-202607-blackjack21`) — not on `main`. Worth getting
whatever you produce into something more durable than that same branch.
