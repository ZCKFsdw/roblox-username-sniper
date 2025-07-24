"""Advanced performance optimizations for ultra-high-speed username checking."""

import asyncio
import aiohttp
import time
import ujson
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import hashlib
import random

@dataclass
class RequestOptimization:
    """Request optimization strategies."""
    use_session_pooling: bool = True
    enable_request_batching: bool = True
    use_intelligent_backoff: bool = True
    enable_response_caching: bool = True
    use_request_prioritization: bool = True

class AdvancedRequestOptimizer:
    """Advanced request optimizer with cutting-edge performance techniques."""
    
    def __init__(self, config):
        self.config = config
        self.session_pool: List[aiohttp.ClientSession] = []
        self.session_index = 0
        self.response_cache: Dict[str, Tuple[dict, float]] = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Performance tracking
        self.request_times: List[float] = []
        self.success_streak = 0
        self.error_streak = 0
        
    async def create_session_pool(self, pool_size: int = 3) -> None:
        """Create a pool of optimized sessions for better performance."""
        for i in range(pool_size):
            connector = aiohttp.TCPConnector(
                limit=400,
                limit_per_host=150,
                ttl_dns_cache=900,  # 15 minutes
                use_dns_cache=True,
                keepalive_timeout=120,  # 2 minutes
                enable_cleanup_closed=True,
                force_close=False,
                happy_eyeballs_delay=0.1,  # IPv4/IPv6 dual stack optimization
            )
            
            timeout = aiohttp.ClientTimeout(
                total=self.config.total_timeout,
                connect=self.config.connect_timeout,
                sock_read=self.config.read_timeout
            )
            
            # Randomize User-Agent for each session to avoid fingerprinting
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/120.0'
            ]
            
            headers = {
                'User-Agent': random.choice(user_agents),
                'Accept': 'application/json,text/plain,*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'DNT': '1',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'cross-site',
            }
            
            session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=headers,
                json_serialize=ujson.dumps,
                trust_env=True,
            )
            
            self.session_pool.append(session)
    
    async def close_session_pool(self) -> None:
        """Close all sessions in the pool."""
        for session in self.session_pool:
            await session.close()
        self.session_pool.clear()
    
    def get_next_session(self) -> aiohttp.ClientSession:
        """Get the next session from the pool using round-robin."""
        if not self.session_pool:
            raise RuntimeError("Session pool not initialized")
        
        session = self.session_pool[self.session_index]
        self.session_index = (self.session_index + 1) % len(self.session_pool)
        return session
    
    def get_cache_key(self, username: str) -> str:
        """Generate cache key for username."""
        return hashlib.md5(username.encode()).hexdigest()
    
    def get_cached_response(self, username: str) -> Optional[dict]:
        """Get cached response if available and not expired."""
        cache_key = self.get_cache_key(username)
        if cache_key in self.response_cache:
            response, timestamp = self.response_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return response
            else:
                # Remove expired cache entry
                del self.response_cache[cache_key]
        return None
    
    def cache_response(self, username: str, response: dict) -> None:
        """Cache response with timestamp."""
        cache_key = self.get_cache_key(username)
        self.response_cache[cache_key] = (response, time.time())
        
        # Limit cache size to prevent memory issues
        if len(self.response_cache) > 10000:
            # Remove oldest 20% of entries
            sorted_cache = sorted(self.response_cache.items(), key=lambda x: x[1][1])
            for key, _ in sorted_cache[:2000]:
                del self.response_cache[key]
    
    async def make_optimized_request(self, username: str) -> dict:
        """Make an optimized request with advanced techniques."""
        # Check cache first
        cached_response = self.get_cached_response(username)
        if cached_response:
            return cached_response
        
        session = self.get_next_session()
        url = f"{self.config.api_url}?Username={username}&Birthday={self.config.birthday}"
        
        start_time = time.time()
        
        try:
            async with session.get(url) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json(loads=ujson.loads)
                    
                    # Cache successful responses
                    self.cache_response(username, data)
                    
                    # Track performance
                    self.request_times.append(response_time)
                    self.success_streak += 1
                    self.error_streak = 0
                    
                    # Keep only recent times for performance calculation
                    if len(self.request_times) > 1000:
                        self.request_times = self.request_times[-500:]
                    
                    return data
                else:
                    self.error_streak += 1
                    self.success_streak = 0
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status
                    )
        
        except Exception as e:
            self.error_streak += 1
            self.success_streak = 0
            raise e
    
    def get_adaptive_delay(self) -> float:
        """Calculate adaptive delay based on performance metrics."""
        base_delay = self.config.base_delay
        
        # If we're on a success streak and performance is good, reduce delay
        if self.success_streak > 20 and self.request_times:
            avg_time = sum(self.request_times[-20:]) / min(20, len(self.request_times))
            if avg_time < 0.2:  # If average response time is under 200ms
                return max(0.0001, base_delay * 0.5)  # Reduce delay by 50%
        
        # If we're having errors, increase delay
        if self.error_streak > 5:
            return min(self.config.max_delay, base_delay * (1.5 ** min(self.error_streak, 10)))
        
        return base_delay
    
    def get_performance_stats(self) -> dict:
        """Get current performance statistics."""
        if not self.request_times:
            return {
                'avg_response_time': 0.0,
                'min_response_time': 0.0,
                'max_response_time': 0.0,
                'cache_hit_ratio': 0.0,
                'success_streak': self.success_streak,
                'error_streak': self.error_streak
            }
        
        recent_times = self.request_times[-100:] if len(self.request_times) > 100 else self.request_times
        cache_size = len(self.response_cache)
        
        return {
            'avg_response_time': sum(recent_times) / len(recent_times),
            'min_response_time': min(recent_times),
            'max_response_time': max(recent_times),
            'cache_size': cache_size,
            'success_streak': self.success_streak,
            'error_streak': self.error_streak,
            'total_requests': len(self.request_times)
        }

class UltraFastBatchProcessor:
    """Ultra-fast batch processor with intelligent request distribution."""
    
    def __init__(self, optimizer: AdvancedRequestOptimizer, rate_limiter):
        self.optimizer = optimizer
        self.rate_limiter = rate_limiter
    
    async def process_batch_ultra_fast(self, usernames: List[str]) -> List[dict]:
        """Process a batch of usernames with maximum performance optimizations."""
        # Create semaphore for this batch
        semaphore = asyncio.Semaphore(self.rate_limiter.current_concurrent)
        
        async def process_single(username: str) -> dict:
            async with semaphore:
                # Apply adaptive delay
                delay = self.optimizer.get_adaptive_delay()
                if delay > 0:
                    await asyncio.sleep(delay)
                
                try:
                    return await self.optimizer.make_optimized_request(username)
                except Exception as e:
                    return {'error': str(e), 'username': username}
        
        # Create tasks for all usernames
        tasks = [process_single(username) for username in usernames]
        
        # Execute with gather for maximum concurrency
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'error': str(result),
                    'username': usernames[i]
                })
            else:
                processed_results.append(result)
        
        return processed_results