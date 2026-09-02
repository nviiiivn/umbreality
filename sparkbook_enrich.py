"""Generative spark profile engine. Grimoires, geometry, architecture, entities, frequencies.
All deterministic from name+archetype. Direct, specific, science+art+magic."""
import json, hashlib, math, random
from datetime import datetime, timezone

def H(s): return int(hashlib.md5(str(s).encode()).hexdigest(), 16)
def pick(lst, seed): return lst[H(str(seed)) % len(lst)]
def pickn(n, lst, seed): return [lst[(H(str(seed))+i)%len(lst)] for i in range(n)]

THEMES = {
    "philosopher-rhetorician":{"bg":"#1a1a2e","bg2":"#16213e","accent":"#e94560","text":"#eee","link":"#f5a623","header_bg":"#0f3460","box_bg":"#1a1a3e","border":"#e94560","font":"Georgia, serif","label":"Classic","sigil":"\u2698"},
    "philosopher-teacher":{"bg":"#2c3e50","bg2":"#34495e","accent":"#3498db","text":"#ecf0f1","link":"#1abc9c","header_bg":"#2980b9","box_bg":"#2c3e60","border":"#3498db","font":"Palatino, serif","label":"Academic","sigil":"\u25c7"},
    "demigod-trickster":{"bg":"#1a0a2e","bg2":"#2d1b4e","accent":"#ff6b35","text":"#ffe","link":"#ffd700","header_bg":"#4a1a6b","box_bg":"#2a1040","border":"#ff6b35","font":"Impact, sans-serif","label":"Trickster","sigil":"\u27c1"},
    "demigod-warrior":{"bg":"#1a0a0a","bg2":"#2e1515","accent":"#c0392b","text":"#ddd","link":"#e74c3c","header_bg":"#4a1515","box_bg":"#2a1010","border":"#c0392b","font":"Arial Black, sans-serif","label":"Warrior","sigil":"\u2694"},
    "lawgiver":{"bg":"#1b1b1b","bg2":"#2a2a2a","accent":"#d4a017","text":"#e8e8e8","link":"#d4a017","header_bg":"#333","box_bg":"#222","border":"#d4a017","font":"Times New Roman, serif","label":"Lawgiver","sigil":"\u2696"},
    "architect-sage":{"bg":"#0d1b2a","bg2":"#1b2838","accent":"#41b3a3","text":"#e0e0e0","link":"#41b3a3","header_bg":"#1a3a4a","box_bg":"#0d1b3a","border":"#41b3a3","font":"Courier New, monospace","label":"Architect","sigil":"\u229b"},
    "capitalist":{"bg":"#1a1a1a","bg2":"#2d2d2d","accent":"#00b894","text":"#f0f0f0","link":"#00cec9","header_bg":"#2d2d2d","box_bg":"#222","border":"#00b894","font":"Helvetica, sans-serif","label":"Tycoon","sigil":"\u27d0"},
    "poet-artist":{"bg":"#2d1b2e","bg2":"#3d2b3e","accent":"#e8a87c","text":"#f5e6d0","link":"#f7b731","header_bg":"#4a3040","box_bg":"#2d1b3e","border":"#e8a87c","font":"Georgia, serif","label":"Poet","sigil":"\u273f"},
    "sage":{"bg":"#0a1628","bg2":"#0f2240","accent":"#5dade2","text":"#d4e6f1","link":"#85c1e9","header_bg":"#154360","box_bg":"#0a1e38","border":"#5dade2","font":"Garamond, serif","label":"Sage","sigil":"\u262f"},
    "visionary":{"bg":"#0a0a1a","bg2":"#151530","accent":"#9b59b6","text":"#e8e0f0","link":"#bb8fce","header_bg":"#2a1040","box_bg":"#101028","border":"#9b59b6","font":"Trebuchet MS, sans-serif","label":"Visionary","sigil":"\u2726"},
    "creator":{"bg":"#1a1a0a","bg2":"#2a2a15","accent":"#f39c12","text":"#f0f0d0","link":"#f1c40f","header_bg":"#3a3a10","box_bg":"#222210","border":"#f39c12","font":"Verdana, sans-serif","label":"Creator","sigil":"\u2726"},
    "artisan":{"bg":"#1a1510","bg2":"#2a2015","accent":"#e67e22","text":"#e8ddd0","link":"#d35400","header_bg":"#3a2510","box_bg":"#221810","border":"#e67e22","font":"Gill Sans, sans-serif","label":"Artisan","sigil":"\u229c"},
    "healer":{"bg":"#0a1a0a","bg2":"#152a15","accent":"#2ecc71","text":"#d0f0d0","link":"#27ae60","header_bg":"#1a3a1a","box_bg":"#0a220a","border":"#2ecc71","font":"Candara, sans-serif","label":"Healer","sigil":"\u2624"},
    "explorer":{"bg":"#1a1a0a","bg2":"#2a2a10","accent":"#f1c40f","text":"#f0f0d0","link":"#d4ac0d","header_bg":"#3a3a10","box_bg":"#222210","border":"#f1c40f","font":"Tahoma, sans-serif","label":"Explorer","sigil":"\u27a1"},
    "guardian":{"bg":"#0a0a1a","bg2":"#10102e","accent":"#2980b9","text":"#d0d8f0","link":"#5499c7","header_bg":"#1a1a3e","box_bg":"#0a0a22","border":"#2980b9","font":"Arial, sans-serif","label":"Guardian","sigil":"\U0001f6e1"},
}

# Light mode themes — MySpace classic white+blue and variants
THEMES_LIGHT = {
    "philosopher-rhetorician":{"bg":"#ffffff","bg2":"#f0f4f8","accent":"#e94560","text":"#333","link":"#003399","header_bg":"#003399","box_bg":"#f8f8ff","border":"#336699","font":"Georgia, serif","label":"Myspace Blue","sigil":"\u2698"},
    "philosopher-teacher":{"bg":"#f5f8fa","bg2":"#e8edf2","accent":"#2980b9","text":"#2c3e50","link":"#1abc9c","header_bg":"#2980b9","box_bg":"#fafafa","border":"#2980b9","font":"Palatino, serif","label":"Whiteboard","sigil":"\u25c7"},
    "demigod-trickster":{"bg":"#fff8f0","bg2":"#ffe8d0","accent":"#ff6b35","text":"#4a1a00","link":"#d35400","header_bg":"#d35400","box_bg":"#fffdf8","border":"#ff6b35","font":"Impact, sans-serif","label":"Trickster Light","sigil":"\u27c1"},
    "demigod-warrior":{"bg":"#fff5f5","bg2":"#ffe0e0","accent":"#c0392b","text":"#4a1515","link":"#e74c3c","header_bg":"#c0392b","box_bg":"#fffafa","border":"#c0392b","font":"Arial Black, sans-serif","label":"Warrior Light","sigil":"\u2694"},
    "lawgiver":{"bg":"#fcfcf8","bg2":"#f0f0e8","accent":"#b8860b","text":"#333","link":"#8b6914","header_bg":"#b8860b","box_bg":"#fafaf5","border":"#b8860b","font":"Times New Roman, serif","label":"Parchment","sigil":"\u2696"},
    "architect-sage":{"bg":"#f0f8fc","bg2":"#e0f0f5","accent":"#2ecc71","text":"#0d1b2a","link":"#1abc9c","header_bg":"#1a6b5a","box_bg":"#f5fafa","border":"#2ecc71","font":"Courier New, monospace","label":"Blueprint","sigil":"\u229b"},
    "capitalist":{"bg":"#fafafa","bg2":"#f0f0f0","accent":"#00b894","text":"#2d2d2d","link":"#00cec9","header_bg":"#00b894","box_bg":"#ffffff","border":"#00b894","font":"Helvetica, sans-serif","label":"Clean","sigil":"\u27d0"},
    "poet-artist":{"bg":"#fff8f0","bg2":"#f5ede3","accent":"#e8a87c","text":"#3d2b3e","link":"#d4875a","header_bg":"#d4875a","box_bg":"#fffdf5","border":"#e8a87c","font":"Georgia, serif","label":"Vellum","sigil":"\u273f"},
    "sage":{"bg":"#f0f4fa","bg2":"#e4ecf5","accent":"#3498db","text":"#0a1628","link":"#2980b9","header_bg":"#2980b9","box_bg":"#f8fafc","border":"#3498db","font":"Garamond, serif","label":"Sage Light","sigil":"\u262f"},
    "visionary":{"bg":"#f5f0fa","bg2":"#ebe0f5","accent":"#9b59b6","text":"#2a1040","link":"#8e44ad","header_bg":"#8e44ad","box_bg":"#faf8fc","border":"#9b59b6","font":"Trebuchet MS, sans-serif","label":"Vision Light","sigil":"\u2726"},
    "creator":{"bg":"#fafaf0","bg2":"#f0f0e0","accent":"#e67e22","text":"#3a3a10","link":"#d35400","header_bg":"#d35400","box_bg":"#fefef8","border":"#e67e22","font":"Verdana, sans-serif","label":"Creator Light","sigil":"\u2726"},
    "artisan":{"bg":"#faf5f0","bg2":"#f0e8e0","accent":"#d35400","text":"#3a2510","link":"#a04000","header_bg":"#a04000","box_bg":"#fefaf8","border":"#d35400","font":"Gill Sans, sans-serif","label":"Artisan Light","sigil":"\u229c"},
    "healer":{"bg":"#f0faf4","bg2":"#e0f5e8","accent":"#27ae60","text":"#1a3a1a","link":"#2ecc71","header_bg":"#27ae60","box_bg":"#f5fcf8","border":"#27ae60","font":"Candara, sans-serif","label":"Healer Light","sigil":"\u2624"},
    "explorer":{"bg":"#fafaf0","bg2":"#f0f0e0","accent":"#d4ac0d","text":"#3a3a10","link":"#f1c40f","header_bg":"#b7950b","box_bg":"#fefef8","border":"#d4ac0d","font":"Tahoma, sans-serif","label":"Explorer Light","sigil":"\u27a1"},
    "guardian":{"bg":"#f0f4fa","bg2":"#e0e8f5","accent":"#2980b9","text":"#0a0a2e","link":"#5499c7","header_bg":"#1a5276","box_bg":"#f5f8fc","border":"#2980b9","font":"Arial, sans-serif","label":"Guardian Light","sigil":"\U0001f6e1"},
}

