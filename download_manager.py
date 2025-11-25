import aiohttp
import asyncio
import time
import mimetypes


URL = 'http://localhost:8080'
NUM_WORKERS = 4
CHUNK_SIZE_MB = 5

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

    async def get_file_info(self, session: aiohttp.ClientSession):
        async def get_content_headers(session: aiohttp.ClientSession, url: str):
            headers = {
                'Accept-Encoding': 'identity'
            }
            async with session.head(url, headers=headers) as r:
                print(f'Response to HEAD request: {r}')
                r.raise_for_status()
                return r.headers

        def get_filename(url: str, headers):
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

        content_headers = await get_content_headers(session, self.url)
        content_length = int(content_headers.get('content-length'))
        filename = get_filename(self.url, content_headers)
        accept_ranges = content_headers.get('accept-ranges') == 'bytes'
        return content_length, filename, accept_ranges

    # producer
    def populate_queue(self, file_size: int):
        num_parts = file_size//self.chunk_size
        l,r = 0,self.chunk_size-1
        for _ in range(int(num_parts)):
            self.queue.put_nowait((l, r))
            l+=self.chunk_size
            r+=self.chunk_size
        if l<file_size-1:
            self.queue.put_nowait((l, file_size-1))

    # consumer
    async def download_chunk(self, session: aiohttp.ClientSession, start: int, end: int):
        async def get_bytes(session: aiohttp.ClientSession, url: str, l: int, r: int):
            headers = {
                'Range': f'bytes={l}-{r}',
                'Accept-Encoding': 'identity'
            }
            async with session.get(url, headers=headers) as resp:
                print(f'Response to GET request: {resp}')
                resp.raise_for_status()
                if resp.status == 206:
                    return await resp.read()
                else:
                    print(f'Error: URL {url} with status code {resp.status}.')
                    return b""

        data = await get_bytes(session, self.url, start, end)
        self.file.seek(start)
        self.file.write(data)

    async def worker(self, session: aiohttp.ClientSession, worker_id: int):
        while True:
            r = await self.queue.get()
            try:
                await self.download_chunk(session, r[0], r[1])
            finally:
                self.queue.task_done()

    async def start(self):
        async with aiohttp.ClientSession() as session:
            content_length, filename, accept_ranges = await self.get_file_info(session)
            if not accept_ranges:
                print(f'Server does not support range requests. Downloading sequentially.')
                with open(filename, 'wb') as self.file:
                    async with session.get(self.url) as resp:
                        resp.raise_for_status()
                        data = await resp.read()
                        self.file.write(data)
                return
            with open(filename, 'wb') as self.file:
                # start consumers
                workers = [asyncio.create_task(self.worker(session, i)) for i in range(self.max_concurrent)]
                # start producers
                self.populate_queue(content_length)
                # wait for queue to be empty
                await self.queue.join()
                # cancel all workers
                for w in workers:
                    w.cancel()

if __name__ == '__main__':
    start = time.perf_counter()
    manager = DownloadManager(url=URL, max_concurrent=NUM_WORKERS, chunk_size_mb=CHUNK_SIZE_MB)
    asyncio.run(manager.start())
    print(f'Time taken: {time.perf_counter() - start:.2f} s')