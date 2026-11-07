"""MC WHACK: every call to whack() becomes a rap verse, and then a live performance.

    python3 spit.py            # one verse, printed + verse.html player
    python3 spit.py --battle   # two MCs, two whack() calls, one winner

What whack() controls:
  * how many words it returns  -> how many bars you get and the BPM
  * the order of the words     -> which words land on the end of each line (the rhymes)
  * the `whack` file it writes -> the most-repeated word in it becomes the HOOK
  * sponsor vs suffering words -> the mood (FLEXING or CRYING AT 3AM)
"""
import json
import re
import random
import sys
from collections import Counter
from pathlib import Path

from whack import whack

# Every one of the 42 words belongs to a rhyme family, with some everyday rhymes to fall back on.
FAMILIES = {
    "ack": (["whack", "hack", "quack", "stack"], ["back", "track", "attack", "jack"]),
    "uck": (["duck"], ["stuck", "luck", "truck", "pluck"]),
    "oose": (["goose"], ["loose", "juice", "produce", "use"]),
    "onk": (["honk"], ["bonk", "plonk", "conk"]),
    "ug": (["bug"], ["plug", "shrug", "mug", "hug"]),
    "eature": (["feature"], ["creature", "teacher", "preacher"]),
    "ick": (["warwick"], ["quick", "slick", "trick", "brick"]),
    "iculous": (["oculus"], ["ridiculous", "meticulous"]),
    "ock": (["compsoc"], ["clock", "rock", "lock", "block"]),
    "artial": (["marshall"], ["partial", "martial"]),
    "ace": (["wace"], ["race", "face", "space", "place"]),
    "even": (["brevan"], ["seven", "heaven", "eleven"]),
    "oward": (["howard"], ["coward", "powered", "showered"]),
    "apital": (["capital"], ["hospital", "tropical", "habitual"]),
    "un": (["one"], ["done", "run", "fun", "won"]),
    "erg": (["bloomberg"], ["iceberg", "Nuremberg"]),
    "aft": (["netcraft"], ["daft", "laughed", "draft", "graft"]),
    "ident": (["incident"], ["confident", "accident", "president"]),
    "o": (["io", "overflow", "demo"], ["flow", "go", "show", "slow"]),
    "eeza": (["pizza"], ["Ibiza", "Mona Lisa", "visa"]),
    "offee": (["coffee"], ["toffee", "trophy"]),
    "eep": (["sleep"], ["deep", "keep", "cheap", "sheep"]),
    "oy": (["deploy"], ["destroy", "joy", "boy", "toy"]),
    "erge": (["merge"], ["urge", "surge", "verge", "purge"]),
    "ict": (["conflict"], ["convict", "strict", "predict"]),
    "it": (["commit"], ["quit", "lit", "split", "spit"]),
    "ush": (["push"], ["rush", "hush", "crush", "blush"]),
    "od": (["prod"], ["god", "nod", "odd", "squad"]),
    "ault": (["segfault"], ["default", "assault", "halt", "salt"]),
    "ull": (["null"], ["dull", "skull", "full", "pull"]),
    "ointer": (["pointer"], ["anointer", "disappointer"]),
    "olon": (["semicolon"], ["swollen", "stolen", "rollin'"]),
    "ubber": (["rubber"], ["lover", "cover", "brother"]),
    "itch": (["pitch"], ["glitch", "switch", "rich", "snitch"]),
    "ize": (["prize"], ["eyes", "rise", "size", "lies"]),
    "ight": (["midnight"], ["tonight", "fight", "light", "right"]),
    "ifi": (["wifi"], ["hi-fi", "sci-fi"]),
}
FAMILY_OF = {w: fam for fam, (members, _) in FAMILIES.items() for w in members}

SPONSORS = {"warwick", "oculus", "compsoc", "marshall", "wace", "brevan", "howard",
            "capital", "one", "bloomberg", "netcraft", "incident", "io", "prize"}
SUFFERING = {"bug", "sleep", "coffee", "conflict", "segfault", "null", "pointer", "stack",
             "overflow", "semicolon", "midnight", "wifi", "prod", "merge", "deploy"}

