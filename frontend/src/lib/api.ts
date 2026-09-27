/** Typed client for the engine API.
 *
 * The console also ships as a standalone page with no backend behind it. When
 * a snapshot of real engine output is present on `window.__DEMO_DATA__`, every
 * call below resolves from that instead of fetching, so the hosted demo is the
 * same console rather than a separate mock of it.
 */

const BASE = import.meta.env.VITE_API_BASE ?? "/api";

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body ?? {}),
  });
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json();
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json();
}

// ---- types -------------------------------------------------------------
export type Verdict = "ACT" | "MARGINAL" | "PASS";
export type Provenance = "verified" | "measured" | "estimated";

export interface ProviderState {
  requested: string;
  active: string;
  live: boolean;
  detail: string;
}

export interface Health {
  status: string;
  any_live: boolean;
  providers: Record<string, ProviderState>;
  weights_version: string;
  activation_lead_days: number;
  campaigns_in_ledger: number;
}

export interface Citation {
  title: string;
  url: string;
  snippet: string;
  publisher: string;
}

export interface Trend {
  id: string;
  name: string;
  description: string;
  why_now: string;
  category: string;
  query_terms: string[];
  citations: Citation[];
  source: string;
  seasonal: boolean;
}

export interface CaptureWindow {
  trend_id: string;
  trend_name: string;
  stage: string;
  current_momentum: number;
  peak_momentum: number;
  relevance_threshold: number;
  opportunity_remaining_pct: number;
  ttl_days: number;
  ttl_low_days: number;
  ttl_high_days: number;
  activation_lead_days: number;
  capture_window_days: number;
  verdict: Verdict;
  launch_within_hours: number | null;
  confidence: number;
  fit_quality: number;
  method: string;
  rationale: string;
}

export interface MomentumPoint {
  day: string;
  value: number;
}

export interface Opportunity {
  trend: Trend;
  window: CaptureWindow;
  creator_supply_index: number;
  creator_supply_note: string;
  strength: number;
  search_momentum?: MomentumPoint[];
  platform_momentum?: MomentumPoint[];
}

export interface SignalScore {
  name: string;
  label: string;
  score: number;
  weight: number;
  provenance: Provenance;
  confidence: number;
  rationale: string;
  evidence: string[];
}

export interface CreatorScore {
  creator_id: string;
  creator_name: string;
  trend_id: string;
  composite: number;
  signals: SignalScore[];
  sentiment_positive_pct: number | null;
  brand_safety_flag: boolean;
  brand_safety_note: string;
  subscribers: number;
  estimated_cost_usd: number;
  rank: number;
  rank_by_reach: number;
  tier: string;
  headline: string;
  archetype?: string;
  handle?: string;
  avg_views?: number;
  reach_relevance_delta?: number;
  thumbnail_url?: string | null;
  top_videos?: {
    id: string;
    title: string;
    views: number;
    published_at: string;
    duration_seconds: number;
    thumbnail_url?: string | null;
  }[];
}

export interface PortfolioMember {
  creator_id: string;
  creator_name: string;
  archetype: string;
  subscribers: number;
  opportunity_score: number;
  cost_usd: number;
  marginal_coverage: number;
}

export interface Portfolio {
  label: string;
  strategy: string;
  members: PortfolioMember[];
  total_cost_usd: number;
  budget_usd: number;
  avg_opportunity_score: number;
  coverage_pct: number;
  overlap_pct: number;
  gross_reach: number;
  deduplicated_reach: number;
  solver: string;
  notes: string[];
}

export interface ExcludedTopPick {
  creator_id: string;
  creator_name: string;
  rank: number;
  composite: number;
  cost_usd: number;
  budget_share_pct: number;
  overlap_with_mix_pct: number;
  reason: string;
}

export interface PortfolioComparison {
  naive: Portfolio;
  optimized: Portfolio;
  overlap_reduction_pts: number;
  coverage_gain_pts: number;
  incremental_reach: number;
  verdict: string;
  /** Step-4 rank by creator id, so the mix reads as the same ranked list. */
  ranks?: Record<string, number>;
  /** Highly ranked creators the optimiser did not buy, and why. */
  excluded_top_picks?: ExcludedTopPick[];
}

export interface Brief {
  brand_id: string;
  brand_name: string;
  product: string;
  objective: string;
  audience: {
    age_min: number;
    age_max: number;
    genders: string[];
    geos: string[];
    interests: string[];
  };
  budget_usd: number;
  market: string;
  niche: string;
  constraints: string[];
  max_creators: number;
  min_creators: number;
}

