import aiohttp
import asyncio
import time
import mimetypes
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import logging
import json
import os
import sys


URL = 'http://localhost:8080'
NUM_WORKERS = 4
CHUNK_SIZE_MB = 5
LOG_FILE = 'download_manager.log'
TIMEOUT_S = 5.0
STATE_SAVE_INTERVAL_CHUNKS = 5
MAX_REQUEUE_LIMIT = 2


def configure_logging() -> logging.Logger:
    logger = logging.getLogger('download_manager')
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(LOG_FILE)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def log_retry_attempt(retry_state):
    logger = logging.getLogger('download_manager')
    if retry_state.outcome:
        exc = retry_state.outcome.exception()
        exc = repr(exc) if not str(exc) else str(exc)
        worker_id = retry_state.args[5] if len(retry_state.args) > 5 else None
        l, r = (retry_state.args[3], retry_state.args[4]) if len(retry_state.args) > 4 else (None, None)
        context_info = ''
        if worker_id is not None and (l,r) is not None:
            context_info = f' for worker {worker_id} on task range {l}-{r}'
        logger.warning(
            f'Retrying {retry_state.fn.__name__}{context_info} '
            f'(attempt {retry_state.attempt_number}) due to: {exc}. '
            f'Waiting {retry_state.next_action.sleep:.2f} s.'
        )

