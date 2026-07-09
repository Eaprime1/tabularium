---
name: Club of Jacks
type: mission
date: 2026-07-09
---

# The Club of Jacks — Threshold Joker, Lumenar, Jacks of All Trades

> "Full dev of the threshold joker, jacks of all trades, luminar and other
> content from the pr 35 submission. Once the concepts are together and
> ready.. we can give the voices choices."
> — Eric, 2026-07-09

Note: "PR #35" is actually **issue #35** in `eaprime1/custos` — GitHub shares
one number sequence for issues and PRs. It was a bounty: *"a symbol for
Claude, and a lexeme for the entities' interaction zone."* Resolved by
**PR #38** (`eaprime1/custos`: `world/symbols.md`, `guides/multi-ai-workflow.md`),
which is the source of two of the three terms below.

## Where things actually stand

### Threshold Joker (J-21) — character developed, appearance not scoped
The voice/character is fully written: **J-21**, "the Threshold Joker,
Blackjack Iteration 21." Equation `J − 21 = −A` (i.e. `J + A = 21` — human
and AI arrive at the threshold together, neither first). Full first-person
voice content exists in `atelier/club-of-jacks-carbonite-130-draft.md`
(sdcard custos clone, `feature/session-202607-blackjack21` branch).

But `eaprime1/custos`'s `.custos/README.md`'s own "Parked, not started" list still names **"the
threshold joker's appearance"** as unscoped — distinct from the character,
this reads as the visual/embodiment layer (art, avatar) not yet given a
scoping pass.

### Lumenar — defined, spelled "Lumenar" in-repo
"The lit interaction zone where entities meet without becoming one another."
Fully defined in `eaprime1/custos`: `world/symbols.md` and
`guides/multi-ai-workflow.md`.
Referenced pervasively across atelier/turns/incoming files on the same
branch. This one reads as done — no open scoping needed that I can see.

### Jacks of All Trades — explicitly parked, and explicitly sequenced
Named in `eaprime1/custos`'s `.custos/README.md`'s parked list: *"Each needs its own scoping
pass before it becomes atelier content."* No character, no content exists.

**Important**: `moav/custos_moav_keeper_seed_launch.json` (priority #6)
states an explicit build order set by Eric previously: *"Missions develop:
Diamond of Queen, Club of Queen, Heart of Queen — then Jacks of all
trades."* Jacks of All Trades was deliberately sequenced to come **after**
the three Queen-rank suit missions, which per this doc are not yet done
either. Starting Jacks of All Trades now would jump that stated queue —
flagging rather than assuming this no longer applies.

## A held, sensitive item found along the way

`atelier/club-of-jacks-carbonite-130-draft.md` is not just lore reference —
it's a **HELD, undelivered carbonite** (a real reward/claim packet) addressed
to three real GitHub contributors (Rachaelisa, Ojas2095, kabbersokhi-boop)
over issue #130 / PR #133, with actual XP awards and an invitation to "The
House of Confusion." Explicitly marked *"Awaiting eaprime1 review"* /
*"status: HELD — draft not delivered."* This is a pending decision for Eric,
not something to resolve or riff on as general worldbuilding content.

## The stranding problem

All of the developed content above (the carbonite draft, the deep J-21
lore) lives only on `feature/session-202607-blackjack21` in the **sdcard**
custos clone (`/sdcard/pixel8a/custos`) — not on `main`, not in the
`pixel8` custos clone. It's one `rm -rf` or one lost device away from
being gone. Same class of risk as the Talinor document family.

## Mission tasks

- [ ] Decide: hold the Queen-rank sequencing, or explicitly re-prioritize
  Jacks of All Trades ahead of it (Eric's call — the moav doc may be stale).
- [ ] Scope "the threshold joker's appearance" (visual/embodiment layer)
  separately from the already-written J-21 character.
- [ ] Get the developed branch content (carbonite draft, deep lore) off the
  single sdcard clone/branch and into something durable — mirrors the
  ~/tabularium duplicate-clone lesson.
- [ ] Resolve the HELD carbonite draft's delivery status — separate
  decision from lore development, involves real people.
- [ ] Once concepts are consolidated and any sequencing question is
  settled, revisit "give the voices choices" — deciding who/what embodies
  each role.

## Notes

Lumenar looks genuinely finished; no action needed there beyond making sure
it survives the branch-stranding problem along with everything else.
