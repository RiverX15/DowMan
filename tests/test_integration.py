import os
import sys
import pytest
from aioresponses import aioresponses, CallbackResult
import tomllib

# to import parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from download_manager import DownloadManager


# fixture for cleanup pre and post every test
@pytest.fixture
def clean_environment():
    def _clean():
        for f in os.listdir('.'):
            if f.endswith('.log') or f.endswith('.dowman') or f.endswith('.bin'):
                try:
                    os.remove(f)
                except OSError:
                    pass
    _clean()
    yield
    _clean()

# fixture for mocking file contents
@pytest.fixture
def mock_file_data():
    return (b'0123456789'*100+b'abcdefghij'*100)*50   # 100 KB

# fixture for fetching test configuration
@pytest.fixture
def config():
    with open('config_test.toml', 'rb') as f:
        config = tomllib.load(f)
    return config

# fixture for dummy manager instance
@pytest.fixture
def manager(config, tmp_path):
    dm = DownloadManager('http://localhost:8080/testfile.bin', config, benchmark_mode=True)
    return dm

@pytest.mark.asyncio
async def test_normal_download(clean_environment, manager, mock_file_data):
    # normal download without interruptions
    url = manager.url
    with aioresponses() as m:
        # mock HEAD request
        m.head(url, status=200, headers={
            'Content-Length': str(len(mock_file_data)),
            'Accept-Ranges': 'bytes'
        })
        # mock GET requests
        def range_callback(url, **kwargs):
            headers = kwargs.get('headers', {})
            l, r = map(int, headers.get('Range').split('=')[-1].split('-'))
            return CallbackResult(status=206, body=mock_file_data[l:r+1])
        m.get(url, callback=range_callback, repeat=True)
        await manager.start()
    assert os.path.exists(manager.filename)
    with open(manager.filename, 'rb') as f:
        assert f.read() == mock_file_data
    assert not os.path.exists(f'{manager.filename}.dowman')

@pytest.mark.asyncio
async def test_no_range_fallback(clean_environment, manager, mock_file_data):
    # sequential download from server without range support
    url = manager.url
    with aioresponses() as m:
        # mock HEAD request without Accept-Ranges
        m.head(url, status=200, headers={
            'Content-Length': str(len(mock_file_data))
        })
        # expect only 1 get request for the entire data
        m.get(url, status=200, body=mock_file_data)
        await manager.start()
    assert os.path.exists(manager.filename)
    with open(manager.filename, 'rb') as f:
        assert f.read() == mock_file_data
    assert not os.path.exists(f'{manager.filename}.dowman')

@pytest.mark.asyncio
async def test_corrupt_sector_download(clean_environment, manager, mock_file_data):
    # normal download from server with fixed failing sector
    url = manager.url
    try:
        with aioresponses() as m:
            m.head(url, status=200, headers={
                'Content-Length': str(len(mock_file_data)),
                'Accept-Ranges': 'bytes'
            })
            def corrupt_callback(url, **kwargs):
                headers = kwargs.get('headers', {})
                l, r = map(int, headers.get('Range').split('=')[-1].split('-'))
                # corrupt second chunk ~10-20 KB
                if 10000 <= l <= 20000:
                    return CallbackResult(status=500)
                return CallbackResult(status=206, body=mock_file_data[l:r+1])
            m.get(url, callback=corrupt_callback, repeat=True)
            await manager.start()
    except Exception as e:
        if 'Download incomplete due to dropped chunks' in str(e):
            pass
        else:
            raise e
    assert os.path.exists(manager.filename)
    with open(manager.filename, 'rb') as f:
        assert f.read() != mock_file_data
    assert os.path.exists(f'{manager.filename}.dowman')

@pytest.mark.asyncio
async def test_resume_capability(clean_environment, manager, mock_file_data, config):
    # normal download with simulated Ctrl+C in downloader
    url = manager.url
    # simulate keyboard interrupt after 2 chunks
    chunks_downloaded = 0
    def interrupting_callback(url, **kwargs):
        nonlocal chunks_downloaded
        chunks_downloaded += 1
        if chunks_downloaded >= 3:
            # raising keyboard interrupt here will cause pytest to exit
            raise RuntimeError('Simulated interrupt (Ctrl+C)')
        headers = kwargs.get('headers', {})
        l, r = map(int, headers.get('Range').split('=')[-1].split('-'))
        return CallbackResult(status=206, body=mock_file_data[l:r+1])
    try:
        with aioresponses() as m:
            m.head(url, status=200, headers={
                'Content-Length': str(len(mock_file_data)),
                'Accept-Ranges': 'bytes'
            })
            m.get(url, callback=interrupting_callback, repeat=True)
            await manager.start()
    except RuntimeError:
        manager.save_state()
    except Exception as e:
        if 'Download incomplete due to dropped chunks' in str(e):
            pass
        else:
            raise e
    assert os.path.exists(manager.filename)
    with open(manager.filename, 'rb') as f:
        assert f.read() != mock_file_data
    assert os.path.exists(f'{manager.filename}.dowman')
    new_manager = DownloadManager(url, config, benchmark_mode=True)
    new_manager.filename = manager.filename
    with aioresponses() as m:
        m.head(url, status=200, headers={
            'Content-Length': str(len(mock_file_data)),
            'Accept-Ranges': 'bytes'
        })
        def range_callback(url, **kwargs):
            headers = kwargs.get('headers', {})
            l, r = map(int, headers.get('Range').split('=')[-1].split('-'))
            return CallbackResult(status=206, body=mock_file_data[l:r+1])
        m.get(url, callback=range_callback, repeat=True)
        await new_manager.start()
    assert os.path.exists(manager.filename)
    with open(manager.filename, 'rb') as f:
        assert f.read() == mock_file_data
    assert not os.path.exists(f'{manager.filename}.dowman')

@pytest.mark.asyncio
async def test_transient_failure_retries(clean_environment, manager, mock_file_data):
    # server fails some requests to test retry capabilities
    url = manager.url
    with aioresponses() as m:
        m.head(url, status=200, headers={
            'Content-Length': str(len(mock_file_data)),
            'Accept-Ranges': 'bytes'
        })
        # fail 2 requests then succeed all
        m.get(url, status=500)
        m.get(url, status=500)
        def range_callback(url, **kwargs):
            headers = kwargs.get('headers', {})
            l, r = map(int, headers.get('Range').split('=')[-1].split('-'))
            return CallbackResult(status=206, body=mock_file_data[l:r+1])
        m.get(url, callback=range_callback, repeat=True)
        await manager.start()
    assert os.path.exists(manager.filename)
    with open(manager.filename, 'rb') as f:
        assert f.read() == mock_file_data
    assert not os.path.exists(f'{manager.filename}.dowman')