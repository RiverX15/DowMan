import time
from tenacity import retry, stop_after_attempt, wait_exponential
import asyncio
import aiohttp


URL = 'http://localhost:8080'

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, exp_base=2, min=1, max=20),
    reraise=True
)
async def get_content_headers(session: aiohttp.ClientSession, url: str):
    global prev_req, start
    headers = {
        'Accept-Encoding': 'identity'
    }
    send_time = time.perf_counter()
    print(f'Making request at {send_time-start:.2f} s from start.')
    print(f'Wait period: {send_time-prev_req:.2f} s')
    prev_req = send_time
    async with session.head(url, headers=headers) as r:
        if r.status == 500:
            print(f'Request failed.')
            raise Exception('Request failed.')
        print(f'Response to HEAD request: {r}')
        return r.headers

async def main(url: str):
    async with aiohttp.ClientSession() as session:
        return await get_content_headers(session, url)

if __name__ == '__main__':
    start = time.perf_counter()
    prev_req = start
    asyncio.run(main(URL))