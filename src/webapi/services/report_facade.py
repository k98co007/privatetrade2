from __future__ import annotations

import logging

from report.report_service import ReportService

from webapi.models import ReportFacadeQuery


LOGGER = logging.getLogger("webapi.service.report")


class ReportFacade:
    def __init__(self, report_service: ReportService | None = None) -> None:
        self.report_service = report_service or ReportService()

    def generate_report(self, simulation_id: str, query: ReportFacadeQuery) -> dict:
        LOGGER.info(
            "report.generate.request simulation_id=%s schema_version=%s include_no_trade=%s sort_order=%s",
            simulation_id,
            query.schema_version,
            query.include_no_trade,
            query.sort_order,
        )
        try:
            report = self.report_service.generate_report(
                simulation_id=simulation_id,
                schema_version=query.schema_version,
                include_no_trade=query.include_no_trade,
                sort_order=query.sort_order,
            )
            LOGGER.info("report.generate.success simulation_id=%s", simulation_id)
            return report
        except Exception:
            LOGGER.exception("report.generate.failed simulation_id=%s", simulation_id)
            raise
