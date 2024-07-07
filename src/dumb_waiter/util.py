import asyncio

async def run_later(delay, callback):
    "Coroutine to call a synchronous callback in delay seconds"
    # To run callback() later in your calling code you should use 
    # asyncio.create_task(run_later(delay=200,callback=foo))
    await asyncio.sleep(delay)
    callback()