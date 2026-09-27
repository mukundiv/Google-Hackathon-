# Deploying the console

The console is a static site with one serverless function behind it. That
split is deliberate: the six screens are precomputed by the real engine, so
they load instantly and cannot fall over, while **Ask Gemini is genuinely
live** — the one thing a judge will want to poke.

**Nothing here needs a credit card.** Cloud Run is not used, because it
requires billing to be enabled on the project even to use its free tier.

---

## There is already a live link

<https://mukundiv.github.io/Google-Hackathon-/> — free, public, no account,
republished by `.github/workflows/deploy-pages.yml` on every push. Give judges
that one.

GitHub Pages serves static files only, so the Ask panel there answers from its
saved replies rather than calling Gemini. Everything below is for the other
link: the same console on a host that can run a function, which is what makes
the Ask box genuinely live. Both can exist at once.

---

## What you need

1. A **Gemini API key** — <https://aistudio.google.com/apikey>. Free tier, no
   card. On Gemini 2.5 Flash the free allowance covers roughly 1,500 grounded
   requests a day, which is far more than a judging panel will use.
2. A **Cloudflare account** — free, no card. Netlify and Vercel work the same
   way; the only difference is where the function file lives.

---

## Cloudflare Pages, start to finish

0. **Check the key first**, before wiring it into anything. One real call,
   about a minute:

   ```bash
   cd backend && python scripts/check_gemini_key.py AIza...your-key
   ```

   It prints whether the key works, whether Google Search grounding is included
   on its tier, and the citations that came back. Grounding is what the trend
   scout and the Ask panel both depend on, so if it is not available on the free
   tier you want to know now rather than after the deploy. The key is never
   printed or written anywhere.
1. Push this branch to GitHub (already done if you are reading this in the repo).
2. Go to <https://dash.cloudflare.com> → **Workers & Pages** → **Create** →
   **Pages** → **Connect to Git**, and pick this repository.
3. Set the build configuration exactly:

   | Field | Value |
   |---|---|
   | Framework preset | None |
   | Build command | `cd frontend && npm install && npm run build:deploy` |
   | Build output directory | `frontend/dist` |
   | Root directory | *(leave blank)* |

4. **Settings → Environment variables → Add variable**
   - Name `GEMINI_API_KEY`, value your key, and click **Encrypt**.
   - Optionally `GEMINI_MODEL` to override `gemini-2.5-flash`.
5. **Save and Deploy.** You get a URL like
   `creator-opportunity-engine.pages.dev`. That is the link to submit.

Cloudflare picks up `frontend/functions/api/ask.js` automatically and serves it
at `/api/ask`. The key is read server-side inside that function and never
reaches the browser — which is the whole reason the Ask box is a function
rather than a fetch from the page.

### Checking it worked

Open the site, click **Ask Gemini**, and ask something about the outside world:

> What's in the news about run clubs right now?

A live answer carries a green **Live · searched the web** badge and a list of
sources underneath. If it says **Saved answer**, the function is not being
reached — check the build output directory. If it says the key is missing, the
environment variable did not save as encrypted.

---

## What is live and what is precomputed

Worth being able to answer straight, because a judge will ask.

| Part | On the deployed site |
|---|---|
| Ask Gemini | **Live.** Real Gemini call, real Google Search grounding, real citations. |
| The six screens | Precomputed. Every number was produced by the real engine and frozen into `demo-data.json` — not authored by hand. |
| Trend scouting, scoring, optimisation | Runs live when you run the repo locally; precomputed on the deployed site. |

The pipeline is precomputed on the deployed site because it loads scipy,
scikit-learn and a MILP solver — more than a free container tier can carry
without cold starts or running out of memory. Rather than gamble on that in
front of a judge, the heavy work is done ahead of time and the interactive part
is the part that is genuinely live.

To regenerate the snapshot after changing the engine:

```bash
cd backend && python -m uvicorn app.main:app --port 8000 &
python scripts/export_demo_snapshot.py
```

---

## Running the whole engine live

Any judge who wants the full pipeline can run it in two commands. See
[SETUP.md](SETUP.md) for the API keys; none of them need a card either.

```bash
cd backend && python -m uvicorn app.main:app --port 8000
cd frontend && npm run dev
```

With `GEMINI_MODE=live` and `YOUTUBE_MODE=live` in `.env`, every screen
recomputes from live Google APIs on each request.

---

## Netlify or Vercel instead

Same idea, different location for the function:

- **Netlify** — move `frontend/functions/api/ask.js` to
  `netlify/functions/ask.js`, change the export to Netlify's handler signature,
  and add a redirect from `/api/ask`. Build command and output directory are
  unchanged.
- **Vercel** — move it to `api/ask.js` at the repo root and export a default
  handler. Vercel routes `/api/*` automatically.

## Cloud Run, once you have billing

The Dockerfile in `backend/` already serves the full live engine. When the
project has billing enabled — Cloud Run's own free tier then covers a demo at
no cost — this becomes a one-liner and every screen is live rather than
precomputed:

```bash
gcloud run deploy creator-engine --source backend --region us-central1 \
  --allow-unauthenticated --set-env-vars GEMINI_MODE=live,YOUTUBE_MODE=live \
  --set-secrets GEMINI_API_KEY=gemini-key:latest,YOUTUBE_API_KEY=youtube-key:latest
```
