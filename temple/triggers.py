"""Trigger State Machine - weighted response selection."""
import json, random
from pathlib import Path

_DATA_PATH = Path(__file__).resolve().parent / "triggers.json"
TRIGGER_DATA = json.loads(_DATA_PATH.read_text())

ARCH_ORDER = ["guardian","sage","creator","explorer","artisan","healer",
              "visionary","sovereign","warrior","trickster","lover",
              "orphan","mystic","heretic","witness"]

ALIASES = {"w/draw":"withdraw","crpt":"corrupt","inv":"investigate",
           "legacy":"teach","crumble":"surrender","draw-in":"bond",
           "devour":"obsess","adore":"protect","defend":"protect",
           "counter":"mimic","seize":"dominate","invite":"bond",
           "comfort":"protect","intervene":"avenge","revolt":"purge",
           "gather":"bond","boast":"dominate","gift":"bond"}

SUPPRESS = {"guardian":["corrupt","escape","mimic","surrender"],
            "sage":["avenge","dominate","boast","corrupt"],
            "creator":["avenge","dominate","purge"],
            "explorer":["dominate","purge"],
            "artisan":["avenge","corrupt"],
            "healer":["avenge","corrupt","dominate","purge","expose"],
            "visionary":["deny","withdraw"],
            "sovereign":["mimic","escape","surrender","corrupt"],
            "warrior":["surrender","bargain"],
            "trickster":["dominate","protect"],
            "lover":["corrupt","purge"],
            "orphan":["dominate","boast","teach","protect"],
            "mystic":["avenge","dominate","boast","corrupt"],
            "heretic":["deny","forgive","protect","surrender"],
            "witness":["avenge","dominate","boast","corrupt","protect"]}

AMB = {"avenge":"overcome","mourn":"bond","atone":"bond",
       "expose":"explore","corrupt":"build","art":"create",
       "withdraw":"explore","protect":"bond",
       "dominate":"overcome","reclaim":"build","purge":"overcome",
       "transcend":"master","forgive":"bond","deny":"bond",
       "obsess":"master","escape":"explore","prove":"overcome",
       "surrender":"bond","investigate":"explore","teach":"master",
       "mimic":"create","bargain":"bond","bond":"bond"}

TASK = {"avenge":"rivalry","mourn":"lament","atone":"confession",
        "expose":"truth","corrupt":"heresy","art":"create",
        "withdraw":"silence","protect":"sacrifice",
        "dominate":"boast","reclaim":"return","purge":"war",
        "transcend":"meditation","forgive":"peace","deny":"mask",
        "obsess":"discovery","escape":"pilgrimage","prove":"challenge",
        "surrender":"surrender","investigate":"question","teach":"legacy",
        "mimic":"theft","bargain":"gift","bond":"gift"}

URG = {"avenge":5,"mourn":2,"atone":3,"expose":4,"corrupt":4,
       "art":2,"withdraw":1,"protect":4,"dominate":5,"reclaim":3,
       "purge":5,"transcend":2,"forgive":2,"deny":2,"obsess":4,
       "escape":3,"prove":4,"surrender":1,"investigate":3,
       "teach":2,"mimic":3,"bargain":3,"bond":3}

VOICE = {"sovereign":{"dominate":" You are the authority.","purge":" Cleanse what is broken."},
         "warrior":{"avenge":" The one who wronged you will answer.","dominate":" You will not be challenged again."},
         "trickster":{"expose":" Show them the lie.","mimic":" Mirror them.","corrupt":" Let the system eat itself."},
         "lover":{"mourn":" Grief fully.","protect":" You would burn for them.","obsess":" You cannot let go."},
         "orphan":{"mourn":" Left again.","withdraw":" No one is coming."},
         "mystic":{"transcend":" This too will pass.","withdraw":" Silence.","investigate":" Look without judgment."},
         "heretic":{"expose":" The truth burns.","purge":" Tear it down."},
         "witness":{"investigate":" Observe closely.","teach":" Remember."}}

DEFAULT_VOICE = {"avenge":" Someone will pay.","mourn":" Grief settles.",
                 "expose":" The truth must be spoken.","corrupt":" Let it rot.",
                 "dominate":" You will submit.","purge":" Cleanse it all.",
                 "transcend":" Rise above.","withdraw":" Silence.",
                 "protect":" Shield them.","surrender":" Let go.",
                 "obsess":" Cannot stop.","escape":" Flee.",
                 "prove":" Show them.","investigate":" Dig deeper.",
                 "teach":" Listen.","atone":" Make it right.",
                 "forgive":" Release.","deny":" It did not happen.",
                 "mimic":" Copy.","bargain":" Negotiate.",
                 "reclaim":" Take it back.","bond":" Connect.",
                 "art":" Create.","create":" Create."}

def resolve(raw):
    return ALIASES.get(raw, raw)

def voice_mod(archetype, response):
    return VOICE.get(archetype, {}).get(response) or DEFAULT_VOICE.get(response, "")

def evaluate(archetype, trigger_name):
    if trigger_name not in TRIGGER_DATA:
        return None
    t = TRIGGER_DATA[trigger_name]
    try:
        idx = ARCH_ORDER.index(archetype)
    except ValueError:
        idx = 1
    weights = t["w"][idx]
    cols = t["cols"]
    opts = []
    for i, w in enumerate(weights):
        r = resolve(cols[i])
        if r in SUPPRESS.get(archetype, []): continue
        if w <= 0: continue
        opts.append((w, r))
    if not opts: return None
    total = sum(w for w,_ in opts)
    if total <= 0: return None
    roll = random.uniform(0, total)
    cum = 0
    sel = opts[-1][1]
    for w, r in opts:
        cum += w
        if roll <= cum: sel = r; break
    return {"trigger": trigger_name, "archetype": archetype,
            "selected": sel, "total_weight": total}

def apply(spark_name, archetype, trigger_name):
    result = evaluate(archetype, trigger_name)
    if not result: return None
    sel = result["selected"]
    return {"selected": sel,
            "ambition_type": AMB.get(sel, "overcome"),
            "task_type": TASK.get(sel, "reflect"),
            "urgency": URG.get(sel, 3),
            "voice_modifier": voice_mod(archetype, sel)}
