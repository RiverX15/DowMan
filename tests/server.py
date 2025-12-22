from aiohttp import web
import asyncio
import os
import random
import logging
import time
import sys
import tomllib


FILE_PATH = 'test_file.bin'
ARTIFICIAL_DELAY_LOW_S = 0.2
ARTIFICIAL_DELAY_HIGH_S = 1.0
LOG_FILE = 'server.log'
ARTIFICIAL_TIMEOUT_S = 10.0
CHUNK_SIZE_MB = 5
CHUNK_SIZE = CHUNK_SIZE_MB * 1024 * 1024


def create_random_binary_file(filename, filesize_mb):
    filesize = filesize_mb*1024*1024
    with open(filename, 'wb') as f:
        while filesize > 0:
            f.write(os.urandom(min(filesize, CHUNK_SIZE)))
            filesize-=min(filesize, CHUNK_SIZE)
    print(f'Successfully created file: {filename}')

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
    file_size = os.path.getsize(FILE_PATH)
    app['l'] = random.randint(0, file_size)
    app['r'] = min(app['l']+3.5*1024*1024, file_size)
    logger.info('Server is starting up.')

async def on_cleanup(app):
    logger.info(f'Server is shutting down. Total runtime: {time.perf_counter() - app['start_time']:.2f} s')

async def failure_simulation(request):
    failure_mode = random.choice(['timeout', 'connection_reset', 'http_error', *['none' for _ in range(97)]])
    if failure_mode == 'timeout':
        logger.info(f'Simulating timeout for request range {request.headers.get('Range', 'HEAD request')}')
        await asyncio.sleep(ARTIFICIAL_TIMEOUT_S)
        return web.Response(status=500, reason='Simulated Timeout')
    elif failure_mode == 'connection_reset':
        logger.info(f'Simulating connection reset for request range {request.headers.get('Range', 'HEAD request')}')
        if request.transport:
            request.transport.close()
        return web.Response(status=500)
    await asyncio.sleep(random.uniform(ARTIFICIAL_DELAY_LOW_S, ARTIFICIAL_DELAY_HIGH_S))
    if failure_mode == 'http_error':
        logger.info(f'Simulating HTTP error for request range {request.headers.get('Range', 'HEAD request')}')
        return web.Response(status=500, reason="Internal Server Error")
    return None

async def handle_download(request):
    logger.debug(f"Request received to server: {request.headers.get('Range', 'HEAD request')}")
    failure = await failure_simulation(request)
    if failure:
        return failure
    logger.info(f'Serving request range {request.headers.get('Range', 'HEAD request')}')
    return web.FileResponse(FILE_PATH)

async def handle_download_without_ranges(request):
    logger.debug(f"Request received to server: {request.headers.get('Range', 'HEAD request')}")
    failure = await failure_simulation(request)
    if failure:
        return failure
    logger.info(f'Serving request without ranges.')
    with open(FILE_PATH, 'rb') as f:
        data = f.read()
    return web.Response(body=data)

async def handle_download_corrupted_sector(request):
    logger.debug(f"Request received to server with corrupted sector: {request.headers.get('Range', 'HEAD request')}")
    if request.headers.get('Range'):
        l, r = [int(x) for x in request.headers.get('Range').split('=')[-1].split('-')]
        if not (l>app['r'] or r<app['l']):
            logger.info(f'Simulating corrupt sector for request range {request.headers.get('Range', 'HEAD request')}')
            return web.Response(status=500, reason="Internal Server Error (corrupted sector)")
    failure = await failure_simulation(request)
    if failure:
        return failure
    logger.info(f'Serving request range {request.headers.get('Range', 'HEAD request')}')
    return web.FileResponse(FILE_PATH)

if '--fast' in sys.argv:
    with open('config_test.toml', 'rb') as f:
        test_config = tomllib.load(f)
        server_conf = test_config['server']
    ARTIFICIAL_TIMEOUT_S = server_conf['artificial_timeout_seconds']
    ARTIFICIAL_DELAY_LOW_S = server_conf['artificial_delay_min_seconds']
    ARTIFICIAL_DELAY_HIGH_S = server_conf['artificial_delay_max_seconds']
    CHUNK_SIZE_MB = server_conf['chunk_size_mb']
    CHUNK_SIZE = CHUNK_SIZE_MB*1024*1024

app = web.Application()
if '--no-range' in sys.argv:
    handler = handle_download_without_ranges
elif '--corrupt' in sys.argv:
    handler = handle_download_corrupted_sector
else:
    handler = handle_download
app.add_routes([web.get('/', handler)])
app.on_startup.append(on_startup)
app.on_cleanup.append(on_cleanup)


if __name__ == '__main__':
    logger = configure_logging()
    if not os.path.exists(FILE_PATH):
        create_random_binary_file(FILE_PATH, 10)
    logger.info(f"Serving {FILE_PATH} in {'NO-RANGE' if '--no-range' in sys.argv else 'RANGE'} mode with {'FAST' if '--fast' in sys.argv else 'NORMAL'} configuration.")
    web.run_app(app, port=8080)