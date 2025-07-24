#!/usr/bin/env python3
"""
🌈 Colorful Roblox Username Checker 🌈
Ultra-fast username validation with beautiful colors!
Compatible with Python 3.13+ and all environments
"""

import requests
import time
import threading
import queue
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple
import sys
from pathlib import Path
from colorama import init, Fore, Back, Style
import random

# Initialize colorama for cross-platform color support
init(autoreset=True)

class ColorfulUsernameChecker:
    """Ultra-fast username checker with beautiful color display."""
    
    def __init__(self, max_workers: int = 50):
        self.max_workers = max_workers
        self.session = requests.Session()
        
        # Configure session for better performance
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # Performance tracking
        self.results = []
        self.processed = 0
        self.start_time = None
        self.valid_usernames = []
        self.lock = threading.Lock()
        
        # Progress display settings
        self.last_progress_update = 0
        self.progress_update_interval = 0.3  # Update every 0.3 seconds for smooth animation
        
        # Color schemes
        self.colors = {
            'header': Fore.CYAN + Style.BRIGHT,
            'success': Fore.GREEN + Style.BRIGHT,
            'error': Fore.RED + Style.BRIGHT,
            'warning': Fore.YELLOW + Style.BRIGHT,
            'info': Fore.BLUE + Style.BRIGHT,
            'accent': Fore.MAGENTA + Style.BRIGHT,
            'highlight': Back.YELLOW + Fore.BLACK + Style.BRIGHT,
            'rainbow': [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.BLUE, Fore.MAGENTA]
        }

    def rainbow_text(self, text: str) -> str:
        """Create rainbow colored text."""
        result = ""
        for i, char in enumerate(text):
            color = self.colors['rainbow'][i % len(self.colors['rainbow'])]
            result += color + char
        return result + Style.RESET_ALL

    def print_header(self):
        """Print colorful header."""
        self.clear_console()
        header_lines = [
            "████████████████████████████████████████████████████████████████████████████████",
            "██                                                                            ██",
            "██   🌈 COLORFUL ROBLOX USERNAME CHECKER 🌈                                   ██",
            "██                                                                            ██",
            "██   Ultra-Fast • Multi-Threaded • Beautiful Colors • Real-Time Progress     ██",
            "██                                                                            ██",
            "████████████████████████████████████████████████████████████████████████████████"
        ]
        
        for line in header_lines:
            print(self.rainbow_text(line))
        print()

    def check_username(self, username: str) -> Dict:
        """Check a single username with colorful result."""
        url = f"https://auth.roblox.com/v1/usernames/validate?username={username}&birthday=01/01/2000"
        
        try:
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                code = data.get('code', -1)
                
                if code == 0:
                    return {
                        'username': username,
                        'status': 'VALID',
                        'code': code,
                        'color': self.colors['success'] + '✅ VALID',
                        'display_color': self.colors['success']
                    }
                elif code == 1:
                    return {
                        'username': username,
                        'status': 'TAKEN',
                        'code': code,
                        'color': self.colors['error'] + '❌ TAKEN',
                        'display_color': self.colors['error']
                    }
                elif code == 2:
                    return {
                        'username': username,
                        'status': 'CENSORED',
                        'code': code,
                        'color': self.colors['warning'] + '🚫 CENSORED',
                        'display_color': self.colors['warning']
                    }
                else:
                    return {
                        'username': username,
                        'status': f'UNKNOWN_{code}',
                        'code': code,
                        'color': self.colors['info'] + f'❓ UNKNOWN_{code}',
                        'display_color': self.colors['info']
                    }
            else:
                return {
                    'username': username,
                    'status': f'HTTP_{response.status_code}',
                    'code': response.status_code,
                    'color': self.colors['error'] + f'⚠️ HTTP_{response.status_code}',
                    'display_color': self.colors['error']
                }
                
        except Exception as e:
            return {
                'username': username,
                'status': 'ERROR',
                'code': -1,
                'color': self.colors['error'] + '💥 ERROR',
                'display_color': self.colors['error'],
                'error': str(e)
            }

    def clear_console(self):
        """Clear console screen."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def create_progress_bar(self, progress: float, width: int = 60) -> str:
        """Create a colorful progress bar."""
        filled = int(width * progress / 100)
        bar = ""
        
        # Rainbow progress bar
        for i in range(width):
            if i < filled:
                color = self.colors['rainbow'][i % len(self.colors['rainbow'])]
                bar += color + "█"
            else:
                bar += Fore.LIGHTBLACK_EX + "░"
        
        return bar + Style.RESET_ALL

    def animate_text(self, text: str, color: str) -> str:
        """Add pulsing animation to text."""
        return color + Style.BRIGHT + text + Style.RESET_ALL

    def display_progress(self, results: List[Dict], total: int, elapsed: float):
        """Display beautiful colorful progress information."""
        self.clear_console()
        
        progress = (len(results) / total) * 100
        rps = len(results) / elapsed if elapsed > 0 else 0
        
        # Count results
        counts = {'VALID': 0, 'TAKEN': 0, 'CENSORED': 0, 'ERROR': 0}
        for result in results:
            status = result['status']
            if status in counts:
                counts[status] += 1
            elif status.startswith('UNKNOWN') or status.startswith('HTTP') or status == 'ERROR':
                counts['ERROR'] += 1
        
        # Header
        self.print_header()
        
        # Progress section
        print(self.colors['header'] + "┌─" + "─" * 78 + "─┐")
        print(self.colors['header'] + "│" + self.animate_text("🚀 LIVE PROGRESS", self.colors['accent']).center(88) + self.colors['header'] + "│")
        print(self.colors['header'] + "└─" + "─" * 78 + "─┘")
        print()
        
        # Progress bar
        progress_bar = self.create_progress_bar(progress)
        print(f"{self.colors['info']}Progress: {progress_bar} {self.colors['accent']}{progress:.1f}%")
        print()
        
        # Statistics in colorful boxes
        print(self.colors['header'] + "┌─" + "─" * 38 + "┬─" + "─" * 38 + "─┐")
        print(self.colors['header'] + "│" + f"{self.colors['info']}📊 STATISTICS".center(48) + self.colors['header'] + "│" + f"{self.colors['accent']}⚡ PERFORMANCE".center(48) + self.colors['header'] + "│")
        print(self.colors['header'] + "├─" + "─" * 38 + "┼─" + "─" * 38 + "─┤")
        
        eta = ((total - len(results)) / rps) if rps > 0 else 0
        print(self.colors['header'] + "│" + f"{self.colors['success']}Processed: {len(results):,} / {total:,}".ljust(48) + self.colors['header'] + "│" + f"{self.colors['accent']}Speed: {rps:.1f} req/sec".ljust(48) + self.colors['header'] + "│")
        print(self.colors['header'] + "│" + f"{self.colors['info']}Time: {elapsed:.1f} seconds".ljust(48) + self.colors['header'] + "│" + f"{self.colors['warning']}ETA: {eta:.1f} seconds".ljust(48) + self.colors['header'] + "│")
        print(self.colors['header'] + "└─" + "─" * 38 + "┴─" + "─" * 38 + "─┘")
        print()
        
        # Results breakdown in colorful format
        print(self.colors['header'] + "┌─" + "─" * 78 + "─┐")
        print(self.colors['header'] + "│" + f"{self.colors['accent']}🔍 RESULTS BREAKDOWN".center(88) + self.colors['header'] + "│")
        print(self.colors['header'] + "├─" + "─" * 78 + "─┤")
        
        # Create colorful result display
        valid_text = f"{self.colors['success']}✅ Valid: {counts['VALID']:,}"
        taken_text = f"{self.colors['error']}❌ Taken: {counts['TAKEN']:,}"
        censored_text = f"{self.colors['warning']}🚫 Censored: {counts['CENSORED']:,}"
        error_text = f"{self.colors['info']}💥 Errors: {counts['ERROR']:,}"
        
        print(self.colors['header'] + "│" + f"{valid_text:<25} {taken_text:<25}".ljust(88) + self.colors['header'] + "│")
        print(self.colors['header'] + "│" + f"{censored_text:<25} {error_text:<25}".ljust(88) + self.colors['header'] + "│")
        print(self.colors['header'] + "└─" + "─" * 78 + "─┘")
        print()
        
        # Show valid usernames found with celebration
        if self.valid_usernames:
            print(self.colors['success'] + "🎉" * 80)
            print(self.animate_text(f"🌟 VALID USERNAMES FOUND ({len(self.valid_usernames)}) 🌟", self.colors['success']).center(80))
            print(self.colors['success'] + "🎉" * 80)
            
            # Display valid usernames in colorful columns
            display_count = min(15, len(self.valid_usernames))
            for i in range(0, display_count, 5):
                row = self.valid_usernames[i:i+5]
                colored_row = []
                for j, username in enumerate(row):
                    color = self.colors['rainbow'][(i + j) % len(self.colors['rainbow'])]
                    colored_row.append(f"{color}{username:<12}")
                print("   " + " ".join(colored_row))
            
            if len(self.valid_usernames) > 15:
                remaining = len(self.valid_usernames) - 15
                print(f"{self.colors['accent']}   ... and {remaining} more amazing usernames! 🚀")
            print()
        
        # Tips and controls
        tip_text = "💡 Press Ctrl+C to stop early and see results"
        print(self.colors['highlight'] + tip_text.center(80) + Style.RESET_ALL)
        print(self.rainbow_text("=" * 80))

    def process_usernames(self, usernames: List[str]) -> List[Dict]:
        """Process usernames with threading and beautiful display."""
        self.print_header()
        
        print(f"{self.colors['accent']}🚀 Starting to check {len(usernames):,} usernames with {self.max_workers} threads...")
        print(f"{self.colors['info']}💡 Use Ctrl+C to stop early and see results")
        
        # Animated countdown
        for i in range(3, 0, -1):
            print(f"{self.colors['warning']}Starting in {i}..." + " " * 20, end="\r")
            time.sleep(1)
        
        self.start_time = time.time()
        results = []
        
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_username = {
                    executor.submit(self.check_username, username): username 
                    for username in usernames
                }
                
                for future in as_completed(future_to_username):
                    result = future.result()
                    
                    with self.lock:
                        results.append(result)
                        self.processed += 1
                        
                        if result['status'] == 'VALID':
                            self.valid_usernames.append(result['username'])
                    
                    current_time = time.time()
                    if (current_time - self.last_progress_update > self.progress_update_interval or 
                        result['status'] == 'VALID'):
                        
                        elapsed = current_time - self.start_time
                        self.display_progress(results, len(usernames), elapsed)
                        self.last_progress_update = current_time
            
        except KeyboardInterrupt:
            print(f"\n\n{self.colors['warning']}⏹️ Stopping early... Preparing colorful results...")
            time.sleep(1)
        
        return results

    def print_summary(self, results: List[Dict]) -> None:
        """Print beautiful, colorful summary of results."""
        self.clear_console()
        
        total_time = time.time() - self.start_time
        avg_rps = len(results) / total_time if total_time > 0 else 0
        
        # Count results
        counts = {'VALID': 0, 'TAKEN': 0, 'CENSORED': 0, 'ERROR': 0}
        valid_usernames = []
        
        for result in results:
            status = result['status']
            if status in counts:
                counts[status] += 1
            elif status.startswith('UNKNOWN') or status.startswith('HTTP') or status == 'ERROR':
                counts['ERROR'] += 1
            
            if status == 'VALID':
                valid_usernames.append(result['username'])
        
        # Celebration header
        print(self.rainbow_text("🎊" * 80))
        print(self.animate_text("🎯 FINAL RESULTS - COLORFUL ROBLOX USERNAME CHECKER 🎯", self.colors['header']).center(80))
        print(self.rainbow_text("🎊" * 80))
        print()
        
        # Performance summary box
        print(self.colors['header'] + "┌─" + "─" * 78 + "─┐")
        print(self.colors['header'] + "│" + f"{self.colors['accent']}📊 PERFORMANCE SUMMARY".center(88) + self.colors['header'] + "│")
        print(self.colors['header'] + "├─" + "─" * 78 + "─┤")
        
        original_time_estimate = len(results) * 0.05
        speedup = original_time_estimate / total_time if total_time > 0 else 1
        
        performance_lines = [
            f"{self.colors['info']}Total Processed:    {len(results):,} usernames",
            f"{self.colors['success']}Processing Time:    {total_time:.2f} seconds",
            f"{self.colors['accent']}Average Speed:      {avg_rps:.1f} usernames/second",
            f"{self.colors['warning']}Speedup Factor:     {speedup:.1f}x faster than basic script"
        ]
        
        for line in performance_lines:
            print(self.colors['header'] + "│" + f"   {line}".ljust(88) + self.colors['header'] + "│")
        
        print(self.colors['header'] + "└─" + "─" * 78 + "─┘")
        print()
        
        # Results breakdown
        print(self.colors['header'] + "┌─" + "─" * 78 + "─┐")
        print(self.colors['header'] + "│" + f"{self.colors['accent']}🔍 RESULTS BREAKDOWN".center(88) + self.colors['header'] + "│")
        print(self.colors['header'] + "├─" + "─" * 78 + "─┤")
        
        total_checked = sum(counts.values())
        success_rate = ((total_checked - counts['ERROR']) / total_checked * 100) if total_checked > 0 else 0
        
        result_lines = [
            f"{self.colors['success']}✅ Valid Usernames:     {counts['VALID']:,}",
            f"{self.colors['error']}❌ Taken Usernames:     {counts['TAKEN']:,}",
            f"{self.colors['warning']}🚫 Censored Usernames:  {counts['CENSORED']:,}",
            f"{self.colors['info']}💥 Errors/Timeouts:     {counts['ERROR']:,}",
            f"{self.colors['accent']}✨ Success Rate:        {success_rate:.1f}%"
        ]
        
        for line in result_lines:
            print(self.colors['header'] + "│" + f"   {line}".ljust(88) + self.colors['header'] + "│")
        
        print(self.colors['header'] + "└─" + "─" * 78 + "─┘")
        print()
        
        # Valid usernames celebration
        if valid_usernames:
            print(self.colors['success'] + "🌟" * 80)
            print(self.animate_text(f"🎉 VALID USERNAMES FOUND ({len(valid_usernames)} total) 🎉", self.colors['success']).center(80))
            print(self.colors['success'] + "🌟" * 80)
            print()
            
            # Display in rainbow columns
            cols = 5
            for i in range(0, len(valid_usernames), cols):
                row = valid_usernames[i:i+cols]
                colored_row = []
                for j, username in enumerate(row):
                    color = self.colors['rainbow'][(i + j) % len(self.colors['rainbow'])]
                    colored_row.append(f"{color}{username:<15}")
                print("   " + " ".join(colored_row))
            
            print()
            rarity = (counts['VALID'] / len(results)) * 100
            print(f"{self.colors['accent']}💎 Valid username rarity: {rarity:.3f}% ({counts['VALID']} out of {len(results):,})")
            
            if rarity < 0.1:
                print(f"{self.colors['success']}🏆 EXCELLENT! These usernames are ultra-rare gems! 💎")
            elif rarity < 0.5:
                print(f"{self.colors['warning']}🎯 GREAT! Found some rare and valuable usernames! ⭐")
        else:
            print(f"{self.colors['error']}😢 NO VALID USERNAMES FOUND")
            print(f"{self.colors['info']}💡 Try running with a different set of usernames or patterns")
        
        print()
        print(self.rainbow_text("🎊" * 80))

    def save_results(self, results: List[Dict], base_filename: str = "colorful_results") -> None:
        """Save results with colorful console output."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        try:
            # Save files (same logic as before but with colorful output)
            json_filename = f"{base_filename}_{timestamp}.json"
            txt_filename = f"{base_filename}_{timestamp}.txt"
            csv_filename = f"{base_filename}_{timestamp}.csv"
            
            # Save JSON
            with open(json_filename, 'w') as f:
                json.dump(results, f, indent=2)
            
            # Save TXT summary
            with open(txt_filename, 'w') as f:
                f.write("🌈 COLORFUL ROBLOX USERNAME CHECKER RESULTS 🌈\n")
                f.write("=" * 60 + "\n\n")
                
                counts = {'VALID': 0, 'TAKEN': 0, 'CENSORED': 0, 'ERROR': 0}
                valid_usernames = []
                
                for result in results:
                    status = result['status']
                    if status in counts:
                        counts[status] += 1
                    elif status.startswith('UNKNOWN') or status.startswith('HTTP') or status == 'ERROR':
                        counts['ERROR'] += 1
                    
                    if status == 'VALID':
                        valid_usernames.append(result['username'])
                
                total_time = time.time() - self.start_time
                avg_rps = len(results) / total_time if total_time > 0 else 0
                
                f.write(f"SUMMARY:\n")
                f.write(f"Total processed: {len(results):,}\n")
                f.write(f"Processing time: {total_time:.2f} seconds\n")
                f.write(f"Average speed: {avg_rps:.1f} usernames/second\n\n")
                
                f.write(f"RESULTS:\n")
                f.write(f"Valid usernames: {counts['VALID']:,}\n")
                f.write(f"Taken usernames: {counts['TAKEN']:,}\n")
                f.write(f"Censored usernames: {counts['CENSORED']:,}\n")
                f.write(f"Errors: {counts['ERROR']:,}\n\n")
                
                if valid_usernames:
                    f.write(f"VALID USERNAMES ({len(valid_usernames)} found):\n")
                    f.write("-" * 40 + "\n")
                    for username in valid_usernames:
                        f.write(f"{username}\n")
                else:
                    f.write("No valid usernames found.\n")
            
            # Save CSV
            with open(csv_filename, 'w') as f:
                f.write("Username,Status,Code,Error\n")
                for result in results:
                    error = result.get('error', '').replace(',', ';') if result.get('error') else ''
                    f.write(f"{result['username']},{result['status']},{result.get('code', '')},{error}\n")
            
            print(f"\n{self.colors['success']}💾 COLORFUL RESULTS SAVED:")
            print(f"{self.colors['info']}   📄 Summary: {txt_filename}")
            print(f"{self.colors['accent']}   📊 Spreadsheet: {csv_filename}")
            print(f"{self.colors['warning']}   📋 Raw data: {json_filename}")
            
        except Exception as e:
            print(f"{self.colors['error']}❌ Error saving results: {e}")

