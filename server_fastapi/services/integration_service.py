from typing import Dict, Any, List, Optional, Union
import asyncio
import logging
import json
import subprocess
import os
from pathlib import Path
from pydantic import BaseModel, Field
import uuid

logger = logging.getLogger(__name__)

# Import circuit breaker and retry policy for resilience
try:
    from ..middleware.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
    from ..middleware.retry_policy import RetryPolicy, exchange_retry_policy
    circuit_breaker_available = True
    retry_policy_available = True
except ImportError:
    circuit_breaker_available = False
    retry_policy_available = False
    logger.warning("Circuit breaker or retry policy not available")

class IntegrationConfig(BaseModel):
    name: str
    enabled: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)
    version: Optional[str] = None
    status: str = "stopped"

class FreqtradeConfig(IntegrationConfig):
    name: str = "freqtrade"
    exchange_name: str = "binanceus"
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    stake_currency: str = "USDT"
    dry_run: bool = True
    strategy: str = "SimpleStrategy"

class JesseConfig(IntegrationConfig):
    name: str = "jesse"
    exchange_name: str = "binanceus"
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    stake_currency: str = "USDT"
    strategy: str = "SimpleStrategy"

class IntegrationService:
    def __init__(self):
        self.integrations: Dict[str, IntegrationConfig] = {}
        self.processes: Dict[str, subprocess.Popen] = {}
        self.base_path = Path(__file__).parent.parent.parent / "server" / "integrations"
        
        # Initialize circuit breakers for each integration
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        if circuit_breaker_available:
            self.circuit_breakers = {
                "freqtrade": CircuitBreaker(
                    name="freqtrade_integration",
                    failure_threshold=5,
                    timeout=60
                ),
                "jesse": CircuitBreaker(
                    name="jesse_integration",
                    failure_threshold=5,
                    timeout=60
                )
            }
        
        self._initialize_integrations()

    def _initialize_integrations(self):
        """Initialize available integrations"""
        # Freqtrade integration
        freqtrade_config = FreqtradeConfig()
        self.integrations["freqtrade"] = freqtrade_config

        # Jesse integration
        jesse_config = JesseConfig()
        self.integrations["jesse"] = jesse_config

    async def list_integrations(self) -> List[Dict[str, Any]]:
        """List all available integrations with their status"""
        result = []
        for name, config in self.integrations.items():
            status = await self.get_integration_status(name)
            result.append({
                "name": config.name,
                "enabled": config.enabled,
                "status": status,
                "version": config.version,
                "config": config.config
            })
        return result

    async def get_integration_status(self, name: str) -> Dict[str, Any]:
        """Get status of a specific integration"""
        if name not in self.integrations:
            return {"status": "not_found", "error": f"Integration {name} not found"}

        config = self.integrations[name]

        # Check if process is running
        if name in self.processes:
            process = self.processes[name]
            if process.poll() is None:  # Still running
                return {"status": "running", "pid": process.pid}
            else:
                # Process finished, clean up
                del self.processes[name]
                config.status = "stopped"

        config.status = "stopped"
        return {"status": config.status}

    async def configure_integration(self, name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Configure an integration"""
        if name not in self.integrations:
            raise ValueError(f"Integration {name} not found")

        integration = self.integrations[name]

        # Update configuration
        for key, value in config.items():
            if hasattr(integration, key):
                setattr(integration, key, value)

        # Update config dict
        integration.config.update(config)

        return {"message": f"Integration {name} configured successfully"}

    async def start_integration(self, name: str) -> Dict[str, Any]:
        """Start an integration adapter"""
        if name not in self.integrations:
            raise ValueError(f"Integration {name} not found")

        # Check if already running
        status = await self.get_integration_status(name)
        if status.get("status") == "running":
            return {"message": f"Integration {name} is already running"}

        # Start the adapter process
        script_path = self.base_path / f"{name}_adapter.py"
        if not script_path.exists():
            raise FileNotFoundError(f"Adapter script not found: {script_path}")

        try:
            # Start process with pipes for stdin/stdout
            process = subprocess.Popen(
                ["python", str(script_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.base_path)
            )

            self.processes[name] = process
            self.integrations[name].status = "running"

            # Give it a moment to start
            await asyncio.sleep(0.5)

            return {"message": f"Integration {name} started successfully", "pid": process.pid}

        except Exception as e:
            logger.error(f"Failed to start integration {name}: {e}")
            raise

    async def stop_integration(self, name: str) -> Dict[str, Any]:
        """Stop an integration adapter"""
        if name not in self.integrations:
            raise ValueError(f"Integration {name} not found")

        if name not in self.processes:
            return {"message": f"Integration {name} is not running"}

        try:
            process = self.processes[name]
            process.terminate()

            # Wait for process to terminate
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

            del self.processes[name]
            self.integrations[name].status = "stopped"

            return {"message": f"Integration {name} stopped successfully"}

        except Exception as e:
            logger.error(f"Failed to stop integration {name}: {e}")
            raise

    async def run_integration_test(self, name: str, test_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run tests for an integration"""
        if name not in self.integrations:
            raise ValueError(f"Integration {name} not found")

        # For now, we'll ping the adapter as a basic test
        try:
            result = await self._call_adapter_method(name, "ping", {})
            return {
                "integration": name,
                "test": "ping",
                "result": result,
                "status": "success"
            }
        except Exception as e:
            return {
                "integration": name,
                "test": "ping",
                "error": str(e),
                "status": "failed"
            }

    async def call_integration_method(self, name: str, method: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Call a method on an integration adapter"""
        return await self._call_adapter_method(name, method, payload)

    async def _call_adapter_method(self, name: str, method: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Internal method to communicate with adapter via stdin/stdout with circuit breaker protection"""
        if name not in self.processes:
            raise RuntimeError(f"Integration {name} is not running")
        
        # Wrap call with circuit breaker if available
        if circuit_breaker_available and name in self.circuit_breakers:
            breaker = self.circuit_breakers[name]
            
            @breaker.call
            async def protected_call():
                return await self._execute_adapter_call(name, method, payload)
            
            try:
                return await protected_call()
            except CircuitBreakerOpenError:
                logger.error(f"Circuit breaker open for {name}, integration unavailable")
                raise RuntimeError(f"Integration {name} circuit breaker is open")
        else:
            # No circuit breaker, call directly
            return await self._execute_adapter_call(name, method, payload)
    
    async def _execute_adapter_call(self, name: str, method: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the actual adapter call"""

        process = self.processes[name]
        if process.poll() is not None:
            # Process died
            del self.processes[name]
            raise RuntimeError(f"Integration {name} process has stopped")

        try:
            # Create request
            request = {
                "id": str(uuid.uuid4()),
                "action": method,
                "payload": payload or {}
            }

            # Send request to stdin
            process.stdin.write(json.dumps(request) + "\n")
            process.stdin.flush()

            # Read response from stdout (with timeout)
            response_line = await asyncio.get_event_loop().run_in_executor(
                None, process.stdout.readline
            )

            if not response_line:
                raise RuntimeError("No response from adapter")

            response = json.loads(response_line.strip())

            if "error" in response:
                raise RuntimeError(response["error"])

            return response.get("result", {})

        except Exception as e:
            logger.error(f"Error calling {method} on {name}: {e}")
            raise

    async def restart_integration(self, name: str) -> Dict[str, Any]:
        """Restart an integration"""
        await self.stop_integration(name)
        await asyncio.sleep(1)  # Brief pause
        return await self.start_integration(name)

    async def cleanup(self):
        """Clean up all running processes"""
        for name in list(self.processes.keys()):
            try:
                await self.stop_integration(name)
            except Exception as e:
                logger.warning(f"Error stopping {name} during cleanup: {e}")
    
    def get_circuit_breaker_stats(self) -> Dict[str, Any]:
        """Get statistics for all circuit breakers"""
        if not circuit_breaker_available:
            return {"status": "unavailable", "message": "Circuit breakers not enabled"}
        
        stats = {}
        for name, breaker in self.circuit_breakers.items():
            stats[name] = breaker.get_stats()
        
        return stats
    
    def reset_circuit_breaker(self, name: str) -> Dict[str, Any]:
        """Manually reset a circuit breaker"""
        if not circuit_breaker_available or name not in self.circuit_breakers:
            return {"status": "error", "message": f"Circuit breaker {name} not found"}
        
        self.circuit_breakers[name].reset()
        return {"status": "success", "message": f"Circuit breaker {name} reset"}

# Global instance
integration_service = IntegrationService()