# Every line is exactly 12 syllables, one per 16th note, with the last one landing on the snare.
SYLLABLES_PER_BAR = 12
FLOW = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12]  # which 16th note each syllable lands on

# {e} = end rhyme, {r}/{s} = internal rhymes (same family as {e}), {a}/{b} = any whack() word
TEMPLATES = {
    "FLEXING": [
        "Pull up with a {r} and a {a}, now I'm the {e}",
        "They call me MC {R}, I'm the king of the {e}",
        "{R} in the bag, {a} on my {e}",
        "Sponsored by {r}, yeah I'm flexing on {e}",
        "Diamonds on my {r}, gold chain made of {e}",
        "Hands up for the {r}, hands up for the {e}",
        "Got a {r}, got a {a}, call me {e}",
        "My {r} so cold, my {a} so {e}",
        "{R}, {S}, I'm the {a} {e}",
        "I don't chase {r}, I just catch the {e}",
    ],
    "CRYING AT 3AM": [
        "Mama said no {r}, so I ran it on {e}",
        "{R} at three AM, still chasing that {e}",
        "I ain't got {r}, I ain't got {e}",
        "Pass me the {r} and the {a}, it's {e}",
        "My {a} hit a {r}, now my life is {e}",
        "Ten cups of {r} and I'm still on {e}",
        "{R}, {S}, my {a} is {e}",
        "Every time I {r}, I get a {e}",
        "Tears on my {r}, it's a {a} {e}",
        "Rubber duck, tell me why my {r} is {e}",
    ],
}
FALLBACKS = ["{R}, {S}, {e}", "{R}, {e}"]
ADLIBS = ["yo", "uh", "yeah", "skrrt", "huh", "quack"]

SYL_OVERRIDES = {
    "io": 2, "oculus": 3, "warwick": 2, "wace": 1, "capital": 3, "bloomberg": 2,
    "incident": 3, "deploy": 2, "overflow": 3, "semicolon": 4, "demo": 2, "wifi": 2,
    "feature": 2, "creature": 2, "teacher": 2, "preacher": 2, "ridiculous": 4,
    "meticulous": 4, "ibiza": 3, "habitual": 4, "anointer": 3, "disappointer": 4,
    "nuremberg": 3, "iceberg": 2, "produce": 2, "eleven": 3, "heaven": 2, "seven": 2,
    "president": 3, "confident": 3, "accident": 3, "trophy": 2, "toffee": 2,
    "every": 2, "everybody": 4, "diamonds": 2, "mc": 2, "am": 2, "they": 1, "ya'll": 1,
    "y'all": 1, "rollin'": 2, "pointer": 2, "conflict": 2, "commit": 2, "marshall": 2,
    "brevan": 2, "howard": 2, "segfault": 2, "default": 2, "assault": 2, "skrrt": 1,
    "chasing": 2, "sponsored": 2, "flexing": 2, "mona": 2, "lisa": 2, "quack": 1,
    "fire": 1, "life": 1, "time": 1, "cold": 1, "made": 1, "one": 1, "whack": 1,
}


def syl(text):
    """Syllables in a word or phrase (a small hand-tuned counter)."""
    total = 0
    for w in re.findall(r"[a-z']+", text.lower().replace("-", " ")):
        if w in SYL_OVERRIDES:
            total += SYL_OVERRIDES[w]
            continue
        n = len(re.findall(r"[aeiouy]+", w))
        if w.endswith("e") and not w.endswith(("le", "ee")) and n > 1:
            n -= 1
        total += max(1, n)
    return total


def tok(text, kind, fam=None):
    return {"t": text, "syl": syl(text), "kind": kind, "fam": fam}


def render(template, fill):
    """Splits a template into tokens: plain text, slot words, internal rhymes, end rhyme."""
    out = []
    for part in re.split(r"(\{[a-zA-Z]\})", template):
        if not part:
            continue
        m = re.fullmatch(r"\{([a-zA-Z])\}", part)
        if not m:
            out.append(tok(part, "text"))
            continue
        key = m.group(1)
        word, kind, fam = fill[key.lower()]
        out.append({**tok(word.upper() if key.isupper() else word, kind, fam)})
    return out