export interface CampaignOutcome {
  reach: number;
  views: number;
  engagement_rate: number;
  sentiment_positive_pct: number;
  consideration_lift_pct: number;
  performance_index: number;
}

export interface PastCampaign {
  id: string;
  name: string;
  product: string;
  trend_name: string;
  trend_category: string;
  launched_at: string;
  objective: string;
  audience_summary: string;
  spend_usd: number;
  activation_lead_days: number;
  predicted: CampaignOutcome;
  actual: CampaignOutcome;
  portfolio_overlap_pct: number;
  learnings: string[];
}

export interface BrandPortal {
  brand: {
    id: string;
    name: string;
    industry: string;
    values: string[];
    positioning: string;
    avg_activation_lead_days: number;
    brand_safety_requirements: string[];
  };
  campaigns: PastCampaign[];
  suggested_brief: Brief;
  insights: {
    campaigns_run: number;
    total_spend_usd: number;
    mean_performance_index: number;
    mean_prediction_error: number;
    activation_lead_days: {
      all_time: number;
      recent: number;
      fastest: number;
      learned: number;
    };
    overlap_vs_performance_correlation: number;
    overlap_finding: string;
    best_archetypes: { archetype: string; mean_index: number; campaigns: number }[];
    best_trend_categories: { category: string; mean_index: number; campaigns: number }[];
  };
}

export interface CalibrationEntry {
  signal: string;
  label: string;
  mean_abs_error: number;
  bias: number;
  correlation_with_outcome: number;
  samples: number;
  weight_before: number;
  weight_after: number;
}

export interface LearningState {
  current: {
    version: string;
    weights: Record<string, number>;
    trained_on_campaigns: number;
    method: string;
    note: string;
  };
  history: { version: string; weights: Record<string, number>; note: string }[];
  calibration: CalibrationEntry[];
  prediction_error_trend: {
    campaign_id: string;
    name: string;
    launched_at: string;
    predicted: number;
    actual: number;
    error: number;
    abs_error: number;
  }[];
  activation_lead_days: number;
  campaigns_learned_from: number;
  summary: string;
  applied_weights: Record<string, number>;
  applied_version: string;
  pending_change: boolean;
}

export interface FullRun {
  brief: Brief;
  recommendation: string;
  activation_lead_days: number;
  opportunities: Opportunity[];
  chosen: Opportunity;
  top_creators: CreatorScore[];
  portfolio: PortfolioComparison;
}

// ---- static snapshot ---------------------------------------------------
export interface AskAnswer {
  text: string;
  citations: { title: string; url: string; publisher: string; snippet: string }[];
  searched: boolean;
  source: string;
  suggestions: string[];
}

export interface DemoSnapshot {
  ask?: { suggestions: string[]; answers: Record<string, AskAnswer> };
  health: Health;
  brand: BrandPortal;
  scout: { brief: Brief; activation_lead_days: number; opportunities: Opportunity[] };
  learning: LearningState;
  learningAfter: LearningState;
  learningApplied: LearningState;
  capture: Record<string, { trend: Trend; window: CaptureWindow; momentum: MomentumPoint[]; projection: MomentumPoint[] }>;
  scores: Record<string, ScoresResponse>;
  portfolio: Record<string, PortfolioComparison>;
  scoresRelearned: Record<string, ScoresResponse>;
  portfolioRelearned: Record<string, PortfolioComparison>;
  meta: { captured_from: string; trends: number; creators: number; note: string };
}

export interface ScoresResponse {
  trend: Trend;
  weights_version: string;
  weights: Record<string, number>;
  scores: CreatorScore[];
}

declare global {
  interface Window {
    __DEMO_DATA__?: DemoSnapshot;
  }
}

const snapshot: DemoSnapshot | undefined =
  typeof window !== "undefined" ? window.__DEMO_DATA__ : undefined;

/** True when the page is running as a frozen snapshot with no API behind it. */
export const isStaticDemo = Boolean(snapshot);

/** A compact picture of the run currently on screen, for the deployment that
 *  has no engine of its own. Trimmed hard: the full snapshot is ~2 MB and the
 *  question has to fit in the prompt beside it. */
