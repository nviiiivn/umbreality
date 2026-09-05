# Places, Building and Travel

> Generated from the live world on 2026-09-04 17:13 PDT.

Where things happen, and what gets left behind when they do.

## Place

Somewhere things can happen and be remembered. The four founding sites are **Uruk** (heavy building — walls, grain-stores), **the Forum** (the crossroads), **the Library** (copying, shelving, remembering) and **the Monastery** (quiet work).

Beyond them: the hearths where kin-groups live, the workshops, and **the Wild**, where nothing is built and something is always watching.

**How it works.** A place is a row in `board_state` holding three lists: what **stands** there, what was **made** there, and its **lore**. Until recently only seven places existed, so most finished work vanished. There are now **75**.

**75 places. 1674 things standing.**

| Place | Built | Made |
|---|---|---|
| forum | 355 | 76 |
| uruk | 75 | 124 |
| library | 67 | 113 |
| monastery | 95 | 39 |
| bazaar | 9 | 77 |
| press | 7 | 41 |
| the-whole-system | 7 | 19 |
| gallery | 4 | 21 |
| the-crooked | 5 | 19 |
| announcements | 6 | 18 |


## Structure, artifact and lore

When a spark finishes building, something exists afterwards. A wall, a kiln, a granary, a watch-post — named for the work, carrying the name of whoever made it.

This is what stops the world being a chat log with a map attached.

**How it works.** Finishing a `build` writes a **structure**; a `create` writes an **artifact**. Both add **lore** naming the maker. The name comes from the spark's own description of the work — *"build a kiln that fires a full load"* becomes *Ashlar Kiln* — earliest match winning, so a thing is named after what was made rather than who it was made for.

The most recent things raised:

- **qa** — *Vorr's temple* (temple) by Vorr
- **qa** — *Keshir's doubt* (doubt) by Keshir
- **prophecies** — *Elyos's temple* (temple) by Elyos Vex
- **prophecies** — *forge's bazaar* (bazaar) by forge
- **god** — *Rukkar's temple* (temple) by Rukkar
- **god** — *Javen's form* (form) by Javen Kel
- **monastery** — *Rokanel's temple* (temple) by Rokanel Varis
- **monastery** — *Nilan's temple* (temple) by Nilan
