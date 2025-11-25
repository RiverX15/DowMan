import aiohttp
import asyncio
import time
import mimetypes


async def get_content_headers(session: aiohttp.ClientSession, url: str):
    print(f'<----- get_content_headers url {url}')
    headers = {
        'Accept-Encoding': 'identity'
    }
    async with session.head(url, headers=headers) as r:
        return r.headers

async def get_bytes(session: aiohttp.ClientSession, url: str, l: int, r: int):
    print(f'<----- get_bytes url {url} l {l} r {r}')
    headers = {
        'Range': f'bytes={l}-{r}',
        'Accept-Encoding': 'identity'
    }
    async with session.get(url, headers=headers) as resp:
        if resp.status == 206 or resp.status==200:
            return await resp.read()
        else:
            print(f"Error. URL: {url}, status code: {resp.status}")
            return b""

def calculate_ranges(file_size: int, num_parts: int):
    print(f'<----- calculate_ranges file_size {file_size} num_parts {num_parts}')
    ranges = []
    l,r = 0,file_size//num_parts-1
    for _ in range(0, num_parts):
        ranges.append((l, r))
        l+=file_size//num_parts
        r+=file_size//num_parts
    tup = ranges.pop()
    ranges.append((tup[0], file_size-1))
    return ranges

async def download_and_write(f, session: aiohttp.ClientSession, url: str, l: int, r: int):
    print(f'<----- download_and_write url {url} l {l} r {r}')
    data = await get_bytes(session, url, l, r)
    f.seek(l)
    f.write(data)

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

async def main(url: str):
    async with aiohttp.ClientSession() as session:
        content_headers = await get_content_headers(session, url)
        print(f'-----> content_headers {content_headers}')
        content_length = int(content_headers.get('content-length'))
        num_parts = 4
        filename = get_filename(url, content_headers)
        ranges = calculate_ranges(content_length, num_parts)
        with open(filename, 'wb') as f:
            coros = [download_and_write(f, session, url, tup[0], tup[1]) for tup in ranges]
            await asyncio.gather(*coros, return_exceptions=True)

if __name__ == '__main__':
    start = time.perf_counter()
    url = 'https://httpbin.io/range/102400'
    asyncio.run(main(url))
    print(f'Time taken: {time.perf_counter() - start:.2f} s')
