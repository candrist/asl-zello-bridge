import asyncio
import logging
import os
import signal
import sys

from .zello import ZelloController
from .usrp import USRPController
from .stream import AsyncByteStream

log_level = os.environ.get('LOG_LEVEL', 'INFO')
log_format = os.environ.get('LOG_FORMAT', '%(levelname)s:%(name)s:%(message)s')
logging.basicConfig(level=log_level, format=log_format)
logger = logging.getLogger('__main__')


async def _main():
    loop = asyncio.get_running_loop()

    # Stream from Zello -> USRP
    zousrp = AsyncByteStream()

    # Stream from USRP -> Zello
    usrpzo = AsyncByteStream()

    usrp_ptt = asyncio.Event()
    zello_ptt = asyncio.Event()

    logger.info('Initialising Zello')
    zello = ZelloController(zousrp, usrpzo, usrp_ptt, zello_ptt)

    logger.info('Initialising USRP')
    usrp = USRPController(usrpzo, zousrp, usrp_ptt, zello_ptt)

    stop_event = asyncio.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            pass

    try:
        transport, _protocol = await loop.create_datagram_endpoint(
            lambda: usrp,
            local_addr=(os.environ.get('USRP_BIND'),
                        int(os.environ.get('USRP_RXPORT', 0))))
    except (OSError, ValueError) as e:
        logger.error(f'Failed to bind USRP RX port: {e}')
        return 1

    tasks = [
        asyncio.create_task(zello.run()),
        asyncio.create_task(usrp.run()),
    ]
    stop_waiter = asyncio.create_task(stop_event.wait())

    done, _pending = await asyncio.wait(
        [*tasks, stop_waiter],
        return_when=asyncio.FIRST_COMPLETED)

    for task in tasks:
        if task.done() and not task.cancelled() and task.exception() is not None:
            logger.error(f'Task failed: {task.exception()}')

    if stop_waiter not in done:
        logger.warning('Bridge task exited unexpectedly, shutting down')

    logger.info('Shutting down...')
    await zello.shutdown()

    for task in [*tasks, stop_waiter]:
        task.cancel()
    await asyncio.gather(*tasks, stop_waiter, return_exceptions=True)

    transport.close()
    logger.info('Shutdown complete')

    return 0 if stop_waiter in done else 1


def main():
    try:
        sys.exit(asyncio.run(_main()))
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == '__main__':
    main()
