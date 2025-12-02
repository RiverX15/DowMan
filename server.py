from aiohttp import web
import asyncio
import os
import random
import logging
import time


FILE_PATH = 'test_file.bin'
ARTIFICIAL_DELAY = 5.0
LOG_FILE = 'server.log'
TIMEOUT = 10

def configure_logging() -> logging.Logger:
    logger = logging.getLogger('server')
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(LOG_FILE)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

async def on_startup(app):
    app['start_time'] = time.perf_counter()
    logger.info('Server is starting up.')

async def on_cleanup(app):
    logger.info(f'Server is shutting down. Total runtime: {time.perf_counter() - app['start_time']:.2f} s')

async def handle_download(request):
    logger.debug(f"Request received to server with range support: {request.headers.get('Range', 'HEAD request')}")
    # failure simulation
    failure_mode = random.choice(['timeout', 'connection_reset', 'http_error', 'none', 'none', 'none'])
    if failure_mode == 'timeout':
        logger.info(f'Simulating timeout for request range {request.headers.get('Range', 'HEAD request')}')
        await asyncio.sleep(TIMEOUT)
        return web.Response(status=500, reason='Simulated Timeout')
    elif failure_mode == 'connection_reset':
        logger.info(f'Simulating connection reset for request range {request.headers.get('Range', 'HEAD request')}')
        if request.transport:
            request.transport.close()
        return web.Response(status=500)
    await asyncio.sleep(random.uniform(0.5, 5.0))
    if failure_mode == 'http_error':
        logger.info(f'Simulating HTTP error for request range {request.headers.get('Range', 'HEAD request')}')
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
app.on_startup.append(on_startup)
app.on_cleanup.append(on_cleanup)

if __name__ == '__main__':
    logger = configure_logging()
    if not os.path.exists(FILE_PATH):
        logger.error(f"Error: Please create {FILE_PATH} first.")
    else:
        logger.info(f"Serving {FILE_PATH}...")
        web.run_app(app, port=8080)