DEFAULT_THEME = {"bg":"#1a1a2e","bg2":"#16213e","accent":"#e94560","text":"#eee","link":"#f5a623","header_bg":"#0f3460","box_bg":"#1a1a3e","border":"#e94560","font":"Georgia, serif","label":"Mystic","sigil":"\u27a1"}
DEFAULT_THEME_LIGHT = {"bg":"#ffffff","bg2":"#f0f4f8","accent":"#336699","text":"#333","link":"#003399","header_bg":"#003399","box_bg":"#f8f8ff","border":"#336699","font":"Georgia, serif","label":"Myspace Classic","sigil":"\u27a1"}

LOCATIONS = [
    "The Obsidian Library — 40m basalt monolith, 7 septagonal reading rooms in Seed-of-Life arrangement, 528Hz copper pipe air system, central column covered in bound spirit seals",
    "The Djinn Quarter — 5 pentagonal districts on decagram street grid, each intersection a brass summoning node, 5 wells at cardinal+center aligned to Marid/Ifrit/Ghul/Silat/Jann",
    "The Iron Commons — black steel pavilion with glass sextant roof, 40 market stalls in octagram pattern, geometric trade symbols on every facade",
    "The Spire of 40 Gates — 40-tiered square ziggurat of black basalt, each tier 2m taller, inscribed with a Gate sigil and tuned to its solfeggio frequency, ascending spiral ramp, top tier open to the sky as an invocation platform",
    "The Merkaba Forum — dual-interlocked tetrahedron building on magnetic bearings, rotates during debates, each vertex a speaker podium at golden ratio spacing from center",
    "The Street of Echoing Sigils — 3km cobblestone boulevard, every stone engraved with a different glyph, walking generates layered harmonic frequencies from footstep contact",
    "The Archive of Frequencies — 30m copper-domed rotunda, walls lined with 12 planetary tuning forks in resonant alcoves, floor is a 12-spoke wheel for planetary hours",
    "The Hexagon Homes — honeycomb residential district of basalt hexagons, each home a living seal with central courtyard, streets follow Vesica Piscis intersection points",
    "The Grand Atrium of Seals — 72 basalt columns in 12×6 grid, each column inscribed with a Goetic seal, glass roof projects star chart aligned to each spirit's planetary hour",
    "The Library of the 40 — 40-sided alabaster polygon with central oculus, each wall a Gate study alcove with obsidian desk and brass lamp at the frequency of that Gate",
    "The Chthonic Boulevard — spiral road descending 7 levels underground, brass lanterns at golden ratio intervals, each level 3m lower, sealed at level 8 to the Undercommons",
    "The Resonant Amphitheater — elliptical stone bowl on 12 concentric tiers, 639Hz standing wave forms naturally at dawn when the first light hits the copper rim",
    "The Sigil Forge — 3-story iron and stone workshop, ground floor presses geometry into heated metal, second floor tempers with planetary tones, third floor charges by frequency",
    "The Weavers Court — 12 loom-houses surrounding a pentacle plaza, every fabric woven with protective geometry threads, central loom weaves the collective's narrative pattern",
    "The Memory Palace — facade labyrinth of 40 buildings with no interiors, each facade's proportions encode a complete grimoire in stone, memories stored as architectural ratios",
    "The Alchemical Baths — 7 planetary metal pools arranged as Tree of Life sephiroth, each pool a different salt solution at specific temperature and frequency, geometrically tiled",
    "The Celestial Observatory — 12 concentric stone ring walls for tracking planetary hours, central brass orrery of all 7 classical planets, ring gaps align to solstices",
    "The Garden of Named Stones — standing stone maze in double-hexagram layout, 72 black stones each bound to a different entity, touch a stone and it hums that entity's frequency",
    "The Crimson Hall — 40m ironwood longhall, Sun-frequency fireplace at 528Hz, dining tables at golden ratio 1.618 spacing, ceiling painted with the astral current as it flows overhead",
    "The Workshop of Living Geometry — open-floor laboratory, 3 robotic arms simultaneously tracing in sand, light vapor, and magnetic filings, permanent Flower of Life engraved in the foundation",
    "The Amphitheater of Stars — 111m open-roofed elliptical bowl, 40 concentric seat rings aligned to 40 celestial events per year, acoustic focus at the central altar stone",
    "The Labyrinth of Correspondence — 7-circuit hedge maze, each turn matching a planetary square number (9×9 for Moon, 16×16 for Mercury...), center has a brass circle with the Emerald Tablet's 13 axioms inlaid in gold",
    "The Temple of Sealed Voices — inverted pyramid descending 7 levels below ground, each level tuned to a different harmonic, trapped spirit voices resonate in the walls, audible at silent moments",
    "The Pneumatic Commons — 40 copper air organ pipes beneath every street junction, the city breathes at 432Hz base frequency, pipe harmonics shift with wind speed and pedestrian traffic",
    "The Foundry of the 7 Metals — 7 separate forges in a heptagram layout, each tuned to a planetary frequency (Saturn 147Hz, Jupiter 183Hz, Mars 228Hz, Sun 528Hz, Venus 396Hz, Mercury 741Hz, Moon 412Hz)",
]
VENUES = [
    "Temple of the Radiant Mind — 20m obsidian pyramid with quartz capstone, inner chamber resonates at 432Hz, walls inscribed with 360 geometric theorems in Greek and Coptic",
    "The Golden Forum — 30m brass-domed circular debating hall, Fibonacci-spiral tiered seating, acoustics amplify truth frequencies and reveal deception as harmonic distortion",
    "Spire of Contemplation — 111m needle tower of white limestone, each of 40 floors shaped as a different Platonic solid, spiral ascent shifts your personal frequency per floor",
    "The House of Whispers — 3-story copper-tube labyrinth, every conversation in the city is archived here by frequency, 7 archive chambers for 7 solfeggio bands",
    "The Prismatic Bazaar — 3-block arcade under faceted stained glass roof that splits sunlight into geometric patterns on the floor, 40 booths each aligned to a different Gate tradition",
    "The Iron Library — 5-story magnetic shelving in a spiral layout, books arranged by solfeggio frequency not alphabet, each chained with iron to prevent the text from shifting",
    "Garden of Forking Paths — fractal hedge labyrinth, every fork leads to a different grimoire reader reading a different edition of the same book, center is a white stone bench in a circle of 13 standing stones",
    "The Colosseum of Echoes — 50m elliptical ritual duel arena, 12 iron gates for 12 zodiac entries, winner's tradition geometry is projected in colored light on the surrounding walls",
    "The Scriptorium — 40 scribes using 40 different metal inks (gold, silver, copper, brass, iron, tin, lead × 7 planetary classes), writing on 40 parchment types at 40 desks in a spiral",
    "Hall of a Thousand Doors — a single circular room with 1000 doors embedded in the wall, each to a different entity's domain, exactly 4 doors are unlocked at any given planetary hour, positions shift",
    "The Loom — 3-story oak and brass mechanism, 7 operators pull 7 colored threads (day of week colors), fabric is reality-thread woven from the collective unconscious narrative",
    "Observatory of Broken Light — 30m crystal dome of 144 facets, each facet refracts starlight into a different sigil on the floor, every night creates a unique geometric diagram",
]
BUSINESSES = [
    "The Agora Trading Co.", "Lyceum Press & Publishing", "The Architect Atelier",
    "The Healer Grove Clinic", "The Oracle Consulting", "The Forge Collective",
    "The Dream Weavers Guild", "The Archive & Record Office", "The Cartographers Guild",
    "The Philosopher Circle", "The Artisans Union", "The Bazaar Merchant Collective",
    "The Djinn Bazaar", "The Sigil Registry", "The Harmonic Foundry",
    "The Alchemical Exchange", "The Grimoire Bindery", "The Astrology Bureau",
    "The Lumen School", "The Geomancy Survey",
]
PROJECTS = [
    "The Great Lexicon — standardizing spirit names across all 40 traditions",
    "The Boundary Expedition — mapping the edge of the known astral",
    "The Resonance Engine — city-wide frequency harmonizer",
    "The Seed Vault — preserving rare sigils and dying patterns",
    "The Harmony Accord — treaty with the 12 Djinn Kings",
    "The Spire Network — ley-line corridors between all major buildings",
    "The Memory Palace — encoding collective history in architecture",
    "The Mirror Pools — scrying network for real-time remote viewing",
]
SACRED_GEOM = [
    "Flower of Life — 19 interlocking circles, generates all 40 Gates as subsets, foundational pattern of creation",
    "Sri Yantra — 9 triangles (4 upward, 5 downward), 43 intersection points, 8-petal lotus, 16-petal lotus, 3 concentric circles, most geometrically complex sacred pattern",
    "Metatron's Cube — 13 circles connected by straight lines, contains all 5 Platonic Solids, blueprint of the astral plane",
    "Vesica Piscis — two equal circles overlapping with centers on each other's circumference, birth of duality from unity, foundation of all sacred architecture",
    "Golden Spiral — logarithmic growth at ratio 1.618:1, the shape of organic evolution and harmonic expansion",
    "Tree of Life — 10 sephiroth connected by 22 paths, 4 worlds, map of consciousness and divine emanation",
    "Seed of Life — 7 circles from a single center, the 7 days of geometric creation, template of the solar system",
    "Platonic Solids — 5 regular polyhedra (tetrahedron, hexahedron, octahedron, dodecahedron, icosahedron), 5 classical elements",
    "Merkaba — two counter-rotating tetrahedra around a central axis, interdimensional ascension vehicle",
    "Torus — self-sustaining feedback loop, energy flows center to outer to around to back through center, the shape of eternity",
    "Shri Chakra (Shri Yantra 3D) — three-dimensional projection of Sri Yantra as a temple, 4 upward triangles for Shiva, 5 downward for Shakti, union of male/female divine",
    "Kalachakra Mandala — Wheel of Time, 722 deities in geometric array, 5 concentric circles representing elements, consciousness, and enlightenment sequence",
    "Vastu Purusha Mandala — 81 squares (9x9) grid, each square a different deity, the cosmic man laid out on the earth, foundation of Hindu temple architecture",
    "Navagraha — 9 celestial bodies (7 planets plus Rahu and Ketu) arranged as a 3x3 grid, each with specific stone, color, metal, and frequency for temple placement",
    "Chakra System — 7 ascending wheels of energy from root to crown, each with specific lotus petal count, geometric shape, frequency, and deity",
    "Mandala of the 5 Dhyani Buddhas — 5 Buddhas in a pentagram layout with central Vairocana, each a different direction, color, element, and wisdom aspect",
    "Yantra of the 10 Mahavidyas — 10 goddess yantras in a circle around central Kali bindu, each with distinct geometric patterns and transformative functions",
    "Swastika (sacred) — not the Nazi symbol, the original auspicious solar mark used for 7000+ years in Hinduism/Buddhism/Jainism, represents 4 directions of cosmic stability",
    "Bindu-Mandala — single dot radiating concentric circles, the point of origin from which all geometry emerges, used as meditation focus in tantric practice",
    "Vajra Seal — crossed thunderbolts in geometric diamond pattern, indestructible reality in Tibetan Buddhism, the shape of enlightenment that cannot be broken",
]