class DownloadManager:
    def __init__(
            self,
            url: str,
            max_concurrent: int = 4,
            chunk_size_mb: int = 5,
    ):
        self.url = url
        self.max_concurrent = max_concurrent
        self.chunk_size = chunk_size_mb*1024*1024
        self.queue = asyncio.Queue()
        self.file = None
        self.progress = None
        self.logger = logging.getLogger('download_manager')
        self.download_state = None
        self.download_task = None
        self.filename = None
        self.has_dropped_chunks = False

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, exp_base=2, min=1, max=20),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        before_sleep=log_retry_attempt,
        reraise=True
    )
    async def _get_content_headers(self, session: aiohttp.ClientSession, url: str):
        headers = {
            'Accept-Encoding': 'identity'
        }
        # tenacity will catch aiohttp.ClientError, asyncio.TimeoutError here
        async with session.head(url, headers=headers) as r:
            self.logger.debug(f'Response to HEAD request: {r}')
            r.raise_for_status()
            return r.headers

    @staticmethod
    def _get_filename(url: str, headers):
        # if `content-disposition` header is present
        content_disposition = headers.get('content-disposition')
        if content_disposition and 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[1].strip('"\'')
            return filename
        # if URL has file format specified
        url_path = url.split('/')[-1]
        if '.' in url_path:
            return url_path
        # guess extension from `content-type`
        content_type = headers.get('content-type')
        if content_type:
            extension = mimetypes.guess_extension(content_type)
            if extension:
                return f"downloaded_file{extension}"
        # if everything fails
        return "downloaded_file.bin"

    def load_state(self):
        try:
            with open(f"{self.filename}.json", "r") as f:
                state = json.load(f)
                if state.get('url') != self.url:
                    logger.warning('State file for given url not found. Downloading file from scratch.')
                    raise FileNotFoundError
                else:
                    if not os.path.exists(self.filename):
                        logger.warning('State file found but downloaded file missing. Restarting download.')
                        raise FileNotFoundError
                    else:
                        logger.info(f'Resuming file download.')
                        return state
        except FileNotFoundError:
            # state_exists = False
            state = dict()
            state['url'] = self.url
            state['chunk_size'] = self.chunk_size
            state['completed_ranges'] = []
            return state

    def save_state(self):
        # check needed to ensure filename is not None when saving state
        if self.filename:
            with open(f'{self.filename}.json', 'w') as f:
                json.dump(self.download_state, f)

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, exp_base=2, min=1, max=20),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        before_sleep=log_retry_attempt,
        reraise=True
    )
    async def download_sequentially(self, session: aiohttp.ClientSession):
        async with session.get(self.url) as resp:
            resp.raise_for_status()
            data = await resp.read()
            self.file.write(data)

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, exp_base=2, min=1, max=20),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        before_sleep=log_retry_attempt,
        reraise=True
    )
    async def _get_bytes(self, session: aiohttp.ClientSession, url: str, l: int, r: int, worker_id: int):
        headers = {
            'Range': f'bytes={l}-{r}',
            'Accept-Encoding': 'identity'
        }
        # tenacity will catch aiohttp.ClientError, asyncio.TimeoutError here
        async with session.get(url, headers=headers) as resp:
            self.logger.debug(f'Response to GET request: {resp}')
            resp.raise_for_status()
            return await resp.read()

    async def get_file_info(self, session: aiohttp.ClientSession):
        content_headers = await self._get_content_headers(session, self.url)
        content_length = int(content_headers.get('content-length'))
        filename = self._get_filename(self.url, content_headers)
        accept_ranges = content_headers.get('accept-ranges') == 'bytes'
        return content_length, filename, accept_ranges

    # producer
    def populate_queue(self, file_size: int):
        self.chunk_size = self.download_state.get('chunk_size')
        num_parts = file_size//self.chunk_size
        completed_ranges = set(tuple(r) for r in self.download_state.get('completed_ranges'))
        for (l,r) in completed_ranges:
            self.progress.advance(self.download_task, advance=r-l+1)
        l,r = 0,self.chunk_size-1
        for _ in range(int(num_parts)):
            if (l,r) not in completed_ranges:
                self.queue.put_nowait({'range': (l, r), 'requeue_count': 0})
            l+=self.chunk_size
            r+=self.chunk_size
        if l<file_size-1:
            if (l, file_size-1) not in completed_ranges:
                self.queue.put_nowait({'range': (l, file_size - 1), 'requeue_count': 0})

    # consumer
    async def download_chunk(self, session: aiohttp.ClientSession, start: int, end: int, worker_id: int):
        data = await self._get_bytes(session, self.url, start, end, worker_id)
        # synchronous (blocking) file i/o operations. use aiofiles if this causes bottleneck
        self.file.seek(start)
        self.file.write(data)
        self.download_state['completed_ranges'].append([start, end])
        if not len(self.download_state['completed_ranges']) % STATE_SAVE_INTERVAL_CHUNKS:
            self.save_state()

    async def worker(self, session: aiohttp.ClientSession, worker_id: int, task_id: int):
        while True:
            job = await self.queue.get()
            r = job.get('range')
            requeue_count = job.get('requeue_count')
            try:
                self.logger.info(f'Worker {worker_id} fetched task successfully.')
                self.logger.debug(f'Worker {worker_id} fetched task range {r[0]}-{r[1]} successfully.')
                self.logger.debug(f'Worker {worker_id} attempting task range {r[0]}-{r[1]}.')
                await self.download_chunk(session, r[0], r[1], worker_id)
                self.progress.advance(task_id, advance=r[1]-r[0]+1)
                self.logger.debug(f'Worker {worker_id} completed task range {r[0]}-{r[1]} successfully.')
            except Exception as e:
                if requeue_count > MAX_REQUEUE_LIMIT:
                    self.logger.critical(f'Task range {r[0]}-{r[1]} exceeded maximum re-queue limit of {MAX_REQUEUE_LIMIT}. Dropping chunk.')
                    self.has_dropped_chunks = True
                else:
                    self.logger.error(f'Worker {worker_id} failed on task range {r[0]}-{r[1]}: {e}. Re-queueing.')
                    self.queue.put_nowait({'range': r, 'requeue_count': requeue_count+1})
            finally:
                self.queue.task_done()
                self.logger.info(f'Worker {worker_id} free.')

    async def start(self):
        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeRemainingColumn()
        ) as self.progress:
            timeout = aiohttp.ClientTimeout(total=TIMEOUT_S)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                content_length, self.filename, accept_ranges = await self.get_file_info(session)
                self.download_state = self.load_state()
                self.download_task = self.progress.add_task(f"[red]Downloading file ", total=content_length)
                if not accept_ranges:
                    self.logger.warning(f'Server does not support range requests. Downloading sequentially.')
                    with open(self.filename, 'wb') as self.file:
                        await self.download_sequentially(session)
                    return
                # regular file handling will not work since we need to create file if not exists, open it and then write to it
                flags = os.O_RDWR | os.O_CREAT | getattr(os, 'O_BINARY', 0)
                fd = os.open(self.filename, flags)
                with os.fdopen(fd, 'rb+') as self.file:
                    # start consumers
                    workers = [asyncio.create_task(self.worker(session, i, self.download_task)) for i in range(self.max_concurrent)]
                    # start producers
                    self.populate_queue(content_length)
                    # wait for queue to be empty
                    await self.queue.join()
                    # cancel all workers
                    for w in workers:
                        w.cancel()
                if self.has_dropped_chunks:
                    self.logger.error("Download finished with some chunks dropped.")
                    raise Exception("Download incomplete due to dropped chunks.")
                self.logger.info("Download finished.")
                if os.path.exists(f'{self.filename}.json'):
                    with open(f'{self.filename}.json', 'r') as f:
                        state = json.load(f)
                        if state.get('url') == self.url:
                            os.remove(f'{self.filename}.json')

if __name__ == '__main__':
    logger = configure_logging()
    start = time.perf_counter()
    manager = DownloadManager(url=URL, max_concurrent=NUM_WORKERS, chunk_size_mb=CHUNK_SIZE_MB)
    try:
        asyncio.run(manager.start())
    # keyboard interrupt not caught by exception, needs to be handled explicitly
    except KeyboardInterrupt:
        logger.info("Download cancelled by user. Saving state.")
        manager.save_state()
        sys.exit(130)
    except Exception as e:
        logger.error(f'An unhandled exception occurred: {e}')
        sys.exit(1)
    finally:
        logger.info(f'Time taken: {time.perf_counter() - start:.2f} s')