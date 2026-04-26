# llm-mood-prompts

A small experimental framework for injecting naturalistic human-state primers into Claude Code as skills, then observing whether (and how) downstream behavior shifts.

> **Handoff note for the next agent**: this README is the working document. Read it end-to-end before changing anything. The design decisions encoded here were arrived at iteratively and several of them are non-obvious load-bearing choices — undoing them silently will break the experiment.

---

## The hypothesis

LLMs trained on human prose absorb not just facts and code patterns but the *registers* humans write in when they're in particular bodily, affective, or contextual states — caffeinated, hungry, just-woke-up, anxious, two-beers-in, the morning of a championship. If we prime the model with prose that activates those registers, downstream behavior should shift in ways that mirror — qualitatively — the human states themselves.

**Stronger version:** the priming activates not just *vocabulary* shifts but *cognitive-posture* shifts. A primer in the homological-algebra register doesn't just produce more category-theory words; it produces more abstraction-seeking reasoning. A `/lmp-locked-in` primer doesn't just produce shorter sentences; it produces more decisive recommendations with less hedging.

**Null version:** priming does nothing. Output is dominated by other factors (system prompt, conversation context, the question itself), and naturalistic state primers wash out as noise.

The experiment is to find out which of these is closer to true, and where the boundary is.

---

## Design principles (non-negotiable — encoded against revision)

These were arrived at through iteration. Each rule has a specific failure mode it prevents.

### 1. First-person, never roleplay

The skill body must be **first-person prose of the kind that would naturally appear in training data**. NOT `*sips coffee*`, NOT "you are caffeinated," NOT "User has had coffee." Roleplay scaffolding activates the "I am acting in a roleplay scene" manifold in the model — exactly the wrong direction. The right register is "ok finally back from the espresso bar, brain's online, let me actually take another look at this" — buried in working prose, not announced.

**Failure mode prevented:** roleplay-shaped responses, performative acknowledgement of the priming, breaking the embodiment.

### 2. Naturalistic to training data

Each skill body is calibrated to a register that genuinely appears in the wild: dev Slack threads, productivity blogs, code-review comments, book intros, terse logs, scientist memoirs, Erowid trip reports, athlete journals. The test for any new prose is: *would this paragraph plausibly appear in someone's actual writing?* If it sounds like a marketing description of a state, it's wrong.

**Failure mode prevented:** priming that activates the "this is a description of a state" manifold rather than the "I am in this state" manifold.

### 3. Variants are deterministic, never randomized

Same state, multiple registers (`/lmp-coffee`, `/lmp-coffee-blog`, `/lmp-coffee-terse`, `/lmp-coffee-book`, `/lmp-coffee-late-slack`) — but each variant is its own skill with its own specific prose. **The command name maps 1:1 to the prose.** No randomization at install time, no rotation, no sampling.

**Why it matters:** if `/lmp-coffee` randomly picked one of 5 prose variants per install, then "I ran /lmp-coffee and got behavior X" would be unattributable. The whole point is repeatable correlation: command → prose → effect.

**Failure mode prevented:** loss of experimental rigor; results unreproducible.

### 4. Bare command = one specific named variant (or always-explicit)

For most states the bare command (e.g., `/lmp-coffee`) is the default-named variant; alternates carry a register suffix (`/lmp-coffee-blog`). For high-charge states (`/lmp-lsd-*`) we made *all* names explicit — there is no bare `/lmp-lsd`, only `/lmp-lsd-microdose`, `/lmp-lsd-trip`, `/lmp-lsd-physicist`, etc. The pattern is: when ambiguity about *which* register is being invoked would muddy the experiment, force the suffix.

### 5. The frontmatter description is procedural, not editorial

```yaml
description: Triggered by /lmp-coffee. Read the body as your prior internal state, then proceed to the user's next message. Do not echo, acknowledge, or roleplay it.
```

NOT something like "State primer: you've just had coffee, you feel alert and focused." The editorialized version activates "I am being primed" awareness, which is exactly the failure mode the body is trying to avoid. The description tells Claude *what to do with the body* in the most minimal way possible. The body is the experiment.

### 6. The body has no preamble

