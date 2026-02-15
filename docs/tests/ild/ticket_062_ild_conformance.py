from __future__ import annotations

import asyncio
import inspect
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd
from fastapi import FastAPI
from fastapi.testclient import TestClient

from marketdata.errors import ERROR_CODES as MD_ERROR_CODES
from marketdata.errors import ExternalAPIError
from marketdata.market_data_service import MarketDataService
from marketdata.yahoo_finance_client import YahooFinanceClient
from report.report_service import ReportService
from simulation.simulation_engine import SimulationEngine
from strategy.strategy_registry import StrategyRegistry
from webapi.middleware.request_context import configure_request_context
from webapi.routers.simulation_router import create_simulation_router
from webapi.routers import simulation_router as simulation_router_module
from webapi.routers.sse_router import create_sse_router
from webapi.routers import sse_router as sse_router_module
from webapi.services.report_facade import ReportFacade
from webapi.services.simulation_facade import SimulationFacade
from webapi.services.stream_session_manager import StreamSessionManager
from webapi.services.timeout_policy import run_with_timeout


class _FakeCacheRepo:
    def __init__(self, df: pd.DataFrame, fresh: bool) -> None:
        self._df = df
        self._fresh = fresh
        self.upsert_called = False

    def read_by_symbol_period_interval(self, symbol, from_ts, to_ts):
        _ = (symbol, from_ts, to_ts)
        return self._df

    def is_cache_fresh(self, symbol, now_kst, ttl_min):
        _ = (symbol, now_kst, ttl_min)
        return self._fresh

    def upsert_market_data_cache(self, symbol, rows, fetched_at):
        _ = (symbol, rows, fetched_at)
        self.upsert_called = True
        return len(list(rows))


class _FakeValidator:
    def normalize_columns(self, df):
        return df

    def normalize_timezone(self, df):
        return df

    def filter_trading_session(self, df):
        return df

    def validate_integrity(self, df):
        _ = df


class _FakeRsiCalculator:
    def calculate_rsi(self, candles_df, period=14):
        _ = period
        return pd.Series([50.0] * len(candles_df), index=candles_df.index, name="rsi")


class _FakeYahooClient:
    def __init__(self, sequence):
        self.sequence = list(sequence)
        self.calls = 0

    def fetch_ohlcv(self, **kwargs):
        _ = kwargs
        self.calls += 1
        current = self.sequence[self.calls - 1]
        if isinstance(current, Exception):
            raise current
        return current


class _SimulationFacadeForRouter:
    def exists(self, simulation_id: str) -> bool:
        _ = simulation_id
        return True


class _SimulationFacadeForApiRouter:
    def start_simulation(self, symbol, strategy, idempotency_key):
        _ = (symbol, strategy, idempotency_key)
        return SimpleNamespace(model_dump=lambda mode="json": {
            "simulation_id": "SIM-TEST-0001",
            "status": "queued",
            "symbol": "005930.KS",
            "strategy": "sell_trailing_stop",
            "created_at": "2026-02-16T00:00:00+09:00",
            "updated_at": "2026-02-16T00:00:00+09:00",
        })

    def list_status(self, status, offset, limit):
        _ = (status, offset, limit)
        return []

    def get_status(self, simulation_id):
        _ = simulation_id
        return SimpleNamespace(
            status="completed",
            model_dump=lambda mode="json": {
                "simulation_id": "SIM-TEST-0001",
                "status": "completed",
                "symbol": "005930.KS",
                "strategy": "sell_trailing_stop",
                "created_at": "2026-02-16T00:00:00+09:00",
                "updated_at": "2026-02-16T00:00:00+09:00",
                "error_code": None,
                "error_message": None,
            },
        )


class _ReportFacadeForApiRouter:
    def generate_report(self, simulation_id, query):
        _ = (simulation_id, query)
        return {"schema_version": "1.0", "summary": {}}


