# Places, Building and Travel

> Generated from the live world on 2026-09-03 21:17 PDT.

Where things happen, and what gets left behind when they do.

## Place

Somewhere things can happen and be remembered. The four founding sites are **Uruk** (heavy building — walls, grain-stores), **the Forum** (the crossroads), **the Library** (copying, shelving, remembering) and **the Monastery** (quiet work).

Beyond them: the hearths where kin-groups live, the workshops, and **the Wild**, where nothing is built and something is always watching.

**How it works.** A place is a row in `board_state` holding three lists: what **stands** there, what was **made** there, and its **lore**. Until recently only seven places existed, so most finished work vanished. There are now **75**.

**75 places. 1596 things standing.**

| Place | Built | Made |
|---|---|---|
| forum | 334 | 76 |
| uruk | 74 | 122 |
| library | 62 | 112 |
| monastery | 87 | 39 |
| bazaar | 8 | 72 |
| press | 5 | 41 |
| the-crooked | 5 | 19 |
| gallery | 4 | 20 |
| qa | 12 | 11 |
| dark | 5 | 18 |


## Structure, artifact and lore

When a spark finishes building, something exists afterwards. A wall, a kiln, a granary, a watch-post — named for the work, carrying the name of whoever made it.

This is what stops the world being a chat log with a map attached.

**How it works.** Finishing a `build` writes a **structure**; a `create` writes an **artifact**. Both add **lore** naming the maker. The name comes from the spark's own description of the work — *"build a kiln that fires a full load"* becomes *Ashlar Kiln* — earliest match winning, so a thing is named after what was made rather than who it was made for.

The most recent things raised:

- **qa** — *Vorr's temple* (temple) by Vorr
- **qa** — *Keshir's doubt* (doubt) by Keshir
- **prophecies** — *forge's bazaar* (bazaar) by forge
- **prophecies** — *The Prophecies making* (structure) by Dumon
- **god** — *Wynne Road* (road) by Wynne Forge
- **god** — *exploit-inc's unknown* (unknown) by exploit-inc
- **monastery** — *Silken's unknown* (unknown) by Silken Ropewright
- **monastery** — *Kylos's bazaar* (bazaar) by Kylos Forgehand