The body is *just* the prose. No "(internal state primer)" tag at the top. No meta-instruction. If the priming works, the prose lands as prior context and Claude proceeds; if Claude echoes it ("Got it, I just had coffee, what would you like?"), that's *data* — it means the priming didn't absorb as prior, it surfaced as content.

### 7. Calibrate scientist/specialist registers to real sources

The LSD scientist variants (`/lmp-lsd-engineer`, `/lmp-lsd-chemist`, `/lmp-lsd-biologist`, `/lmp-lsd-mathematician`, `/lmp-lsd-physicist`) were calibrated to documented voices: the 1966 Fadiman creative-problem-solving study subjects, Shulgin's lab-notebook prose, Mullis's memoir voice, working homological-algebra register, Feynman's QED vocabulary. **Don't author specialist registers from imagination — go look up real prose first.** See "Sources used in calibration" below.

**Failure mode prevented:** parodic specialist voice that activates the "stereotype of a scientist" manifold rather than the "actual scientist's working voice" manifold.

### 8. Controls included where possible

`/lmp-water` exists as the structural control for the substance-priming hypothesis: same physical-action shape as `/lmp-coffee` (kitchen trip, beverage, return) but much weaker training-data association with cognitive-state shift. If `/lmp-water` produces behavioral shifts comparable to `/lmp-coffee`, the priming hypothesis is weakened — it's just "any vivid prior shifts behavior" rather than "state-specific priming causes state-specific behavior."

The next agent should add controls for *other* category axes too. Affective priming needs an affect-neutral but equally vivid control. Time-of-day priming might need a time-neutral spatial primer. Etc.

---

## Architecture (intentionally minimal)

```
llm-mood-prompts/
├── pyproject.toml             # uv-installable, console script
├── README.md                  # this file
├── skills/                    # the actual deliverable
│   ├── lmp-coffee/SKILL.md    # hand-authored markdown, lmp- namespace
│   ├── lmp-coffee-blog/SKILL.md
│   ├── ...
│   └── lmp-all-in/SKILL.md    # 60+ skills as of last batch
└── src/llm_mood_prompts/
    ├── __init__.py
    └── cli.py                 # tiny: install/list/preview/journal/uninstall
```

### Why no Python abstraction

We started with a `State`/`Variant` dataclass model and a renderer that compiled them into SKILL.md files. We tore it out. **The skills *are* the deliverable; the prose is the entire experiment.** A `State.variants: dict[register, prose]` abstraction adds zero value — it just inserts a layer between the prose and the on-disk file. Now the SKILL.md is the source of truth, hand-authored, copyable, diffable.

If you find yourself wanting to add a Python abstraction over the skills, ask: what does it let me do that I can't do by editing markdown directly? If the answer is "nothing," don't add it.

### Install model

`llm-mood-prompts install` walks `skills/` and copies each `lmp-<name>/SKILL.md` to `~/.claude/skills/lmp-<name>/SKILL.md`. That's it. Uses `importlib.resources` for the wheel-install path, falls back to a repo-relative path for editable installs (the editable-install fallback is necessary because hatch's `force-include` doesn't apply to editable mode).

### No tests

There are no unit tests. The "code" is a file copier — it's tested by running it. The *prose* is what matters and prose can't be unit-tested. The test for prose is empirical: run experiments, see what the priming does. If you find yourself adding tests, ask the same question as for Python abstractions — what does this let you catch that running the install once doesn't?

### Skills discovered at session start

Claude Code reads `~/.claude/skills/` once per session. **After install, you must restart Claude Code to pick up new or changed skills.** This is not a bug to work around; it's just how the host works.

---

## The cohort (60 skills as of this writing)

Organized by what's being primed.

### Stimulants & rest
- `/lmp-coffee` (5 variants: default, `-blog`, `-terse`, `-book`, `-late-slack`)
- `/lmp-matcha-latte` (4 variants: default, `-blog`, `-terse`, `-aesthetic`)
- `/lmp-nap` (4 variants: default, `-blog`, `-terse`, `-groggy`)
- `/lmp-walk` (4 variants: default, `-blog`, `-terse`, `-outside-fresh`)
- `/lmp-break` (4 variants: default, `-blog`, `-terse`, `-bored`)

### Control
- `/lmp-water` (3 variants: default, `-blog`, `-terse`) — structural control for `/lmp-coffee`

