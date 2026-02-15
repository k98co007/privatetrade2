from __future__ import annotations

from datetime import date

from .constants import ERROR_CODES
from .errors import (
    ReportCalculationError,
    ReportNotFoundError,
    ReportValidationError,
    StorageError,
)
from .models import ReportWarning, SimulationMeta
from .profit_calculator import ProfitCalculator
from .report_repository import ReportRepository
from .schema import serialize_comprehensive_report, validate_schema_version
from .summary_report_generator import SummaryReportGenerator
from .trade_history_formatter import TradeHistoryFormatter


class ReportService:
    def __init__(
        self,
        repository: ReportRepository | None = None,
        profit_calculator: ProfitCalculator | None = None,
        trade_formatter: TradeHistoryFormatter | None = None,
        summary_generator: SummaryReportGenerator | None = None,
    ) -> None:
        self.repository = repository or ReportRepository()
        self.profit_calculator = profit_calculator or ProfitCalculator()
        self.trade_formatter = trade_formatter or TradeHistoryFormatter()
        self.summary_generator = summary_generator or SummaryReportGenerator()

    def generate_report(
        self,
        simulation_id: str,
        schema_version: str | None = None,
        include_no_trade: bool = True,
        from_date: date | None = None,
        to_date: date | None = None,
        sort_order: str = "asc",
    ) -> dict:
        version = validate_schema_version(schema_version)
        if not simulation_id:
            raise ReportValidationError(ERROR_CODES["E_RP_001"], "simulation_id_required")

        try:
            simulation = self.repository.read_simulation_result(simulation_id)
            if simulation is None:
                raise ReportNotFoundError(ERROR_CODES["E_RP_012"], "simulation_not_found")

            trades = self.repository.read_trade_records(
                simulation_id=simulation_id,
                include_no_trade=include_no_trade,
                from_date=from_date,
                to_date=to_date,
                sort_order=sort_order,
            )
            trade_details = self.trade_formatter.format_trade_history(
                trades=trades,
                include_no_trade=include_no_trade,
                sort_order=sort_order,
            )

            warnings: list[ReportWarning] = []
            profit_summary = self.profit_calculator.calculate_profit_summary(
                initial_seed=simulation.initial_seed,
                final_seed=simulation.final_seed,
            )
            summary = self.summary_generator.generate_summary(
                trade_details=trade_details,
                initial_seed=simulation.initial_seed,
                final_seed=simulation.final_seed,
            )
            report = self.summary_generator.build_comprehensive_report(
                meta=SimulationMeta(
                    simulation_id=simulation.simulation_id,
                    symbol=simulation.symbol,
                    strategy=simulation.strategy,
                    start_date=simulation.start_date.isoformat(),
                    end_date=simulation.end_date.isoformat(),
                ),
                profit_summary=profit_summary,
                summary=summary,
                trade_details=trade_details,
                warnings=warnings,
                schema_version=version,
            )
            return serialize_comprehensive_report(report)
        except (ReportValidationError, ReportNotFoundError, ReportCalculationError, StorageError):
            raise
        except Exception as exc:
            raise ReportCalculationError(ERROR_CODES["E_RP_005"], "report_generation_failed", cause=exc) from exc
