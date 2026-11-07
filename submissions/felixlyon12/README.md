# MC WHACK 🎤🦆

**By:** Felix Lyon

**Pitch:** every call to `whack()` becomes a rap verse, and then a live performance with a synth beat, a robot rapper and karaoke lyrics. You can also have two MCs battle it out with their own `whack()` calls.

## How to run it

```
python3 spit.py            # one verse
python3 spit.py --battle   # two MCs, two whack() calls, one winner
```

Each run prints the verse to the terminal, with the rhyming words colour-coded, and writes `verse.html`. Open that page in a browser and press **DROP THE BEAT**. No installs, no API keys, just Python 3 and a browser. To see the player without running anything, open `example_battle.html`.

## How `whack()` writes the song

Nothing is hand-picked. Every part of the song comes from `whack()`:

| `whack()` gives… | …which decides |
|---|---|
| **how many words** (1–100) | how many bars (4–16) and the **BPM** (71–170) |
| **the order of the words** | which words land at the end of each line. All 42 words sit in rhyme families (`whack/hack/quack/stack`, `io/overflow/demo`…), and the next line rhymes with the last one |
| **the `whack` file** | the most-repeated word in the file becomes the **HOOK** ("DUCK DUCK DUCK… Everybody say DUCK!") |
| **sponsor words vs suffering words** | the mood: **FLEXING** ("Sponsored by bloomberg, yeah I'm flexing on…") or **CRYING AT 3AM** ("Ten cups of coffee and I'm still on…") |
| **everything else** | the rest of each bar is filled with the remaining words, in order |

The battle score counts whack-on-whack rhymes, vocabulary and hook strength. If `whack()` hands you a single word, your MC raps that word for the whole verse and loses badly (see LIL HONK below).

## Screenshot

![the player](screenshot.png)

![the terminal](terminal.png)
