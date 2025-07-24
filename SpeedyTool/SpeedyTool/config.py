"""Configuration settings for the ultra-high-performance Roblox username checker."""

import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    """Configuration class for the username checker."""
    
    # Performance settings - Enhanced for ultra-speed
    max_concurrent_requests: int = 300
    min_concurrent_requests: int = 100
    initial_concurrent_requests: int = 200
    
    # Rate limiting - Optimized for maximum speed
    base_delay: float = 0.0001  # 0.1ms base delay
    max_delay: float = 0.5     # 0.5 second max delay
    backoff_factor: float = 1.2
    
    # Connection settings - Optimized for speed
    total_timeout: int = 15
    connect_timeout: int = 5
    read_timeout: int = 5
    
    # Retry settings
    max_retries: int = 3
    retry_delay: float = 0.1
    
    # Batch settings - Increased for better throughput
    batch_size: int = 250
    
    # File settings
    input_file: str = "usernames.txt"
    output_file: Optional[str] = None
    
    # API settings
    api_url: str = "https://auth.roblox.com/v1/usernames/validate"
    birthday: str = "2000-01-01"
    
    # Performance monitoring
    progress_update_interval: float = 0.1  # Update every 100ms
    enable_detailed_logging: bool = True
    
    # Memory management
    chunk_size: int = 1000  # Process usernames in chunks
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Create config from environment variables with defaults."""
        return cls(
            max_concurrent_requests=int(os.getenv('MAX_CONCURRENT', 150)),
            min_concurrent_requests=int(os.getenv('MIN_CONCURRENT', 50)),
            initial_concurrent_requests=int(os.getenv('INITIAL_CONCURRENT', 100)),
            base_delay=float(os.getenv('BASE_DELAY', 0.001)),
            max_delay=float(os.getenv('MAX_DELAY', 1.0)),
            total_timeout=int(os.getenv('TOTAL_TIMEOUT', 30)),
            input_file=os.getenv('INPUT_FILE', 'usernames.txt'),
            output_file=os.getenv('OUTPUT_FILE'),
            enable_detailed_logging=os.getenv('DETAILED_LOGGING', 'true').lower() == 'true'
        )
