"""Ultra-high-performance async username checker with intelligent optimizations."""

import asyncio
import aiohttp
import aiofiles
import time
import ujson
from typing import List, Dict, Optional, Tuple, AsyncGenerator
from dataclasses import dataclass
from pathlib import Path

from config import Config
from rate_limiter import AdaptiveRateLimiter
from performance_monitor import PerformanceMonitor
from advanced_optimizations import AdvancedRequestOptimizer, UltraFastBatchProcessor

@dataclass
class CheckResult:
    """Result of a username check."""
    username: str
    status: str  # 'valid', 'taken', 'censored', 'error'
    code: Optional[int] = None
    error_message: Optional[str] = None
    response_time: float = 0.0

class UltraUsernameChecker:
    """Ultra-high-performance async username checker."""
    
    def __init__(self, config: Config):
        self.config = config
        self.rate_limiter = AdaptiveRateLimiter(config)
        self.monitor: Optional[PerformanceMonitor] = None
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Advanced optimizations
        self.optimizer = AdvancedRequestOptimizer(config)
        self.batch_processor: Optional[UltraFastBatchProcessor] = None
        
        # Results tracking
        self.results: List[CheckResult] = []
        self.result_counts = {
            'valid': 0, 'taken': 0, 'censored': 0, 'errors': 0
        }
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self._create_session()
        await self.optimizer.create_session_pool(pool_size=5)  # Create session pool
        self.batch_processor = UltraFastBatchProcessor(self.optimizer, self.rate_limiter)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._close_session()
        await self.optimizer.close_session_pool()
    
    async def _create_session(self) -> None:
        """Create optimized aiohttp session."""
        # Ultra-optimized connector settings for maximum performance
        connector = aiohttp.TCPConnector(
            limit=1000,  # Total connection pool size
            limit_per_host=400,  # Connections per host
            ttl_dns_cache=600,  # DNS cache TTL (10 minutes)
            use_dns_cache=True,
            keepalive_timeout=60,  # Longer keepalive
            enable_cleanup_closed=True,
            force_close=False,
        )
        
        # Optimized timeout settings
        timeout = aiohttp.ClientTimeout(
            total=self.config.total_timeout,
            connect=self.config.connect_timeout,
            sock_read=self.config.read_timeout
        )
        
        # Custom headers to optimize requests
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
        }
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers,
            json_serialize=ujson.dumps,  # Use ultra-fast JSON
        )
    
    async def _close_session(self) -> None:
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
    
    async def load_usernames(self, file_path: str) -> List[str]:
        """Load usernames from file with streaming for memory efficiency."""
        usernames = []
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
                async for line in file:
                    username = line.strip()
                    if username:  # Skip empty lines
                        usernames.append(username)
        except FileNotFoundError:
            raise FileNotFoundError(f"Username file not found: {file_path}")
        except Exception as e:
            raise Exception(f"Error reading username file: {e}")
        
        return usernames
    
    async def check_username_batch(self, usernames: List[str]) -> List[CheckResult]:
        """Check a batch of usernames with ultra-fast processing."""
        if self.batch_processor:
            # Use the advanced batch processor
            raw_results = await self.batch_processor.process_batch_ultra_fast(usernames)
            
            # Convert raw results to CheckResult objects
            batch_results = []
            for i, result in enumerate(raw_results):
                username = usernames[i]
                
                if 'error' in result:
                    check_result = CheckResult(
                        username=username,
                        status='error',
                        error_message=result['error']
                    )
                    self.result_counts['errors'] += 1
                else:
                    code = result.get('code')
                    if code == 0:
                        status = 'valid'
                    elif code == 1:
                        status = 'taken'
                    elif code == 2:
                        status = 'censored'
                    else:
                        status = 'error'
                    
                    check_result = CheckResult(
                        username=username,
                        status=status,
                        code=code
                    )
                    self.result_counts[status] += 1
                
                batch_results.append(check_result)
            
            return batch_results
        else:
            # Fallback to original method
            return await self._check_username_batch_fallback(usernames)
    
    async def _check_username_batch_fallback(self, usernames: List[str]) -> List[CheckResult]:
        """Fallback batch processing method."""
        tasks = []
        for username in usernames:
            task = asyncio.create_task(self._check_single_username(username))
            tasks.append(task)
        
        # Execute all tasks concurrently and gather results
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle exceptions
        batch_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Handle exceptions
                error_result = CheckResult(
                    username=usernames[i],
                    status='error',
                    error_message=str(result)
                )
                batch_results.append(error_result)
                self.result_counts['errors'] += 1
            else:
                batch_results.append(result)
                self.result_counts[result.status] += 1
        
        return batch_results
    
    async def _check_single_username(self, username: str) -> CheckResult:
        """Check a single username with rate limiting and retry logic."""
        start_time = time.time()
        
        for attempt in range(self.config.max_retries + 1):
            try:
                # Apply rate limiting
                await self.rate_limiter.acquire()
                
                try:
                    # Make the API request
                    url = f"{self.config.api_url}?Username={username}&Birthday={self.config.birthday}"
                    
                    async with self.session.get(url) as response:
                        response_time = time.time() - start_time
                        
                        if response.status == 200:
                            try:
                                data = await response.json(loads=ujson.loads)
                                code = data.get("code")
                                
                                # Record success
                                self.rate_limiter.record_success(response_time)
                                
                                # Determine status based on code
                                if code == 0:
                                    status = 'valid'
                                elif code == 1:
                                    status = 'taken'
                                elif code == 2:
                                    status = 'censored'
                                else:
                                    status = 'error'
                                
                                return CheckResult(
                                    username=username,
                                    status=status,
                                    code=code,
                                    response_time=response_time
                                )
                            
                            except (ValueError, KeyError) as e:
                                # JSON parsing error
                                self.rate_limiter.record_error("json_error")
                                if attempt < self.config.max_retries:
                                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                                    continue
                                
                                return CheckResult(
                                    username=username,
                                    status='error',
                                    error_message=f"JSON parsing error: {e}",
                                    response_time=response_time
                                )
                        
                        elif response.status == 429:
                            # Rate limited
                            self.rate_limiter.record_error("429_rate_limit")
                            if self.monitor:
                                self.monitor.record_network_error()
                            
                            if attempt < self.config.max_retries:
                                await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                                continue
                        
                        else:
                            # Other HTTP error
                            self.rate_limiter.record_error(f"http_{response.status}")
                            if self.monitor:
                                self.monitor.record_network_error()
                            
                            if attempt < self.config.max_retries:
                                await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                                continue
                
                finally:
                    self.rate_limiter.release()
            
            except asyncio.TimeoutError:
                self.rate_limiter.record_error("timeout")
                if self.monitor:
                    self.monitor.record_timeout()
                
                if attempt < self.config.max_retries:
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                    continue
            
            except aiohttp.ClientError as e:
                self.rate_limiter.record_error("client_error")
                if self.monitor:
                    self.monitor.record_network_error()
                
                if attempt < self.config.max_retries:
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                    continue
        
        # All retries exhausted
        return CheckResult(
            username=username,
            status='error',
            error_message="Max retries exhausted",
            response_time=time.time() - start_time
        )
    
    async def process_usernames(self, usernames: List[str]) -> List[CheckResult]:
        """Process all usernames with batching and performance monitoring."""
        total_usernames = len(usernames)
        
        # Initialize performance monitor
        self.monitor = PerformanceMonitor(total_usernames, self.config)
        await self.monitor.start()
        
        try:
            all_results = []
            
            # Process usernames in chunks for memory efficiency
            for i in range(0, total_usernames, self.config.chunk_size):
                chunk = usernames[i:i + self.config.chunk_size]
                
                # Process chunk in smaller batches for optimal concurrency
                for j in range(0, len(chunk), self.config.batch_size):
                    batch = chunk[j:j + self.config.batch_size]
                    
                    # Update monitor with current concurrency
                    self.monitor.update_concurrent(self.rate_limiter.current_concurrent)
                    
                    # Process batch
                    batch_results = await self.check_username_batch(batch)
                    all_results.extend(batch_results)
                    
                    # Update progress
                    self.monitor.update_progress(len(all_results), self.result_counts)
            
            self.results = all_results
            return all_results
        
        finally:
            await self.monitor.stop()
    
    async def save_results(self, output_file: str) -> None:
        """Save results to file asynchronously."""
        try:
            async with aiofiles.open(output_file, 'w', encoding='utf-8') as file:
                await file.write("Username,Status,Code,ResponseTime,ErrorMessage\n")
                
                for result in self.results:
                    line = f"{result.username},{result.status},{result.code or ''},"
                    line += f"{result.response_time:.3f},{result.error_message or ''}\n"
                    await file.write(line)
                    
        except Exception as e:
            print(f"Error saving results: {e}")
    
    def print_summary(self) -> None:
        """Print a summary of results to console."""
        total = len(self.results)
        if total == 0:
            print("No usernames processed.")
            return
        
        print(f"\n📊 Processing Summary:")
        print(f"Total processed: {total:,}")
        print(f"✅ Valid: {self.result_counts['valid']:,}")
        print(f"❌ Taken: {self.result_counts['taken']:,}")
        print(f"🚫 Censored: {self.result_counts['censored']:,}")
        print(f"⚠️ Errors: {self.result_counts['errors']:,}")
        
        # Print some valid usernames if found
        valid_usernames = [r.username for r in self.results if r.status == 'valid']
        if valid_usernames:
            print(f"\n🎉 Found {len(valid_usernames)} valid usernames!")
            if len(valid_usernames) <= 10:
                print("Valid usernames:", ", ".join(valid_usernames))
            else:
                print("First 10 valid usernames:", ", ".join(valid_usernames[:10]))
