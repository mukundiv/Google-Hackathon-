# Demo script

Six screens, about five minutes, following the pitch deck's own argument. The
scenario is the deck's: **Momentum Athletics**, an athletic apparel brand
launching a women's running shoe to **women 18–30 in the US** on a **$250,000**
budget, for awareness and consideration.

Start the API and the console, open <http://localhost:5173>, and check the
header badges show the provider mix you intend to present.

---

### 00 · Brand Portal — *"this brand has a history, and it is the input"*

> "This is a brand that has run eight campaigns through the engine. It is not a
> blank slate, and the most important number on this page is the activation
> lead time: **nine days** from spotting an opportunity to being live. That
> number is learned from their own campaigns, and everything downstream is
> judged against it."

Point at **best creator types** and the **audience overlap finding** — the
engine has already noticed that their campaigns with more duplicated audience
performed worse. Click **Start a new campaign**.

---

### 01 · Trend Scout — *"what is emerging, and says who"*

> "Gemini searches the live web for what is actually emerging in this niche
> right now. Every trend comes back with its sources — you can click through
> and check."

Open the sources panel on **Social Running Clubs**. Then:

> "But the interesting part is that two of these are already rejected. The
> engine is not ranking trends by how hot they are. It is asking whether this
> brand can still catch them."

---

### 02 · Capture Window — *"is there still time?"*

The headline number.

> "Momentum stays above the relevance threshold for another **22 days**. Nine
> of those get eaten by the time it takes this brand to get live. That leaves a
> **13-day capture window** — and that subtraction is the whole product."

Point at the chart: grey band is time lost to their own process, green band is
what is left. Then the honesty beat:

> "Notice what it says about method. This trend has not peaked yet, so the
> decay rate is **assumed from a category prior**, not measured — because you
> cannot observe a peak that has not happened. The engine says so rather than
> handing you a confident number it did not earn."

Switch the dropdown to **Strava Wrapped**:

> "Same engine, same brand. This one has already peaked, the decay *is*
> measurable, and the window is negative. **Pass.** It would be a trap, and
> every trend dashboard on the market would have shown it as hot."

---

### 03 · Creator Score — *"who can credibly own it?"*

Lead with the scatter plot.

> "If audience size bought relevance, this would slope upward. It does not.
> The largest channel here has **2.7 million subscribers** and ranks **38th**.
> The winner has 536,000."

Expand the top creator:

> "Five signals, and every one shows its working — which videos, which numbers,
> where the data came from. And look at the audience-fit tag: this creator's
> owner connected their YouTube Analytics, so it says **verified**. Everyone
> else says **estimated**, because demographics are owner-only data and we are
> not going to pretend otherwise."

Scroll to a flagged creator:

> "This one is flagged for brand safety — before/after body framing, against
> this brand's stated requirements. It gets excluded from the portfolio until a
> human clears it."

---

### 04 · Portfolio — *"where does the money go?"*

The money shot.

> "The obvious move is to buy the highest-scoring creators. That is the left
> column. It spends the budget and it looks great — average score 85."
>
> "The optimiser refuses to do that. It **drops the single best creator** and
> accepts a lower average score, because those five top creators sell you the
> same audience five times. Same $250,000: duplicate audience falls from
> **28% to 17%**, coverage rises, and it reaches about **128,000 more distinct
> people**."

> "That is a trade a human planner would have to feel their way to. Here it is
> a constraint in a solver."

---

### 05 · Learning Loop — *"and it gets better"*

> "Results come back and the model changes. The engine has learned from eight
> campaigns that for this brand, **content fit and momentum matter more** than
> it assumed, and **brand fit and past performance matter less**."

Click **Feed back a campaign result**, then **Apply new weights**:

> "That is a live re-weighting. Go back to the creator scores and the ranking
> has moved. It also learns how fast this brand actually ships, which feeds
> straight back into the capture window — so the next opportunity is judged
> against a better estimate of their own speed."

---

## Closing line

> "Trend tools tell you what is happening. Creator platforms tell you who
> exists. Analytics tells you what happened. None of them tell you whether to
> act, who to back, or where the money goes. That is the gap, and it is the
> only thing this engine does."

---

## Questions you should expect

**"Is the trend data real?"** Gemini's web search is real and cited. Momentum
is real from the BigQuery public Trends dataset where it covers the term, and
YouTube publishing velocity otherwise. There is no open Google Trends API —
the official one is still alpha and approval-only.

**"Where do the demographics come from?"** Verified from the channel owner's
YouTube Analytics where they have connected it, inferred from public signals
otherwise, and the console labels which. That boundary is real for everyone,
including the paid vendors — they wrap the same OAuth.

**"Is the campaign history real?"** No, and it could not be: no public API
exposes what a brand paid a creator and what came back. Every platform in this
category gets that from brands uploading their own. The Brand Portal is the
surface where a real brand's data would live.

**"Why is the capture window better than just looking at a trend line?"**
Because it is brand-specific. The same trend is an ACT for a brand that ships
in six days and a PASS for one that takes forty-five. A trend line cannot tell
you that; it does not know who is asking.
