# The Ultimate HTTP Performance Analysis Tool

[![Language](https://img.shields.io/badge/Language-Python-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
![Developer](https://img.shields.io/badge/DEV-DXXTHLY-black.svg)

Welcome to the Ultimate HTTP Performance Analysis Tool, a professional-grade, asynchronous load testing suite built for developers. This tool is designed to help you understand the performance limits of your web applications, APIs, and servers in a controlled, safe, and highly detailed manner.

It is a sophisticated diagnostic instrument, not a simple stresser.



## What is this tool?

This is a Python-based command-line utility that generates a configurable amount of HTTP traffic against a target URL and provides a detailed, nerdy breakdown of the server's performance. It uses modern asynchronous technology to handle thousands of connections efficiently from a single machine.

Its purpose is to answer critical questions like:
*   How many requests per second can my server *actually* handle?
*   What is the server's response time under heavy load?
*   How consistent is the performance? (i.e., is there high jitter?)
*   Where are the bottlenecks? (DNS, TCP connection, or server processing time?)

## Key Features

*   **Dual-Mode Operation:** Run tests based on a fixed number of requests (`-n`) or for a specific duration (`-t`).
*   **Asynchronous Core:** Built with `asyncio` and `aiohttp` to handle high concurrency with minimal overhead.
*   **Concurrency & Rate Limiting:** Precisely control the number of simultaneous users (`-c`) and the target requests per second (`-r`).
*   **In-Depth "Nerdy" Statistics:**
    *   **Latency Percentiles:** See the average, median (p50), p90, p95, and p99 response times.
    *   **Jitter/Standard Deviation:** Measure the consistency of your server's responses.
    *   **Detailed Latency Breakdown:** Get average timings for **DNS Lookup**, **TCP Connection**, and **Time To First Byte (TTFB)**.
    *   **Throughput:** Reports the actual data transfer rate in Megabits per second (Mbps).
*   **Beautiful & Informative UI:**
    *   A live progress bar (`tqdm`) shows requests per second and failures in real-time.
    *   A final, colorized report is presented in a clean, retro-style ASCII table.
    *   A visual **Response Time Histogram** to see the distribution of latencies at a glance.
*   **Full HTTP Support:** Use any HTTP method (`-m`), add custom headers (`-H`), and include JSON data payloads (`-d`).
*   **Results Exporting:** Save the raw data from every single request to a JSON file (`-o`) for further analysis or charting.
*   **User-Friendly Interactive Mode:** If you run the script without a URL, it will guide you through every option with helpful prompts.

## Requirements

*   Python 3.7+
*   Required packages: `numpy`, `tqdm`, `aiohttp`

### Installation

1.  Clone the repository or download the `httploader.py` script.
2.  Install the dependencies using pip:
    ```bash
    pip install numpy tqdm aiohttp
    ```

## How to Use

The tool can be run in two ways: interactively or directly from the command line.

### Interactive Mode (Recommended for first-time use)

Simply run the script without any arguments. It will launch a user-friendly wizard to guide you through setting up the test.

```bash
python3 httploader.py


You will be prompted for the URL, test mode (requests vs. duration), concurrency, and other parameters.

Command-Line Mode

For quick tests or scripting, you can provide all parameters as command-line arguments.

Syntax:

Generated bash
python3 httploader.py [url] [-n requests | -t duration] [options...]
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END
Examples:

Simple Test: Send 500 requests to a local server with 50 concurrent users.

Generated bash
python3 httploader.py http://127.0.0.1:8000 -n 500 -c 50
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

Duration-Based Test: Run a test for 60 seconds against a production URL, with 100 concurrent users and a rate limit of 20 RPS.

Generated bash
python3 httploader.py https://api.example.com/v1/status -t 60 -c 100 -r 20
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

POST Request with Data: Send 1000 POST requests with a JSON payload and save the raw results to a file.

Generated bash
python3 httploader.py https://api.example.com/v1/users -n 1000 -c 25 -m POST -d '{"username":"test"}' -o results.json
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END
All Command-Line Arguments
Argument	Flag	Description
url	(positional)	The full URL to test. If omitted, interactive mode starts.
--requests	-n	Test Mode: Total number of requests to send.
--duration	-t	Test Mode: Duration of the test in seconds.
--concurrent	-c	Maximum number of concurrent connections (simulated users).
--rate	-r	Target requests per second (rate limit). Set to 0 for unlimited.
--method	-m	HTTP method to use (e.g., GET, POST, PUT). Default: GET.
--header	-H	Custom header in 'Key:Value' format. Can be used multiple times.
--data	-d	Data payload. Can be a JSON string or a path to a file with JSON.
--output	-o	File path to save the full raw results as JSON.
License

This project is licensed under the MIT License.

Generated code
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
IGNORE_WHEN_COPYING_END
