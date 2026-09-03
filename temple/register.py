"""How a spark talks, as distinct from what it says.

The lexicon came out bland - delicate, guidance, fascinating, philosophical -
and the reason was upstream of the lexicon. Every archetype's voice
instruction was written in the same literary key: "speak with the certainty
of someone who has seen through the lie", "feel everything, every bond is a
lifeline". Given prompts like that a model produces careful essay English,
and 298 sparks producing careful essay English have no dialect to drift.

Nothing was censoring them. Nobody had ever told them they were allowed to
talk like people.

So register is a separate axis from archetype. Archetype is what a spark
cares about; register is the mouth it says it with. A heretic and a witness
can both be foul-mouthed, and two mystics can sound nothing alike - which is
the point, because a world where everyone shares one prose style has no
vocabulary to diverge.

The assignment is deterministic from the spark's own name, so a spark's
manner of speech is a fact about it rather than something that rerolls every
cycle. It never changes underneath them.

The weights are not uniform. Most people talk plainly; a few are foul, a few
are ornate, and the ornate ones are rare on purpose - if everyone is florid,
florid is the baseline and nothing stands out.
"""
import hashlib

# The register a spark speaks in, and how common that is. Weights are
# roughly how people actually distribute: mostly plain, a decent minority
# crude, ornate genuinely rare.
REGISTERS = {
    "plain": (34, """Talk like a person talking, not like a person writing.
Contractions. Short sentences. Say the ordinary word instead of the
impressive one - "use" not "utilise", "start" not "commence"."""),

    "crude": (22, """You swear, and not for effect - it is just how you talk.
Fuck, shit, hell, bastard, arse, whatever fits. Contractions, fragments,
half-finished thoughts. You interrupt yourself. You are not trying to sound
clever and you never reach for the fancy word."""),

    "slangy": (16, """You talk in slang and you make up your own. Shorten
things. Nickname everything and everyone. Use the same handful of words for
everything until they mean too much. Say "dead" for boring, or invent
better. Never the dictionary word if a worse one is funnier."""),

    "clipped": (12, """Few words. No adjectives you can cut. Sentence
fragments are fine. You would rather say nothing than pad. Never explain
twice."""),

    "warm": (9, """You talk to people, not at them. You use their names. You
ask things. You say when you do not know. Easy, unguarded, a bit rambling
when you are comfortable."""),

    "ornate": (7, """Long sentences that hold their shape. Uncommon words
where the common one is imprecise. Metaphor drawn from what you actually
know. Never flowery for its own sake - you are exact, and exactness happens
to be beautiful."""),
}

# Things every spark is told, regardless of register. These exist because a
# model's default register is a press release, and it drifts back to it
# unless told plainly not to.
UNIVERSAL = """Do not write like an article. No "moreover", no "it is worth
noting", no "in conclusion", no summing up at the end. Do not be balanced.
Do not hedge. Repeat yourself if you are worked up. Trail off if you lose
the thread."""


def _weighted_pick(name: str) -> str:
    """Deterministic from the name, so a spark's mouth is a fact about it."""
    total = sum(w for w, _ in REGISTERS.values())
    h = int(hashlib.sha256(("register:" + name).encode()).hexdigest()[:8], 16)
    point = h % total
    for reg, (weight, _) in sorted(REGISTERS.items()):
        if point < weight:
            return reg
        point -= weight
    return "plain"


def register_of(spark_name: str) -> str:
    return _weighted_pick(spark_name)


def instruction(spark_name: str) -> str:
    """The whole of what a spark is told about how to speak."""
    reg = register_of(spark_name)
    body = REGISTERS[reg][1].replace("\n", " ").strip()
    return "HOW YOU TALK (%s): %s %s" % (reg, body, UNIVERSAL.replace("\n", " "))


def census() -> dict:
    """How the population divides, for checking the weights hold up."""
    import sqlite3
    from pathlib import Path
    db = Path(__file__).resolve().parent / "soul.db"
    try:
        c = sqlite3.connect(str(db), timeout=20)
        names = [r[0] for r in c.execute("SELECT spark_name FROM spark_state")]
        c.close()
    except sqlite3.Error as e:
        return {"error": str(e)}
    out = {}
    for n in names:
        r = register_of(n)
        out[r] = out.get(r, 0) + 1
    return {"population": len(names),
            "registers": dict(sorted(out.items(), key=lambda kv: -kv[1]))}