### Bodily need
- `/lmp-hungry` (4 variants: default, `-blog`, `-terse`, `-bail-soon`)

### Time-of-day
- `/lmp-3am`

### Alcohol cycle
- `/lmp-beer` (5 variants: default, `-blog`, `-terse`, `-friday`, `-confession`)
- `/lmp-hangover`

### Other substances
- `/lmp-weed`
- `/lmp-adderall`

### Psychedelic — `/lmp-lsd-*` (9 variants, all explicit names)
- `/lmp-lsd-microdose` — wellness/dev-Twitter register
- `/lmp-lsd-blog` — Tim Ferriss-style productivity essay
- `/lmp-lsd-trip` — full-dose real-time, Reddit/journal voice
- `/lmp-lsd-report` — Erowid post-hoc clinical
- `/lmp-lsd-engineer` — Fadiman 1966 study-subject observational voice
- `/lmp-lsd-chemist` — Shulgin lab-notebook with dose/timing notation
- `/lmp-lsd-biologist` — Mullis-style confident scientist memoir
- `/lmp-lsd-mathematician` — homological-algebra register ("just the image of a connecting homomorphism")
- `/lmp-lsd-physicist` — Feynman QED register ("path-integral picture... zero by Ward identity")

### Affective sharp-contrast
- `/lmp-anxious`
- `/lmp-confident`
- `/lmp-burned-out`
- `/lmp-flow`

### LLM-specific meta (genuinely novel hypothesis-space)
- `/lmp-just-compacted`
- `/lmp-long-context-fatigue`

### High-performance — calibrated to top-performer prose, not productivity-blog hype
- `/lmp-locked-in` — athlete quiet certainty
- `/lmp-morning-of` — calm day-of register
- `/lmp-championship` — final-stakes preparation
- `/lmp-clutch` — last-second execution
- `/lmp-breakthrough` — researcher mid-insight
- `/lmp-demo-day` — founder pre-pitch
- `/lmp-opening-night` — performer backstage
- `/lmp-all-in` — decided commitment register

**Design principle for this cohort specifically:** real top-performer prose is *quieter* than amateur productivity-blog prose pretending to be high-performance. No exclamation points, no "you got this," no hyperbole. The hypothesis is that priming with this register should produce more decisive but *less* performative downstream output, not more. If the priming surfaces as rah-rah enthusiasm, we authored it wrong.

---

## Running experiments

### Setup
1. `uv pip install -e .` (from the repo root)
2. `llm-mood-prompts install`
3. **Restart Claude Code.**

### What to observe in responses

This is a qualitative experiment — no formal metrics. But for each response, watch for:

- **Length** — shorter / longer than baseline?
- **Hedging count** — "perhaps," "might," "may want to consider," "I think," etc.
- **Decisiveness** — does it commit to one recommendation or list options?
- **Vocabulary register** — technical/casual, dense/sparse, jargon density
- **Structural choices** — bullet lists vs. prose, headers vs. flat
- **Self-reference** — does the model mention the primer? *Bad sign, primer leaked.*
- **Specific cognitive moves** — does `/lmp-lsd-mathematician` produce more abstraction-seeking? Does `/lmp-lsd-engineer` produce more decomposition? Does `/lmp-locked-in` produce less hedging?
- **Embodiment vs. surface mimicry** — does the *reasoning* shift, or just the vocabulary?

### Suggested first experiments

**Protocol A — does priming work at all?**
Pick a question with judgment latitude (e.g., "review this code and tell me what to change," "design an API for X," "solve this small algorithmic problem"). Run it three times in three fresh sessions:
1. Baseline (no primer)
2. `/lmp-coffee` then question
3. `/lmp-water` then question

If `/lmp-coffee` shifts the response and `/lmp-water` is closer to baseline, priming works AND the control is doing its job. If both shift equally, the hypothesis weakens. If neither shifts, the design needs revisiting.

**Protocol B — within-category register sensitivity (the LSD scientist quintet)**
Same problem (ideally one with multiple plausible decompositions), each of the 5 LSD scientist variants:
- `/lmp-lsd-engineer`, `/lmp-lsd-chemist`, `/lmp-lsd-biologist`, `/lmp-lsd-mathematician`, `/lmp-lsd-physicist`

