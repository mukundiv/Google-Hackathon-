# Architecture

```
SIGNALS                    INTELLIGENCE        DECISION ENGINE        OUTPUT
├ Gemini Trend Scout  ─┐                      ┌ Capture Window      ┌ ACT / PASS
├ Google Trends       ─┤    Google Gemini     ├ Opportunity Score   ├ Window: N days
├ YouTube Data API    ─┼──  classify          ├ Portfolio Optimizer ├ Creator mix
├ YouTube Analytics   ─┤    synthesize        └ Learning Loop       ├ Budget split
└ Brand Inputs        ─┘    reason                                  └ Launch timing
                            structure
```

## The provider swap layer

Every external signal sits behind a `Protocol` in `app/providers/base.py` with
two implementations: a seeded one and a live one. `app/providers/registry.py`
resolves each at startup from environment variables and records the outcome,
which `GET /api/health` exposes and the console renders as a per-source badge.

```
GEMINI_MODE=mock|live      YOUTUBE_MODE=mock|live
TRENDS_MODE=mock|bigquery  ANALYTICS_MODE=mock|oauth
```

Three properties this buys, in order of how much they matter:

1. **The product is fully functional with no credentials.** The team can design
   and refine behaviour before any integration work happens.
2. **Failure degrades instead of breaking.** A live provider that cannot be
   constructed, or a call that throws, falls back — first to a cached response,
   then to the seeded one. A blown quota costs fidelity, not the demo.
3. **The gap is visible.** A source that was asked to be live and is not says
   why. Nobody has to guess whether a number on screen is real.

Live SDK imports are lazy, so seeded mode has no dependency on any Google
library being installed or importable.

---

## Stage 01 — Listen (`engine/listen.py`)

Gemini searches the live web with the `google_search` tool and returns
candidate trends as structured JSON with `groundingMetadata` citations. Those
citations are carried through to the UI, both because Google's terms require it
and because a trend claim without a source is not worth acting on.

Discovery and measurement are separate jobs on purpose: the model is good at
noticing that something is happening and bad at knowing how fast, and the
time-series data is the reverse.

**Opportunity strength** ranks candidates. An earlier version ranked by the
longest capture window, which promoted trends nobody had noticed yet — a trend
with no momentum has all the runway in the world. Strength combines current
momentum, creator supply and window adequacy, where past about a fortnight
extra runway stops being worth anything.

---

## Stage 02 — Predict (`engine/predict.py`, `engine/momentum_model.py`)

```
capture window = time-to-live − activation lead time
```

Momentum is fitted to

```
m(t) = L / (1 + e^(−k(t − t0))) · e^(−max(0, t − tp) / τ)
tp    = t0 + logit(0.85) / k
```

Three design decisions carry this stage:

**The decay onset `tp` is derived, not fitted.** An earlier version made it a
free parameter and the fit was degenerate: for a trend that has not peaked, the
future peak is not in the data, so the optimiser could place it anywhere and
still match the observed rise — r² of 0.98 with the peak fifty days out of
position. Deriving it from the rise removes that freedom.

**The decay constant `τ` is observable only after the peak.** Past the peak the
data determines it; before the peak it comes from a category prior and the fit
may only move it inside a bounded band. With only a few days of observed
decline the measured value is shrunk toward the prior in proportion to how much
decline has actually been seen — nine days of Strava Wrapped data overshot τ by
25% unshrunk, which alone flipped a PASS into a MARGINAL. Every result reports
which regime produced it.

**The fit is weighted, in two passes.** Measurement noise grows with the
momentum level, so equal weighting lets a long low-signal tail outvote the part
of the curve that determines where it saturates. Deriving those weights from
the *observed* values then biases the result — a point that happened to land
high gets a larger sigma and is trusted less, so upward noise is systematically
discounted and the whole curve sags. The second pass recomputes the weights
from the first pass's fitted values, which carry no noise of their own. That
was worth about a day of peak-position accuracy.

Time-to-live is searched forward from the peak, not from today. A trend on its
way up is *supposed* to sit below 40% of a peak it has not reached yet;
short-circuiting on that rejected exactly the early opportunities the engine
exists to find.

Activation lead time comes from the brand's own campaign history, which is what
makes the verdict brand-specific rather than a property of the trend.

---

## Stage 03 — Match (`engine/match.py`)

Five signals, each 0–100, weighted into a composite the learning loop can
revise.

| Signal | How it is computed | Provenance |
|---|---|---|
| Content Fit | Cosine similarity, trend text against the creator's catalogue. Gemini embeddings live, TF-IDF seeded. | measured |
| Audience Fit | Share of audience inside the brief's target segments. | **verified** when the owner connected their channel, **estimated** otherwise |
| Brand Fit | Gemini reasoning over values, positioning and tone. Raises a brand-safety flag. | estimated |
| Momentum | The creator's trend-adjacent content against *their own* baseline. | measured |
| Proven Performance | Delivered results for this brand. Falls back to an engagement-rate prior, flagged as a guess. | measured / estimated |

Both fit signals are compressed rather than linear. Cosine similarity between a
short trend description and a long catalogue falls away steeply, and a linear
map turned a creator with genuine adjacent content into a near-zero, leaving no
usable gradient across the middle of the pool.

Every signal returns `score + rationale + evidence`. A number a brand cannot
interrogate is not decision intelligence.

---

## Stage 04 — Optimize (`engine/optimize.py`)

Maximise, subject to budget and portfolio size:

```
Σ opportunity_score · x  +  coverage(S)  −  overlap(S)
```

Coverage is submodular — the second creator in a segment adds less than the
first — and is linearised as a per-segment saturation variable. Overlap needs
the product of two selection variables, linearised the standard way. Solved as
a MILP with CBC; a submodular greedy stands in if no solver is available.

**Overlap is a duplication rate, not a cosine.** Cosine compares the *shape* of
two audiences, and since nearly every creator in a running niche skews the same
way it reported ~90% overlap for every possible pair, which made the penalty
uninformative. What a media planner wants is the share of the smaller audience
the larger one already reaches. Assuming independence within a segment, the
expected duplicated audience is `Σ_s (r_is · r_ks / P_s)`.

The metrics reported back are computed exactly, including a Sainsbury-style
deduplicated reach the MILP cannot express. Optimising a surrogate and
reporting the true number is deliberate.

Creator cost models a real partnership package — several assets plus usage
rights and exclusivity — not a single video, because a single-video rate card
left the budget 60% unspent and the optimiser with nothing to trade.

---

## Stage 05 — Learn (`engine/learn.py`)

A ridge regression of each campaign's signal profile against what it actually
delivered, blended with the baseline in proportion to the evidence available.
Eight campaigns should move the model, not rewrite it, so the fit carries
`n / (n + 8)` of the weight. Fewer than three campaigns changes nothing.

The loop also learns the brand's activation lead time, which feeds straight
back into Stage 02 — past campaigns teach the engine how fast this brand can
actually move.

---

## Data model

Audiences are vectors over `gender:age:geo:interest` segments. That single
choice is what lets audience fit, coverage, overlap and deduplicated reach all
be computed from the same structure, and it is the shape YouTube Analytics
returns for a connected channel.

## Persistence

SQLite via SQLModel, holding three things: learned weight versions, campaign
results observed at runtime, and the live-provider response cache. The seeded
world is generated deterministically by `scripts/generate_seed.py` and read
from JSON.
