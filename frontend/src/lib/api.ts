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

export interface PortfolioComparison {
  naive: Portfolio;
  optimized: Portfolio;
  overlap_reduction_pts: number;
  coverage_gain_pts: number;
  incremental_reach: number;
  verdict: string;
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
export interface DemoSnapshot {
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
};

export const api = (snapshot ? staticApi : liveApi) as typeof liveApi;
