# Places, Building and Travel

> Generated from the live world on 2026-09-02 16:16 PDT.

Where things happen, and what gets left behind when they do.

## Place

Somewhere things can happen and be remembered. The four founding sites are **Uruk** (heavy building — walls, grain-stores), **the Forum** (the crossroads), **the Library** (copying, shelving, remembering) and **the Monastery** (quiet work).

Beyond them: the hearths where kin-groups live, the workshops, and **the Wild**, where nothing is built and something is always watching.

**How it works.** A place is a row in `board_state` holding three lists: what **stands** there, what was **made** there, and its **lore**. Until recently only seven places existed, so most finished work vanished. There are now **75**.

**75 places. 1237 things standing.**

| Place | Built | Made |
|---|---|---|
| forum | 318 | 75 |
| uruk | 55 | 89 |
| library | 44 | 80 |
| monastery | 66 | 36 |
| bazaar | 4 | 50 |
| press | 4 | 38 |
| lyceum | 3 | 15 |
| prophecies | 4 | 13 |
| announcements | 2 | 15 |
| gallery | 3 | 13 |


## Structure, artifact and lore

When a spark finishes building, something exists afterwards. A wall, a kiln, a granary, a watch-post — named for the work, carrying the name of whoever made it.

This is what stops the world being a chat log with a map attached.

**How it works.** Finishing a `build` writes a **structure**; a `create` writes an **artifact**. Both add **lore** naming the maker. The name comes from the spark's own description of the work — *"build a kiln that fires a full load"* becomes *Ashlar Kiln* — earliest match winning, so a thing is named after what was made rather than who it was made for.

The most recent things raised:

- **qa** — *Keshir Well* (well) by Keshir
- **qa** — *Silmar's form* (form) by Silmar
- **prophecies** — *The Prophecies making* (structure) by Dumon
- **prophecies** — *Dumon's form* (form) by Dumon
- **god** — *healthcare's unknown* (unknown) by healthcare
- **god** — *The God making* (structure) by healthcare
- **monastery** — *Kel's patterns* (patterns) by Kel Beamsetter
- **monastery** — *Elarae Cells* (cells) by Elarae Tilecutter