def build_line(templates, end, end_from_whack, words, feed, used):
    """Finds a template + whack() words that make exactly 12 syllables, with internal rhymes."""
    fam = FAMILY_OF.get(end) or next(f for f, (_, fill) in FAMILIES.items() if end in fill)
    members, fillers = FAMILIES[fam]
    present = set(words)
    rhymes = [w for w in members if w in present and w != end]           # whack-on-whack first
    rhymes += [w for w in members + fillers if w not in rhymes and w != end]
    best = None
    for template in templates + FALLBACKS:
        slots = set(re.findall(r"\{([a-z])\}", template.lower())) - {"e"}
        need_r = [k for k in ("r", "s") if k in slots]
        need_a = [k for k in ("a", "b") if k in slots]
        r_choices = [rhymes[i:i + len(need_r)] for i in range(len(rhymes) - len(need_r) + 1)]
        for rs in r_choices:
            pool = [w for w in feed[:12] if w != end and w not in rs]
            for As in ([[]] if not need_a else [[w] for w in pool]):
                fill = {"e": (end, "end", fam)}
                for k, w in zip(need_r, rs):
                    fill[k] = (w, "rhyme", fam)
                for k, w in zip(need_a, As):
                    fill[k] = (w, "word", None)
                toks = render(template, fill)
                gap = SYLLABLES_PER_BAR - sum(t["syl"] for t in toks)
                if gap < 0 or (template in FALLBACKS and best and best[0][0] <= 4):
                    continue
                n_whack = sum(w in present for w in rs)
                key = (gap + 2 * used[template], -n_whack, random.random())
                if best is None or key < best[0]:
                    best = (key, toks, As, n_whack, template)
    if best is None:
        raise RuntimeError("no line fits")
    (gap, *_), toks, As, n_whack, template = best
    used[template] += 1
    for w in As:  # used words go to the back of the queue
        feed.remove(w)
        feed.append(w)
    first = toks[0]["t"]
    if gap and not first.startswith(("I ", "I'", "MC")) and not first.isupper():
        toks[0]["t"] = first[0].lower() + first[1:]
    toks = [tok(random.choice(ADLIBS) + ",", "adlib") for _ in range(gap)] + toks
    toks[0]["t"] = toks[0]["t"][0].upper() + toks[0]["t"][1:]
    return {"tokens": toks, "end": end, "family": fam, "whack": end_from_whack,
            "whack_rhymes": n_whack}


def hook_line(lead, words):
    """A hook line built only from the hook words, padded to exactly 12 syllables."""
    toks = [tok(t + " ", "text") for t in lead]
    while True:
        for w in words:
            if sum(t["syl"] for t in toks) + syl(w) <= SYLLABLES_PER_BAR:
                toks.append(tok(w.upper() + "! ", "end", "hook"))
        gap = SYLLABLES_PER_BAR - sum(t["syl"] for t in toks)
        if gap < min(syl(w) for w in words):
            break
    toks += [tok("yeah!", "adlib") for _ in range(gap)]  # noqa
    return {"tokens": toks, "end": words[0], "family": "hook", "whack": True, "whack_rhymes": 0}


