from __future__ import annotations

from report.report_service import ReportService

from webapi.models import ReportFacadeQuery


class ReportFacade:
    def __init__(self, report_service: ReportService | None = None) -> None:
        self.report_service = report_service or ReportService()

    def generate_report(self, simulation_id: str, query: ReportFacadeQuery) -> dict:
        return self.report_service.generate_report(
            simulation_id=simulation_id,
            schema_version=query.schema_version,
            include_no_trade=query.include_no_trade,
            sort_order=query.sort_order,
        )
