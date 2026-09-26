# Setup

The console runs with **no credentials at all**. Everything below is optional
and switches on one source at a time, so you can integrate in whatever order
suits you and demo at any point in between.

A source set to live without its credential falls back to seeded data and
reports why on `GET /api/health`, which the console renders as a per-source
badge. Nothing breaks mid-demo because a key is missing or a quota ran out.

```bash
cp .env.example .env     # then fill in only what you need
```

---

## Phase 1 — Gemini (~30 minutes, free tier)

Unlocks live brand-fit reasoning, sentiment classification and the written
recommendation.

1. Go to <https://aistudio.google.com/apikey>.
2. Sign in and click **Create API key**. Pick an existing Google Cloud project
   or let it make one.
3. Copy the key into `.env`:
   ```
   GEMINI_MODE=live
   GEMINI_API_KEY=your-key-here
   ```
4. Restart the API. The Gemini badge in the console header turns green.

### Phase 1b — Grounding with Google Search (~15 minutes, paid tier)

This is what makes the Trend Scout search the live web instead of returning
seeded trends. It requires the paid tier: **$35 per 1,000 grounded queries**.

1. In Google AI Studio, open **Billing** and enable a paid plan on the project.
2. No config change is needed — `GEMINI_MODE=live` already uses the
   `google_search` tool for scouting.

Google's terms require that you display the grounding citations returned with
any grounded answer. The console already does this: every trend card carries a
sources panel. Do not strip it.

---

## Phase 2 — YouTube Data API v3 (~45 minutes, free)

Unlocks live creator discovery, real channel and video statistics, real
comments for sentiment, and real topic supply.

1. Open <https://console.cloud.google.com/>, create or pick a project.
2. **APIs & Services → Library**, search **YouTube Data API v3**, click **Enable**.
3. **APIs & Services → Credentials → Create credentials → API key**.
4. Restrict the key to the YouTube Data API (recommended, not required).
5. Add to `.env`:
   ```
   YOUTUBE_MODE=live
   YOUTUBE_API_KEY=your-key-here
   ```

**Mind the quota.** The daily allowance is 10,000 units. `search.list` costs
**100 units per call**; `channels.list` and `videos.list` cost 1. The provider
caches search results for 24 hours and channel data for 24 hours precisely
because of this — roughly 60–80 searches per day is the real ceiling. If you
exhaust it, the engine serves the last cached response rather than failing.

---

## Phase 3 — BigQuery Trends (~2 hours, free tier covers it)

Unlocks real Google Trends momentum from Google's own public dataset.

1. In the same Cloud project, **enable billing** (the free tier covers these
   queries; the card is a prerequisite, not a cost).
2. **APIs & Services → Library → BigQuery API → Enable**.
3. Authenticate locally:
   ```bash
   gcloud auth application-default login
   ```
4. Add to `.env`:
   ```
   TRENDS_MODE=bigquery
   GCP_PROJECT_ID=your-project-id
   ```

**Know what this dataset is.** `bigquery-public-data.google_trends` holds the
**top 25 terms and top 25 rising terms per DMA per week** — not arbitrary query
volume. Niche phrases like "social running club" usually are not in it. When a
term is not covered the provider returns nothing rather than inventing a curve,
and the engine falls back to YouTube publishing velocity.

There is no open Google Trends API. Google announced an official one in July
2025; as of 2026 it is still alpha and approval-only. If you want to try for
access, apply through the Google Trends API page — but do not plan the demo
around it landing.

---

## Phase 4 — YouTube Analytics via OAuth (~4–6 hours, free)

Unlocks **verified** audience demographics for channels whose owner connects
them. This is the only way to get real demographic data, for anyone.

1. **APIs & Services → Library → YouTube Analytics API → Enable**.
2. **OAuth consent screen** → External. Fill in app name and support email.
   Add these scopes:
   - `https://www.googleapis.com/auth/yt-analytics.readonly`
   - `https://www.googleapis.com/auth/youtube.readonly`
3. Add the Google accounts that will connect channels as **Test users**.
4. **Credentials → Create credentials → OAuth client ID → Desktop app**.
   Download the JSON.
5. Add to `.env`:
   ```
   ANALYTICS_MODE=oauth
   GOOGLE_OAUTH_CLIENT_SECRETS=/absolute/path/to/client_secret.json
   ```
6. Connect a channel — run this as the person who owns it:
   ```bash
   cd backend && python scripts/connect_channel.py
   ```
   It opens a consent screen and writes a token to `backend/.tokens/`.

**The limits are worth knowing before you promise anything.** An unverified app
is capped at **100 test users**, which is ample for a demo. Going beyond that
needs Google verification, which takes weeks and requires a privacy policy and
a domain. And no amount of verification gets you analytics for a channel whose
owner has not connected it — that boundary is the point, not an obstacle.

---

## Verifying

```bash
curl -s localhost:8000/api/health | python -m json.tool
```

Each source reports `requested`, `active`, `live` and, when they differ, the
reason. The console header shows the same thing as badges, so during a demo you
always know whether a number on screen came from a Google API or the seeded
world.

## Regenerating the seeded world

```bash
cd backend && python scripts/generate_seed.py
```

Rebuilds trends, creators and campaign history deterministically. Edit
`scripts/_creators.py`, `scripts/_brand.py` or the trend specs in
`scripts/generate_seed.py` to change the scenario.
