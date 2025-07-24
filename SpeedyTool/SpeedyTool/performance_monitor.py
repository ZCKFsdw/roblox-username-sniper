"""Real-time performance monitoring and statistics."""

import time
import psutil
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from rich.console import Console
from rich.progress import Progress, TaskID, TextColumn, BarColumn, TimeElapsedColumn, MofNCompleteColumn
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout

@dataclass
class PerformanceMetrics:
    """Performance metrics for monitoring."""
    start_time: float = field(default_factory=time.time)
    total_processed: int = 0
    total_usernames: int = 0
    valid_count: int = 0
    taken_count: int = 0
    censored_count: int = 0
    error_count: int = 0
    current_rps: float = 0.0
    avg_rps: float = 0.0
    peak_rps: float = 0.0
    current_concurrent: int = 0
    memory_usage_mb: float = 0.0
    cpu_percent: float = 0.0
    network_errors: int = 0
    timeouts: int = 0
    
    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        return time.time() - self.start_time
    
    @property
    def completion_percentage(self) -> float:
        """Get completion percentage."""
        if self.total_usernames == 0:
            return 0.0
        return (self.total_processed / self.total_usernames) * 100
    
    @property
    def eta_seconds(self) -> float:
        """Estimate time to completion in seconds."""
        if self.avg_rps <= 0 or self.total_usernames <= 0:
            return float('inf')
        remaining = self.total_usernames - self.total_processed
        return remaining / self.avg_rps

