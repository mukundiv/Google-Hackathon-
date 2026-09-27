# Creator Opportunity Engine

Creator marketing does not have a data problem. Brands can already see what is
trending, discover thousands of creators and measure campaigns after the fact.
None of that answers the three questions that decide a campaign:

**Is there still time to act? Who should capture this? Where should the money go?**

This is a working prototype of a decision engine that answers them, built for a
Google hackathon. It runs a continuous loop over Google and YouTube signals:

| | Stage | Question | Output |
|---|---|---|---|
| **01** | Listen | What is emerging? | Trends discovered on the live web, with citations |
| **02** | Predict | Is there still time? | **Capture Window** → ACT / MARGINAL / PASS |
| **03** | Match | Who can credibly own it? | **Creator Opportunity Score**, 0–100, with evidence |
| **04** | Optimize | What is the best mix? | **Portfolio** maximising coverage per dollar |
| **05** | Learn | What improves next time? | Re-weighted model, from real outcomes |

## See it

**[Open the demo →](https://claude.ai/artifact/9yiTUctS3QZN6uGKfjQaQH)** ·
**[Plain-mode version →](https://claude.ai/artifact/N7PsdfRxPNVfDiCacYviDP)**

Two presentations of the same engine, for the team to choose between. The
second is the same data and the same charts in plain language, styled after
YouTube's own interface, with every technical figure moved behind a
*Show the working* disclosure. Build either with `npm run build:demo` or
`npm run build:demo:v2` in `frontend/`.

Both are hosted snapshots of one full run: all six screens, real charts, real
numbers, nothing to install. Every figure was computed by the engine — the
pages carry a frozen capture of the API's output rather than authored
fixtures.

## Run it

No API keys required. The console is fully functional on seeded data.

```bash
# backend
cd backend
python -m venv ../.venv && ../.venv/bin/pip install -r requirements.txt
../.venv/bin/python -m uvicorn app.main:app --port 8000

# frontend, in a second terminal
cd frontend
npm install && npm run dev
```

Open <http://localhost:5173>. Or `docker compose up` for both at once.

To go live on real Google APIs, see **[SETUP.md](SETUP.md)** — each source
switches on independently, and a source set to live without its credential
falls back to seeded data rather than breaking.

## The three ideas worth looking at

**Capture Window is arithmetic, not vibes.**

```
capture window = time-to-live − activation lead time
```

Momentum is fitted to a logistic-rise / exponential-decay curve to get
time-to-live; activation lead time is learned from the brand's own campaign
history. A trend is only an opportunity if it outlives the brand's own
Identify → Analyze → Select → Approve → Produce → Launch chain. The same trend
returns ACT for a brand that ships in six days and PASS for one that takes
forty-five — which is the Activation Gap, made operational.

The engine will not claim to measure what it cannot see. A trend that has not
peaked yet has no observable decay rate, so that comes from a declared category
prior and every result says which regime produced it.

**Reach is not relevance, and the score shows its working.**

Five signals — content fit, audience fit, brand fit, momentum, proven
performance — each carrying provenance and evidence. In the seeded scenario the
2.7M-subscriber creator ranks 38th while a 536K-subscriber run-club creator
ranks first. Audience data earned from a channel owner's analytics is labelled
`verified`; everything inferred is labelled `estimated`, and the two are never
blended into one confident-looking number.

**The optimiser declines the best creators on purpose.**

Buying the top-ranked line-up buys the same audience several times. Solved as a
mixed-integer program, the recommended portfolio drops the single
highest-scoring creator and accepts a lower average score to cut duplicate
audience from 28% to 17% — reaching about 128,000 more distinct people for the
same $250,000.

## What is real and what is seeded

Being straight about this matters more than a bigger claim.

| Signal | Status |
|---|---|
| **YouTube Data API v3** | Fully real. Public data on any channel — subscribers, views, titles, tags, comments. |
| **Gemini** | Fully real, including Grounding with Google Search for trend discovery. |
| **Google Trends** | Partly. No open API exists; the official one is still alpha and approval-only. Real momentum comes from the BigQuery public dataset, which only covers top and rising terms, so niche phrases fall back to YouTube publishing velocity. |
| **YouTube Analytics** | Owner-only, by design. Demographics require the channel owner to complete OAuth. No key buys this, and unified vendors wrap the same consent rather than removing it. The engine supports both states and labels which is which. |
| **Historical campaign results** | Seeded. No public API exposes what a brand paid a creator and what came back; every incumbent gets this from brands uploading their own. The Brand Portal is the surface where that data would live. |

## Layout

```
backend/
  app/engine/      listen · predict · match · optimize · learn
  app/providers/   one protocol per signal, mock + live implementations
  app/models/      typed domain objects
  app/routers/     HTTP surface
  scripts/         seed generation, channel OAuth connection
  tests/           63 tests over the engine maths and the API
frontend/src/
  pages/           the six console screens
  components/      charts and UI
docs/              architecture, integration timeline, demo script
```

## Tests

```bash
cd backend && ../.venv/bin/python -m pytest -q
```

They cover the parts that have to be right: that the predictor recovers the
time-to-live the seed generator encoded, that the verdict flips correctly on
activation lead time, that reach does not outrank relevance, that the optimiser
respects the budget and genuinely reduces duplicate reach, and that the
learning loop moves every signal weight toward the relationship hidden in the
ledger.

## Demo

`docs/DEMO_SCRIPT.md` walks the six screens in the order the pitch deck makes
its argument, using the deck's own scenario: an athletic apparel brand
launching a women's running shoe to women 18–30 in the US on a $250,000 budget.
