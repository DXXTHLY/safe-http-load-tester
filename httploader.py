#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DEV: GITHUB.COM/DXXTHLY

Advanced HTTP Load Tester

A professional-grade, asynchronous load testing tool for developers.
Features rate limiting, concurrency control, detailed performance statistics,
and support for various HTTP methods, custom headers, and data payloads.
"""

import asyncio
import aiohttp
import time
import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

# --- Dependencies Check ---
try:
    import numpy as np
    from tqdm.asyncio import tqdm
except ImportError:
    print("Error: Required packages are not installed.")
    print("Please run: pip install numpy tqdm aiohttp")
    sys.exit(1)

# --- ANSI Color Codes for a Beautiful CLI ---
class Colors:
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    UNDERLINE = '\033[4m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'

# --- Data Structures ---
@dataclass
class TestResult:
    """Holds the result of a single HTTP request."""
    status_code: int
    response_time: float
    response_size_bytes: int
    error: Optional[str] = None

# --- Statistics Calculator ---
class StatisticsCalculator:
    """Calculates and displays advanced performance metrics."""
    def __init__(self, results: List[TestResult], duration: float):
        self.results = results
        self.duration = duration

    def _get_response_times(self) -> List[float]:
        return [r.response_time for r in self.results if r.error is None]

    def print_summary(self):
        if not self.results:
            print(f"{Colors.RED}No results to display.{Colors.ENDC}")
            return

        total_reqs = len(self.results)
        successes = [r for r in self.results if 200 <= r.status_code < 400 and r.error is None]
        failures = [r for r in self.results if r.status_code >= 400 or r.error or r.status_code == -1]
        
        # Handle division by zero
        success_rate = (len(successes) / total_reqs * 100) if total_reqs > 0 else 0
        failure_rate = (len(failures) / total_reqs * 100) if total_reqs > 0 else 0
        
        total_data = sum(r.response_size_bytes for r in self.results)
        response_times = self._get_response_times()
        
        actual_rps = total_reqs / self.duration if self.duration > 0 else 0
        throughput_mbps = (total_data * 8) / (self.duration * 1_000_000) if self.duration > 0 else 0

        print("\n" + "=" * 60)
        print(f"{Colors.MAGENTA}{Colors.BOLD}            PERFORMANCE ANALYSIS REPORT             {Colors.ENDC}")
        print("=" * 60)
        
        print(f"{Colors.BLUE}{Colors.BOLD}Summary:{Colors.ENDC}")
        print(f"  {'Total Test Duration:':<25} {self.duration:.2f}s")
        print(f"  {'Total Requests Sent:':<25} {total_reqs}")
        print(f"  {'Actual Requests/Sec (RPS):':<25} {Colors.CYAN}{actual_rps:.2f}{Colors.ENDC}")
        print(f"  {'Total Data Transferred:':<25} {total_data/1_048_576:.2f} MB")
        print(f"  {'Throughput:':<25} {Colors.CYAN}{throughput_mbps:.2f} Mbps{Colors.ENDC}")
        
        print(f"\n{Colors.BLUE}{Colors.BOLD}Request Outcomes:{Colors.ENDC}")
        print(f"  {Colors.GREEN}{'Successful Requests:':<25}{Colors.ENDC} {len(successes)} ({success_rate:.1f}%)")
        print(f"  {Colors.RED}{'Failed Requests:':<25}{Colors.ENDC} {len(failures)} ({failure_rate:.1f}%)")

        if response_times:
            print(f"\n{Colors.BLUE}{Colors.BOLD}Latency Statistics (ms):{Colors.ENDC}")
            latencies_ms = [t * 1000 for t in response_times]
            print(f"  {'Average:':<15} {np.mean(latencies_ms):.2f}")
            print(f"  {'Median (p50):':<15} {np.percentile(latencies_ms, 50):.2f}")
            print(f"  {'Min | Max:':<15} {np.min(latencies_ms):.2f} | {np.max(latencies_ms):.2f}")
            print(f"  {'Standard Dev:':<15} {np.std(latencies_ms):.2f}")
            print(f"  {'p90:':<15} {Colors.YELLOW}{np.percentile(latencies_ms, 90):.2f}{Colors.ENDC}")
            print(f"  {'p95:':<15} {Colors.YELLOW}{np.percentile(latencies_ms, 95):.2f}{Colors.ENDC}")
            print(f"  {'p99:':<15} {Colors.RED}{np.percentile(latencies_ms, 99):.2f}{Colors.ENDC}")
            
            if len(latencies_ms) >= 10:  # Only show histogram if we have enough data points
                self._print_histogram(latencies_ms)
        else:
            print(f"\n{Colors.RED}No successful responses to calculate latency statistics.{Colors.ENDC}")
            
        self._print_breakdowns()

    def _print_histogram(self, latencies_ms: List[float]):
        print(f"\n{Colors.BLUE}{Colors.BOLD}Response Time Distribution (ms):{Colors.ENDC}")
        try:
            hist, bins = np.histogram(latencies_ms, bins=min(10, len(latencies_ms)))
            max_count = hist.max()
            for i in range(len(hist)):
                bar_width = int((hist[i] / max_count) * 40) if max_count > 0 else 0
                bar = '█' * bar_width
                print(f"  {bins[i]:<7.2f} - {bins[i+1]:<7.2f} | {Colors.CYAN}{bar:<40}{Colors.ENDC} ({hist[i]})")
        except Exception as e:
            print(f"  {Colors.YELLOW}Unable to generate histogram: {str(e)}{Colors.ENDC}")
            
    def _print_breakdowns(self):
        status_codes = {}
        errors = {}
        for r in self.results:
            status_codes[r.status_code] = status_codes.get(r.status_code, 0) + 1
            if r.error:
                errors[r.error] = errors.get(r.error, 0) + 1

        print(f"\n{Colors.BLUE}{Colors.BOLD}Status Code Breakdown:{Colors.ENDC}")
        for code, count in sorted(status_codes.items()):
            if code == -1:
                color = Colors.RED
                code_str = "Network Error"
            elif 200 <= code < 300:
                color = Colors.GREEN
                code_str = str(code)
            elif 300 <= code < 400:
                color = Colors.YELLOW
                code_str = str(code)
            else:
                color = Colors.RED
                code_str = str(code)
            print(f"  - Code {color}{code_str:<12}{Colors.ENDC}: {count} responses")
        
        if errors:
            print(f"\n{Colors.BLUE}{Colors.BOLD}Error Type Breakdown:{Colors.ENDC}")
            for error, count in sorted(errors.items()):
                print(f"  - {Colors.RED}{error:<20}{Colors.ENDC}: {count} occurrences")


# --- Main Tester Class ---
class AdvancedLoadTester:
    def __init__(self, **kwargs):
        self.config = kwargs
        self.results: List[TestResult] = []
        self.semaphore = asyncio.Semaphore(self.config['concurrent'])
        self._validate_config()

    def _validate_config(self):
        """Validate configuration parameters"""
        if self.config['requests'] <= 0:
            raise ValueError("Number of requests must be greater than 0")
        if self.config['concurrent'] <= 0:
            raise ValueError("Concurrency must be greater than 0")
        if self.config['rate'] <= 0:
            raise ValueError("Rate limit must be greater than 0")
        if not self.config['url'].startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")

    async def single_request(self, session: aiohttp.ClientSession, request_delay: float = None) -> TestResult:
        async with self.semaphore:
            # Apply rate limiting delay if specified
            if request_delay:
                await asyncio.sleep(request_delay)
                
            start_time = time.time()
            try:
                request_kwargs = {
                    'timeout': aiohttp.ClientTimeout(total=30, connect=10),
                    'ssl': False if self.config['url'].startswith('http://') else None
                }
                
                if self.config.get('data') and self.config['method'].upper() in ['POST', 'PUT', 'PATCH']:
                    if isinstance(self.config['data'], dict):
                        request_kwargs['json'] = self.config['data']
                    else:
                        request_kwargs['data'] = self.config['data']
                    
                method = getattr(session, self.config['method'].lower())
                async with method(self.config['url'], **request_kwargs) as response:
                    content = await response.read()
                    return TestResult(
                        status_code=response.status,
                        response_time=time.time() - start_time,
                        response_size_bytes=len(content)
                    )
            except asyncio.TimeoutError:
                return TestResult(
                    status_code=-1,
                    response_time=time.time() - start_time,
                    response_size_bytes=0,
                    error="TimeoutError"
                )
            except aiohttp.ClientError as e:
                return TestResult(
                    status_code=-1,
                    response_time=time.time() - start_time,
                    response_size_bytes=0,
                    error=f"ClientError: {type(e).__name__}"
                )
            except Exception as e:
                return TestResult(
                    status_code=-1,
                    response_time=time.time() - start_time,
                    response_size_bytes=0,
                    error=f"UnexpectedError: {type(e).__name__}"
                )

    async def run_test(self):
        print("\n" + "-" * 60)
        print(f"{Colors.BOLD}Test Parameters:{Colors.ENDC}")
        print(f"  {'URL:':<15} {self.config['url']}")
        print(f"  {'Method:':<15} {self.config['method'].upper()}")
        print(f"  {'Total Requests:':<15} {self.config['requests']}")
        print(f"  {'Concurrency:':<15} {self.config['concurrent']}")
        print(f"  {'Rate Limit:':<15} {self.config['rate']} req/s")
        if self.config.get('data'):
            print(f"  {'Has Payload:':<15} Yes")
        print("-" * 60)

        # Calculate delay between requests for rate limiting
        request_delay = 1.0 / self.config['rate'] if self.config['rate'] > 0 else 0
        
        # Configure connection pooling and limits
        connector = aiohttp.TCPConnector(
            limit=self.config['concurrent'] * 2,  # Allow some buffer
            limit_per_host=self.config['concurrent'],
            ttl_dns_cache=300,
            use_dns_cache=True,
            ssl=False if self.config['url'].startswith('http://') else None
        )

        try:
            async with aiohttp.ClientSession(
                connector=connector, 
                headers=self.config.get('headers', {}),
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                
                # Create tasks with proper rate limiting
                tasks = []
                for i in range(self.config['requests']):
                    # Stagger request starts for rate limiting
                    delay = (i // self.config['rate']) if self.config['rate'] > 0 else 0
                    task = asyncio.create_task(
                        self.single_request(session, delay)
                    )
                    tasks.append(task)
                
                # Use tqdm for progress tracking
                try:
                    # Create a progress bar
                    progress_bar = tqdm(
                        total=len(tasks),
                        desc=f"{Colors.CYAN}Executing Requests{Colors.ENDC}",
                        unit="req"
                    )
                    
                    # Gather results with progress tracking
                    self.results = []
                    completed_tasks = asyncio.as_completed(tasks)
                    
                    for completed_task in completed_tasks:
                        try:
                            result = await completed_task
                            if isinstance(result, TestResult):
                                self.results.append(result)
                        except Exception as e:
                            # Create error result for failed tasks
                            error_result = TestResult(
                                status_code=-1,
                                response_time=0.0,
                                response_size_bytes=0,
                                error=f"TaskError: {type(e).__name__}"
                            )
                            self.results.append(error_result)
                        finally:
                            progress_bar.update(1)
                    
                    progress_bar.close()
                    
                except Exception as e:
                    print(f"{Colors.RED}Error during test execution: {e}{Colors.ENDC}")
                    # Collect results from any completed tasks
                    self.results = []
                    for task in tasks:
                        if task.done() and not task.cancelled():
                            try:
                                result = await task
                                if isinstance(result, TestResult):
                                    self.results.append(result)
                            except Exception:
                                # Add error result for failed tasks
                                error_result = TestResult(
                                    status_code=-1,
                                    response_time=0.0,
                                    response_size_bytes=0,
                                    error="TaskCollectionError"
                                )
                                self.results.append(error_result)
                                
        except Exception as e:
            print(f"{Colors.RED}Failed to create HTTP session: {e}{Colors.ENDC}")
            raise


# --- Main Execution Block ---
def get_interactive_input():
    """Get all test parameters interactively with user-friendly prompts."""
    config = {}
    print(f"\n{Colors.CYAN}Entering Interactive Mode...{Colors.ENDC}")
    
    # URL with validation
    while True:
        url = input(f"Enter full target URL {Colors.BOLD}(e.g., http://localhost:8080/api){Colors.ENDC}: ").strip()
        if url.lower().startswith(('http://', 'https://')):
            config['url'] = url
            break
        print(f"{Colors.RED}Invalid URL. Please include http:// or https://{Colors.ENDC}")

    # Safety check for non-local URLs
    if not any(x in config['url'].lower() for x in ['localhost', '127.0.0.1', '192.168.', '10.', '172.16.', '172.17.', '172.18.', '172.19.', '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.', '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.']):
        print(f"{Colors.YELLOW}Warning: Testing against external URL: {config['url']}{Colors.ENDC}")
        confirm = input("This doesn't appear to be a local server. Continue? (y/N): ")
        if confirm.lower() != 'y':
            print("Test cancelled for safety.")
            sys.exit(0)

    # Method validation
    valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
    while True:
        method = input(f"Enter HTTP Method {Colors.BOLD}(GET, POST, PUT, etc.) [default: GET]{Colors.ENDC}: ").upper() or 'GET'
        if method in valid_methods:
            config['method'] = method
            break
        print(f"{Colors.RED}Invalid method. Choose from: {', '.join(valid_methods)}{Colors.ENDC}")
    
    # Core params with validation
    while True:
        try:
            requests = int(input(f"Enter total number of requests to send {Colors.BOLD}[default: 100]{Colors.ENDC}: ") or 100)
            if requests > 0:
                config['requests'] = requests
                break
            else:
                print(f"{Colors.RED}Number of requests must be positive{Colors.ENDC}")
        except ValueError:
            print(f"{Colors.RED}Please enter a valid number{Colors.ENDC}")
    
    while True:
        try:
            concurrent = int(input(f"Enter max concurrent connections {Colors.BOLD}[default: 10]{Colors.ENDC}: ") or 10)
            if 1 <= concurrent <= 1000:  # Reasonable limits
                config['concurrent'] = concurrent
                break
            else:
                print(f"{Colors.RED}Concurrency must be between 1 and 1000{Colors.ENDC}")
        except ValueError:
            print(f"{Colors.RED}Please enter a valid number{Colors.ENDC}")
    
    while True:
        try:
            rate = int(input(f"Enter target requests per second {Colors.BOLD}[default: 10]{Colors.ENDC}: ") or 10)
            if rate > 0:
                config['rate'] = rate
                break
            else:
                print(f"{Colors.RED}Rate must be positive{Colors.ENDC}")
        except ValueError:
            print(f"{Colors.RED}Please enter a valid number{Colors.ENDC}")

    # Headers
    config['headers'] = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    print(f"\n{Colors.CYAN}Default User-Agent set. Add custom headers below (format: Key: Value){Colors.ENDC}")
    print(f"{Colors.YELLOW}Press Enter on empty line to finish:{Colors.ENDC}")
    
    while True:
        header = input("  > ").strip()
        if not header: 
            break
        if ':' in header:
            key, value = header.split(':', 1)
            config['headers'][key.strip()] = value.strip()
            print(f"    {Colors.GREEN}Added: {key.strip()}: {value.strip()}{Colors.ENDC}")
        else:
            print(f"    {Colors.YELLOW}Invalid format. Use 'Key: Value'{Colors.ENDC}")

    # Data payload
    config['data'] = None
    if config['method'] in ['POST', 'PUT', 'PATCH']:
        print(f"\n{Colors.CYAN}Enter JSON data payload for {config['method']} request:{Colors.ENDC}")
        data_str = input("JSON payload (or press Enter to skip): ").strip()
        if data_str:
            try:
                config['data'] = json.loads(data_str)
                print(f"    {Colors.GREEN}Valid JSON payload added{Colors.ENDC}")
            except json.JSONDecodeError as e:
                print(f"    {Colors.RED}Invalid JSON: {e}. Continuing without payload.{Colors.ENDC}")

    return config

async def main():
    banner = f"""{Colors.MAGENTA}
