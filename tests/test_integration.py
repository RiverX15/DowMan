import pytest
import subprocess
import sys
import time
import os
import signal
import hashlib


SERVER_SCRIPT = "server.py"
DOWNLOADER_SCRIPT = "../download_manager.py"
DOWNLOADED_FILE = "downloaded_file.bin"
SOURCE_FILE = "test_file.bin"


@pytest.fixture(scope="function")
def clean_environment():
    _clean()
    yield
    _clean()

def _clean():
    for f in os.listdir('.'):
        if f.endswith('.log') or f.endswith('.json') or f.endswith('.bin'):
            try:
                os.remove(f)
            except OSError:
                pass

@pytest.fixture(scope="function")
def server_process():
    process = subprocess.Popen(
        [sys.executable, SERVER_SCRIPT, "--fast"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(0.5)
    yield process
    process.terminate()
    process.wait()

@pytest.fixture(scope="function")
def server_process_no_range():
    process = subprocess.Popen(
        [sys.executable, SERVER_SCRIPT, "--no-range", "--fast"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(0.5)
    yield process
    process.terminate()
    process.wait()

@pytest.fixture(scope="function")
def server_process_corrupt_sector():
    process = subprocess.Popen(
        [sys.executable, SERVER_SCRIPT, "--corrupt", "--fast"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(0.5)
    yield process
    process.terminate()
    process.wait()

def calculate_shasum(file_path, algo='sha256'):
    with open(file_path, 'rb') as f:
        digest = hashlib.file_digest(f, algo)
    return digest.hexdigest()

def test_normal_download(clean_environment, server_process):
    result = subprocess.run([sys.executable, DOWNLOADER_SCRIPT, "--url", "http://localhost:8080", "--test"], check=True)
    assert result.returncode == 0, f"Downloader script exited with status {result.returncode}"
    assert os.path.exists(DOWNLOADED_FILE), "Downloaded file not found after complete download"
    assert not os.path.exists(f'{DOWNLOADED_FILE}.json'), "JSON state file not removed after download"
    assert calculate_shasum(DOWNLOADED_FILE) == calculate_shasum(SOURCE_FILE), "Downloaded file integrity verification failed"

def test_interrupted_download(clean_environment, server_process):
    downloader = subprocess.Popen([sys.executable, DOWNLOADER_SCRIPT, "--url", "http://localhost:8080", "--test"])
    time.sleep(0.3)
    downloader.send_signal(signal.SIGINT)
    try:
        downloader.wait(timeout=0.5)
    except subprocess.TimeoutExpired:
        downloader.kill()
    assert downloader.returncode == 130, f"Downloader script interrupted but exited with status {downloader.returncode}"
    assert os.path.exists(f'{DOWNLOADED_FILE}.json'), "JSON state file not present after interrupted download"
    result = subprocess.run([sys.executable, DOWNLOADER_SCRIPT, "--url", "http://localhost:8080", "--test"], check=True)
    assert result.returncode == 0, f"Downloader script exited with status {result.returncode}"
    assert os.path.exists(DOWNLOADED_FILE), "Downloaded file not found after complete download"
    assert not os.path.exists(f'{DOWNLOADED_FILE}.json'), "JSON state file not removed after download"
    assert calculate_shasum(DOWNLOADED_FILE) == calculate_shasum(SOURCE_FILE), "Downloaded file integrity verification failed"

def test_no_range_download(clean_environment, server_process_no_range):
    result = subprocess.run([sys.executable, DOWNLOADER_SCRIPT, "--url", "http://localhost:8080", "--test"], check=True)
    assert result.returncode == 0, f"Downloader script exited with status {result.returncode}"
    assert os.path.exists(DOWNLOADED_FILE), "Downloaded file not found after complete download"
    assert not os.path.exists(f'{DOWNLOADED_FILE}.json'), "JSON state file present after complete sequential download"
    assert calculate_shasum(DOWNLOADED_FILE) == calculate_shasum(SOURCE_FILE), "Downloaded file integrity verification failed"

def test_killed_download(clean_environment, server_process):
    downloader = subprocess.Popen([sys.executable, DOWNLOADER_SCRIPT, "--url", "http://localhost:8080", "--test"])
    time.sleep(0.5)
    downloader.kill()
    downloader.wait()
    assert os.path.exists(f'{DOWNLOADED_FILE}.json'), "JSON state file not found after hard kill"
    result = subprocess.run([sys.executable, DOWNLOADER_SCRIPT, "--url", "http://localhost:8080", "--test"], check=True)
    assert result.returncode == 0, f"Downloader script exited with status {result.returncode}"
    assert os.path.exists(DOWNLOADED_FILE), "Downloaded file not found after complete download"
    assert not os.path.exists(f'{DOWNLOADED_FILE}.json'), "JSON state file not removed after download"
    assert calculate_shasum(DOWNLOADED_FILE) == calculate_shasum(SOURCE_FILE), "Downloaded file integrity verification failed"

def test_corrupt_sector_download(clean_environment, server_process_corrupt_sector):
    result = subprocess.run([sys.executable, DOWNLOADER_SCRIPT, "--url", "http://localhost:8080", "--test"])
    assert result.returncode == 1, f"Downloader script exited with status {result.returncode}"
    assert os.path.exists(DOWNLOADED_FILE), "Downloaded file not found after complete download"
    assert os.path.exists(f'{DOWNLOADED_FILE}.json'), "JSON state file not present after corrupted sector download"
    assert not calculate_shasum(DOWNLOADED_FILE) == calculate_shasum(SOURCE_FILE), "Downloaded file integrity verification successful for corrupted sector"