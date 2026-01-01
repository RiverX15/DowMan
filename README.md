# DowMan

<p align="center">
  <a href="https://github.com/RiverX15/DowMan/actions/workflows/tests.yml" target="_blank">
    <img src="https://github.com/RiverX15/DowMan/actions/workflows/tests.yml/badge.svg" alt="Tests">
  </a>
  <img src="https://img.shields.io/badge/python-3.12%20|%203.13-blue?style=flat&logo=python&logoColor=white" alt="Python Versions">
  <a href="https://github.com/RiverX15/DowMan/blob/main/LICENSE" target="_blank">
    <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  </a>
</p>

---

A robust, asynchronous file downloader written in Python.

This project implements a multi-segment downloader that splits files into chunks and downloads them concurrently using
`asyncio` and `aiohttp`.

---

## 🚀 Features

* **Concurrency:** Splits files into chunks and downloads them in parallel to maximize bandwidth.
* **Resilience:** Intelligent retry logic with exponential backoff (via `tenacity`) for handling network drops.
* **Persistence:** Pauses and resumes downloads seamlessly. State is saved to a lightweight JSON file, protecting 
against unexpected program crashes.
* **Visual Feedback:** Real-time progress bars and transfer statistics using `rich`.
* **Integrity:** Automatic fallback to sequential downloading for servers that don't support Range requests.

---

## 🛠️ Prerequisites

* **OS:** Linux (Ubuntu 24.04 recommended), macOS or Windows
* **Python:** 3.12+
* **Package Manager:** [uv](https://github.com/astral-sh/uv) (Recommended for lightning-fast setups)

---

## 📦 Installation

### 1. Clone the repository:
```bash
git clone https://github.com/RiverX15/DowMan.git
cd DowMan
```

### 2. For Users (Run the downloader)

If you just want to use the tool, sync only the core runtime dependencies:
```bash
# Sync dependencies (creates a virtual environment automatically)
uv sync --no-dev

# Run the downloader
uv run --no-dev download_manager.py --url <target-resource-url>
```

In-progress downloads can be paused using `Ctrl+C`. DowMan saves the progress to a `*.dowman` state file next to the 
partial download. To resume, re-run the exact same command you used to start the download.

### 3. For Developers (Run Tests)

If you want to contribute or run the test suite, you'll need the development dependencies:
```bash
# Sync all dependencies
uv sync

# Navigate to the tests directory and run the integration test suite
cd tests
uv run pytest
```

---

## ⚙️ Configuration

You can fine-tune DowMan's behavior by modifying [`config.toml`](config.toml). For developers running tests, these
parameters are critical for simulating network conditions.

### 🌐 Network & Performance
Parameters that control how the downloader connects to the internet.

| Parameter         | Default | Description                                                                            |
|:------------------|:--------|:---------------------------------------------------------------------------------------|
| `max_concurrent`  | `4`     | Maximum number of parallel connections.                                                |
| `chunk_size_mb`   | `5`     | Size of each file segment (in MB). Smaller chunks are better for unstable connections. |
| `timeout_seconds` | `60.0`  | Time to wait for a server response before retrying.                                    |

### 🛡️ Resilience & Retries
Controls how the downloader handles failures.

| Parameter                    | Default | Description                                                                       |
|:-----------------------------|:--------|:----------------------------------------------------------------------------------|
| `max_retries`                | `5`     | How many times to retry a failed chunk with exponential backoff before giving up. |
| `max_requeue_limit`          | `3`     | If a chunk fails all retries, it is put back in the queue this many times.        |
| `state_save_interval_chunks` | `5`     | Save download progress to JSON every `N` completed chunks.                        |

---

## 📊 Benchmarks

Performance comparison against industry-standard download accelerators (`aria2`, `axel`) and standard tools (`curl`).

**Test Environment:**
* **Platform:** GitHub Codespaces (2-core vCPU, 8GB RAM)
* **File:** 100MB Test File (`speedtest.tele2.net`)
* **Concurrency:** 4 connections with each connection's disk buffer size of 5MB (where applicable)

| Tool       | Language   | Mean Time [s] | Relative Time |
|:-----------|:-----------|:--------------|:--------------|
| **axel**   | C          | 53.93         | 1.00x         |
| **DowMan** | **Python** | **54.70**     | **1.01x**     |
| **aria2**  | C++        | 54.70         | 1.01x         |
| **curl**   | C          | 202.35        | 3.75x         |

> By leveraging `asyncio` and `aiohttp`, DowMan matches the download efficiency of `axel` or `aria2`, while significantly
> outperforming standard single-threaded `curl`.
> 
> See [`BENCHMARK.md`](BENCHMARK.md) for raw test output.

---

## 🏗️ Architecture

DowMan implements a **Producer-Consumer** pattern using `asyncio.Queue`:

1. **Producer:** Calculates byte ranges (chunks) for the file that are yet to be downloaded and pushes them into a queue.
2. **Consumers (Workers):** A pool of worker tasks pull ranges from the queue, fetch the bytes asynchronously, and write
them to the disk.
3. **State Manager:** Periodically writes a JSON state file to disk, tracking completed chunks for resumability.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---