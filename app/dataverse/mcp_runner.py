import asyncio
import threading
from typing import Any, Coroutine, Optional

_loop: Optional[asyncio.AbstractEventLoop] = None
_thread: Optional[threading.Thread] = None

def _start_loop(loop: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(loop)
    loop.run_forever()

def ensure_loop() -> asyncio.AbstractEventLoop:
    """Ensure a background event loop is running and return it."""
    global _loop, _thread
    if _loop and _loop.is_running():
        return _loop
    _loop = asyncio.new_event_loop()
    _thread = threading.Thread(target=_start_loop, args=(_loop,), daemon=True)
    _thread.start()
    return _loop

def run_sync(coro: Coroutine[Any, Any, Any], timeout: Optional[float] = None) -> Any:
    """
    Submit an async coroutine to the background loop and wait for the result.

    Usage:
        result = run_sync(mcp_client.get_service_lines(claim_id), timeout=30)
    """
    loop = ensure_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result(timeout)