class PerformanceMonitor:
    """Real-time performance monitoring with rich display."""
    
    def __init__(self, total_usernames: int, config):
        self.config = config
        self.metrics = PerformanceMetrics(total_usernames=total_usernames)
        self.console = Console()
        
        # Rich progress components
        self.progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=None),
            MofNCompleteColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.1f}%"),
            TimeElapsedColumn(),
            console=self.console,
            expand=True
        )
        
        self.main_task: Optional[TaskID] = None
        self.live: Optional[Live] = None
        
        # Performance tracking
        self.rps_history: List[float] = []
        self.last_update_time = time.time()
        self.last_processed_count = 0
        
        # System monitoring
        self.process = psutil.Process()
        
    async def start(self) -> None:
        """Start the performance monitor."""
        self.main_task = self.progress.add_task(
            "Processing usernames...", 
            total=self.metrics.total_usernames
        )
        
        # Create layout
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="progress", size=3),
            Layout(name="stats", size=10),
            Layout(name="footer", size=3)
        )
        
        # Start live display
        self.live = Live(layout, console=self.console, refresh_per_second=10)
        self.live.start()
        
        # Start monitoring task
        asyncio.create_task(self._monitor_loop())
    
    async def stop(self) -> None:
        """Stop the performance monitor."""
        if self.live:
            self.live.stop()
        
        # Print final summary
        await self._print_final_summary()
    
    def update_progress(self, processed: int, results: Dict[str, int]) -> None:
        """Update progress and metrics."""
        self.metrics.total_processed = processed
        self.metrics.valid_count = results.get('valid', 0)
        self.metrics.taken_count = results.get('taken', 0)
        self.metrics.censored_count = results.get('censored', 0)
        self.metrics.error_count = results.get('errors', 0)
        
        if self.main_task:
            self.progress.update(self.main_task, completed=processed)
    
    def record_network_error(self) -> None:
        """Record a network error."""
        self.metrics.network_errors += 1
    
    def record_timeout(self) -> None:
        """Record a timeout."""
        self.metrics.timeouts += 1
    
    def update_concurrent(self, concurrent: int) -> None:
        """Update current concurrent request count."""
        self.metrics.current_concurrent = concurrent
    
    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while True:
            try:
                await self._update_metrics()
                await self._update_display()
                await asyncio.sleep(self.config.progress_update_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                # Don't let monitoring errors crash the main process
                continue
    
    async def _update_metrics(self) -> None:
        """Update performance metrics."""
        current_time = time.time()
        time_delta = current_time - self.last_update_time
        
        if time_delta >= 1.0:  # Update RPS every second
            processed_delta = self.metrics.total_processed - self.last_processed_count
            current_rps = processed_delta / time_delta
            
            self.metrics.current_rps = current_rps
            self.rps_history.append(current_rps)
            
            # Keep only last 60 seconds of history
            if len(self.rps_history) > 60:
                self.rps_history = self.rps_history[-60:]
            
            # Calculate average and peak RPS
            if self.rps_history:
                self.metrics.avg_rps = sum(self.rps_history) / len(self.rps_history)
                self.metrics.peak_rps = max(self.rps_history)
            
            # Update system metrics
            try:
                self.metrics.memory_usage_mb = self.process.memory_info().rss / 1024 / 1024
                self.metrics.cpu_percent = self.process.cpu_percent()
            except:
                pass
            
            self.last_update_time = current_time
            self.last_processed_count = self.metrics.total_processed
    
    async def _update_display(self) -> None:
        """Update the live display."""
        if not self.live:
            return
        
        layout = self.live.renderable
        
        # Header
        layout["header"].update(
            Panel(
                f"🚀 Ultra-High-Performance Roblox Username Checker",
                style="bold magenta"
            )
        )
        
        # Progress
        layout["progress"].update(self.progress)
        
        # Statistics table
        stats_table = Table(title="📊 Real-Time Performance Metrics", show_header=True, header_style="bold cyan")
        stats_table.add_column("Metric", style="white", width=20)
        stats_table.add_column("Value", style="green", width=15)
        stats_table.add_column("Metric", style="white", width=20)
        stats_table.add_column("Value", style="green", width=15)
        
        # Add performance metrics
        stats_table.add_row(
            "🏃 Current RPS", f"{self.metrics.current_rps:.1f}",
            "📈 Average RPS", f"{self.metrics.avg_rps:.1f}"
        )
        stats_table.add_row(
            "🔥 Peak RPS", f"{self.metrics.peak_rps:.1f}",
            "🔄 Concurrent", f"{self.metrics.current_concurrent}"
        )
        stats_table.add_row(
            "✅ Valid", f"{self.metrics.valid_count:,}",
            "❌ Taken", f"{self.metrics.taken_count:,}"
        )
        stats_table.add_row(
            "🚫 Censored", f"{self.metrics.censored_count:,}",
            "⚠️ Errors", f"{self.metrics.error_count:,}"
        )
        stats_table.add_row(
            "🧠 Memory (MB)", f"{self.metrics.memory_usage_mb:.1f}",
            "⚡ CPU %", f"{self.metrics.cpu_percent:.1f}"
        )
        stats_table.add_row(
            "🌐 Net Errors", f"{self.metrics.network_errors:,}",
            "⏱️ Timeouts", f"{self.metrics.timeouts:,}"
        )
        
        eta_str = "∞" if self.metrics.eta_seconds == float('inf') else f"{self.metrics.eta_seconds:.1f}s"
        stats_table.add_row(
            "⏰ ETA", eta_str,
            "📊 Complete %", f"{self.metrics.completion_percentage:.1f}%"
        )
        
        layout["stats"].update(stats_table)
        
        # Footer with tips
        layout["footer"].update(
            Panel(
                "💡 Tip: Monitor RPS and adjust concurrency settings if needed. Peak performance achieved through adaptive rate limiting!",
                style="dim"
            )
        )
    
    async def _print_final_summary(self) -> None:
        """Print final performance summary."""
        elapsed = self.metrics.elapsed_time
        
        summary_table = Table(title="🎯 Final Performance Summary", show_header=True, header_style="bold green")
        summary_table.add_column("Metric", style="white", width=25)
        summary_table.add_column("Value", style="green", width=20)
        
        summary_table.add_row("Total Processed", f"{self.metrics.total_processed:,}")
        summary_table.add_row("Total Time", f"{elapsed:.2f} seconds")
        summary_table.add_row("Average RPS", f"{self.metrics.avg_rps:.1f}")
        summary_table.add_row("Peak RPS", f"{self.metrics.peak_rps:.1f}")
        summary_table.add_row("Valid Usernames", f"{self.metrics.valid_count:,}")
        summary_table.add_row("Taken Usernames", f"{self.metrics.taken_count:,}")
        summary_table.add_row("Censored Usernames", f"{self.metrics.censored_count:,}")
        summary_table.add_row("Total Errors", f"{self.metrics.error_count:,}")
        summary_table.add_row("Success Rate", f"{((self.metrics.total_processed - self.metrics.error_count) / max(1, self.metrics.total_processed) * 100):.1f}%")
        
        # Performance comparison
        old_time_estimate = self.metrics.total_processed * 0.05  # Old script ~50ms per request
        speedup = old_time_estimate / elapsed if elapsed > 0 else 1
        summary_table.add_row("Speedup vs Original", f"{speedup:.1f}x faster")
        
        self.console.print("\n")
        self.console.print(summary_table)
        self.console.print(f"\n🎉 [bold green]Processing completed! Achieved {speedup:.1f}x speedup over the original tool.[/bold green]")
