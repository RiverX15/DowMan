import aiohttp
import asyncio
import time


async def get_content_length(session: aiohttp.ClientSession, url: str):
    async with session.head(url) as r:
        return int(r.headers.get('content-length'))

async def get_first_n_bytes(session: aiohttp.ClientSession, url: str, n: int = 100):
    headers = {
        'Range': f'bytes=0-{n-1}'
    }
    async with session.get(url, headers=headers) as r:
        if r.status == 206:
            return await r.read()
        else:
            print(f"Server for {url} doesn't support range requests. Status code: {r.status}")
            return b""

async def main(url: str):
    async with aiohttp.ClientSession() as session:
        content_length = await get_content_length(session, url)
        data = await get_first_n_bytes(session, url, 26)
        return content_length, data

if __name__ == '__main__':
    start = time.perf_counter()
    url = 'https://httpbin.org/range/4096'
    result = asyncio.run(main(url))
    print(result)
    print(f"Time taken: {time.perf_counter() - start:.2f} s")
