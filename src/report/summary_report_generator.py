from __future__ import annotations

from decimal import Decimal, InvalidOperation, localcontext

from .constants import (
    AMOUNT_QUANTIZER,
    AMOUNT_ROUNDING,
    DECIMAL_PRECISION,
    ERROR_CODES,
    NO_TRADE_REASON_CODES,
    RATE_QUANTIZER,
    RATE_ROUNDING,
)
from .errors import ReportCalculationError, ReportValidationError
from .models import ComprehensiveReport, ProfitSummary, ReportSummary, ReportWarning, SimulationMeta, TradeDetail


class SummaryReportGenerator:
    def generate_summary(
        self,
        trade_details: list[TradeDetail],
        initial_seed: Decimal,
        final_seed: Decimal,
    ) -> ReportSummary:
        if initial_seed is None or final_seed is None:
            raise ReportValidationError(ERROR_CODES["E_RP_001"], "seed_value_required")

        counters = self.calculate_trade_counters(trade_details)
        totals = self.calculate_profit_loss_totals(trade_details)
        win_rate = self.calculate_win_rate(counters["profit_trades"], counters["total_trades"])

        if counters["total_trades"] != counters["profit_trades"] + counters["loss_trades"] + counters["flat_trades"]:
            raise ReportCalculationError(ERROR_CODES["E_RP_005"], "trade_counter_inconsistent")

        return ReportSummary(
            total_trades=counters["total_trades"],
            profit_trades=counters["profit_trades"],
            loss_trades=counters["loss_trades"],
            flat_trades=counters["flat_trades"],
            no_trade_days=counters["no_trade_days"],
            total_profit_amount=totals["total_profit_amount"],
            total_loss_amount=totals["total_loss_amount"],
            win_rate=win_rate,
        )

    def calculate_trade_counters(self, trade_details: list[TradeDetail]) -> dict[str, int]:
        profit_trades = 0
        loss_trades = 0
        flat_trades = 0
        no_trade_days = 0

        for trade in trade_details:
            reason = str(trade.sell_reason).lower()
            is_no_trade = reason in NO_TRADE_REASON_CODES
            if is_no_trade:
                no_trade_days += 1
                continue

            if trade.net_profit > Decimal("0"):
                profit_trades += 1
            elif trade.net_profit < Decimal("0"):
                loss_trades += 1
            else:
                flat_trades += 1

        total_trades = profit_trades + loss_trades + flat_trades
        return {
            "total_trades": total_trades,
            "profit_trades": profit_trades,
            "loss_trades": loss_trades,
            "flat_trades": flat_trades,
            "no_trade_days": no_trade_days,
        }

    def calculate_profit_loss_totals(self, trade_details: list[TradeDetail]) -> dict[str, Decimal]:
        total_profit_amount = Decimal("0")
        total_loss_amount = Decimal("0")

        try:
            with localcontext() as ctx:
                ctx.prec = DECIMAL_PRECISION
                for trade in trade_details:
                    if str(trade.sell_reason).lower() in NO_TRADE_REASON_CODES:
                        continue
                    if trade.net_profit > Decimal("0"):
                        total_profit_amount += trade.net_profit
                    elif trade.net_profit < Decimal("0"):
                        total_loss_amount += abs(trade.net_profit)
        except (InvalidOperation, TypeError) as exc:
            raise ReportCalculationError(ERROR_CODES["E_RP_005"], "profit_loss_total_calculation_failed", cause=exc) from exc

        return {
            "total_profit_amount": total_profit_amount.quantize(AMOUNT_QUANTIZER, rounding=AMOUNT_ROUNDING),
            "total_loss_amount": total_loss_amount.quantize(AMOUNT_QUANTIZER, rounding=AMOUNT_ROUNDING),
        }

    def calculate_win_rate(self, profit_trades: int, total_trades: int) -> Decimal:
        if profit_trades < 0 or total_trades < 0:
            raise ReportValidationError(ERROR_CODES["E_RP_001"], "trade_counter_must_be_non_negative")
        if total_trades == 0:
            return Decimal("0.00")

        with localcontext() as ctx:
            ctx.prec = DECIMAL_PRECISION
            rate = (Decimal(profit_trades) / Decimal(total_trades)) * Decimal("100")
            return rate.quantize(RATE_QUANTIZER, rounding=RATE_ROUNDING)

    def build_comprehensive_report(
        self,
        meta: SimulationMeta,
        profit_summary: ProfitSummary,
        summary: ReportSummary,
        trade_details: list[TradeDetail],
        warnings: list[ReportWarning],
        schema_version: str,
    ) -> ComprehensiveReport:
        if not meta.simulation_id:
            raise ReportValidationError(ERROR_CODES["E_RP_002"], "simulation_id_required")
        return ComprehensiveReport(
            schema_version=schema_version,
            simulation_id=meta.simulation_id,
            symbol=meta.symbol,
            strategy=meta.strategy,
            period={
                "start_date": meta.start_date,
                "end_date": meta.end_date,
            },
            profit_summary=profit_summary,
            summary=summary,
            trades=trade_details,
            warnings=warnings,
        )