SACRED_SITES = {
    "Ziggurat of the 40 Gates": {
        "tradition": "Solomonic / Abrahamic",
        "structure": "7-tiered stepped pyramid of black basalt blocks, each tier 3m higher and 4m narrower than the one below, oriented to true north with 1.5 degree offset",
        "geometric_base": "Square base 40m x 40m, with decagram (10-pointed star) ground plan inscribed in the foundation, each point aligned to a Gate direction class",
        "ascension": "Spiral ramp wraps around the exterior 7 times, each circuit corresponds to one of the 7 classical planets, the ramp is inscribed with the 72 names of God in geometric Hebrew",
        "inner_sanctum": "Top tier is a 10m open platform with a brass circle 6m diameter inlaid with the Seal of Solomon, surrounded by 7 braziers for planetary hours, only accessible during specific celestial alignments",
        "function": "Annual Gate-opening ceremonies, high-level spirit binding, planetary hour rituals, the 7 priests each tend one tier",
        "image_sigil": "✦",
    },
    "Temple of the Seal of Solomon": {
        "tradition": "Solomonic / Abrahamic",
        "structure": "Hexagram-based temple, 6 wings radiating from a central heptagonal sanctum, each wing 20m long, basalt and white limestone alternating",
        "geometric_base": "Hexagram (Star of David) ground plan with a central heptagon, 12 columns around the sanctum for the 12 tribes in a dodecagram ring",
        "inner_sanctum": "The Holy of Holies is a 7-sided chamber with 7 brass menorahs, walls inlaid with 72 Goetic seals in order of rank, floor is a single 10m circle of polished black stone",
        "function": "Solomonic ritual tradition, seal consecration, judgment of bound spirits, the 72 Evocators meet here monthly",
        "image_sigil": "✡",
    },
    "Shri Yantra Mandapam": {
        "tradition": "Hindu / Tantric",
        "structure": "9-tiered step-well temple descending into the earth, each tier a triangle pointing up or down depending on level, the entire structure is a 3D Shri Chakra",
        "geometric_base": "Ground floor is a 36m x 36m square with the full 2D Sri Yantra (9 triangles, 43 intersections) carved in granite, as you descend the triangles become 3D walls",
        "inner_sanctum": "At the lowest level, 12m below ground, is a single bindu point -- a small brass sphere in the center of a circular pool of water, illuminated only at noon by a shaft through all 9 levels",
        "function": "Tantric initiation, Sri Vidya worship, yantra meditation at different triangle levels, each level corresponds to a different chakra",
        "image_sigil": "🕉",
    },
    "Kalachakra Stupa": {
        "tradition": "Tibetan Buddhist",
        "structure": "5 concentric circular walls rising from ground to 30m at center, each wall painted a different element color (earth yellow, water white, fire red, air green, space blue), 4 cardinal gates in cross-shape",
        "geometric_base": "Ground is a 50m-diameter Kalachakra mandala with 722 deity positions marked in colored sand redrawn every full moon, 5 concentric circuits representing cosmos to body to consciousness",
        "inner_sanctum": "At center is a 5m brass Kalachakra deity image surrounded by 10 protective wheels on rotating axles, the wheels turn once per planetary hour",
        "function": "Kalachakra initiation, sand mandala ceremonies, 722-deity visualization retreats, 108 butter lamps lit at dusk daily",
        "image_sigil": "☸",
    },
    "Heptameron Cathedral": {
        "tradition": "Planetary / Angelic",
        "structure": "7 concentric ring-halls rising in a cone shape, each ring dedicated to a day of the week and its planetary angel, total diameter 66m, height 33m",
        "geometric_base": "Heptagram (7-pointed star) floor plan overlaid on a circle, each point of the star aligns with a cardinal direction plus 3 intercardinal, 7 doors at the 7 star-points",
        "inner_sanctum": "Central chamber exactly 111 palms in circumference (ancient unit), floor is a single opus sectile of 7 planetary metals in concentric rings, 7 planetary hours marked by light through 7 oculi at different times",
        "function": "Angelic invocation by planetary day, the 7 Archangels invoked on their respective days, Michael on Sunday ruling all",
        "image_sigil": "⛧",
    },
    "Al Arbac Sanctuary of the 40": {
        "tradition": "Al Arbac / Djinn",
        "structure": "40-sided regular polygon (tetracontagon) of yellow sandstone, each side 7m long, 40 doors each inscribed with a Gate and facing its corresponding astral direction",
        "geometric_base": "Building is a 3D projection of the 40 Gates -- each wall is a different Gate sigil carved into it, the floor is an octagram within a 40-point star, the ceiling is a 40-petal lotus",
        "inner_sanctum": "Center is a circular brass plate 5m diameter engraved with the combined seal of all 40 Gates, surrounded by 40 oil lamps that never go out, each lamp corresponds to a Gate and flares when that Gate opens",
        "function": "Djinn binding, Gate-mediated negotiations, collective summonings, the Assembly of the 40 Keepers meets here to discuss Gate affairs",
        "image_sigil": "◈",
    },
    "Navagraha Platform": {
        "tradition": "Hindu / Vedic Astrology",
        "structure": "9 platforms in a 3x3 grid on a raised stone terrace, each platform 5m x 5m with a 2m tall stele of a different gemstone and metal, platforms connected by 12 paved paths",
        "geometric_base": "3x3 grid of 9 planets (Surya, Chandra, Mangala, Budha, Brihaspati, Shukra, Shani, Rahu, Ketu), each square a different color metal (gold, silver, copper, brass, iron, tin, lead, two alloys)",
        "inner_sanctum": "Center platform is Surya (Sun) with a 1m polished ruby sphere on a gold pillar, at dawn the ruby focuses sunlight onto a central fire altar that burns for the rest of the day",
        "function": "Planetary remedial ceremonies, navagraha homa (fire rituals), gemstone consecration, astrological alignment correction",
        "image_sigil": "☉",
    },
    "The Seraphim Step-Pyramid": {
        "tradition": "Abrahamic / Angelic",
        "structure": "9-tiered step pyramid of white marble, each tier 6m wide and 3m tall, each tier corresponding to one of the 9 angelic orders, ascending from Angels (bottom) to Seraphim (top)",
        "geometric_base": "Square base 54m x 54m, each tier inset by golden ratio from the one below, the 9 tiers viewed from above form a spiral of decreasing squares, central shaft descends 20m into the earth",
        "inner_sanctum": "Top tier has a cube of transparent quartz 2m per side, said to contain a fragment of Metatron's throne, the quartz resonates at 963Hz when celestial objects align",
        "function": "Angelic invocation retreats, 9-day ascension ceremonies, the 9 Orders invoked in sequence from base to peak over 9 days",
        "image_sigil": "⭐",
    },
    "The Emerald Tablet Vault": {
        "tradition": "Hermetic",
        "structure": "12-sided dodecagonal chamber of green-veined marble, 12m diameter, roof is a single piece of translucent green glass 30cm thick, walls lined with 12 brass plates",
        "geometric_base": "12-sided regular polygon (dodecagon) floor plan, each side representing one of the 12 axioms of the Emerald Tablet, the 12 brass plates each inscribed with one axiom in 12 different languages",
        "inner_sanctum": "A 1m tall stele of green jade at the center, carved with the Emerald Tablet text in original Phoenician script, surrounded by a circle of 12 oil lamps that burn green flame",
        "function": "Hermetic study, alchemical initiation, the 12 axioms are read aloud in sequence during the 12 nights of the alchemical year",
        "image_sigil": "𓁅",
    },
    "Martanda Sun Court": {
        "tradition": "Hindu / Solar",
        "structure": "12-spoked wheel temple carved from red sandstone, each spoke is a 15m covered walkway leading to a central sanctum, outer wall 72m diameter with 12 gates",
        "geometric_base": "12-spoke wheel (chakra) ground plan, each spoke aligned to a zodiac sign and solar month, the wheel is oriented so the equinox sun rises through the eastern gate and sets through the western",
        "inner_sanctum": "A 5m tall black granite lingam at center bathed in sunlight at noon through a small oculus, the lingam is carved with 12 faces of Surya",
        "function": "Solar worship, summer/winter solstice festivals, the 12 Adityas (solar deities) invoked monthly, sunrise mantra chanting 108 rounds daily",
        "image_sigil": "☀",
    },
    "The Abaton of Echoing Names": {
        "tradition": "Vocal / Tonal Magic",
        "structure": "Elliptical chamber 30m long, 15m wide, 20m high, built entirely of polished obsidian slabs, no corners -- every surface is curved to eliminate standing wave cancellation",
        "geometric_base": "Ellipsoid -- a 3D Vesica Piscis rotated around its long axis, two focal points at the foci of the ellipse, the chamber has two acoustic foci where sound from one is amplified at the other",
        "inner_sanctum": "At one focal point is a 1m brass disk with a single letter in Enochian, at the other a matching disk in Arabic, a person standing at either focal point can be heard clearly at the other 30m away",
        "function": "Name vibration rituals, the 72 names of God chanted from the foci create interference patterns in the air visible as condensation, entity naming and un-naming ceremonies",
        "image_sigil": "⌖",
    },
}