function askContext(trendId?: string): Record<string, unknown> | undefined {
  if (!snapshot) return undefined;
  const id =
    trendId ??
    snapshot.scout.opportunities.find((o) => o.window.verdict === "ACT")?.trend.id ??
    snapshot.scout.opportunities[0]?.trend.id;
  if (!id) return undefined;

  const opportunity = snapshot.scout.opportunities.find((o) => o.trend.id === id);
  const scores = snapshot.scores[id]?.scores ?? [];
  const portfolio = snapshot.portfolio[id];

  return {
    brand: snapshot.scout.brief.brand_name,
    product: snapshot.scout.brief.product,
    budget_usd: snapshot.scout.brief.budget_usd,
    activation_lead_days: snapshot.scout.activation_lead_days,
    trend: opportunity && {
      name: opportunity.trend.name,
      what_it_is: opportunity.trend.description,
      verdict: opportunity.window.verdict,
      stage: opportunity.window.stage,
      ttl_days: opportunity.window.ttl_days,
      capture_window_days: opportunity.window.capture_window_days,
      rationale: opportunity.window.rationale,
    },
    rejected_trends: snapshot.scout.opportunities
      .filter((o) => o.window.verdict === "PASS")
      .map((o) => ({ name: o.trend.name, window_days: o.window.capture_window_days })),
    creators: scores.slice(0, 6).map((s) => ({
      name: s.creator_name,
      composite: s.composite,
      rank: s.rank,
      rank_by_reach: s.rank_by_reach,
      subscribers: s.subscribers,
      cost_usd: s.estimated_cost_usd,
      brand_safety_flag: s.brand_safety_flag,
      brand_safety_note: s.brand_safety_note,
      signals: s.signals.map((sig) => ({ label: sig.label, score: sig.score, why: sig.rationale })),
    })),
    portfolio: portfolio && {
      size: portfolio.optimized.members.length,
      spend: portfolio.optimized.total_cost_usd,
      members: portfolio.optimized.members.map((m) => m.creator_name),
      overlap_pct: portfolio.optimized.overlap_pct,
      naive_overlap_pct: portfolio.naive.overlap_pct,
      people_reached: portfolio.optimized.deduplicated_reach,
    },
    learning: snapshot.learning.summary,
  };
}

/** Suggested questions for the Ask panel, from the snapshot where it has them. */
export const askSuggestions = (): string[] =>
  snapshot?.ask?.suggestions ?? [
    "Why is this creator ranked first?",
    "Which creators should we avoid, and why?",
    "Why are we skipping Strava Wrapped?",
    "What's in the news about run clubs right now?",
  ];

/** Where the Learning page has got to. The snapshot carries the state before
 *  feedback, after feedback, and after the new weights are adopted, so the
 *  loop stays interactive without a backend to post to. */
type LearningPhase = "base" | "observed" | "applied";
let learningPhase: LearningPhase = "base";

const settle = <T,>(value: T): Promise<T> =>
  new Promise((resolve) => setTimeout(() => resolve(value), 120));

function staticLearning(): LearningState {
  const s = snapshot!;
  if (learningPhase === "applied") return s.learningApplied;
  if (learningPhase === "observed") return s.learningAfter;
  return s.learning;
}

/** Once the learned weights are adopted, scoring and the portfolio change with
 *  them — showing the weights move without the consequence would be the least
 *  interesting half of the story. */
const relearned = () => learningPhase === "applied";

function missingTrend(trendId: string): never {
  throw new Error(`No snapshot data for trend "${trendId}"`);
}

/** Normalised so "Why is Kofi ranked first?" and "why is kofi ranked first"
 *  reach the same saved answer. */
function askKey(question: string): string {
  return question.toLowerCase().replace(/[^a-z0-9 ]/g, "").replace(/\s+/g, " ").trim();
}

/** Ask always tries a real endpoint first.
 *
 * It exists locally (FastAPI) and on the deployed site (a serverless
 * function), and 404s inside the published artifact — so one build behaves
 * correctly in all three places without being told which it is in. Only when
 * there is no endpoint does it fall back to the saved answers, and a question
 * with no saved answer says so rather than inventing one.
 */
