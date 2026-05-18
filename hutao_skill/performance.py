"""性能追踪器

用于追踪各操作的性能指标，支持慢操作告警。
"""

import logging
import time
from contextlib import contextmanager
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class PerformanceTracker:
    """性能追踪器"""

    def __init__(self, enabled: bool = True, slow_threshold: float = 1.0):
        self.enabled = enabled
        self.slow_threshold = slow_threshold
        self._stats: Dict[str, Dict[str, Any]] = {}

    @contextmanager
    def track(self, operation: str, **context: Any):
        """追踪一个操作的性能"""
        if not self.enabled:
            yield
            return

        start = time.time()
        try:
            yield
        finally:
            elapsed = time.time() - start
            self._record(operation, elapsed, context)

    def _record(self, operation: str, elapsed: float, context: Dict[str, Any]) -> None:
        """记录性能数据"""
        if operation not in self._stats:
            self._stats[operation] = {
                "count": 0,
                "total": 0.0,
                "min": float("inf"),
                "max": 0.0,
                "times": [],
                "slow_count": 0,
            }

        stat = self._stats[operation]
        stat["count"] += 1
        stat["total"] += elapsed
        stat["min"] = min(stat["min"], elapsed)
        stat["max"] = max(stat["max"], elapsed)
        stat["times"].append(elapsed)

        # 只保留最近 100 次记录
        if len(stat["times"]) > 100:
            stat["times"] = stat["times"][-100:]

        if elapsed > self.slow_threshold:
            stat["slow_count"] += 1
            logger.warning(
                f"Slow operation '{operation}' took {elapsed:.3f}s "
                f"(threshold: {self.slow_threshold}s), context: {context}"
            )

    def get_stats(self, operation: str) -> Optional[Dict[str, Any]]:
        """获取指定操作的统计"""
        stat = self._stats.get(operation)
        if not stat:
            return None

        times = stat["times"]
        count = stat["count"]
        return {
            "count": count,
            "avg": stat["total"] / count if count > 0 else 0,
            "min": stat["min"] if stat["min"] != float("inf") else 0,
            "max": stat["max"],
            "p95": sorted(times)[int(len(times) * 0.95)] if times else 0,
            "slow_count": stat["slow_count"],
        }

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有操作的统计"""
        return {op: self.get_stats(op) for op in self._stats}

    def reset(self) -> None:
        """重置所有统计"""
        self._stats.clear()