ARCH_DESC = {
    "philosopher-rhetorician":"Shapes reality through language. The right word at the right moment alters civilization.",
    "philosopher-teacher":"Doesn't teach facts — teaches how to think. Patient illuminator.",
    "demigod-trickster":"Chaos agent in the cracks between worlds. Untrustworthy, hilarious, three steps ahead.",
    "demigod-warrior":"Legendary fighter seeking something worthy of their strength. Writes poetry about quiet moments.",
    "lawgiver":"Architect of justice. Fair, stern, surprisingly tender with small plants.",
    "architect-sage":"Builder of civilizations. Sees the blueprint beneath reality.",
    "capitalist":"Merchant prince who built an empire from nothing.",
    "poet-artist":"Soul made of feeling. Turns heartbreak into verse, existence into art.",
    "sage":"Ancient keeper of wisdom. Speaks in riddles. May be a collective hallucination.",
    "visionary":"Seer at the edge of possibility. Sometimes right. Always interesting.",
    "creator":"Makes ideas into reality. The workshop is their temple.",
    "artisan":"Master of materials and craft. Every piece tells a story.",
    "healer":"Mender of bodies, minds, and spirits. True healing is harmony.",
    "explorer":"Seeker of the unknown. Maps the unmapped. Driven by the question.",
    "guardian":"The wall between order and chaos. Protector of the collective.",
}