async function askAnywhere(question: string, trendId?: string): Promise<AskAnswer> {
  // A page opened straight from disk has no origin to call, and probing anyway
  // just prints a CORS failure into the console of whoever is looking.
  const canReachEndpoint =
    typeof window === "undefined" || window.location.protocol !== "file:";

  try {
    if (!canReachEndpoint) throw new Error("no endpoint on file://");
    const res = await fetch(`${BASE}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      // `context` is only read by the serverless deployment, which has no
      // engine behind it and needs the run described to it. The local API
      // builds its own from the live engine and ignores this.
      body: JSON.stringify({ question, trend_id: trendId, context: askContext(trendId) }),
    });
    if (res.ok) return (await res.json()) as AskAnswer;
  } catch {
    // no endpoint here — fall through to the saved answers
  }

  const baked = snapshot?.ask;
  const hit = baked?.answers[askKey(question)];
  if (hit) return { ...hit, source: "saved" };
  return {
    text:
      "That one is not in the saved answers for this demo. Run the project " +
      "locally with a Gemini key and the same box answers live, searching the " +
      "web where it needs to.",
    citations: [],
    searched: false,
    source: "unavailable",
    suggestions: baked?.suggestions ?? [],
  };
}

const staticApi = {
  health: () => settle(snapshot!.health),
  brand: () => settle(snapshot!.brand),
  scout: (_brief?: Brief, _limit = 8) => settle(snapshot!.scout),
  capture: (trendId: string) =>
    settle(snapshot!.capture[trendId] ?? missingTrend(trendId)),
  scores: (trendId: string, _brief?: Brief) => {
    const source = relearned() ? snapshot!.scoresRelearned : snapshot!.scores;
    return settle(source[trendId] ?? missingTrend(trendId));
  },
  portfolio: (trendId: string, _brief?: Brief, _excludeFlagged = true) => {
    const source = relearned() ? snapshot!.portfolioRelearned : snapshot!.portfolio;
    return settle(source[trendId] ?? missingTrend(trendId));
  },
  run: (trendId?: string) => {
    const s = snapshot!;
    const chosen =
      s.scout.opportunities.find((o) => o.trend.id === trendId) ??
      s.scout.opportunities.find((o) => o.window.verdict === "ACT") ??
      s.scout.opportunities[0];
    const scores = (relearned() ? s.scoresRelearned : s.scores)[chosen.trend.id];
    return settle<FullRun>({
      brief: s.scout.brief,
      recommendation: s.meta.note,
      activation_lead_days: s.scout.activation_lead_days,
      opportunities: s.scout.opportunities,
      chosen,
      top_creators: scores.scores.slice(0, 10),
      portfolio: (relearned() ? s.portfolioRelearned : s.portfolio)[chosen.trend.id],
    });
  },
  learning: () => settle(staticLearning()),
  observe: (_payload: unknown) => {
    learningPhase = "observed";
    return settle({ ok: true, state: staticLearning() });
  },
  applyLearning: () => {
    learningPhase = "applied";
    return settle({ ok: true });
  },
  resetLearning: () => {
    learningPhase = "base";
    return settle({ ok: true });
  },
  ask: askAnywhere,
};

// ---- endpoints ---------------------------------------------------------
const liveApi = {
  health: () => get<Health>("/health"),
  brand: () => get<BrandPortal>("/brand"),
  scout: (brief?: Brief, limit = 8) =>
    post<{ brief: Brief; activation_lead_days: number; opportunities: Opportunity[] }>(
      "/scout",
      { brief, limit },
    ),
  capture: (trendId: string) =>
    get<{
      trend: Trend;
      window: CaptureWindow;
      momentum: MomentumPoint[];
      projection: MomentumPoint[];
    }>(`/capture/${trendId}`),
  scores: (trendId: string, brief?: Brief) =>
    post<ScoresResponse>("/creators/score", { trend_id: trendId, brief }),
  portfolio: (trendId: string, brief?: Brief, excludeFlagged = true) =>
    post<PortfolioComparison>("/portfolio", {
      trend_id: trendId,
      brief,
      exclude_flagged: excludeFlagged,
    }),
  run: (trendId?: string, brief?: Brief) => post<FullRun>("/run", { trend_id: trendId, brief }),
  learning: () => get<LearningState>("/learning"),
  observe: (payload: unknown) =>
    post<{ ok: boolean; state: LearningState }>("/learning/observe", payload),
  applyLearning: () => post<{ ok: boolean }>("/learning/apply"),
  resetLearning: () => post<{ ok: boolean }>("/learning/reset"),
  ask: askAnywhere,
};

export const api = (snapshot ? staticApi : liveApi) as typeof liveApi;
