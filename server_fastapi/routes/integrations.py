from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, List, Optional, Annotated
import logging

from ..services.trading_orchestrator import (
    TradingOrchestrator,
    EnsemblePrediction,
    PingResult,
    BacktestResult,
)
from ..services.integration_service import (
    integration_service,
    IntegrationConfig,
    FreqtradeConfig,
    JesseConfig,
)


logger = logging.getLogger(__name__)


# Dependency injection for orchestrator
def get_trading_orchestrator():
    return TradingOrchestrator()


# Dependency injection for integration service
def get_integration_service():
    return integration_service


# Import centralized auth dependency
from ..dependencies.auth import get_current_user
from ..middleware.cache_manager import cached


# Pydantic models for integration management
class IntegrationListResponse(BaseModel):
    name: str
    enabled: bool
    status: Dict[str, Any]
    version: Optional[str] = None
    config: Dict[str, Any]


class ConfigureIntegrationRequest(BaseModel):
    enabled: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


class IntegrationTestRequest(BaseModel):
    config: Optional[Dict[str, Any]] = None


class IntegrationResponse(BaseModel):
    message: str
    data: Optional[Dict[str, Any]] = None


class IntegrationStatusResponse(BaseModel):
    name: str
    status: Dict[str, Any]
    details: Optional[Dict[str, Any]] = None


class IntegrationStatusDetail(BaseModel):
    name: str
    running: bool
    pid: Optional[int] = None
    enabled: bool = True
    error: Optional[str] = None


class IntegrationsOverviewResponse(BaseModel):
    status: str
    running: bool
    integrations: Dict[str, IntegrationStatusDetail]
    adapters: Dict[str, IntegrationStatusDetail] | None = None
    started: bool | None = None


router = APIRouter()


