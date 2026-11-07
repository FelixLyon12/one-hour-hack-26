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
    "apital": (["capital"], ["habitual", "rapid fire, y'all"]),
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

TEMPLATES = {
    "FLEXING": [
        "Pull up to the {a} with a {b} and a {end}",
        "They call me MC {A}, I'm the king of the {end}",
        "{A} in the bag and a {b} on my {end}",
        "Sponsored by {a}, yeah I'm flexing on {end}",
        "Diamonds on my {a}, gold chain made of {end}",
        "Hands up for the {a}, hands up for the {end}",
        "Got a {a} in my {b}, call me {end}",
        "My {a} so cold it's a {end}",
        "Ten {a}s deep in a {b}, straight {end}",
        "I don't chase {a}, I just catch the {end}",
    ],
    "CRYING AT 3AM": [
        "Mama said no {a}, so I ran it on {end}",
        "{A} at 3AM, still chasing that {end}",
        "I ain't got {a}, I ain't got {end}",
        "Pass me the {a} and the {b}, it's {end}",
        "My {a} hit a {b}, now my life is {end}",
        "Ten cups of {a} and I'm still on {end}",
        "Got a {a} in my {b}, call me {end}",
        "Every time I {a}, I get a {end}",
        "Tears on my {a}, it's a {b} {end}",
        "Rubber duck, tell me why my {a} is {end}",
    ],
}


def build_verse(words, file_words):
    """Turns one whack() result into a verse. Everything comes from whack()."""
    n = len(words)
    bars = max(4, min(16, 2 * ((n + 6) // 12) + 2))
    bpm = 70 + n  # 71..170
    sponsor = sum(w in SPONSORS for w in words)
    pain = sum(w in SUFFERING for w in words)
    mood = "FLEXING" if sponsor > pain else "CRYING AT 3AM"
    hook_word, hook_count = Counter(file_words).most_common(1)[0]
    runner_up = [w for w, _ in Counter(file_words).most_common(2)]
    hook_word_2 = runner_up[-1]

    feed = list(words)
    pos = 0

    def next_word(avoid=None):
        nonlocal pos
        for _ in range(len(feed)):
            w = feed[pos % len(feed)]
            pos += 1
            if w != avoid:
                return w
        return w

    templates = TEMPLATES[mood][:]
    random.shuffle(templates)
    unused = list(dict.fromkeys(words))  # end words: whack() output in order, no repeats
    lines, true_rhymes = [], 0
    for couplet in range(bars // 2):
        first = unused.pop(0) if unused else next_word()
        fam = FAMILY_OF[first]
        partner = next((w for w in unused if FAMILY_OF[w] == fam and w != first), None)
        if partner:
            unused.remove(partner)
            true_rhymes += 1
            second, second_is_whack = partner, True
        else:
            second, second_is_whack = random.choice(FAMILIES[fam][1]), False
        for end, from_whack in ((first, True), (second, second_is_whack)):
            t = templates[len(lines) % len(templates)]
            a, b = next_word(end), next_word(end)
            pre = t.split("{end}")[0].format(a=a, b=b, A=a.upper())
            lines.append({"pre": pre[0].upper() + pre[1:], "end": end, "family": fam,
                          "whack": from_whack})

    h, h2 = hook_word.upper(), hook_word_2.upper()
    hook = [
        {"pre": f"{h} {h} {h}, ", "end": h2.lower(), "family": "hook", "whack": True},
        {"pre": f"Everybody say {h}! ({h}!) ", "end": hook_word, "family": "hook", "whack": True},
    ]
    return {
        "words": words, "count": n, "bars": bars, "bpm": bpm, "mood": mood,
        "hook": hook_word, "hook_count": hook_count, "lines": lines + hook + hook,
        "true_rhymes": true_rhymes,
        "score": true_rhymes * 10 + len(set(words)) + hook_count,
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
    fams = {}
    for i, line in enumerate(v["lines"]):
        if i == v["bars"]:
            print("\n  \033[2m[HOOK x2]\033[0m")
        if i >= v["bars"] + 2:
            break
        c = fams.setdefault(line["family"], COLOURS[len(fams) % len(COLOURS)])
        star = "★" if line["whack"] else " "
        print(f"  {line['pre']}\033[1;{c}m{line['end']}\033[0m \033[2m{star}\033[0m")
    print(f"\n  \033[2m★ = rhyme word straight out of whack()  ·  "
          f"{v['true_rhymes']} whack-on-whack rhymes  ·  score {v['score']}\033[0m")


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
