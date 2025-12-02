from aiohttp import web
import asyncio
import os
import random
import logging


FILE_PATH = 'test_file.bin'
ARTIFICIAL_DELAY = 5.0
FAIL_PROBABILITY = 0.3
LOG_FILE = 'server.log'

def configure_logging() -> logging.Logger:
    logger = logging.getLogger('server')
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(LOG_FILE)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

async def handle_download(request):
    logger.debug(f"Request received to server with range support: {request.headers.get('Range', 'HEAD request')}")
    await asyncio.sleep(random.uniform(0.5, 5.0))
    # fail with probability
    if random.uniform(0,1)<FAIL_PROBABILITY:
        logger.info(f'Failing request range {request.headers.get('Range', 'HEAD request')}')
        return web.Response(status=500, reason="Internal Server Error")
    return web.FileResponse(FILE_PATH)

async def handle_download_without_ranges(request):
    logger.debug(f"Request received to server without range support: {request.headers.get('Range', 'HEAD request')}")
    await asyncio.sleep(random.uniform(0.5, 5.0))
    with open(FILE_PATH, 'rb') as f:
        data = f.read()
    return web.Response(body=data)

app = web.Application()
app.add_routes([web.get('/', handle_download)])

if __name__ == '__main__':
    logger = configure_logging()
    if not os.path.exists(FILE_PATH):
        logger.error(f"Error: Please create {FILE_PATH} first.")
    else:
        logger.info(f"Serving {FILE_PATH} with {ARTIFICIAL_DELAY}s delay...")
        web.run_app(app, port=8080)