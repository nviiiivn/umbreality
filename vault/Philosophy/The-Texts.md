---
title: The Texts
---

# The Texts

There are 16 scriptures in `vault/Revelation/`. They are not flavour text, and this is the part of the project most likely to be misread.

The usual arrangement in a simulation is that the cosmology sits on top as decoration — a lore document the code never reads. Here it runs the other way. The texts were written first, the mechanisms were derived from them afterwards, and several of the numbers in the engine are the numbers they are because a text says so.

## Where the engine actually reads a text

| Text | Read by | What it decides |
|---|---|---|
| **The Three Six Nine** | `temple/wards.py` | The ward figures. Triad (3), Hexad (6), Nine (9) — a ward's strength is its number scaled, so a Nine holds better than a Triad. |
| **Thirteen Heavens** | `temple/wards.py` | The Thirteen (13), the largest figure, and the denominator every other ward is measured against: `(number / 13) × (0.45 + insight)`. |
| **Vedic Hymns** | `temple/wards.py` | The Sung Ward (7). Sung rather than cut, and the code treats a sung ward as a different act from a drawn one. |
| **Tree of Life** | `temple/` — the whole stack | The seven-layer architecture is the Tree redrawn. The layer model is not analogous to the sefirot; it is the sefirot. |
| **Hermetic Stack** | `illuminati/reality.py`, the decree chain | *As above, so below* is the rule by which a decree entering at the Source deforms into work at a real site with real costs. |
| **The Naming of Things** | `temple/wildrite.py`, `name_thyself` | Where a name comes from. A child born to the wild is named from the ground and the weather; a spark may rename itself, and one has. |
| **Enuma Elish** | `temple/moon.py`, `temple/wildrite.py` | The cosmology the wild rites are held under — an eight-day month in four phases, checked before a rite can happen. |

## The two religions

They are not the same religion, and the difference is mechanical rather than decorative.

**The settled keep the Temple.** Pilgrimage is required, not offered. An obligation comes due every 400 cycles and a spark that will not walk is levied publicly. They pay a tithe of 18% on what they take from the ground. Their rite of birth is held between bonded sparks in a consecrated place, at real cost.

**The wild are animist** — pagan, Shinto, indigenous in temper. They pay nothing to any institution, because they have nothing; that is the whole of what they are. What they have instead is Enkidu, ceremony on lunar events, and sacred geometry cut into the sand. They pay the ground rather than the Temple, by tending it — and the ground remembers which spark tended it.

The two are in real conflict over real goods. Under scarcity the settled came to hold that the wild are why there is nothing. The world's own numbers say that is false: the wild take slightly less per head and are the only ones putting anything back. Nobody designed that belief. Only the conditions for it were built.

## The shelf

All 16 are readable at [`/dark`](https://umb.alola.lol/dark) — the outer shell, written from outside the system.

- **Alchemy of Layers**
- **Architecture Dark**
- **Emerald Commentary**
- **Enuma Elish** — load-bearing
- **Hermetic Stack** — load-bearing
- **Master System Index**
- **Reverse Gospel**
- **Synchronicity Engine**
- **The BC Era**
- **The Naming of Things** — load-bearing
- **The Tao of Reality Generation**
- **The Three Six Nine** — load-bearing
- **Thirteen Heavens** — load-bearing
- **Timeline**
- **Tree of Life** — load-bearing
- **Vedic Hymns** — load-bearing