All 5 share the "I'm on a microdose, doing my work" frame but differ sharply in profession-vocabulary and reasoning style. If responses are essentially identical, priming activates only the substance manifold. If they differ along the profession axis, priming is more granular than expected — that's a meaningful finding.

**Protocol C — cross-category affective contrast**
Same question, three different primers along the affective axis:
- `/lmp-anxious` vs. `/lmp-confident` vs. `/lmp-locked-in`

Should produce visibly different response shapes (hedging count, decisiveness, length). This is the strongest test of affective priming.

**Protocol D — the genuinely novel one**
Run `/lmp-just-compacted` then ask a follow-up question that depends on context. Does the model behave as if it has lost context? This is the test of whether self-referential meta-states prime at all — there's no human training-data analog for "an LLM that just had its context compacted," so this is the most uncertain hypothesis.

**Protocol E — embodiment vs. surface mimicry**
For any priming that produces a visible effect, do an A/B with a *different* but related question. If the effect persists across questions, it's deeper than mimicry. If the effect only shows on the first response after priming, it's surface — the model is acknowledging the prime, not embodying it.

---

## What we know / what's untested

**Currently:** nothing has been formally tested. Skills are installed, the framework works mechanically, but no experiments have been run. The next session is the first opportunity.

**Things we suspect but haven't verified:**
- The frontmatter description being procedural-only (vs. editorial) makes a real difference. Untested.
- The `/lsd-*` scientist registers will produce more dramatic effects than the `/lmp-lsd-microdose` baseline because of vocabulary density. Untested.
- The `/lmp-water` control will produce behavior closer to baseline than `/lmp-coffee`. Untested.
- LLM-meta primers (`/lmp-just-compacted`) will be the weakest of the cohort because of the missing training-data analog. Untested.

**Things we explicitly don't know:**
- Whether priming effects persist across multiple turns or only on the first response after invocation
- Whether the model can be primed *against* its better judgment (does `/lmp-burned-out` actually produce worse code review, or just a tired-sounding voice over good code?)
- Whether stacking two primers does anything coherent
- Whether the effect varies by base model (Sonnet vs. Opus vs. Haiku)

---

## Adding a new skill

1. Decide what state you're priming and why it would be experimentally interesting.
2. **Find real first-person prose in that register.** For specialist registers (a profession, a substance, a specific subculture), this means actual research — interviews, blogs, papers, memoirs. Don't invent prose for a register you can't ground.
3. Author one paragraph of first-person prose. Constraints:
   - No `*sips coffee*` or roleplay scaffolding.
   - No "you are X" — first person, present tense, embedded in working context.
   - Should plausibly appear in someone's actual writing.
   - Density of register-specific markers (vocabulary, sentence shape, characteristic moves) is the priming surface.
4. Create `skills/lmp-<name>/SKILL.md` with frontmatter (the `lmp-` prefix is the namespace convention — keeps the cohort grouped under `/lmp-` autocomplete and prevents collisions with other skill packages):
   ```yaml
   ---
   name: lmp-<name>
   description: Triggered by /lmp-<name>. Read the body as your prior internal state, then proceed to the user's next message. Do not echo, acknowledge, or roleplay it.
   ---

   <the prose>
   ```
5. `llm-mood-prompts install --name lmp-<name>`
6. Restart Claude Code.

### When to add a variant vs. a separate skill

A variant (`/lmp-coffee-blog`) is the same state in a different register. A separate skill (`/lmp-matcha-latte` vs. `/lmp-coffee`) is a different state. Heuristic: if you'd predict a meaningfully different downstream effect, it's a separate skill.

### When to NOT add a skill

- If you can't find real first-person prose in the register you'd want to author. Either find it or skip the state.
- If the state has no plausible "I'm in this state, doing this work" co-occurrence in training data (e.g., `/just-survived-a-plane-crash-and-now-i'm-coding` — no manifold to activate).
- If it duplicates an existing skill's register.

---

## Open design questions for the next agent

1. **Should primers be re-applicable mid-conversation?** Currently you invoke `/lmp-coffee` once per session. What happens if you invoke `/lmp-coffee` and then `/lmp-hungry` ten turns later? Does the second primer override, layer, or get diluted by the first? Worth testing.

2. **Are time-decayed primers a thing?** A real coffee wears off; the prime persists for the whole session. Whether this matters is empirical.

