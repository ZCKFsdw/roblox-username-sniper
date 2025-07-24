#!/usr/bin/env python3
"""
Simple, Fast Roblox Username Checker
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

# Initialize colorama for cross-platform color support
init(autoreset=True)

class SimpleUsernameChecker:
    """Simple but fast username checker using threads."""
    
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
        self.progress_update_interval = 0.5  # Update every 0.5 seconds
        
    def check_username(self, username: str) -> Dict:
        """Check a single username."""
        url = f"https://auth.roblox.com/v1/usernames/validate?Username={username}&Birthday=2000-01-01"
        
        try:
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                code = data.get("code")
                
                if code == 0:
                    status = "VALID"
                    color = "🟢"
                elif code == 1:
                    status = "TAKEN"
                    color = "🔴"
                elif code == 2:
                    status = "CENSORED"
                    color = "🟡"
                else:
                    status = f"UNKNOWN({code})"
                    color = "⚪"
                    
                return {
                    'username': username,
                    'status': status,
                    'code': code,
                    'color': color,
                    'error': None
                }
            else:
                return {
                    'username': username,
                    'status': 'ERROR',
                    'code': None,
                    'color': '❌',
                    'error': f'HTTP {response.status_code}'
                }
                
        except Exception as e:
            return {
                'username': username,
                'status': 'ERROR',
                'code': None,
                'color': '❌',
                'error': str(e)
            }
    
    def clear_console(self):
        """Clear console screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def display_progress(self, results: List[Dict], total: int, elapsed: float):
        """Display clean progress information."""
        self.clear_console()
        
        progress = (len(results) / total) * 100
        rps = len(results) / elapsed if elapsed > 0 else 0
        
        # Count results
        counts = {'VALID': 0, 'TAKEN': 0, 'CENSORED': 0, 'ERROR': 0}
        for result in results:
            status = result['status']
            if status in counts:
                counts[status] += 1
            elif status.startswith('UNKNOWN'):
                counts['ERROR'] += 1
        
        print(Fore.CYAN + Style.BRIGHT + "=" * 80)
        print(Fore.YELLOW + Style.BRIGHT + "🚀 ROBLOX USERNAME CHECKER - LIVE PROGRESS")
        print(Fore.CYAN + Style.BRIGHT + "=" * 80)
        print()
        
        # Colorful progress bar
        bar_length = 50
        filled_length = int(bar_length * progress / 100)
        bar = Fore.GREEN + "█" * filled_length + Fore.LIGHTBLACK_EX + "░" * (bar_length - filled_length)
        print(f"{Fore.BLUE}Progress: [{bar}{Fore.BLUE}] {Fore.MAGENTA + Style.BRIGHT}{progress:.1f}%")
        print()
        
        # Statistics in colorful format
        print(f"{Fore.CYAN + Style.BRIGHT}📊 STATISTICS:")
        print(f"{Fore.WHITE}   Processed:     {Fore.GREEN}{len(results):,}{Fore.WHITE} / {Fore.CYAN}{total:,}")
        print(f"{Fore.WHITE}   Speed:         {Fore.YELLOW}{rps:.1f}{Fore.WHITE} usernames/second")
        print(f"{Fore.WHITE}   Time elapsed:  {Fore.BLUE}{elapsed:.1f}{Fore.WHITE} seconds")
        print(f"{Fore.WHITE}   ETA:           {Fore.MAGENTA}{((total - len(results)) / rps) if rps > 0 else 0:.1f}{Fore.WHITE} seconds")
        print()
        
        # Colorful results breakdown
        print(f"{Fore.CYAN + Style.BRIGHT}🔍 RESULTS BREAKDOWN:")
        print(f"{Fore.GREEN}   🟢 Valid:      {counts['VALID']:,}")
        print(f"{Fore.RED}   🔴 Taken:      {counts['TAKEN']:,}")
        print(f"{Fore.YELLOW}   🟡 Censored:   {counts['CENSORED']:,}")
        print(f"{Fore.LIGHTRED_EX}   ❌ Errors:     {counts['ERROR']:,}")
        print()
        
        # Show valid usernames found with colors
        if self.valid_usernames:
            print(f"{Fore.GREEN + Style.BRIGHT}🎉 VALID USERNAMES FOUND ({len(self.valid_usernames)}):")
            for i, username in enumerate(self.valid_usernames[-10:]):  # Show last 10
                colors = [Fore.GREEN, Fore.CYAN, Fore.YELLOW, Fore.MAGENTA, Fore.BLUE]
                color = colors[i % len(colors)]
                print(f"{color}   ✓ {username}")
            if len(self.valid_usernames) > 10:
                print(f"{Fore.CYAN}   ... and {len(self.valid_usernames) - 10} more!")
            print()
        
        print(f"{Back.YELLOW + Fore.BLACK + Style.BRIGHT}💡 Press Ctrl+C to stop early{Style.RESET_ALL}")
        print(Fore.CYAN + Style.BRIGHT + "=" * 80)
    
    def process_usernames(self, usernames: List[str]) -> List[Dict]:
        """Process usernames with threading for speed."""
        print(f"🚀 Starting to check {len(usernames):,} usernames with {self.max_workers} threads...")
        print("💡 Use Ctrl+C to stop early and see results")
        time.sleep(2)  # Give user time to read
        
        self.start_time = time.time()
        results = []
        
        try:
            # Use ThreadPoolExecutor for concurrent processing
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks
                future_to_username = {
                    executor.submit(self.check_username, username): username 
                    for username in usernames
                }
                
                # Process completed tasks
                for future in as_completed(future_to_username):
                    result = future.result()
                    
                    with self.lock:
                        results.append(result)
                        self.processed += 1
                        
                        # Track valid usernames
                        if result['status'] == 'VALID':
                            self.valid_usernames.append(result['username'])
                    
                    # Update display every 0.5 seconds or for valid usernames
                    current_time = time.time()
                    if (current_time - self.last_progress_update > self.progress_update_interval or 
                        result['status'] == 'VALID'):
                        
                        elapsed = current_time - self.start_time
                        self.display_progress(results, len(usernames), elapsed)
                        self.last_progress_update = current_time
            
        except KeyboardInterrupt:
            print("\n\n⏹️ Stopping early... Preparing results...")
            time.sleep(1)
        
        return results
    
    def print_summary(self, results: List[Dict]) -> None:
        """Print clean, well-formatted summary of results."""
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
            elif status.startswith('UNKNOWN'):
                counts['ERROR'] += 1
            
            if status == 'VALID':
                valid_usernames.append(result['username'])
        
        print(Fore.CYAN + Style.BRIGHT + "=" * 80)
        print(Fore.YELLOW + Style.BRIGHT + "🎯 FINAL RESULTS - COLORFUL ROBLOX USERNAME CHECKER")
        print(Fore.CYAN + Style.BRIGHT + "=" * 80)
        print()
        
        # Colorful performance metrics
        print(f"{Fore.CYAN + Style.BRIGHT}📊 PERFORMANCE SUMMARY:")
        print(f"{Fore.WHITE}   Total Processed:    {Fore.GREEN + Style.BRIGHT}{len(results):,}{Fore.WHITE} usernames")
        print(f"{Fore.WHITE}   Processing Time:    {Fore.BLUE + Style.BRIGHT}{total_time:.2f}{Fore.WHITE} seconds")
        print(f"{Fore.WHITE}   Average Speed:      {Fore.YELLOW + Style.BRIGHT}{avg_rps:.1f}{Fore.WHITE} usernames/second")
        
        # Performance comparison
        original_time_estimate = len(results) * 0.05  # Original ~50ms per request
        speedup = original_time_estimate / total_time if total_time > 0 else 1
        print(f"{Fore.WHITE}   Speedup Factor:     {Fore.MAGENTA + Style.BRIGHT}{speedup:.1f}x{Fore.WHITE} faster than basic script")
        print()
        
        # Colorful results breakdown
        print(f"{Fore.CYAN + Style.BRIGHT}🔍 RESULTS BREAKDOWN:")
        total_checked = sum(counts.values())
        success_rate = ((total_checked - counts['ERROR']) / total_checked * 100) if total_checked > 0 else 0
        
        print(f"{Fore.GREEN}   🟢 Valid Usernames:     {counts['VALID']:,}")
        print(f"{Fore.RED}   🔴 Taken Usernames:     {counts['TAKEN']:,}")
        print(f"{Fore.YELLOW}   🟡 Censored Usernames:  {counts['CENSORED']:,}")
        print(f"{Fore.LIGHTRED_EX}   ❌ Errors/Timeouts:     {counts['ERROR']:,}")
        print(f"{Fore.CYAN}   ✅ Success Rate:        {Fore.GREEN + Style.BRIGHT}{success_rate:.1f}%")
        print()
        
        # Colorful valid usernames section
        if valid_usernames:
            print(f"{Fore.GREEN + Style.BRIGHT}🎉 VALID USERNAMES FOUND ({len(valid_usernames)} total):")
            print(f"{Fore.GREEN}-" * 50)
            
            # Display in colorful columns
            cols = 4
            colors = [Fore.GREEN, Fore.CYAN, Fore.YELLOW, Fore.MAGENTA, Fore.BLUE]
            for i in range(0, len(valid_usernames), cols):
                row = valid_usernames[i:i+cols]
                formatted_row = []
                for j, username in enumerate(row):
                    color = colors[(i + j) % len(colors)]
                    formatted_row.append(f"{color + Style.BRIGHT}{username:<12}")
                print("   " + " ".join(formatted_row))
            
            print(f"{Fore.GREEN}-" * 50)
            print(f"{Fore.WHITE}   Total valid usernames: {Fore.GREEN + Style.BRIGHT}{len(valid_usernames)}")
        else:
            print(f"{Fore.RED + Style.BRIGHT}😞 NO VALID USERNAMES FOUND")
            print(f"{Fore.YELLOW}   Try running with a different set of usernames")
        
        print()
        print(Fore.CYAN + Style.BRIGHT + "=" * 80)
        
        # Colorful insights
        if counts['VALID'] > 0:
            rarity = (counts['VALID'] / len(results)) * 100
            print(f"{Fore.MAGENTA + Style.BRIGHT}💡 INSIGHTS:")
            print(f"{Fore.WHITE}   Valid username rarity: {Fore.CYAN + Style.BRIGHT}{rarity:.3f}%{Fore.WHITE} ({Fore.GREEN}{counts['VALID']}{Fore.WHITE} out of {Fore.BLUE}{len(results):,}{Fore.WHITE})")
            if rarity < 0.1:
                print(f"{Fore.GREEN + Style.BRIGHT}   🏆 This is excellent! Valid usernames are very rare.")
            elif rarity < 0.5:
                print(f"{Fore.YELLOW + Style.BRIGHT}   🎯 Good results! Found some rare valid usernames.")
        
        print(Fore.CYAN + Style.BRIGHT + "=" * 80)
    
    def save_results(self, results: List[Dict], base_filename: str = "username_results") -> None:
        """Save results to multiple easy-to-read formats."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        try:
            # Save detailed JSON
            json_filename = f"{base_filename}_{timestamp}.json"
            with open(json_filename, 'w') as f:
                json.dump(results, f, indent=2)
            
            # Save clean text summary
            txt_filename = f"{base_filename}_{timestamp}.txt"
            with open(txt_filename, 'w') as f:
                f.write("ROBLOX USERNAME CHECKER RESULTS\n")
                f.write("=" * 50 + "\n\n")
                
                # Count results
                counts = {'VALID': 0, 'TAKEN': 0, 'CENSORED': 0, 'ERROR': 0}
                valid_usernames = []
                
                for result in results:
                    status = result['status']
                    if status in counts:
                        counts[status] += 1
                    elif status.startswith('UNKNOWN'):
                        counts['ERROR'] += 1
                    
                    if status == 'VALID':
                        valid_usernames.append(result['username'])
                
                # Write summary
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
                
                # Write valid usernames
                if valid_usernames:
                    f.write(f"VALID USERNAMES ({len(valid_usernames)} found):\n")
                    f.write("-" * 30 + "\n")
                    for username in valid_usernames:
                        f.write(f"{username}\n")
                else:
                    f.write("No valid usernames found.\n")
            
            # Save CSV for easy analysis
            csv_filename = f"{base_filename}_{timestamp}.csv"
            with open(csv_filename, 'w') as f:
                f.write("Username,Status,Code,Error\n")
                for result in results:
                    error = result.get('error', '').replace(',', ';') if result.get('error') else ''
                    f.write(f"{result['username']},{result['status']},{result.get('code', '')},{error}\n")
            
            print(f"\n{Fore.GREEN + Style.BRIGHT}💾 COLORFUL RESULTS SAVED:")
            print(f"{Fore.CYAN}   📄 Summary: {Fore.YELLOW}{txt_filename}")
            print(f"{Fore.CYAN}   📊 Spreadsheet: {Fore.MAGENTA}{csv_filename}")
            print(f"{Fore.CYAN}   📋 Raw data: {Fore.BLUE}{json_filename}")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error saving results: {e}")

def load_usernames(filename: str = "usernames.txt") -> List[str]:
    """Load usernames from file."""
    try:
        with open(filename, 'r') as f:
            usernames = [line.strip() for line in f if line.strip()]
        return usernames
    except FileNotFoundError:
        print(f"❌ File '{filename}' not found!")
        print("📝 Please create a file named 'usernames.txt' with usernames (one per line)")
        return []
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return []

def main():
    """Main function with colorful interface."""
    init()  # Initialize colorama
    
    # Colorful welcome
    print(Fore.CYAN + Style.BRIGHT + "🌈" * 60)
    print(Fore.YELLOW + Style.BRIGHT + "🚀 COLORFUL SIMPLE ROBLOX USERNAME CHECKER 🚀")
    print(Fore.GREEN + "Compatible with Python 3.13+ and all environments")
    print(Fore.CYAN + Style.BRIGHT + "🌈" * 60)
    print()
    
    # Load usernames
    usernames = load_usernames()
    if not usernames:
        return
    
    print(f"{Fore.GREEN + Style.BRIGHT}📂 Loaded {len(usernames):,} usernames")
    
    # Ask user for number of threads with colorful input
    print(f"\n{Fore.CYAN + Style.BRIGHT}🔧 How many threads do you want to use?")
    print(f"{Fore.YELLOW}💡 Recommended: 30-50 (more = faster, but may hit rate limits)")
    
    try:
        max_workers = int(input(f"{Fore.MAGENTA}Enter threads (default 50, max 100): ") or "50")
        max_workers = min(max_workers, 100)  # Limit to prevent overwhelming
    except ValueError:
        max_workers = 50
        print(f"{Fore.YELLOW}Using default: 50 threads")
    
    # Create checker and process
    print(f"\n{Fore.GREEN + Style.BRIGHT}🚀 Initializing colorful checker with {max_workers} threads...")
    
    checker = SimpleUsernameChecker(max_workers=max_workers)
    results = checker.process_usernames(usernames)
    
    # Show summary
    checker.print_summary(results)
    
    # Ask if user wants to save results
    save = input(f"\n{Fore.CYAN}Save results to file? (y/n): ").lower().strip()
    if save in ['y', 'yes']:
        checker.save_results(results)
    
    print(f"\n{Fore.GREEN + Style.BRIGHT}🎉 Thank you for using the Colorful Username Checker!")
    print(f"{Fore.CYAN}Press Enter to exit...")
    input()

if __name__ == "__main__":
    main()