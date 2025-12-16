import pytest
import subprocess
import sys
import time
import os
import signal


SERVER_SCRIPT = "server.py"
DOWNLOADER_SCRIPT = "../download_manager.py"
VALIDATOR_SCRIPT = "verify_download.py"
DOWNLOADED_FILE = "downloaded_file.bin"

@pytest.fixture(scope="function")
def clean_environment():
    _clean()
    yield
    _clean()

def _clean():
    for f in os.listdir('.'):
        if f.endswith('.log') or f.startswith('downloaded_file') or f.endswith('.json'):
            try:
                os.remove(f)
            except OSError:
                pass

@pytest.fixture(scope="function")
def server_process():
    print("Starting server fixture...")
    process = subprocess.Popen(
        [sys.executable, SERVER_SCRIPT],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(2)
    yield process
    print("Terminating server fixture...")
    process.terminate()
    process.wait()

def run_validator():
    result = subprocess.run([sys.executable, VALIDATOR_SCRIPT], capture_output=True)
    return result.returncode == 0

def test_normal_download(clean_environment, server_process):
    result = subprocess.run([sys.executable, DOWNLOADER_SCRIPT], check=True)
    assert result.returncode == 0, "Downloader script failed"
    assert os.path.exists(DOWNLOADED_FILE), "Downloaded file not found"
    assert not os.path.exists(f'{DOWNLOADED_FILE}.json'), "JSON state file not removed"
    assert run_validator(), "File integrity verification failed"

def test_interrupted_download(clean_environment, server_process):
    downloader = subprocess.Popen([sys.executable, DOWNLOADER_SCRIPT])
    time.sleep(6)
    downloader.send_signal(signal.SIGINT)
    try:
        downloader.wait(timeout=5)
    except subprocess.TimeoutExpired:
        downloader.kill()
    result = subprocess.run([sys.executable, DOWNLOADER_SCRIPT], check=True)
    assert result.returncode == 0, "Downloader script failed"
    assert not os.path.exists(f'{DOWNLOADED_FILE}.json'), "JSON state file not removed"
    assert run_validator(), "File integrity verification failed after resume"
