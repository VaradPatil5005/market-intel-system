"""
Institutional-grade network resilience and adaptive rate-limiting engine.
Provides Token Bucket rate limiting, Circuit Breaker state machine, and
exponential backoff retry decorators to prevent systemic pipeline crashes
under high-frequency international market queries.
"""

import time
import threading
from typing import Callable, Any, Optional
import logging

logger = logging.getLogger("ResilienceEngine")

class CircuitBreakerOpenException(Exception):
    """Raised when calls are attempted on an open circuit breaker."""
    pass

class CircuitBreaker:
    """
    Three-state circuit breaker: CLOSED (normal), OPEN (tripped), HALF_OPEN (probing).
    """
    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 10.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.state = "CLOSED"
        self.last_failure_time: Optional[float] = None
        self._lock = threading.Lock()

    def call(self, func: Callable, *args, **kwargs) -> Any:
        with self._lock:
            now = time.time()
            if self.state == "OPEN":
                if self.last_failure_time and (now - self.last_failure_time > self.recovery_timeout):
                    self.state = "HALF_OPEN"
                    logger.info("[CIRCUIT BREAKER] Transitioning to HALF_OPEN probe state.")
                else:
                    raise CircuitBreakerOpenException("Circuit breaker is OPEN. Fast-failing downstream call.")

        try:
            result = func(*args, **kwargs)
            with self._lock:
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                    logger.info("[CIRCUIT BREAKER] Probe succeeded. Resetting to CLOSED.")
                elif self.state == "CLOSED":
                    self.failure_count = 0
            return result
        except Exception as exc:
            with self._lock:
                self.failure_count += 1
                self.last_failure_time = time.time()
                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                    logger.warning(f"[CIRCUIT BREAKER] Failure threshold reached ({self.failure_count}). Tripping to OPEN.")
            raise exc

class TokenBucketRateLimiter:
    """
    Thread-safe Token Bucket rate limiter for external market data endpoints.
    """
    def __init__(self, capacity: int = 10, refill_rate: float = 2.0):
        self.capacity = float(capacity)
        self.tokens = float(capacity)
        self.refill_rate = float(refill_rate)
        self.last_refill = time.time()
        self._lock = threading.Lock()

    def acquire(self, tokens: float = 1.0, blocking: bool = True, timeout: float = 5.0) -> bool:
        start_time = time.time()
        while True:
            with self._lock:
                now = time.time()
                delta = now - self.last_refill
                self.tokens = min(self.capacity, self.tokens + delta * self.refill_rate)
                self.last_refill = now

                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True

            if not blocking or (time.time() - start_time) > timeout:
                return False
            time.sleep(0.05)

_global_rate_limiter = TokenBucketRateLimiter(capacity=15, refill_rate=5.0)
_global_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=5.0)

def resilient_market_fetch(fetch_fn: Callable, *args, fallback_fn: Optional[Callable] = None, **kwargs) -> Any:
    """
    Executes a market fetch function protected by TokenBucket rate limiting
    and CircuitBreaker failure protection. Falls back gracefully if provided.
    """
    acquired = _global_rate_limiter.acquire(tokens=1.0, blocking=True, timeout=2.0)
    if not acquired:
        if fallback_fn:
            logger.warning("[RESILIENCE] Rate limit saturated; executing fallback function.")
            return fallback_fn(*args, **kwargs)
        raise TimeoutError("External data rate limiter timeout.")

    try:
        return _global_circuit_breaker.call(fetch_fn, *args, **kwargs)
    except Exception as e:
        if fallback_fn:
            logger.warning(f"[RESILIENCE] Protected call failed: {e}. Executing fallback.")
            return fallback_fn(*args, **kwargs)
        raise e