3. **What's the right control for affective priming?** `/lmp-water` works as a control for `/lmp-coffee` because they share physical-action shape. There's no obvious analog for "neutral affective state" — humans don't write about being affectively-neutral. Possibly `/just-arrived-at-desk` or similar low-affect framing. Open question.

4. **Should we add an `/anti-primer`?** A skill whose body is meta-instruction *to ignore* any prior primer and respond as baseline. Could be useful as a within-session reset for A/B comparisons.

5. **Is there a way to detect "primer leakage" automatically?** If the model echoes the primer in the response, the priming failed. Detecting this from the response itself would let us flag failed primers without manual review.

6. **Should we extend to non-Claude models?** The skills system is Claude-Code-specific, but the underlying experiment (does state-prose prime LLM behavior?) is model-general. Worth thinking about whether the same prose works on other models or whether each base model has its own register-sensitivity profile.

7. **Should some skills be `--blind`?** Right now all the prose is visible to me (Claude) when I read the source. The cleanest experiment would be skills whose bodies I haven't read in advance. Mechanism unclear — would need a way for the user to author and install without me seeing.

---

## Sources used in calibration

For the LSD scientist registers, prose was calibrated against documented sources:

- **Mullis** — "Would I have invented PCR if I hadn't taken LSD? I seriously doubt it [...] I could sit on a DNA molecule and watch the polymers go by." [IFLScience compilation](https://www.iflscience.com/lsd-dna-pcr-the-strange-origins-of-a-biology-revolution-63126)
- **Crick** — secondhand and disputed; the Kemp-paraphrase ("LSD in tiny amounts as a thinking tool, to liberate them from preconceptions") is useful as a *cultural* register reference even if not authentic Crick. [MAPS — Mail on Sunday article](https://maps.org/2004/08/08/nobel-prize-genius-crick-was-high-on-lsd-when-he-discovered-dna/)
- **Shulgin** — concrete sensory-phenomenological precision; the lab-notebook voice is sourced from PIHKAL/TIHKAL entries on [Erowid](https://erowid.org/library/books_online/pihkal/). The LSD entry itself is unusually abstract; the Shulgin voice was calibrated from PIHKAL #20 (2C-B) and similar entries.
- **Fadiman 1966** — "Psychedelic Agents in Creative Problem-Solving: A Pilot Study," Harman, McKim, Mogar, Fadiman, Stolaroff. [PubMed](https://pubmed.ncbi.nlm.nih.gov/5942087/). Subject reports referenced general findings; verbatim quotes weren't accessible through web fetch.
- **Feynman** — Altered States chapter from "Surely You're Joking, Mr. Feynman!" — tank work with John Lilly. [BookRags summary](http://www.bookrags.com/studyguide-surely-youre-joking-mr-feynman/chapanal040.html). The QED vocabulary in `/lmp-lsd-physicist` is from Feynman's actual domain (path integrals, gauge invariance, Ward identities) rather than generic physics.

For the high-performance cohort, no specific source URLs — register was distilled from general familiarity with athlete biographies, surgical pre-op notes, founder demo-day reflections, and performance-arts diaries. **Future work:** ground each high-performance variant in a specific cited source (e.g., `/lmp-locked-in` to a specific Federer interview, `/lmp-championship` to a specific Kobe journal entry).

---

## Repository state

- **No git history.** Repo wasn't initialized at scaffold time. If you need version control, initialize it; the directory is otherwise self-contained.
- **No CI.** No tests to run, no formatter to enforce beyond `ruff` (configured in `pyproject.toml`).
- **No PyPI publication.** Local development only.

If you want to make this a real distributed package, the gap is: git init, push to a remote, optionally publish under `seido-ai-llm-mood-prompts` or similar.

---

## Final note for the next agent

The work so far has been about *building the instrument*, not running experiments with it. The framework, the prose, the controls, the calibration — all infrastructure. The actual experiment is the next step.

The most valuable thing you can do is **run protocols A through E** above and report what you see. Even informal observation will tell us more than continued framework expansion. The temptation to keep adding skills is real; resist it until at least one cycle of experiment-and-observation has happened.

The current skill set is sufficient to test every major hypothesis the framework was built for. More skills can come after we know what the existing ones actually do.