# Overview status endpoint (public, no auth required)
@router.get("/status", response_model=IntegrationsOverviewResponse)
async def get_integrations_overview(
    integration_svc: Annotated[Any, Depends(get_integration_service)],
    orchestrator: Annotated[TradingOrchestrator, Depends(get_trading_orchestrator)],
) -> IntegrationsOverviewResponse:
    """Get overview status of all integrations and trading adapters"""
    try:
        statuses: Dict[str, IntegrationStatusDetail] = {}
        any_running = False

        # Check integration service processes
        for name in integration_svc.integrations.keys():
            proc = integration_svc.processes.get(name)
            running = proc is not None and proc.poll() is None
            any_running = any_running or running

            statuses[name] = IntegrationStatusDetail(
                name=name,
                running=running,
                pid=proc.pid if running else None,
                enabled=integration_svc.integrations[name].enabled,
            )

        # Collect adapter statuses separately for response shape expected by tests
        adapters: Dict[str, IntegrationStatusDetail] = {}
        for adapter_name in ["freqtrade", "jesse"]:
            detail = IntegrationStatusDetail(
                name=adapter_name, running=orchestrator.started, enabled=True
            )
            adapters[adapter_name] = detail
            if orchestrator.started:
                any_running = True
            # Keep adapters also inside integrations for backwards compatibility
            statuses[adapter_name] = detail

        return IntegrationsOverviewResponse(
            status="ok",
            running=any_running,
            integrations=statuses,
            adapters=adapters,
            started=orchestrator.started,
        )
    except Exception as e:
        logger.error(f"Error getting integrations overview: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# Integration management endpoints
@router.get("/integrations", response_model=List[IntegrationListResponse])
@cached(ttl=120, prefix="integrations")  # 120s TTL for integrations list
async def list_integrations(
    integration_svc: Annotated[Any, Depends(get_integration_service)],
    user: Annotated[dict, Depends(get_current_user)],
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> List[IntegrationListResponse]:
    """List all available integrations with their status and pagination"""
    try:
        integrations = await integration_svc.list_integrations()

        # Apply pagination
        total = len(integrations)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_integrations = integrations[start_idx:end_idx]

        return [
            IntegrationListResponse(**integration)
            for integration in paginated_integrations
        ]
    except Exception as e:
        logger.error(f"Error listing integrations: {e}")
        raise HTTPException(status_code=500, detail="Failed to list integrations")


@router.get("/integrations/{name}/status", response_model=IntegrationStatusResponse)
async def get_integration_status(
    name: str,
    integration_svc: Annotated[Any, Depends(get_integration_service)],
    user: Annotated[dict, Depends(get_current_user)],
) -> IntegrationStatusResponse:
    """Get status of a specific integration"""
    try:
        status = await integration_svc.get_integration_status(name)
        return IntegrationStatusResponse(name=name, status=status)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting integration status for {name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status for {name}")


@router.put("/integrations/{name}/configure", response_model=IntegrationResponse)
async def configure_integration(
    name: str,
    request: ConfigureIntegrationRequest,
    integration_svc: Annotated[Any, Depends(get_integration_service)],
    user: Annotated[dict, Depends(get_current_user)],
) -> IntegrationResponse:
    """Configure an integration adapter"""
    try:
        config_updates = {}
        if request.enabled is not None:
            config_updates["enabled"] = request.enabled
        if request.config:
            config_updates.update(request.config)

        result = await integration_svc.configure_integration(name, config_updates)
        return IntegrationResponse(message=result["message"])
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error configuring integration {name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to configure {name}")


@router.post("/integrations/{name}/test", response_model=Dict[str, Any])
async def run_integration_test(
    name: str,
    integration_svc: Annotated[Any, Depends(get_integration_service)],
    user: Annotated[dict, Depends(get_current_user)],
    request: IntegrationTestRequest = IntegrationTestRequest(),
) -> Dict[str, Any]:
    """Run tests for an integration"""
    try:
        result = await integration_svc.run_integration_test(name, request.config)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error running test for integration {name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to run test for {name}")


@router.post("/integrations/{name}/start", response_model=IntegrationResponse)
async def start_integration(
    name: str,
    integration_svc: Annotated[Any, Depends(get_integration_service)],
    user: Annotated[dict, Depends(get_current_user)],
) -> IntegrationResponse:
    """Start an integration adapter"""
    try:
        result = await integration_svc.start_integration(name)
        return IntegrationResponse(
            message=result["message"], data={"pid": result.get("pid")}
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting integration {name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start {name}")


@router.post("/integrations/{name}/stop", response_model=IntegrationResponse)
async def stop_integration(
    name: str,
    integration_svc: Annotated[Any, Depends(get_integration_service)],
    user: Annotated[dict, Depends(get_current_user)],
) -> IntegrationResponse:
    """Stop an integration adapter"""
    try:
        result = await integration_svc.stop_integration(name)
        return IntegrationResponse(message=result["message"])
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error stopping integration {name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop {name}")


@router.post("/integrations/{name}/restart", response_model=IntegrationResponse)
async def restart_integration(
    name: str,
    integration_svc: Annotated[Any, Depends(get_integration_service)],
    user: Annotated[dict, Depends(get_current_user)],
) -> IntegrationResponse:
    """Restart an integration adapter"""
    try:
        result = await integration_svc.restart_integration(name)
        return IntegrationResponse(
            message=result["message"], data={"pid": result.get("pid")}
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error restarting integration {name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to restart {name}")


class PredictRequest(BaseModel):
    symbol: str = Field(..., description="Trading symbol (e.g., 'BTC/USDT')")
    timeframe: str = Field("1h", description="Timeframe for analysis")
    data: List[Dict[str, Any]] = Field(
        ..., description="OHLCV market data", min_length=1
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symbol": "BTC/USDT",
                "timeframe": "1h",
                "data": [
                    {
                        "timestamp": "2023-01-01T00:00:00Z",
                        "open": 16500.0,
                        "high": 16600.0,
                        "low": 16400.0,
                        "close": 16550.0,
                        "volume": 100.0,
                    }
                ],
            }
        }
    )


class BacktestRequest(BaseModel):
    symbol: str = Field(..., description="Trading symbol")
    start_date: str = Field(..., description="Backtest start date (ISO format)")
    end_date: str = Field(..., description="Backtest end date (ISO format)")
    initial_balance: float = Field(10000.0, description="Initial balance", gt=0)
    strategy_params: Dict[str, Any] = Field(
        default_factory=dict, description="Strategy parameters"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symbol": "BTC/USDT",
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
                "initial_balance": 10000.0,
                "strategy_params": {"rsi_period": 14},
            }
        }
    )


@router.post("/predict")
async def predict(
    request: PredictRequest,
    orchestrator: Annotated[TradingOrchestrator, Depends(get_trading_orchestrator)],
    integration_svc: Annotated[Any, Depends(get_integration_service)],
    user: Annotated[dict, Depends(get_current_user)],
) -> EnsemblePrediction:
    """Get ensemble prediction from all available trading frameworks"""
    try:
        # Validate input data
        if not request.data or len(request.data) == 0:
            raise HTTPException(status_code=400, detail="Market data is required")
        if not request.symbol:
            raise HTTPException(status_code=400, detail="Symbol is required")

        payload = {
            "symbol": request.symbol,
            "timeframe": request.timeframe,
            "data": request.data,
        }
        prediction = await orchestrator.get_ensemble_prediction(payload)
        return prediction
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ensemble prediction: {e}")
        raise HTTPException(status_code=500, detail="Failed to get prediction")


@router.post("/backtest")
async def backtest(
    request: BacktestRequest,
    orchestrator: Annotated[TradingOrchestrator, Depends(get_trading_orchestrator)],
    integration_svc: Annotated[Any, Depends(get_integration_service)],
    user: Annotated[dict, Depends(get_current_user)],
) -> BacktestResult:
    """Run backtest across all trading frameworks"""
    try:
        # Validate input data
        if not request.symbol:
            raise HTTPException(status_code=400, detail="Symbol is required")
        if not request.start_date or not request.end_date:
            raise HTTPException(
                status_code=400, detail="Start and end dates are required"
            )
        if request.start_date >= request.end_date:
            raise HTTPException(
                status_code=400, detail="End date must be after start date"
            )
        if request.initial_balance <= 0:
            raise HTTPException(
                status_code=400, detail="Initial balance must be positive"
            )

        payload = {
            "symbol": request.symbol,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "initial_balance": request.initial_balance,
            "strategy_params": request.strategy_params,
        }
        result = await orchestrator.backtest(payload)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        raise HTTPException(status_code=500, detail="Failed to run backtest")


@router.get("/ping")
async def ping(
    orchestrator: Annotated[TradingOrchestrator, Depends(get_trading_orchestrator)],
    integration_svc: Annotated[Any, Depends(get_integration_service)],
    user: Annotated[dict, Depends(get_current_user)],
) -> PingResult:
    """Ping all trading framework adapters"""
    try:
        result = await orchestrator.ping_all()
        # Enhance with integration service status
        enhanced_result = PingResult(freqtrade=result.freqtrade, jesse=result.jesse)
        return enhanced_result
    except Exception as e:
        logger.error(f"Error pinging adapters: {e}")
        raise HTTPException(status_code=500, detail="Failed to ping adapters")


@router.post("/start")
async def start_all(
    orchestrator: Annotated[TradingOrchestrator, Depends(get_trading_orchestrator)],
    integration_svc: Annotated[Any, Depends(get_integration_service)],
    user: Annotated[dict, Depends(get_current_user)],
):
    """Start all trading framework adapters"""
    try:
        orchestrator.start_all()
        # Also start integration services
        for name in integration_svc.integrations.keys():
            if integration_svc.integrations[name].enabled:
                try:
                    await integration_svc.start_integration(name)
                except Exception as e:
                    logger.warning(f"Failed to start integration {name}: {e}")
        return {"message": "All trading adapters started successfully"}
    except Exception as e:
        logger.error(f"Error starting adapters: {e}")
        raise HTTPException(status_code=500, detail="Failed to start adapters")


@router.post("/stop")
async def stop_all(
    orchestrator: Annotated[TradingOrchestrator, Depends(get_trading_orchestrator)],
    integration_svc: Annotated[Any, Depends(get_integration_service)],
    user: Annotated[dict, Depends(get_current_user)],
):
    """Stop all trading framework adapters"""
    try:
        orchestrator.stop_all()
        # Also stop integration services
        await integration_svc.cleanup()
        return {"message": "All trading adapters stopped successfully"}
    except Exception as e:
        logger.error(f"Error stopping adapters: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop adapters")


@router.get("/status")
async def get_status(
    orchestrator: Annotated[TradingOrchestrator, Depends(get_trading_orchestrator)],
    integration_svc: Annotated[Any, Depends(get_integration_service)],
    user: Annotated[dict, Depends(get_current_user)],
) -> Dict[str, Any]:
    """Get status of all trading framework adapters"""
    try:
        ping_result = await orchestrator.ping_all()
        # Get integration statuses
        integration_statuses = {}
        for name in integration_svc.integrations.keys():
            try:
                status = await integration_svc.get_integration_status(name)
                integration_statuses[name] = status
            except Exception as e:
                integration_statuses[name] = {"status": "error", "error": str(e)}

        return {
            "started": getattr(orchestrator, "started", False),
            "adapters": {
                "freqtrade": getattr(ping_result, "freqtrade", None),
                "jesse": getattr(ping_result, "jesse", None),
            },
            "integrations": integration_statuses,
        }
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get status")


@router.get("/adapter/{name}/health")
async def get_adapter_health(
    name: str,
    orchestrator: Annotated[TradingOrchestrator, Depends(get_trading_orchestrator)],
    integration_svc: Annotated[Any, Depends(get_integration_service)],
    user: Annotated[dict, Depends(get_current_user)],
) -> Dict[str, Any]:
    """Get health status of a specific adapter"""
    try:
        # Check orchestrator health
        ping_result = await orchestrator.ping_all()
        orchestrator_status = None
        if name == "freqtrade":
            orchestrator_status = getattr(ping_result, "freqtrade", None)
        elif name == "jesse":
            orchestrator_status = getattr(ping_result, "jesse", None)

        # Check integration service health
        integration_status = await integration_svc.get_integration_status(name)

        # Combine results
        healthy = False
        details = {
            "orchestrator": orchestrator_status,
            "integration": integration_status,
        }

        # Determine overall health
        if orchestrator_status and orchestrator_status.get("ok", False):
            healthy = True
        elif integration_status.get("status") == "running":
            healthy = True

        return {"adapter": name, "healthy": healthy, "details": details}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting adapter health for {name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get health for {name}")


@router.post("/adapter/{name}/restart")
async def restart_adapter(
    name: str,
    orchestrator: Annotated[TradingOrchestrator, Depends(get_trading_orchestrator)],
    integration_svc: Annotated[Any, Depends(get_integration_service)],
    user: Annotated[dict, Depends(get_current_user)],
):
    """Restart a specific adapter"""
    try:
        # Restart integration service
        result = await integration_svc.restart_integration(name)
        return {"message": f"Adapter {name} restarted successfully", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error restarting adapter {name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to restart adapter {name}")
