import sys
import os
import pytest
import asyncio
from unittest.mock import MagicMock
import tomllib

# to import parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from download_manager import DownloadManager


# fixture for dummy manager instance
@pytest.fixture
def manager():
    with open('config_test.toml', 'rb') as f:
        config = tomllib.load(f)
    dm = DownloadManager("http://localhost:8080/testfile.bin", config)
    dm.download_state = {
        'chunk_size': 1024, # force 1KB chunks
        'completed_ranges': []
    }
    dm.queue = asyncio.Queue()
    dm.progress = MagicMock()   # mock progress bar to avoid cluttered test output
    return dm

@pytest.mark.asyncio
async def test_populate_queue_creates_correct_chunks(manager):
    # 2500 byte file with 1024 byte chunk size should create chunks (0, 1023), (1024, 2047), (2048, 2499)
    file_size = 2500
    manager._populate_queue(file_size)
    assert manager.queue.qsize() == 3
    task1 = await manager.queue.get()
    assert task1['range'] == (0, 1023)
    task2 = await manager.queue.get()
    assert task2['range'] == (1024, 2047)
    task3 = await manager.queue.get()
    assert task3['range'] == (2048, 2499)

@pytest.mark.asyncio
async def test_worker_requeues_on_failure(manager):
    # queue has only 1 job which we hard code to fail and test out worker's requeue logic
    manager.queue.put_nowait({'range': (0, 100), 'requeue_count': 0})
    # mock _download_chunk to fail
    manager._download_chunk = MagicMock(side_effect=Exception('Network Error'))
    job = await manager.queue.get()
    await manager._process_job(MagicMock(), job, MagicMock(), MagicMock())
    assert manager.queue.qsize() == 1
    new_job = await manager.queue.get()
    assert new_job['requeue_count'] == 1

def test_get_filename_from_content_disposition(manager):
    headers = {'content-disposition': 'attachment; filename="file.bin"'}
    assert manager._get_filename(headers) == 'file.bin'

def test_get_filename_from_url(manager):
    manager.url = 'https://example.com/archive.zip?token=12345'
    assert manager._get_filename({}) == 'archive.zip'