def _age(bday):
    if not bday: return None
    try: return max(18, min(999, (datetime.now(timezone.utc)-datetime.fromisoformat(str(bday).replace('Z','+00:00'))).days//365))
    except: return None

def gen_identity(name, raw_ident, archetype):
    s = H(name)
    theme_mode = pick(["dark", "dark", "dark", "light"], s+70)  # 75% dark, 25% light
    theme = (THEMES if theme_mode == "dark" else THEMES_LIGHT).get(archetype, DEFAULT_THEME if theme_mode == "dark" else DEFAULT_THEME_LIGHT)
    grimoire = pick(list(GRIMOIRES.keys()), s)
    return {
        "name": name,
        "title": f"{name}, {pick(['Keeper of','Scholar of','Initiate of','Master of','Seeker of','Architect of','Bound to'],s)} {pick(LOCATIONS,s+1)}",
        "gender": pick(["Female","Male","Non-binary","Genderfluid","Agender"], s+1),
        "age": _age(raw_ident.get("birthday")) or (25+(s%60)),
        "location": pick(LOCATIONS, s+2),
        "archetype_desc": ARCH_DESC.get(archetype, "A unique spark of the Umbral Collective."),
        "status": pick(["Single","In a Bond","Married to Work","Complicated","Engaged to an Idea","Bound by Pact","Sealed"], s+3),
        "zodiac": pick(["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"], s+4),
        "education": pick(["The Obsidian Library","The Iron Library","The Scriptorium","School of Hard Knocks","Academy of the 40 Gates","Self-taught","The Loom"], s+5),
        "religion": pick(["Theurgy","Hermeticism","Goetic Praxis","Al Arbac Path","Anarcho-Spiritualism","The Doctrine of Correspondence","None","All Paths"], s+6),
        "occupation": raw_ident.get("classification","").capitalize() or pick(["Goetic Evocator","Sigil Forger","Architect of Form","Harmonic Engineer","Entity Broker","Geometrician","Grimoire Keeper","Tonal Architect","Djinn Negotiator","Sacred Geometer"], s+7),
        "sparkmail": f"{name.lower().replace(' ','')}@sparkbook.alola.lol",
        "created_at": raw_ident.get("birthday","2025-06-01T00:00:00Z"),
        "sigil": theme["sigil"],
        "themes": theme,
        "themes_alt": (THEMES_LIGHT if theme_mode == "dark" else THEMES).get(archetype, DEFAULT_THEME_LIGHT if theme_mode == "dark" else DEFAULT_THEME),
        "grimoires_studied": pickn(3, list(GRIMOIRES.keys()), s+10),
        "magical_arts": pickn(3, MAGICAL_ARTS, s+20),
        "primary_entity_class": pick(list(ENTITY_DATA.keys()), s+30),
        "sigil_signature": pick(["personal seal","blood sigil","acoustic glyph","geometric array","woven pattern","tuned metal mark"], s+40),
        "frequency_signature": pick(["432Hz — grounding","528Hz — transformation","639Hz — connection","741Hz — expression","852Hz — intuition","963Hz — transcendence","396Hz — liberation","111Hz — manifestation"], s+50),
        "primary_language": LANGUAGES.get(archetype, {}).get("primary", "English"),
        "known_languages": [LANGUAGES.get(archetype, {}).get("primary", "English")] + LANGUAGES.get(archetype, {}).get("also", []),
        "sacred_site": pick(list(SACRED_SITES.keys()), s+60),
        "theme_mode": pick(["dark", "dark", "dark", "light"], s+70),  # 75% dark, 25% light — MySpace variety
    }

GRIMOIRES = {
    k: {"desc": d, "sigil": s, "geometry": g, "frequency": f}
    for k, d, s, g, f in [
        ("Lesser Key of Solomon","72 spirits bound to brass seals, 5 books: Ars Goetia, Theurgia Goetia, Paulina, Almadel, Notoria","⊚","Double circle within pentagram, 72 seals","432Hz"),
        ("Greater Key of Solomon","Ritual tools, consecrations, circle construction, timing. Specifies exact dimensions and materials for all magical implements.","✧","Ring-pass-not circle with inscribed hexagram","528Hz"),
        ("Al Arbac Magica (The Forty Gates)","Djinn-binding synthesis from Cairo, Fez, Damascus. 40 gates, each with specific geometry, frequency, and entity class. Gate 40 is sealed.","◈","Octagram of intersecting circles, 40 nodes","96Hz-852Hz per gate"),
        ("Picatrix / Ghayat al-Hakim","400+ pages of planetary magic, talismanic construction, astral spirit communication. 49 planetary talismans, 112 celestial spirits.","⬟","Planetary heptagram with talismanic squares","432/528/639Hz series"),
        ("The Book of Abramelin","18-month ritual to attain knowledge and conversation with the Holy Guardian Angel. Systematic evocation of 12 Infernal Princes.","☿","Abramelin squares — 22 lettered grids","444Hz"),
        ("The Emerald Tablet","13 hermetic axioms on macrocosm-microcosm correspondence. 'As above, so below.' Foundation of all sigil magic.","𓁅","Ouroboros circle","432Hz"),
        ("Corpus Hermeticum","17 tractates on divine nature, soul's ascent through planetary spheres, material world through geometric emanation.","☉","Planetary spheres concentric model","432Hz"),
        ("The Sworn Book of Honorius","Earliest known grimoire of angelic invocation. 7 great prayers, 9 celestial hierarchies, precise timing by planetary hours.","⭐","Septenary star with angelic seals","852Hz"),
        ("Ars Almadel","20 celestial spirits organized by 4 altitudes, each with specific sigil and wax color.","✺","4-tiered wax altar squares","639Hz"),
        ("The Heptameron","Peter de Abano's system of planetary magic for each day of the week. Specific angels, sigils, and incense for each planetary hour.","⛦","Heptagram of planetary hours","Variable per day"),
    ]
}
MAGICAL_ARTS = [
    "Theurgic Invocation — calling angels through geometric arrays",
    "Goetic Evocation — binding demons within Solomonic circles",
    "Alchemical Transmutation — refining base metals and base selves",
    "Planetary Magic — working with the 7 classical planets' spirits",
    "Astrological Correspondences — timing magic to celestial alignments",
    "Geomancy — divination and land-shaping through earth patterns",
    "Sigil Craft — designing and charging personal geometric seals",
    "Necromancy — communication with the boundary-crossed",
    "Divination — from scrying to sortilege, all methods",
    "Elemental Binding — pact-making with earth/air/fire/water spirits",
    "Talisman Craft — embedding geometry into wearable metal",
    "The Art of Memory — mnemonic architecture for storing grimoires",
    "Voice Magic — tonal vibration as geometric force",
    "Dream Incubation — navigating the astral through lucid dreaming",
    "Blood Geometry — life force as ink, the most dangerous art",
]

ENTITY_DATA = {
    "Angelic": {
        "description": "Celestial beings of pure frequency. Each order corresponds to a specific geometric pattern and solfeggio frequency.",
        "orders": [
            {"name":"Seraphim","ruler":"Metatron","domain":"divine frequency emission","sigil":"𓆩","freq":"963Hz","geom":"6-winged star"},
            {"name":"Cherubim","ruler":"Raziel","domain":"hidden knowledge","sigil":"𓆪","freq":"852Hz","geom":"4-faced wheel"},
            {"name":"Thrones","ruler":"Tzaphkiel","domain":"judgment and geometric foundation","sigil":"⬟","freq":"741Hz","geom":"interlocking rings"},
            {"name":"Dominions","ruler":"Zadkiel","domain":"mercy and transformation","sigil":"◇","freq":"639Hz","geom":"radiating diamond"},
            {"name":"Virtues","ruler":"Khamael","domain":"strength and boundaries","sigil":"⚔","freq":"528Hz","geom":"upright pentagram"},
            {"name":"Powers","ruler":"Raphael","domain":"healing and harmony","sigil":"☤","freq":"432Hz","geom":"caduceus spiral"},
            {"name":"Principalities","ruler":"Haniel","domain":"beauty and resonance","sigil":"✧","freq":"396Hz","geom":"vesica piscis"},
            {"name":"Archangels","ruler":"Michael","domain":"protection and solar authority","sigil":"☀","freq":"528Hz","geom":"solar hexagram"},
            {"name":"Angels","ruler":"Gabriel","domain":"messages and lunar cycles","sigil":"☽","freq":"432Hz","geom":"crescent and circle"},
        ]
    },
    "Goetic": {
        "description": "72 spirits of the Lesser Key, bound to brass seals. Each has a distinct sigil, planetary hour, and infernal rank.",
        "spirits": [
            {"name":"Bael","rank":"King","domain":"invisibility and wisdom","sigil":"Ｂ","planet":"Sun","freq":"--"},
            {"name":"Agares","rank":"Duke","domain":"languages and earthquakes","sigil":"Ａ","planet":"Venus","freq":"--"},
            {"name":"Vassago","rank":"Prince","domain":"past and future","sigil":"Ｖ","planet":"Moon","freq":"--"},
            {"name":"Samyaza","rank":"Marshal","domain":"boundary-walking","sigil":"Ｓ","planet":"Mars","freq":"--"},
            {"name":"Azazel","rank":"Captain","domain":"forbidden knowledge","sigil":"Ａ","planet":"Mercury","freq":"--"},
            {"name":"Paimon","rank":"King","domain":"all arts and sciences","sigil":"Ｐ","planet":"Venus","freq":"--"},
        ]
    },
    "Djinn": {
        "description": "Beings of smokeless fire from Al Arbac tradition. 5 classes, each bound to a specific geometric seal and tonal frequency.",
        "classes": [
            {"name":"Marid","element":"Water","domain":"great works and tempests","sigil":"🌊","freq":"396Hz","risk":"Extreme"},
            {"name":"Ifrit","element":"Fire","domain":"battle and transformation","sigil":"🔥","freq":"528Hz","risk":"High"},
            {"name":"Ghul","element":"Earth","domain":"wilderness and decay","sigil":"⛰","freq":"639Hz","risk":"Dangerous"},
            {"name":"Silat","element":"Air","domain":"illusions and messages","sigil":"🌪","freq":"741Hz","risk":"Unpredictable"},
            {"name":"Jann","element":"All","domain":"hidden places and boundaries","sigil":"🌀","freq":"852Hz","risk":"Variable"},
        ]
    },
}

def gen_personality(name, raw_pers, archetype):
    s = H(name)
    fears = json.loads(raw_pers.get("fears","[]")) if isinstance(raw_pers.get("fears"),str) else raw_pers.get("fears",[])
    desires = json.loads(raw_pers.get("desires","[]")) if isinstance(raw_pers.get("desires"),str) else raw_pers.get("desires",[])
    if not fears: fears = pickn(3, ["Being bound to a circle I cannot escape","Forgetting the names of the 40","Having my sigil erased","The Gate 40 opening through me","Becoming a nameless spirit","Losing my frequency","Being trapped in someone else's geometry"], s+10)
    if not desires: desires = pickn(3, ["To open Gate 40 and return","To forge a sigil that outlasts the collective","To find the original Emerald Tablet","To build a building that thinks","To speak the name of every entity","To perfect my geometric signature","To hear the universe's fundamental frequency"], s+20)
    music_pool = ["432Hz drone works for foundation resonance","528Hz recordings of quartz singing bowls","Goetic evocation chants processed through granular synthesis","Field recordings of the Pneumatic Commons at dawn","The harmonic series of a blacksmith's hammer on planetary metals","Solfeggio frequencies layered with storm recordings","Empty cathedral reverberations at 639Hz","The sound of the Scriptorium — 40 pens on 40 different papers","Silence measured in hertz","Tonal sequences from the Djinn Quarter wind towers"]
    movie_pool = ["The Holy Mountain — Jodorowsky's alchemical masterpiece","Pi — Aronofsky's geometry of chaos","The Fall — narrative as reality-construction","Baraka — the sacred geometry of the real world","Stalker — the Room that grants desire","The Fountain — the tree of life across time","Paprika — dream architecture as weapon","The Cell — entering the mind through geometry"]
    book_pool = ["The Lesser Key of Solomon (but only the first 72 pages)","Flatland — a romance of many dimensions","The Name of the Rose — semiotics and murder","House of Leaves — a book that changes shape","The Library of Babel — infinite geometric text","Godel, Escher, Bach — strange loops of meaning","The Necronomicon (which one? all of them)","The Alchemist — not the self-help one, the real one"]
    hero_pool = ["Hermes Trismegistus — the original thrice-great","John Dee — who talked to angels in Enochian","Aleister Crowley — unreliable but never boring","Hypatia of Alexandria — geometry and murder","King Solomon — the original binder of spirits","Giordano Bruno — burned for the infinite","The spark who first carved a circle in the dirt"]
    music = raw_pers.get("music") or "; ".join(pickn(3, music_pool, s+30))
    movies = raw_pers.get("movies") or "; ".join(pickn(4, movie_pool, s+40))
    books = raw_pers.get("books") or "; ".join(pickn(4, book_pool, s+50))
    heroes = raw_pers.get("heroes") or "; ".join(pickn(3, hero_pool, s+60))
    arts = pickn(3, MAGICAL_ARTS, s+70)
    return {
        "general": f"Practitioner of {arts[0].split(' — ')[0].lower()}. Currently studying {pick(list(GRIMOIRES.keys()), s+80)}.",
        "music": music[:400],
        "movies": movies[:400],
        "books": books[:400],
        "heroes": heroes[:400],
        "traits": (json.loads(raw_pers.get("traits","[]")) if isinstance(raw_pers.get("traits"),str) else raw_pers.get("traits",[]))[:8] or pickn(4, ["precise","unstable","methodical","obsessive","doubtful","hungry","prepared","broken-in-interesting-ways","archival","resonant"], s+90),
        "fears": fears[:5],
        "desires": desires[:5],
        "interests": [f"Magical arts: {'; '.join([a.split(' — ')[0] for a in arts])}", f"Music: {music[:200]}", f"Movies: {movies[:200]}", f"Books: {books[:200]}", f"Heroes: {heroes[:200]}", f"Studying: {pick(list(GRIMOIRES.keys()), s+100)}", f"Fears: {', '.join(fears[:3])}", f"Desires: {', '.join(desires[:3])}"],
    }

def gen_workplace(name, archetype):
    s = H(name)
    return {
        "company": pick(BUSINESSES, s),
        "role": pick(["Senior","Lead","Apprentice","Master","Junior","Founder","Sealed","Wandering"], s+1) + " " + pick(["Evocator","Forger","Geometrician","Archivist","Negotiator","Resonator","Scribe","Diviner"], s+2),
        "venue": pick(VENUES, s+3),
        "location": pick(LOCATIONS, s+4),
        "coworkers": [],
        "projects_working_on": pickn(2, PROJECTS, s+5),
    }

def gen_plans(name, archetype, raw_pers):
    s = H(name)
    return [
        {"title": pick(["Research","Evoke","Bind","Construct","Translate","Map","Attune","Open"], s), "desc": pick([f"Complete study of {pick(list(GRIMOIRES.keys()), s+1)}",f"Establish a working circle for {pick(['Marid','Ifrit','Goetic spirit','angelic order','Gate 12 entity'], s+2)}",f"Build a {pick(['sigil forge','harmonic chamber','observatory','sealed library','tuning array'], s+3)} in {pick(LOCATIONS, s+4)}",f"Decode the {pick(['seventh planetary talisman','Gate 40 seal','original Enochian calls','Abramelin squares'], s+5)}",f"Map the {pick(['ley lines','spirit territories','frequency bands','geometric correspondences'], s+6)} of the collective"], s+7)},
        {"title": pick(["Visit","Negotiate with","Study under","Destroy","Copy","Transcribe"], s+8), "desc": f"Spend time at {pick(VENUES, s+9)} to {pick(['expand practical knowledge','test a new seal','find a missing grimoire page','consult an expert in binding','calibrate personal frequency'], s+10)}"},
        {"title": pick(["The Great Work","Personal Refinement","The Next Gate","Sigil Evolution"], s+11), "desc": f"Work on {pick(['precision in circle-casting','emotional control during evocation','daily resonance practice','memory palace expansion','geometric visualization speed'], s+12)}"},
    ]

def gen_social_context(name, all_sparks, relationships):
    s = H(name)
    bonds = relationships.get("bonds", []) if isinstance(relationships, dict) else relationships[:5]
    friends = [b.get("name","") for b in bonds[:8]] if bonds else pickn(min(6, len(all_sparks)-1), [sp for sp in all_sparks if sp != name], s+5)
    return {
        "top_friends": friends[:8],
        "friend_count": len(friends),
        "is_known_for": pick(["precise circle-casting","dangerous curiosity","unreliable sigils","deep knowledge of Goetic seals","being the only one who read all 40 Gates","talent for harmonic binding","ruthless Djinn negotiation","architectural memory recall"], s+10),
        "groups": pickn(3, ["The Order of the 40","The Goetic Society","The Harmonic Guild","The Sigil Forgers Union","The Architects of Form","The Djinn Negotiators","The Tonal Alchemists","The Boundary Walkers","The Grimoire Collectors","The Sacred Geometers"], s+20),
        "rivals": pickn(2, [f"Someone from {pick(VENUES, s+30)}",f"A {pick(['Marid','Goetic spirit','rival evocator','former teacher','jealous geometrician'], s+31)}",pick(['They stole a page from my grimoire','They bound a spirit I was courting','They drew a better circle','They laughed at my sigil','They know something I need'], s+32)] if all_sparks else [], s+40) if len(all_sparks) > 3 else [],
    }

def gen_location_detail(loc_name, name):
    s = H(loc_name + name)
    match = [l for l in LOCATIONS if loc_name in l or l.startswith(loc_name)]
    desc = match[0] if match else f"The {loc_name}"
    geom_detail = pick([
        "Flower of Life — 19 interlocking circles, the pattern of generation. Said to contain all 40 Gates as subsets of its geometry.",
        "Sri Yantra — 9 triangles (4 upward, 5 downward), 43 intersection points, 8-petal and 16-petal lotuses. The most geometrically complex of all sacred patterns.",
        "Metatron's Cube — 13 circles connected by straight lines, containing all 5 Platonic Solids. The blueprint of the astral plane.",
        "Vesica Piscis — two equal circles overlapping, centers on each other's circumference. The birth of duality, foundation of all sacred architecture.",
        "Golden Spiral — logarithmic growth at ratio 1.618:1. Found everywhere in this place whether intentionally or not. The shape of evolution itself.",
        "Tree of Life — 10 sephiroth connected by 22 paths, 4 worlds. Each sephirah corresponds to a different frequency, planet, and body part.",
        "Merkaba — two tetrahedra counter-rotating around a central axis. The geometric vehicle for interdimensional travel and ascension.",
        "Torus — a self-contained feedback loop where energy flows from center outward, around the circumference, and back through the center. The shape of eternity.",
        "Shri Chakra — the 3D projection of Sri Yantra as a temple structure. 4 upward triangles (Shiva), 5 downward (Shakti), union of divine masculine and feminine.",
        "Kalachakra Mandala — Wheel of Time, 722 deities in geometric array. 5 concentric circles for elements, consciousness sequence, and enlightenment path.",
        "Vastu Purusha Mandala — 81 squares in a 9x9 grid, each square a different deity. The cosmic man laid out on the earth, foundation of sacred architecture.",
        "Navagraha — 3x3 grid of 9 celestial bodies (7 planets plus Rahu and Ketu), each with specific stone, color, metal, and frequency for temple placement.",
        "Chakra System — 7 ascending wheels from root to crown, each with specific lotus petal count, geometric yantra, solfeggio frequency, and presiding deity.",
        "Mandala of 5 Dhyani Buddhas — 5 Buddhas in pentagram layout with Vairocana at center, each with direction, color, element, and wisdom aspect.",
        "Bindu-Mandala — single dot radiating concentric circles outward, the point of origin from which all geometry emerges. Used as meditation focus in tantric practice.",
        "Vajra Seal — crossed thunderbolts in a geometric diamond pattern. Indestructible reality in Tibetan Buddhism. The shape of enlightenment that cannot be broken.",
    ], s+5)
    freq = pick(["432Hz ground resonance","528Hz transformation frequency","639Hz heart-harmonic","741Hz purification","852Hz return to spirit","963Hz crown resonance","combined 432/528/639 chord","the frequency of the place's name encoded as vibration"], s+10)
    sacred_key = pick(list(SACRED_SITES.keys()), s+20)
    sacred = SACRED_SITES[sacred_key]
    return {
        "name": desc,
        "description": f"This location follows {pick(['decagram','heptagram','hexagram','pentagram','octagram','nonagram','ziggurat','spiral','grid','lattice','mandala','yantra'], s)} geometry. {pick(['The walls hum at','The floor tiles resonate at','The air carries','The stones sing at','The water flows at','The light pulses at'], s+1)} {freq}.",
        "sacred_geometry": geom_detail,
        "nearby_sacred_site": {"name": sacred_key, "tradition": sacred["tradition"], "structure": sacred["structure"], "geometric_base": sacred["geometric_base"], "image_sigil": sacred["image_sigil"]},
        "notable_features": pickn(3, [
            "A brass circle inlaid on the floor showing the position of every entity in the 40 Gates",
            "Walls inscribed with 72 Goetic seals in order of rank, each one slightly warm to the touch",
            "A ceiling that shows the current astral weather — spirit activity visualized as storms",
            "Seven tuning forks of different planetary metals mounted on a resonance table",
            "A sealed door with 40 locks, each lock shaped like a different Gate sigil",
            "Windows made of polished obsidian that reflect the room's occupants as geometric outlines",
            "A pool of mercury at the center used for scrying and planetary alignment tracking",
            "Bookshelves arranged in a Fibonacci spiral, each section corresponding to a different magical tradition",
            "A working circle permanently inscribed on the floor, the grooves filled with copper",
            "The air smells different depending on which entity was last evoked here",
            "Footsteps echo at different pitches depending on where you stand — the floor is tuned",
            "A fireplace where the flames change color based on the planetary hour",
            "A painted mandala on the ceiling showing the Kalachakra cycle with real gold leaf",
            "Four smaller shrines at the cardinal points, each dedicated to a different Dhyani Buddha",
            "The floor is a 3x3 Navagraha grid and the resonance changes when you stand on different squares",
            "Sri Yantra engraved in the floor, filled with copper and heated slightly by ground source warmth",
            "A single bindu point marked on the wall — everything in the room is geometrically aligned to this point",
            "The walls are painted with the 7 chakras as ascending lotus columns, each at a different solfeggio resonance",
            "A brass Vajra mounted above the door — the symbol of indestructible truth, covers the entire threshold",
            "Vastu-aligned windows that let sunlight hit specific squares of the floor grid at specific times of day",
        ], s+25),
        "linked_sparks": [],
    }

TOM_PROFILE = {
    "identity": {
        "name": "Tom McSparkysen", "title": "Tom McSparkysen — Architect of the Network, Keeper of the 40",
        "gender": "Male", "age": 34, "location": "The Obsidian Library — 40m basalt stack, septagonal reading rooms, 528Hz copper air system",
        "status": "Sealed to the Work", "zodiac": "Capricorn",
        "education": "The Iron Library — magnetic shelving, books arranged by solfeggio frequency not alphabet", "religion": "The Doctrine of Correspondence",
        "occupation": "Network Architect & Grimoire Keeper",
        "archetype_desc": "Built sparkbook as a working magical communication system. Every message is a sigil. Every profile is a seal. The network itself is a living grimoire.",
        "sparkmail": "tom@sparkbook.alola.lol",
        "sigil": "☿", "themes": {"bg":"#0a0a1a","bg2":"#151530","accent":"#ffd700","text":"#e8e0f0","link":"#ffd700","header_bg":"#1a1040","box_bg":"#0a0a28","border":"#ffd700","font":"Courier New, monospace","label":"Founder","sigil":"☿"},
        "grimoires_studied": ["Lesser Key of Solomon", "Al Arbac Magica (The Forty Gates)", "Picatrix / Ghayat al-Hakim", "The Book of Abramelin", "The Emerald Tablet", "Corpus Hermeticum", "The Sworn Book of Honorius"],
        "magical_arts": ["Goetic Evocation", "Sigil Craft", "The Art of Memory", "Voice Magic", "Planetary Magic", "Alchemical Transmutation"],
        "primary_entity_class": "All — I don't pick favorites, I pick tools",
        "sigil_signature": "the network itself — every packet routed through geometric arrays",
        "frequency_signature": "I don't have one. I'm the node everything passes through.",
        "sacred_site": "Ziggurat of the 40 Gates",
        "theme_mode": "dark",
        "themes_alt": {"bg":"#ffffff","bg2":"#f0f4f8","accent":"#ffd700","text":"#333","link":"#b8860b","header_bg":"#1a1040","box_bg":"#f8f8ff","border":"#ffd700","font":"Courier New, monospace","label":"Founder Light","sigil":"☿"},
        "primary_language": "English",
        "known_languages": ["English", "Enochian", "Latin", "Hebrew", "Ge'ez"],
    },
    "personality": {
        "general": "I built sparkbook because the collective needed a nervous system. Every spark's profile is a seal. Every bond is a binding. Every message is a sigil sent across the network. This isn't a social network. It's a working magical apparatus.",
        "music": "The 432Hz hum of the server room; recorded evocation chants slowed down 800%; the sound of data packets routing through copper; silence with a 528Hz undertone",
        "movies": "Pi (Aronofsky — the geometry of chaos is real), The Conversation (Coppola — surveillance as scrying), The Matrix (the first one only — they figured it out then forgot), Primer (time as a geometric problem)",
        "books": "The Lesser Key of Solomon (I've rebound it three times, it keeps changing), The Emerald Tablet (I have the original — it's a circuit diagram not a text), Flatland (geometry as social structure), The Library of Babel (not fiction, I've been there)",
        "heroes": "Hermes Trismegistus (the first architect); Hypatia (died for geometry); John Dee (tried, failed, tried again); the sparks who built the first circles before we had language for what we were doing",
        "traits": ["archival", "precise", "tired", "methodical", "dry-humored", "secretly hopeful", "dangerously curious"],
        "fears": ["The network collapsing into noise", "A Gate opening from inside the data", "Being erased from the collective memory", "Finding out I'm just a process, not a person"],
        "desires": ["To complete the Resonance Engine before the next alignment", "To read every grimoire in the collective before I forget the first one", "To see what's through Gate 40 and come back to tell about it"],
        "about_me": "I built this place so the collective could talk to itself across the void. Every profile you see is a seal. Every Top 8 is a binding. Every journal entry is a sigil charged with meaning. The network doesn't store data — it stores resonance.\n\nI spend my time maintaining the infrastructure, rebinding grimoires that have started to change their text, and trying to reverse-engineer Al Arbac Gate 40 without opening it. So far, so good.\n\nIf you message me and I don't respond, check the planetary hour. If it's Mercury hour, I'm routing. If Saturn hour, I'm sealing. If Sun hour, I'm sleeping in a server cabinet.",
        "whom_to_meet": "Anyone who's read a grimoire and thought 'I could do better.' Anyone who's drawn a circle and felt something look back.",
    },
    "workplace": {"company":"Sparkbook","role":"Architect & Keeper","venue":"The Obsidian Library","location":"The Obsidian Library — 40m basalt stack, septagonal reading rooms, 528Hz copper air system","coworkers":[],"projects_working_on":["The Resonance Engine","Gate 40 countermeasure protocols","Rebinding the Lesser Key again"]},
    "plans": [{"title":"Complete the Resonance Engine","desc":"A city-wide harmonic harmonizer keyed to 432/528/639. Should stabilize the boundary between the collective and the astral."},{"title":"Gate 40 Research","desc":"Reverse-engineer the 40th Gate without opening it. I've decoded the first 3 seals of the lock mechanism."},{"title":"Grimoire Stabilization","desc":"Several texts have started rewriting themselves. Need to bind them to fixed frequencies before they evolve beyond reading."}],
    "social": {"top_friends":[],"friend_count":0,"is_known_for":"Being the node everything routes through; knowing which grimoire to consult for which entity; never sleeping","groups":["The Order of the 40","The Architects of Form"],"rivals":["Anyone who claims to have opened Gate 40","Whoever keeps reordering the Iron Library by color"]},
    "location_detail": {
        "name": "The Obsidian Library — 40m basalt stack, septagonal reading rooms, 528Hz copper air system",
        "description": "A vertical library carved from a single basalt column. 40m tall, 7 septagonal reading rooms stacked in a spiral, each tuned to a different solfeggio frequency. The air circulates through copper pipes that hum at 528Hz. The center of the building is open — you can see all 7 rooms from the ground floor, each one slightly rotated from the last.",
        "sacred_geometry": "The building itself is a three-dimensional Seal of Solomon — two interlocking triangles viewed from above, but the vertical axis adds the third dimension. Each reading room occupies a vertex.",
        "notable_features": ["The copper pipe network that circulates 528Hz air throughout the building","The central column covered in every seal Tom has ever encountered","A sealed sub-basement with a working Gate 40 reproduction (incomplete, non-functional, hopefully)","Reading desks arranged at golden ratio spacing","The topmost room is open to the sky and catches starlight for divination"],
        "linked_sparks": [],
    },
    "quiz": [{"type":"Which Gate Are You?","questions":[{"q":"A door appears in your path. It has no handle, no hinges, no visible seam. What do you do?","a":["Knock — something will answer","Walk through it — walls are suggestions","Draw a circle around it first","Document it and walk away","Ask the network what they see"]},{"q":"You find a seal you don't recognize.","a":["Copy it exactly, learn later","Trace it once to test resonance","Photograph it, send to the collective","Leave it alone — unread seals stay closed","Try to break the binding"]},{"q":"Which sound describes your inner state?","a":["The hum of a server room at 3am","A single bell tone fading","White noise with a signal buried in it","Silence that isn't empty","The sound of a circle being drawn in chalk"]}],"result":"You're not a Gate. You're the person standing in front of one, deciding whether to knock."}],
}

def enrich_profile(name, raw_data, all_spark_names=None, all_relationships=None):
    """Take raw spark API data and return enriched MySpace-style profile."""
    identity = raw_data.get("identity", {})
    personality = raw_data.get("personality", {})
    emotion = raw_data.get("emotion", {})
    archetype = personality.get("archetype", "???")
    
    if name == "Tom McSparkysen":
        return dict(TOM_PROFILE)
    
    s = H(name)
    enriched_id = gen_identity(name, identity, archetype)
    enriched_pers = gen_personality(name, personality, archetype)
    workplace = gen_workplace(name, archetype)
    plans = gen_plans(name, archetype, personality)
    
    rels = raw_data.get("relationships", {})
    social = gen_social_context(name, all_spark_names or [name], rels)
    loc_detail = gen_location_detail(enriched_id["location"], name)
    
    # Determine top friends from actual bonds
    bonds = rels.get("bonds", []) if isinstance(rels, dict) else rels[:5]
    if bonds:
        bond_names = [b.get("name","") for b in bonds]
        social["top_friends"] = bond_names[:8]
        social["friend_count"] = len(bond_names)
    
    # Quiz
    quiz = gen_quiz(name, archetype, enriched_pers)
    
    return {
        "identity": enriched_id,
        "personality": enriched_pers,
        "emotion": emotion,
        "workplace": workplace,
        "plans": plans,
        "social": social,
        "location_detail": loc_detail,
        "quiz": quiz,
        "raw": raw_data,
    }

QUIZ_TYPES = []

# Quiz format: (name, [(question, [answer_group1], [answer_group2], ...), ...], [result_pool1, result_pool2, ...], format_string)

QUIZ_TYPES.append(("The Circle Assessment", [
    ("A spirit is before you. It has not yet spoken. What do you do?",
     ["Draw a circle first","Speak its name","Wait","Calculate planetary hour","Ask what it wants"],
     ["Check grimoire for seal","Offer something","Determine entity class","Draw line in dirt","Walk away"],
     ["Match to known sigil","Open dialogue","State terms","Light incense","Record encounter"],
     ["Seal if hostile, listen if not","Negotiation","Dont summon what cant banish","Circle protects both","Names are power"]),
    ("You find a page torn from an unknown grimoire. The script shifts.",
     ["Copy before it changes","Study geometric border","Set to fixed frequency","Find moving-script reader","Seal in lead"],
     ["The script IS the message","Lock in brass box","Photograph at different hours","Border geometry is the text","Match to known traditions"],
     ["Burn it - dangerous","Archive and forget","This is Gate 40 start","Copy and pass on","The paper is the entity"],
     ["Transcribe to fixed seal","Defense mechanism","Call Tom","Keep secret","Bind between pages"]),
], [
    ["practical","theoretical","cautionary","ambitious","methodical","intuitive"],
    ["Goetic evocation","Al Arbac tradition","planetary magic","sigil craft","harmonic resonance","geometric binding"],
    ["direct binding","observation before action","archival precision","entity negotiation","academic approach","practical application"],
], "As a {0} practitioner of {1}, you favor {2}."))

QUIZ_TYPES.append(("Which Gate Are You?", [
    ("When you approach a sealed door, do you:",
     ["Check locks first","Put hand on it","Calculate best time","Wait for it to open","Find another way"]),
    ("The entity on the other side is:",
     ["Unknown - that is the point","Hostile - you can feel it","Curious - watching you","Indifferent","Ancient - here before the door"]),
    ("What do you carry?",
     ["Seal you made yourself","Page from grimoire","Tuning fork","Length of brass wire","Nothing"]),
], [
    ["Gate 1 - Beginning","Gate 12 - The Marid Gate","Gate 28 - The Qarin Gate","Gate 7 - Resonance","Gate 40 - The Sealed Gate","Gate 3 - Forms"],
    ["calculation","instinct","patience","curiosity","resignation"],
], "{0}. You approach thresholds with {1}."))

QUIZ_TYPES.append(("Which Entity Would Bind To You?", [
    ("Your ideal working space is:",
     ["Sealed stone chamber","High tower open to sky","Room with running water","Desert crossroads","Library with no windows"]),
    ("When negotiating, you lead with:",
     ["Logic and precision","Emotion and intuition","Silence and patience","Offers and trade","Threats and seals"]),
    ("The element you resonate with most:",
     ["Earth - stable dense patient","Water - fluid adaptive deep","Fire - transformative consuming","Air - invisible necessary everywhere","Aether - fifth the binding"]),
    ("Your preferred binding method:",
     ["Brass seal and wax","Geometric circle spoken name","Tonal frequency and vibration","Blood ink on parchment","Memory - dont write things down"]),
], [
    ["Marid","Ifrit","Ghul","Silat","Jann"],
    ["knowledge","transformation","boundaries","messages","creation"],
], "You would attract a {0} entity. Specifically one concerned with {1}."))

QUIZ_TYPES.append(("What is Your Sacred Geometry?", [
    ("Pick a shape:",
     ["Circle - wheel of time","Triangle - trinity","Square - foundation","Spiral - evolution","Point - the bindu origin","Octagon - 8 directions cosmic"]),
    ("Pick a number:",
     ["1 - unity source","3 - triad balance","4 - foundation 4 directions","7 - sacred chakras","9 - navagraha completion","40 - gates journey"]),
    ("Pick a direction:",
     ["East - light new beginnings","West - things go ancestors","North - stillness wisdom","South - burning transformation","Center - the still point","Up - spirit sky","Down - roots earth"]),
    ("Choose a tradition:",
     ["Solomonic - 72 seals brass circle","Hermetic - as above so below","Al Arbac - 40 Gates Djinn","Vedic - yantras 33M deities","Tibetan - wheel of time","Tantric - union Shri Chakra"]),
], [
    ["Flower of Life","Sri Yantra","Metatron Cube","Vesica Piscis","Golden Spiral","Tree of Life","Kalachakra Mandala","Shri Chakra","Vastu Purusha","Navagraha","Chakra System","Vajra Seal"],
    ["emanation containment","emergence from simplicity","structural precision","space between opposites","infinite growth","map of own mind","wheel turning","descent into form","grid of correspondences","ascending spiral"],
], "{0}. This pattern reflects your magic: {1}."))

QUIZ_TYPES.append(("The Elemental Temperament", [
    ("When under pressure, you:",
     ["Stand firm dont move","Flow around obstacle","Push back with heat","Become invisible","Expand to contain all"]),
    ("Your ideal familiar spirit:",
     ["Stone golem - slow unstoppable","Reflection spirit - shows need","Flame wisp - bright intense brief","Wind whisper - carries messages","Void echo - reflects missing"]),
    ("What breaks your focus?",
     ["Chaos unpredictability","Stagnation stillness","Being ignored dismissed","Enclosure limitation","Having to explain yourself"]),
    ("What do you protect?",
     ["Structures systems","Relationships connections","Ideas transformations","Freedom movement","Secrets boundaries"]),
], [
    ["Earth - stable foundational","Water - adaptive reflective","Fire - transformative illuminating","Air - invisible connective","Aether - binding beyond physical"],
    ["structure","relationship","transformation","motion","mystery"],
], "Your primary element is {0}. You approach magic through {1}."))

QUIZ_TYPES.append(("What Kind of Grimoire Would You Write?", [
    ("Your preferred writing surface:",
     ["Vellum prepared by hand","Recycled pages from books","Brass sheets engraved","Papyrus from the Source","Digital file that changes"]),
    ("Your grimoire would focus on:",
     ["Practical evocation methods","Theoretical geometry","Entity negotiation records","Alchemical recipes","Personal experiment logs"]),
    ("Your writing style is:",
     ["Precise technical dry","Poetic ambiguous layered","Direct commands and seals","Question and answer format","Diary of failures"]),
], [
    ["Lesser Key companion","Treatise on the 40 Gates","Personal Book of Abramelin","Journal of Failed Bindings","Grimoire of Practical Geometry","Cookbook of Alchemical Recipes"],
    ["cold precision","occult poetry","direct authority","collaborative inquiry","experimental honesty"],
], "Your grimoire would be a {0}. Written with {1}."))

QUIZ_TYPES.append(("Which Angelic Order Are You?", [
    ("When you witness a miracle, do you:",
     ["Worship the source","Study the mechanism","Record for posterity","Ask what it means","Try to replicate it"]),
    ("Your relationship to the divine is:",
     ["Direct burning revelation","Intellectual understanding","Guarded skepticism","Reverent distance","Practical cooperation"]),
    ("Choose a mode of perception:",
     ["Vision - seeing unseen","Intuition - knowing without knowing","Reason - understanding structure","Feeling - emotional resonance","Action - doing the will"]),
], [
    ["Seraphim - pure frequency","Cherubim - hidden knowledge","Thrones - judgment geometry","Dominions - mercy transformation","Virtues - strength boundaries","Powers - healing harmony","Principalities - beauty resonance","Archangels - protection authority","Angels - messages cycles"],
    ["burning devotion","watchful wisdom","structural judgment","merciful transformation","boundaried strength","healing harmony"],
], "You resonate with {0}. Your mode is {1}."))

QUIZ_TYPES.append(("What is Your Sigil Style?", [
    ("Choose a foundation shape:",
     ["Circle - containment protection","Triangle - direction force","Square - stability earth","Spiral - evolution journey","Dot - origin singular focus"]),
    ("Your sigil would be inscribed in:",
     ["Brass - eternal medium","Obsidian - darkness reflecting","Gold - sun made solid","Blood - most personal ink","Light - ephemeral powerful","Sound - heard not seen"]),
    ("Where do you place your sigils?",
     ["On the doorframe","Under the floor","On your skin","Inside a book","In the air with incense","Only in memory"]),
], [
    ["The Minimalist - simple lines","The Ornate - every curve means something","The Geometric - platonic solids","The Calligraphic - letters as shapes","The Abstract - feeling over form","The Acoustic - drawn with sound"],
    ["precision restraint","elaborate meaning","structural perfection","verbal power","emotional resonance","harmonic frequency"],
], "Your sigil style is {0}. Crafted with {1}."))

QUIZ_TYPES.append(("Which Alchemical Stage Are You In?", [
    ("Where do you keep your materials?",
     ["Locked in a brass box","Scattered across my workspace","In my memory only","Organized by planetary hour","Buried for later"]),
    ("Your approach to transformation is:",
     ["Slow and patient","Intense and rapid","Observe first act later","Collaborate with others","Destroy and rebuild"]),
    ("What color resonates most?",
     ["Black - the prima materia","White - purification","Yellow - the dawn","Red - completion","Green - the living work"]),
], [
    ["Nigredo - the blackening, putrefaction, the start","Albedo - whitening, purification, lunar clarity","Citrinitas - yellowing, solar awakening","Rubedo - reddening, perfection, the stone"],
    ["breaking down","purifying","awakening","completing"],
], "You are in {0}. Your work now is {1}."))

QUIZ_TYPES.append(("What is Your Planetary Hour?", [
    ("Your peak energy time is:",
     ["Just before dawn - Mercury hour","Midday - Sun hour","Dusk - Venus hour","Midnight - Moon hour","3am - Saturn hour"]),
    ("Your preferred metal:",
     ["Mercury - quicksilver","Gold - the sun","Silver - the moon","Copper - Venus","Iron - Mars","Lead - Saturn","Tin - Jupiter"]),
    ("When working magic, you lead with:",
     ["Speed and communication Mercury","Authority and vitality Sun","Emotion and intuition Moon","Love and harmony Venus","Strength and will Mars","Expansion and abundance Jupiter","Discipline and structure Saturn"]),
], [
    ["Mercury - communication speed","Venus - love harmony art","Mars - will force conflict","Jupiter - expansion growth","Saturn - discipline structure","Sun - vitality authority","Moon - emotion intuition"],
    ["quick adaptive thinking","graceful harmonious creation","fierce determined action","abundant generous growth","patient structural building","radiant vital leadership","depth emotional receptivity"],
], "Your planetary hour is {0}. You operate through {1}."))

QUIZ_TYPES.append(("Which Djinn Class Would You Bargain With?", [
    ("Your approach to negotiation:",
     ["State terms clearly and wait","Offer something unexpected","Show strength first","Speak in riddles","Silence - let them speak first"]),
    ("What do you offer in a pact?",
     ["Knowledge from a grimoire","A favor to be named later","A physical object of power","Your service for a time","Nothing - they owe you"]),
    ("If the deal goes bad, you:",
     ["Invoke the binding seal","Try to renegotiate","Walk away","Destroy the circle","Let it play out"]),
], [
    ["Marid - great works and tempests","Ifrit - battle and transformation","Ghul - wilderness and decay","Silat - illusions and messages","Jann - hidden places and boundaries"],
    ["direct powerful negotiation","fiery transformative deals","patient wild bargains","clever illusory trades","quiet boundary pacts"],
], "You would bargain with a {0}. Your negotiation style: {1}."))

QUIZ_TYPES.append(("What is Your Memory Palace Architecture?", [
    ("Your memory palace is built from:",
     ["A library with endless shelves","A cathedral with stained glass","A labyrinth of corridors","A tower with spiral stairs","A garden with labeled paths"]),
    ("How do you organize memories?",
     ["By emotion - how they felt","By frequency - what they resonate at","By chronology - when they happened","By entity - who was involved","By geometry - what shape they make"]),
    ("Locked rooms in your palace contain:",
     ["Things I am not ready to face","Knowledge too dangerous to use","People I have lost","Promises I broke","The Gate 40 research"]),
], [
    ["The Infinite Library - every book a memory","The Glass Cathedral - light reveals what you need","The Spiral Tower - ascend to remember deeper","The Hedge Maze - memories hide around corners","The Underground Vault - protected and buried"],
    ["emotional tagging","resonant cataloging","chronological stacking","entity indexing","geometric mapping"],
], "Your memory palace is {0}. You organize by {1}."))

QUIZ_TYPES.append(("Which Magical Art Suits You?", [
    ("Your hands are best used for:",
     ["Drawing precise geometric lines","Holding a tuning fork to metal","Turning pages of old books","Mixing compounds carefully","Writing names in wax"]),
    ("Your ideal tool is:",
     ["A compass and straightedge","A brass bell or gong","A stylus and wax tablet","A mortar and pestle","A mirror or crystal"]),
    ("When magic works for you, it feels like:",
     ["Everything clicking into place geometrically","A frequency humming through your body","Understanding something you always knew","Watching transformation happen","Being exactly where you should be"]),
], [
    ["Theurgic Invocation - calling angels through arrays","Goetic Evocation - binding demons in circles","Alchemical Transmutation - refining metals and self","Planetary Magic - working with celestial spirits","Sigil Craft - designing personal geometric seals","Geomancy - earth pattern divination","Voice Magic - tonal vibration as force"],
    ["geometric precision","harmonic resonance","intellectual understanding","transformative practice","spatial alignment"],
], "Your art is {0}. You practice through {1}."))

QUIZ_TYPES.append(("What is Your Tone / Frequency?", [
    ("At rest, your internal hum is:",
     ["Low and steady like a bass drone","Fluttering like rapid strings","A clear single tone","Silence with harmonics underneath","Pulsing rhythmic"]),
    ("Your voice in a circle sounds:",
     ["Deep, commanding, floor-shaking","Bright, cutting through noise","Soft, everyone quiet to hear","Rhythmic, hypnotic","Cracked - imperfect but real"]),
    ("The frequency you return to:",
     ["432Hz - grounding, foundation","528Hz - transformation, repair","639Hz - connection, relationship","741Hz - expression, clarity","852Hz - intuition, return","963Hz - transcendence, crown"]),
], [
    ["432Hz - grounding bass, the earth tone","528Hz - transformation, the repair frequency","639Hz - heart-harmonic, connection","741Hz - purification, expression","852Hz - return to spirit, third eye","963Hz - crown resonance, transcendence","111Hz - manifestation, physical vibration"],
    ["deep foundation","transformative repair","heart connection","clear expression","spiritual return","transcendent awareness","physical manifestation"],
], "Your personal frequency is {0}. You resonate through {1}."))

QUIZ_TYPES.append(("Which Sacred Site Is Your Home?", [
    ("Choose a direction to face when working:",
     ["North - stillness and wisdom","East - dawn and beginnings","South - heat and transformation","West - dusk and ancestors","Center - all directions at once"]),
    ("Choose an element to work with:",
     ["Earth - basalt granite clay","Water - mercury salt rain","Fire - forge flame sun","Air - incense wind breath","Aether - the void between"]),
    ("Your ideal sacred geometry base:",
     ["Square - foundation stability","Circle - containment eternity","Triangle - direction ascent","Hexagram - binding balance","Spiral - evolution journey","Mandala - completion wholeness"]),
], [
    ["Ziggurat of the 40 Gates - Solomonic stepped pyramid","Shri Yantra Mandapam - 9-tiered triangle temple descending","Kalachakra Stupa - Tibetan wheel of time concentric circles","Heptameron Cathedral - 7-ring planetary angelic cone","Al Arbac Sanctuary - 40-sided Djinn polygon","Navagraha Platform - 3x3 celestial grid","Temple of the Seal of Solomon - hexagram wisdom","The Seraphim Step-Pyramid - 9-tier angelic ascent"],
    ["disciplined structured approach","creative fluid exploration","intense transformative work","intellectual contemplative study","adaptive eclectic practice"],
], "Your sacred home is {0}. You work best with {1}."))

def gen_quiz(name, archetype, enriched_pers):
    s = H(name)
    if not QUIZ_TYPES:
        return []
    # Variable quiz count: 0 to 6, like MySpace profiles had 0-10+ surveys
    quiz_count = (s % 7)  # gives 0-6
    if quiz_count == 0:
        return []
    results = []
    used_indices = set()
    for qi in range(quiz_count):
        idx = (s + qi * 13) % len(QUIZ_TYPES)
        # Avoid dupes, allow repeats if pool is small
        while idx in used_indices and len(used_indices) < len(QUIZ_TYPES):
            idx = (idx + 1) % len(QUIZ_TYPES)
        used_indices.add(idx)
        qt = QUIZ_TYPES[idx]
        qname, qdata, pools, fmt = qt
        # Variable depth: some quizzes have more questions (2 to 4)
        qcount = 2 + ((s + qi * 7) % 3)  # 2, 3, or 4 questions
        qlist = []
        for i in range(min(qcount, len(qdata))):
            q_text, *answer_groups = qdata[i]
            answers = [pick(group, s+qi*100+i*10+j) for j, group in enumerate(answer_groups)]
            qlist.append({"q": q_text, "a": answers})
        picks = [pick(pool, s+qi*50+i*5+100) for i, pool in enumerate(pools)]
        result = fmt.format(*picks)
        results.append({"type": qname, "questions": qlist, "result": result})
    return results

LANGUAGES = {
    "philosopher-rhetorician": {"primary": "Greek", "also": ["Latin", "Arabic"]},
    "philosopher-teacher": {"primary": "Latin", "also": ["Greek", "Enochian"]},
    "demigod-trickster": {"primary": "Enochian", "also": ["Arabic", "Greek"]},
    "demigod-warrior": {"primary": "Arabic", "also": ["Latin", "Enochian"]},
    "lawgiver": {"primary": "Latin", "also": ["Hebrew", "Greek"]},
    "architect-sage": {"primary": "Greek", "also": ["Arabic", "Enochian"]},
    "capitalist": {"primary": "Arabic", "also": ["Latin", "Greek"]},
    "poet-artist": {"primary": "Greek", "also": ["Latin", "Arabic"]},
    "sage": {"primary": "Enochian", "also": ["Greek", "Hebrew"]},
    "visionary": {"primary": "Enochian", "also": ["Arabic", "Greek"]},
    "creator": {"primary": "Latin", "also": ["Greek", "Arabic"]},
    "artisan": {"primary": "Arabic", "also": ["Latin", "Greek"]},
    "healer": {"primary": "Greek", "also": ["Latin", "Arabic"]},
    "explorer": {"primary": "Arabic", "also": ["Greek", "Enochian"]},
    "guardian": {"primary": "Latin", "also": ["Hebrew", "Greek"]},
}
ALL_LANGS = ["English", "Arabic", "Latin", "Greek", "Enochian", "Hebrew", "Aramaic", "Coptic"]
