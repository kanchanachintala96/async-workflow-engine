import asyncio
import time
from functools import wraps
import logging

logger = logging.getLogger("TelemetryTracer")


def trace_execution(func):
    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            logger.info(f"TRACE START: Function '{func.__name__}'")
            try:
                result = await func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000
                logger.info(f"TRACE SUCCESS: '{func.__name__}' completed in {duration:.2f}ms")
                return result
            except Exception as exc:
                duration = (time.time() - start_time) * 1000
                logger.error(
                    f"TRACE ERROR: '{func.__name__}' failed after {duration:.2f}ms. Error: {str(exc)}"
                )
                raise

        return async_wrapper

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        logger.info(f"TRACE START: Function '{func.__name__}'")
        try:
            result = func(*args, **kwargs)
            duration = (time.time() - start_time) * 1000
            logger.info(f"TRACE SUCCESS: '{func.__name__}' completed in {duration:.2f}ms")
            return result
        except Exception as exc:
            duration = (time.time() - start_time) * 1000
            logger.error(
                f"TRACE ERROR: '{func.__name__}' failed after {duration:.2f}ms. Error: {str(exc)}"
            )
            raise

    return sync_wrapper