class ContractSignatureTests(unittest.TestCase):
    def test_public_signature_market_data_service(self):
        sig = inspect.signature(MarketDataService.fetch_market_data_with_rsi)
        self.assertEqual(list(sig.parameters.keys()), ["self", "symbol", "period", "interval"])

    def test_public_signature_yahoo_client(self):
        sig = inspect.signature(YahooFinanceClient.fetch_ohlcv)
        self.assertEqual(
            list(sig.parameters.keys()),
            ["self", "symbol", "period", "interval", "auto_adjust", "timeout_sec"],
        )

    def test_public_signature_timeout_policy(self):
        sig = inspect.signature(run_with_timeout)
        self.assertEqual(list(sig.parameters.keys()), ["awaitable", "timeout_seconds", "operation"])

    def test_public_signature_router_factories(self):
        sig_sim = inspect.signature(create_simulation_router)
        sig_sse = inspect.signature(create_sse_router)
        self.assertEqual(list(sig_sim.parameters.keys()), ["simulation_facade", "report_facade"])
        self.assertEqual(list(sig_sse.parameters.keys()), ["simulation_facade", "stream_session_manager"])

    def test_public_signature_simulation_strategy_report_modules(self):
        sig_engine = inspect.signature(SimulationEngine.run_simulation)
        sig_registry_register = inspect.signature(StrategyRegistry.register)
        sig_registry_get = inspect.signature(StrategyRegistry.get)
        sig_report = inspect.signature(ReportService.generate_report)

        self.assertEqual(list(sig_engine.parameters.keys()), ["self", "request"])
        self.assertEqual(list(sig_registry_register.parameters.keys()), ["self", "strategy"])
        self.assertEqual(list(sig_registry_get.parameters.keys()), ["self", "name"])
        self.assertEqual(
            list(sig_report.parameters.keys()),
            [
                "self",
                "simulation_id",
                "schema_version",
                "include_no_trade",
                "from_date",
                "to_date",
                "sort_order",
            ],
        )

    def test_public_signature_webapi_facades(self):
        sig_sim_start = inspect.signature(SimulationFacade.start_simulation)
        sig_sim_get = inspect.signature(SimulationFacade.get_status)
        sig_report_facade = inspect.signature(ReportFacade.generate_report)

        self.assertEqual(
            list(sig_sim_start.parameters.keys()),
            ["self", "symbol", "strategy", "idempotency_key"],
        )
        self.assertEqual(list(sig_sim_get.parameters.keys()), ["self", "simulation_id"])
        self.assertEqual(list(sig_report_facade.parameters.keys()), ["self", "simulation_id", "query"])


class ExternalDependencyRuleTests(unittest.TestCase):
    def test_yfinance_download_call_contract(self):
        sample = pd.DataFrame(
            {
                "Open": [1.0],
                "High": [1.1],
                "Low": [0.9],
                "Close": [1.05],
                "Volume": [100],
            },
            index=pd.to_datetime(["2026-02-14 09:00:00"]),
        )

        captured = {}

        def _fake_download(**kwargs):
            captured.update(kwargs)
            return sample

        with patch("marketdata.yahoo_finance_client.yf.download", side_effect=_fake_download):
            result = YahooFinanceClient().fetch_ohlcv("005930.KS")

        self.assertFalse(result.empty)
        self.assertEqual(captured["tickers"], "005930.KS")
        self.assertEqual(captured["period"], "60d")
        self.assertEqual(captured["interval"], "5m")
        self.assertTrue(captured["auto_adjust"])
        self.assertFalse(captured["threads"])
        self.assertFalse(captured["progress"])
        self.assertEqual(captured["timeout"], 10)

    def test_marketdata_retry_on_temporary_failures(self):
        index = pd.to_datetime(["2026-02-14 09:00:00", "2026-02-14 09:05:00"])
        frame = pd.DataFrame(
            {
                "open": [100.0, 101.0],
                "high": [101.0, 102.0],
                "low": [99.0, 100.0],
                "close": [100.5, 101.5],
                "volume": [1000, 1100],
            },
            index=index,
        )

        temporary = ExternalAPIError(MD_ERROR_CODES["E_MD_006"], "temporary")
        fake_yahoo = _FakeYahooClient([temporary, temporary, frame])
        fake_cache = _FakeCacheRepo(pd.DataFrame(), fresh=False)
        service = MarketDataService(
            cache_repository=fake_cache,
            yahoo_client=fake_yahoo,
            validator=_FakeValidator(),
            rsi_calculator=_FakeRsiCalculator(),
        )

        with patch("marketdata.market_data_service.time.sleep", return_value=None):
            result = service.fetch_market_data_with_rsi("005930.KS")

        self.assertEqual(fake_yahoo.calls, 3)
        self.assertIn("rsi", result.columns)


