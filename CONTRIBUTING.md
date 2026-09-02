# Contributing

This is one person's research project that grew into a world. Contributions
are welcome; so is just reading it and telling me it is strange.

## Before you start

Open an issue describing what you want to change. The system has a lot of
load-bearing weirdness — mechanisms that look accidental and are not — and a
short conversation first saves both of us a wasted afternoon.

## Running it

You need:

- Python 3.11 or newer
- [Ollama](https://ollama.com) with at least one model pulled
- A GPU if you want more than a handful of sparks thinking at once

```sh
git clone https://github.com/nviiiivn/umbreality
cd umbreality
cp .env.example .env        # fill in whatever you actually use
docker compose up -d
```

The databases are not in this repository — they are the sparks' own memories
and run to 231MB. On a fresh clone the world starts empty and populates
itself.

## House style

The code is written to be read by someone who was not there when it was
written. Two things matter more than anything else:

**Comments explain why, not what.** `# increment the counter` above `i += 1`
is noise. `# the rotation position lives on the function object, so a
restart sends it back to the first twelve sparks alphabetically` is the
comment that would have saved eleven weeks.

**Failures must be loud.** There is a long history in this codebase of bare
`except: pass` hiding real breakage for months — dropped sparks, silent
dispatch failures, counters that could never increment. If you catch an
exception, catch a specific one and print what happened.

## What is most useful

- The self-modification loop exists, is sandboxed, and has never been
  allowed to act. Look at `temple/selfmod.py` and `temple/sandbox.py`.
- Language drift (`temple/drift.py`) is the most interesting part and the
  most fragile. It has leaked engine text as spark speech four separate
  times. Every fix has been structural rather than another blacklist.
- Anything measuring whether emergent behaviour is real rather than
  imagined. Honest negative results are worth more here than encouraging
  ones.
