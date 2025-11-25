from aiohttp import web
import asyncio
import os


FILE_PATH = 'test_file.bin'
ARTIFICIAL_DELAY = 5.0

async def handle_download(request):
    print(f"Request received: {request.headers.get('Range', 'No Range')}")
    await asyncio.sleep(ARTIFICIAL_DELAY)
    return web.FileResponse(FILE_PATH)

async def handle_download_without_ranges(request):
    print(f"Request received without range support: {request.headers.get('Range', 'No Range')}")
    await asyncio.sleep(ARTIFICIAL_DELAY)
    with open(FILE_PATH, 'rb') as f:
        data = f.read()
    return web.Response(body=data)

app = web.Application()
app.add_routes([web.get('/', handle_download)])

if __name__ == '__main__':
    if not os.path.exists(FILE_PATH):
        print(f"Error: Please create {FILE_PATH} first.")
    else:
        print(f"Serving {FILE_PATH} with {ARTIFICIAL_DELAY}s delay...")
        web.run_app(app, port=8080)