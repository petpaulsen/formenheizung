import asyncio
import functools


def async_test(func, timeout=5):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        loop = asyncio.SelectorEventLoop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(asyncio.wait_for(func(*args, **kwargs), timeout=timeout))
    return wrapper
async_test.__test__ = False