██████  ██   ██ ██   ██ ████████ ██   ██ ██      ██    ██ 
██   ██  ██ ██   ██ ██     ██    ██   ██ ██       ██  ██  
██   ██   ███     ███      ██    ███████ ██        ████   
██   ██  ██ ██   ██ ██     ██    ██   ██ ██         ██    
██████  ██   ██ ██   ██    ██    ██   ██ ███████    ██    
                                                          
{Colors.ENDC}
{Colors.BOLD}                   Advanced HTTP Load Tester by DXXTHLY                   {Colors.ENDC}
"""
    print(banner)

    parser = argparse.ArgumentParser(
        description="Advanced HTTP Load Tester - Safe testing for your web applications",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("url", nargs='?', default=None, help="Target URL (starts interactive mode if omitted)")
    parser.add_argument("-n", "--requests", type=int, default=100, help="Total requests (default: 100)")
    parser.add_argument("-c", "--concurrent", type=int, default=10, help="Max concurrent connections (default: 10)")
    parser.add_argument("-r", "--rate", type=int, default=10, help="Requests per second (default: 10)")
    parser.add_argument("-m", "--method", type=str, default='GET', help="HTTP method (default: GET)")
    parser.add_argument("-H", "--header", action='append', help="Custom header: 'Key:Value'")
    parser.add_argument("-d", "--data", type=str, help="JSON data or file path for POST/PUT")
    
    args = parser.parse_args()

    try:
        if args.url:
            # Command line mode
            config = {
                'url': args.url,
                'method': args.method.upper(),
                'requests': args.requests,
                'concurrent': args.concurrent,
                'rate': args.rate,
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                },
                'data': None
            }
            
            # Process headers
            if args.header:
                for h in args.header:
                    if ':' in h:
                        key, value = h.split(':', 1)
                        config['headers'][key.strip()] = value.strip()

            # Process data payload
            if args.data:
                try:
                    if os.path.exists(args.data):
                        with open(args.data, 'r') as f:
                            config['data'] = json.load(f)
                    else:
                        config['data'] = json.loads(args.data)
                except (json.JSONDecodeError, FileNotFoundError) as e:
                    print(f"{Colors.RED}Error processing data: {e}{Colors.ENDC}")
                    return
        else:
            # Interactive mode
            config = get_interactive_input()

        # Create and run tester
        tester = AdvancedLoadTester(**config)
        
        print(f"\n{Colors.GREEN}Starting load test...{Colors.ENDC}")
        start_time = time.time()
        await tester.run_test()
        total_time = time.time() - start_time
        
        # Display results
        stats = StatisticsCalculator(tester.results, total_time)
        stats.print_summary()
        print("=" * 60)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user!{Colors.ENDC}")
    except ValueError as e:
        print(f"{Colors.RED}Configuration error: {e}{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.RED}Unexpected error: {e}{Colors.ENDC}")
        raise


if __name__ == "__main__":
    # Enable color support on Windows
    if os.name == 'nt':
        try:
            os.system('color')
        except:
            pass
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}Program terminated by user.{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.RED}Fatal error: {e}{Colors.ENDC}")
        sys.exit(1)