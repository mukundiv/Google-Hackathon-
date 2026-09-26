"""Google Trends momentum from the BigQuery public dataset.

There is no open Google Trends API. Google announced an official one in July
2025 but as of 2026 it is still alpha and approval-only, so the practical
source of *official* Google trend data is the public BigQuery dataset
`bigquery-public-data.google_trends`.

Its coverage is the thing to understand before relying on it: the tables hold
the **top 25 terms and top 25 rising terms per DMA per week**, not arbitrary
query volume. A niche phrase like "social running club" will usually not
appear at all. So this provider returns a series when the dataset genuinely
covers a term and an empty list when it does not, rather than fabricating one —
the engine then falls back to YouTube platform velocity and says so.

Costs nothing meaningful: the queries are small and the free tier covers them.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta

from app.config import Settings
from app.models.trend import MomentumPoint
from app.store import cache_get, cache_get_stale, cache_set

log = logging.getLogger(__name__)

QUERY = """
SELECT
  week,
  term,
  MIN(rank) AS best_rank
FROM `bigquery-public-data.google_trends.top_terms`
WHERE
  refresh_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
  AND week >= DATE_SUB(CURRENT_DATE(), INTERVAL @days DAY)
  AND LOWER(term) IN UNNEST(@terms)
GROUP BY week, term
ORDER BY week
"""


class BigQueryTrendsProvider:
    mode = "bigquery"

    def __init__(self, settings: Settings):
        from google.cloud import bigquery  # lazy: mock mode needs no SDK

        if not settings.gcp_project_id:
            raise RuntimeError("GCP_PROJECT_ID is not set")
        self.settings = settings
        self.client = bigquery.Client(project=settings.gcp_project_id)

    def momentum(
        self, query_terms: list[str], market: str = "US", days: int = 180
    ) -> list[MomentumPoint]:
        terms = [t.lower().strip() for t in query_terms if t.strip()]
        if not terms:
            return []

        key = f"bq:trends:{','.join(sorted(terms))}:{market}:{days}"
        cached = cache_get(key, ttl_seconds=60 * 60 * 12)
        if cached is not None:
            return [MomentumPoint.model_validate(p) for p in cached]

        try:
            from google.cloud import bigquery

            job = self.client.query(
                QUERY,
                job_config=bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ArrayQueryParameter("terms", "STRING", terms),
                        bigquery.ScalarQueryParameter("days", "INT64", days),
                    ]
                ),
            )
            rows = list(job.result())
            if not rows:
                log.info(
                    "no BigQuery Trends coverage for %s — the public dataset only "
                    "holds top/rising terms per DMA, so niche phrases are absent",
                    terms,
                )
                cache_set(key, [])
                return []

            series = _rank_to_momentum(rows, days)
            cache_set(key, [p.model_dump(mode="json") for p in series])
            return series
        except Exception:
            log.warning("BigQuery Trends query failed", exc_info=True)
            stale = cache_get_stale(key)
            return [MomentumPoint.model_validate(p) for p in stale] if stale else []


def _rank_to_momentum(rows, days: int) -> list[MomentumPoint]:
    """Turn weekly top-25 ranks into a daily 0-100 momentum series.

    The dataset gives rank, not volume, and rank 1 is the strongest — so it is
    inverted before scaling. Weekly points are held flat across their week
    rather than interpolated: pretending to daily resolution the source does
    not have would be inventing data.
    """
    by_week: dict[date, float] = {}
    for row in rows:
        week = row["week"]
        score = max(0.0, (26 - float(row["best_rank"])) / 25.0 * 100.0)
        by_week[week] = max(by_week.get(week, 0.0), score)

    if not by_week:
        return []

    weeks = sorted(by_week)
    start, end = weeks[0], date.today()
    out: list[MomentumPoint] = []
    day = start
    while day <= end and (end - day).days <= days:
        applicable = [w for w in weeks if w <= day]
        if applicable:
            out.append(MomentumPoint(day=day, value=round(by_week[applicable[-1]], 2)))
        day += timedelta(days=1)
    return out
