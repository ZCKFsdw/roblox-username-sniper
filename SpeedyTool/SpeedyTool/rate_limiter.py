"""Adaptive rate limiter for optimal API performance."""

import asyncio
import time
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class RateLimitStats:
    """Statistics for rate limiting decisions."""
    success_rate: float = 1.0
    avg_response_time: float = 0.0
    error_rate: float = 0.0
    requests_per_second: float = 0.0

class AdaptiveRateLimiter:
    """Intelligent rate limiter that adapts to API performance."""
    
    def __init__(self, config):
        self.config = config
        self.semaphore = asyncio.Semaphore(config.initial_concurrent_requests)
        self.current_delay = config.base_delay
        self.current_concurrent = config.initial_concurrent_requests
        
        # Performance tracking
        self.response_times: List[float] = []
        self.error_count = 0
        self.success_count = 0
        self.last_stats_time = time.time()
        self.last_request_time = time.time()
        
        # Rate limiting state
        self.consecutive_errors = 0
        self.consecutive_successes = 0
        
    async def acquire(self) -> None:
        """Acquire permission to make a request."""
        await self.semaphore.acquire()
        
        # Apply dynamic delay
        if self.current_delay > 0:
            await asyncio.sleep(self.current_delay)
    
    def release(self) -> None:
        """Release the semaphore."""
        self.semaphore.release()
    
    def record_success(self, response_time: float) -> None:
        """Record a successful request."""
        self.success_count += 1
        self.consecutive_successes += 1
        self.consecutive_errors = 0
        self.response_times.append(response_time)
        
        # Keep only recent response times
        if len(self.response_times) > 100:
            self.response_times = self.response_times[-50:]
        
        # Adapt rate limiting based on success
        self._adapt_on_success()
    
    def record_error(self, error_type: str = "unknown") -> None:
        """Record a failed request."""
        self.error_count += 1
        self.consecutive_errors += 1
        self.consecutive_successes = 0
        
        # Adapt rate limiting based on error
        self._adapt_on_error(error_type)
    
    def _adapt_on_success(self) -> None:
        """Adapt rate limiting after successful requests."""
        # If we have consistent successes and good response times, increase throughput
        if (self.consecutive_successes >= 10 and 
            self.response_times and 
            sum(self.response_times[-10:]) / min(10, len(self.response_times)) < 0.5):
            
            # Increase concurrency if below max
            if self.current_concurrent < self.config.max_concurrent_requests:
                old_concurrent = self.current_concurrent
                self.current_concurrent = min(
                    self.config.max_concurrent_requests,
                    int(self.current_concurrent * 1.1)
                )
                if self.current_concurrent != old_concurrent:
                    self._update_semaphore()
            
            # Decrease delay
            self.current_delay = max(
                self.config.base_delay,
                self.current_delay * 0.9
            )
    
    def _adapt_on_error(self, error_type: str) -> None:
        """Adapt rate limiting after errors."""
        # Different strategies for different error types
        if "429" in error_type or "rate" in error_type.lower():
            # Rate limit hit - be more aggressive in backing off
            self.current_delay = min(
                self.config.max_delay,
                self.current_delay * self.config.backoff_factor * 2
            )
            # Reduce concurrency more aggressively
            self.current_concurrent = max(
                self.config.min_concurrent_requests,
                int(self.current_concurrent * 0.5)
            )
        else:
            # General error - moderate backoff
            self.current_delay = min(
                self.config.max_delay,
                self.current_delay * self.config.backoff_factor
            )
            # Slight reduction in concurrency
            self.current_concurrent = max(
                self.config.min_concurrent_requests,
                int(self.current_concurrent * 0.8)
            )
        
        self._update_semaphore()
    
    def _update_semaphore(self) -> None:
        """Update semaphore with new concurrency limit."""
        # Create new semaphore with updated limit
        current_value = self.semaphore._value
        self.semaphore = asyncio.Semaphore(self.current_concurrent)
        # Try to preserve some of the current permits
        if current_value > 0:
            for _ in range(min(current_value, self.current_concurrent)):
                try:
                    self.semaphore._value -= 1
                except:
                    break
    
    def get_stats(self) -> RateLimitStats:
        """Get current rate limiting statistics."""
        total_requests = self.success_count + self.error_count
        
        if total_requests == 0:
            return RateLimitStats()
        
        success_rate = self.success_count / total_requests
        error_rate = self.error_count / total_requests
        
        avg_response_time = 0.0
        if self.response_times:
            avg_response_time = sum(self.response_times) / len(self.response_times)
        
        # Calculate requests per second
        current_time = time.time()
        time_elapsed = current_time - self.last_stats_time
        requests_per_second = 0.0
        if time_elapsed > 0:
            requests_per_second = total_requests / time_elapsed
        
        return RateLimitStats(
            success_rate=success_rate,
            avg_response_time=avg_response_time,
            error_rate=error_rate,
            requests_per_second=requests_per_second
        )
    
    def reset_stats(self) -> None:
        """Reset statistics for new measurement period."""
        self.success_count = 0
        self.error_count = 0
        self.response_times.clear()
        self.last_stats_time = time.time()
