# API integration timeline

What each Google integration costs in time and money, and what it actually
buys. Step-by-step instructions are in [SETUP.md](../SETUP.md).

Nothing here is a prerequisite for a working demo. Phase 0 is the whole product.

| Phase | Unlocks | Effort | Cost | Blocker risk |
|---|---|---|---|---|
| **0 — now** | Everything, on seeded data | none | free | none |
| **1 — Gemini key** | Live brand-fit reasoning, sentiment, written recommendation | ~30 min | free tier | none |
| **1b — Gemini paid tier** | Trend Scout searching the live web, with citations | +15 min | **$35 / 1,000 grounded queries** | needs billing enabled |
| **2 — YouTube Data API v3** | Real creators, channels, videos, comments, topic supply | ~45 min | free | **10,000 units/day; `search.list` costs 100** |
| **3 — BigQuery Trends** | Official Google Trends momentum | ~2 hrs | free tier covers it | dataset only holds top/rising terms |
| **4 — YouTube Analytics OAuth** | **Verified** audience demographics per connected channel | ~4–6 hrs | free | unverified app caps at 100 test users |
| **5 — post-hackathon** | Multi-platform creator analytics at scale | — | Phyllo or similar, **$1,000s/month** | commercial contract |

## Recommended order for the hackathon

**Do phases 1 and 2.** Together they take about 75 minutes, cost nothing beyond
the grounding tier, and make the two most visible claims real: Gemini genuinely
searching the web for trends, and genuinely real creators with real subscriber
counts and real comments. That is the demo.

**Do phase 4 only if someone on the team owns a YouTube channel.** Connecting
one real channel turns a slide into a proof: the console shows `verified` next
to that creator's audience data and `estimated` next to everyone else's. It is
a strong answer to the obvious question about where demographic data comes
from. If nobody owns a channel, skip it — the estimated path is already honest
and already labelled.

**Phase 3 is the lowest value for the effort.** The public dataset covers top
and rising terms per DMA, so most niche phrases return nothing. Worth doing if
you want "official Google Trends data" on the architecture slide; the YouTube
publishing-velocity fallback is more useful for the trends this product cares
about.

## Quota planning for demo day

The binding constraint is YouTube's 10,000 units/day with `search.list` at 100
units. That is roughly 60–80 distinct searches per day after caching, which is
plenty for a demo and nowhere near enough for production discovery.

Mitigations already in the code:

- search results cached 24 hours, channel data cached 24 hours
- one search per topic, not per creator
- a failed or exhausted call serves the last cached response
- the whole thing falls back to seeded data rather than erroring

**Before presenting:** run the demo once on the morning of, with live mode on.
That populates the cache, so the presentation itself costs almost no quota and
runs at seeded-mode speed.

## Known limits worth stating out loud

**There is no open Google Trends API.** Google announced one in July 2025; as of
2026 it is still alpha and approval-only. Anyone claiming a live Trends
integration is using the BigQuery public dataset, an unofficial scraper, or a
paid reseller.

**Audience demographics are owner-only.** No API key buys them. Unified creator
data platforms such as Phyllo handle the OAuth plumbing and normalise across
platforms, which is genuinely useful at scale, but they cannot bypass creator
consent either — they wrap the same flow. Their production pricing starts in
the thousands per month.

**Historical campaign performance does not exist as a public API.** Nobody
publishes what a brand paid a creator and what came back. Every platform in
this category gets it from brands uploading their own data, which is what the
Brand Portal is for.

Saying these plainly is a better answer to a judge than a claim that does not
survive a follow-up question.
