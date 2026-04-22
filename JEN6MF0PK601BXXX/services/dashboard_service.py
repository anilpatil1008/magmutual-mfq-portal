from __future__ import annotations

from repositories.claim_repository import get_dashboard_metrics, get_claim_queue


class DashboardService:
    def get_metrics(self):
        return get_dashboard_metrics()

    def get_queue(self, search_text: str = "", status_filter=None, priority_filter=None, confidence_band: str = "All"):
        return get_claim_queue(search_text, status_filter, priority_filter, confidence_band)
