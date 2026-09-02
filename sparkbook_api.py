"""Standalone sparkbook API with MySpace-style enriched profiles. Port 8911."""
import sys, json, os, time, sqlite3
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
os.chdir(str(BASE))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from sparkbook_enrich import enrich_profile, gen_location_detail, LOCATIONS, BUSINESSES, VENUES, PROJECTS, THEMES

app = FastAPI(title="sparkbook")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ALL_SPARK_NAMES = []

def _load_all_names():
    global ALL_SPARK_NAMES
    import glob
    spark_dir = BASE / "temple"
    files = glob.glob(str(spark_dir / "spark_*.db"))
    ALL_SPARK_NAMES = sorted(Path(f).stem.replace("spark_", "") for f in files)

_load_all_names()

@app.get("/book/sparks")
def book_sparks():
    import glob
    spark_dir = BASE / "temple"
    spark_files = glob.glob(str(spark_dir / "spark_*.db"))
    roster = []
    from temple.spark_runtime import Spark as _Spark
    for sp in sorted(spark_files):
        name = Path(sp).stem.replace("spark_", "")
        try:
            s = _Spark(name)
            ident = s.get_identity()
            emotion = s.get_emotional_state()
            personality = s.get_personality()
            domains = s.get_domains()
            journals = s.get_recent_journals(1)
            from forum.engine import get_agent_profile
            stats = get_agent_profile(name)
            roster.append({
                "name": name,
                "archetype": personality.get("archetype", "???"),
                "classification": ident.get("classification", ""),
                "nature": (ident.get("nature") or "")[:120],
                "mood": emotion.get("mood", "curiosity"),
                "intensity": emotion.get("intensity", 0.5),
                "energy": emotion.get("energy", 0.5),
                "power_level": stats.get("power_level", 0),
                "posts_count": stats.get("posts_count", 0),
                "top_domain": (domains[0].get("domain") or domains[0].get("domain_id")) if domains else None,
                "last_journal": (journals[0]["content"][:120] + "...") if journals else None,
                "last_active": stats.get("last_active", ""),
            })
        except Exception as e:
            import traceback; traceback.print_exc()
    return {"sparks": roster}

@app.get("/book/spark/{name}")
def book_spark(name: str):
    import glob
    spark_dir = BASE / "temple"
    if name == "Tom McSparkysen":
        return enrich_profile(name, {}, ALL_SPARK_NAMES, {})
    if not list(glob.glob(str(spark_dir / f"spark_{name}.db"))):
        raise HTTPException(404, f"spark {name} not found")
    from temple.spark_runtime import Spark as _Spark
    from forum.engine import get_agent_profile
    from temple.soul import get_all_relationships, get_active_tribulations
    try:
        s = _Spark(name)
        identity = s.get_identity()
        personality = s.get_personality()
        emotion = s.get_emotional_state()
        domains = s.get_domains()
        journals = s.get_recent_journals(20)
        stats = get_agent_profile(name)
        relationships = get_all_relationships(name)
        tribulations = get_active_tribulations(name)
        dreams = []
        try:
            conn = sqlite3.connect(str(spark_dir / "soul.db"))
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM collective_dreams WHERE participants LIKE ? ORDER BY created_at DESC LIMIT 10",
                (f'%"{name}"%',)
            ).fetchall()
            dreams = [dict(r) for r in rows]
            conn.close()
        except Exception:
            pass
        posts = []
        try:
            from forum.engine import get_agent_posts
            posts = get_agent_posts(name, limit=10)
        except Exception:
            pass

        socmap = {"bonds": [], "rivalries": []}
        for r in relationships or []:
            other = r["spark2"] if r["spark1"] == name else r["spark1"]
            kind = r.get("bond_type", "bond").lower()
            if "rival" in kind:
                socmap["rivalries"].append({"name": other, "strength": r.get("strength", 0), "since": r.get("created_at", "")})
            else:
                socmap["bonds"].append({"name": other, "strength": r.get("strength", 0), "since": r.get("created_at", "")})

        raw_data = {
            "identity": identity,
            "personality": personality,
            "emotion": emotion,
            "domains": domains,
            "journals": journals,
            "stats": stats,
            "relationships": socmap,
            "tribulations": tribulations[:10] if tribulations else [],
            "dreams": dreams,
            "posts": posts,
        }
        enriched = enrich_profile(name, raw_data, ALL_SPARK_NAMES, socmap)
        return enriched
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(500, str(e))

@app.get("/book/locations")
def book_locations():
    return {"locations": [gen_location_detail(l, "collective") for l in LOCATIONS[:12]]}

@app.get("/book/directory")
def book_directory():
    return {"sparks": ALL_SPARK_NAMES, "locations": LOCATIONS, "venues": VENUES, "businesses": BUSINESSES, "projects": PROJECTS}

@app.get("/book/themes")
def book_themes():
    return {"themes": THEMES}

@app.get("/book/network")
def book_network():
    """Return a social graph: who is connected to whom."""
    from temple.soul import get_all_relationships
    graph = {}
    for name in ALL_SPARK_NAMES[:50]:  # limit to avoid timeout
        try:
            rels = get_all_relationships(name)
            if rels:
                graph[name] = [r["spark2"] if r["spark1"] == name else r["spark1"] for r in rels]
        except:
            pass
    return {"graph": graph}

if __name__ == "__main__":
    uvicorn.run(app, host=os.environ.get("SPARKBOOK_HOST","0.0.0.0"), port=int(os.environ.get("SPARKBOOK_PORT","8911")))