def main():
    """Main function with colorful interface."""
    init()  # Initialize colorama
    
    # Colorful welcome
    print(Fore.CYAN + Style.BRIGHT + "🌈" * 80)
    print(Fore.YELLOW + Style.BRIGHT + "Welcome to the Colorful Roblox Username Checker!".center(80))
    print(Fore.CYAN + Style.BRIGHT + "🌈" * 80)
    print()
    
    # Check if usernames file exists
    username_file = "usernames.txt"
    if not Path(username_file).exists():
        print(f"{Fore.RED}❌ File '{username_file}' not found!")
        print(f"{Fore.YELLOW}💡 Please create a file with usernames (one per line)")
        return
    
    # Load usernames
    try:
        with open(username_file, 'r') as f:
            usernames = [line.strip() for line in f if line.strip()]
        
        print(f"{Fore.GREEN}✅ Loaded {len(usernames):,} usernames from {username_file}")
    except Exception as e:
        print(f"{Fore.RED}❌ Error loading usernames: {e}")
        return
    
    # Get thread count with colorful input
    print(f"\n{Fore.CYAN}🔧 How many threads do you want to use?")
    print(f"{Fore.YELLOW}💡 Recommended: 30-50 (more = faster, but may hit rate limits)")
    
    try:
        max_workers = int(input(f"{Fore.MAGENTA}Enter threads (default 50): ") or "50")
        max_workers = max(1, min(100, max_workers))  # Limit between 1-100
    except ValueError:
        max_workers = 50
        print(f"{Fore.YELLOW}Using default: 50 threads")
    
    # Create and run checker
    print(f"\n{Fore.GREEN}🚀 Initializing colorful checker with {max_workers} threads...")
    
    checker = ColorfulUsernameChecker(max_workers=max_workers)
    results = checker.process_usernames(usernames)
    
    # Show final summary
    checker.print_summary(results)
    
    # Save results
    checker.save_results(results)
    
    print(f"\n{Fore.CYAN + Style.BRIGHT}🎉 Thank you for using the Colorful Username Checker! 🎉")
    print(f"{Fore.YELLOW}Press Enter to exit...")
    input()

if __name__ == "__main__":
    main()