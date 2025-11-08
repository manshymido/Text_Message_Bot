"""Health check system for bot services."""

from datetime import datetime
from typing import Dict, List, Optional

from utils.logger import logger


class HealthStatus:
    """Health status enumeration."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthCheck:
    """Individual health check."""

    def __init__(self, name: str, check_func, critical: bool = True):
        """
        Initialize health check.

        Args:
            name: Name of the health check
            check_func: Function that returns (status, message)
            critical: Whether this check is critical for overall health
        """
        self.name = name
        self.check_func = check_func
        self.critical = critical
        self.last_check: Optional[datetime] = None
        self.last_status: Optional[str] = None
        self.last_message: Optional[str] = None

    def run(self) -> tuple:
        """
        Run the health check.

        Returns:
            Tuple of (status, message)
        """
        try:
            status, message = self.check_func()
            self.last_check = datetime.utcnow()
            self.last_status = status
            self.last_message = message
            return status, message
        except Exception as e:
            logger.error(f"Health check {self.name} failed: {e}")
            return HealthStatus.UNHEALTHY, f"Check failed: {str(e)}"


class HealthChecker:
    """Manages health checks for the bot."""

    def __init__(self):
        """Initialize health checker."""
        self.checks: List[HealthCheck] = []

    def register_check(self, name: str, check_func, critical: bool = True):
        """
        Register a health check.

        Args:
            name: Name of the health check
            check_func: Function that returns (status, message)
            critical: Whether this check is critical
        """
        check = HealthCheck(name, check_func, critical)
        self.checks.append(check)
        logger.info(f"Registered health check: {name}")

    def run_all_checks(self) -> Dict:
        """
        Run all registered health checks.

        Returns:
            Dictionary with overall status and individual check results
        """
        results = {}
        overall_status = HealthStatus.HEALTHY
        has_critical_failure = False

        for check in self.checks:
            status, message = check.run()
            results[check.name] = {
                "status": status,
                "message": message,
                "critical": check.critical,
                "last_check": check.last_check.isoformat() if check.last_check else None,
            }

            if status == HealthStatus.UNHEALTHY:
                if check.critical:
                    has_critical_failure = True
                else:
                    overall_status = HealthStatus.DEGRADED
            elif status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.DEGRADED

        if has_critical_failure:
            overall_status = HealthStatus.UNHEALTHY

        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": results,
        }

    def get_overall_status(self) -> str:
        """
        Get overall health status.

        Returns:
            Overall health status
        """
        result = self.run_all_checks()
        return result["status"]

    def is_healthy(self) -> bool:
        """
        Check if system is healthy.

        Returns:
            True if healthy or degraded, False if unhealthy
        """
        status = self.get_overall_status()
        return status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]

