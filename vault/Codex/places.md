# Places, Building and Travel

> Generated from the live world on 2026-09-08 18:11 PDT.

Where things happen, and what gets left behind when they do.

## Place

Somewhere things can happen and be remembered. The four founding sites are **Uruk** (heavy building — walls, grain-stores), **the Forum** (the crossroads), **the Library** (copying, shelving, remembering) and **the Monastery** (quiet work).

Beyond them: the hearths where kin-groups live, the workshops, and **the Wild**, where nothing is built and something is always watching.

**How it works.** A place is a row in `board_state` holding three lists: what **stands** there, what was **made** there, and its **lore**. Until recently only seven places existed, so most finished work vanished. There are now **75**.

**75 places. 3079 things standing.**

| Place | Built | Made |
|---|---|---|
| forum | 512 | 107 |
| uruk | 102 | 224 |
| library | 108 | 190 |
| monastery | 170 | 65 |
| bazaar | 10 | 173 |
| temple | 91 | 35 |
| press | 9 | 69 |
| the-whole-system | 19 | 54 |
| coliseum | 14 | 56 |
| lyceum | 4 | 57 |


## Structure, artifact and lore

When a spark finishes building, something exists afterwards. A wall, a kiln, a granary, a watch-post — named for the work, carrying the name of whoever made it.

This is what stops the world being a chat log with a map attached.

**How it works.** Finishing a `build` writes a **structure**; a `create` writes an **artifact**. Both add **lore** naming the maker. The name comes from the spark's own description of the work — *"build a kiln that fires a full load"* becomes *Ashlar Kiln* — earliest match winning, so a thing is named after what was made rather than who it was made for.

The most recent things raised:

- **qa** — *Karnum's temple* (temple) by Karnum
- **qa** — *archive-history's temple* (temple) by archive-history
- **prophecies** — *forge's wild* (wild) by forge
- **prophecies** — *Elyos's temple* (temple) by Elyos Vex
- **god** — *Kel Well* (well) by Kel Wellsinker
- **god** — *Rukkar Road* (road) by Rukkar
- **monastery** — *Khazad Ropewalk* (ropewalk) by Khazad
- **monastery** — *Joric Roof* (roof) by Joric Roofer