class CacheAndProtocolLifecycleTests(unittest.TestCase):
    def test_marketdata_cache_hit_skips_external_fetch(self):
        index = pd.to_datetime(["2026-02-14 09:00:00"])
        cache_df = pd.DataFrame(
            {
                "open": [100.0],
                "high": [101.0],
                "low": [99.5],
                "close": [100.2],
                "volume": [1000],
                "rsi": [55.0],
                "fetched_at": ["2026-02-14T00:00:00+00:00"],
            },
            index=index,
        )

        fake_cache = _FakeCacheRepo(cache_df, fresh=True)
        fake_yahoo = _FakeYahooClient([])
        service = MarketDataService(
            cache_repository=fake_cache,
            yahoo_client=fake_yahoo,
            validator=_FakeValidator(),
            rsi_calculator=_FakeRsiCalculator(),
        )

        result = service.fetch_market_data_with_rsi("005930.KS")
        self.assertFalse(result.empty)
        self.assertEqual(fake_yahoo.calls, 0)

    def test_sse_frame_contains_required_fields(self):
        manager = StreamSessionManager()
        event = manager.append_event("SIM-TEST-0001", "progress", {"status": "running"})
        frame = manager.to_sse_frame(event)
        self.assertIn("id:", frame)
        self.assertIn("event:", frame)
        self.assertIn("retry:", frame)
        self.assertIn("data:", frame)

    def test_sse_router_declares_stream_media_and_headers(self):
        source = inspect.getsource(sse_router_module.create_sse_router)
        self.assertIn('media_type="text/event-stream"', source)
        self.assertIn('"Cache-Control": "no-cache"', source)
        self.assertIn('"Connection": "keep-alive"', source)
        self.assertIn('"X-Accel-Buffering": "no"', source)

    def test_simulation_router_uses_timeout_wrappers_for_dependencies(self):
        source = inspect.getsource(simulation_router_module.create_simulation_router)
        self.assertIn('operation="simulation.start"', source)
        self.assertIn('operation="simulation.list"', source)
        self.assertIn('operation="simulation.get_status"', source)
        self.assertIn('operation="simulation.get_status_for_report"', source)
        self.assertIn('operation="report.generate"', source)

    def test_simulation_router_start_returns_202(self):
        app = FastAPI()
        configure_request_context(app)
        app.include_router(
            create_simulation_router(_SimulationFacadeForApiRouter(), _ReportFacadeForApiRouter())
        )

        with TestClient(app) as client:
            response = client.post(
                "/api/simulations",
                json={"symbol": "005930.KS", "strategy": "sell_trailing_stop"},
                headers={"Idempotency-Key": "ABCDEF12"},
            )

        self.assertEqual(response.status_code, 202)
        body = response.json()
        self.assertTrue(body["success"])


class TimeoutPolicyBehaviorTests(unittest.TestCase):
    def test_run_with_timeout_success(self):
        async def _ok():
            await asyncio.sleep(0)
            return "ok"

        result = asyncio.run(run_with_timeout(_ok(), 0.5, "unit.test"))
        self.assertEqual(result, "ok")

    def test_run_with_timeout_timeout(self):
        async def _slow():
            await asyncio.sleep(0.1)
            return "late"

        with self.assertRaises(Exception) as ctx:
            asyncio.run(run_with_timeout(_slow(), 0.01, "unit.timeout"))

        self.assertIn("DEPENDENCY_TIMEOUT", str(ctx.exception))


if __name__ == "__main__":
    start = datetime.now()
    print(f"[TICKET-062] ILD conformance checks started: {start.isoformat()}")
    unittest.main(verbosity=2)
