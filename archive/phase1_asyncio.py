import asyncio
import random
import time


async def download(url: str, delay: float = 1.0):
    print(f"{url} download started")
    await asyncio.sleep(delay)
    print(f"{url} download finished")

async def main():
    start = time.perf_counter()
    urls = ["https://www.google.com/", "https://www.google2.com", "https://www.google3.com",
            "https://www.google4.com", "https://www.google5.com"]
    coros = [download(url, random.uniform(1,5)) for url in urls]
    results = await asyncio.gather(*coros, return_exceptions=True)
    print(f"Time taken: {time.perf_counter()-start:.2f} s")

if __name__ == '__main__':
    asyncio.run(main())