def build_verse(words, file_words):
    """Turns one whack() result into a verse. Everything comes from whack()."""
    n = len(words)
    bars = max(4, min(16, 2 * ((n + 6) // 12) + 2))
    bpm = 70 + n  # 71..170
    sponsor = sum(w in SPONSORS for w in words)
    pain = sum(w in SUFFERING for w in words)
    mood = "FLEXING" if sponsor > pain else "CRYING AT 3AM"
    counts = Counter(file_words).most_common(2)
    hook_word, hook_count = counts[0]
    hook_word_2 = counts[-1][0]

    feed = list(words)
    unused = list(dict.fromkeys(words))  # end words: whack() output in order, no repeats
    lines, used = [], Counter()
    for _ in range(bars // 2):
        first = unused.pop(0) if unused else random.choice(words)
        fam = FAMILY_OF[first]
        partner = next((w for w in unused if FAMILY_OF[w] == fam), None)
        if partner:
            unused.remove(partner)
        second = partner or random.choice([w for w in FAMILIES[fam][1] if w != first])
        for end, from_whack in ((first, True), (second, bool(partner))):
            templates = TEMPLATES[mood]
            lines.append(build_line(templates, end, from_whack, words, feed, used))

    hook = [hook_line([], [hook_word, hook_word_2]),
            hook_line(["Everybody say"], [hook_word])]
    whack_rhymes = sum(l["whack_rhymes"] for l in lines) + sum(
        l["whack"] for l in lines[1::2])
    return {
        "words": words, "count": n, "bars": bars, "bpm": bpm, "mood": mood,
        "hook": hook_word, "hook_count": hook_count, "lines": lines + hook + hook,
        "flow": FLOW, "true_rhymes": whack_rhymes,
        "score": whack_rhymes * 10 + len(set(words)) + hook_count,
    }


def spit(mc_name):
    words = whack()
    file_words = Path("whack").read_text(encoding="utf-8").split()
    verse = build_verse(words, file_words)
    verse["mc"] = mc_name
    return verse


COLOURS = [31, 32, 33, 34, 35, 36, 91, 92, 93, 94, 95, 96]


def show(v):
    print(f"\n\033[1;97;45m 🎤 {v['mc']} \033[0m  whack() gave {v['count']} words  ·  "
          f"{v['bars']} bars  ·  {v['bpm']} BPM  ·  mood: \033[1m{v['mood']}\033[0m  ·  "
          f"hook: \033[1;93m{v['hook'].upper()}\033[0m (x{v['hook_count']} in the whack file)\n")
    print(f"  \033[2m{'1 . . . 2 . . . 3 . . . 4 . . .':<60}  syllables\033[0m")
    fams = {}
    for i, line in enumerate(v["lines"]):
        if i == v["bars"]:
            print("\n  \033[2m[HOOK x2]\033[0m")
        if i >= v["bars"] + 2:
            break
        c = fams.setdefault(line["family"], COLOURS[len(fams) % len(COLOURS)])
        parts, plain = [], 0
        for t in line["tokens"]:
            text = t["t"] + (" " if t["kind"] == "adlib" else "")
            plain += len(text)
            if t["kind"] == "end":
                parts.append(f"\033[1;4;{c}m{text}\033[0m")
            elif t["kind"] == "rhyme":
                parts.append(f"\033[1;{c}m{text}\033[0m")
            elif t["kind"] == "adlib":
                parts.append(f"\033[2;3m{text}\033[0m")
            else:
                parts.append(text)
        body = "".join(parts)
        n = sum(t["syl"] for t in line["tokens"])
        print(f"  {body}{' ' * max(1, 62 - plain)}\033[2m{n}\033[0m")
    print(f"\n  \033[2munderlined = end rhyme · bold = internal rhyme · same colour = same rhyme family"
          f"\n  every bar = 12 syllables on the 16ths, last one lands on the snare"
          f"\n  {v['true_rhymes']} whack-on-whack rhymes  ·  score {v['score']}\033[0m")


def write_player(verses, out="verse.html"):
    template = (Path(__file__).parent / "player.html").read_text(encoding="utf-8")
    Path(out).write_text(template.replace("/*VERSES*/[]", json.dumps(verses)), encoding="utf-8")
    print(f"\n🔊 Open {Path(out).resolve()} in a browser and press DROP THE BEAT.\n")


def main():
    if "--battle" in sys.argv:
        verses = [spit("MC QUACKSTAR"), spit("LIL HONK")]
        for v in verses:
            show(v)
        a, b = verses
        winner = a if a["score"] >= b["score"] else b
        print(f"\n🏆 \033[1;93m{winner['mc']} WINS\033[0m  ({a['score']} vs {b['score']})")
        for v in verses:
            v["winner"] = v is winner
    else:
        verses = [spit("MC WHACK")]
        show(verses[0])
    write_player(verses)


if __name__ == "__main__":
    main()
